## Why

The dashboard fires 7 concurrent MQTT requests on every page load and 30-second refresh cycle. The Roborock cloud MQTT broker cannot handle simultaneous commands from a single client — requests queue and all hit the 10-second hard timeout, producing mass "Command timed out after 10.0s" failures across every panel.

## What Changes

- Add a per-endpoint in-process response cache (5-second TTL) in `dashboard.py` so repeated calls within a refresh window return cached data instead of issuing new MQTT commands
- Stagger `refreshAll()` in the frontend JS to spread loader invocations ~300 ms apart, reducing burst pressure on the MQTT connection
- Cache covers all read endpoints: `/api/status`, `/api/rooms`, `/api/routines`, `/api/consumables`, `/api/history`, `/api/settings`
- Cache is invalidated automatically on TTL expiry and explicitly after any write (POST) action

## Capabilities

### New Capabilities

- `dashboard-response-cache`: Per-endpoint async response cache with TTL and explicit invalidation, embedded in the dashboard server

### Modified Capabilities

- `web-dashboard`: Auto-refresh behavior changes — reads are served from cache within TTL; JS refresh is staggered

## Impact

- `src/vacuum/dashboard.py`: Cache layer + staggered JS only; no changes to `client.py`, `scheduler.py`, or MCP server
- No new dependencies — uses stdlib `asyncio` and `time`
- All existing API contracts unchanged; cache is transparent to callers
