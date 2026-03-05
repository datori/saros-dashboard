## Context

The vacuum package already has a working `VacuumClient` with cloud API access. The dashboard is purely additive — a new FastAPI server module that reuses `VacuumClient` and serves a single-page HTML UI. No existing code changes except adding two methods to `VacuumClient` (`get_consumables`, `get_clean_history`).

The Saros 10R connects only via cloud (local API unimplemented). Each HTTP request to the dashboard triggers one or more cloud API calls, so latency per action is ~4–6s (MQTT connection setup). Auto-refresh must account for this.

## Goals / Non-Goals

**Goals:**
- Live dashboard showing all readable vacuum state in one view
- Buttons/forms for every supported action
- No JS build step — plain HTML/CSS/JS served from Python string or file
- Runs locally on demand (`vacuum-dashboard` CLI command, default port 8080)
- Accessible from anywhere on the local LAN (binds to `0.0.0.0`; startup prints LAN URL)

**Non-Goals:**
- Authentication / access control (trusted LAN use only — no internet exposure)
- WebSocket push / real-time streaming (too complex for initial version)
- Mobile-responsive design (desktop-first is fine)
- Persistent history storage (show what the API returns, don't add a DB)
- Production deployment / HTTPS

## Decisions

### Decision 1: FastAPI + uvicorn, no JS framework
**Choice:** FastAPI for the HTTP server, plain HTML/JS (no React/Vue/bundler).
**Rationale:** Fits the existing Python project. Zero build toolchain. FastAPI gives async handlers natively, which integrates cleanly with VacuumClient's async interface. Alternatives: Flask (sync), aiohttp (more boilerplate), Starlette directly (same as FastAPI minus conveniences).

### Decision 2: Single VacuumClient per server process via lifespan
**Choice:** One `VacuumClient` instance created at startup, held for the server lifetime (same pattern as MCP server).
**Rationale:** Each `VacuumClient` instantiation re-authenticates and re-connects. Holding one instance amortizes auth cost across all requests. Consistent with `mcp_server.py`.

### Decision 3: Inline HTML served from Python, not a separate static file
**Choice:** Serve the full HTML page as a Python string from `dashboard.py`.
**Rationale:** Keeps the module self-contained (single file, no `static/` directory). Easy to install with pip. Acceptable for a local dev tool. If the UI grows, can extract to a template file later.

### Decision 4: Polling for data refresh (not WebSockets)
**Choice:** Frontend JS polls `/api/status`, `/api/rooms`, etc. on a configurable interval (default 30s).
**Rationale:** Simpler than WebSockets. Cloud API latency (~5s) makes sub-second updates pointless anyway. 30s interval gives fresh data without hammering the Roborock rate limit.

### Decision 5: Consumables via `get_consumable` command
**Choice:** `RoborockCommand.GET_CONSUMABLE` returns brush/filter hours used; compute percentage against known lifespans.
**Rationale:** python-roborock exposes consumable data via `v1.consumable`. Known lifespans: main brush 300h, side brush 200h, filter 150h.

### Decision 6: Clean history via `GET_CLEAN_SUMMARY` + `GET_CLEAN_RECORD`
**Choice:** Call `GET_CLEAN_SUMMARY` for totals, then `GET_CLEAN_RECORD` for individual job records.
**Rationale:** Summary gives cumulative stats (total area, total time). Records give per-job detail. Show last 10 jobs in the dashboard.

## Risks / Trade-offs

- **Cloud rate limiting** → Mitigation: default 30s refresh interval; don't auto-refresh during active cleaning
- **Consumables API unverified on Saros 10R** → Mitigation: wrap in try/except, show "unavailable" if command fails
- **Clean history format may differ** → Mitigation: same — graceful degradation, log raw response for debugging
- **Long action latency (~5s)** → Mitigation: disable action buttons while request in flight; show spinner

## Open Questions

- Should consumables show raw hours or percentage? (Plan: percentage with raw hours as tooltip)
- Should the dashboard auto-open a browser tab on start? (Plan: yes, via `webbrowser.open`)
