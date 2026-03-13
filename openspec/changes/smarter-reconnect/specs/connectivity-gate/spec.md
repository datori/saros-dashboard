## ADDED Requirements

### Requirement: Pre-flight connectivity check for read endpoints
Before issuing a device command for a GET endpoint, the dashboard SHALL check `VacuumClient.is_connected`. If disconnected and stale data exists, the stale data SHALL be returned immediately without waiting for a timeout.

#### Scenario: Disconnected with stale data available
- **WHEN** a GET endpoint is called, the MQTT session is disconnected, and stale cache exists for that endpoint
- **THEN** the stale data SHALL be returned immediately (no 10-second timeout wait)
- **AND** the response SHALL include a stale indicator

#### Scenario: Disconnected with no stale data
- **WHEN** a GET endpoint is called, the MQTT session is disconnected, and no stale cache exists
- **THEN** the request SHALL proceed normally (attempting the device command which will timeout)

#### Scenario: Connected
- **WHEN** a GET endpoint is called and the MQTT session is connected
- **THEN** the request SHALL proceed normally through the cache/fetch path

### Requirement: Pre-flight connectivity check for write endpoints
Before issuing a device command for a POST endpoint, the dashboard SHALL check `VacuumClient.is_connected`. If disconnected, the endpoint SHALL immediately return HTTP 503.

#### Scenario: Write when disconnected
- **WHEN** a POST endpoint is called and the MQTT session is disconnected
- **THEN** the endpoint SHALL immediately raise `HTTPException(503, "Device disconnected")`

#### Scenario: Write when connected
- **WHEN** a POST endpoint is called and the MQTT session is connected
- **THEN** the request SHALL proceed normally
