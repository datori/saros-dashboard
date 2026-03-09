## ADDED Requirements

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

### Requirement: Dispatch loop
The system SHALL automatically dispatch cleans while a window is open and rooms need cleaning.

#### Scenario: Window open, rooms overdue, vacuum idle
- **WHEN** the health poller detects an open window, the vacuum is idle/docked, and rooms are overdue
- **THEN** the system SHALL select rooms by priority score, batch them within the remaining window time, and dispatch via `clean_rooms()`

#### Scenario: Window open, no rooms overdue
- **WHEN** the health poller detects an open window but no rooms have overdue_ratio >= 1.0
- **THEN** no dispatch SHALL occur and the window SHALL remain open (in case rooms become overdue or the threshold is already met for a different mode)

#### Scenario: Window open, vacuum already cleaning
- **WHEN** the health poller detects an open window and the vacuum is actively cleaning
- **THEN** no new dispatch SHALL occur; the completion monitor SHALL handle the active clean

#### Scenario: Clean completes with window time remaining
- **WHEN** a clean completes successfully, the window is still active, and additional rooms are overdue
- **THEN** the dispatch loop SHALL select and dispatch the next batch of rooms within the remaining window time

#### Scenario: Clean completes with no window time remaining
- **WHEN** a clean completes and the window has expired
- **THEN** no further dispatch SHALL occur

### Requirement: Batch selection within window
The system SHALL select rooms that fit within the remaining window time.

#### Scenario: All overdue rooms fit
- **WHEN** the estimated duration of all overdue rooms is less than remaining window time
- **THEN** all overdue rooms SHALL be included in the batch

#### Scenario: Partial fit
- **WHEN** not all overdue rooms fit within remaining window time
- **THEN** rooms SHALL be selected in priority score order until adding the next room would exceed remaining time

#### Scenario: No room fits
- **WHEN** the remaining window time is less than the estimated duration of any single overdue room
- **THEN** no dispatch SHALL occur for that cycle

#### Scenario: Unknown duration room
- **WHEN** a room's duration cannot be estimated
- **THEN** it SHALL be included in the batch without budget deduction, with a note logged
