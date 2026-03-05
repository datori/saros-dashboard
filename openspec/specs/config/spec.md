## ADDED Requirements

### Requirement: Credentials loaded from environment
The system SHALL read `ROBOROCK_USERNAME` and `ROBOROCK_PASSWORD` from environment variables, with fallback to a `.env` file in the project root.

#### Scenario: Env vars present
- **WHEN** `ROBOROCK_USERNAME` and `ROBOROCK_PASSWORD` are set in the environment
- **THEN** the config module SHALL return them without reading any file

#### Scenario: .env file fallback
- **WHEN** env vars are absent but a `.env` file exists with the credentials
- **THEN** the config module SHALL load and return them from the file

#### Scenario: No credentials found
- **WHEN** neither env vars nor `.env` file contain credentials
- **THEN** the config module SHALL raise a `ConfigError` with instructions for setting credentials

### Requirement: .env.example provided
The project SHALL include a `.env.example` file documenting required and optional environment variables.

#### Scenario: Example file present
- **WHEN** a developer clones the repo
- **THEN** `.env.example` SHALL exist with commented-out `ROBOROCK_USERNAME` and `ROBOROCK_PASSWORD` entries

### Requirement: Optional device selection
The system SHALL support an optional `ROBOROCK_DEVICE_NAME` environment variable to select a specific device when multiple are on the account; defaulting to the first discovered device.

#### Scenario: Default device selection
- **WHEN** `ROBOROCK_DEVICE_NAME` is not set
- **THEN** the client SHALL use the first device returned by device discovery

#### Scenario: Named device selection
- **WHEN** `ROBOROCK_DEVICE_NAME` is set to a valid device name
- **THEN** the client SHALL use that specific device

### Requirement: IOT base URL cached in session file
The system SHALL cache the resolved Roborock IOT base URL as `_base_url` inside `.roborock_session.json` after the first successful authentication, and pass it to subsequent API client instantiations to eliminate the `_get_iot_login_info()` network round-trip.

#### Scenario: Base URL cached on first run
- **WHEN** authentication succeeds and no `_base_url` is present in the session file
- **THEN** the client SHALL resolve the IOT base URL and write it back to the session file

#### Scenario: Cached base URL used on subsequent runs
- **WHEN** `.roborock_session.json` contains a `_base_url` entry
- **THEN** the client SHALL pass it directly to `RoborockApiClient` and `UserParams`, skipping the `_get_iot_login_info()` API call

#### Scenario: Cache invalidation
- **WHEN** `.roborock_session.json` is deleted and `vacuum login` is re-run
- **THEN** the base URL SHALL be re-discovered and re-cached automatically
