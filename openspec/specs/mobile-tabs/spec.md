## ADDED Requirements

### Requirement: Mobile bottom tab bar
The dashboard SHALL display a fixed bottom tab bar on viewports narrower than 900px. The tab bar SHALL contain four tabs: **Now**, **Clean**, **Plan**, and **Info**. On viewports 900px and wider, the tab bar SHALL be hidden and the cockpit layout (sidebar + right-pane tabs) takes over.

#### Scenario: Tab bar visible on mobile
- **WHEN** the viewport width is less than 900px
- **THEN** a fixed bottom navigation bar with four tabs (Now, Clean, Plan, Info) is visible

#### Scenario: Tab bar hidden on desktop
- **WHEN** the viewport width is 900px or wider
- **THEN** no bottom tab bar is shown and the cockpit layout is active

### Requirement: Panel tab assignment
Each dashboard panel SHALL be assigned to exactly one mobile tab via a `data-tab` attribute. Assignments SHALL be:
- **Now**: Cleaning Schedule panel, Status panel, Actions panel
- **Clean**: Clean Rooms panel (with scope toggle + overrides), Routines panel
- **Plan**: Window Planner panel, Auto-Clean Triggers panel
- **Info**: Clean Settings panel, Consumables panel, Clean History panel

#### Scenario: Active tab shows its panels
- **WHEN** the user taps a tab
- **THEN** only panels assigned to that tab are visible; all other panels are hidden

#### Scenario: Default tab on first load
- **WHEN** the page loads and no tab preference is stored
- **THEN** the Now tab is active

### Requirement: Tab state persistence
The active tab SHALL be stored in `sessionStorage` under the key `activeTab`. On page load, the stored tab SHALL be restored.

#### Scenario: Tab persists after reload
- **WHEN** the user selects the Plan tab and then reloads the page (viewport < 900px)
- **THEN** the Plan tab is still active after reload

### Requirement: Active tab visual indicator
The active tab button SHALL have a visually distinct style (accent color) compared to inactive tab buttons.

#### Scenario: Active tab highlighted
- **WHEN** the Plan tab is active
- **THEN** the Plan tab button is highlighted with the accent color; Now, Clean, and Info buttons are dimmed

### Requirement: iOS safe area inset for tab bar
The tab bar SHALL apply `padding-bottom: env(safe-area-inset-bottom)` so that it does not overlap the iOS home indicator on notched devices.

#### Scenario: Tab bar respects home indicator
- **WHEN** the app is running in standalone PWA mode on iPhone
- **THEN** tab bar content is above the home indicator swipe zone
