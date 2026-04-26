## MODIFIED Requirements

### Requirement: Mobile bottom tab bar
The dashboard SHALL display a fixed bottom tab bar on viewports narrower than 900px. The tab bar SHALL contain three tabs: **Schedule**, **Clean**, and **History**. On viewports 900px and wider, the tab bar SHALL be hidden and the cockpit layout (status bar + two-pane) takes over.

#### Scenario: Tab bar visible on mobile with three tabs
- **WHEN** the viewport width is less than 900px
- **THEN** a fixed bottom navigation bar with three tabs (Schedule, Clean, History) is visible

#### Scenario: Tab bar hidden on desktop
- **WHEN** the viewport width is 900px or wider
- **THEN** no bottom tab bar is shown and the two-pane cockpit layout is active

### Requirement: Panel tab assignment
Each dashboard panel SHALL be assigned to exactly one mobile tab. Assignments SHALL be:
- **Schedule**: Cleaning Schedule panel (full width)
- **Clean**: Clean Rooms panel (with scope toggle + overrides), Routines panel, Auto-Clean Triggers panel, Window Planner panel
- **History**: Clean History panel, Consumables panel, Clean Settings panel

#### Scenario: Schedule tab shows schedule panel
- **WHEN** the user taps the Schedule tab
- **THEN** only the Cleaning Schedule panel is visible; all other panels are hidden

#### Scenario: Clean tab shows clean and trigger panels
- **WHEN** the user taps the Clean tab
- **THEN** the Clean Rooms panel, Routines panel, Auto-Clean Triggers panel, and Window Planner panel are visible; all other panels are hidden

#### Scenario: History tab shows history, consumables, and settings
- **WHEN** the user taps the History tab
- **THEN** the Clean History panel, Consumables panel, and Clean Settings panel are visible; all other panels are hidden

### Requirement: Tab state persistence
The active tab SHALL be stored in `sessionStorage` under the key `activeTab`. On page load, the stored tab SHALL be restored if it matches a valid tab name (`schedule`, `clean`, or `history`). If the stored value does not match, the default tab **Schedule** SHALL be used.

#### Scenario: Tab persists after reload
- **WHEN** the user selects the History tab and then reloads the page (viewport < 900px)
- **THEN** the History tab is still active after reload

#### Scenario: Invalid stored tab falls back to Schedule
- **WHEN** the stored `activeTab` value is not one of `schedule`, `clean`, or `history` (e.g. an old value like `"now"` or `"plan"`)
- **THEN** the Schedule tab is shown as the default

### Requirement: Default tab on first load
On first page load with no stored tab preference, the **Schedule** tab SHALL be active.

#### Scenario: Default tab is Schedule
- **WHEN** the page loads and no tab preference is stored (or stored value is invalid)
- **THEN** the Schedule tab is active

### Requirement: Active tab visual indicator
The active tab button SHALL have a visually distinct style (accent color) compared to inactive tab buttons.

#### Scenario: Active tab highlighted
- **WHEN** the History tab is active
- **THEN** the History tab button is highlighted with the accent color; Schedule and Clean buttons are dimmed

### Requirement: iOS safe area inset for tab bar
The tab bar SHALL apply `padding-bottom: env(safe-area-inset-bottom)` so that it does not overlap the iOS home indicator on notched devices.

#### Scenario: Tab bar respects home indicator
- **WHEN** the app is running in standalone PWA mode on iPhone
- **THEN** tab bar content is above the home indicator swipe zone
