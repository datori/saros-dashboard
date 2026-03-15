## ADDED Requirements

### Requirement: Shoelace loaded via CDN
The dashboard SHALL load Shoelace 2.x dark theme CSS and the Shoelace autoloader JS from jsDelivr CDN in the `<head>`. The `<body>` element SHALL have `class="sl-theme-dark"` applied.

#### Scenario: Shoelace dark theme active
- **WHEN** the dashboard page loads
- **THEN** Shoelace components render using the dark colour theme without any additional CSS overrides

#### Scenario: Autoloader resolves components
- **WHEN** a Shoelace custom element (e.g. `<sl-button>`) appears in the DOM
- **THEN** the autoloader fetches and registers the component definition automatically

### Requirement: Action buttons use sl-button
All five action buttons (Start, Stop, Pause, Dock, Locate) in the Actions panel SHALL use `<sl-button>`. Variants SHALL map as: Start → `primary`, Stop → `danger`, Pause → `warning`, Dock and Locate → `default`.

#### Scenario: Action buttons render as sl-button
- **WHEN** the dashboard loads
- **THEN** the Actions panel contains five `<sl-button>` elements with correct variants

#### Scenario: Routine Run buttons use sl-button
- **WHEN** routines are loaded
- **THEN** each routine's Run button is an `<sl-button variant="primary" size="small">`

### Requirement: All dropdowns use sl-select
Every dropdown in the dashboard SHALL use `<sl-select>` with `<sl-option>` children. This includes: Clean Mode, Fan Speed, Mop Mode, Water Flow, Route (in Clean Rooms panel), Fan Speed, Mop Mode, Water Flow (in Clean Settings panel), and all Dispatch Settings selects.

#### Scenario: sl-select exposes value property
- **WHEN** JavaScript reads the `.value` property of a dropdown
- **THEN** `sl-select.value` returns the selected option string, identical in behaviour to native `<select>.value`

#### Scenario: sl-select change events wired correctly
- **WHEN** the user changes a dropdown value
- **THEN** the `sl-change` event fires and any associated handler (e.g. `applyCleanMode`) executes correctly

### Requirement: Status badges use sl-badge
State, dock status, error, and battery level indicators in the Status panel SHALL use `<sl-badge>`. Variants SHALL map as: green states → `success`, yellow/warning states → `warning`, red/error states → `danger`, neutral states → `neutral`.

#### Scenario: State badge renders correctly
- **WHEN** the vacuum state is "charging"
- **THEN** a `<sl-badge variant="success">` displays the state string

### Requirement: Consumable progress bars use sl-progress-bar
Each consumable indicator (Main brush, Side brush, Filter, Sensors) in the Consumables panel SHALL use `<sl-progress-bar>` with `value` set to the percentage. The label SHALL display the percentage text.

#### Scenario: Progress bar reflects consumable percentage
- **WHEN** consumables data loads with main brush at 80%
- **THEN** `<sl-progress-bar value="80">` renders with the filled bar at 80%

#### Scenario: Low consumable shows warning colour
- **WHEN** a consumable is below 20%
- **THEN** the `<sl-progress-bar>` has a custom style or class indicating warning/danger

### Requirement: Right-pane tabs use sl-tab-group
The desktop right-pane tab bar SHALL use `<sl-tab-group>` with `<sl-tab slot="nav">` and `<sl-tab-panel>` elements replacing the current `#right-tab-bar` div + CSS `[data-right-tab]` visibility rules.

#### Scenario: Selecting a right-pane tab shows its panel
- **WHEN** the user clicks a tab in the right pane on desktop
- **THEN** `sl-tab-group` shows the corresponding `<sl-tab-panel>` and hides all others

#### Scenario: Right-pane tab state persists across reload
- **WHEN** the user selects the Triggers tab and reloads the page
- **THEN** the `sl-tab-group` restores to the Triggers tab on load (via `customElements.whenDefined` + `tabGroup.show()`)

### Requirement: Scope toggle uses sl-radio-group
The All rooms / Select rooms scope toggle in the Clean Rooms panel SHALL use `<sl-radio-group>` with `<sl-radio-button>` children rendered as a pill/segmented control (`size="small"`).

#### Scenario: Scope toggle renders as segmented control
- **WHEN** the Clean Rooms panel is visible
- **THEN** "All rooms" and "Select rooms" appear as adjacent pill-style radio buttons

#### Scenario: Scope toggle change fires updateCleanScope
- **WHEN** the user selects "All rooms"
- **THEN** the `sl-change` event on `<sl-radio-group>` fires `updateCleanScope()` and hides the room checkbox list
