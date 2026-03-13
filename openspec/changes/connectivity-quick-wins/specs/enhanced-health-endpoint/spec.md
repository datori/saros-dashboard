## ADDED Requirements

### Requirement: Health endpoint exposes MQTT connection state
The `GET /api/health` endpoint SHALL include the MQTT connection state from the python-roborock library.

#### Scenario: MQTT connected
- **WHEN** the health endpoint is called and `device.is_connected` is `True`
- **THEN** the response SHALL include `"mqtt_connected": true`

#### Scenario: MQTT disconnected
- **WHEN** the health endpoint is called and `device.is_connected` is `False`
- **THEN** the response SHALL include `"mqtt_connected": false`

#### Scenario: Client not initialized
- **WHEN** the health endpoint is called and the VacuumClient is not yet authenticated
- **THEN** the response SHALL include `"mqtt_connected": false`

### Requirement: Health endpoint exposes failure count
The `GET /api/health` endpoint SHALL include the current consecutive failure count.

#### Scenario: Failure count reported
- **WHEN** the health endpoint is called
- **THEN** the response SHALL include `"failures": <int>` reflecting the current value of `_client_failures`

### Requirement: Health endpoint exposes reconnect-in-progress state
The `GET /api/health` endpoint SHALL indicate whether a reconnect is currently in progress.

#### Scenario: Reconnect in progress
- **WHEN** the health endpoint is called while `_reconnect_lock` is held
- **THEN** the response SHALL include `"reconnecting": true`

#### Scenario: No reconnect in progress
- **WHEN** the health endpoint is called while `_reconnect_lock` is not held
- **THEN** the response SHALL include `"reconnecting": false`

### Requirement: VacuumClient exposes connection state
VacuumClient SHALL expose an `is_connected` property that delegates to the underlying device's connection state.

#### Scenario: Device connected
- **WHEN** `is_connected` is accessed and the device's MQTT channel reports connected
- **THEN** it SHALL return `True`

#### Scenario: Device not authenticated
- **WHEN** `is_connected` is accessed before `authenticate()` has been called
- **THEN** it SHALL return `False`
