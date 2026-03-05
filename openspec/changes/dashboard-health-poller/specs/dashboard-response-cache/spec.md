## ADDED Requirements

### Requirement: Stale data fallback
The cache SHALL maintain a secondary stale-data store of the last successful response per endpoint with no expiry. When a live fetch fails and stale data exists, the stale data SHALL be returned with a `_stale: true` field appended.

#### Scenario: Stale fallback on device error
- **WHEN** a GET endpoint's live fetch raises an exception
- **AND** a prior successful response exists in the stale cache
- **THEN** the endpoint SHALL return the stale data with `_stale: true` instead of `{"error": "..."}`

#### Scenario: No stale fallback when cache is empty
- **WHEN** a GET endpoint's live fetch raises an exception
- **AND** no prior successful response exists
- **THEN** the endpoint SHALL return `{"error": "..."}` as before

#### Scenario: Stale cache cleared on reconnect
- **WHEN** `_maybe_reconnect()` successfully creates a new VacuumClient
- **THEN** both the hot cache and stale cache SHALL be cleared
