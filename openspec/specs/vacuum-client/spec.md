## ADDED Requirements

### Requirement: Authenticated client initialization
The system SHALL initialize an authenticated connection to the Roborock cloud API using username and password credentials, discovering the user's devices and selecting the Saros 10R.

#### Scenario: Successful initialization
- **WHEN** valid `ROBOROCK_USERNAME` and `ROBOROCK_PASSWORD` are provided
- **THEN** the client authenticates with the Roborock cloud and exposes the Saros 10R device for control

#### Scenario: Missing credentials
- **WHEN** credentials are absent or empty
- **THEN** the client SHALL raise a `ConfigError` with a clear message before attempting network calls

#### Scenario: Authentication failure
- **WHEN** credentials are invalid or the cloud API rejects them
- **THEN** the client SHALL raise an `AuthError` with the upstream error message

### Requirement: Device status retrieval
The system SHALL retrieve the current status of the vacuum, including cleaning state, battery level, error codes, and dock status.

#### Scenario: Status when idle
- **WHEN** `get_status()` is called and the vacuum is docked and idle
- **THEN** the response SHALL include state, battery percentage, and dock status

#### Scenario: Status when cleaning
- **WHEN** `get_status()` is called during an active cleaning job
- **THEN** the response SHALL include current state, area cleaned, and elapsed time

### Requirement: Basic vacuum control commands
The system SHALL support start, stop, pause, and return-to-dock commands dispatched to the vacuum via the cloud API.

#### Scenario: Start full clean
- **WHEN** `start_clean()` is called
- **THEN** the vacuum SHALL begin a full home cleaning session

#### Scenario: Pause cleaning
- **WHEN** `pause()` is called during an active session
- **THEN** the vacuum SHALL pause in place without returning to dock

#### Scenario: Stop and dock
- **WHEN** `return_to_dock()` is called
- **THEN** the vacuum SHALL stop any active cleaning and return to its charging dock

### Requirement: Room cleaning by segment ID
The system SHALL support cleaning one or more specific rooms identified by their segment IDs, with configurable repeat count.

#### Scenario: Single room clean
- **WHEN** `clean_rooms(segment_ids=[n], repeat=1)` is called
- **THEN** the vacuum SHALL clean only the specified room segment

#### Scenario: Multi-room clean with repeats
- **WHEN** `clean_rooms(segment_ids=[n, m], repeat=2)` is called
- **THEN** the vacuum SHALL clean both segments, each passed twice

### Requirement: Zone cleaning by coordinates
The system SHALL support cleaning rectangular zones defined by coordinate pairs.

#### Scenario: Single zone clean
- **WHEN** `clean_zones(zones=[(x1, y1, x2, y2)], repeat=1)` is called
- **THEN** the vacuum SHALL clean the defined rectangular area

### Requirement: Map and room discovery
The system SHALL retrieve map data including segment IDs and their names to support room-based automation.

#### Scenario: Room list retrieval
- **WHEN** `get_rooms()` is called
- **THEN** the response SHALL include a list of segments with ID and name for each room

### Requirement: Vacuum locator
The system SHALL trigger an audible sound on the vacuum to assist in physical location.

#### Scenario: Locate sound
- **WHEN** `locate()` is called
- **THEN** the vacuum SHALL play its locator sound

### Requirement: Routine execution
The system SHALL trigger named routines that have been configured in the Roborock app.

#### Scenario: Run named routine
- **WHEN** `run_routine(name)` is called with a valid routine name
- **THEN** the corresponding routine SHALL be triggered via the cloud API

#### Scenario: Unknown routine
- **WHEN** `run_routine(name)` is called with an unrecognized name
- **THEN** the client SHALL raise a `RoutineNotFoundError` listing available routine names

### Requirement: Consumables retrieval
The system SHALL retrieve consumable usage data including main brush, side brush, and filter life.

#### Scenario: Consumables returned
- **WHEN** `get_consumables()` is called
- **THEN** the response SHALL include percentage remaining for main brush, side brush, and filter

#### Scenario: Consumables command fails
- **WHEN** the device does not support the GET_CONSUMABLE command
- **THEN** the method SHALL raise a descriptive exception rather than return partial data

### Requirement: Clean history retrieval
The system SHALL retrieve a list of recent cleaning job records including start time, duration, and area.

#### Scenario: History returned
- **WHEN** `get_clean_history(limit=10)` is called
- **THEN** the response SHALL include up to 10 recent cleaning records with start time, duration in seconds, and area in cm²

#### Scenario: No history available
- **WHEN** `get_clean_history()` is called and no records exist
- **THEN** the method SHALL return an empty list
