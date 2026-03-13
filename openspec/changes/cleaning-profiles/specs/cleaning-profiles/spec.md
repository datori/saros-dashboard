## ADDED Requirements

### Requirement: Profile data model
The system SHALL store cleaning profiles in a `profiles` table in `vacuum_schedule.db`. Each profile SHALL have an `id` (INTEGER PK), `name` (TEXT, required), `fan_speed` (TEXT or NULL), `mop_mode` (TEXT or NULL), `water_flow` (TEXT or NULL), `route` (TEXT or NULL), `is_default` (INTEGER 0/1), and `sort_order` (INTEGER). NULL setting columns SHALL mean "no override — use device default."

#### Scenario: Table created on startup
- **WHEN** the dashboard starts and `scheduler.init_db()` runs
- **THEN** the `profiles` table SHALL be created if it does not exist, without affecting existing data

#### Scenario: NULL settings preserved
- **WHEN** a profile is saved with some setting fields omitted or set to null
- **THEN** those fields SHALL be stored as NULL and not sent as overrides when the profile is applied

### Requirement: Profile CRUD API
The system SHALL expose REST endpoints for managing profiles.

#### Scenario: List profiles
- **WHEN** `GET /api/profiles` is requested
- **THEN** the response SHALL be a JSON array of all profiles with fields: `id`, `name`, `fan_speed`, `mop_mode`, `water_flow`, `route`, `is_default`

#### Scenario: Create profile
- **WHEN** `POST /api/profiles` is called with `{name, fan_speed?, mop_mode?, water_flow?, route?, is_default?}`
- **THEN** a new profile SHALL be created and the created profile object SHALL be returned

#### Scenario: Update profile
- **WHEN** `PUT /api/profiles/{id}` is called with updated fields
- **THEN** the profile SHALL be updated and the updated object returned; unknown fields SHALL be ignored

#### Scenario: Delete profile
- **WHEN** `DELETE /api/profiles/{id}` is called
- **THEN** the profile SHALL be removed and `{"ok": true}` returned

#### Scenario: Invalid profile id
- **WHEN** `PUT /api/profiles/{id}` or `DELETE /api/profiles/{id}` is called with a non-existent id
- **THEN** the API SHALL return HTTP 404

### Requirement: Single default profile
The system SHALL allow at most one profile to be marked as default at any time.

#### Scenario: Setting a new default clears others
- **WHEN** a profile is saved or updated with `is_default: true`
- **THEN** all other profiles SHALL have `is_default` cleared to 0 in the same operation

#### Scenario: Deleting the default profile
- **WHEN** the profile with `is_default = 1` is deleted
- **THEN** no other profile is automatically promoted; the system falls back to "Device defaults" (no overrides)

### Requirement: Profile chip bar UI
The dashboard SHALL display a profile selector chip bar in both the "Start clean" and "Room clean" panels.

#### Scenario: Device defaults chip always present
- **WHEN** the profile chip bar is rendered
- **THEN** a "Device defaults" chip SHALL appear first and SHALL NOT have an edit button

#### Scenario: Default profile pre-selected on load
- **WHEN** the page loads and a default profile exists
- **THEN** that profile's chip SHALL be selected and its settings SHALL pre-populate the override dropdowns

#### Scenario: No default profile on load
- **WHEN** the page loads and no profile is marked default
- **THEN** "Device defaults" SHALL be pre-selected and all override dropdowns SHALL be empty

#### Scenario: Selecting a profile chip
- **WHEN** a profile chip is clicked
- **THEN** the chip becomes selected and the override dropdowns SHALL be populated with that profile's non-null settings; null settings SHALL leave the dropdown empty (device default)

#### Scenario: Selecting Device defaults chip
- **WHEN** the "Device defaults" chip is clicked
- **THEN** all override dropdowns SHALL be cleared

### Requirement: Profile edit modal
The dashboard SHALL provide a modal dialog for creating and editing profiles, accessible from the chip bar.

#### Scenario: Open create modal
- **WHEN** the "+" chip or button is clicked
- **THEN** a modal SHALL open with empty fields and a save button

#### Scenario: Open edit modal
- **WHEN** the edit icon on a profile chip is clicked
- **THEN** a modal SHALL open pre-filled with that profile's current settings

#### Scenario: Save creates or updates profile
- **WHEN** the user submits the modal form
- **THEN** the profile SHALL be saved via the API, the chip bar SHALL refresh, and the modal SHALL close

#### Scenario: Delete from edit modal
- **WHEN** the user clicks "Delete profile" in the edit modal
- **THEN** the profile SHALL be deleted via the API and the chip bar SHALL refresh

#### Scenario: Set as default from edit modal
- **WHEN** the user clicks "Set as default" in the edit modal
- **THEN** `is_default` SHALL be set to true on save for that profile

#### Scenario: Modal is mobile-friendly
- **WHEN** the modal is displayed on a narrow viewport (mobile)
- **THEN** all inputs and buttons SHALL be comfortably tappable (min 44px touch targets) and the modal SHALL not overflow the viewport

### Requirement: Profile integration with clean flows
When a clean is started, the active profile's settings (already pre-filled into override dropdowns) SHALL flow through the existing start-clean and room-clean request paths without additional changes to the API contract.

#### Scenario: Start clean uses profile settings
- **WHEN** a profile is selected and the user starts a clean without changing the override dropdowns
- **THEN** `POST /api/action/start` SHALL be called with the profile's non-null settings as override fields

#### Scenario: Per-clean override still works
- **WHEN** a profile is selected but the user manually changes an override dropdown before starting
- **THEN** the manually chosen value SHALL be used, not the profile value
