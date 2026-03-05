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
