## ADDED Requirements

### Requirement: Trigger configuration
The system SHALL store named triggers with time budgets in the SQLite database.

#### Scenario: Create trigger
- **WHEN** a trigger is created with `name="gym"`, `budget_min=20`, `mode="vacuum"`
- **THEN** a row SHALL be inserted into the `triggers` table with those values

#### Scenario: Update trigger budget
- **WHEN** a trigger named "gym" exists and its budget is updated to 30 minutes
- **THEN** the `budget_min` value SHALL be updated to 30.0

#### Scenario: Delete trigger
- **WHEN** a trigger named "gym" is deleted
- **THEN** the row SHALL be removed from the `triggers` table

#### Scenario: List triggers
- **WHEN** the trigger list is queried
- **THEN** all configured triggers SHALL be returned with name, budget_min, mode, and notes

### Requirement: Fire trigger
The system SHALL open a cleaning window when a trigger is fired.

#### Scenario: Fire trigger with no active window
- **WHEN** trigger "gym" (budget=20min) is fired and no window is active
- **THEN** the window end time SHALL be set to `now + 20 minutes`

#### Scenario: Fire trigger extends existing window
- **WHEN** a window is active ending at 2:15pm and trigger "leaving" (budget=60min) is fired at 2:05pm
- **THEN** the window end time SHALL be updated to `max(2:15pm, 3:05pm)` = 3:05pm

#### Scenario: Fire trigger with shorter budget than active window
- **WHEN** a window is active ending at 3:00pm and trigger "shower" (budget=15min) is fired at 2:50pm
- **THEN** the window end time SHALL remain 3:00pm (not shortened to 3:05pm only if 3:05 > 3:00, but here max(3:00, 3:05) = 3:05pm)

#### Scenario: Fire trigger while vacuum is already cleaning
- **WHEN** a trigger is fired and the vacuum is currently cleaning
- **THEN** the window SHALL be opened/extended but no new dispatch SHALL occur until the current clean completes

### Requirement: Anti-trigger
The system SHALL immediately close the cleaning window and dock the vacuum when an anti-trigger is fired.

#### Scenario: Anti-trigger with active window and idle vacuum
- **WHEN** an anti-trigger is fired, a window is active, and the vacuum is idle/docked
- **THEN** the window SHALL be closed (window end = now) and no further dispatch SHALL occur

#### Scenario: Anti-trigger with active window and cleaning vacuum
- **WHEN** an anti-trigger is fired and the vacuum is currently cleaning
- **THEN** the window SHALL be closed AND `return_to_dock()` SHALL be called to stop the current clean

#### Scenario: Anti-trigger with no active window
- **WHEN** an anti-trigger is fired and no window is active
- **THEN** no action SHALL be taken (idempotent)

### Requirement: Trigger event logging
The system SHALL log trigger firings for budget tuning purposes.

#### Scenario: Log trigger firing
- **WHEN** a trigger is fired
- **THEN** a `trigger_events` row SHALL be inserted with `trigger_name`, `fired_at=now()`, and `clean_event_id` if a clean was dispatched

#### Scenario: Log anti-trigger or natural window close
- **WHEN** a window closes (via anti-trigger or expiry)
- **THEN** the most recent `trigger_events` row for that window SHALL have `returned_at` set to now and `actual_min` computed

### Requirement: Trigger API endpoints
The system SHALL expose REST endpoints for managing and firing triggers.

#### Scenario: GET triggers list
- **WHEN** `GET /api/triggers` is called
- **THEN** all configured triggers SHALL be returned as JSON array

#### Scenario: POST create/update trigger
- **WHEN** `PUT /api/triggers/{name}` is called with `{budget_min, mode?, notes?}`
- **THEN** the trigger SHALL be upserted

#### Scenario: DELETE trigger
- **WHEN** `DELETE /api/triggers/{name}` is called
- **THEN** the trigger SHALL be removed

#### Scenario: POST fire trigger
- **WHEN** `POST /api/trigger/{name}/fire` is called
- **THEN** the trigger SHALL be fired, opening/extending the cleaning window

#### Scenario: POST anti-trigger
- **WHEN** `POST /api/trigger/stop` is called
- **THEN** the anti-trigger SHALL fire, closing any active window and docking the vacuum

#### Scenario: GET window status
- **WHEN** `GET /api/window` is called
- **THEN** the response SHALL include `active` (bool), `ends_at` (ISO timestamp or null), `remaining_minutes` (float or null), and `current_clean` (object or null)
