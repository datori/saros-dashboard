## Context

The dashboard in `dashboard.py` has three resilience mechanisms: response cache with stale fallback, auto-reconnect after consecutive failures, and a health poller. These work well but have small gaps identified during a connectivity deep-dive against python-roborock v4.17.2.

All changes are confined to `dashboard.py` and are low-risk, independent fixes.

## Goals / Non-Goals

**Goals:**
- Preserve stale cache across reconnects so fallback data survives outages
- Make write-action failures visible to the reconnect mechanism
- Give operators enough health data to diagnose connectivity issues

**Non-Goals:**
- Changing the reconnect strategy itself (that's the `smarter-reconnect` change)
- Modifying `client.py` or the python-roborock library
- Changing frontend behavior (the new health fields are available but JS updates are optional)

## Decisions

### Decision 1: Remove `_stale_cache.clear()` from `_maybe_reconnect()`

**Choice**: Only clear `_cache` (hot cache) on reconnect. Preserve `_stale_cache`.

**Rationale**: `_stale_cache` exists specifically to serve data when the device is unreachable. Clearing it on reconnect means that if the reconnect itself fails (common during cloud outages), users see raw errors instead of the last-known-good data. The hot cache clear is correct — it forces fresh fetches against the new client.

**Alternative considered**: Clear stale cache only on successful reconnect. Rejected — even after a successful reconnect, the stale data is harmless and serves as insurance if the new connection fails quickly.

### Decision 2: Wrap POST endpoints with failure tracking via a helper

**Choice**: Create an `async def _tracked_action(fn)` helper that calls `fn()`, then calls `_record_success()` on success or `_record_failure()` + optional reconnect on failure. POST endpoints use this wrapper.

**Rationale**: POST endpoints bypass `_cached()` (correctly — actions shouldn't be cached), but this means their failures are invisible to the reconnect mechanism. A helper avoids duplicating the try/except/record pattern in every endpoint.

**Alternative considered**: Move failure tracking into `VacuumClient` itself. Rejected — failure tracking is a dashboard concern, not a client concern. The client should stay a thin wrapper.

### Decision 3: Expose library-level connection state in `/api/health`

**Choice**: Access `_client._device.is_connected` (the python-roborock property) and expose it alongside existing health fields.

**Rationale**: This tells operators whether the MQTT session is actually alive vs. whether we've had a recent successful command. These are different — the session can be connected but commands fail (device offline), or the session can be reconnecting but our last command was recent (stale cache hiding the issue).

**Alternative considered**: Expose the library's `HealthManager` internals (consecutive timeout count, last restart time). Rejected — those are private implementation details that could change across library versions. `is_connected` is a stable public property.

## Risks / Trade-offs

- **[Risk] Accessing `_client._device`** — This reaches into VacuumClient internals. → Mitigation: Add a `@property` on VacuumClient (e.g., `is_connected`) that delegates to `self._device.is_connected`, keeping the access clean.
- **[Risk] Write failure tracking could trigger premature reconnect** — A burst of write failures (e.g., user spam-clicking start) could push the failure counter past threshold. → Mitigation: The existing `_reconnect_lock` prevents concurrent reconnects, and `_maybe_reconnect()` double-checks the counter inside the lock.
