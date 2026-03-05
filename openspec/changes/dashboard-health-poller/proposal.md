## Why

The dashboard currently reacts to device failures — panels show errors after 10-second timeouts, and the auto-reconnect fires only after 3 consecutive user-visible failures. A background health poller inverts this: it proactively checks device connectivity every 60 seconds, warms the cache before the JS refresh cycle fires, and triggers reconnect before users encounter errors. Additionally, when the cloud is temporarily unreachable, panels should show the last known good data with a staleness indicator rather than blank error messages.

## What Changes

- Add a background asyncio task in the dashboard lifespan that polls `get_status()` every 60 seconds
- On success: reset failure counter, store result in cache, update a "last contact" timestamp
- On failure: increment failure counter, trigger `_maybe_reconnect()` proactively
- Add a "stale cache" layer alongside the hot cache: stores the last successful response per endpoint indefinitely; returned with `_stale: true` when the live fetch fails
- JS updates: show "last updated X ago" in panel headers; show a subtle banner when data is stale

## Capabilities

### New Capabilities

- `dashboard-health-poller`: Background connectivity poller with proactive reconnect and stale-data fallback

### Modified Capabilities

- `web-dashboard`: Panel headers show last-updated timestamp; stale data indicated visually rather than showing error messages
- `dashboard-response-cache`: Extended with a stale-data fallback tier alongside the existing TTL cache

## Impact

- `src/vacuum/dashboard.py`: New background task, stale cache dict, JS changes to header/status display
- No changes to `client.py`, `scheduler.py`, MCP server, or CLI
- No new dependencies
