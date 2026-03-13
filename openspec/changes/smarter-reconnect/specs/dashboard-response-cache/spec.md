## ADDED Requirements

### Requirement: Tiered reconnect strategy
The auto-reconnect mechanism SHALL use a tiered approach: first waiting for the library's built-in MQTT reconnect, then falling back to full VacuumClient recreation.

#### Scenario: Threshold reached, MQTT connected, recent success
- **WHEN** the failure counter reaches the reconnect threshold, `is_connected` is `True`, and `_last_contact` is within 120 seconds
- **THEN** `_maybe_reconnect()` SHALL NOT recreate the client (errors are device-side, not connection-side)
- **AND** the failure counter SHALL be reset

#### Scenario: Threshold reached, MQTT connected, no recent success (zombie connection)
- **WHEN** the failure counter reaches the reconnect threshold, `is_connected` is `True`, and `_last_contact` is more than 120 seconds ago (or None)
- **THEN** `_maybe_reconnect()` SHALL recreate the VacuumClient (full re-auth), treating the session as a zombie connection

#### Scenario: Threshold reached, MQTT disconnected, library self-heals
- **WHEN** the failure counter reaches the reconnect threshold, `is_connected` is `False`, and the library reconnects within 60 seconds
- **THEN** `_maybe_reconnect()` SHALL NOT recreate the client
- **AND** the failure counter SHALL be reset

#### Scenario: Threshold reached, MQTT disconnected, library fails to recover
- **WHEN** the failure counter reaches the reconnect threshold, `is_connected` is `False`, and the library does not reconnect within 60 seconds
- **THEN** `_maybe_reconnect()` SHALL recreate the VacuumClient (full re-auth)

### Requirement: Health poller warms additional caches
The background health polling task SHALL warm `status`, `settings`, and `consumables` caches, with spacing between commands.

#### Scenario: Normal polling cycle
- **WHEN** the health poll timer fires (every 60 seconds)
- **THEN** the poller SHALL fetch `status`, `settings`, and `consumables` in sequence with a 2-second delay between each

#### Scenario: Polling aborts on failure
- **WHEN** a health poll fetch fails for any endpoint
- **THEN** the poller SHALL skip remaining endpoints in that cycle and wait for the next cycle
