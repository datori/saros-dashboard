## Why

The scheduler knows which rooms are overdue but nothing acts on that knowledge — a human must check the dashboard and manually trigger cleans. Additionally, clean events are credited at dispatch time regardless of whether the clean actually completes, making overdue ratios unreliable. This change adds a time-window-based auto-cleaning system with priority scoring, and fixes completion tracking so only successful cleans count.

## What Changes

- **Time windows**: Named triggers (e.g. "gym", "shower", "leaving") open cleaning windows with configurable time budgets. Anti-triggers close windows immediately and dock the vacuum. Multiple triggers extend the window to the latest end time. While a window is open and rooms need cleaning, the system dispatches batched cleans automatically.
- **Priority scoring**: Rooms are ranked by a composite score combining room priority weight, clean type weight (vacuum > mop), and overdue ratio. Only rooms with overdue_ratio >= 1.0 enter the queue. The highest-scoring rooms that fit the remaining window are batched and dispatched.
- **Completion monitoring**: The health poller monitors vacuum state transitions after dispatch. Successful cleans (state → charging) credit all rooms. Failed/interrupted cleans use time-based inference to credit rooms whose cumulative estimated duration fits within actual elapsed time. Only completed rooms update the "last cleaned" timestamp used for overdue calculations.
- **Completion tracking fix**: `_get_last_cleaned()` now filters on `complete = 1` instead of counting dispatched-but-incomplete cleans.
- **Trigger budget tuning**: Trigger events log actual durations so users can compare configured budgets against real absence times and adjust.

## Capabilities

### New Capabilities

- `clean-triggers`: Named triggers and anti-triggers that open/close time windows for automated cleaning. Stored in SQLite with configurable budgets and mode preferences.
- `clean-windows`: Time-window dispatch loop that monitors for open windows, selects rooms by priority, dispatches batched cleans, and re-dispatches when a clean completes with window time remaining.
- `priority-scoring`: Composite room scoring combining room weight, clean type weight, and overdue ratio for determining dispatch order.
- `completion-monitor`: State-based completion tracking that monitors vacuum status after dispatch, credits rooms on success, and uses time-based inference for partial credit on interrupted multi-room cleans.

### Modified Capabilities

- `clean-scheduler`: `_get_last_cleaned()` filters on `complete = 1`. Room schedules gain a `priority_weight` column. Overdue ratios only reflect successfully completed cleans.

## Impact

- **Code**: `scheduler.py` (new tables, priority scoring, completion logic), `dashboard.py` (trigger API endpoints, window dispatch loop integrated with health poller, completion monitor), `client.py` (possibly expose state codes for monitoring)
- **API**: New endpoints: `POST /api/trigger/{name}`, `DELETE /api/trigger` (anti-trigger), `GET /api/triggers`, `PATCH /api/triggers/{name}`. New fields on schedule responses.
- **DB**: New tables `triggers`, `trigger_events`. New columns on `room_schedules` (`priority_weight`) and `clean_events` (`started_at`, `finished_at`, `trigger_name`).
- **Behavior**: Rooms are no longer credited as cleaned until the clean actually completes. Existing `clean_events` with `complete = 0` will stop counting toward "last cleaned" timestamps.
