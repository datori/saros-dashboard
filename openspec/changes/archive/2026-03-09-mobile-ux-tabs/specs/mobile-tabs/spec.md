## ADDED Requirements

### Requirement: Mobile bottom tab bar
The dashboard SHALL display a fixed bottom tab bar on viewports narrower than 640px. The tab bar SHALL contain three tabs: **Home**, **Clean**, and **Info**. On viewports 640px and wider, the tab bar SHALL be hidden and all panels SHALL be visible simultaneously.

#### Scenario: Tab bar visible on mobile
- **WHEN** the viewport width is less than 640px
- **THEN** a fixed bottom navigation bar with three tabs (Home, Clean, Info) is visible

#### Scenario: Tab bar hidden on desktop
- **WHEN** the viewport width is 640px or wider
- **THEN** no tab bar is shown and all panels are visible in the grid layout

### Requirement: Panel tab assignment
Each dashboard panel SHALL be assigned to exactly one tab via a `data-tab` attribute. Assignments SHALL be:
- **Home**: Status panel, Actions panel, Consumables panel
- **Clean**: Clean Rooms panel, Clean Settings panel, Routines panel
- **Info**: Schedule panel, History panel

#### Scenario: Active tab shows its panels
- **WHEN** the user taps a tab
- **THEN** only panels assigned to that tab are visible; all other panels are hidden

#### Scenario: Default tab on first load
- **WHEN** the page loads and no tab preference is stored
- **THEN** the Home tab is active

### Requirement: Tab state persistence
The active tab SHALL be stored in `sessionStorage` under the key `activeTab`. On page load, the stored tab SHALL be restored.

#### Scenario: Tab persists after reload
- **WHEN** the user selects the Clean tab and then reloads the page
- **THEN** the Clean tab is still active after reload

### Requirement: Active tab visual indicator
The active tab button SHALL have a visually distinct style (accent color) compared to inactive tab buttons.

#### Scenario: Active tab highlighted
- **WHEN** the Info tab is active
- **THEN** the Info tab button is highlighted with the accent color; Home and Clean buttons are dimmed

### Requirement: iOS safe area inset for tab bar
The tab bar SHALL apply `padding-bottom: env(safe-area-inset-bottom)` so that it does not overlap the iOS home indicator on notched devices.

#### Scenario: Tab bar respects home indicator
- **WHEN** the app is running in standalone PWA mode on iPhone
- **THEN** tab bar content is above the home indicator swipe zone
