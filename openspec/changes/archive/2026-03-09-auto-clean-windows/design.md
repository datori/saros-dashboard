## Context

The vacuum project has a scheduler (`scheduler.py`) with per-room interval tracking, overdue ratio computation, and a `plan_clean()` function that selects rooms by overdue ratio within a time budget. The dashboard (`dashboard.py`) has a health poller that polls device status every 60s, a caching layer, and auto-reconnect logic. Clean events are logged at dispatch time with a `complete` column that is never actually set, and `_get_last_cleaned()` doesn't filter on it.

The user wants to automate cleaning based on real-life activity triggers ("I'm going to the gym") rather than fixed schedules. Each trigger opens a time window during which the system should dispatch cleans for the most urgent rooms that fit the budget.

## Goals / Non-Goals

**Goals:**
- Time-window-based auto-dispatch: triggers open windows, system cleans autonomously while window is open
- Priority-based room selection using composite score (room weight × type weight × overdue ratio)
- Accurate completion tracking: only successful cleans count toward "last cleaned"
- Time-based partial credit for interrupted multi-room batches
- Anti-triggers to immediately close windows and dock the vacuum
- Trigger budget tracking for future tuning

**Non-Goals:**
- Automatic trigger firing (geofence, calendar, presence detection) — triggers are manually fired via API/dashboard/MCP
- Automatic budget tuning — system logs actuals but user adjusts budgets manually
- Automatic frequency tuning — user adjusts room intervals manually
- Per-room triggering — all dispatch decisions are centralized through the priority queue
- Room adjacency optimization — small living space makes transit time (~30-60s) negligible

## Decisions

### 1. Window model: single active window with extending end time

The system tracks a single `_window_end` timestamp (or `None` when no window is active). When a trigger fires, `_window_end = max(_window_end or 0, now + budget)`. When an anti-trigger fires, `_window_end = now` and the vacuum is docked.

**Why not multiple concurrent windows?** Unnecessary complexity. The only thing that matters is "until when is cleaning allowed?" — a single timestamp captures this regardless of how many triggers contributed.

### 2. Dispatch loop integrated into health poller

The existing `_health_poll_loop()` runs every 60s and already polls device status. Extend it to also check: (a) is a window open? (b) is the vacuum idle/docked? (c) are there overdue rooms? If all three are true, dispatch a batch.

**Why not a separate dispatch loop?** The health poller already has the status polling cadence and the lifespan management. Adding window-check logic to it avoids a second concurrent loop competing for device commands.

**Polling interval**: 60s is acceptable. Worst case, a trigger opens a window and the dispatch happens up to 60s later. For human activities like "going to the gym," this latency is imperceptible.

### 3. Priority score: `room_weight × type_weight × overdue_ratio`

Each room has a `priority_weight` (default 1.0, stored in `room_schedules`). Clean types have fixed weights: vacuum=1.5, mop=1.0. The score is multiplicative.

**Why multiplicative?** A room that is 10× overdue should dominate regardless of its base weight. Multiplicative scoring preserves the relative ordering: a high-priority room at 1.1× overdue still beats a low-priority room at 1.5× overdue (if weights are calibrated), but a low-priority room at 10× overdue will eventually surface.

**Why not additive?** Additive (`weight + ratio`) makes the weight dominate at low overdue ratios and become irrelevant at high ones. Multiplicative keeps the weight as a consistent scaling factor.

### 4. Batch rooms in a single `clean_rooms()` call

Rooms are dispatched as a single batch rather than one at a time. This avoids return-to-dock overhead between rooms. The dispatch order in the `segment_ids` list is assumed to match the vacuum's execution order.

**Trade-off**: Coarser completion tracking. Mitigated by time-based inference for interrupted cleans.

### 5. Time-based partial credit for interrupted batches

When a multi-room clean is interrupted, compute cumulative expected duration per room in dispatch order. Credit rooms whose cumulative milestone ≤ actual elapsed time. Single-room cleans are binary (complete or not).

Example: rooms [A(8min), B(12min), C(6min)] interrupted at 19min. Cumulative: A=8, B=20, C=26. Only A (8 ≤ 19) gets credit.

**Assumption**: Room cleaning order matches `segment_ids` dispatch order. If wrong, worst case is mis-attribution of credit — correctable by updating the ordering logic later.

### 6. Completion monitoring via state transitions

After dispatching a clean, the health poller tracks the active clean event. State transitions:
- `sweeping`/`mopping` → clean is running, record `started_at`
- `charging`/`charging_complete` → clean succeeded, mark all rooms complete
- `error` or `idle` after running → clean failed, apply partial credit by elapsed time
- No state change for 5 minutes after dispatch → mark as failed (dispatch didn't take)

The `_active_clean` module-level variable tracks `{event_id, segment_ids, dispatched_at, started_at, per_room_estimates}`.

### 7. Database: extend existing tables + two new tables

New tables: `triggers` (name, budget, mode) and `trigger_events` (history for tuning).
Extended: `room_schedules` gains `priority_weight REAL DEFAULT 1.0`. `clean_events` gains `started_at`, `finished_at`, `trigger_name`.

All in the existing `vacuum_schedule.db`. No new database files.

### 8. `_get_last_cleaned()` filters on `complete = 1`

This is a correctness fix. The existing `complete` column and `update_clean_duration()` function are already in place — they just aren't used. Adding `AND e.complete = 1` to the query and ensuring the completion monitor calls `update_clean_duration()` closes the loop.

**Migration**: Existing `clean_events` rows all have `complete = 0` (the default). After this change, all historical cleans will stop counting as "last cleaned," which will make every room appear maximally overdue. This is actually correct — we have no proof those cleans completed. On the first window-based clean cycle, rooms will be re-credited with verified completion data.

## Risks / Trade-offs

- **60s poll latency for dispatch**: A trigger opens a window but the clean doesn't start for up to 60s. Acceptable for the use case, but means very short windows (< 2 min) may waste time on latency. → Mitigation: document minimum useful window size; consider reducing poll interval to 30s if needed.

- **State transition missed between polls**: If the vacuum completes a room clean between two 60s polls, we might not catch the intermediate state. → Mitigation: we only care about terminal states (charging = success, error = failure). Intermediate states are nice-to-have for `started_at` but not critical.

- **Partial credit mis-attribution**: If room execution order doesn't match dispatch order, the wrong rooms get credit. → Mitigation: assume dispatch order is correct (likely), revisit if empirically wrong. Under-crediting is safer than over-crediting (room just gets cleaned again sooner).

- **Historical data reset**: All existing `clean_events` become non-complete, making all rooms appear overdue. → Mitigation: this is actually the correct state given we can't verify past completions. The system self-corrects after one cleaning cycle. Optionally, a one-time migration could mark historical events as complete if desired.

- **Anti-trigger during multi-room clean**: Calling `return_to_dock()` mid-clean interrupts the batch. Partial credit applies. → Acceptable: the user explicitly chose to stop cleaning.
