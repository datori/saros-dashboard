## ADDED Requirements

### Requirement: MCP server exposes vacuum control tools
The system SHALL provide an MCP server that exposes vacuum operations as callable tools consumable by Claude or any MCP-compatible client.

#### Scenario: Server starts and lists tools
- **WHEN** the MCP server is started
- **THEN** it SHALL advertise all vacuum tools with names, descriptions, and input schemas

### Requirement: Status tool
The server SHALL expose a `vacuum_status` tool returning the current vacuum state.

#### Scenario: Status query via MCP
- **WHEN** an MCP client calls `vacuum_status` with no arguments
- **THEN** the tool SHALL return a JSON object with state, battery, dock status, and any active error

### Requirement: Start cleaning tool
The server SHALL expose a `start_cleaning` tool that begins a full home clean.

#### Scenario: Full clean initiated via MCP
- **WHEN** an MCP client calls `start_cleaning`
- **THEN** the vacuum SHALL begin cleaning and the tool SHALL return a success confirmation

### Requirement: Stop and pause tools
The server SHALL expose `stop_cleaning` and `pause_cleaning` tools.

#### Scenario: Stop via MCP
- **WHEN** an MCP client calls `stop_cleaning`
- **THEN** the vacuum SHALL stop and the tool SHALL confirm

#### Scenario: Pause via MCP
- **WHEN** an MCP client calls `pause_cleaning`
- **THEN** the vacuum SHALL pause in place

### Requirement: Return to dock tool
The server SHALL expose a `return_to_dock` tool.

#### Scenario: Dock command via MCP
- **WHEN** an MCP client calls `return_to_dock`
- **THEN** the vacuum SHALL navigate to the dock

### Requirement: Locate tool
The server SHALL expose a `locate_vacuum` tool that plays the locator sound.

#### Scenario: Locate via MCP
- **WHEN** an MCP client calls `locate_vacuum`
- **THEN** the vacuum SHALL play the locator sound

### Requirement: Room clean tool
The server SHALL expose a `room_clean` tool accepting room names or segment IDs and optional repeat count.

#### Scenario: Room clean by name via MCP
- **WHEN** an MCP client calls `room_clean` with `rooms=["Kitchen"]`
- **THEN** the server SHALL resolve room names to segment IDs and initiate cleaning

### Requirement: Zone clean tool
The server SHALL expose a `zone_clean` tool accepting a list of coordinate rectangles.

#### Scenario: Zone clean via MCP
- **WHEN** an MCP client calls `zone_clean` with coordinate zones
- **THEN** the vacuum SHALL clean the specified areas

### Requirement: Get map tool
The server SHALL expose a `get_map` tool returning map data and room segment information.

#### Scenario: Map retrieval via MCP
- **WHEN** an MCP client calls `get_map`
- **THEN** the tool SHALL return room names, segment IDs, and map metadata

### Requirement: Run routine tool
The server SHALL expose a `run_routine` tool accepting a routine name.

#### Scenario: Routine triggered via MCP
- **WHEN** an MCP client calls `run_routine` with a valid routine name
- **THEN** the routine SHALL execute and the tool SHALL confirm

### Requirement: MCP tool error handling
The server SHALL return structured error responses for all tool failures rather than crashing.

#### Scenario: Command fails
- **WHEN** a tool call results in an API error or invalid argument
- **THEN** the tool SHALL return an error content block with a human-readable message
