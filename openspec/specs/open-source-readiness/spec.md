### Requirement: Repository has a LICENSE file
The repository SHALL include an MIT `LICENSE` file at the root with the standard MIT license text and the copyright holder's name.

#### Scenario: LICENSE file exists
- **WHEN** a user visits the repository root on GitHub
- **THEN** a `LICENSE` file is present and GitHub identifies it as MIT

### Requirement: pyproject.toml has complete publish metadata
The `pyproject.toml` SHALL include `name = "saros-dashboard"`, `description`, `readme = "README.md"`, and `license = {text = "MIT"}` fields. The package name SHALL be `saros-dashboard`.

#### Scenario: Package name is specific
- **WHEN** `pyproject.toml` is read
- **THEN** `name` is `saros-dashboard` (not the generic `vacuum`)

#### Scenario: Metadata fields present
- **WHEN** `pyproject.toml` is read
- **THEN** `description`, `readme`, and `license` fields are all present and non-empty

### Requirement: CLAUDE.md contains no personal or machine-specific data
`CLAUDE.md` SHALL NOT contain: private LAN IP addresses, OS/kernel version strings specific to a personal machine, names of unrelated processes running on the developer's host, or the developer's actual room layout as a static table.

#### Scenario: No LAN IP in CLAUDE.md
- **WHEN** `CLAUDE.md` is searched for IP address patterns matching `192.168.x.x`
- **THEN** no matches are found

#### Scenario: No personal OS details in CLAUDE.md
- **WHEN** `CLAUDE.md` is read
- **THEN** references to "Proxmox VE", kernel version strings, or foreign process names (`finance-dashboa`) are absent

#### Scenario: Room table is generic
- **WHEN** the "Known room segment IDs" table in `CLAUDE.md` is read
- **THEN** the room names are illustrative examples, not the developer's actual home layout

### Requirement: .gitignore covers SQLite runtime files
The `.gitignore` SHALL include patterns for `vacuum_schedule.db`, `vacuum_schedule.db-shm`, and `vacuum_schedule.db-wal` so these files are never accidentally committed.

#### Scenario: DB files are ignored
- **WHEN** `vacuum_schedule.db` exists in the working directory
- **THEN** `git status` does not list it as an untracked file

### Requirement: openspec/ directory is tracked in git
All files under `openspec/` SHALL be tracked in the git repository so that the project's design history is published alongside the code.

#### Scenario: openspec changes are committed
- **WHEN** `git ls-files openspec/` is run
- **THEN** the output lists files from both `openspec/changes/` and `openspec/specs/`

### Requirement: openspec archive docs contain no personal data
All files under `openspec/` SHALL NOT contain absolute filesystem paths specific to the developer's machine or private LAN IP addresses.

#### Scenario: No personal paths in openspec
- **WHEN** openspec files are searched for `/home/openclaw`
- **THEN** no matches are found

#### Scenario: No personal IPs in openspec
- **WHEN** openspec files are searched for `192.168.0.180`
- **THEN** no matches are found

### Requirement: README.md is suitable for public GitHub audience
The `README.md` SHALL include: a one-paragraph project description, a feature list, a system requirements / dependencies section, step-by-step setup instructions (credentials, env file, login), a note that the API is cloud-only (no local LAN control), usage examples for CLI and dashboard, and a license badge/section.

#### Scenario: README communicates cloud-only constraint
- **WHEN** a user reads the README
- **THEN** there is a clearly visible note that all commands route through Roborock's cloud, not the local network

#### Scenario: README covers setup end-to-end
- **WHEN** a new user follows the README
- **THEN** they can install, configure credentials, and start the dashboard without consulting other files
