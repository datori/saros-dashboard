## ADDED Requirements

### Requirement: Room priority weight
The system SHALL store a configurable priority weight for each room.

#### Scenario: Default weight
- **WHEN** a room is created via `sync_rooms()` and no weight has been set
- **THEN** its `priority_weight` SHALL default to 1.0

#### Scenario: Set weight
- **WHEN** `set_room_priority(segment_id, weight=1.5)` is called
- **THEN** the room's `priority_weight` SHALL be updated to 1.5 in the database

#### Scenario: Weight in schedule query
- **WHEN** `get_schedule()` is called
- **THEN** each room's `priority_weight` SHALL be included in the result

### Requirement: Clean type weight
The system SHALL assign fixed weights to clean types for scoring purposes.

#### Scenario: Vacuum weight
- **WHEN** scoring a room for vacuum cleaning
- **THEN** the type weight SHALL be 1.5

#### Scenario: Mop weight
- **WHEN** scoring a room for mopping
- **THEN** the type weight SHALL be 1.0

### Requirement: Composite priority score
The system SHALL compute a composite score for each overdue room as `room_weight × type_weight × overdue_ratio`.

#### Scenario: Standard scoring
- **WHEN** Living Room (weight=1.5) is 1.2× overdue for vacuum (type_weight=1.5)
- **THEN** its score SHALL be `1.5 × 1.5 × 1.2 = 2.7`

#### Scenario: Low priority room very overdue
- **WHEN** Closet (weight=0.5) is 3.0× overdue for mop (type_weight=1.0)
- **THEN** its score SHALL be `0.5 × 1.0 × 3.0 = 1.5`

#### Scenario: Never-cleaned room
- **WHEN** a room has overdue_ratio = infinity
- **THEN** its score SHALL be treated as infinity (highest priority regardless of weights)

#### Scenario: Room not overdue
- **WHEN** a room has overdue_ratio < 1.0 or no interval configured
- **THEN** it SHALL NOT be included in priority scoring

### Requirement: Cross-mode priority ranking
The system SHALL rank rooms across both vacuum and mop modes in a single priority queue.

#### Scenario: Mixed mode selection
- **WHEN** Kitchen is 2.0× overdue for vacuum and Bathroom is 3.0× overdue for mop
- **THEN** both SHALL appear in the priority queue, scored independently, and the higher-scoring entry SHALL be dispatched first

#### Scenario: Same room overdue for both modes
- **WHEN** a room is overdue for both vacuum and mop
- **THEN** it SHALL appear twice in the priority queue (once per mode) with independent scores

#### Scenario: Batch mode grouping
- **WHEN** the dispatch selects multiple rooms, all selected rooms for the same mode SHALL be batched together
- **THEN** if both vacuum and mop rooms are selected, the higher-priority mode batch SHALL be dispatched first
