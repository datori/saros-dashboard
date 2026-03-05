## ADDED Requirements

### Requirement: MCP tool — get cleaning schedule
The MCP server SHALL expose a tool to retrieve the full cleaning schedule status for all rooms.

#### Scenario: Schedule returned
- **WHEN** `get_cleaning_schedule()` is called via MCP
- **THEN** the tool SHALL return all rooms with their last_vacuumed, last_mopped, overdue ratios, configured intervals, and notes

#### Scenario: Unscheduled rooms included
- **WHEN** some rooms have no interval configured
- **THEN** they SHALL be included in the response with null interval and ratio fields

### Requirement: MCP tool — set room interval
The MCP server SHALL expose a tool to configure cleaning intervals per room.

#### Scenario: Set vacuum interval by name
- **WHEN** `set_room_interval(room="Kitchen", mode="vacuum", days=2.0)` is called
- **THEN** the scheduler SHALL update the Kitchen's vacuum_days to 2.0 and return confirmation

#### Scenario: Set mop interval by name
- **WHEN** `set_room_interval(room="Living Room", mode="mop", days=7.0)` is called
- **THEN** the scheduler SHALL update mop_days for Living Room to 7.0

#### Scenario: Unknown room rejected
- **WHEN** `set_room_interval(room="Garage", ...)` is called and no room named "Garage" exists
- **THEN** the tool SHALL raise an error listing available room names

### Requirement: MCP tool — get overdue rooms
The MCP server SHALL expose a tool to list rooms that are past their cleaning interval.

#### Scenario: Overdue rooms listed
- **WHEN** `get_overdue_rooms()` is called
- **THEN** the tool SHALL return rooms where overdue_ratio ≥ 1.0, sorted by ratio descending, for each configured mode

#### Scenario: Nothing overdue
- **WHEN** all configured rooms are within schedule
- **THEN** the tool SHALL return an empty list with a message indicating no rooms are overdue

### Requirement: MCP tool — plan clean
The MCP server SHALL expose a tool that recommends which rooms to clean given a time budget.

#### Scenario: Plan with time budget
- **WHEN** `plan_clean(max_minutes=45)` is called
- **THEN** the tool SHALL return the recommended rooms sorted by overdue priority, their estimated total duration, and which rooms were deferred and why

#### Scenario: Plan without time budget
- **WHEN** `plan_clean()` is called with no max_minutes
- **THEN** the tool SHALL return all overdue rooms sorted by priority with no budget constraint applied

#### Scenario: Mode filter
- **WHEN** `plan_clean(mode="vacuum")` is called
- **THEN** only vacuum overdue ratios SHALL be used for ranking and selection

### Requirement: MCP tool — set room notes
The MCP server SHALL expose a tool to attach free-text notes to a room's schedule entry.

#### Scenario: Notes saved
- **WHEN** `set_room_notes(room="Bedroom", notes="Pets sleep here, prioritize")` is called
- **THEN** the note SHALL be persisted and returned in subsequent schedule queries
