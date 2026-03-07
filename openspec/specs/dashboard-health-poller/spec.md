## ADDED Requirements

### Requirement: Background health poll
The dashboard server SHALL run a background asyncio task that polls `get_status()` every 60 seconds for the lifetime of the server process.

#### Scenario: Successful poll warms cache
- **WHEN** the background poller calls `get_status()` and it succeeds
- **THEN** the result SHALL be stored in both the hot cache and the stale cache, and `_last_contact` SHALL be updated

#### Scenario: Failed poll triggers proactive reconnect
- **WHEN** the background poller calls `get_status()` and it raises an exception
- **THEN** the failure SHALL be recorded and `_maybe_reconnect()` SHALL be triggered if the failure threshold is reached

#### Scenario: Poller starts and stops with lifespan
- **WHEN** the FastAPI lifespan starts
- **THEN** the poller task SHALL be created
- **WHEN** the lifespan shuts down
- **THEN** the poller task SHALL be cancelled and awaited

### Requirement: Health status endpoint
The dashboard server SHALL expose `GET /api/health` returning connection health metadata.

#### Scenario: Health endpoint returns metadata
- **WHEN** `GET /api/health` is called
- **THEN** the response SHALL include `last_contact_seconds_ago` (float or null), `reconnect_count` (int), and `ok` (bool, true if last contact within 120s)
