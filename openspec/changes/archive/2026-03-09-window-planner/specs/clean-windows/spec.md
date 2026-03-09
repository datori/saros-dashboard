## MODIFIED Requirements

### Requirement: Window state management
The system SHALL maintain a single active cleaning window represented by an end timestamp.

#### Scenario: No window active
- **WHEN** no trigger has been fired or the window has expired
- **THEN** `_window_end` SHALL be `None` and no automatic dispatch SHALL occur

#### Scenario: Window expires naturally
- **WHEN** the current time exceeds `_window_end`
- **THEN** the window SHALL be considered closed and any pending trigger events SHALL have `returned_at` set

#### Scenario: Window active check
- **WHEN** the dispatch loop checks window state
- **THEN** the window SHALL be considered active if and only if `_window_end is not None and now < _window_end`

#### Scenario: Open window directly
- **WHEN** `POST /api/window/open` is called with `{budget_min: N}`
- **THEN** the system SHALL call `_open_window(N)` to set or extend the window end time, and return the updated window status
