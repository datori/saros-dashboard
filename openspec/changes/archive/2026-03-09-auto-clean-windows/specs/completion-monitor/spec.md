## ADDED Requirements

### Requirement: Active clean tracking
The system SHALL track the currently active clean event for completion monitoring.

#### Scenario: Clean dispatched
- **WHEN** a clean is dispatched via the auto-clean system or manually via the dashboard
- **THEN** the system SHALL store the active clean context: event_id, segment_ids (in dispatch order), dispatched_at, and per-room duration estimates

#### Scenario: No active clean
- **WHEN** no clean has been dispatched or the last clean has been resolved
- **THEN** `_active_clean` SHALL be `None`

### Requirement: State-based completion detection
The system SHALL detect clean completion or failure by monitoring vacuum state transitions.

#### Scenario: Successful completion
- **WHEN** the vacuum state transitions to `charging` or `charging_complete` after a clean was dispatched
- **THEN** the clean event SHALL be marked as complete with `complete=1`, `finished_at=now()`, and `duration_sec` computed from `started_at` to now

#### Scenario: Clean started
- **WHEN** the vacuum state transitions to `sweeping` or `mopping` after dispatch
- **THEN** `started_at` SHALL be recorded on the clean event

#### Scenario: Error state
- **WHEN** the vacuum state transitions to an error state after a clean was dispatched and started
- **THEN** the clean event SHALL be marked as failed and partial credit SHALL be applied

#### Scenario: Dispatch timeout
- **WHEN** 5 minutes elapse after dispatch without the vacuum entering a cleaning state
- **THEN** the clean event SHALL be marked as failed with no rooms credited

#### Scenario: Idle after cleaning
- **WHEN** the vacuum transitions to `idle` after being in a cleaning state
- **THEN** this SHALL be treated the same as an error — partial credit applied based on elapsed time

### Requirement: Full completion credit
The system SHALL credit all rooms in a batch when the clean completes successfully.

#### Scenario: All rooms credited
- **WHEN** a multi-room clean completes successfully (state → charging)
- **THEN** `update_clean_duration()` SHALL be called with `complete=1`, and ALL rooms in the batch SHALL count toward "last cleaned"

### Requirement: Time-based partial credit
The system SHALL credit rooms proportionally when a multi-room clean is interrupted.

#### Scenario: Partial completion by elapsed time
- **WHEN** rooms [A(8min), B(12min), C(6min)] are dispatched and the clean is interrupted at 19 minutes elapsed
- **THEN** cumulative milestones are A=8, B=20, C=26; only room A (8 ≤ 19) SHALL be credited as complete

#### Scenario: No rooms completed
- **WHEN** a 3-room clean is interrupted at 3 minutes (before the first room's estimated completion)
- **THEN** no rooms SHALL be credited

#### Scenario: Single room interrupted
- **WHEN** a single-room clean is interrupted before completion
- **THEN** the room SHALL NOT be credited (binary: complete or not)

#### Scenario: Unknown per-room estimates
- **WHEN** per-room duration estimates are unavailable for an interrupted clean
- **THEN** no rooms SHALL be credited (conservative fallback)

### Requirement: Completion-gated overdue calculation
The system SHALL only count completed clean events when computing overdue ratios.

#### Scenario: Incomplete clean ignored
- **WHEN** a clean event has `complete = 0`
- **THEN** it SHALL NOT be considered when computing `_get_last_cleaned()` for any room

#### Scenario: Completed clean counted
- **WHEN** a clean event has `complete = 1`
- **THEN** its `dispatched_at` SHALL be used as the "last cleaned" timestamp for credited rooms

#### Scenario: Partially credited multi-room clean
- **WHEN** a multi-room clean is interrupted and rooms A and B are credited but C is not
- **THEN** a new clean event SHALL be created for the credited rooms with `complete = 1`, and the original event SHALL remain with `complete = 0`
