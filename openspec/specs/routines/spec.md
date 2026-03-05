## ADDED Requirements

### Requirement: Composable routine definitions
The system SHALL provide a routines module where multi-step automation sequences are defined as Python async functions using the vacuum client.

#### Scenario: Routine executes steps in order
- **WHEN** a routine function is called
- **THEN** it SHALL execute each step sequentially, waiting for each to complete before proceeding

### Requirement: Morning clean routine
The system SHALL include a `morning_clean` routine that runs a full home clean and docks when complete.

#### Scenario: Morning clean
- **WHEN** `morning_clean()` is called
- **THEN** the vacuum SHALL start a full clean, and upon completion return to dock

### Requirement: Targeted room routine
The system SHALL include a `clean_rooms_then_dock` routine accepting a list of room names, cleaning each in sequence then docking.

#### Scenario: Targeted room sequence
- **WHEN** `clean_rooms_then_dock(["Kitchen", "Dining Room"])` is called
- **THEN** the vacuum SHALL clean those rooms in order then return to dock

### Requirement: Routine status reporting
Each routine SHALL log its steps to stdout so the caller can observe progress.

#### Scenario: Step logging
- **WHEN** a routine is running
- **THEN** each step SHALL print a status line (e.g., "Starting kitchen clean...")

### Requirement: Routine error handling
Routines SHALL catch vacuum client errors, log the failure, and attempt to return the vacuum to dock before re-raising.

#### Scenario: Mid-routine failure
- **WHEN** a step in a routine raises an error
- **THEN** the routine SHALL log the error, issue a dock command, and re-raise the exception
