## ADDED Requirements

### Requirement: Dispatch settings storage
The system SHALL store per-mode device settings for auto-dispatch in the scheduler database.

#### Scenario: Default settings seeded
- **WHEN** `init_db()` runs for the first time
- **THEN** two rows SHALL be created: `vacuum` mode with `fan_speed=balanced, water_flow=off` and `mop` mode with `fan_speed=off, mop_mode=standard, water_flow=medium`

#### Scenario: Get dispatch settings
- **WHEN** `get_dispatch_settings()` is called
- **THEN** it SHALL return settings for both modes, each with `fan_speed`, `mop_mode`, `water_flow`, and `route` fields (nullable)

#### Scenario: Update dispatch settings
- **WHEN** `update_dispatch_settings(mode, fan_speed=..., water_flow=...)` is called
- **THEN** only the provided fields SHALL be updated for that mode; omitted fields SHALL remain unchanged

### Requirement: Dispatch settings API
The dashboard SHALL expose endpoints to view and modify dispatch settings.

#### Scenario: Get all dispatch settings
- **WHEN** `GET /api/dispatch-settings` is called
- **THEN** the response SHALL contain settings for both `vacuum` and `mop` modes

#### Scenario: Update mode settings
- **WHEN** `PATCH /api/dispatch-settings/{mode}` is called with a partial settings object
- **THEN** the specified mode's settings SHALL be updated and the response SHALL confirm success

### Requirement: Dispatch settings UI
The dashboard SHALL display a section for viewing and editing dispatch settings per mode.

#### Scenario: Settings displayed
- **WHEN** the dashboard loads
- **THEN** the dispatch settings section SHALL show current settings for both vacuum and mop modes with dropdown selectors for each parameter

#### Scenario: Settings edited
- **WHEN** the user changes a setting and saves
- **THEN** the system SHALL call `PATCH /api/dispatch-settings/{mode}` and update the display
