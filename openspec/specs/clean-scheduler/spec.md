## MODIFIED Requirements

### Requirement: Room schedule configuration
The system SHALL store per-room cleaning intervals (vacuum and mop separately) in a local SQLite database. Each room SHALL also have a configurable `priority_weight` (default 1.0) used for priority scoring.

#### Scenario: Set vacuum interval
- **WHEN** `set_room_interval(segment_id, mode="vacuum", days=3.0)` is called
- **THEN** the room's `vacuum_days` SHALL be updated to `3.0` in the database

#### Scenario: Set mop interval
- **WHEN** `set_room_interval(segment_id, mode="mop", days=7.0)` is called
- **THEN** the room's `mop_days` SHALL be updated to `7.0` in the database

#### Scenario: Clear interval
- **WHEN** `set_room_interval(segment_id, mode="vacuum", days=None)` is called
- **THEN** `vacuum_days` SHALL be set to NULL and the room SHALL be excluded from overdue calculations

#### Scenario: Set room notes
- **WHEN** `set_room_notes(segment_id, "pets sleep here")` is called
- **THEN** the note SHALL be persisted and returned in schedule queries

#### Scenario: Set room priority weight
- **WHEN** `set_room_priority(segment_id, weight=1.5)` is called
- **THEN** the room's `priority_weight` SHALL be updated to 1.5

### Requirement: Overdue ratio computation
The system SHALL compute an overdue ratio for each room that has a configured interval, based only on completed clean events. Due-ness SHALL be quantized to the local calendar day: if a clean becomes due at any time on the current local date, the room SHALL be treated as due for the full day.

#### Scenario: Not yet due
- **WHEN** a room was last successfully cleaned 1 day ago with a 3-day interval
- **THEN** its vacuum overdue ratio SHALL be approximately 0.33

#### Scenario: Exactly due
- **WHEN** a room was last successfully cleaned exactly 3 days ago with a 3-day interval
- **THEN** its vacuum overdue ratio SHALL be 1.0

#### Scenario: Due later today counts as due now
- **WHEN** a room's exact due timestamp falls later on the current local calendar day
- **THEN** its overdue ratio SHALL be treated as at least `1.0`
- **AND** the room SHALL be included in overdue queries, planning, and auto-window dispatch before the exact due timestamp arrives

#### Scenario: Overdue
- **WHEN** a room was last successfully cleaned 6 days ago with a 3-day interval
- **THEN** its vacuum overdue ratio SHALL be 2.0

#### Scenario: Never cleaned
- **WHEN** a room has a configured interval but no completed clean event on record
- **THEN** its overdue ratio SHALL be treated as infinity (highest priority)

#### Scenario: No interval configured
- **WHEN** a room has `vacuum_days = NULL`
- **THEN** it SHALL be excluded from overdue calculations and schedule queries

#### Scenario: Incomplete clean ignored
- **WHEN** a room's most recent clean event has `complete = 0`
- **THEN** that event SHALL NOT count as the "last cleaned" timestamp; the system SHALL use the most recent event with `complete = 1`

### Requirement: Time-budget planning
The system SHALL select an optimal set of overdue rooms that fits within a given time budget, ranked by composite priority score instead of raw overdue ratio.

#### Scenario: Plan within budget
- **WHEN** `plan_clean(max_minutes=45, mode="vacuum")` is called
- **THEN** the system SHALL return rooms sorted by priority score (descending), greedily selected until adding the next room would exceed 45 minutes

#### Scenario: Most urgent first
- **WHEN** multiple rooms are overdue and not all fit in the budget
- **THEN** rooms with higher priority score SHALL be selected over rooms with lower priority score

#### Scenario: Never-cleaned rooms take priority
- **WHEN** some rooms have never been cleaned and have an interval configured
- **THEN** they SHALL be ranked above all rooms with a finite overdue ratio

#### Scenario: No rooms overdue
- **WHEN** all rooms with configured intervals are within their schedule
- **THEN** `plan_clean` SHALL return an empty room list with a note that nothing is overdue

#### Scenario: Unknown duration rooms
- **WHEN** a room's duration cannot be estimated
- **THEN** it SHALL be included in the plan with a `null` estimated_minutes and a warning

### Requirement: Schedule status query
The system SHALL provide a full schedule status view for all configured rooms.

#### Scenario: Full schedule returned
- **WHEN** `get_schedule()` is called
- **THEN** the result SHALL include for each room: segment_id, name, vacuum_days, mop_days, last_vacuumed, last_mopped, vacuum_overdue_ratio, mop_overdue_ratio, notes, priority_weight

#### Scenario: Rooms without schedule
- **WHEN** `get_schedule()` is called and some rooms have NULL intervals
- **THEN** those rooms SHALL be included with NULL ratio fields and clearly marked as unscheduled

### Requirement: Combined-mode credit for mop dispatches with fan speed
When the mop dispatch settings include a non-OFF fan speed, the robot physically vacuums and mops simultaneously. The system SHALL log such dispatches as `mode='both'` so that vacuum overdue ratios are also reset.

#### Scenario: Mop dispatch with fan speed credits vacuum
- **WHEN** a scheduled mop clean is dispatched via the auto-window
- **AND** the `mop` dispatch settings have `fan_speed` set to a non-OFF value
- **THEN** the clean event SHALL be logged with `mode='both'`
- **AND** `_get_last_cleaned(segment_id, 'vacuum')` SHALL return this event's timestamp

#### Scenario: Mop dispatch without fan speed credits only mop
- **WHEN** a scheduled mop clean is dispatched via the auto-window
- **AND** the `mop` dispatch settings have `fan_speed = 'off'` or no fan speed set
- **THEN** the clean event SHALL be logged with `mode='mop'`
- **AND** `_get_last_cleaned(segment_id, 'vacuum')` SHALL NOT return this event

#### Scenario: mode='both' satisfies both overdue queries
- **WHEN** a clean event exists with `mode='both'` and `complete=1`
- **THEN** `_get_last_cleaned(segment_id, 'vacuum')` SHALL return its timestamp
- **AND** `_get_last_cleaned(segment_id, 'mop')` SHALL return its timestamp
