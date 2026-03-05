## Context

The dashboard's VacuumClient is a long-lived singleton. The MQTT connection degrades silently over time (python-roborock reconnect bug), and the cloud broker is intermittently unreachable. Current mitigations (auto-reconnect after 3 failures, 5s cache) are reactive — the user sees errors before recovery kicks in. The goal is to detect and recover from connectivity problems proactively, and to keep the UI informative rather than blank during outages.

## Goals / Non-Goals

**Goals:**
- Poll the device in the background so failures are detected before the next JS refresh cycle
- Warm the response cache proactively so page load/refresh costs fewer MQTT round-trips
- Return stale data with a visual indicator rather than error messages during transient outages
- Show per-panel "last updated" timestamps so users know data freshness at a glance

**Non-Goals:**
- Polling all 6 endpoints in the background (only `status` — it's the most volatile; others are polled lazily by JS with the stale fallback)
- Changing the 30s JS refresh interval
- Persistent cache across server restarts

## Decisions

### D1: Poll status only, every 60 seconds

Polling all 6 endpoints in the background would double MQTT load. Status is the most time-sensitive; rooms, routines, and settings rarely change. The 5s hot cache plus the new stale fallback handles the rest. 60s interval is fast enough to detect session degradation before the 30s JS cycle, without being aggressive.

### D2: Two-tier cache: hot (5s TTL) + stale (indefinite, last-known-good)

```
_cache        = {key: (timestamp, data)}   # existing hot cache, 5s TTL
_stale_cache  = {key: data}                # new: last successful response, no expiry
```

When `_cached()` catches a fetch exception, it checks `_stale_cache` and returns `{**data, "_stale": True}` if available. This means panels show real data (visually dimmed) instead of "Error: timed out" during connectivity blips.

Stale cache is cleared on reconnect (same as hot cache) to avoid serving pre-failure data after a fresh connection.

### D3: `_last_contact` timestamp for UI display

A module-level `_last_contact: float | None` (monotonic timestamp) is updated on every successful device call (not just the poller). The `GET /api/health` endpoint exposes `{last_contact_seconds_ago, reconnect_count, status}` so the JS can show "last updated 47s ago" without coupling it to specific panel data.

### D4: JS stale indicator — subtle, not alarming

When any panel receives `_stale: true` in its data, it adds a `title="Stale data"` attribute and a CSS class that slightly dims the panel header and adds a small clock icon. No modal, no banner — the data is still useful. A global banner appears only if `last_contact_seconds_ago > 120` (2 min without contact).

Alternative: Red "OFFLINE" banner — rejected as too alarming for a transient blip.

## Risks / Trade-offs

- **Stale data misread as current**: A user might not notice the stale indicator and act on outdated status. Mitigation: the "last updated X ago" timestamp in every panel header is always visible, not just on errors.
- **Poller fires during active clean**: The poller calls `get_status()` every 60s, which is one extra MQTT command. The cache means JS calls within 5s of the poll hit cache for free. Acceptable overhead.
- **Stale cache grows unbounded**: Only 6 keys (one per endpoint), each a small JSON dict. Negligible.

## Migration Plan

Additive change — no existing behavior removed. The stale fallback is invisible when the device is healthy. The poller is a background task that starts with the lifespan and stops on shutdown.
