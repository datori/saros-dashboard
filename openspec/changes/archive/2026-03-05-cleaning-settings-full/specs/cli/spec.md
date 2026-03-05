## MODIFIED Requirements

### Requirement: Clean subcommand
The CLI SHALL provide a `vacuum clean` subcommand to start a full home clean, with optional flags for fan speed, mop mode, water flow, and route.

#### Scenario: Full clean with defaults
- **WHEN** user runs `vacuum clean`
- **THEN** the vacuum SHALL start cleaning with current device settings and the CLI SHALL confirm with a success message

#### Scenario: Full clean with fan speed
- **WHEN** user runs `vacuum clean --fan-speed turbo`
- **THEN** `start_clean(fan_speed=FanSpeed.TURBO)` SHALL be called

#### Scenario: Full clean with multiple settings
- **WHEN** user runs `vacuum clean --fan-speed max --mop-mode deep --water-flow high`
- **THEN** `start_clean()` SHALL be called with all three settings

#### Scenario: Invalid flag value
- **WHEN** user runs `vacuum clean --fan-speed invalid`
- **THEN** the CLI SHALL print an error listing valid values and exit with code 1

### Requirement: Room clean subcommand
The CLI SHALL provide `vacuum rooms <room_name>...` accepting one or more room names, an optional `--repeat` flag, and optional `--fan-speed`, `--mop-mode`, `--water-flow`, `--route` flags.

#### Scenario: Single room clean
- **WHEN** user runs `vacuum rooms Kitchen`
- **THEN** the vacuum SHALL clean only the Kitchen segment with current device settings

#### Scenario: Multi-room with repeat
- **WHEN** user runs `vacuum rooms Kitchen Office --repeat 2`
- **THEN** the vacuum SHALL clean both rooms twice each

#### Scenario: Room clean with settings
- **WHEN** user runs `vacuum rooms Kitchen --fan-speed quiet --mop-mode fast`
- **THEN** `clean_rooms()` SHALL be called with `fan_speed=FanSpeed.QUIET` and `mop_mode=MopMode.FAST`

## ADDED Requirements

### Requirement: Settings subcommand
The CLI SHALL provide a `vacuum settings` subcommand to view and update device cleaning parameter defaults.

#### Scenario: View settings
- **WHEN** user runs `vacuum settings`
- **THEN** the CLI SHALL print current fan speed, mop mode, water flow, and route in a human-readable table

#### Scenario: Set a single setting
- **WHEN** user runs `vacuum settings --fan-speed turbo`
- **THEN** `set_fan_speed(FanSpeed.TURBO)` SHALL be called and the CLI SHALL confirm success

#### Scenario: Set multiple settings at once
- **WHEN** user runs `vacuum settings --fan-speed max --mop-mode deep --water-flow high`
- **THEN** all three setters SHALL be called and success confirmed

#### Scenario: Invalid value
- **WHEN** user runs `vacuum settings --fan-speed bogus`
- **THEN** the CLI SHALL print an error listing valid values and exit with code 1
