## ADDED Requirements

### Requirement: Settings API endpoints
The system SHALL expose `GET /api/settings` and `POST /api/settings` endpoints for reading and writing device cleaning parameter defaults.

#### Scenario: GET /api/settings returns current settings
- **WHEN** `GET /api/settings` is called
- **THEN** the response SHALL return JSON with `fan_speed`, `mop_mode`, `water_flow` as string enum names (e.g., `"TURBO"`, `"DEEP"`, `"HIGH"`) or `null` if unrecognized

#### Scenario: POST /api/settings updates device settings
- **WHEN** `POST /api/settings` is called with `{"fan_speed": "TURBO", "mop_mode": "DEEP"}`
- **THEN** the corresponding `set_fan_speed()` and `set_mop_mode()` SHALL be called and `{ok: true}` returned

#### Scenario: POST /api/settings ignores null fields
- **WHEN** `POST /api/settings` is called with `{"fan_speed": null, "mop_mode": "FAST"}`
- **THEN** only `set_mop_mode()` SHALL be called; `fan_speed` SHALL remain unchanged

#### Scenario: Invalid setting value returns 400
- **WHEN** `POST /api/settings` is called with an unrecognized enum name
- **THEN** the endpoint SHALL return HTTP 400 with an error message listing valid values

### Requirement: Settings panel in dashboard UI
The system SHALL display a "Clean Settings" panel with dropdowns for fan speed, mop mode, water flow, and route, populated from `/api/settings` and with a "Save Settings" button.

#### Scenario: Panel loads with current settings
- **WHEN** the dashboard loads
- **THEN** the settings panel SHALL show the current device settings fetched from `GET /api/settings`

#### Scenario: Save settings
- **WHEN** the user changes a dropdown and clicks "Save Settings"
- **THEN** the dashboard SHALL POST to `/api/settings` and show success or error feedback

### Requirement: Clean actions accept inline settings
The system SHALL accept optional `fan_speed`, `mop_mode`, `water_flow`, and `route` in the `POST /api/rooms/clean` request body and the `POST /api/action/start` request body.

#### Scenario: Room clean with inline settings
- **WHEN** `POST /api/rooms/clean` is called with `{"segment_ids": [1], "repeat": 1, "fan_speed": "TURBO"}`
- **THEN** `clean_rooms()` SHALL be called with `fan_speed=FanSpeed.TURBO`

#### Scenario: Start clean with inline settings
- **WHEN** `POST /api/action/start` is called with body `{"fan_speed": "QUIET", "mop_mode": "FAST"}`
- **THEN** `start_clean()` SHALL be called with those settings

#### Scenario: Missing settings fields use device defaults
- **WHEN** `POST /api/rooms/clean` is called without settings fields
- **THEN** `clean_rooms()` SHALL be called with no settings arguments (device defaults apply)

## MODIFIED Requirements

### Requirement: Clean history panel
The system SHALL display the last 10 cleaning jobs with start time, duration, area, completion, start type, clean type, and finish reason.

#### Scenario: History displayed with enriched fields
- **WHEN** the dashboard loads
- **THEN** the clean history panel SHALL show a table with columns: start time, duration, area, complete, start type, clean type, finish reason

#### Scenario: History unavailable
- **WHEN** the history API call fails
- **THEN** the panel SHALL display "Unavailable" gracefully
