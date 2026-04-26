## ADDED Requirements

### Requirement: Priority queue preview endpoint
The system SHALL expose a `GET /api/window/preview` endpoint that returns the current priority queue for client-side planning.

#### Scenario: Rooms are overdue
- **WHEN** `GET /api/window/preview` is called and rooms are due today or overdue (`overdue_ratio >= 1.0` after scheduler day-quantization)
- **THEN** the response SHALL contain a `queue` array of entries sorted by priority_score descending, each with `segment_id`, `name`, `mode`, `estimated_sec`, `priority_score`, `overdue_ratio`, and `priority_weight`

#### Scenario: No rooms overdue
- **WHEN** `GET /api/window/preview` is called and no rooms are due today or overdue
- **THEN** the response SHALL contain an empty `queue` array

#### Scenario: Mixed modes in queue
- **WHEN** both vacuum and mop entries are overdue
- **THEN** all entries SHALL be returned in a single sorted list regardless of mode

### Requirement: Window planner panel
The dashboard SHALL display a "Window Planner" panel with a budget slider and priority queue preview.

#### Scenario: Panel initial state
- **WHEN** the planner panel loads
- **THEN** the slider SHALL default to 30 minutes with range 5–90, and the preview SHALL be fetched automatically on first load

#### Scenario: Slider adjustment
- **WHEN** the user moves the budget slider
- **THEN** the room list SHALL update immediately (client-side) showing which rooms would be cleaned at the new budget, without making an API call

#### Scenario: Room list display
- **WHEN** the preview is populated
- **THEN** selected rooms (that fit in budget) SHALL be shown with a filled indicator and cumulative time, and excluded rooms SHALL be shown with a hollow indicator below a visual divider

#### Scenario: Mode grouping in preview
- **WHEN** the priority queue contains entries of mixed modes
- **THEN** the preview SHALL select rooms matching the mode of the highest-priority entry, consistent with actual dispatch behavior

#### Scenario: Manual refresh
- **WHEN** the user clicks the refresh button
- **THEN** the system SHALL re-fetch `GET /api/window/preview` and update the display

#### Scenario: Summary line
- **WHEN** rooms are displayed
- **THEN** a summary SHALL show the count of selected rooms and the total estimated time versus budget (e.g., "3 rooms, 20 min of 22 min budget")

### Requirement: Open window from planner
The planner SHALL allow users to open a cleaning window directly at the previewed budget.

#### Scenario: Open window button
- **WHEN** the user clicks "Open Window" with the slider at N minutes
- **THEN** the system SHALL call `POST /api/window/open` with `{budget_min: N}` and update the window status display

#### Scenario: Window already active
- **WHEN** a window is already active and the user clicks "Open Window"
- **THEN** the window end time SHALL be extended using `max(current_end, now + budget)` consistent with existing window extension behavior
