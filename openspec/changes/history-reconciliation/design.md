## Context

The completion monitor in `dashboard.py` uses a state machine (`_check_active_clean`) that watches vacuum state transitions every 60s to detect clean completion. It requires seeing a `CLEANING_STATES` transition before recognizing `SUCCESS_STATES` as completion. This breaks when:

1. The vacuum encounters an error mid-clean — monitor clears `_active_clean`, so completion is never detected
2. The 60s poll misses short cleans entirely — monitor never sees the cleaning state
3. The dashboard restarts mid-clean — `_active_clean` is lost (in-memory only)

The device itself maintains authoritative clean history via `get_clean_history()`, which returns timestamped records with duration, area, and completion status.

## Goals / Non-Goals

**Goals:**
- Rooms get credit when the device reports a clean completed, regardless of state transitions observed
- Survive error/recovery cycles, missed polls, and dashboard restarts
- Keep UI responsiveness: "cleaning in progress" feedback, double-dispatch prevention

**Non-Goals:**
- Room-level attribution from device history (device doesn't report which rooms per job — we trust our dispatch records)
- Retroactive reconciliation of cleans that happened before this system existed
- Changing the 60s health poll interval

## Decisions

### 1. Reconcile by timestamp correlation

**Decision**: Match scheduler `clean_events` to device history by comparing `dispatched_at` against device record `start_time` within a ±10 minute window.

**Why**: The device history doesn't include a correlation ID or room list — timestamp is the only linkable field. 10 minutes covers dispatch-to-start delay plus clock skew.

**Alternative considered**: Track device history record IDs before/after dispatch to detect new entries. Rejected — adds complexity and still requires timestamp-based fallback for dashboard restarts.

### 2. Demote `_active_clean` to UI/guard role

**Decision**: Keep `_active_clean` for (a) showing "cleaning in progress" in the dashboard and (b) preventing double-dispatch in `_check_dispatch`. Remove all completion-credit logic from state monitoring.

**Why**: The state machine is inherently fragile with 60s polling. Separating UI feedback from credit assignment means each can fail independently without data loss.

### 3. Reconciliation runs in the health poll loop

**Decision**: Add a reconciliation step to `_health_poll_loop` that runs every poll (60s). It queries unreconciled events from the DB and fetches device history once per poll.

**Why**: The health poll already runs on a 60s cycle and has access to the client. Adding one `get_clean_history()` call is one extra MQTT round-trip — acceptable given the 60s interval.

**Optimization**: Only fetch device history if there are unreconciled events (events with `complete = 0` dispatched within the last 2 hours).

### 4. Keep `_active_clean` state monitoring for UX, with relaxed rules

**Decision**: Still monitor state transitions for `_active_clean`, but:
- On error state: log it, but do NOT clear `_active_clean` — let the reconciler handle credit
- On success state (charging): clear `_active_clean` (UI cleanup) but do NOT mark the event complete — let the reconciler handle credit
- On dispatch timeout (5 min): clear `_active_clean` for UI but do NOT mark the event as failed

**Why**: The reconciler is the single source of truth for credit. The state monitor only manages UI state.

### 5. Reconciliation marks events with device data

**Decision**: When a match is found, copy device-reported `duration_seconds`, `area_m2`, and `complete` to the scheduler event. If the device reports `complete=True`, mark our event `complete=1`. If the device reports `complete=False`, mark our event with `complete=0` and actual duration/area (no credit, but data preserved).

**Why**: The device is authoritative. Its `complete` flag accounts for error recovery, manual intervention, and partial runs.

### 6. Staleness cutoff for unreconciled events

**Decision**: Events older than 2 hours with `complete=0` are considered abandoned — skip them in reconciliation. They can be manually reconciled if needed.

**Why**: Prevents accumulating stale events that slow down queries. 2 hours is generous given most cleans are <1 hour.

## Risks / Trade-offs

- **Timestamp correlation isn't perfect** → Mitigation: 10-minute window is generous. If multiple dispatches happen within 10 minutes (unlikely given window dispatch logic), take the closest match.
- **One extra MQTT call per health poll** → Mitigation: Only fetch history when unreconciled events exist. Cached like other calls.
- **Device history has no room-level data** → Mitigation: Trust dispatch records. If we dispatched rooms [1,3,7] and the device completed a clean at that time, those rooms were cleaned. For partial cleans (device `complete=False`), no credit — conservative but correct.
- **Dashboard restart loses `_active_clean`** → This is now fine: credit comes from reconciliation, not from `_active_clean`. The reconciler will pick up the unreconciled event on restart.
