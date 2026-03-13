## ADDED Requirements

### Requirement: History reconciliation loop
The system SHALL reconcile unreconciled clean events against device clean history on every health poll cycle.

#### Scenario: Unreconciled events exist
- **WHEN** the health poll fires and there are `clean_events` with `complete = 0` dispatched within the last 2 hours
- **THEN** the system SHALL fetch device clean history (`get_clean_history(limit=5)`) and attempt to match each unreconciled event

#### Scenario: No unreconciled events
- **WHEN** the health poll fires and there are no `clean_events` with `complete = 0` within the last 2 hours
- **THEN** the system SHALL skip fetching device history (no MQTT call)

### Requirement: Timestamp-based matching
The system SHALL match scheduler events to device history entries by timestamp correlation.

#### Scenario: Match found within window
- **WHEN** a device history entry has `start_time` within ±10 minutes of a scheduler event's `dispatched_at`
- **THEN** the system SHALL consider this a match

#### Scenario: Multiple candidates
- **WHEN** multiple device history entries fall within the ±10 minute window of a scheduler event
- **THEN** the system SHALL select the entry with `start_time` closest to `dispatched_at`

#### Scenario: No match found
- **WHEN** no device history entry falls within the ±10 minute window of an unreconciled event
- **THEN** the event SHALL remain unreconciled (`complete = 0`) and be retried on the next poll

### Requirement: Credit from device history
The system SHALL mark clean events complete based on the device's reported completion status.

#### Scenario: Device reports complete
- **WHEN** a matched device history entry has `complete = True`
- **THEN** the scheduler event SHALL be updated with `complete = 1`, and the device-reported `duration_seconds` and `area_m2` SHALL be copied to the event

#### Scenario: Device reports incomplete
- **WHEN** a matched device history entry has `complete = False`
- **THEN** the scheduler event SHALL be updated with the device-reported `duration_seconds` and `area_m2` but `complete` SHALL remain `0` (no room credit)

### Requirement: Staleness cutoff
The system SHALL stop attempting to reconcile events older than 2 hours.

#### Scenario: Event older than 2 hours
- **WHEN** an unreconciled event has `dispatched_at` more than 2 hours ago
- **THEN** the system SHALL skip it during reconciliation (it remains `complete = 0` and can be manually fixed)

#### Scenario: Event within 2 hours
- **WHEN** an unreconciled event has `dispatched_at` within the last 2 hours
- **THEN** the system SHALL include it in reconciliation attempts

### Requirement: Query unreconciled events
The scheduler SHALL provide a query to retrieve unreconciled events for the reconciler.

#### Scenario: Unreconciled events query
- **WHEN** the reconciler requests unreconciled events
- **THEN** the scheduler SHALL return all `clean_events` with `complete = 0` and `dispatched_at` within the last 2 hours, including their associated `segment_ids` from `clean_event_rooms`
