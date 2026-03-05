## ADDED Requirements

### Requirement: Dashboard visual theme
The dashboard SHALL use the GitHub Dark Dimmed color palette for its base background, surface, border, text, and muted colors.

#### Scenario: Background color
- **WHEN** the dashboard page is loaded
- **THEN** the page background SHALL be `#22272e`

#### Scenario: Card/surface color
- **WHEN** any card or panel is rendered
- **THEN** its background SHALL be `#2d333b`

#### Scenario: Border color
- **WHEN** any card border or divider is rendered
- **THEN** its color SHALL be `#444c56`

#### Scenario: Primary text color
- **WHEN** primary text is rendered
- **THEN** its color SHALL be `#adbac7`

#### Scenario: Muted text color
- **WHEN** secondary/muted text is rendered
- **THEN** its color SHALL be `#768390`

#### Scenario: Badge backgrounds are proportionally lifted
- **WHEN** a status badge is rendered
- **THEN** green badge background SHALL be `#1e3a2a`, yellow `#3d2c00`, red `#3d1515`, blue `#243d5e`

### Requirement: Dashboard server launch
The system SHALL provide a `vacuum-dashboard` CLI entry point that starts a local FastAPI/uvicorn server and opens the dashboard in the default browser.

#### Scenario: Default launch
- **WHEN** `vacuum-dashboard` is run with no arguments
- **THEN** the server SHALL start on port 8080 and open `http://localhost:8080` in the browser

#### Scenario: Custom port
- **WHEN** `vacuum-dashboard --port 9090` is run
- **THEN** the server SHALL start on port 9090

### Requirement: Live status panel
The system SHALL display a status panel showing current vacuum state, battery level, dock status, and error code (if any).

#### Scenario: Status displayed on load
- **WHEN** the dashboard page loads
- **THEN** the status panel SHALL show state, battery percentage, and dock status fetched from `/api/status`

#### Scenario: Auto-refresh
- **WHEN** the dashboard is open and 30 seconds elapse
- **THEN** all data panels SHALL refresh by re-fetching their respective API endpoints

### Requirement: Rooms panel
The system SHALL display a panel listing all rooms with their segment IDs and names.

#### Scenario: Rooms listed
- **WHEN** the dashboard loads
- **THEN** the rooms panel SHALL show a table of room ID and name for every segment returned by `/api/rooms`

### Requirement: Routines panel
The system SHALL display a panel listing all configured routines with a run button for each.

#### Scenario: Routines listed with run buttons
- **WHEN** the dashboard loads
- **THEN** the routines panel SHALL show each routine name with a "Run" button

#### Scenario: Run routine via UI
- **WHEN** the user clicks "Run" next to a routine
- **THEN** the dashboard SHALL POST to `/api/routine/{name}` and show success or error feedback

### Requirement: Consumables panel
The system SHALL display a panel showing consumable life percentages (main brush, side brush, filter).

#### Scenario: Consumables displayed
- **WHEN** the dashboard loads
- **THEN** the consumables panel SHALL show percentage remaining for each consumable fetched from `/api/consumables`

#### Scenario: Consumables unavailable
- **WHEN** the consumables API call fails or returns no data
- **THEN** the panel SHALL display "Unavailable" without crashing the rest of the UI

### Requirement: Clean history panel
The system SHALL display the last 10 cleaning jobs with start time, duration, area, completion, start type, clean type, and finish reason.

#### Scenario: History displayed with enriched fields
- **WHEN** the dashboard loads
- **THEN** the clean history panel SHALL show a table with columns: start time, duration, area, complete, start type, clean type, finish reason

#### Scenario: History unavailable
- **WHEN** the history API call fails
- **THEN** the panel SHALL display "Unavailable" gracefully

### Requirement: Actions panel
The system SHALL provide buttons for all supported one-click actions: Start clean, Stop, Pause, Return to dock, Locate.

#### Scenario: Action buttons present
- **WHEN** the dashboard loads
- **THEN** the actions panel SHALL show buttons for Start, Stop, Pause, Dock, and Locate

#### Scenario: Action feedback
- **WHEN** an action button is clicked
- **THEN** the button SHALL be disabled during the request and show success or error feedback on completion

### Requirement: Room clean form
The system SHALL provide a form to select one or more rooms and a repeat count, then trigger a room clean.

#### Scenario: Room clean submitted
- **WHEN** the user selects rooms and clicks "Clean Rooms"
- **THEN** the dashboard SHALL POST to `/api/rooms/clean` with selected segment IDs and repeat count

### Requirement: Dashboard API endpoints
The system SHALL expose REST API endpoints consumed by the frontend.

#### Scenario: GET /api/status
- **WHEN** GET `/api/status` is called
- **THEN** the response SHALL return JSON with state, battery, in_dock, error_code

#### Scenario: GET /api/rooms
- **WHEN** GET `/api/rooms` is called
- **THEN** the response SHALL return JSON array of `{id, name}` objects

#### Scenario: GET /api/routines
- **WHEN** GET `/api/routines` is called
- **THEN** the response SHALL return JSON array of routine names

#### Scenario: GET /api/consumables
- **WHEN** GET `/api/consumables` is called
- **THEN** the response SHALL return JSON with consumable names and percentage remaining

#### Scenario: GET /api/history
- **WHEN** GET `/api/history` is called
- **THEN** the response SHALL return JSON array of up to 10 recent clean job records

#### Scenario: POST /api/action/{name}
- **WHEN** POST `/api/action/{name}` is called with name in [start, stop, pause, dock, locate]
- **THEN** the corresponding VacuumClient method SHALL be called and `{ok: true}` returned on success

#### Scenario: POST /api/routine/{name}
- **WHEN** POST `/api/routine/{name}` is called
- **THEN** `run_routine(name)` SHALL be called and `{ok: true}` returned on success

#### Scenario: POST /api/rooms/clean
- **WHEN** POST `/api/rooms/clean` is called with `{segment_ids: [...], repeat: n}`
- **THEN** `clean_rooms(segment_ids, repeat)` SHALL be called and `{ok: true}` returned on success

#### Scenario: GET /api/settings
- **WHEN** GET `/api/settings` is called
- **THEN** the response SHALL return JSON with `fan_speed`, `mop_mode`, `water_flow` as string enum names or `null` if unrecognized

#### Scenario: POST /api/settings
- **WHEN** POST `/api/settings` is called with `{"fan_speed": "TURBO", "mop_mode": "DEEP"}`
- **THEN** the corresponding setters SHALL be called and `{ok: true}` returned

#### Scenario: POST /api/consumables/reset/{attribute}
- **WHEN** `POST /api/consumables/reset/{attribute}` is called with a valid attribute name
- **THEN** `client.reset_consumable(attribute)` SHALL be called and `{ok: true}` returned

#### Scenario: Invalid attribute returns 400
- **WHEN** `POST /api/consumables/reset/{attribute}` is called with an unknown attribute
- **THEN** the endpoint SHALL return HTTP 400 with an error message

### Requirement: Consumable reset buttons in dashboard UI
The system SHALL display a "Reset" button next to each consumable progress bar in the consumables panel.

#### Scenario: Reset button present for each consumable
- **WHEN** the consumables panel loads
- **THEN** each consumable row SHALL show a "Reset" button alongside the progress bar

#### Scenario: Confirm dialog before reset
- **WHEN** the user clicks a "Reset" button
- **THEN** a confirmation dialog SHALL appear naming the consumable before proceeding

#### Scenario: Reset success feedback
- **WHEN** the user confirms a reset and the API call succeeds
- **THEN** the consumables panel SHALL refresh and show updated (reset) values

#### Scenario: Reset error feedback
- **WHEN** the API call fails
- **THEN** an error message SHALL be displayed without crashing the UI

### Requirement: Settings panel in dashboard UI
The system SHALL display a "Clean Settings" panel with dropdowns for fan speed, mop mode, water flow, and route, populated from `/api/settings` and with a "Save Settings" button.

#### Scenario: Panel loads with current settings
- **WHEN** the dashboard loads
- **THEN** the settings panel SHALL show the current device settings fetched from `GET /api/settings`

#### Scenario: Save settings
- **WHEN** the user changes a dropdown and clicks "Save Settings"
- **THEN** the dashboard SHALL POST to `/api/settings` and show success or error feedback

### Requirement: Clean actions accept inline settings
The system SHALL accept optional `fan_speed`, `mop_mode`, `water_flow`, and `route` in the `POST /api/rooms/clean` and `POST /api/action/start` request bodies.

#### Scenario: Room clean with inline settings
- **WHEN** `POST /api/rooms/clean` is called with `{"segment_ids": [1], "repeat": 1, "fan_speed": "TURBO"}`
- **THEN** `clean_rooms()` SHALL be called with `fan_speed=FanSpeed.TURBO`

#### Scenario: Start clean with inline settings
- **WHEN** `POST /api/action/start` is called with body `{"fan_speed": "QUIET", "mop_mode": "FAST"}`
- **THEN** `start_clean()` SHALL be called with those settings

#### Scenario: Missing settings fields use device defaults
- **WHEN** `POST /api/rooms/clean` is called without settings fields
- **THEN** `clean_rooms()` SHALL be called with no settings arguments (device defaults apply)

### Requirement: Clean mode selector in Clean Rooms panel
The system SHALL display a "Clean Mode" dropdown in the Clean Rooms panel that pre-populates the fan speed and water flow fields based on the selected mode.

#### Scenario: Clean mode dropdown present
- **WHEN** the Clean Rooms panel renders
- **THEN** a "Clean Mode" dropdown SHALL appear with options: (no preference), Vacuum only, Mop only, Both (simultaneous), Vacuum then Mop

#### Scenario: Selecting Vacuum only presets fields
- **WHEN** the user selects "Vacuum only"
- **THEN** the fan speed dropdown SHALL be set to device default (cleared) and the water flow dropdown SHALL be set to "OFF"

#### Scenario: Selecting Mop only presets fields
- **WHEN** the user selects "Mop only"
- **THEN** the fan speed dropdown SHALL be set to "OFF" and the water flow dropdown SHALL be cleared to device default

#### Scenario: Selecting Both presets fields
- **WHEN** the user selects "Both (simultaneous)"
- **THEN** both the fan speed and water flow dropdowns SHALL be cleared to device default

#### Scenario: Selecting Vacuum then Mop presets fields
- **WHEN** the user selects "Vacuum then Mop"
- **THEN** the water flow dropdown SHALL be set to "VAC_THEN_MOP" and fan speed SHALL be cleared to device default

#### Scenario: Individual overrides remain editable after mode selection
- **WHEN** the user selects a clean mode and then changes an individual setting dropdown
- **THEN** the changed value SHALL be used in the clean request (mode selection is a preset, not a lock)

### Requirement: Clean mode selector in Start Clean action
The system SHALL display clean mode and optional settings overrides below the Start Clean button, matching the Clean Rooms panel behavior.

#### Scenario: Start clean mode controls present
- **WHEN** the Actions panel renders
- **THEN** a "Clean Mode" dropdown and fan speed / water flow overrides SHALL be shown below the action buttons

#### Scenario: Start clean dispatches with mode settings
- **WHEN** the user selects a clean mode and/or overrides and clicks "▶ Start"
- **THEN** `POST /api/action/start` SHALL be called with the resulting fan_speed and water_flow values

#### Scenario: Start clean with no overrides uses device defaults
- **WHEN** no clean mode is selected and no overrides are set
- **THEN** `POST /api/action/start` SHALL be called with no body (device defaults apply), matching prior behavior

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
The system SHALL record a clean event in the scheduler whenever a clean is dispatched via the dashboard. The logged mode SHALL reflect whether the dispatch was a vacuum-only, mop-only, or combined clean.

#### Scenario: Room clean logged on dispatch
- **WHEN** `POST /api/rooms/clean` is called with segment_ids and succeeds
- **THEN** `scheduler.log_clean(segment_ids, mode, source="dashboard")` SHALL be called before returning the response

#### Scenario: Mode is mop when fan_speed is OFF
- **WHEN** the dispatch request includes `fan_speed` set to `"OFF"`
- **THEN** the logged mode SHALL be `"mop"`

#### Scenario: Mode is both when water_flow is active
- **WHEN** the dispatch request includes `water_flow` set to a non-OFF value (including `VAC_THEN_MOP`) and `fan_speed` is not `"OFF"`
- **THEN** the logged mode SHALL be `"both"` (covers simultaneous and sequential vacuum+mop)

#### Scenario: Mode defaults to vacuum
- **WHEN** the dispatch request does not include `water_flow`, sets it to `"OFF"`, and `fan_speed` is not `"OFF"`
- **THEN** the logged mode SHALL be `"vacuum"`
