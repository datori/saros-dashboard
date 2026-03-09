## ADDED Requirements

### Requirement: Table scroll wrapper
Both the History table and the Schedule table SHALL be wrapped in a `<div class="table-scroll">` element with `overflow-x: auto` and `-webkit-overflow-scrolling: touch`, preventing the table from causing the page to overflow horizontally.

#### Scenario: Table is scrollable on narrow viewport
- **WHEN** the viewport is 390px wide and a table has more columns than fit
- **THEN** the table scrolls horizontally within its panel without causing page-level overflow

### Requirement: Hide non-essential columns on mobile
Secondary columns SHALL be hidden on viewports narrower than 640px via a `hide-mobile` CSS class. The following columns SHALL be hidden on mobile:
- **History table**: "Started by", "Type", "Finish reason" (both `<th>` and all `<td>` in that column)
- **Schedule table**: "Last Vacuumed", "Last Mopped" (both `<th>` and all `<td>` in that column)

The following columns SHALL remain visible on mobile:
- **History**: Start, Duration, Area (m²), Complete
- **Schedule**: Room, Vacuum Due, Mop Due, Vacuum Every, Mop Every, Edit button

#### Scenario: Secondary columns hidden on mobile
- **WHEN** the viewport width is less than 640px
- **THEN** the "Started by", "Type", and "Finish reason" columns are not visible in the History table

#### Scenario: Secondary columns visible on desktop
- **WHEN** the viewport width is 640px or wider
- **THEN** all History and Schedule columns are visible

#### Scenario: Core columns always visible
- **WHEN** viewing the History table on any viewport
- **THEN** Start, Duration, Area, and Complete columns are always shown
