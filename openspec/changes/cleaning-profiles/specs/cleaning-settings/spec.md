## MODIFIED Requirements

### Requirement: Dashboard override dropdowns initialised from active profile
The dashboard's start-clean and room-clean override dropdowns SHALL be initialised on page load from the active (default) profile's settings, rather than being blank. This replaces the previous behavior of always starting blank.

#### Scenario: Default profile pre-populates start-clean overrides
- **WHEN** the page loads and a default cleaning profile exists
- **THEN** the start-clean fan_speed and water_flow dropdowns SHALL be set to the profile's values (if non-null)

#### Scenario: Default profile pre-populates room-clean overrides
- **WHEN** the page loads and a default cleaning profile exists
- **THEN** the room-clean fan_speed, mop_mode, water_flow, and route dropdowns SHALL be set to the profile's values (if non-null)

#### Scenario: No default profile — dropdowns remain blank
- **WHEN** the page loads and no profile is marked as default
- **THEN** all override dropdowns SHALL remain empty, preserving the original behavior
