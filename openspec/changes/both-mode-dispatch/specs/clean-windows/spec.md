## MODIFIED Requirements

### Requirement: Dispatch loop
The system SHALL automatically dispatch cleans while a window is open, using the window's mode to drive room selection and dispatch settings.

#### Scenario: Window open, vacuum mode, rooms overdue
- **WHEN** `_window_mode == "vacuum"`, the vacuum is idle/docked, and rooms have `vacuum_overdue_ratio >= 1.0`
- **THEN** the system SHALL select vacuum-overdue rooms by priority score, fit them within the remaining window time, apply `dispatch_settings["vacuum"]`, and log the event as `mode="vacuum"`

#### Scenario: Window open, mop mode, rooms overdue
- **WHEN** `_window_mode == "mop"`, the vacuum is idle/docked, and rooms have `mop_overdue_ratio >= 1.0`
- **THEN** the system SHALL select mop-overdue rooms by priority score, fit them within the remaining window time, apply `dispatch_settings["mop"]`, and log the event as `mode="mop"`

#### Scenario: Window open, both mode, rooms overdue
- **WHEN** `_window_mode == "both"`, the vacuum is idle/docked, and rooms have `mop_overdue_ratio >= 1.0`
- **THEN** the system SHALL select mop-overdue rooms by priority score (same pool as mop mode), fit them within the remaining window time, apply `dispatch_settings["both"]`, and log the event as `mode="both"`

#### Scenario: Window open, both mode, no mop-overdue rooms
- **WHEN** `_window_mode == "both"` but no rooms have `mop_overdue_ratio >= 1.0`
- **THEN** no dispatch SHALL occur (same behaviour as mop mode with no overdue rooms)

#### Scenario: Window open, no rooms overdue
- **WHEN** the health poller detects an open window but no rooms match the window mode's overdue criteria
- **THEN** no dispatch SHALL occur and the window SHALL remain open

#### Scenario: Window open, vacuum already cleaning
- **WHEN** the health poller detects an open window and the vacuum is actively cleaning
- **THEN** no new dispatch SHALL occur; the completion monitor SHALL handle the active clean

#### Scenario: Clean completes with window time remaining
- **WHEN** a clean completes successfully, the window is still active, and additional rooms are overdue
- **THEN** the dispatch loop SHALL select and dispatch the next batch within the remaining window time

#### Scenario: Clean completes with no window time remaining
- **WHEN** a clean completes and the window has expired
- **THEN** no further dispatch SHALL occur

## ADDED Requirements

### Requirement: Manual window open with mode
The system SHALL accept an optional mode when manually opening a window via the API.

#### Scenario: Open window with explicit mode
- **WHEN** `POST /api/window/open` is called with `{budget_min: 30, mode: "both"}`
- **THEN** the window SHALL open for 30 minutes and `_window_mode` SHALL be set to `"both"`

#### Scenario: Open window without mode
- **WHEN** `POST /api/window/open` is called with `{budget_min: 30}` and no mode
- **THEN** the window SHALL open for 30 minutes and `_window_mode` SHALL default to `"vacuum"`
