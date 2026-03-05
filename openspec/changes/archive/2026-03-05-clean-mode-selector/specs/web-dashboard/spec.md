## ADDED Requirements

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

## MODIFIED Requirements

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
