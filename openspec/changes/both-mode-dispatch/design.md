## Context

The dashboard's auto-dispatch system uses a priority queue to decide which rooms to clean when a window is open. Triggers store a `mode` field ("vacuum" or "mop") but it is never passed to `_check_dispatch()` — the dispatch mode is determined entirely by `queue[0].mode`, the highest-priority entry in the queue. This means the trigger's intended mode is silently ignored.

Additionally, the user runs combined vac+mop cleans manually (`water_flow=VAC_THEN_MOP`, logged as `mode="both"`), but auto-dispatch has no equivalent. The scheduler's credit query already handles `mode="both"` (`OR e.mode = 'both'`), so the bookkeeping layer is ready; only the dispatch path needs wiring.

## Goals / Non-Goals

**Goals:**
- Wire trigger mode through to `_check_dispatch()` so the trigger's intent is respected
- Add `"both"` as a valid trigger mode that selects mop-overdue rooms and gives dual credit
- Add a `"both"` row to `dispatch_settings` with sensible defaults
- Expose `"both"` in the trigger UI and dispatch settings panel

**Non-Goals:**
- Changing how manual (non-trigger) dispatches from the dashboard work
- Adding a separate "vacuum then mop" sequencing mode (two separate passes)
- Changing the priority scoring algorithm

## Decisions

### Decision: Store window mode in a `_window_mode` global

`_open_window()` already manages `_window_end` as a module-level monotonic timestamp. Adding `_window_mode: str | None = None` alongside it is the minimal change — no new data structures, no DB round-trips in the dispatch hot path.

**Alternative considered**: Query the most recently fired trigger each dispatch cycle to get its mode. Rejected: adds a DB call per health-poll cycle and fails for manually-opened windows (`POST /api/window/open`).

### Decision: "both" room selection = mop-overdue pool

When `_window_mode == "both"`, `_check_dispatch()` filters the priority queue to entries where `entry.mode == "mop"`. This gives the same room selection as a mop dispatch, with the vacuum benefit as a bonus.

**Alternative considered**: Union (vacuum OR mop overdue). Rejected: a room that only needs vacuuming shouldn't trigger a full mop pass. The user stated "for mopping we run both" — mopping is the intent.

**Alternative considered**: Intersection (vacuum AND mop overdue). Rejected: overly restrictive; rooms rarely hit both thresholds simultaneously.

### Decision: `_window_mode` follows the most recent `_open_window()` call

If two triggers fire in sequence (e.g., "gym" then "dinner"), the second call to `_open_window()` sets `_window_mode` to the newer trigger's mode. This is consistent with how `_window_end` already takes the max of the two budgets — the window reflects the combined state of all fired triggers.

**Alternative considered**: Keep the mode from the first trigger that opened the window. Rejected: less predictable for the user; the last-fired trigger is the most recent signal.

### Decision: Seed "both" defaults as `fan_speed=balanced, mop_mode=standard, water_flow=vac_then_mop`

`VAC_THEN_MOP` water flow is the natural match for a combined pass. `fan_speed=balanced` (not OFF, not TURBO) is a reasonable default that works alongside mopping. These can be overridden by the user in the UI.

## Risks / Trade-offs

- **Window mode reset on restart**: `_window_mode` is in-memory. If the dashboard restarts while a window is open, the mode is lost and `_check_dispatch()` falls back to `queue[0].mode` (existing behaviour). Low impact — window state is already lost on restart.
- **`api_window_open` mode parameter is optional**: manual window opens via `POST /api/window/open` accept an optional `mode`; if omitted, `_window_mode` defaults to `"vacuum"` (preserving existing behaviour for callers that don't send mode).
