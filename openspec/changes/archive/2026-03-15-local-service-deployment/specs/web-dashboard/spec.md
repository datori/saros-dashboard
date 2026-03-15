## MODIFIED Requirements

### Requirement: Dashboard server launch
The system SHALL provide a `vacuum-dashboard` CLI entry point that starts a local FastAPI/uvicorn server and opens the dashboard in the default browser.

#### Scenario: Default launch
- **WHEN** `vacuum-dashboard` is run with no arguments
- **THEN** the server SHALL start on port 9103 and open `http://localhost:9103` in the browser

#### Scenario: Custom port
- **WHEN** `vacuum-dashboard --port 9999` is run
- **THEN** the server SHALL start on port 9999
