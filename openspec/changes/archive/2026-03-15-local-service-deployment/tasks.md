## 1. Port update

- [x] 1.1 In `src/vacuum/dashboard.py` line 917: change default port from `8080` → `9103`
- [x] 1.2 In `frontend/vite.config.ts` lines 15-16: change proxy target from `http://localhost:8181` → `http://localhost:9103`
- [x] 1.3 In `scripts/dev.sh`: update comment and `--port 8181` invocation to `9103`

## 2. Systemd unit file

- [x] 2.1 Create `deploy/` directory
- [x] 2.2 Create `deploy/vacuum-dashboard.service` with `[Unit]`, `[Service]` (ExecStart, WorkingDirectory, Restart=on-failure, Environment PATH), and `[Install]` (WantedBy=default.target) sections

## 3. Install script

- [x] 3.1 Create `scripts/install-service.sh` (executable): create `~/.config/systemd/user/` if needed, symlink `deploy/vacuum-dashboard.service` there, run `systemctl --user daemon-reload`, `enable`, `restart`
- [x] 3.2 Make script idempotent: remove old symlink before re-creating if it exists

## 4. Makefile

- [x] 4.1 Create `Makefile` at project root with targets: `deploy`, `restart`, `logs`, `status`, `install`
- [x] 4.2 `deploy` target: `cd frontend && npm run build` then `systemctl --user restart vacuum-dashboard`
- [x] 4.3 Add `.PHONY` declaration for all targets

## 5. Documentation

- [x] 5.1 Update `CLAUDE.md`: change port references from 8181 → 9103; add note about `make deploy` as the standard iteration command and `make install` for first-time setup
