## Context

The dashboard `refreshAll()` fires 7 `fetch()` calls simultaneously (no `await` between them). Each maps to a FastAPI endpoint that calls the VacuumClient, which sends an MQTT RPC command through a single persistent connection to Roborock's cloud. The python-roborock RPC layer has a hard 10-second timeout per command and no retry or queue — when 7 arrive at once, they saturate the MQTT broker and cascade-timeout.

The VacuumClient and python-roborock internals are third-party and not safe to modify. All changes are confined to `dashboard.py`.

## Goals / Non-Goals

**Goals:**
- Eliminate mass timeout cascades by reducing simultaneous MQTT commands
- Return cached data instantly for rapid repeat calls (< 5s apart)
- Spread JS refresh bursts to avoid hitting the MQTT broker simultaneously
- Invalidate cache after write actions so data stays reasonably fresh

**Non-Goals:**
- Persistent cache (memory-only, reset on server restart)
- Fixing the MQTT timeout value or retry behavior in python-roborock
- Adding a semaphore/lock to serialize all MQTT calls (would serialize unnecessarily slow the happy path)
- Caching write/action endpoints

## Decisions

### D1: Simple dict-based TTL cache, not a library

A `dict[str, (timestamp, data)]` in module scope is sufficient. The cache key is the endpoint name (e.g. `"status"`, `"rooms"`). No external dependency needed. `asyncio.Lock` per key prevents a cache stampede (two requests arriving simultaneously both missing cache and both firing MQTT).

Alternative: `cachetools`, `aiocache` — rejected; adds dependency for trivial logic.

### D2: TTL = 5 seconds

Matches the expected MQTT round-trip time under normal conditions. Prevents any two of the 7 panel loads from issuing the same MQTT command. On the 30-second auto-refresh cycle, all data is always stale by then so first caller refreshes.

Alternative: 10s, 30s — 30s would mean stale data after actions; 10s still allows duplicates if requests spread > 5s apart but is safer.

### D3: Explicit cache invalidation after write actions

After any POST that changes device state (settings, action, rooms/clean), call `_cache_invalidate("status")` and `_cache_invalidate("settings")` as appropriate. Prevents the user from clicking "Start" and seeing stale "charging" status.

### D4: JS stagger via sequential `setTimeout` delays

Each loader in `refreshAll()` is called with a `setTimeout(fn, i * 300)` offset (0ms, 300ms, 600ms, …). This spreads 7 calls over ~1.8 seconds, ensuring no more than 1–2 MQTT commands are in-flight at a time.

Alternative: Await each fetch before starting the next (fully serial) — too slow; page would take 7+ seconds to fully render. The stagger + cache combo is better: first call hits MQTT, subsequent calls hit cache.

## Risks / Trade-offs

- **Stale cache for 5s after an action**: If the user clicks "Dock" and immediately looks at status, they may briefly see the old state. Mitigation: invalidate relevant cache keys on every write action.
- **Cache stampede on cold start**: First page load still fires 7 concurrent requests, all missing cold cache. Mitigation: stagger (D4) ensures they arrive 300ms apart; the first one populates cache before the second arrives, so at most 1–2 real MQTT calls per endpoint per refresh.
- **Memory**: Cache holds at most ~6 entries of small JSON dicts. Negligible.

## Migration Plan

No migration needed. Cache is in-memory and transparent. Old behavior is preserved when cache is cold (first load). No schema, config, or API changes.
