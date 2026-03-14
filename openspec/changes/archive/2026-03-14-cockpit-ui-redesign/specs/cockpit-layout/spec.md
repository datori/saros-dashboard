## ADDED Requirements

### Requirement: Desktop cockpit layout
On viewports 900px wide or wider, the dashboard SHALL use a two-column cockpit layout: a fixed-width sidebar (240px) on the left containing the Status, Actions, and Consumables panels; and a scrollable right pane containing all other panels organized under a horizontal tab bar.

#### Scenario: Sidebar visible on desktop
- **WHEN** the viewport width is 900px or wider
- **THEN** a 240px fixed sidebar is visible containing Status, Actions, and Consumables panels

#### Scenario: Sidebar stays in view while scrolling right pane
- **WHEN** the right pane content is taller than the viewport and the user scrolls down
- **THEN** the sidebar remains fixed at the top of the viewport (sticky)

#### Scenario: Right pane is scrollable
- **WHEN** the right pane content exceeds viewport height
- **THEN** only the right pane scrolls; the sidebar does not scroll

### Requirement: Desktop right-pane tab bar
The right pane SHALL display a horizontal tab bar with four tabs: **Rooms**, **Routines**, **Triggers**, and **Info**. The active tab's panels SHALL be visible; all other panels SHALL be hidden.

#### Scenario: Rooms tab shows room panels
- **WHEN** the Rooms tab is active
- **THEN** the Clean Rooms panel (with scope toggle and override controls) is visible

#### Scenario: Routines tab shows routines panel
- **WHEN** the Routines tab is active
- **THEN** the Routines panel is visible

#### Scenario: Triggers tab shows triggers and planner
- **WHEN** the Triggers tab is active
- **THEN** the Auto-Clean Triggers panel and Window Planner panel are visible

#### Scenario: Info tab shows settings, schedule, and history
- **WHEN** the Info tab is active
- **THEN** the Clean Settings panel, Cleaning Schedule panel, and Clean History panel are visible

### Requirement: Desktop right-pane tab state persistence
The active right-pane tab SHALL be stored in `sessionStorage` under the key `activeRightTab`. On page load, the stored tab SHALL be restored. Default tab is **Rooms**.

#### Scenario: Right pane tab persists after reload
- **WHEN** the user selects the Triggers tab and reloads the page (viewport ≥ 900px)
- **THEN** the Triggers tab is still active after reload

### Requirement: Desktop sidebar Actions panel — quick buttons only
On desktop, the Actions panel in the sidebar SHALL display only the five action buttons (Start, Stop, Pause, Dock, Locate) with no override dropdowns. Override controls (fan speed, water flow, mode) are available in the Rooms tab.

#### Scenario: No override dropdowns in sidebar Actions
- **WHEN** the viewport is 900px or wider
- **THEN** the Actions panel contains Start, Stop, Pause, Dock, and Locate buttons and no fan speed, water flow, or clean mode selects

### Requirement: Rooms tab scope toggle
The Clean Rooms panel SHALL include a toggle (radio or segmented control) at the top to select scope: **All rooms** or **Select rooms**. When **All rooms** is active, the room checkbox list SHALL be hidden. Override settings (fan speed, water flow, clean mode, route, repeat) SHALL be visible for both scope values.

#### Scenario: All rooms scope hides checkbox list
- **WHEN** the user selects "All rooms" scope
- **THEN** the room checkbox list is hidden and the override controls remain visible

#### Scenario: Select rooms scope shows checkbox list
- **WHEN** the user selects "Select rooms" scope
- **THEN** the room checkbox list is visible alongside the override controls

#### Scenario: Start Clean respects scope
- **WHEN** "All rooms" scope is selected and the user clicks Start Clean
- **THEN** `doAction('start')` is called with the current override values

#### Scenario: Start Clean with rooms respects scope
- **WHEN** "Select rooms" scope is selected, at least one room is checked, and the user clicks Start Clean
- **THEN** `cleanRooms()` is called with the checked segment IDs and override values

### Requirement: Cockpit layout hidden on mobile
On viewports narrower than 900px, the cockpit layout (sidebar + right-pane tab bar) SHALL not be rendered. The mobile layout (bottom tab bar) takes over.

#### Scenario: Sidebar hidden on mobile
- **WHEN** the viewport width is less than 900px
- **THEN** no sidebar is visible; the layout is single-column
