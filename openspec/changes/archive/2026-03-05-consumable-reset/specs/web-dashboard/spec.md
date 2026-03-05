## ADDED Requirements

### Requirement: Consumable reset API endpoint
The system SHALL expose a REST endpoint to reset individual consumable timers.

#### Scenario: POST /api/consumables/reset/{attribute}
- **WHEN** `POST /api/consumables/reset/{attribute}` is called with a valid attribute name
- **THEN** `client.reset_consumable(attribute)` SHALL be called and `{ok: true}` returned

#### Scenario: Invalid attribute returns 400
- **WHEN** `POST /api/consumables/reset/{attribute}` is called with an unknown attribute
- **THEN** the endpoint SHALL return HTTP 400 with an error message

### Requirement: Consumable reset buttons in dashboard UI
The system SHALL display a "Reset" button next to each consumable progress bar in the consumables panel.

#### Scenario: Reset button present for each consumable
- **WHEN** the consumables panel loads
- **THEN** each consumable row SHALL show a "Reset" button alongside the progress bar

#### Scenario: Confirm dialog before reset
- **WHEN** the user clicks a "Reset" button
- **THEN** a confirmation dialog SHALL appear naming the consumable before proceeding

#### Scenario: Reset success feedback
- **WHEN** the user confirms a reset and the API call succeeds
- **THEN** the consumables panel SHALL refresh and show updated (reset) values

#### Scenario: Reset error feedback
- **WHEN** the API call fails
- **THEN** an error message SHALL be displayed without crashing the UI
