# Scheduler Reliability Plan

Concrete implementation plan for improving scheduler correctness under the current Roborock cloud API constraints.

## Goals

- Prevent obviously bad device-history entries from resetting room schedules
- Make reconciliation deterministic when multiple scheduler events happen close together
- Reduce repeated dispatch loops against unreachable rooms
- Preserve enough data to support future partial-credit work if the device order can be validated

## Priority Order

Ordered by impact first, then effort.

| Priority | Change | Impact | Effort | Concrete outcome |
|----------|--------|--------|--------|------------------|
| 1 | Add credit plausibility checks before marking a clean complete | High | Low | Short or zero-area "successes" no longer reset a room's schedule automatically |
| 2 | Make reconciliation one-to-one | High | Low | A single device-history row cannot satisfy multiple scheduler events |
| 3 | Add dispatch retry backoff for repeated failed auto-window attempts | High | Medium | The scheduler stops hammering the same room every poll cycle after a likely bad dispatch |
| 4 | Persist reconciliation metadata | Medium | Low | Scheduler records why an event was credited or rejected, making debugging and manual cleanup practical |
| 5 | Add manual admin override for credit / uncredit | Medium | Medium | Bad credits can be corrected without editing SQLite by hand |
| 6 | Persist room dispatch order in our own schema | Medium | Medium | Future partial-credit logic has stable room-order data even after restart |
| 7 | Investigate Roborock clean-sequence commands | Medium | Medium | Determine whether the device follows submitted room order or exposes a canonical order |
| 8 | Reintroduce partial-credit logic behind conservative guards | Medium | High | Interrupted multi-room jobs can credit completed rooms only when order is trustworthy |
| 9 | Improve trigger analytics if named triggers become primary | Low | Low | Trigger firings link clean events to budgets for tuning and reporting |

## Phase 1: Correctness Guardrails

These should happen first.

### 1. Plausibility filter for credited cleans

Before copying `complete=True` from device history into scheduler credit:

- Reject or flag runs with `area_m2 <= 0`
- Reject or flag runs with implausibly short duration
- Compare duration against `default_duration_sec` when available
- Store the reason a run was rejected or flagged

Suggested rule set:

- If `area_m2 <= 0`, do not auto-credit
- If a single-room run is under `max(120 sec, 0.25 * manual_estimate)`, do not auto-credit
- If a multi-room run is under `max(180 sec, 0.20 * summed_manual_estimate)`, do not auto-credit
- If no manual estimate exists, use conservative fixed minimums only

Implementation area:

- [dashboard.py](/home/openclaw/code/vacuum/src/vacuum/dashboard.py)
- [scheduler.py](/home/openclaw/code/vacuum/src/vacuum/scheduler.py)

### 2. One-to-one reconciliation

Current matching is nearest-history-record per event. It should become nearest-unmatched-history-record per event.

Implementation shape:

- Fetch candidate unreconciled events
- Fetch recent device history
- Match oldest event first
- Remove a history record from the candidate pool once matched
- Persist enough metadata to explain the match

Benefits:

- Prevents duplicate credit from one device-history entry
- Makes repeated-dispatch bursts much less dangerous

## Phase 2: Dispatch Stability

### 3. Retry backoff for likely failed dispatches

When the same room or room-set is dispatched repeatedly with very short unsuccessful runs:

- Add a cooldown on that room or room-set
- Skip it for one or more poll cycles
- Log why it was deferred

Suggested first pass:

- If the same room is dispatched twice within 10 minutes and both runs are uncredited with duration under 2 minutes, suppress auto-dispatch for that room for 15 minutes

Implementation area:

- [dashboard.py](/home/openclaw/code/vacuum/src/vacuum/dashboard.py)
- [scheduler.py](/home/openclaw/code/vacuum/src/vacuum/scheduler.py)

### 4. Persist reconciliation metadata

Add columns or a side table for:

- matched device-history timestamp or record key
- reconciliation status: `matched_complete`, `matched_rejected`, `matched_incomplete`, `unmatched`
- rejection reason, such as `zero_area` or `too_short`
- finish reason if available

Benefits:

- Makes bad scheduler state explainable
- Enables future UI surfacing of suspicious runs
- Supports manual override tooling

## Phase 3: Operator Controls

### 5. Manual credit override

Add a small admin surface for:

- mark clean event credited
- mark clean event uncredited
- optionally set a note or reason

Minimum viable surface:

- API endpoint first
- UI later if needed

Benefits:

- Lets you recover from weird Roborock history without direct DB edits

## Phase 4: Partial-Clean Foundations

### 6. Persist dispatch order

`clean_event_rooms` currently stores membership only. Add stable ordering:

- either `position INTEGER` on `clean_event_rooms`
- or a separate ordered table keyed by event and ordinal

This should store the exact order submitted to `clean_rooms()`.

### 7. Investigate clean sequence support

The installed `python-roborock` package exposes:

- `GET_CLEAN_SEQUENCE`
- `SET_CLEAN_SEQUENCE`

Questions to answer:

- Does the Saros 10R support these over the cloud path?
- Does `clean_order_mode=0` mean "use given order" or "use device order"?
- Can the current device order be queried?
- If device order differs from submitted order, which one wins?

Output of this step should be a short findings doc or code comments with a verified conclusion.

Current finding from physical testing on April 11, 2026:

- `GET_CLEAN_SEQUENCE` returned `[]`
- `GET_SEGMENT_STATUS` returned `[1]` both idle and during `segment_cleaning`
- Physical two-room tests did not follow the submitted `segments` order
- Observed cases:
  - submitted `Kitchen -> Hall`, robot entered `Hall` first
  - submitted `Hall -> Kitchen`, robot entered `Hall` first
  - submitted `Kitchen -> Closet`, robot entered `Closet` first
  - submitted `Closet -> Kitchen` as vacuum-only, robot entered `Closet` first

Interpretation:

- Submitted `APP_SEGMENT_CLEAN` room order is not trustworthy for scheduler credit
- The robot appears to prefer an internal/path-based order over submitted order
- Partial-credit logic must remain blocked unless a future API path exposes actual execution order

### 8. Partial credit, only if order is trustworthy

Only implement after steps 6 and 7.

Conservative version:

- single-room interrupted runs still get binary credit only
- multi-room interrupted runs can credit completed prefix rooms
- use stored dispatch order plus manual duration estimates
- require the credited prefix to clear a confidence threshold

Do not implement partial credit if room order remains unverified.

Given the April 11, 2026 physical test results, treat this work as blocked for now.

## Trigger Analytics

### 9. Trigger-event linking

This matters only if named triggers become the primary workflow again.

Changes:

- Link `trigger_events.clean_event_id` when a fired trigger causes a dispatch
- Do not log fake trigger analytics for raw `/api/window/open`
- Surface actual budget versus realized clean duration in reports

## Recommended Sequence

1. Plausibility filter
2. One-to-one reconciliation
3. Reconciliation metadata
4. Retry backoff
5. Manual override API
6. Dispatch-order persistence
7. Clean-sequence investigation
8. Partial credit, if justified
9. Trigger analytics polish

## Validation Checklist

- A short, zero-area device-history "success" does not reset a room schedule
- Two scheduler events near the same time do not both reconcile to one device-history entry
- Repeated failed dispatches to one room stop retrying every poll
- An operator can inspect why an event was or was not credited
- Dispatch order survives restart and is queryable from the DB
- Partial credit remains disabled unless room-order trust is established
