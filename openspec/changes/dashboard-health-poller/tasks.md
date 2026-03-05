## 1. Stale Cache Infrastructure

- [x] 1.1 Add `_stale_cache: dict[str, object]` module-level dict alongside `_cache`
- [x] 1.2 Update `_cached()`: on successful fetch, write to `_stale_cache[key]` in addition to `_cache`
- [x] 1.3 Update `_cached()`: on fetch exception, check `_stale_cache` and return `{**data, "_stale": True}` if present; otherwise re-raise
- [x] 1.4 Update `_maybe_reconnect()`: clear `_stale_cache` alongside `_cache` on successful reconnect

## 2. Background Health Poller

- [x] 2.1 Add `_last_contact: float | None = None` and `_reconnect_count: int = 0` module-level vars; increment `_reconnect_count` in `_maybe_reconnect()` on success
- [x] 2.2 Implement `async def _health_poll_loop()`: infinite loop with 60s sleep, calls `_fetch_status()`, updates `_last_contact` on success, calls `_record_failure()` / `_maybe_reconnect()` on failure; suppresses all exceptions
- [x] 2.3 Start `_health_poll_loop()` as a background task in `_lifespan` after authenticate; cancel and await it on shutdown

## 3. Health Endpoint

- [x] 3.1 Add `GET /api/health` endpoint returning `{ok, last_contact_seconds_ago, reconnect_count}`; `ok` is true if `last_contact` within 120s or never-polled-yet but no failures

## 4. JS — Stale Indicator

- [x] 4.1 In `loadStatus()`, detect `d._stale` and add CSS class `stale` to the status panel header
- [x] 4.2 In `loadRooms()`, `loadRoutines()`, `loadConsumables()`, `loadHistory()`, `loadSettings()` — detect `_stale` on response object and mark panel header with `stale` class
- [x] 4.3 Add CSS for `.stale` panel header: reduced opacity, small clock icon (unicode `⏱`) prepended to title
- [x] 4.4 Add `loadHealth()` function: fetches `/api/health`, shows connectivity banner if `ok === false` ("`⚠ Device unreachable — last contact X ago`"), removes banner if `ok === true`
- [x] 4.5 Add `loadHealth()` to `refreshAll()` stagger sequence and call it on initial load
