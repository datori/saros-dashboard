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
