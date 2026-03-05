## ADDED Requirements

### Requirement: Reset consumable timer
The system SHALL allow resetting individual consumable timers to zero via the VacuumClient and the dashboard REST API.

#### Scenario: Reset via client method
- **WHEN** `client.reset_consumable("sensor_dirty_time")` is called
- **THEN** the `RESET_CONSUMABLE` command SHALL be sent to the device with that attribute value

#### Scenario: Invalid attribute rejected
- **WHEN** `reset_consumable` is called with an unknown attribute string
- **THEN** a `ValueError` SHALL be raised before any command is sent

#### Scenario: Supported attributes
- **WHEN** any of `sensor_dirty_time`, `filter_work_time`, `side_brush_work_time`, `main_brush_work_time` is passed
- **THEN** the reset SHALL succeed without error
