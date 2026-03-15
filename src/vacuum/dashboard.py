"""Local web dashboard for Roborock Saros 10R status and control."""

from __future__ import annotations

import asyncio
import logging
import time
import webbrowser
from contextlib import asynccontextmanager
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Annotated

import uvicorn
from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse, Response
from fastapi.staticfiles import StaticFiles
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
# PWA assets (served before static mount so they take precedence)
# ---------------------------------------------------------------------------

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


# ---------------------------------------------------------------------------
# React SPA — serve built frontend (must come after all /api/* routes)
# ---------------------------------------------------------------------------

_DIST = Path(__file__).parent.parent.parent / "frontend" / "dist"

if not _DIST.exists():
    logging.getLogger("vacuum").warning(
        "frontend/dist/ not found — run 'cd frontend && npm run build' first"
    )
else:
    app.mount("/", StaticFiles(directory=str(_DIST), html=True), name="static")


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
