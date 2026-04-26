## MODIFIED Requirements

### Requirement: Desktop cockpit layout
On viewports 900px wide or wider, the dashboard SHALL use a two-pane layout beneath a persistent status bar: a flex-1 Schedule pane on the left and a fixed-width (380px) tabbed right pane. There is no left sidebar. The status bar SHALL be ~44px tall and span the full width of the content area.

#### Scenario: Two-pane layout visible on desktop
- **WHEN** the viewport width is 900px or wider
- **THEN** a persistent status bar is shown at the top and the content area below shows the Schedule pane on the left (flex-1) and a 380px right pane

#### Scenario: No left sidebar on desktop
- **WHEN** the viewport width is 900px or wider
- **THEN** no left sidebar column is rendered; Status, Actions, and Consumables are not shown as standalone panels

#### Scenario: Schedule pane fills available space
- **WHEN** the viewport width is 900px or wider
- **THEN** the Schedule pane expands to fill all horizontal space not occupied by the 380px right pane

#### Scenario: Right pane stays in view while scrolling schedule
- **WHEN** the schedule content is taller than the viewport and the user scrolls
- **THEN** the right pane remains fixed (sticky) at the top of the viewport

### Requirement: Persistent status bar
The dashboard SHALL display a persistent compact status bar (~44px tall) above the main content area on all viewport widths. The status bar SHALL show: current state badge, battery progress bar and percentage, dock status indicator, window planner active indicator, and five action buttons (Start, Stop, Pause, Dock, Locate) as icon-only buttons. The status bar SHALL remain visible regardless of which tab or panel is active.

#### Scenario: Status bar always visible on desktop
- **WHEN** the viewport is 900px or wider and any right-pane tab is active
- **THEN** the status bar is visible at the top of the content area showing state, battery, dock status, and action buttons

#### Scenario: Status bar always visible on mobile
- **WHEN** the viewport is less than 900px and any mobile tab is active
- **THEN** the status bar is visible at the top of the page showing state, battery, dock status, and action buttons

#### Scenario: Status bar stale indicator
- **WHEN** the status data has not been refreshed within the stale threshold
- **THEN** the status bar applies reduced opacity or shows a stale indicator (⏱) to signal the data may be outdated

#### Scenario: Error code shown in status bar
- **WHEN** the device reports a non-zero error code
- **THEN** the status bar displays the error code alongside the state badge

### Requirement: Desktop right-pane tab bar
The right pane SHALL display a horizontal tab bar with three tabs: **Clean**, **Triggers**, and **History**. The active tab's panels SHALL be visible; all other panels SHALL be hidden.

#### Scenario: Clean tab shows room and routine panels
- **WHEN** the Clean tab is active
- **THEN** the Clean Rooms panel and the Routines panel are visible in the right pane

#### Scenario: Triggers tab shows triggers and planner
- **WHEN** the Triggers tab is active
- **THEN** the Auto-Clean Triggers panel and the Window Planner panel are visible in the right pane

#### Scenario: History tab shows history, consumables, and settings
- **WHEN** the History tab is active
- **THEN** the Clean History panel, the Consumables panel, and the Clean Settings panel are visible in the right pane

### Requirement: Desktop right-pane tab state persistence
The active right-pane tab SHALL be stored in `sessionStorage` under the key `activeRightTab`. On page load, the stored tab SHALL be restored if it matches a valid tab name (`clean`, `triggers`, or `history`). If the stored value does not match, the default tab **Clean** SHALL be used.

#### Scenario: Right pane tab persists after reload
- **WHEN** the user selects the Triggers tab and reloads the page (viewport ≥ 900px)
- **THEN** the Triggers tab is still active after reload

#### Scenario: Invalid stored tab value falls back to default
- **WHEN** the stored `activeRightTab` value is not one of `clean`, `triggers`, or `history`
- **THEN** the Clean tab is shown as the default

### Requirement: Desktop sidebar Actions panel — quick buttons only
On desktop, action buttons SHALL appear in the persistent status bar as icon-only buttons. No separate Actions panel SHALL exist in the layout.

#### Scenario: Action buttons in status bar on desktop
- **WHEN** the viewport is 900px or wider
- **THEN** Start, Stop, Pause, Dock, and Locate buttons are rendered inside the status bar with icon-only display

### Requirement: Cockpit layout hidden on mobile
On viewports narrower than 900px, the two-pane cockpit layout (Schedule pane + right-pane tab bar) SHALL not be rendered. The mobile layout (bottom tab bar + single-column content) takes over.

#### Scenario: Cockpit layout hidden on mobile
- **WHEN** the viewport width is less than 900px
- **THEN** the Schedule pane and right-pane tab bar are not visible; the mobile tab layout is shown instead

## REMOVED Requirements

### Requirement: Desktop sidebar Actions panel — quick buttons only (original)
**Reason**: The left sidebar is eliminated; action buttons move to the persistent status bar.
**Migration**: Action buttons now render in `StatusBar` component; `ActionsPanel` component is no longer rendered.

### Requirement: Rooms tab scope toggle
**Reason**: The "Rooms" tab is renamed to "Clean" and now also includes Routines. The scope toggle behavior itself is unchanged — only the tab name and grouping change.
**Migration**: No user-facing change to the toggle behavior. Update tab name from "Rooms" to "Clean" in tab bar.
