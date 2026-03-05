## 1. Response Cache Infrastructure

- [x] 1.1 Add `_cache: dict[str, tuple[float, any]]` module-level dict and `_cache_locks: dict[str, asyncio.Lock]` in `dashboard.py`
- [x] 1.2 Implement `async def _cached(key: str, ttl: float, fn)` helper: check cache, acquire per-key lock, double-check on miss, call `fn()`, store result with timestamp
- [x] 1.3 Add `_cache_invalidate(*keys: str)` helper that deletes named entries from `_cache`

## 2. Wrap GET Endpoints with Cache

- [x] 2.1 Wrap `/api/status` — key `"status"`, TTL 5s
- [x] 2.2 Wrap `/api/rooms` — key `"rooms"`, TTL 5s
- [x] 2.3 Wrap `/api/routines` — key `"routines"`, TTL 5s
- [x] 2.4 Wrap `/api/consumables` — key `"consumables"`, TTL 5s
- [x] 2.5 Wrap `/api/history` — key `"history"`, TTL 5s
- [x] 2.6 Wrap `/api/settings` — key `"settings"`, TTL 5s

## 3. Cache Invalidation on Writes

- [x] 3.1 Call `_cache_invalidate("status")` after successful `POST /api/action/{name}`
- [x] 3.2 Call `_cache_invalidate("settings")` after successful `POST /api/settings`
- [x] 3.3 Call `_cache_invalidate("status")` after successful `POST /api/rooms/clean`

## 4. Stagger JS refreshAll()

- [x] 4.1 Replace simultaneous loader calls in `refreshAll()` with `setTimeout(fn, i * 300)` staggering (0ms, 300ms, 600ms, … for each loader)
