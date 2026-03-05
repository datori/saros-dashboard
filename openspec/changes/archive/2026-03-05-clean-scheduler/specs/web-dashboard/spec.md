## ADDED Requirements

### Requirement: Schedule panel in dashboard UI
The system SHALL display a "Schedule" panel showing per-room cleaning status, overdue indicators, and interval configuration.

#### Scenario: Panel loads with schedule data
- **WHEN** the dashboard loads
- **THEN** the schedule panel SHALL show a table with columns: Room, Last Vacuumed, Last Mopped, Vacuum Due, Mop Due, and an edit button for intervals

#### Scenario: Overdue rooms highlighted
- **WHEN** a room's overdue ratio ≥ 1.0
- **THEN** the corresponding cell SHALL be visually highlighted (e.g., red/orange) to indicate it is past due

#### Scenario: Never-cleaned rooms indicated
- **WHEN** a room has an interval configured but no clean events on record
- **THEN** the Last Vacuumed / Last Mopped cell SHALL display "Never" with an overdue indicator

#### Scenario: Unscheduled rooms shown
- **WHEN** a room has no interval configured
- **THEN** it SHALL appear in the table with "—" for interval and due date, without overdue styling

#### Scenario: Schedule unavailable
- **WHEN** the schedule API call fails
- **THEN** the panel SHALL display "Unavailable" gracefully without crashing other panels

### Requirement: Inline interval editing
The system SHALL allow editing a room's vacuum and mop intervals directly in the schedule panel.

#### Scenario: Edit interval
- **WHEN** the user clicks the edit button for a room and submits new vacuum_days or mop_days values
- **THEN** the dashboard SHALL POST to `/api/schedule/rooms/{segment_id}` and refresh the schedule panel on success

#### Scenario: Clear interval
- **WHEN** the user clears the interval field and saves
- **THEN** the room's interval SHALL be set to null and it SHALL no longer appear in overdue calculations

### Requirement: Dashboard schedule API endpoints
The system SHALL expose REST API endpoints for schedule state and configuration.

#### Scenario: GET /api/schedule
- **WHEN** GET `/api/schedule` is called
- **THEN** the response SHALL return a JSON array of room schedule objects: `{segment_id, name, vacuum_days, mop_days, last_vacuumed, last_mopped, vacuum_overdue_ratio, mop_overdue_ratio, notes}`

#### Scenario: PATCH /api/schedule/rooms/{segment_id}
- **WHEN** PATCH `/api/schedule/rooms/{segment_id}` is called with `{vacuum_days?, mop_days?, notes?}`
- **THEN** the specified fields SHALL be updated in the scheduler and `{ok: true}` returned

#### Scenario: Room sync on startup
- **WHEN** the dashboard server starts
- **THEN** it SHALL call `sync_rooms()` to ensure all device rooms are present in the scheduler database

### Requirement: Auto-log cleans dispatched from dashboard
The system SHALL record a clean event in the scheduler whenever a clean is dispatched via the dashboard.

#### Scenario: Room clean logged on dispatch
- **WHEN** `POST /api/rooms/clean` is called with segment_ids and succeeds
- **THEN** `scheduler.log_clean(segment_ids, mode, source="dashboard")` SHALL be called before returning the response

#### Scenario: Mode inferred from water_flow
- **WHEN** the dispatch request includes `water_flow` set to a non-OFF value
- **THEN** the logged mode SHALL be `"both"` (vacuum + mop)

#### Scenario: Mode defaults to vacuum
- **WHEN** the dispatch request does not include `water_flow` or sets it to `OFF`
- **THEN** the logged mode SHALL be `"vacuum"`
