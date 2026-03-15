## Context

The vacuum dashboard is currently started manually (`vacuum-dashboard --port 8181`) with no persistence across reboots and no guaranteed port. Two forces now demand a stable address:

1. **Iterative dev workflow** — we rebuild and restart constantly; a Makefile target that does `npm run build && systemctl restart` is the right shape for that loop.
2. **External integrations** — Home Assistant (and other local services) need a stable `http://host:PORT/api/...` URL to fire triggers, poll status, or issue commands. That URL cannot change.

The system uses systemd user units (no root required, starts at login, runs as the developer user) and `WorkingDirectory` set to the project root as a convention, though all config/session/DB paths are `__file__`-relative and will resolve correctly regardless.

## Goals / Non-Goals

**Goals:**
- Single stable port (`9103`) for the service — documented, memorable, doesn't clash with common dev ports
- Service auto-starts on login, restarts on crash
- Unit file is version-controlled (reproducible on any machine)
- `make deploy` is the one command to push iterative changes to the running service
- One-time install is a single script call

**Non-Goals:**
- Separate "dev" vs "prod" service instances — the running service IS the dev version
- HTTPS / TLS termination — LAN-only, localhost trust model
- Multi-user or containerized deployment
- Authentication — out of scope for a local home-network service

## Decisions

### D1: systemd user unit (not root system unit, not `screen`/`tmux`, not Docker)

systemd user units (`systemctl --user`) require no root, start on login, support `Restart=on-failure`, and integrate with `journalctl`. This is the right primitive for a developer-run home service on a Linux machine.

Alternatives considered:
- **System unit** (`/etc/systemd/system/`): requires root for install/management; overkill for a personal tool
- **`screen`/`tmux` session**: not persistent across reboots, no crash recovery
- **Docker**: massive overhead for a simple Python process; complicates hot-iteration

### D2: `make deploy` = build frontend + restart (no separate step)

A single `make deploy` rebuilds `frontend/dist/` and restarts the service. FastAPI serves the new static files on next request. No hot-module-replacement needed for the running service — a ~15s full rebuild is acceptable.

Alternatively: watch-mode rebuild + SIGHUP. Rejected — adds complexity; a clean restart is simpler and sufficient.

### D3: Unit file at `deploy/vacuum-dashboard.service`, symlinked into `~/.config/systemd/user/`

Keeps the unit version-controlled without polluting the project root. The install script does the symlink + `systemctl --user enable + start`. On machines where the repo path changes, re-run `make install`.

### D4: Port `9103`

- Above the 8xxx "dev server" range
- Below high system ports (>49151)
- No well-known service occupies 9103
- Easy to remember as "the vacuum port"

### D5: Vite dev proxy still points to `:8181` (or whatever port is in `vite.config.ts`)

The Vite dev server (`./scripts/dev.sh`) uses a different port (8181) from the production service (9103). This is intentional — when doing frontend hot-reload work, you run `./scripts/dev.sh` and open Vite's port. When using the stable service, you open 9103. No conflict.

Actually — we should update `dev.sh` / `vite.config.ts` to proxy to 9103 and have the backend run on 9103 always, to avoid confusion. Both dev and service use 9103; Vite just proxies `/api/*` to it.

**Revised D5**: Backend always runs on 9103. `dev.sh` starts backend on 9103, Vite proxies to 9103. The systemd service also runs on 9103. Only one can own the port at a time — that's fine since you either run the service OR `dev.sh`, not both.

## Risks / Trade-offs

**[Port conflict between service and dev.sh]** → Since both use 9103, running `dev.sh` while the service is active will fail to bind. Mitigation: `make restart` stops the service before dev work; `dev.sh` could auto-stop it. For now, document the expectation: stop service before running dev.sh.

**[Symlink breaks if repo is moved]** → `~/.config/systemd/user/vacuum-dashboard.service` symlinks to an absolute path. Re-running `make install` fixes it. Low risk for a stable dev machine.

**[Unit doesn't start on headless boot without lingering]** → `loginctl enable-linger` is needed for user services to run before first login. Not needed if the machine is used interactively. Install script should mention this but not require it.

## Migration Plan

1. `make install` — one-time: creates symlink, enables and starts service
2. Service starts on port 9103; old 8181 invocations stop working (update bookmarks)
3. Home Assistant `rest_command` entries use `http://<host>:9103/api/...`
4. Rollback: `systemctl --user disable --now vacuum-dashboard`, remove symlink, run manually
