"""Local web dashboard for Roborock Saros 10R status and control."""

from __future__ import annotations

import webbrowser
from contextlib import asynccontextmanager
from typing import Annotated

import uvicorn
from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse
from pydantic import BaseModel

import typer

from .client import CleanRoute, FanSpeed, MopMode, VacuumClient, WaterFlow
from . import scheduler

# ---------------------------------------------------------------------------
# App state
# ---------------------------------------------------------------------------

_client: VacuumClient | None = None


@asynccontextmanager
async def _lifespan(app: FastAPI):
    global _client
    scheduler.init_db()
    _client = VacuumClient()
    await _client.authenticate()
    rooms = await _client.get_rooms()
    await scheduler.sync_rooms(rooms)
    try:
        yield
    finally:
        if _client:
            await _client.close()
            _client = None


app = FastAPI(title="Vacuum Dashboard", lifespan=_lifespan)


def _get_client() -> VacuumClient:
    if _client is None:
        raise HTTPException(status_code=503, detail="Vacuum client not ready")
    return _client


# ---------------------------------------------------------------------------
# API endpoints
# ---------------------------------------------------------------------------


@app.get("/api/status")
async def api_status():
    s = await _get_client().get_status()
    return s.as_dict()


@app.get("/api/rooms")
async def api_rooms():
    rooms = await _get_client().get_rooms()
    return [{"id": r.id, "name": r.name} for r in rooms]


@app.get("/api/routines")
async def api_routines():
    routines = await _get_client().get_routines()
    return [r.name for r in routines]


@app.get("/api/consumables")
async def api_consumables():
    try:
        c = await _get_client().get_consumables()
        return c.as_dict()
    except Exception as e:
        return {"error": str(e)}


@app.get("/api/history")
async def api_history():
    try:
        records = await _get_client().get_clean_history(limit=10)
        return [r.as_dict() for r in records]
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


@app.get("/api/settings")
async def api_settings_get():
    s = await _get_client().get_current_settings()
    return s.as_dict()


class SettingsRequest(BaseModel):
    fan_speed: str | None = None
    mop_mode: str | None = None
    water_flow: str | None = None


@app.post("/api/settings")
async def api_settings_post(body: SettingsRequest):
    client = _get_client()
    fan_speed, mop_mode, water_flow, _ = _parse_settings(body.model_dump(exclude_none=False))
    if fan_speed is not None:
        await client.set_fan_speed(fan_speed)
    if mop_mode is not None:
        await client.set_mop_mode(mop_mode)
    if water_flow is not None:
        await client.set_water_flow(water_flow)
    return {"ok": True}


class StartCleanRequest(BaseModel):
    fan_speed: str | None = None
    mop_mode: str | None = None
    water_flow: str | None = None
    route: str | None = None


@app.post("/api/action/{name}")
async def api_action(name: str, body: StartCleanRequest | None = None):
    if name == "start":
        data = body.model_dump() if body else {}
        fan_speed, mop_mode, water_flow, route = _parse_settings(data)
        await _get_client().start_clean(fan_speed=fan_speed, mop_mode=mop_mode, water_flow=water_flow, route=route)
        # Log whole-home clean if water_flow is present
        if body and body.water_flow:
            mode = "both" if body.water_flow != "OFF" else "vacuum"
            rows = await scheduler.get_schedule()
            all_ids = [r.segment_id for r in rows]
            if all_ids:
                await scheduler.log_clean(all_ids, mode, source="dashboard")
        return {"ok": True}
    if name not in _ACTIONS:
        raise HTTPException(status_code=404, detail=f"Unknown action '{name}'. Valid: start, {list(_ACTIONS)}")
    await _ACTIONS[name](_get_client())
    return {"ok": True}


@app.post("/api/consumables/reset/{attribute}")
async def api_consumables_reset(attribute: str):
    try:
        await _get_client().reset_consumable(attribute)
        return {"ok": True}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/api/routine/{name}")
async def api_routine(name: str):
    await _get_client().run_routine(name)
    return {"ok": True}


class RoomsCleanRequest(BaseModel):
    segment_ids: list[int]
    repeat: int = 1
    fan_speed: str | None = None
    mop_mode: str | None = None
    water_flow: str | None = None
    route: str | None = None


@app.post("/api/rooms/clean")
async def api_rooms_clean(body: RoomsCleanRequest):
    fan_speed, mop_mode, water_flow, route = _parse_settings(body.model_dump())
    await _get_client().clean_rooms(
        body.segment_ids, repeat=body.repeat,
        fan_speed=fan_speed, mop_mode=mop_mode, water_flow=water_flow, route=route,
    )
    mode = "both" if (body.water_flow and body.water_flow != "OFF") else "vacuum"
    await scheduler.log_clean(body.segment_ids, mode, source="dashboard")
    return {"ok": True}


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


@app.patch("/api/schedule/rooms/{segment_id}")
async def api_schedule_room_patch(segment_id: int, body: ScheduleRoomPatch):
    if "vacuum_days" in body.model_fields_set:
        await scheduler.set_room_interval(segment_id, "vacuum", body.vacuum_days)
    if "mop_days" in body.model_fields_set:
        await scheduler.set_room_interval(segment_id, "mop", body.mop_days)
    if "notes" in body.model_fields_set:
        await scheduler.set_room_notes(segment_id, body.notes)
    return {"ok": True}


# ---------------------------------------------------------------------------
# Frontend HTML
# ---------------------------------------------------------------------------

_HTML = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
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
    padding: 20px;
  }
  header {
    display: flex;
    align-items: center;
    gap: 12px;
    margin-bottom: 24px;
  }
  header h1 { font-size: 20px; font-weight: 600; }
  header .refresh-info { color: var(--muted); font-size: 12px; margin-left: auto; }
  .grid {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(340px, 1fr));
    gap: 16px;
  }
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
  /* Schedule panel */
  .schedule-table { width: 100%; border-collapse: collapse; font-size: 13px; }
  .schedule-table th { text-align: left; color: var(--muted); font-weight: 500; padding: 4px 8px 8px 0; font-size: 12px; }
  .schedule-table td { padding: 7px 8px 7px 0; border-bottom: 1px solid var(--border); vertical-align: middle; }
  .schedule-table tr:last-child td { border-bottom: none; }
  .overdue-cell { color: var(--red); font-weight: 600; }
  .warning-cell { color: var(--yellow); font-weight: 600; }
  .dim-cell { color: var(--muted); }
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

<div class="grid">

  <!-- Status Panel -->
  <div class="panel">
    <div class="panel-title">Status</div>
    <div id="status-content" class="loading">Loading…</div>
    <div class="last-updated" id="status-updated"></div>
  </div>

  <!-- Actions Panel -->
  <div class="panel">
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

  <!-- Rooms Panel -->
  <div class="panel">
    <div class="panel-title">Rooms</div>
    <div id="rooms-content" class="loading">Loading…</div>
  </div>

  <!-- Room Clean Panel -->
  <div class="panel">
    <div class="panel-title">Clean Rooms</div>
    <div id="room-check-list" class="checkbox-list loading">Loading…</div>
    <div class="form-row">
      <label>Repeat:</label>
      <input type="number" id="repeat-count" value="1" min="1" max="3">
      <button class="btn btn-primary" onclick="cleanRooms()">Clean Selected</button>
    </div>
    <div style="margin-top:12px">
      <div style="font-size:11px;color:var(--muted);margin-bottom:8px">Override settings (optional)</div>
      <div class="settings-grid">
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
          <select id="rooms-water-flow"><option value="">— device default —</option><option>OFF</option><option>LOW</option><option>MEDIUM</option><option>HIGH</option><option>EXTREME</option></select>
        </div>
        <div class="settings-row">
          <span class="settings-label">Route</span>
          <select id="rooms-route"><option value="">— device default —</option><option>STANDARD</option><option>FAST</option><option>DEEP</option><option>DEEP_PLUS</option></select>
        </div>
      </div>
    </div>
    <div class="feedback" id="rooms-clean-feedback"></div>
  </div>

  <!-- Clean Settings Panel -->
  <div class="panel">
    <div class="panel-title">Clean Settings</div>
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
  <div class="panel" style="grid-column: 1/-1; min-width: 0;">
    <div class="panel-title">Cleaning Schedule</div>
    <div id="schedule-content" class="loading">Loading…</div>
  </div>

  <!-- Routines Panel -->
  <div class="panel">
    <div class="panel-title">Routines</div>
    <div id="routines-content" class="loading">Loading…</div>
    <div class="feedback" id="routine-feedback"></div>
  </div>

  <!-- Consumables Panel -->
  <div class="panel">
    <div class="panel-title">Consumables</div>
    <div id="consumables-content" class="loading">Loading…</div>
  </div>

  <!-- Clean History Panel -->
  <div class="panel" style="grid-column: 1/-1; min-width: 0;">
    <div class="panel-title">Clean History (last 10)</div>
    <div id="history-content" class="loading">Loading…</div>
  </div>

</div>

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
      <label>Notes (optional)</label>
      <input type="text" id="edit-notes" placeholder="e.g. Pets sleep here, prioritize">
    </div>
    <div class="modal-actions">
      <button class="btn btn-neutral" onclick="closeEditModal()">Cancel</button>
      <button class="btn btn-primary" onclick="saveEditModal()">Save</button>
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
  const el = document.getElementById('rooms-content');
  const checkEl = document.getElementById('room-check-list');
  try {
    _rooms = await fetch('/api/rooms').then(r => r.json());
    if (!_rooms.length) {
      el.innerHTML = '<span class="unavailable">No rooms found.</span>';
      checkEl.innerHTML = '<span class="unavailable">No rooms found.</span>';
      return;
    }
    el.innerHTML = `<table>
      <tr><th>ID</th><th>Name</th></tr>
      ${_rooms.map(r => `<tr><td>${r.id}</td><td>${r.name}</td></tr>`).join('')}
    </table>`;
    checkEl.className = 'checkbox-list';
    checkEl.innerHTML = _rooms.map(r =>
      `<label><input type="checkbox" value="${r.id}"> ${r.name}</label>`
    ).join('');
  } catch(e) {
    el.innerHTML = `<span class="unavailable">Error: ${e.message}</span>`;
    checkEl.innerHTML = `<span class="unavailable">Error: ${e.message}</span>`;
  }
}

async function cleanRooms() {
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
  const btn = event.target;
  btn.disabled = true;
  try {
    const res = await apiPost('/api/rooms/clean', body);
    setFeedback('rooms-clean-feedback', res.ok ? 'Cleaning started!' : (res.detail || 'Error'), !res.ok);
  } catch(e) {
    setFeedback('rooms-clean-feedback', e.message, true);
  } finally {
    btn.disabled = false;
  }
}

// ------------------------------------------------------------------ routines
async function loadRoutines() {
  const el = document.getElementById('routines-content');
  try {
    const routines = await fetch('/api/routines').then(r => r.json());
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

// ------------------------------------------------------------------ settings
async function loadSettings() {
  try {
    const s = await fetch('/api/settings').then(r => r.json());
    populateSelect('set-fan-speed',  ['QUIET','BALANCED','TURBO','MAX','MAX_PLUS','OFF','SMART'], s.fan_speed);
    populateSelect('set-mop-mode',   ['STANDARD','FAST','DEEP','DEEP_PLUS','SMART'], s.mop_mode);
    populateSelect('set-water-flow', ['OFF','LOW','MEDIUM','HIGH','EXTREME','SMART'], s.water_flow);
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
    el.innerHTML = `<table>
      <tr><th>Start</th><th>Duration</th><th>Area (m²)</th><th>Complete</th><th>Started by</th><th>Type</th><th>Finish reason</th></tr>
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
        return `<tr><td>${dt}</td><td>${dur}</td><td>${area}</td><td>${done}</td><td>${startType}</td><td>${cleanType}</td><td>${reason}</td></tr>`;
      }).join('')}
    </table>`;
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
      <table class="schedule-table">
        <tr>
          <th>Room</th>
          <th>Last Vacuumed</th>
          <th>Last Mopped</th>
          <th>Vacuum Due</th>
          <th>Mop Due</th>
          <th>Vacuum Every</th>
          <th>Mop Every</th>
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

          return `<tr>
            <td><strong>${r.name}</strong></td>
            <td>${lv}</td>
            <td>${lm}</td>
            <td>${vDueHtml}</td>
            <td>${mDueHtml}</td>
            <td>${vInterval}</td>
            <td>${mInterval}</td>
            <td><button class="btn btn-neutral btn-sm" onclick="openEditModal(${r.segment_id}, '${r.name}', ${r.vacuum_days || 'null'}, ${r.mop_days || 'null'}, ${JSON.stringify(r.notes || '')})">Edit</button></td>
          </tr>`;
        }).join('')}
      </table>`;
    el.innerHTML = html;
  } catch(e) {
    el.innerHTML = `<span class="unavailable">Unavailable: ${e.message}</span>`;
  }
}

// ------------------------------------------------------------------ schedule edit modal
let _editSegmentId = null;

function openEditModal(segmentId, name, vacuumDays, mopDays, notes) {
  _editSegmentId = segmentId;
  document.getElementById('edit-modal-title').textContent = name;
  document.getElementById('edit-vacuum-days').value = vacuumDays ?? '';
  document.getElementById('edit-mop-days').value    = mopDays ?? '';
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
  const body = {};
  body.vacuum_days = vd !== '' ? parseFloat(vd) : null;
  body.mop_days    = md !== '' ? parseFloat(md) : null;
  body.notes       = nt || null;
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

// ------------------------------------------------------------------ refresh
function refreshAll() {
  loadStatus();
  loadRooms();
  loadRoutines();
  loadConsumables();
  loadHistory();
  loadSettings();
  loadSchedule();
}

// Initial load + auto-refresh
refreshAll();
setInterval(refreshAll, 30000);
</script>
</body>
</html>"""


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
