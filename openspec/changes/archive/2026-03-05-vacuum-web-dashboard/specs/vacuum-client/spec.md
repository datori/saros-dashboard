## ADDED Requirements

### Requirement: Consumables retrieval
The system SHALL retrieve consumable usage data including main brush, side brush, and filter life.

#### Scenario: Consumables returned
- **WHEN** `get_consumables()` is called
- **THEN** the response SHALL include percentage remaining for main brush, side brush, and filter

#### Scenario: Consumables command fails
- **WHEN** the device does not support the GET_CONSUMABLE command
- **THEN** the method SHALL raise a descriptive exception rather than return partial data

### Requirement: Clean history retrieval
The system SHALL retrieve a list of recent cleaning job records including start time, duration, and area.

#### Scenario: History returned
- **WHEN** `get_clean_history(limit=10)` is called
- **THEN** the response SHALL include up to 10 recent cleaning records with start time, duration in seconds, and area in cm²

#### Scenario: No history available
- **WHEN** `get_clean_history()` is called and no records exist
- **THEN** the method SHALL return an empty list
