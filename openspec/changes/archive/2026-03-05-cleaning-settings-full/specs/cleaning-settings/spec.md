## ADDED Requirements

### Requirement: Cleaning parameter enums
The system SHALL define typed enums `FanSpeed`, `MopMode`, `WaterFlow`, and `CleanRoute` in `vacuum.client` that map friendly names to Saros 10R device codes.

#### Scenario: FanSpeed enum values
- **WHEN** code imports `FanSpeed` from `vacuum.client`
- **THEN** `FanSpeed` SHALL have members: `OFF`, `QUIET`, `BALANCED`, `TURBO`, `MAX`, `MAX_PLUS`, `SMART`

#### Scenario: MopMode enum values
- **WHEN** code imports `MopMode` from `vacuum.client`
- **THEN** `MopMode` SHALL have members: `STANDARD`, `FAST`, `DEEP`, `DEEP_PLUS`, `SMART`

#### Scenario: WaterFlow enum values
- **WHEN** code imports `WaterFlow` from `vacuum.client`
- **THEN** `WaterFlow` SHALL have members: `OFF`, `LOW`, `MEDIUM`, `HIGH`, `EXTREME`, `SMART`

#### Scenario: CleanRoute enum values
- **WHEN** code imports `CleanRoute` from `vacuum.client`
- **THEN** `CleanRoute` SHALL have members: `STANDARD`, `FAST`, `DEEP`, `DEEP_PLUS`, `SMART`

### Requirement: Inline settings on clean commands
The system SHALL accept optional `fan_speed`, `mop_mode`, `water_flow`, and `route` parameters on `start_clean()`, `clean_rooms()`, and `clean_zones()`. When provided, the corresponding `SET_*` command SHALL be issued before the clean command.

#### Scenario: Clean rooms with fan speed
- **WHEN** `clean_rooms(segment_ids=[1], fan_speed=FanSpeed.TURBO)` is called
- **THEN** `SET_CUSTOM_MODE` SHALL be sent with turbo code before `APP_SEGMENT_CLEAN`

#### Scenario: Clean rooms with mop mode
- **WHEN** `clean_rooms(segment_ids=[1], mop_mode=MopMode.DEEP)` is called
- **THEN** `SET_MOP_MODE` SHALL be sent with deep code before `APP_SEGMENT_CLEAN`

#### Scenario: Clean rooms with water flow
- **WHEN** `clean_rooms(segment_ids=[1], water_flow=WaterFlow.HIGH)` is called
- **THEN** `SET_WATER_BOX_CUSTOM_MODE` SHALL be sent with high code before `APP_SEGMENT_CLEAN`

#### Scenario: None setting is a no-op
- **WHEN** a setting parameter is `None` (the default)
- **THEN** no `SET_*` command SHALL be issued for that setting

### Requirement: Standalone setting setters
The system SHALL provide `set_fan_speed(speed)`, `set_mop_mode(mode)`, `set_water_flow(flow)`, and `set_route(route)` methods that persist device-level defaults without starting a clean.

#### Scenario: Set fan speed
- **WHEN** `set_fan_speed(FanSpeed.MAX)` is called
- **THEN** `SET_CUSTOM_MODE` SHALL be sent with the MAX code

#### Scenario: Set mop mode
- **WHEN** `set_mop_mode(MopMode.FAST)` is called
- **THEN** `SET_MOP_MODE` SHALL be sent with the FAST code

#### Scenario: Set water flow
- **WHEN** `set_water_flow(WaterFlow.MEDIUM)` is called
- **THEN** `SET_WATER_BOX_CUSTOM_MODE` SHALL be sent with the MEDIUM code

### Requirement: Current settings retrieval
The system SHALL provide `get_current_settings()` returning the active fan speed, mop mode, and water flow as enum members (or `None` if unrecognized).

#### Scenario: Settings returned
- **WHEN** `get_current_settings()` is called
- **THEN** the response SHALL include `fan_speed`, `mop_mode`, and `water_flow` reflecting the device's current state

#### Scenario: Unrecognized code
- **WHEN** the device returns a code not in our enum
- **THEN** the corresponding field SHALL be `None` rather than raising an exception

### Requirement: Enriched CleanRecord fields
The system SHALL include `start_type`, `clean_type`, `finish_reason`, `avoid_count`, and `wash_count` in `CleanRecord`, populated from the library's clean record data.

#### Scenario: Fields populated when available
- **WHEN** `get_clean_history()` is called and the library record includes `start_type`
- **THEN** the returned `CleanRecord` SHALL include the start type as a string name (e.g., `"app"`, `"schedule"`)

#### Scenario: Fields are None when unavailable
- **WHEN** the library record does not include a field (older record or unsupported)
- **THEN** the corresponding `CleanRecord` field SHALL be `None`
