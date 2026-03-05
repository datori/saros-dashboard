## ADDED Requirements

### Requirement: CLI entry point
The system SHALL provide a `vacuum` CLI command installable via `pip install -e .` with subcommands for all vacuum operations.

#### Scenario: Help output
- **WHEN** user runs `vacuum --help`
- **THEN** the CLI SHALL display all available subcommands with descriptions

### Requirement: Status subcommand
The CLI SHALL provide a `vacuum status` subcommand displaying current vacuum state.

#### Scenario: Status display
- **WHEN** user runs `vacuum status`
- **THEN** the CLI SHALL print state, battery level, dock status, and any error in human-readable format

### Requirement: Clean subcommand
The CLI SHALL provide a `vacuum clean` subcommand to start a full home clean.

#### Scenario: Full clean
- **WHEN** user runs `vacuum clean`
- **THEN** the vacuum SHALL start cleaning and the CLI SHALL confirm with a success message

### Requirement: Stop, pause, and dock subcommands
The CLI SHALL provide `vacuum stop`, `vacuum pause`, and `vacuum dock` subcommands.

#### Scenario: Stop
- **WHEN** user runs `vacuum stop`
- **THEN** the vacuum SHALL stop cleaning

#### Scenario: Dock
- **WHEN** user runs `vacuum dock`
- **THEN** the vacuum SHALL return to its dock

### Requirement: Room clean subcommand
The CLI SHALL provide `vacuum rooms <room_name>...` accepting one or more room names and an optional `--repeat` flag.

#### Scenario: Single room clean
- **WHEN** user runs `vacuum rooms Kitchen`
- **THEN** the vacuum SHALL clean only the Kitchen segment

#### Scenario: Multi-room with repeat
- **WHEN** user runs `vacuum rooms Kitchen Office --repeat 2`
- **THEN** the vacuum SHALL clean both rooms twice each

### Requirement: Routine subcommand
The CLI SHALL provide `vacuum routine <name>` to trigger a named routine.

#### Scenario: Run routine
- **WHEN** user runs `vacuum routine "morning-clean"`
- **THEN** the named routine SHALL execute

#### Scenario: List routines
- **WHEN** user runs `vacuum routine --list`
- **THEN** the CLI SHALL print all available routine names

### Requirement: Locate subcommand
The CLI SHALL provide `vacuum locate` to play the locator sound.

#### Scenario: Locate
- **WHEN** user runs `vacuum locate`
- **THEN** the vacuum SHALL play the locator sound

### Requirement: Map subcommand
The CLI SHALL provide `vacuum map` to display room segment IDs and names.

#### Scenario: Map display
- **WHEN** user runs `vacuum map`
- **THEN** the CLI SHALL print a table of room names and their segment IDs

### Requirement: CLI error output
The CLI SHALL print actionable error messages to stderr and exit with a non-zero code on failure.

#### Scenario: Auth failure
- **WHEN** credentials are missing or invalid
- **THEN** the CLI SHALL print a clear error message to stderr and exit with code 1
