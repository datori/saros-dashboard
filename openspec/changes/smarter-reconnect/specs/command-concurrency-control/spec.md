## ADDED Requirements

### Requirement: Concurrent MQTT command limit
The dashboard SHALL limit the number of concurrent in-flight MQTT commands using an asyncio Semaphore with a maximum of 2 concurrent commands.

#### Scenario: Two commands execute concurrently
- **WHEN** two device commands are issued simultaneously
- **THEN** both SHALL execute concurrently through the MQTT channel

#### Scenario: Third command waits for a slot
- **WHEN** a third device command is issued while two are already in-flight
- **THEN** it SHALL wait until one of the in-flight commands completes before executing

#### Scenario: Semaphore applies to both reads and writes
- **WHEN** a read (GET) and a write (POST) command are issued simultaneously
- **THEN** both SHALL count against the same semaphore limit of 2
