## MODIFIED Requirements

### Requirement: Auto-refresh
The system SHALL refresh all data panels on a 30-second interval, with panel loaders staggered to avoid concurrent MQTT burst pressure. When a panel receives stale data (`_stale: true`), it SHALL display the data in a visually dimmed state with a staleness indicator rather than showing an error.

#### Scenario: Auto-refresh
- **WHEN** the dashboard is open and 30 seconds elapse
- **THEN** all data panels SHALL refresh by re-fetching their respective API endpoints, with each loader staggered approximately 300 ms apart

#### Scenario: Stale data displayed with indicator
- **WHEN** a panel receives a response containing `_stale: true`
- **THEN** the panel SHALL render the data content (not an error) with a visual staleness indicator (dimmed header, "last updated X ago" text)

#### Scenario: Connectivity lost banner
- **WHEN** `GET /api/health` returns `ok: false` (no contact for >120s)
- **THEN** a non-alarming banner SHALL appear at the top of the dashboard indicating the device is unreachable and showing time since last contact
