## MODIFIED Requirements

### Requirement: Auto-refresh
The system SHALL refresh all data panels on a 30-second interval, with panel loaders staggered to avoid concurrent MQTT burst pressure.

#### Scenario: Auto-refresh
- **WHEN** the dashboard is open and 30 seconds elapse
- **THEN** all data panels SHALL refresh by re-fetching their respective API endpoints, with each loader staggered approximately 300 ms apart
