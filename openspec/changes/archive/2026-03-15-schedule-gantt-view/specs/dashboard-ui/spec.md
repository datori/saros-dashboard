## ADDED Requirements

### Requirement: Schedule panel visual
The dashboard SHALL display the cleaning schedule as a Gantt timeline visualization. The previous table layout (text columns for Vac Due, Mop Due, Every) SHALL be replaced by the timeline track view defined in the `schedule-gantt` spec. The panel title, tab placement (Info tab on mobile, Info right-tab on desktop), and Edit room functionality (via EditModal) SHALL remain unchanged.

#### Scenario: Schedule panel renders Gantt not table
- **WHEN** the Info tab / Info right-tab is active and schedule data is loaded
- **THEN** the panel renders track rows with gradient bands and event dots, not a table with text date columns

#### Scenario: Edit room button still accessible
- **WHEN** user interacts with a room row
- **THEN** an Edit button remains accessible that opens the EditModal for interval and notes configuration
