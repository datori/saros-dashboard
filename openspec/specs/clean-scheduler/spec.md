## ADDED Requirements

### Requirement: Room schedule configuration
The system SHALL store per-room cleaning intervals (vacuum and mop separately) in a local SQLite database.

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

### Requirement: Room sync from device
The system SHALL populate and refresh room names from the VacuumClient device API.

#### Scenario: Initial sync
- **WHEN** `sync_rooms(rooms)` is called with a list of Room objects
- **THEN** each room SHALL be upserted into `room_schedules` with its segment_id and name, preserving existing interval configuration

#### Scenario: Name refresh
- **WHEN** a room is renamed in the Roborock app and `sync_rooms()` is called
- **THEN** the name SHALL be updated without changing `vacuum_days` or `mop_days`

### Requirement: Clean event logging
The system SHALL log a clean event when a room clean is dispatched.

#### Scenario: Log dispatched vacuum clean
- **WHEN** `log_clean(segment_ids=[1, 4], mode="vacuum", source="dashboard")` is called
- **THEN** a `clean_events` row SHALL be inserted with `dispatched_at=now()` and `clean_event_rooms` rows for each segment_id

#### Scenario: Log dispatched mop+vacuum clean
- **WHEN** `log_clean(segment_ids=[1], mode="both", source="mcp")` is called
- **THEN** the event SHALL be stored with `mode="both"`, giving that room credit for both vacuum and mop intervals

#### Scenario: Log with duration (post-hoc)
- **WHEN** `update_clean_duration(event_id, duration_sec=1800, area_m2=42.5)` is called
- **THEN** the event SHALL be updated with the provided duration and area values

### Requirement: Overdue ratio computation
The system SHALL compute an overdue ratio for each room that has a configured interval.

#### Scenario: Not yet due
- **WHEN** a room was last vacuumed 1 day ago with a 3-day interval
- **THEN** its vacuum overdue ratio SHALL be approximately 0.33

#### Scenario: Exactly due
- **WHEN** a room was last vacuumed exactly 3 days ago with a 3-day interval
- **THEN** its vacuum overdue ratio SHALL be 1.0

#### Scenario: Overdue
- **WHEN** a room was last vacuumed 6 days ago with a 3-day interval
- **THEN** its vacuum overdue ratio SHALL be 2.0

#### Scenario: Never cleaned
- **WHEN** a room has a configured interval but no clean event on record
- **THEN** its overdue ratio SHALL be treated as infinity (highest priority)

#### Scenario: No interval configured
- **WHEN** a room has `vacuum_days = NULL`
- **THEN** it SHALL be excluded from overdue calculations and schedule queries

### Requirement: Run-time estimation
The system SHALL estimate how long cleaning a given set of rooms will take based on historical data.

#### Scenario: Exact match available
- **WHEN** `estimate_duration(segment_ids=[1, 4])` is called and ≥2 past events with exactly those rooms exist
- **THEN** the estimate SHALL be the average `duration_sec` of those events

#### Scenario: Per-room decomposition
- **WHEN** no exact match exists but single-room history is available for each room
- **THEN** the estimate SHALL be the sum of per-room averages plus a fixed 300-second overhead

#### Scenario: Area-based fallback
- **WHEN** neither exact match nor per-room history is available
- **THEN** the estimate SHALL use `total_area_m2 × 150 sec/m²` + 300s overhead if area data exists, otherwise return `None`

### Requirement: Time-budget planning
The system SHALL select an optimal set of overdue rooms that fits within a given time budget.

#### Scenario: Plan within budget
- **WHEN** `plan_clean(max_minutes=45, mode="vacuum")` is called
- **THEN** the system SHALL return rooms sorted by overdue ratio (descending), greedily selected until adding the next room would exceed 45 minutes

#### Scenario: Most overdue first
- **WHEN** multiple rooms are overdue and not all fit in the budget
- **THEN** rooms with higher overdue ratio SHALL be selected over rooms with lower overdue ratio

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
- **THEN** the result SHALL include for each room: segment_id, name, vacuum_days, mop_days, last_vacuumed, last_mopped, vacuum_overdue_ratio, mop_overdue_ratio, notes

#### Scenario: Rooms without schedule
- **WHEN** `get_schedule()` is called and some rooms have NULL intervals
- **THEN** those rooms SHALL be included with NULL ratio fields and clearly marked as unscheduled
