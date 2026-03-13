## Why

The dashboard's auto-reconnect (`_maybe_reconnect`) tears down and recreates the entire `VacuumClient` after 3 failures, but python-roborock v4.17.2 now has its own built-in `HealthManager` that restarts just the MQTT session after 3 timeouts. These two mechanisms race each other, and the dashboard's heavy approach (full re-auth, new MQTT connection) is often unnecessary. Additionally, when MQTT is disconnected, every dashboard panel hangs for 10 seconds waiting for a timeout instead of immediately returning stale data. A command semaphore and broader cache warming would further reduce user-visible failures.

## What Changes

- **Check `is_connected` before sending commands**: Before issuing any device command, check `device.is_connected`. For reads, return stale data immediately. For writes, fail fast with 503 instead of hanging for 10 seconds.
- **Tiered reconnect strategy**: After 3 failures, first check if the library's own reconnect is working (wait up to 60s). Only do a full `VacuumClient` recreation as a last resort.
- **Command semaphore**: Limit concurrent MQTT commands to 2 via `asyncio.Semaphore`. Prevents command pile-up during degraded connectivity (7 concurrent 10s timeouts = 70s of wall-clock pain).
- **Broader cache warming**: Expand the health poller to warm `settings` and `consumables` caches (in addition to `status`), with 2s spacing between commands and early abort on failure.

## Capabilities

### New Capabilities

- `connectivity-gate`: Pre-flight connectivity check that short-circuits device commands when MQTT is disconnected, returning stale data for reads and fast 503 for writes.
- `command-concurrency-control`: Semaphore limiting concurrent MQTT commands to prevent pile-up and cascading timeouts.

### Modified Capabilities

- `dashboard-response-cache`: Health poller warms additional cache keys (settings, consumables) beyond just status. Reconnect strategy is tiered — library self-heal first, full recreation as fallback.

## Impact

- **Code**: `dashboard.py` — `_maybe_reconnect()` rewrite, new `_connectivity_gate()` wrapper, `_command_semaphore`, expanded `_health_poll_loop()`
- **Dependencies**: No new dependencies; uses existing `device.is_connected` from python-roborock
- **Behavior**: Dashboard becomes more responsive during outages (instant stale data instead of 10s hangs). Reconnect is less disruptive (lighter-weight when library self-heals).
