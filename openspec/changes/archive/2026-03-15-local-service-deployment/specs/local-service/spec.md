## ADDED Requirements

### Requirement: Systemd user unit
The project SHALL include a systemd user unit file at `deploy/vacuum-dashboard.service` that runs `vacuum-dashboard --port 9103` as the authenticated user, restarts on failure, and sets `WorkingDirectory` to the project root.

#### Scenario: Unit file present
- **WHEN** the repository is cloned
- **THEN** `deploy/vacuum-dashboard.service` SHALL exist and be valid systemd unit syntax

#### Scenario: Service restarts on crash
- **WHEN** the `vacuum-dashboard` process exits unexpectedly
- **THEN** systemd SHALL restart it automatically (Restart=on-failure)

#### Scenario: Service starts at login
- **WHEN** the user logs in (or linger is enabled)
- **THEN** systemd SHALL start `vacuum-dashboard.service` automatically if it is enabled

### Requirement: Install script
The project SHALL include `scripts/install-service.sh` that performs one-time service setup with no manual steps required beyond running the script.

#### Scenario: Script creates symlink
- **WHEN** `scripts/install-service.sh` is executed
- **THEN** `~/.config/systemd/user/vacuum-dashboard.service` SHALL be a symlink pointing to `deploy/vacuum-dashboard.service` in the project root

#### Scenario: Script enables and starts service
- **WHEN** `scripts/install-service.sh` completes
- **THEN** the service SHALL be enabled (survives reboot) and running

#### Scenario: Script is idempotent
- **WHEN** `scripts/install-service.sh` is run a second time
- **THEN** it SHALL succeed without error (re-links and restarts)

### Requirement: Makefile targets
The project SHALL include a `Makefile` at the project root with targets for all common service operations.

#### Scenario: make deploy
- **WHEN** `make deploy` is run
- **THEN** the React frontend SHALL be rebuilt (`npm run build` in `frontend/`) and the service restarted, making the new build live

#### Scenario: make restart
- **WHEN** `make restart` is run
- **THEN** `systemctl --user restart vacuum-dashboard` SHALL be executed

#### Scenario: make logs
- **WHEN** `make logs` is run
- **THEN** `journalctl --user -u vacuum-dashboard -f` SHALL be executed (follow mode)

#### Scenario: make status
- **WHEN** `make status` is run
- **THEN** `systemctl --user status vacuum-dashboard` SHALL be executed

#### Scenario: make install
- **WHEN** `make install` is run
- **THEN** `scripts/install-service.sh` SHALL be executed
