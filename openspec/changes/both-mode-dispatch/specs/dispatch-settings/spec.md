## MODIFIED Requirements

### Requirement: Dispatch settings storage
The system SHALL store per-mode device settings for auto-dispatch in the scheduler database.

#### Scenario: Default settings seeded
- **WHEN** `init_db()` runs for the first time
- **THEN** three rows SHALL be created: `vacuum` mode with `fan_speed=balanced, water_flow=off`; `mop` mode with `fan_speed=off, mop_mode=standard, water_flow=medium`; and `both` mode with `fan_speed=balanced, mop_mode=standard, water_flow=vac_then_mop`

#### Scenario: Get dispatch settings
- **WHEN** `get_dispatch_settings()` is called
- **THEN** it SHALL return settings for all three modes (`vacuum`, `mop`, `both`), each with `fan_speed`, `mop_mode`, `water_flow`, and `route` fields (nullable)

#### Scenario: Update dispatch settings
- **WHEN** `update_dispatch_settings(mode, fan_speed=..., water_flow=...)` is called
- **THEN** only the provided fields SHALL be updated for that mode; omitted fields SHALL remain unchanged

### Requirement: Dispatch settings API
The dashboard SHALL expose endpoints to view and modify dispatch settings.

#### Scenario: Get all dispatch settings
- **WHEN** `GET /api/dispatch-settings` is called
- **THEN** the response SHALL contain settings for `vacuum`, `mop`, and `both` modes

#### Scenario: Update mode settings — both mode
- **WHEN** `PATCH /api/dispatch-settings/both` is called with a partial settings object
- **THEN** the `both` mode settings SHALL be updated and the response SHALL confirm success

#### Scenario: Invalid mode rejected
- **WHEN** `PATCH /api/dispatch-settings/{mode}` is called with a mode other than `vacuum`, `mop`, or `both`
- **THEN** the API SHALL return HTTP 400

### Requirement: Dispatch settings UI
The dashboard SHALL display a section for viewing and editing dispatch settings per mode.

#### Scenario: Settings displayed — three modes
- **WHEN** the dashboard loads
- **THEN** the dispatch settings section SHALL show current settings for `vacuum`, `mop`, and `both` modes with dropdown selectors for each parameter

#### Scenario: Settings edited
- **WHEN** the user changes a setting and saves
- **THEN** the system SHALL call `PATCH /api/dispatch-settings/{mode}` and update the display
