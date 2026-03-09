## MODIFIED Requirements

### Requirement: Dispatch loop
The system SHALL automatically dispatch cleans while a window is open and rooms need cleaning.

#### Scenario: Window open, rooms overdue, vacuum idle
- **WHEN** the health poller detects an open window, the vacuum is idle/docked, and rooms are overdue
- **THEN** the system SHALL select rooms by priority score, batch them within the remaining window time, load dispatch settings for the batch's mode, and dispatch via `clean_rooms()` with those settings applied

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
