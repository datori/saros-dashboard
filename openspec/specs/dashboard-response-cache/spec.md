## ADDED Requirements

### Requirement: Per-endpoint response cache with TTL
The dashboard server SHALL maintain an in-process cache of device API responses, keyed by endpoint name, with a configurable TTL (default 5 seconds).

#### Scenario: Cache hit returns stored data
- **WHEN** a GET endpoint is called within TTL seconds of a prior successful response
- **THEN** the cached data SHALL be returned immediately without issuing an MQTT command

#### Scenario: Cache miss fetches from device
- **WHEN** a GET endpoint is called and no cached entry exists or the entry has expired
- **THEN** the endpoint SHALL fetch fresh data from the device and store it in the cache

#### Scenario: Concurrent cache miss (stampede prevention)
- **WHEN** two requests for the same endpoint arrive simultaneously and both miss the cache
- **THEN** only one MQTT command SHALL be issued; the second request SHALL wait and receive the same result

### Requirement: Cache invalidation after write actions
The dashboard server SHALL invalidate relevant cache entries after any successful write action.

#### Scenario: Action endpoint invalidates status cache
- **WHEN** POST `/api/action/{name}` succeeds
- **THEN** the `status` cache entry SHALL be invalidated

#### Scenario: Settings write invalidates settings cache
- **WHEN** POST `/api/settings` succeeds
- **THEN** the `settings` cache entry SHALL be invalidated

#### Scenario: Rooms clean invalidates status cache
- **WHEN** POST `/api/rooms/clean` succeeds
- **THEN** the `status` cache entry SHALL be invalidated

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
