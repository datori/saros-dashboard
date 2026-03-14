"""Local web dashboard for Roborock Saros 10R status and control."""

from __future__ import annotations

import asyncio
import logging
import time
import webbrowser
from contextlib import asynccontextmanager
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Annotated

import uvicorn
from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse, Response
from pydantic import BaseModel

import typer

from .client import CleanRoute, FanSpeed, MopMode, VacuumClient, WaterFlow
from . import scheduler

# ---------------------------------------------------------------------------
# App state
# ---------------------------------------------------------------------------

_client: VacuumClient | None = None
_client_failures: int = 0
_reconnect_lock: asyncio.Lock = asyncio.Lock()
_MAX_FAILURES_BEFORE_RECONNECT = 3

# ---------------------------------------------------------------------------
# Response cache
# ---------------------------------------------------------------------------

_cache: dict[str, tuple[float, object]] = {}
_cache_locks: dict[str, asyncio.Lock] = {}
_stale_cache: dict[str, object] = {}

# ---------------------------------------------------------------------------
# Health state
# ---------------------------------------------------------------------------

_last_contact: float | None = None  # monotonic timestamp of last successful device call
_reconnect_count: int = 0

# ---------------------------------------------------------------------------
# Active clean tracking & completion monitor
# ---------------------------------------------------------------------------

_DISPATCH_TIMEOUT_SEC = 300  # 5 minutes to enter cleaning state
_CLEANING_STATES = {"sweeping", "mopping", "cleaning"}
_SUCCESS_STATES = {"charging", "charging_complete"}
_FAILURE_STATES = {"error", "idle"}


@dataclass
class ActiveClean:
    event_id: int
    segment_ids: list[int]
    dispatched_at: float  # monotonic time
    mode: str = "vacuum"


_active_clean: ActiveClean | None = None


async def _check_active_clean(status: dict) -> None:
    """Monitor vacuum state for UI feedback. Credit is handled by history reconciliation."""
    global _active_clean
    if _active_clean is None:
        return

    log = logging.getLogger("vacuum")
    state = status.get("state", "")
    now = time.monotonic()

    # Vacuum returned to dock — clean is done (or was never started). Clear UI state.
    if state in _SUCCESS_STATES:
        log.info("Clean %d: vacuum docked, clearing active clean (reconciler handles credit)",
                 _active_clean.event_id)
        _active_clean = None
        return

    # Vacuum is idle (not docked) — unusual but clear UI state
    if state in _FAILURE_STATES and state != "error":
        log.info("Clean %d: vacuum idle, clearing active clean", _active_clean.event_id)
        _active_clean = None
        return

    # Error state — do NOT clear; vacuum may recover
    if state == "error":
        log.info("Clean %d: vacuum in error state, keeping active clean (may recover)",
                 _active_clean.event_id)
        return

    # Dispatch timeout — clear UI state but don't mark event as failed
    if state not in _CLEANING_STATES and now - _active_clean.dispatched_at > _DISPATCH_TIMEOUT_SEC:
        log.warning("Clean %d: dispatch timeout (%.0fs), clearing active clean",
                    _active_clean.event_id, now - _active_clean.dispatched_at)
        _active_clean = None


# ---------------------------------------------------------------------------
# History reconciliation
# ---------------------------------------------------------------------------

_MATCH_WINDOW_SEC = 600  # ±10 minutes for timestamp matching


async def _reconcile_clean_events() -> None:
    """Match unreconciled scheduler events against device clean history."""
    log = logging.getLogger("vacuum")
    unreconciled = await scheduler.get_unreconciled_events()
    if not unreconciled:
        return

    try:
        client = _get_client()
        history = await client.get_clean_history(limit=5)
    except Exception as e:
        log.debug("Reconciliation: failed to fetch device history: %s", e)
        return

    if not history:
        return

    for event in unreconciled:
        dispatched = datetime.fromisoformat(event.dispatched_at)
        if dispatched.tzinfo is None:
            dispatched = dispatched.replace(tzinfo=timezone.utc)

        best_match = None
        best_delta = float("inf")

        for record in history:
            if record.start_time is None:
                continue
            record_start = datetime.fromisoformat(record.start_time)
            if record_start.tzinfo is None:
                record_start = record_start.replace(tzinfo=timezone.utc)
            delta = abs((record_start - dispatched).total_seconds())
            if delta <= _MATCH_WINDOW_SEC and delta < best_delta:
                best_match = record
                best_delta = delta

        if best_match is None:
            continue

        await scheduler.reconcile_event(
            event.event_id,
            duration_sec=best_match.duration_seconds,
            area_m2=best_match.area_m2,
            complete=best_match.complete,
        )
        status = "complete" if best_match.complete else "incomplete"
        log.info(
            "Reconciled event %d (%s, delta=%.0fs): %s",
            event.event_id, event.source, best_delta, status,
        )


# ---------------------------------------------------------------------------
# Window dispatch loop
# ---------------------------------------------------------------------------

_window_end: float | None = None  # monotonic time


def _open_window(budget_min: float) -> None:
    """Open or extend the cleaning window."""
    global _window_end
    new_end = time.monotonic() + budget_min * 60
    _window_end = max(_window_end or 0, new_end)


async def _close_window() -> None:
    """Close the cleaning window, dock vacuum if cleaning, close trigger events."""
    global _window_end
    _window_end = None
    # Dock vacuum if it's currently cleaning
    try:
        client = _get_client()
        status = await _cached("status", _CACHE_TTL, _fetch_status)
        if status.get("state") in _CLEANING_STATES:
            await client.return_to_dock()
            _cache_invalidate("status")
    except Exception:
        pass
    # Close all open trigger events
    await scheduler.close_all_trigger_events()


_ENUM_MAP = {
    "fan_speed": {e.name.lower(): e for e in FanSpeed},
    "mop_mode": {e.name.lower(): e for e in MopMode},
    "water_flow": {e.name.lower(): e for e in WaterFlow},
    "route": {e.name.lower(): e for e in CleanRoute},
}


def _parse_dispatch_settings(settings: dict) -> dict:
    """Convert string setting names to enum values, skipping None values."""
    result = {}
    for field, enum_map in _ENUM_MAP.items():
        val = settings.get(field)
        if val is not None and val.lower() in enum_map:
            result[field] = enum_map[val.lower()]
    return result


async def _check_dispatch(status: dict) -> None:
    """If window is open and vacuum is idle, dispatch overdue rooms."""
    global _active_clean
    if _window_end is None:
        return
    now = time.monotonic()
    if now >= _window_end:
        # Window expired
        await _close_window()
        return

    state = status.get("state", "")
    in_dock = status.get("in_dock", False)
    # Only dispatch if vacuum is idle/docked
    if state not in ("charging", "charging_complete", "idle") and not in_dock:
        return

    remaining_sec = _window_end - now
    remaining_min = remaining_sec / 60

    # Get priority queue and select batch
    queue = await scheduler.get_priority_queue()
    if not queue:
        return

    log = logging.getLogger("vacuum")

    # Select rooms that fit within remaining time, by priority score
    selected: list[scheduler.PriorityEntry] = []
    running_sec = 0.0
    # Group by mode — dispatch the highest-priority mode batch
    # For simplicity, take rooms from highest priority regardless of mode,
    # then batch by the mode of the highest-priority entry
    target_mode = queue[0].mode
    for entry in queue:
        if entry.mode != target_mode:
            continue
        if entry.estimated_sec is None:
            selected.append(entry)
            log.info("Window dispatch: %s (unknown duration, included)", entry.name)
        elif running_sec + entry.estimated_sec <= remaining_sec:
            selected.append(entry)
            running_sec += entry.estimated_sec
        # else: doesn't fit, skip

    if not selected:
        return

    segment_ids = [e.segment_id for e in selected]
    log.info("Window dispatch: sending %d rooms (%s) for %s, est %.0fs, window %.0fs remaining",
             len(selected), ", ".join(e.name for e in selected), target_mode,
             running_sec, remaining_sec)

    try:
        client = _get_client()
        # Apply mode-specific dispatch settings
        ds = await scheduler.get_dispatch_settings()
        dkwargs = _parse_dispatch_settings(ds.get(target_mode, {}))
        await client.clean_rooms(segment_ids, **dkwargs)
        event_id = await scheduler.log_clean(segment_ids, target_mode, source="auto-window")
        _active_clean = ActiveClean(
            event_id=event_id,
            segment_ids=segment_ids,
            dispatched_at=time.monotonic(),
            mode=target_mode,
        )
        _cache_invalidate("status")
    except Exception as e:
        log.error("Window dispatch failed: %s", e)


async def _cached(key: str, ttl: float, fn):
    """Return cached result if fresh, else call fn() and cache the result.
    Falls back to stale cache on failure. Tracks success/failure for auto-reconnect."""
    global _last_contact
    now = time.monotonic()
    if key in _cache:
        ts, val = _cache[key]
        if now - ts < ttl:
            return val
    if key not in _cache_locks:
        _cache_locks[key] = asyncio.Lock()
    async with _cache_locks[key]:
        # Double-check after acquiring lock
        if key in _cache:
            ts, val = _cache[key]
            if now - ts < ttl:
                return val
        await _maybe_reconnect()
        try:
            result = await fn()
        except Exception:
            if _record_failure():
                asyncio.ensure_future(_maybe_reconnect())
            # Return stale data if available
            if key in _stale_cache:
                stale = _stale_cache[key]
                if isinstance(stale, dict):
                    return {**stale, "_stale": True}
                if isinstance(stale, list):
                    return stale  # lists can't carry _stale; JS handles via health endpoint
            raise
        _record_success()
        _last_contact = time.monotonic()
        _cache[key] = (_last_contact, result)
        _stale_cache[key] = result
        return result


def _cache_invalidate(*keys: str) -> None:
    """Remove named entries from the hot cache (stale cache preserved for fallback)."""
    for key in keys:
        _cache.pop(key, None)


async def _health_poll_loop() -> None:
    """Background task: poll device status every 60s, reconcile history, dispatch from window."""
    log = logging.getLogger("vacuum")
    while True:
        await asyncio.sleep(60)
        try:
            status = await _cached("status", _CACHE_TTL, _fetch_status)
            # Active clean UI monitor
            await _check_active_clean(status)
            # History reconciliation — credit via device history
            await _reconcile_clean_events()
            # Window dispatch (only if no active clean)
            if _active_clean is None:
                await _check_dispatch(status)
        except Exception as e:
            log.debug("Health poll failed: %s", e)


@asynccontextmanager
async def _lifespan(app: FastAPI):
    global _client
    scheduler.init_db()
    _client = VacuumClient()
    await _client.authenticate()
    try:
        rooms = await _client.get_rooms()
        await scheduler.sync_rooms(rooms)
    except Exception as e:
        logging.getLogger("vacuum").warning("Could not sync rooms on startup: %s", e)
    poller = asyncio.create_task(_health_poll_loop())
    try:
        yield
    finally:
        poller.cancel()
        try:
            await poller
        except asyncio.CancelledError:
            pass
        if _client:
            await _client.close()
            _client = None


app = FastAPI(title="Vacuum Dashboard", lifespan=_lifespan)


def _get_client() -> VacuumClient:
    if _client is None:
        raise HTTPException(status_code=503, detail="Vacuum client not ready")
    return _client


def _record_success() -> None:
    global _client_failures
    _client_failures = 0


def _record_failure() -> bool:
    """Increment failure count. Returns True if reconnect threshold is reached."""
    global _client_failures
    _client_failures += 1
    return _client_failures >= _MAX_FAILURES_BEFORE_RECONNECT


async def _maybe_reconnect() -> None:
    """Recreate the VacuumClient if failure threshold has been reached."""
    global _client, _client_failures, _reconnect_count
    if _client_failures < _MAX_FAILURES_BEFORE_RECONNECT:
        return
    if _reconnect_lock.locked():
        return  # Another coroutine is already reconnecting
    async with _reconnect_lock:
        if _client_failures < _MAX_FAILURES_BEFORE_RECONNECT:
            return  # Already reset by a concurrent reconnect
        log = logging.getLogger("vacuum")
        log.warning("Reconnecting VacuumClient after %d consecutive failures", _client_failures)
        try:
            new_client = VacuumClient()
            await new_client.authenticate()
            # Only replace after successful auth — never leave _client = None
            old = _client
            _client = new_client
            _client_failures = 0
            _reconnect_count += 1
            _cache.clear()
            _stale_cache.clear()
            log.info("VacuumClient reconnected successfully (reconnect #%d)", _reconnect_count)
            if old:
                try:
                    await old.close()
                except Exception:
                    pass
        except Exception as e:
            log.error("Reconnect failed: %s — will retry on next request", e)
            # Reset failure counter slightly so we don't hammer on every request,
            # but stay above threshold so reconnect is retried soon.
            _client_failures = _MAX_FAILURES_BEFORE_RECONNECT


# ---------------------------------------------------------------------------
# API endpoints
# ---------------------------------------------------------------------------


_CACHE_TTL = 5.0  # seconds


async def _fetch_status():
    s = await _get_client().get_status()
    return s.as_dict()


async def _fetch_rooms():
    rooms = await _get_client().get_rooms()
    return [{"id": r.id, "name": r.name} for r in rooms]


async def _fetch_routines():
    routines = await _get_client().get_routines()
    return [r.name for r in routines]


async def _fetch_consumables():
    c = await _get_client().get_consumables()
    return c.as_dict()


async def _fetch_history():
    records = await _get_client().get_clean_history(limit=10)
    return [r.as_dict() for r in records]


async def _fetch_settings():
    s = await _get_client().get_current_settings()
    return s.as_dict()


@app.get("/api/status")
async def api_status():
    try:
        return await _cached("status", _CACHE_TTL, _fetch_status)
    except Exception as e:
        return {"error": str(e)}


@app.get("/api/rooms")
async def api_rooms():
    try:
        return await _cached("rooms", _CACHE_TTL, _fetch_rooms)
    except Exception as e:
        return {"error": str(e)}


@app.get("/api/routines")
async def api_routines():
    try:
        return await _cached("routines", _CACHE_TTL, _fetch_routines)
    except Exception as e:
        return {"error": str(e)}


@app.get("/api/consumables")
async def api_consumables():
    try:
        return await _cached("consumables", _CACHE_TTL, _fetch_consumables)
    except Exception as e:
        return {"error": str(e)}


@app.get("/api/history")
async def api_history():
    try:
        return await _cached("history", _CACHE_TTL, _fetch_history)
    except Exception as e:
        return {"error": str(e)}


_ACTIONS = {
    "stop": lambda c, **_: c.stop(),
    "pause": lambda c, **_: c.pause(),
    "dock": lambda c, **_: c.return_to_dock(),
    "locate": lambda c, **_: c.locate(),
}

# ---------------------------------------------------------------------------
# Settings helpers
# ---------------------------------------------------------------------------

_FAN_SPEED_NAMES   = {e.name: e for e in FanSpeed}
_MOP_MODE_NAMES    = {e.name: e for e in MopMode}
_WATER_FLOW_NAMES  = {e.name: e for e in WaterFlow}
_CLEAN_ROUTE_NAMES = {e.name: e for e in CleanRoute}


def _parse_settings(data: dict) -> tuple[FanSpeed | None, MopMode | None, WaterFlow | None, CleanRoute | None]:
    """Parse optional settings fields from a request dict. Raises HTTPException on invalid values."""
    fan_speed  = None
    mop_mode   = None
    water_flow = None
    route      = None

    if (v := data.get("fan_speed")) is not None:
        if v not in _FAN_SPEED_NAMES:
            raise HTTPException(400, f"Invalid fan_speed '{v}'. Valid: {sorted(_FAN_SPEED_NAMES)}")
        fan_speed = _FAN_SPEED_NAMES[v]

    if (v := data.get("mop_mode")) is not None:
        if v not in _MOP_MODE_NAMES:
            raise HTTPException(400, f"Invalid mop_mode '{v}'. Valid: {sorted(_MOP_MODE_NAMES)}")
        mop_mode = _MOP_MODE_NAMES[v]

    if (v := data.get("water_flow")) is not None:
        if v not in _WATER_FLOW_NAMES:
            raise HTTPException(400, f"Invalid water_flow '{v}'. Valid: {sorted(_WATER_FLOW_NAMES)}")
        water_flow = _WATER_FLOW_NAMES[v]

    if (v := data.get("route")) is not None:
        if v not in _CLEAN_ROUTE_NAMES:
            raise HTTPException(400, f"Invalid route '{v}'. Valid: {sorted(_CLEAN_ROUTE_NAMES)}")
        route = _CLEAN_ROUTE_NAMES[v]

    return fan_speed, mop_mode, water_flow, route


def _infer_clean_mode(fan_speed_str: str | None, water_flow_str: str | None) -> str:
    """Infer scheduler mode from raw string values before enum parsing."""
    if fan_speed_str == "OFF":
        return "mop"
    if water_flow_str and water_flow_str != "OFF":
        return "both"
    return "vacuum"


@app.get("/api/settings")
async def api_settings_get():
    try:
        return await _cached("settings", _CACHE_TTL, _fetch_settings)
    except Exception as e:
        return {"error": str(e)}


class SettingsRequest(BaseModel):
    fan_speed: str | None = None
    mop_mode: str | None = None
    water_flow: str | None = None


@app.post("/api/settings")
async def api_settings_post(body: SettingsRequest):
    try:
        client = _get_client()
        fan_speed, mop_mode, water_flow, _ = _parse_settings(body.model_dump(exclude_none=False))
        if fan_speed is not None:
            await client.set_fan_speed(fan_speed)
        if mop_mode is not None:
            await client.set_mop_mode(mop_mode)
        if water_flow is not None:
            await client.set_water_flow(water_flow)
        _cache_invalidate("settings")
        return {"ok": True}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=503, detail=str(e))


class StartCleanRequest(BaseModel):
    fan_speed: str | None = None
    mop_mode: str | None = None
    water_flow: str | None = None
    route: str | None = None


@app.post("/api/action/{name}")
async def api_action(name: str, body: StartCleanRequest | None = None):
    global _active_clean
    try:
        if name == "start":
            data = body.model_dump() if body else {}
            fan_speed, mop_mode, water_flow, route = _parse_settings(data)
            await _get_client().start_clean(fan_speed=fan_speed, mop_mode=mop_mode, water_flow=water_flow, route=route)
            # Log whole-home clean and populate active clean
            mode = _infer_clean_mode(
                body.fan_speed if body else None,
                body.water_flow if body else None,
            )
            rows = await scheduler.get_schedule()
            all_ids = [r.segment_id for r in rows]
            if all_ids:
                event_id = await scheduler.log_clean(all_ids, mode, source="dashboard")
                _active_clean = ActiveClean(
                    event_id=event_id,
                    segment_ids=all_ids,
                    dispatched_at=time.monotonic(),
                    mode=mode,
                )
            _cache_invalidate("status")
            return {"ok": True}
        if name not in _ACTIONS:
            raise HTTPException(status_code=404, detail=f"Unknown action '{name}'. Valid: start, {list(_ACTIONS)}")
        await _ACTIONS[name](_get_client())
        _cache_invalidate("status")
        return {"ok": True}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=503, detail=str(e))


@app.post("/api/consumables/reset/{attribute}")
async def api_consumables_reset(attribute: str):
    try:
        await _get_client().reset_consumable(attribute)
        return {"ok": True}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/api/routine/{name}")
async def api_routine(name: str):
    try:
        await _get_client().run_routine(name)
        return {"ok": True}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=503, detail=str(e))


class RoomsCleanRequest(BaseModel):
    segment_ids: list[int]
    repeat: int = 1
    fan_speed: str | None = None
    mop_mode: str | None = None
    water_flow: str | None = None
    route: str | None = None


@app.post("/api/rooms/clean")
async def api_rooms_clean(body: RoomsCleanRequest):
    global _active_clean
    try:
        fan_speed, mop_mode, water_flow, route = _parse_settings(body.model_dump())
        await _get_client().clean_rooms(
            body.segment_ids, repeat=body.repeat,
            fan_speed=fan_speed, mop_mode=mop_mode, water_flow=water_flow, route=route,
        )
        mode = _infer_clean_mode(body.fan_speed, body.water_flow)
        event_id = await scheduler.log_clean(body.segment_ids, mode, source="dashboard")
        _active_clean = ActiveClean(
            event_id=event_id,
            segment_ids=body.segment_ids,
            dispatched_at=time.monotonic(),
            mode=mode,
        )
        _cache_invalidate("status")
        return {"ok": True}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=503, detail=str(e))


# ---------------------------------------------------------------------------
# Schedule API endpoints
# ---------------------------------------------------------------------------


@app.get("/api/schedule")
async def api_schedule_get():
    rows = await scheduler.get_schedule()
    return [r.as_dict() for r in rows]


class ScheduleRoomPatch(BaseModel):
    vacuum_days: float | None = None
    mop_days: float | None = None
    notes: str | None = None
    priority_weight: float | None = None
    default_duration_min: float | None = None


@app.patch("/api/schedule/rooms/{segment_id}")
async def api_schedule_room_patch(segment_id: int, body: ScheduleRoomPatch):
    if "vacuum_days" in body.model_fields_set:
        await scheduler.set_room_interval(segment_id, "vacuum", body.vacuum_days)
    if "mop_days" in body.model_fields_set:
        await scheduler.set_room_interval(segment_id, "mop", body.mop_days)
    if "notes" in body.model_fields_set:
        await scheduler.set_room_notes(segment_id, body.notes)
    if "priority_weight" in body.model_fields_set and body.priority_weight is not None:
        await scheduler.set_room_priority(segment_id, body.priority_weight)
    if "default_duration_min" in body.model_fields_set:
        sec = body.default_duration_min * 60 if body.default_duration_min is not None else None
        await scheduler.set_room_duration(segment_id, sec)
    return {"ok": True}


# ---------------------------------------------------------------------------
# Trigger API endpoints
# ---------------------------------------------------------------------------


@app.get("/api/triggers")
async def api_triggers_get():
    return await scheduler.get_triggers()


class TriggerUpsertRequest(BaseModel):
    budget_min: float
    mode: str = "vacuum"
    notes: str | None = None


@app.put("/api/triggers/{name}")
async def api_trigger_upsert(name: str, body: TriggerUpsertRequest):
    await scheduler.upsert_trigger(name, body.budget_min, body.mode, body.notes)
    return {"ok": True}


@app.delete("/api/triggers/{name}")
async def api_trigger_delete(name: str):
    await scheduler.delete_trigger(name)
    return {"ok": True}


@app.post("/api/trigger/{name}/fire")
async def api_trigger_fire(name: str):
    # Look up trigger
    triggers = await scheduler.get_triggers()
    trigger = next((t for t in triggers if t["name"] == name), None)
    if trigger is None:
        raise HTTPException(status_code=404, detail=f"Trigger '{name}' not found")
    _open_window(trigger["budget_min"])
    await scheduler.log_trigger_event(name)
    now = time.monotonic()
    remaining = max(0, (_window_end or 0) - now)
    return {
        "ok": True,
        "window": {
            "active": True,
            "remaining_minutes": round(remaining / 60, 1),
        },
    }


@app.post("/api/trigger/stop")
async def api_trigger_stop():
    await _close_window()
    return {"ok": True, "window": {"active": False}}


@app.get("/api/window")
async def api_window_get():
    now = time.monotonic()
    active = _window_end is not None and now < _window_end
    remaining = max(0, (_window_end or 0) - now) if active else 0
    return {
        "active": active,
        "remaining_minutes": round(remaining / 60, 1) if active else 0,
        "current_clean": {
            "event_id": _active_clean.event_id,
            "segment_ids": _active_clean.segment_ids,
            "mode": _active_clean.mode,
            "started": True,
        } if _active_clean else None,
    }


class WindowOpenRequest(BaseModel):
    budget_min: float


@app.post("/api/window/open")
async def api_window_open(body: WindowOpenRequest):
    _open_window(body.budget_min)
    now = time.monotonic()
    active = _window_end is not None and now < _window_end
    remaining = max(0, (_window_end or 0) - now) if active else 0
    return {
        "active": active,
        "remaining_minutes": round(remaining / 60, 1) if active else 0,
        "current_clean": {
            "event_id": _active_clean.event_id,
            "segment_ids": _active_clean.segment_ids,
            "mode": _active_clean.mode,
            "started": True,
        } if _active_clean else None,
    }


@app.get("/api/window/preview")
async def api_window_preview():
    queue = await scheduler.get_priority_queue()
    return {"queue": [entry.as_dict() for entry in queue]}


@app.get("/api/dispatch-settings")
async def api_dispatch_settings_get():
    return await scheduler.get_dispatch_settings()


class DispatchSettingsPatch(BaseModel):
    fan_speed: str | None = None
    mop_mode: str | None = None
    water_flow: str | None = None
    route: str | None = None


@app.patch("/api/dispatch-settings/{mode}")
async def api_dispatch_settings_patch(mode: str, body: DispatchSettingsPatch):
    if mode not in ("vacuum", "mop"):
        raise HTTPException(status_code=400, detail="Mode must be 'vacuum' or 'mop'")
    updates = {k: v for k, v in body.model_dump().items() if k in body.model_fields_set}
    await scheduler.update_dispatch_settings(mode, **updates)
    return {"ok": True}


@app.get("/api/health")
async def api_health():
    now = time.monotonic()
    seconds_ago = round(now - _last_contact, 1) if _last_contact is not None else None
    ok = _last_contact is not None and (now - _last_contact) < 120
    return {"ok": ok, "last_contact_seconds_ago": seconds_ago, "reconnect_count": _reconnect_count}


# ---------------------------------------------------------------------------
# Frontend HTML
# ---------------------------------------------------------------------------

_HTML = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0, viewport-fit=cover">
<meta name="apple-mobile-web-app-capable" content="yes">
<meta name="apple-mobile-web-app-status-bar-style" content="black-translucent">
<meta name="apple-mobile-web-app-title" content="Vacuum">
<meta name="theme-color" content="#22272e">
<link rel="manifest" href="/manifest.json">
<link rel="apple-touch-icon" href="/icons/apple-touch-icon.png">
<title>Vacuum Dashboard</title>
<style>
  :root {
    --bg: #22272e;
    --surface: #2d333b;
    --border: #444c56;
    --accent: #4f8ef7;
    --accent2: #7c3aed;
    --green: #22c55e;
    --yellow: #eab308;
    --red: #ef4444;
    --text: #adbac7;
    --muted: #768390;
    --radius: 12px;
  }
  * { box-sizing: border-box; margin: 0; padding: 0; }
  body {
    background: var(--bg);
    color: var(--text);
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
    font-size: 14px;
    min-height: 100vh;
    padding: max(20px, env(safe-area-inset-top)) max(20px, env(safe-area-inset-right)) max(20px, env(safe-area-inset-bottom)) max(20px, env(safe-area-inset-left));
  }
  header {
    display: flex;
    align-items: center;
    gap: 12px;
    margin-bottom: 24px;
  }
  header h1 { font-size: 20px; font-weight: 600; }
  header .refresh-info { color: var(--muted); font-size: 12px; margin-left: auto; }
  /* Cockpit layout — mobile default (stacked) */
  #cockpit { display: flex; flex-direction: column; gap: 16px; }
  #sidebar { display: contents; }
  #right-pane { display: contents; }
  #right-tab-bar { display: none; }
  /* Scope toggle for Clean Rooms panel */
  .scope-toggle { display: flex; gap: 16px; margin-bottom: 12px; font-size: 13px; }
  .scope-toggle label { display: flex; align-items: center; gap: 6px; cursor: pointer; }
  .scope-toggle input[type=radio] { accent-color: var(--accent); }
  /* Right-pane tab bar (desktop only) */
  .right-tab-btn { background: none; border: none; color: var(--muted); cursor: pointer; font-size: 13px; font-weight: 500; padding: 7px 14px; border-radius: 8px; transition: color 0.15s, background 0.15s; }
  .right-tab-btn:hover { color: var(--text); background: var(--border); }
  .right-tab-btn.active { color: var(--accent); background: #1a2744; }
  .panel {
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: var(--radius);
    padding: 20px;
  }
  .panel-title {
    font-size: 11px;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.08em;
    color: var(--muted);
    margin-bottom: 16px;
    display: flex;
    align-items: center;
    gap: 6px;
  }
  .panel-title.stale { opacity: 0.6; }
  .panel-title.stale::after { content: "⏱"; font-size: 10px; }
  #connectivity-banner {
    display: none;
    background: #3d2b1f;
    border: 1px solid #7c3a1e;
    color: #f97316;
    border-radius: var(--radius);
    padding: 10px 16px;
    margin-bottom: 16px;
    font-size: 13px;
  }
  .stat-row {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 6px 0;
    border-bottom: 1px solid var(--border);
  }
  .stat-row:last-child { border-bottom: none; }
  .stat-label { color: var(--muted); }
  .stat-value { font-weight: 500; }
  .badge {
    display: inline-block;
    padding: 2px 8px;
    border-radius: 999px;
    font-size: 11px;
    font-weight: 600;
  }
  .badge-green { background: #1e3a2a; color: var(--green); }
  .badge-yellow { background: #3d2c00; color: var(--yellow); }
  .badge-red { background: #3d1515; color: var(--red); }
  .badge-blue { background: #243d5e; color: var(--accent); }
  .badge-gray { background: var(--border); color: var(--muted); }
  .progress-wrap { margin: 8px 0; }
  .progress-label { display: flex; justify-content: space-between; margin-bottom: 4px; }
  .btn-reset { font-size: 11px; padding: 2px 8px; border-radius: 4px; border: 1px solid var(--border); background: var(--surface); color: var(--muted); cursor: pointer; }
  .btn-reset:hover { color: var(--text); border-color: var(--accent); }
  .progress-bar-bg {
    height: 8px;
    background: var(--border);
    border-radius: 4px;
    overflow: hidden;
  }
  .progress-bar {
    height: 100%;
    border-radius: 4px;
    transition: width 0.5s ease;
  }
  .bar-green { background: var(--green); }
  .bar-yellow { background: var(--yellow); }
  .bar-red { background: var(--red); }
  .bar-blue { background: var(--accent); }
  .btn {
    display: inline-flex;
    align-items: center;
    gap: 6px;
    padding: 8px 14px;
    border-radius: 8px;
    border: none;
    cursor: pointer;
    font-size: 13px;
    font-weight: 500;
    transition: opacity 0.15s, transform 0.1s;
  }
  .btn:active { transform: scale(0.97); }
  .btn:disabled { opacity: 0.45; cursor: not-allowed; transform: none; }
  .btn-primary { background: var(--accent); color: #fff; }
  .btn-danger  { background: var(--red); color: #fff; }
  .btn-warning { background: var(--yellow); color: #000; }
  .btn-neutral { background: var(--border); color: var(--text); }
  .btn-purple  { background: var(--accent2); color: #fff; }
  .btn-sm { padding: 5px 10px; font-size: 12px; }
  .actions-grid {
    display: flex;
    flex-wrap: wrap;
    gap: 8px;
  }
  .feedback {
    font-size: 12px;
    margin-top: 8px;
    min-height: 18px;
  }
  .feedback.ok { color: var(--green); }
  .feedback.err { color: var(--red); }
  table { width: 100%; border-collapse: collapse; }
  th { text-align: left; color: var(--muted); font-weight: 500; padding: 4px 8px 8px 0; font-size: 12px; }
  td { padding: 6px 8px 6px 0; border-bottom: 1px solid var(--border); vertical-align: top; }
  tr:last-child td { border-bottom: none; }
  .checkbox-list { display: flex; flex-direction: column; gap: 6px; max-height: 180px; overflow-y: auto; }
  .checkbox-list label { display: flex; align-items: center; gap: 8px; cursor: pointer; }
  .checkbox-list input[type=checkbox] { accent-color: var(--accent); width: 15px; height: 15px; }
  .form-row { display: flex; align-items: center; gap: 8px; margin-top: 12px; flex-wrap: wrap; }
  .form-row label { color: var(--muted); white-space: nowrap; }
  input[type=number] {
    background: var(--bg);
    border: 1px solid var(--border);
    border-radius: 6px;
    color: var(--text);
    padding: 6px 10px;
    width: 64px;
    font-size: 13px;
  }
  .routine-list { display: flex; flex-direction: column; gap: 8px; }
  .routine-row { display: flex; justify-content: space-between; align-items: center; }
  .spinner { display: inline-block; width: 14px; height: 14px; border: 2px solid rgba(255,255,255,.3); border-top-color: #fff; border-radius: 50%; animation: spin .7s linear infinite; }
  @keyframes spin { to { transform: rotate(360deg); } }
  .loading { color: var(--muted); font-style: italic; }
  .unavailable { color: var(--muted); font-style: italic; }
  .last-updated { font-size: 11px; color: var(--muted); margin-top: 12px; }
  select {
    background: var(--bg);
    border: 1px solid var(--border);
    border-radius: 6px;
    color: var(--text);
    padding: 5px 10px;
    font-size: 13px;
    cursor: pointer;
  }
  select:focus { outline: none; border-color: var(--accent); }
  .settings-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 10px; }
  .settings-row { display: flex; flex-direction: column; gap: 4px; }
  .settings-label { font-size: 11px; color: var(--muted); }
  /* Trigger buttons */
  .trigger-grid { display: flex; flex-wrap: wrap; gap: 8px; margin-bottom: 12px; }
  .btn-trigger { background: #1e3a5e; color: var(--accent); border: 1px solid var(--accent); }
  .btn-trigger:hover { background: #243d5e; }
  .btn-stop-window { background: #3d1515; color: var(--red); border: 1px solid var(--red); }
  .window-status { margin-top: 12px; font-size: 13px; padding: 8px 12px; border-radius: 8px; }
  .window-active { background: #1e3a2a; border: 1px solid var(--green); color: var(--green); }
  .window-inactive { background: var(--border); color: var(--muted); }
  /* Trigger management */
  .trigger-mgmt-row { display: flex; justify-content: space-between; align-items: center; padding: 6px 0; border-bottom: 1px solid var(--border); }
  .trigger-mgmt-row:last-child { border-bottom: none; }
  .trigger-mgmt-info { display: flex; flex-direction: column; gap: 2px; }
  .trigger-mgmt-name { font-weight: 500; }
  .trigger-mgmt-detail { font-size: 12px; color: var(--muted); }
  /* Schedule panel */
  .schedule-table { width: 100%; border-collapse: collapse; font-size: 13px; }
  .schedule-table th { text-align: left; color: var(--muted); font-weight: 500; padding: 4px 8px 8px 0; font-size: 12px; }
  .schedule-table td { padding: 7px 8px 7px 0; border-bottom: 1px solid var(--border); vertical-align: middle; }
  .schedule-table tr:last-child td { border-bottom: none; }
  .overdue-cell { color: var(--red); font-weight: 600; }
  .warning-cell { color: var(--yellow); font-weight: 600; }
  .dim-cell { color: var(--muted); }
  /* Window planner */
  .planner-slider-row { display: flex; align-items: center; gap: 10px; margin-bottom: 12px; }
  .planner-slider-row label { font-size: 13px; color: var(--muted); white-space: nowrap; }
  .planner-slider-row input[type=range] { flex: 1; accent-color: var(--accent); }
  #planner-budget-label { font-size: 14px; font-weight: 600; min-width: 50px; }
  .planner-room { display: flex; align-items: center; gap: 8px; padding: 5px 0; font-size: 13px; }
  .planner-room .dot { width: 8px; height: 8px; border-radius: 50%; flex-shrink: 0; }
  .planner-room .dot.selected { background: var(--accent); }
  .planner-room .dot.excluded { border: 2px solid var(--muted); }
  .planner-room .room-name { min-width: 90px; }
  .planner-room .room-mode { color: var(--muted); font-size: 11px; min-width: 30px; }
  .planner-room .room-est { color: var(--muted); font-size: 12px; min-width: 35px; text-align: right; }
  .planner-room .room-score { color: var(--muted); font-size: 12px; min-width: 35px; text-align: right; }
  .planner-room .bar-wrap { flex: 1; height: 10px; background: var(--border); border-radius: 5px; overflow: hidden; min-width: 60px; }
  .planner-room .bar-fill { height: 100%; background: var(--accent); border-radius: 5px; transition: width 0.15s; }
  .planner-divider { border-top: 1px dashed var(--border); margin: 6px 0; }
  .planner-summary { font-size: 12px; color: var(--muted); margin-top: 8px; }
  /* Interval edit modal */
  .modal-overlay {
    display: none; position: fixed; inset: 0;
    background: rgba(0,0,0,.6); z-index: 100;
    align-items: center; justify-content: center;
  }
  .modal-overlay.open { display: flex; }
  .modal {
    background: var(--surface); border: 1px solid var(--border);
    border-radius: var(--radius); padding: 24px; min-width: 300px;
  }
  .modal h3 { font-size: 15px; margin-bottom: 16px; }
  .modal-row { display: flex; flex-direction: column; gap: 4px; margin-bottom: 12px; }
  .modal-row label { font-size: 12px; color: var(--muted); }
  .modal-row input[type=number] { width: 100%; }
  .modal-row input[type=text] {
    background: var(--bg); border: 1px solid var(--border); border-radius: 6px;
    color: var(--text); padding: 6px 10px; font-size: 13px; width: 100%;
  }
  .modal-actions { display: flex; gap: 8px; margin-top: 16px; justify-content: flex-end; }
  /* Table scroll wrapper */
  .table-scroll { overflow-x: auto; -webkit-overflow-scrolling: touch; }
  /* Mobile bottom tab bar */
  #tab-bar { display: none; }
  .tab-btn { display: flex; flex-direction: column; align-items: center; gap: 3px; flex: 1; background: none; border: none; color: var(--muted); cursor: pointer; font-size: 10px; padding: 8px 0; transition: color 0.15s; }
  .tab-btn .tab-icon { font-size: 20px; line-height: 1; }
  .tab-btn.active { color: var(--accent); }
  /* Desktop cockpit layout (≥ 900px) */
  @media (min-width: 900px) {
    #cockpit { flex-direction: row; align-items: flex-start; }
    #sidebar { display: flex; flex-direction: column; gap: 16px; width: 320px; flex-shrink: 0; position: sticky; top: 20px; max-height: calc(100vh - 40px); overflow-y: auto; }
    #right-pane { display: flex; flex-direction: column; gap: 16px; flex: 1; min-width: 0; max-width: 640px; }
    #right-tab-bar { display: flex; gap: 4px; background: var(--surface); border: 1px solid var(--border); border-radius: var(--radius); padding: 6px; }
    #right-pane[data-active-right-tab="rooms"]    [data-right-tab]:not([data-right-tab="rooms"])    { display: none; }
    #right-pane[data-active-right-tab="routines"] [data-right-tab]:not([data-right-tab="routines"]) { display: none; }
    #right-pane[data-active-right-tab="triggers"] [data-right-tab]:not([data-right-tab="triggers"]) { display: none; }
    #right-pane[data-active-right-tab="info"]     [data-right-tab]:not([data-right-tab="info"])     { display: none; }
  }
  /* Mobile layout (< 900px) */
  @media (max-width: 899px) {
    .hide-mobile { display: none !important; }
    #tab-bar {
      display: flex;
      position: fixed;
      bottom: 0;
      left: 0;
      right: 0;
      background: var(--surface);
      border-top: 1px solid var(--border);
      padding-bottom: env(safe-area-inset-bottom);
      z-index: 50;
    }
    body { padding-bottom: calc(60px + env(safe-area-inset-bottom)); }
    body[data-active-tab="now"]   [data-tab]:not([data-tab="now"])   { display: none; }
    body[data-active-tab="clean"] [data-tab]:not([data-tab="clean"]) { display: none; }
    body[data-active-tab="plan"]  [data-tab]:not([data-tab="plan"])  { display: none; }
    body[data-active-tab="info"]  [data-tab]:not([data-tab="info"])  { display: none; }
  }
</style>
</head>
<body>

<header>
  <svg width="28" height="28" viewBox="0 0 28 28" fill="none">
    <circle cx="14" cy="14" r="13" stroke="#4f8ef7" stroke-width="2"/>
    <circle cx="14" cy="14" r="6" fill="#4f8ef7" opacity="0.3"/>
    <circle cx="14" cy="14" r="2" fill="#4f8ef7"/>
    <circle cx="14" cy="4"  r="1.5" fill="#4f8ef7"/>
    <circle cx="14" cy="24" r="1.5" fill="#4f8ef7"/>
    <circle cx="4"  cy="14" r="1.5" fill="#4f8ef7"/>
    <circle cx="24" cy="14" r="1.5" fill="#4f8ef7"/>
  </svg>
  <h1>Vacuum Dashboard</h1>
  <span class="refresh-info">Auto-refreshes every 30s &nbsp;·&nbsp; <a href="#" onclick="refreshAll();return false" style="color:var(--accent)">Refresh now</a></span>
</header>

<div id="connectivity-banner"></div>
<div id="cockpit">

  <div id="sidebar">

    <!-- Status Panel -->
    <div class="panel" data-tab="now">
      <div class="panel-title" id="title-status">Status</div>
      <div id="status-content" class="loading">Loading…</div>
      <div class="last-updated" id="status-updated"></div>
    </div>

    <!-- Actions Panel (quick buttons only) -->
    <div class="panel" data-tab="now">
      <div class="panel-title">Actions</div>
      <div class="actions-grid">
        <button class="btn btn-primary" onclick="doAction('start')">▶ Start</button>
        <button class="btn btn-danger"  onclick="doAction('stop')">■ Stop</button>
        <button class="btn btn-warning" onclick="doAction('pause')">⏸ Pause</button>
        <button class="btn btn-neutral" onclick="doAction('dock')">⏏ Dock</button>
        <button class="btn btn-neutral" onclick="doAction('locate')">🔔 Locate</button>
      </div>
      <div class="feedback" id="action-feedback"></div>
    </div>

    <!-- Consumables Panel -->
    <div class="panel" data-tab="info">
      <div class="panel-title" id="title-consumables">Consumables</div>
      <div id="consumables-content" class="loading">Loading…</div>
    </div>

  </div><!-- /#sidebar -->

  <div id="right-pane">

    <div id="right-tab-bar">
      <button class="right-tab-btn" id="rtab-rooms"    onclick="activateRightTab('rooms')">Rooms</button>
      <button class="right-tab-btn" id="rtab-routines" onclick="activateRightTab('routines')">Routines</button>
      <button class="right-tab-btn" id="rtab-triggers" onclick="activateRightTab('triggers')">Triggers</button>
      <button class="right-tab-btn" id="rtab-info"     onclick="activateRightTab('info')">Info</button>
    </div>

    <!-- Room Clean Panel -->
    <div class="panel" data-right-tab="rooms" data-tab="clean">
      <div class="panel-title">Clean Rooms</div>
      <div class="scope-toggle">
        <label><input type="radio" name="clean-scope" id="scope-all" value="all" onchange="updateCleanScope()"> All rooms</label>
        <label><input type="radio" name="clean-scope" id="scope-select" value="select" checked onchange="updateCleanScope()"> Select rooms</label>
      </div>
      <div id="room-check-list" class="checkbox-list loading">Loading…</div>
      <div style="margin-top:12px">
        <div style="font-size:11px;color:var(--muted);margin-bottom:8px">Override settings (optional)</div>
        <div class="settings-grid">
          <div class="settings-row">
            <span class="settings-label">Clean Mode</span>
            <select id="rooms-clean-mode" onchange="applyCleanMode(this.value)">
              <option value="">— no preference —</option>
              <option value="vacuum">Vacuum only</option>
              <option value="mop">Mop only</option>
              <option value="both">Both (simultaneous)</option>
              <option value="vac_then_mop">Vacuum, then Mop</option>
            </select>
          </div>
          <div class="settings-row">
            <span class="settings-label">Fan Speed</span>
            <select id="rooms-fan-speed"><option value="">— device default —</option><option>QUIET</option><option>BALANCED</option><option>TURBO</option><option>MAX</option><option>MAX_PLUS</option><option>OFF</option></select>
          </div>
          <div class="settings-row">
            <span class="settings-label">Mop Mode</span>
            <select id="rooms-mop-mode"><option value="">— device default —</option><option>STANDARD</option><option>FAST</option><option>DEEP</option><option>DEEP_PLUS</option></select>
          </div>
          <div class="settings-row">
            <span class="settings-label">Water Flow</span>
            <select id="rooms-water-flow"><option value="">— device default —</option><option>OFF</option><option>LOW</option><option>MEDIUM</option><option>HIGH</option><option>EXTREME</option><option>VAC_THEN_MOP</option></select>
          </div>
          <div class="settings-row">
            <span class="settings-label">Route</span>
            <select id="rooms-route"><option value="">— device default —</option><option>STANDARD</option><option>FAST</option><option>DEEP</option><option>DEEP_PLUS</option></select>
          </div>
        </div>
      </div>
      <div class="form-row" style="margin-top:12px">
        <label>Repeat:</label>
        <input type="number" id="repeat-count" value="1" min="1" max="3">
        <button class="btn btn-primary" onclick="startCleanFromRooms(this)">Start Clean</button>
      </div>
      <div class="feedback" id="rooms-clean-feedback"></div>
    </div>

    <!-- Routines Panel -->
    <div class="panel" data-right-tab="routines" data-tab="clean">
      <div class="panel-title" id="title-routines">Routines</div>
      <div id="routines-content" class="loading">Loading…</div>
      <div class="feedback" id="routine-feedback"></div>
    </div>

    <!-- Triggers & Window Panel -->
    <div class="panel" data-right-tab="triggers" data-tab="plan">
      <div class="panel-title">Auto-Clean Triggers</div>
      <div id="trigger-buttons" class="trigger-grid loading">Loading…</div>
      <div id="window-status" class="window-status window-inactive">No active window</div>
      <div class="feedback" id="trigger-feedback"></div>
      <div style="margin-top:12px;border-top:1px solid var(--border);padding-top:12px">
        <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:8px">
          <span style="font-size:11px;color:var(--muted);text-transform:uppercase;letter-spacing:0.08em;font-weight:600">Manage Triggers</span>
          <button class="btn btn-primary btn-sm" onclick="openTriggerModal()">+ Add</button>
        </div>
        <div id="trigger-mgmt-list"></div>
      </div>
      <div style="margin-top:12px;border-top:1px solid var(--border);padding-top:12px">
        <span style="font-size:11px;color:var(--muted);text-transform:uppercase;letter-spacing:0.08em;font-weight:600">Dispatch Settings</span>
        <div id="dispatch-settings" style="margin-top:8px"></div>
      </div>
    </div>

    <!-- Window Planner Panel -->
    <div class="panel" data-right-tab="triggers" data-tab="plan">
      <div class="panel-title">Window Planner <button class="btn btn-neutral btn-sm" onclick="loadPlannerPreview()" style="margin-left:8px;font-size:11px">Refresh</button></div>
      <div id="planner-content">
        <div class="planner-slider-row">
          <label for="planner-budget">Budget:</label>
          <input type="range" id="planner-budget" min="5" max="90" value="30" step="1">
          <span id="planner-budget-label">30 min</span>
        </div>
        <div id="planner-rooms"></div>
        <div id="planner-summary" class="planner-summary"></div>
        <div style="margin-top:12px">
          <button class="btn btn-primary" onclick="openWindowFromPlanner()">Open Window</button>
        </div>
      </div>
    </div>

    <!-- Clean Settings Panel -->
    <div class="panel" data-right-tab="info" data-tab="info">
      <div class="panel-title" id="title-settings">Clean Settings</div>
      <div class="settings-grid" id="settings-content">
        <div class="settings-row">
          <span class="settings-label">Fan Speed</span>
          <select id="set-fan-speed"><option value="">Loading…</option></select>
        </div>
        <div class="settings-row">
          <span class="settings-label">Mop Mode</span>
          <select id="set-mop-mode"><option value="">Loading…</option></select>
        </div>
        <div class="settings-row">
          <span class="settings-label">Water Flow</span>
          <select id="set-water-flow"><option value="">Loading…</option></select>
        </div>
      </div>
      <div class="form-row" style="margin-top:12px">
        <button class="btn btn-primary" onclick="saveSettings()">Save Settings</button>
      </div>
      <div class="feedback" id="settings-feedback"></div>
    </div>

    <!-- Schedule Panel -->
    <div class="panel" data-right-tab="info" data-tab="info">
      <div class="panel-title">Cleaning Schedule</div>
      <div id="schedule-content" class="loading">Loading…</div>
    </div>

    <!-- Clean History Panel -->
    <div class="panel" data-right-tab="info" data-tab="info">
      <div class="panel-title" id="title-history">Clean History (last 10)</div>
      <div id="history-content" class="loading">Loading…</div>
    </div>

  </div><!-- /#right-pane -->

</div><!-- /#cockpit -->

<!-- Interval edit modal -->
<div class="modal-overlay" onclick="if(event.target===this)closeEditModal()">
  <div class="modal">
    <h3 id="edit-modal-title">Edit Intervals</h3>
    <div class="modal-row">
      <label>Vacuum every (days) — clear to unschedule</label>
      <input type="number" id="edit-vacuum-days" min="0.5" step="0.5" placeholder="e.g. 3">
    </div>
    <div class="modal-row">
      <label>Mop every (days) — clear to unschedule</label>
      <input type="number" id="edit-mop-days" min="0.5" step="0.5" placeholder="e.g. 7">
    </div>
    <div class="modal-row">
      <label>Priority weight (default 1.0, higher = more urgent)</label>
      <input type="number" id="edit-priority-weight" min="0.1" step="0.1" placeholder="e.g. 1.5">
    </div>
    <div class="modal-row">
      <label>Est. duration (min) — clear to use auto-estimate</label>
      <input type="number" id="edit-duration-min" min="1" step="1" placeholder="e.g. 8">
    </div>
    <div class="modal-row">
      <label>Notes (optional)</label>
      <input type="text" id="edit-notes" placeholder="e.g. Pets sleep here, prioritize">
    </div>
    <div class="modal-actions">
      <button class="btn btn-neutral" onclick="closeEditModal()">Cancel</button>
      <button class="btn btn-primary" onclick="saveEditModal()">Save</button>
    </div>
  </div>
</div>

<!-- Trigger edit modal -->
<div class="modal-overlay" id="trigger-modal-overlay" onclick="if(event.target===this)closeTriggerModal()">
  <div class="modal">
    <h3 id="trigger-modal-title">Add Trigger</h3>
    <div class="modal-row">
      <label>Name</label>
      <input type="text" id="trigger-name" placeholder="e.g. Gym, Shower, Leaving">
    </div>
    <div class="modal-row">
      <label>Budget (minutes)</label>
      <input type="number" id="trigger-budget" min="5" step="5" placeholder="e.g. 25">
    </div>
    <div class="modal-row">
      <label>Mode</label>
      <select id="trigger-mode">
        <option value="vacuum">Vacuum</option>
        <option value="mop">Mop</option>
      </select>
    </div>
    <div class="modal-row">
      <label>Notes (optional)</label>
      <input type="text" id="trigger-notes" placeholder="e.g. Quick clean while at gym">
    </div>
    <div class="modal-actions">
      <button class="btn btn-neutral" onclick="closeTriggerModal()">Cancel</button>
      <button class="btn btn-primary" onclick="saveTriggerModal()">Save</button>
    </div>
  </div>
</div>

<script>
// ------------------------------------------------------------------ helpers
function fmt(val, fallback='—') { return val != null ? val : fallback; }

function pctColor(p) {
  if (p == null) return 'bar-gray';
  if (p > 50) return 'bar-green';
  if (p > 20) return 'bar-yellow';
  return 'bar-red';
}

function pctBadge(p) {
  if (p == null) return '<span class="badge badge-gray">—</span>';
  const cls = p > 50 ? 'badge-green' : p > 20 ? 'badge-yellow' : 'badge-red';
  return `<span class="badge ${cls}">${p}%</span>`;
}

function progressBar(label, pct, attribute) {
  const color = pctColor(pct);
  const display = pct != null ? pct + '%' : '—';
  const resetBtn = attribute
    ? `<button class="btn-reset" onclick="resetConsumable('${attribute}','${label}')">Reset</button>`
    : '';
  return `
    <div class="progress-wrap">
      <div class="progress-label"><span>${label}</span><span style="display:flex;align-items:center;gap:8px">${display}${resetBtn}</span></div>
      <div class="progress-bar-bg">
        <div class="progress-bar ${color}" style="width:${pct ?? 0}%"></div>
      </div>
    </div>`;
}

function setFeedback(id, msg, isErr) {
  const el = document.getElementById(id);
  el.textContent = msg;
  el.className = 'feedback ' + (isErr ? 'err' : 'ok');
  if (msg) setTimeout(() => { el.textContent = ''; el.className = 'feedback'; }, 4000);
}

async function apiPost(url, body) {
  const r = await fetch(url, {
    method: 'POST',
    headers: {'Content-Type':'application/json'},
    body: body !== undefined ? JSON.stringify(body) : undefined,
  });
  return r.json();
}

function populateSelect(id, options, current) {
  const el = document.getElementById(id);
  el.innerHTML = '<option value="">— device default —</option>' +
    options.map(o => `<option${o === current ? ' selected' : ''}>${o}</option>`).join('');
}

// ------------------------------------------------------------------ status
async function loadStatus() {
  const el = document.getElementById('status-content');
  try {
    const d = await fetch('/api/status').then(r => r.json());
    if (d.error) { el.innerHTML = `<span class="unavailable">Error: ${d.error}</span>`; return; }
    markStale('title-status', !!d._stale);

    const stateColor = d.state && d.state.toLowerCase().includes('clean') ? 'badge-blue'
      : d.state === 'charging' || d.state === 'charging_complete' ? 'badge-green'
      : d.state === 'error' ? 'badge-red' : 'badge-gray';

    const dockBadge = d.in_dock
      ? '<span class="badge badge-green">In dock</span>'
      : '<span class="badge badge-yellow">Away</span>';

    const battColor = (d.battery ?? 0) > 50 ? 'bar-green' : (d.battery ?? 0) > 20 ? 'bar-yellow' : 'bar-red';

    el.innerHTML = `
      <div class="stat-row">
        <span class="stat-label">State</span>
        <span class="badge ${stateColor}">${fmt(d.state)}</span>
      </div>
      <div class="stat-row">
        <span class="stat-label">Dock</span>
        ${dockBadge}
      </div>
      ${d.error_code ? `<div class="stat-row"><span class="stat-label">Error</span><span class="badge badge-red">${d.error_code}</span></div>` : ''}
      <div style="margin-top:12px">
        <div class="progress-label"><span>Battery</span><span>${fmt(d.battery, '?')}%</span></div>
        <div class="progress-bar-bg" style="height:12px;border-radius:6px">
          <div class="progress-bar ${battColor}" style="width:${d.battery ?? 0}%;height:100%"></div>
        </div>
      </div>`;
    document.getElementById('status-updated').textContent =
      'Updated ' + new Date().toLocaleTimeString();
  } catch(e) {
    el.innerHTML = `<span class="unavailable">Error: ${e.message}</span>`;
  }
}

// ------------------------------------------------------------------ rooms
let _rooms = [];

async function loadRooms() {
  const checkEl = document.getElementById('room-check-list');
  try {
    _rooms = await fetch('/api/rooms').then(r => r.json());
    if (!Array.isArray(_rooms)) {
      const msg = _rooms.error || 'Unavailable';
      checkEl.innerHTML = `<span class="unavailable">Error: ${msg}</span>`;
      _rooms = [];
      return;
    }
    if (!_rooms.length) {
      checkEl.innerHTML = '<span class="unavailable">No rooms found.</span>';
      return;
    }
    checkEl.className = 'checkbox-list';
    checkEl.innerHTML = _rooms.map(r =>
      `<label><input type="checkbox" value="${r.id}"> ${r.name}</label>`
    ).join('');
  } catch(e) {
    checkEl.innerHTML = `<span class="unavailable">Error: ${e.message}</span>`;
  }
}


// ------------------------------------------------------------------ routines
async function loadRoutines() {
  const el = document.getElementById('routines-content');
  try {
    const routines = await fetch('/api/routines').then(r => r.json());
    if (!Array.isArray(routines)) {
      el.innerHTML = `<span class="unavailable">Error: ${routines.error || 'Unavailable'}</span>`;
      return;
    }
    if (!routines.length) {
      el.innerHTML = '<span class="unavailable">No routines found.</span>';
      return;
    }
    el.innerHTML = `<div class="routine-list">
      ${routines.map(name =>
        `<div class="routine-row">
          <span>${name}</span>
          <button class="btn btn-purple btn-sm" onclick="runRoutine(this, '${name.replace(/'/g, "\\'")}')">Run</button>
        </div>`
      ).join('')}
    </div>`;
  } catch(e) {
    el.innerHTML = `<span class="unavailable">Error: ${e.message}</span>`;
  }
}

async function runRoutine(btn, name) {
  btn.disabled = true;
  btn.innerHTML = '<span class="spinner"></span>';
  try {
    const res = await fetch('/api/routine/' + encodeURIComponent(name), {method:'POST'}).then(r => r.json());
    setFeedback('routine-feedback', res.ok ? `'${name}' started!` : (res.detail || 'Error'), !res.ok);
  } catch(e) {
    setFeedback('routine-feedback', e.message, true);
  } finally {
    btn.disabled = false;
    btn.innerHTML = 'Run';
  }
}

// ------------------------------------------------------------------ clean mode
function applyCleanMode(mode) {
  const fs = document.getElementById('rooms-fan-speed');
  const wf = document.getElementById('rooms-water-flow');
  if (!fs || !wf) return;
  if (mode === 'vacuum') {
    fs.value = '';
    wf.value = 'OFF';
  } else if (mode === 'mop') {
    fs.value = 'OFF';
    wf.value = '';
  } else if (mode === 'both') {
    fs.value = '';
    wf.value = '';
  } else if (mode === 'vac_then_mop') {
    fs.value = '';
    wf.value = 'VAC_THEN_MOP';
  } else {
    fs.value = '';
    wf.value = '';
  }
}

// ------------------------------------------------------------------ scope toggle
function updateCleanScope() {
  const all = document.getElementById('scope-all').checked;
  document.getElementById('room-check-list').style.display = all ? 'none' : '';
}

// ------------------------------------------------------------------ actions
async function doAction(name) {
  const btns = document.querySelectorAll('.actions-grid .btn');
  btns.forEach(b => b.disabled = true);
  setFeedback('action-feedback', '');
  try {
    const res = await apiPost('/api/action/' + name, {});
    setFeedback('action-feedback', res.ok ? `${name} sent!` : (res.detail || 'Error'), !res.ok);
    if (name !== 'locate') setTimeout(loadStatus, 2000);
  } catch(e) {
    setFeedback('action-feedback', e.message, true);
  } finally {
    btns.forEach(b => b.disabled = false);
  }
}

async function startCleanFromRooms(btn) {
  const all = document.getElementById('scope-all').checked;
  btn.disabled = true;
  setFeedback('rooms-clean-feedback', '');
  try {
    if (all) {
      const body = {};
      const fs = document.getElementById('rooms-fan-speed').value;
      const wf = document.getElementById('rooms-water-flow').value;
      if (fs) body.fan_speed = fs;
      if (wf) body.water_flow = wf;
      const res = await apiPost('/api/action/start', body);
      setFeedback('rooms-clean-feedback', res.ok ? 'Cleaning started!' : (res.detail || 'Error'), !res.ok);
      if (res.ok) setTimeout(loadStatus, 2000);
    } else {
      const checked = [...document.querySelectorAll('#room-check-list input:checked')];
      if (!checked.length) { setFeedback('rooms-clean-feedback', 'Select at least one room.', true); return; }
      const ids = checked.map(c => parseInt(c.value));
      const repeat = parseInt(document.getElementById('repeat-count').value) || 1;
      const body = {segment_ids: ids, repeat};
      const fs = document.getElementById('rooms-fan-speed').value;
      const mm = document.getElementById('rooms-mop-mode').value;
      const wf = document.getElementById('rooms-water-flow').value;
      const rt = document.getElementById('rooms-route').value;
      if (fs) body.fan_speed = fs;
      if (mm) body.mop_mode = mm;
      if (wf) body.water_flow = wf;
      if (rt) body.route = rt;
      const res = await apiPost('/api/rooms/clean', body);
      setFeedback('rooms-clean-feedback', res.ok ? 'Cleaning started!' : (res.detail || 'Error'), !res.ok);
      if (res.ok) setTimeout(loadStatus, 2000);
    }
  } catch(e) {
    setFeedback('rooms-clean-feedback', e.message, true);
  } finally {
    btn.disabled = false;
  }
}

// ------------------------------------------------------------------ settings
async function loadSettings() {
  try {
    const s = await fetch('/api/settings').then(r => r.json());
    if (s.error) { document.getElementById('settings-feedback').textContent = `Could not load settings: ${s.error}`; return; }
    markStale('title-settings', !!s._stale);
    populateSelect('set-fan-speed',  ['QUIET','BALANCED','TURBO','MAX','MAX_PLUS','OFF','SMART'], s.fan_speed);
    populateSelect('set-mop-mode',   ['STANDARD','FAST','DEEP','DEEP_PLUS','SMART'], s.mop_mode);
    populateSelect('set-water-flow', ['OFF','LOW','MEDIUM','HIGH','EXTREME','VAC_THEN_MOP','SMART'], s.water_flow);
  } catch(e) {
    document.getElementById('settings-feedback').textContent = 'Could not load settings.';
  }
}

async function saveSettings() {
  const body = {};
  const fs = document.getElementById('set-fan-speed').value;
  const mm = document.getElementById('set-mop-mode').value;
  const wf = document.getElementById('set-water-flow').value;
  if (fs) body.fan_speed = fs;
  if (mm) body.mop_mode = mm;
  if (wf) body.water_flow = wf;
  try {
    const res = await apiPost('/api/settings', body);
    setFeedback('settings-feedback', res.ok ? 'Settings saved!' : (res.detail || 'Error'), !res.ok);
  } catch(e) {
    setFeedback('settings-feedback', e.message, true);
  }
}

// ------------------------------------------------------------------ consumables
async function loadConsumables() {
  const el = document.getElementById('consumables-content');
  try {
    const c = await fetch('/api/consumables').then(r => r.json());
    if (c.error) {
      el.innerHTML = `<span class="unavailable">Unavailable: ${c.error}</span>`;
      return;
    }
    markStale('title-consumables', !!c._stale);
    el.innerHTML = [
      progressBar('Main brush', c.main_brush_pct, 'main_brush_work_time'),
      progressBar('Side brush', c.side_brush_pct, 'side_brush_work_time'),
      progressBar('Filter',     c.filter_pct,     'filter_work_time'),
      progressBar('Sensors',    c.sensor_pct,     'sensor_dirty_time'),
    ].join('');
  } catch(e) {
    el.innerHTML = `<span class="unavailable">Error: ${e.message}</span>`;
  }
}

async function resetConsumable(attribute, label) {
  if (!confirm(`Reset ${label} timer? This cannot be undone.`)) return;
  try {
    const res = await fetch(`/api/consumables/reset/${attribute}`, {method:'POST'}).then(r => r.json());
    if (res.ok) {
      await loadConsumables();
    } else {
      alert(`Reset failed: ${res.detail || 'Unknown error'}`);
    }
  } catch(e) {
    alert(`Reset error: ${e.message}`);
  }
}

// ------------------------------------------------------------------ history
async function loadHistory() {
  const el = document.getElementById('history-content');
  try {
    const records = await fetch('/api/history').then(r => r.json());
    if (records.error) {
      el.innerHTML = `<span class="unavailable">Unavailable: ${records.error}</span>`;
      return;
    }
    if (!records.length) {
      el.innerHTML = '<span class="unavailable">No clean history found.</span>';
      return;
    }
    el.innerHTML = `<div class="table-scroll"><table>
      <tr><th>Start</th><th>Duration</th><th>Area (m²)</th><th>Complete</th><th class="hide-mobile">Started by</th><th class="hide-mobile">Type</th><th class="hide-mobile">Finish reason</th></tr>
      ${records.map(r => {
        const dt = r.start_time ? new Date(r.start_time).toLocaleString() : '—';
        const dur = r.duration_seconds != null
          ? Math.floor(r.duration_seconds/60) + 'm ' + (r.duration_seconds%60) + 's'
          : '—';
        const area = r.area_m2 != null ? r.area_m2 + ' m²' : '—';
        const done = r.complete
          ? '<span class="badge badge-green">Yes</span>'
          : '<span class="badge badge-yellow">No</span>';
        const startType = r.start_type ? r.start_type.replace(/_/g,' ') : '—';
        const cleanType = r.clean_type ? r.clean_type.replace(/_/g,' ') : '—';
        const reason = r.finish_reason ? r.finish_reason.replace(/_/g,' ') : '—';
        return `<tr><td>${dt}</td><td>${dur}</td><td>${area}</td><td>${done}</td><td class="hide-mobile">${startType}</td><td class="hide-mobile">${cleanType}</td><td class="hide-mobile">${reason}</td></tr>`;
      }).join('')}
    </table></div>`;
  } catch(e) {
    el.innerHTML = `<span class="unavailable">Error: ${e.message}</span>`;
  }
}

// ------------------------------------------------------------------ schedule
function fmtDate(iso) {
  if (!iso) return null;
  const d = new Date(iso);
  return d.toLocaleDateString(undefined, {month:'short', day:'numeric', year:'numeric'});
}

function dueDateStr(lastIso, intervalDays) {
  if (!intervalDays) return null;
  if (!lastIso) return 'Never';
  const due = new Date(new Date(lastIso).getTime() + intervalDays * 86400000);
  return due.toLocaleDateString(undefined, {month:'short', day:'numeric', year:'numeric'});
}

function overdueClass(ratio, intervalDays, lastIso) {
  if (!intervalDays) return 'dim-cell';       // no interval
  if (!lastIso) return 'overdue-cell';        // never cleaned → overdue
  if (ratio == null) return '';
  if (ratio >= 1.0) return 'overdue-cell';
  if (ratio >= 0.8) return 'warning-cell';
  return '';
}

async function loadSchedule() {
  const el = document.getElementById('schedule-content');
  try {
    const rows = await fetch('/api/schedule').then(r => r.json());
    if (!rows.length) {
      el.innerHTML = '<span class="unavailable">No rooms in schedule yet.</span>';
      return;
    }
    const html = `
      <div class="table-scroll"><table class="schedule-table">
        <tr>
          <th>Room</th>
          <th class="hide-mobile">Last Vacuumed</th>
          <th class="hide-mobile">Last Mopped</th>
          <th>Vacuum Due</th>
          <th>Mop Due</th>
          <th>Vacuum Every</th>
          <th>Mop Every</th>
          <th class="hide-mobile">Priority</th>
          <th class="hide-mobile">Est.</th>
          <th></th>
        </tr>
        ${rows.map(r => {
          const lv = fmtDate(r.last_vacuumed) || (r.vacuum_days ? '<span class="overdue-cell">Never</span>' : '<span class="dim-cell">—</span>');
          const lm = fmtDate(r.last_mopped)   || (r.mop_days   ? '<span class="overdue-cell">Never</span>' : '<span class="dim-cell">—</span>');

          const vDue = dueDateStr(r.last_vacuumed, r.vacuum_days);
          const mDue = dueDateStr(r.last_mopped, r.mop_days);
          const vClass = overdueClass(r.vacuum_overdue_ratio, r.vacuum_days, r.last_vacuumed);
          const mClass = overdueClass(r.mop_overdue_ratio, r.mop_days, r.last_mopped);

          const vDueHtml = vDue
            ? `<span class="${vClass}">${vDue}${r.vacuum_overdue_ratio != null && r.vacuum_overdue_ratio >= 1.0 ? ' ⚠' : (r.vacuum_days && !r.last_vacuumed ? ' ⚠' : '')}</span>`
            : '<span class="dim-cell">—</span>';
          const mDueHtml = mDue
            ? `<span class="${mClass}">${mDue}${r.mop_overdue_ratio != null && r.mop_overdue_ratio >= 1.0 ? ' ⚠' : (r.mop_days && !r.last_mopped ? ' ⚠' : '')}</span>`
            : '<span class="dim-cell">—</span>';

          const vInterval = r.vacuum_days ? r.vacuum_days + 'd' : '<span class="dim-cell">—</span>';
          const mInterval = r.mop_days    ? r.mop_days    + 'd' : '<span class="dim-cell">—</span>';

          const pw = r.priority_weight != null ? r.priority_weight : 1.0;
          const pwDisplay = pw !== 1.0 ? `<strong>${pw}</strong>` : '<span class="dim-cell">1.0</span>';
          const durMin = r.default_duration_sec != null ? Math.round(r.default_duration_sec / 60) : null;
          const durDisplay = durMin != null ? durMin + 'm' : '<span class="dim-cell">—</span>';

          return `<tr>
            <td><strong>${r.name}</strong></td>
            <td class="hide-mobile">${lv}</td>
            <td class="hide-mobile">${lm}</td>
            <td>${vDueHtml}</td>
            <td>${mDueHtml}</td>
            <td>${vInterval}</td>
            <td>${mInterval}</td>
            <td class="hide-mobile">${pwDisplay}</td>
            <td class="hide-mobile">${durDisplay}</td>
            <td><button class="btn btn-neutral btn-sm" onclick='openEditModal(${r.segment_id}, ${JSON.stringify(r.name)}, ${r.vacuum_days || "null"}, ${r.mop_days || "null"}, ${JSON.stringify(r.notes || "")}, ${pw}, ${r.default_duration_sec != null ? (r.default_duration_sec / 60) : "null"})'>Edit</button></td>
          </tr>`;
        }).join('')}
      </table></div>`;
    el.innerHTML = html;
  } catch(e) {
    el.innerHTML = `<span class="unavailable">Unavailable: ${e.message}</span>`;
  }
}

// ------------------------------------------------------------------ schedule edit modal
let _editSegmentId = null;

function openEditModal(segmentId, name, vacuumDays, mopDays, notes, priorityWeight, durationMin) {
  _editSegmentId = segmentId;
  document.getElementById('edit-modal-title').textContent = name;
  document.getElementById('edit-vacuum-days').value = vacuumDays ?? '';
  document.getElementById('edit-mop-days').value    = mopDays ?? '';
  document.getElementById('edit-priority-weight').value = priorityWeight ?? '';
  document.getElementById('edit-duration-min').value = durationMin ?? '';
  document.getElementById('edit-notes').value       = notes ?? '';
  document.querySelector('.modal-overlay').classList.add('open');
}

function closeEditModal() {
  document.querySelector('.modal-overlay').classList.remove('open');
  _editSegmentId = null;
}

async function saveEditModal() {
  if (_editSegmentId == null) return;
  const vd = document.getElementById('edit-vacuum-days').value;
  const md = document.getElementById('edit-mop-days').value;
  const nt = document.getElementById('edit-notes').value;
  const pw = document.getElementById('edit-priority-weight').value;
  const dur = document.getElementById('edit-duration-min').value;
  const body = {};
  body.vacuum_days = vd !== '' ? parseFloat(vd) : null;
  body.mop_days    = md !== '' ? parseFloat(md) : null;
  body.notes       = nt || null;
  if (pw !== '') body.priority_weight = parseFloat(pw);
  body.default_duration_min = dur !== '' ? parseFloat(dur) : null;
  try {
    const res = await fetch(`/api/schedule/rooms/${_editSegmentId}`, {
      method: 'PATCH',
      headers: {'Content-Type':'application/json'},
      body: JSON.stringify(body),
    }).then(r => r.json());
    if (res.ok) {
      closeEditModal();
      await loadSchedule();
    } else {
      alert('Save failed: ' + (res.detail || 'Unknown error'));
    }
  } catch(e) {
    alert('Save error: ' + e.message);
  }
}

// ------------------------------------------------------------------ triggers & window
let _triggers = [];

async function loadTriggers() {
  const btnEl = document.getElementById('trigger-buttons');
  const mgmtEl = document.getElementById('trigger-mgmt-list');
  try {
    _triggers = await fetch('/api/triggers').then(r => r.json());
    if (!_triggers.length) {
      btnEl.innerHTML = '<span class="unavailable">No triggers configured yet. Add one below.</span>';
      btnEl.className = '';
      mgmtEl.innerHTML = '';
    } else {
      btnEl.className = 'trigger-grid';
      btnEl.innerHTML = _triggers.map(t =>
        `<button class="btn btn-trigger" onclick="fireTrigger('${t.name.replace(/'/g, "\\\\'")}')">${t.name} (${t.budget_min}m)</button>`
      ).join('') +
        `<button class="btn btn-stop-window" onclick="stopWindow()">Stop</button>`;
      mgmtEl.innerHTML = _triggers.map(t => `
        <div class="trigger-mgmt-row">
          <div class="trigger-mgmt-info">
            <span class="trigger-mgmt-name">${t.name}</span>
            <span class="trigger-mgmt-detail">${t.budget_min}min · ${t.mode}${t.notes ? ' · ' + t.notes : ''}</span>
          </div>
          <div style="display:flex;gap:4px">
            <button class="btn btn-neutral btn-sm" onclick='openTriggerModal(${JSON.stringify(t.name)}, ${t.budget_min}, ${JSON.stringify(t.mode)}, ${JSON.stringify(t.notes || "")})'>Edit</button>
            <button class="btn btn-danger btn-sm" onclick="deleteTrigger('${t.name.replace(/'/g, "\\\\'")}')">Del</button>
          </div>
        </div>`
      ).join('');
    }
  } catch(e) {
    btnEl.innerHTML = `<span class="unavailable">Error: ${e.message}</span>`;
  }
}

async function loadWindowStatus() {
  const el = document.getElementById('window-status');
  try {
    const w = await fetch('/api/window').then(r => r.json());
    if (w.active) {
      el.className = 'window-status window-active';
      let text = `Window active — ${w.remaining_minutes} min remaining`;
      if (w.current_clean) {
        text += ` · Cleaning ${w.current_clean.segment_ids.length} room(s)`;
      }
      el.textContent = text;
    } else {
      el.className = 'window-status window-inactive';
      el.textContent = 'No active window';
    }
  } catch(e) { /* ignore */ }
}

async function fireTrigger(name) {
  try {
    const res = await apiPost(`/api/trigger/${encodeURIComponent(name)}/fire`);
    if (res.ok) {
      setFeedback('trigger-feedback', `${name} fired! Window: ${res.window.remaining_minutes}min`, false);
      loadWindowStatus();
    } else {
      setFeedback('trigger-feedback', res.detail || 'Error', true);
    }
  } catch(e) {
    setFeedback('trigger-feedback', e.message, true);
  }
}

async function stopWindow() {
  try {
    const res = await apiPost('/api/trigger/stop');
    setFeedback('trigger-feedback', res.ok ? 'Window closed, vacuum docking' : (res.detail || 'Error'), !res.ok);
    loadWindowStatus();
    setTimeout(loadStatus, 2000);
  } catch(e) {
    setFeedback('trigger-feedback', e.message, true);
  }
}

// ------------------------------------------------------------------ trigger modal
let _editingTriggerName = null;

function openTriggerModal(name, budget, mode, notes) {
  if (name) {
    _editingTriggerName = name;
    document.getElementById('trigger-modal-title').textContent = 'Edit Trigger';
    document.getElementById('trigger-name').value = name;
    document.getElementById('trigger-name').readOnly = true;
    document.getElementById('trigger-budget').value = budget ?? '';
    document.getElementById('trigger-mode').value = mode || 'vacuum';
    document.getElementById('trigger-notes').value = notes || '';
  } else {
    _editingTriggerName = null;
    document.getElementById('trigger-modal-title').textContent = 'Add Trigger';
    document.getElementById('trigger-name').value = '';
    document.getElementById('trigger-name').readOnly = false;
    document.getElementById('trigger-budget').value = '';
    document.getElementById('trigger-mode').value = 'vacuum';
    document.getElementById('trigger-notes').value = '';
  }
  document.getElementById('trigger-modal-overlay').classList.add('open');
}

function closeTriggerModal() {
  document.getElementById('trigger-modal-overlay').classList.remove('open');
  _editingTriggerName = null;
}

async function saveTriggerModal() {
  const name = document.getElementById('trigger-name').value.trim();
  const budget = parseFloat(document.getElementById('trigger-budget').value);
  const mode = document.getElementById('trigger-mode').value;
  const notes = document.getElementById('trigger-notes').value.trim() || null;
  if (!name) { alert('Name is required'); return; }
  if (!budget || budget <= 0) { alert('Budget must be positive'); return; }
  try {
    const res = await fetch(`/api/triggers/${encodeURIComponent(name)}`, {
      method: 'PUT',
      headers: {'Content-Type':'application/json'},
      body: JSON.stringify({budget_min: budget, mode, notes}),
    }).then(r => r.json());
    if (res.ok) {
      closeTriggerModal();
      await loadTriggers();
    } else {
      alert('Save failed: ' + (res.detail || 'Unknown error'));
    }
  } catch(e) {
    alert('Save error: ' + e.message);
  }
}

async function deleteTrigger(name) {
  if (!confirm(`Delete trigger "${name}"?`)) return;
  try {
    await fetch(`/api/triggers/${encodeURIComponent(name)}`, {method:'DELETE'});
    await loadTriggers();
  } catch(e) {
    alert('Delete error: ' + e.message);
  }
}

// ------------------------------------------------------------------ stale + health
function markStale(titleId, isStale) {
  const el = document.getElementById(titleId);
  if (!el) return;
  if (isStale) el.classList.add('stale');
  else el.classList.remove('stale');
}

async function loadHealth() {
  try {
    const h = await fetch('/api/health').then(r => r.json());
    const banner = document.getElementById('connectivity-banner');
    if (!h.ok && h.last_contact_seconds_ago !== null) {
      const mins = Math.round(h.last_contact_seconds_ago / 60);
      banner.textContent = `⚠ Device unreachable — last contact ${mins}m ago`;
      banner.style.display = 'block';
    } else {
      banner.style.display = 'none';
    }
  } catch(e) { /* ignore */ }
}

// ------------------------------------------------------------------ refresh
function refreshAll() {
  const loaders = [loadStatus, loadRooms, loadRoutines, loadConsumables, loadHistory, loadSettings, loadSchedule, loadHealth, loadTriggers, loadWindowStatus, loadPlannerPreview, loadDispatchSettings];
  loaders.forEach((fn, i) => setTimeout(fn, i * 300));
}

// ------------------------------------------------------------------ dispatch settings
const _FAN_SPEEDS = ['off','quiet','balanced','turbo','max','max_plus','smart'];
const _MOP_MODES = ['standard','fast','deep','deep_plus','smart'];
const _WATER_FLOWS = ['off','low','medium','high','extreme','smart'];
const _ROUTES = ['standard','fast','deep','deep_plus','smart'];

async function loadDispatchSettings() {
  const el = document.getElementById('dispatch-settings');
  try {
    const settings = await fetch('/api/dispatch-settings').then(r => r.json());
    let html = '';
    for (const mode of ['vacuum', 'mop']) {
      const s = settings[mode] || {};
      html += `<div style="margin-bottom:10px">
        <span style="font-size:12px;font-weight:600;text-transform:capitalize">${mode}</span>
        <div style="display:grid;grid-template-columns:1fr 1fr;gap:4px 8px;margin-top:4px;font-size:12px">
          <label style="color:var(--muted)">Fan speed</label>
          ${_makeSelect(mode, 'fan_speed', s.fan_speed, _FAN_SPEEDS)}
          <label style="color:var(--muted)">Mop mode</label>
          ${_makeSelect(mode, 'mop_mode', s.mop_mode, _MOP_MODES)}
          <label style="color:var(--muted)">Water flow</label>
          ${_makeSelect(mode, 'water_flow', s.water_flow, _WATER_FLOWS)}
          <label style="color:var(--muted)">Route</label>
          ${_makeSelect(mode, 'route', s.route, _ROUTES)}
        </div>
      </div>`;
    }
    el.innerHTML = html;
  } catch(e) {
    el.innerHTML = `<span class="unavailable">${e.message}</span>`;
  }
}

function _makeSelect(mode, field, current, options) {
  const opts = ['<option value=""' + (current == null ? ' selected' : '') + '>—</option>']
    .concat(options.map(o => `<option value="${o}"${o === current ? ' selected' : ''}>${o.replace(/_/g,' ')}</option>`));
  return `<select onchange="saveDispatchSetting('${mode}','${field}',this.value)" style="font-size:12px;background:var(--bg);color:var(--text);border:1px solid var(--border);border-radius:4px;padding:2px 4px">${opts.join('')}</select>`;
}

async function saveDispatchSetting(mode, field, value) {
  const body = {};
  body[field] = value || null;
  try {
    await fetch(`/api/dispatch-settings/${mode}`, {
      method: 'PATCH',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify(body),
    });
  } catch(e) {
    alert('Failed to save: ' + e.message);
  }
}

// ------------------------------------------------------------------ window planner
let _plannerQueue = [];

async function loadPlannerPreview() {
  try {
    const data = await fetch('/api/window/preview').then(r => r.json());
    _plannerQueue = data.queue || [];
    renderPlanner();
  } catch(e) {
    document.getElementById('planner-rooms').innerHTML =
      `<span class="unavailable">Preview unavailable: ${e.message}</span>`;
  }
}

function renderPlanner() {
  const budget = parseInt(document.getElementById('planner-budget').value, 10);
  document.getElementById('planner-budget-label').textContent = budget + ' min';
  const budgetSec = budget * 60;
  const roomsEl = document.getElementById('planner-rooms');
  const summaryEl = document.getElementById('planner-summary');

  if (!_plannerQueue.length) {
    roomsEl.innerHTML = '<span class="dim-cell">No overdue rooms</span>';
    summaryEl.textContent = '';
    return;
  }

  // Batch selection: mode from top entry, greedy fill
  const targetMode = _plannerQueue[0].mode;
  const selected = [];
  const excluded = [];
  let runSec = 0;

  for (const entry of _plannerQueue) {
    if (entry.mode !== targetMode) { excluded.push({...entry, reason: 'mode'}); continue; }
    const est = entry.estimated_sec;
    if (est == null) {
      selected.push({...entry, cumul: runSec});
    } else if (runSec + est <= budgetSec) {
      runSec += est;
      selected.push({...entry, cumul: runSec});
    } else {
      excluded.push({...entry, reason: 'budget'});
    }
  }

  let html = '';
  for (const r of selected) {
    const estMin = r.estimated_sec != null ? Math.round(r.estimated_sec / 60) + 'm' : '?';
    const score = r.priority_score != null ? r.priority_score.toFixed(1) : '∞';
    const pct = budgetSec > 0 ? Math.min(100, (r.cumul / budgetSec) * 100) : 0;
    html += `<div class="planner-room">
      <span class="dot selected"></span>
      <span class="room-name">${r.name}</span>
      <span class="room-mode">${r.mode}</span>
      <span class="room-est">${estMin}</span>
      <span class="room-score">${score}</span>
      <span class="bar-wrap"><span class="bar-fill" style="width:${pct.toFixed(1)}%"></span></span>
    </div>`;
  }

  if (excluded.length) {
    html += '<div class="planner-divider"></div>';
    for (const r of excluded) {
      const estMin = r.estimated_sec != null ? Math.round(r.estimated_sec / 60) + 'm' : '?';
      const score = r.priority_score != null ? r.priority_score.toFixed(1) : '∞';
      const note = r.reason === 'mode' ? r.mode : "won't fit";
      html += `<div class="planner-room">
        <span class="dot excluded"></span>
        <span class="room-name" style="color:var(--muted)">${r.name}</span>
        <span class="room-mode">${note}</span>
        <span class="room-est" style="opacity:0.5">${estMin}</span>
        <span class="room-score" style="opacity:0.5">${score}</span>
        <span class="bar-wrap"></span>
      </div>`;
    }
  }

  roomsEl.innerHTML = html;
  const totalMin = Math.round(runSec / 60);
  summaryEl.textContent = selected.length
    ? `${selected.length} room${selected.length > 1 ? 's' : ''} · ${totalMin} min of ${budget} min budget`
    : 'No rooms fit in budget';
}

document.getElementById('planner-budget').addEventListener('input', renderPlanner);

async function openWindowFromPlanner() {
  const budget = parseInt(document.getElementById('planner-budget').value, 10);
  try {
    await fetch('/api/window/open', {
      method: 'POST',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify({budget_min: budget}),
    });
    await loadWindowStatus();
  } catch(e) {
    alert('Failed to open window: ' + e.message);
  }
}

// ------------------------------------------------------------------ tabs
function activateTab(tab) {
  document.body.dataset.activeTab = tab;
  sessionStorage.setItem('activeTab', tab);
  document.querySelectorAll('.tab-btn').forEach(btn => {
    btn.classList.toggle('active', btn.id === 'tab-' + tab);
  });
}
activateTab(sessionStorage.getItem('activeTab') || 'now');

function activateRightTab(tab) {
  const pane = document.getElementById('right-pane');
  pane.dataset.activeRightTab = tab;
  sessionStorage.setItem('activeRightTab', tab);
  document.querySelectorAll('.right-tab-btn').forEach(btn => {
    btn.classList.toggle('active', btn.id === 'rtab-' + tab);
  });
}
activateRightTab(sessionStorage.getItem('activeRightTab') || 'rooms');

// Initial load + auto-refresh
refreshAll();
setInterval(refreshAll, 30000);
</script>

<nav id="tab-bar">
  <button class="tab-btn" id="tab-now"   onclick="activateTab('now')"><span class="tab-icon">🏠</span>Now</button>
  <button class="tab-btn" id="tab-clean" onclick="activateTab('clean')"><span class="tab-icon">🧹</span>Clean</button>
  <button class="tab-btn" id="tab-plan"  onclick="activateTab('plan')"><span class="tab-icon">📅</span>Plan</button>
  <button class="tab-btn" id="tab-info"  onclick="activateTab('info')"><span class="tab-icon">📊</span>Info</button>
</nav>
</body>
</html>"""


_ICON_SVG = """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 192 192">
  <rect width="192" height="192" rx="40" fill="#22272e"/>
  <circle cx="96" cy="82" r="46" fill="none" stroke="#4f8ef7" stroke-width="10"/>
  <circle cx="96" cy="82" r="18" fill="#4f8ef7"/>
  <rect x="58" y="136" width="76" height="12" rx="6" fill="#adbac7"/>
  <rect x="70" y="152" width="12" height="16" rx="4" fill="#adbac7"/>
  <rect x="110" y="152" width="12" height="16" rx="4" fill="#adbac7"/>
</svg>"""


@app.get("/icons/apple-touch-icon.png")
async def icon():
    return Response(content=_ICON_SVG, media_type="image/svg+xml")


@app.get("/manifest.json")
async def manifest():
    return JSONResponse({
        "name": "Vacuum Dashboard",
        "short_name": "Vacuum",
        "start_url": "/",
        "display": "standalone",
        "background_color": "#22272e",
        "theme_color": "#22272e",
        "icons": [
            {
                "src": "/icons/apple-touch-icon.png",
                "sizes": "192x192",
                "type": "image/svg+xml",
            }
        ],
    }, headers={"Content-Type": "application/manifest+json"})


@app.get("/", response_class=HTMLResponse)
async def index():
    return HTMLResponse(_HTML)


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------

_cli = typer.Typer(name="vacuum-dashboard", add_completion=False)


@_cli.command()
def _cmd(
    port: Annotated[int, typer.Option("--port", "-p", help="Port to listen on")] = 8080,
    no_browser: Annotated[bool, typer.Option("--no-browser", help="Don't open browser on start")] = False,
) -> None:
    """Launch the vacuum web dashboard."""
    import socket
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        lan_ip = s.getsockname()[0]
        s.close()
    except Exception:
        lan_ip = None

    typer.echo(f"Vacuum dashboard starting on port {port}")
    typer.echo(f"  Local:   http://localhost:{port}")
    if lan_ip and not lan_ip.startswith("127."):
        typer.echo(f"  Network: http://{lan_ip}:{port}")

    if not no_browser:
        import threading
        def _open():
            import time
            time.sleep(1.2)
            webbrowser.open(f"http://localhost:{port}")
        threading.Thread(target=_open, daemon=True).start()

    uvicorn.run(app, host="0.0.0.0", port=port, log_level="warning")


def main() -> None:
    _cli()
