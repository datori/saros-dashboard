## ADDED Requirements

### Requirement: Stale cache preserved across reconnects
The stale cache SHALL NOT be cleared when the VacuumClient is recreated during auto-reconnect. Only the hot cache (TTL-based) SHALL be cleared.

#### Scenario: Reconnect preserves stale data
- **WHEN** `_maybe_reconnect()` successfully creates a new VacuumClient
- **THEN** the hot cache (`_cache`) SHALL be cleared
- **AND** the stale cache (`_stale_cache`) SHALL be preserved

#### Scenario: Stale data available after failed reconnect
- **WHEN** `_maybe_reconnect()` fails to create a new client and a subsequent read request also fails
- **THEN** the stale cache SHALL still contain previously cached data for fallback
