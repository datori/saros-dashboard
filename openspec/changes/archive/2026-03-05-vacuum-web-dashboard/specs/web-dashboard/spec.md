## ADDED Requirements

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
The system SHALL display the last 10 cleaning jobs with start time, duration, and area cleaned.

#### Scenario: History displayed
- **WHEN** the dashboard loads
- **THEN** the clean history panel SHALL show a table of recent jobs from `/api/history`

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
