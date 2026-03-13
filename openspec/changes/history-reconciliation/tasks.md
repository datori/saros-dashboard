## 1. Scheduler: unreconciled events query

- [x] 1.1 Add `get_unreconciled_events()` to `scheduler.py` — returns `clean_events` with `complete = 0` and `dispatched_at` within last 2 hours, including associated `segment_ids`
- [x] 1.2 Add `reconcile_event(event_id, duration_sec, area_m2, complete)` to `scheduler.py` — updates an event with device-reported data

## 2. Dashboard: reconciliation loop

- [x] 2.1 Add `_reconcile_clean_events()` async function to `dashboard.py` — fetches device history, matches against unreconciled events by timestamp (±10 min window, closest match), calls `reconcile_event()` for matches
- [x] 2.2 Integrate `_reconcile_clean_events()` into `_health_poll_loop()` — call after `_check_active_clean`, only when unreconciled events exist

## 3. Dashboard: demote `_active_clean` to UI-only

- [x] 3.1 Modify `_check_active_clean()` — on success states (`charging`, `charging_complete`): clear `_active_clean` but do NOT mark event complete
- [x] 3.2 Modify `_check_active_clean()` — on error states: do NOT clear `_active_clean` (let vacuum recover; reconciler handles credit)
- [x] 3.3 Modify `_check_active_clean()` — on dispatch timeout: clear `_active_clean` for UI but do NOT mark event as failed
- [x] 3.4 Modify `_check_active_clean()` — on idle state: clear `_active_clean` for UI but do NOT mark event as failed
- [x] 3.5 Remove `_resolve_clean_success()` and `_resolve_clean_failure()` — credit logic replaced by reconciler
- [x] 3.6 Simplify `ActiveClean` dataclass — remove `per_room_estimates` and `started_at` fields (no longer needed for credit)
