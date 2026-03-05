## MODIFIED Requirements

### Requirement: Room cleaning by segment ID
The system SHALL support cleaning one or more specific rooms identified by their segment IDs, with configurable repeat count, fan speed, mop mode, water flow, and route pattern.

#### Scenario: Single room clean
- **WHEN** `clean_rooms(segment_ids=[n], repeat=1)` is called
- **THEN** the vacuum SHALL clean only the specified room segment

#### Scenario: Multi-room with repeats
- **WHEN** `clean_rooms(segment_ids=[n, m], repeat=2)` is called
- **THEN** the vacuum SHALL clean both segments, each passed twice

#### Scenario: Room clean with fan speed
- **WHEN** `clean_rooms(segment_ids=[n], fan_speed=FanSpeed.TURBO)` is called
- **THEN** `SET_CUSTOM_MODE` SHALL be sent before `APP_SEGMENT_CLEAN`

#### Scenario: Room clean with mop settings
- **WHEN** `clean_rooms(segment_ids=[n], mop_mode=MopMode.DEEP, water_flow=WaterFlow.HIGH)` is called
- **THEN** both `SET_MOP_MODE` and `SET_WATER_BOX_CUSTOM_MODE` SHALL be sent before `APP_SEGMENT_CLEAN`

#### Scenario: None settings are no-ops
- **WHEN** a setting parameter is `None`
- **THEN** no `SET_*` command SHALL be issued for that setting

### Requirement: Zone cleaning by coordinates
The system SHALL support cleaning rectangular zones defined by coordinate pairs, with configurable repeat count, fan speed, mop mode, water flow, and route pattern.

#### Scenario: Single zone clean
- **WHEN** `clean_zones(zones=[(x1, y1, x2, y2)], repeat=1)` is called
- **THEN** the vacuum SHALL clean the defined rectangular area

#### Scenario: Zone clean with fan speed
- **WHEN** `clean_zones(zones=[(x1, y1, x2, y2)], fan_speed=FanSpeed.QUIET)` is called
- **THEN** `SET_CUSTOM_MODE` SHALL be sent before `APP_ZONED_CLEAN`

### Requirement: Basic vacuum control commands
The system SHALL support start, stop, pause, and return-to-dock commands, with `start_clean()` accepting optional fan speed, mop mode, water flow, and route parameters.

#### Scenario: Start full clean with defaults
- **WHEN** `start_clean()` is called with no settings arguments
- **THEN** the vacuum SHALL begin a full home cleaning session using current device settings

#### Scenario: Start full clean with settings
- **WHEN** `start_clean(fan_speed=FanSpeed.MAX, water_flow=WaterFlow.HIGH)` is called
- **THEN** `SET_CUSTOM_MODE` and `SET_WATER_BOX_CUSTOM_MODE` SHALL be sent before `APP_START`

#### Scenario: Pause cleaning
- **WHEN** `pause()` is called during an active session
- **THEN** the vacuum SHALL pause in place without returning to dock

#### Scenario: Stop and dock
- **WHEN** `return_to_dock()` is called
- **THEN** the vacuum SHALL stop any active cleaning and return to its charging dock

### Requirement: Clean history retrieval
The system SHALL retrieve a list of recent cleaning job records including start time, duration, area, completion status, start type, clean type, finish reason, avoid count, and wash count.

#### Scenario: History returned with enriched fields
- **WHEN** `get_clean_history(limit=10)` is called
- **THEN** the response SHALL include up to 10 recent records; each SHALL include `start_type`, `clean_type`, `finish_reason`, `avoid_count`, `wash_count` where available from the library

#### Scenario: No history available
- **WHEN** `get_clean_history()` is called and no records exist
- **THEN** the method SHALL return an empty list
