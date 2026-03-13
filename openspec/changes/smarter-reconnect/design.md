## Context

The dashboard currently has a two-layer resilience approach:
1. **Library layer** (python-roborock v4.17.2): `HealthManager` restarts the MQTT session after 3 consecutive timeouts (30-min cooldown). `MqttSession._run_reconnect_loop()` handles exponential backoff.
2. **Dashboard layer**: `_maybe_reconnect()` destroys and recreates the entire `VacuumClient` (full re-auth, new MQTT session) after 3 failures.

These two mechanisms race each other. The dashboard's heavy approach often fires while the library is mid-recovery, tearing down a session that was about to self-heal. Meanwhile, when MQTT is disconnected, every dashboard panel hangs for 10 seconds per command timeout.

This change depends on `connectivity-quick-wins` being applied first (for the `is_connected` property and write failure tracking).

## Goals / Non-Goals

**Goals:**
- Eliminate 10-second UI hangs during MQTT disconnections
- Let the library's built-in reconnect handle transient failures
- Reserve full client recreation for persistent failures the library can't recover from
- Limit concurrent MQTT commands to prevent cascading timeouts
- Proactively warm more caches to reduce user-triggered device commands

**Non-Goals:**
- Implementing local API support (blocked on python-roborock Saros 10R fixes)
- Adding Matter support
- Changing the 10-second per-command timeout in python-roborock (library constant)
- Modifying python-roborock internals

## Decisions

### Decision 1: Connectivity gate — check `is_connected` before commands

**Choice**: Add an `_ensure_connected()` check before any device command. For reads (GET endpoints via `_cached`), if disconnected and stale data exists, return stale immediately. For writes (POST endpoints), raise `HTTPException(503)` immediately.

**Rationale**: The most impactful UX improvement. When MQTT is down, every panel currently waits 10 seconds for a timeout before showing an error. Checking `is_connected` first makes the dashboard feel responsive even during outages — stale data appears instantly with a "stale" indicator.

**Alternative considered**: Add timeouts shorter than 10s at the dashboard layer. Rejected — doesn't help if we can know the connection is down before even trying.

### Decision 2: Tiered reconnect — library-first, full recreation as fallback

**Choice**: Replace `_maybe_reconnect()` with a tiered approach:
1. After threshold failures, check `is_connected`
2. If connected AND `_last_contact` is recent (within 120s) → don't reconnect (errors are device-side, not connection-side)
3. If connected BUT `_last_contact` is stale (>120s ago) → treat as zombie connection, proceed to full recreation (step 5)
4. If disconnected → wait up to 60s for the library's own reconnect to succeed (poll `is_connected` every 5s)
5. If still disconnected after 60s → full `VacuumClient` recreation (current behavior)

**Rationale**: The library's `HealthManager` + `_run_reconnect_loop()` handle most transient MQTT drops. Full client recreation should be the exception, not the first response. The 60s wait aligns with the library's reconnect backoff (starts at 5s, grows to 900s).

The `_last_contact` freshness check (step 3) guards against zombie connections — sessions where MQTT reports `_healthy=True` but commands consistently time out. This can happen when the `HealthManager` successfully restarts the MQTT session but the new session is also non-functional, and the 30-minute `RESTART_COOLDOWN` prevents further restarts. Without this check, the dashboard would loop (reset counter → 3 more failures → reset counter → ...) for up to 30 minutes. The 120s threshold aligns with the existing health banner trigger.

**Alternative considered**: Remove dashboard-level reconnect entirely, rely on library. Rejected — the library's 30-minute HealthManager cooldown means it won't retry for 30 minutes if the first restart fails. Dashboard needs a fallback.

**Alternative considered**: Track "threshold resets" (number of times we reset because `is_connected=True`) and force recreation after N resets in M minutes. Rejected — `_last_contact` already captures the same signal more directly. If we're "connected" but no command has succeeded in 2 minutes, that's a zombie connection regardless of how many resets we've done.

### Decision 3: Command semaphore — limit to 2 concurrent MQTT commands

**Choice**: `asyncio.Semaphore(2)` wrapping all device commands (both reads via `_cached()` and writes).

**Rationale**: On page load, 8 loaders fire (staggered by 300ms but still overlapping). If MQTT is degraded, all 8 hit the 10s timeout — 80 seconds of wall-clock time. With a semaphore of 2, only 2 commands are in-flight at once. If the first 2 fail, the connectivity gate kicks in for the rest (returning stale data immediately).

The semaphore goes inside `_cached()` (around the `fn()` call) and inside the write-action wrapper, ensuring all device I/O is gated.

**Alternative considered**: Semaphore of 1 (fully serial). Rejected — too slow for healthy operation. Two concurrent commands is fine for the single MQTT channel and allows reasonable throughput.

### Decision 4: Broader cache warming in health poller

**Choice**: Expand `_health_poll_loop()` to warm `status`, `settings`, and `consumables` with 2s spacing. Abort the cycle on first failure (don't hammer a broken connection).

**Rationale**: `settings` and `consumables` change infrequently but are always fetched on page load. Pre-warming means most page loads hit cache. `rooms` and `routines` are excluded — they're essentially static and the 5s cache handles them fine. `history` is excluded — it's the most expensive call (fetches individual records) and the data changes only after cleans.

## Risks / Trade-offs

- **[Risk] 60s wait in tiered reconnect blocks the reconnect lock** — Other requests see `_reconnect_lock.locked()` and skip reconnect. → Mitigation: This is actually correct — we don't want multiple concurrent reconnect attempts. The 60s wait is bounded and the connectivity gate ensures users get stale data immediately, so the wait is invisible to users.
- **[Risk] Zombie connection — MQTT reports connected but commands time out** — The library's `HealthManager` has a 30-minute `RESTART_COOLDOWN`. If the HealthManager restarts the session but the new session is also broken, no further restarts occur for 30 minutes. During this window, `is_connected=True` but every command times out. → Mitigation: The `_last_contact` freshness check catches this. If no successful command in 120s despite being "connected", we bypass the library and force full recreation.
- **[Risk] Semaphore of 2 could bottleneck healthy operation** — If one command is slow (e.g., `get_clean_history` fetching 10 records sequentially), it holds a semaphore slot. → Mitigation: The 5s cache TTL means most requests are cache hits and don't acquire the semaphore. Only cache misses compete for slots.
- **[Risk] `is_connected` could be stale** — The property reflects the library's internal state which may lag behind actual MQTT state. → Mitigation: `is_connected` returns `MqttSession._healthy`, which is set to `False` immediately when the connection task fails or is cancelled. It's reliable for "definitely disconnected" even if it occasionally reports "connected" when the session is about to drop.
