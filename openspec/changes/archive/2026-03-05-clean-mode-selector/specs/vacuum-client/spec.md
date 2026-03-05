## MODIFIED Requirements

### Requirement: Basic vacuum control commands
The system SHALL support start, stop, pause, and return-to-dock commands, with `start_clean()` accepting optional fan speed, mop mode, water flow, and route parameters. `WaterFlow` SHALL include a `VAC_THEN_MOP` member (value 235) representing the Saros 10R sequential vacuum-then-mop mode.

#### Scenario: Start full clean with defaults
- **WHEN** `start_clean()` is called with no settings arguments
- **THEN** the vacuum SHALL begin a full home cleaning session using current device settings

#### Scenario: Start full clean with settings
- **WHEN** `start_clean(fan_speed=FanSpeed.MAX, water_flow=WaterFlow.HIGH)` is called
- **THEN** `SET_CUSTOM_MODE` and `SET_WATER_BOX_CUSTOM_MODE` SHALL be sent before `APP_START`

#### Scenario: Start mop-only clean
- **WHEN** `start_clean(fan_speed=FanSpeed.OFF, water_flow=WaterFlow.MEDIUM)` is called
- **THEN** `SET_CUSTOM_MODE` with value 105 and `SET_WATER_BOX_CUSTOM_MODE` with value 202 SHALL be sent before `APP_START`

#### Scenario: Start sequential vacuum-then-mop
- **WHEN** `start_clean(water_flow=WaterFlow.VAC_THEN_MOP)` is called
- **THEN** `SET_WATER_BOX_CUSTOM_MODE` with value 235 SHALL be sent before `APP_START`

#### Scenario: Pause cleaning
- **WHEN** `pause()` is called during an active session
- **THEN** the vacuum SHALL pause in place without returning to dock

#### Scenario: Stop and dock
- **WHEN** `return_to_dock()` is called
- **THEN** the vacuum SHALL stop any active cleaning and return to its charging dock
