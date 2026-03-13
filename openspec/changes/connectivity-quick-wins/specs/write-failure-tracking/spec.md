## ADDED Requirements

### Requirement: Write endpoints contribute to failure tracking
POST endpoints that issue device commands SHALL call `_record_failure()` on exception and `_record_success()` on success, so that write-action failures contribute to the auto-reconnect threshold.

#### Scenario: Successful write action resets failure counter
- **WHEN** a POST endpoint (`/api/action/{name}`, `/api/settings`, `/api/rooms/clean`, `/api/routine/{name}`) completes successfully
- **THEN** the failure counter SHALL be reset to zero via `_record_success()`

#### Scenario: Failed write action increments failure counter
- **WHEN** a POST endpoint raises an exception from a device command
- **THEN** the failure counter SHALL be incremented via `_record_failure()`

#### Scenario: Write failures trigger reconnect at threshold
- **WHEN** consecutive write-action failures reach the reconnect threshold (3)
- **THEN** `_maybe_reconnect()` SHALL be invoked, identical to how read failures trigger reconnect
