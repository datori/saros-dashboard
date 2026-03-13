## MODIFIED Requirements

### Requirement: Active clean tracking
The system SHALL track the currently active clean event for UI feedback and double-dispatch prevention only.

#### Scenario: Clean dispatched
- **WHEN** a clean is dispatched via the auto-clean system or manually via the dashboard
- **THEN** the system SHALL store the active clean context: event_id, segment_ids, dispatched_at, and mode

#### Scenario: No active clean
- **WHEN** no clean has been dispatched or the last clean has been resolved
- **THEN** `_active_clean` SHALL be `None`

### Requirement: State-based completion detection
The system SHALL monitor vacuum state transitions for UI feedback, but SHALL NOT use them to determine clean credit.

#### Scenario: Successful completion detected
- **WHEN** the vacuum state transitions to `charging` or `charging_complete` while `_active_clean` is set
- **THEN** `_active_clean` SHALL be cleared (UI cleanup) but the clean event SHALL NOT be marked complete — reconciliation handles credit

#### Scenario: Error state detected
- **WHEN** the vacuum state transitions to an error state while `_active_clean` is set
- **THEN** `_active_clean` SHALL NOT be cleared — the vacuum may recover and complete the clean; reconciliation handles credit

#### Scenario: Dispatch timeout
- **WHEN** 5 minutes elapse after dispatch without the vacuum entering a cleaning state
- **THEN** `_active_clean` SHALL be cleared (UI cleanup) but the clean event SHALL NOT be marked as failed — reconciliation handles credit

#### Scenario: Idle after cleaning
- **WHEN** the vacuum transitions to `idle` while `_active_clean` is set
- **THEN** `_active_clean` SHALL be cleared (UI cleanup) but the clean event SHALL NOT be marked as failed — reconciliation handles credit

## REMOVED Requirements

### Requirement: Full completion credit
**Reason**: Completion credit is now determined by the history reconciliation system, not by the state-based completion monitor.
**Migration**: `_resolve_clean_success()` no longer calls `update_clean_duration()`. The reconciler marks events complete when device history confirms it.

### Requirement: Time-based partial credit
**Reason**: Partial credit logic based on elapsed time and per-room estimates is removed. The device's own `complete` flag is authoritative — if the device says incomplete, no rooms get credit.
**Migration**: `_resolve_clean_failure()` and its partial credit logic are removed. The reconciler uses device history `complete` status directly.
