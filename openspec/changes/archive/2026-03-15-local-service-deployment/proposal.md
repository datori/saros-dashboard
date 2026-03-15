## Why

The vacuum dashboard runs ad-hoc today — started manually, on whatever port is free, with no guarantee it survives a reboot. Formalizing it as a systemd user service gives it a stable, known address (`localhost:9103`) so both human users and external integrations (e.g. Home Assistant automations firing triggers via HTTP) can rely on it always being there.

## What Changes

- Default port changes from `8181` → `9103` (distinct from common dev-server range)
- `vacuum-dashboard` runs as a **systemd user service** (`vacuum-dashboard.service`), auto-starting on login and surviving restarts
- Unit file version-controlled at `deploy/vacuum-dashboard.service`
- `scripts/install-service.sh` handles one-time setup (symlink unit, enable, start)
- `Makefile` provides everyday operations: `make deploy`, `make restart`, `make logs`, `make status`, `make install`
- `deploy` target rebuilds the React frontend and restarts the service — the single command for pushing iterative changes to the running instance
- CLAUDE.md updated to reflect port 9103 as the canonical service port

## Capabilities

### New Capabilities

- `local-service`: systemd user unit, install script, and Makefile targets for running the dashboard as a stable local service

### Modified Capabilities

- `web-dashboard`: default port changes from 8181 → 9103

## Impact

- `src/vacuum/dashboard.py` — default port constant updated
- `pyproject.toml` — if port default is baked in there
- `deploy/vacuum-dashboard.service` — new file
- `scripts/install-service.sh` — new file
- `Makefile` — new file
- `CLAUDE.md` — port reference updated
- `frontend/vite.config.ts` — proxy target may need updating if it hardcodes 8181
