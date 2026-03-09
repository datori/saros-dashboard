## Context

The auto-clean window system (implemented in `dashboard.py`) dispatches rooms based on priority scoring when a trigger fires and opens a time window. However, there's no way to preview what would be cleaned for a given budget, and opening a window requires a named trigger. Users want to see the priority queue visualized against a sliding time budget and open windows directly.

The existing `get_priority_queue()` in `scheduler.py` already returns all overdue rooms scored and sorted. The `_check_dispatch()` function in `dashboard.py` implements the greedy batch selection logic. The planner reuses this data without modifying the scheduler.

## Goals / Non-Goals

**Goals:**
- Dashboard panel with a budget slider that previews which rooms would be cleaned
- Client-side batch selection matching `_check_dispatch()` logic (mode grouping, greedy fill)
- Direct window opening from the planner without requiring a named trigger
- On-demand refresh (not polled) to keep it lightweight

**Non-Goals:**
- Multi-cycle prediction (what would happen across successive dispatches within one window) — too speculative since the queue changes after each clean
- Modifying the scheduler or priority scoring logic
- Real-time/auto-updating preview — on-demand refresh is sufficient

## Decisions

### 1. Single API endpoint returning the full priority queue

`GET /api/window/preview` returns the complete scored queue. The JS does batch selection client-side as the slider moves. This avoids a server round-trip on every slider tick.

**Why not server-side per-budget?** The slider should feel instant. The queue is small (7 rooms × 2 modes = 14 entries max) so client-side filtering is trivial.

### 2. Client-side batch selection mirrors `_check_dispatch()`

The JS implements the same greedy algorithm: pick mode from the top entry, iterate in score order, accumulate estimated time until budget exceeded. This keeps the preview honest about what would actually happen.

**Trade-off**: Duplicated logic between Python and JS. Acceptable because the algorithm is simple (< 15 lines) and the queue is pre-sorted by the server.

### 3. `POST /api/window/open` with `{budget_min}` body

A new endpoint that calls `_open_window(budget_min)` directly, without requiring a trigger name. The existing trigger-fire endpoint remains for trigger-based workflows.

**Why not reuse `POST /api/trigger/{name}/fire`?** That endpoint requires a pre-configured trigger with a name and budget. The planner's use case is ad-hoc: "open a 22-minute window right now."

### 4. Own panel in the dashboard, `data-tab="clean"`

The planner is operational (what would happen now), not configuration (what triggers exist). It belongs on the "clean" tab alongside rooms/clean and triggers, not on the "info" tab with schedules.

### 5. Slider range 5–90 minutes, default 30

5 minutes is roughly the minimum useful window (one small room). 90 minutes covers the whole apartment. Default at 30 gives a useful starting view.

### 6. Visual design: table with cumulative time bars

Rooms listed in priority order. Selected rooms (●) above a divider, excluded rooms (○) below. A cumulative bar per row shows budget fill. Summary line shows "N rooms, Xm of Ym budget."

## Risks / Trade-offs

- **JS/Python logic drift**: If batch selection logic changes in `_check_dispatch()`, the JS preview could diverge. → Mitigation: the algorithm is simple and unlikely to change; the preview is explicitly labeled as a preview, not a guarantee.
- **Stale preview**: The queue reflects the last refresh, not real-time. If a clean completes between refresh and opening the window, the actual dispatch may differ. → Mitigation: on-demand refresh button; preview is clearly a snapshot.
- **No mode toggle**: The preview shows the batch for the dominant mode (highest-priority entry's mode). Users can't preview "what if I forced mop mode." → Acceptable: matches actual dispatch behavior. Can add mode override later if needed.
