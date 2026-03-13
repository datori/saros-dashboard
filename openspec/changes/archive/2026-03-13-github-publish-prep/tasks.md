## 1. Gitignore and database files

- [x] 1.1 Add `vacuum_schedule.db`, `vacuum_schedule.db-shm`, and `vacuum_schedule.db-wal` to `.gitignore`

## 2. License

- [x] 2.1 Create `LICENSE` file at repo root with standard MIT license text

## 3. Sanitize CLAUDE.md

- [x] 3.1 Remove LAN IP address (`192.168.0.180`) from CLAUDE.md — replace with a generic note like "use the UDP connect trick to discover your LAN IP"
- [x] 3.2 Remove OS/machine-specific details: "Proxmox VE host, kernel 6.8.12" — replace with "Linux"
- [x] 3.3 Remove foreign process info: "`finance-dashboa`, pid ~866531" — replace with generic "another process"
- [x] 3.4 Replace the specific room segment ID table (Bedroom/Closet/Bathroom/Kitchen/Living room/Study/Hall) with a generic example table showing placeholder room names and the note that real IDs are visible in the Roborock app

## 4. Sanitize openspec archive docs

- [x] 4.1 Remove `/home/openclaw/code/vacuum/` path from `openspec/changes/archive/2026-03-05-roborock-vacuum-automation/proposal.md`
- [x] 4.2 Remove `192.168.0.180` IP from `openspec/changes/archive/2026-03-08-pwa-home-screen/design.md`

## 5. pyproject.toml metadata

- [x] 5.1 Change `name = "vacuum"` to `name = "saros-dashboard"`
- [x] 5.2 Add `description = "CLI, MCP server, and web dashboard for the Roborock Saros 10R robot vacuum"`
- [x] 5.3 Add `readme = "README.md"`
- [x] 5.4 Add `license = {text = "MIT"}`

## 6. README rewrite

- [x] 6.1 Write a project overview paragraph (what it is, what device it supports, what interfaces it provides)
- [x] 6.2 Add a feature list (CLI, MCP server, web dashboard, scheduling, history, consumables)
- [x] 6.3 Add a requirements/dependencies section (Python >=3.11, Roborock account, Saros 10R)
- [x] 6.4 Add step-by-step setup: clone, `pip install -e .`, create `.env` from `.env.example`, `vacuum login`
- [x] 6.5 Add prominent cloud-only API caveat (all commands route through Roborock cloud MQTT, not local LAN)
- [x] 6.6 Add usage examples for CLI (`vacuum status`, `vacuum clean`, etc.) and dashboard (`vacuum-dashboard --port 8181`)
- [x] 6.7 Add MCP server setup instructions (Claude Desktop config snippet)
- [x] 6.8 Add Contributing section and MIT license section/badge

## 7. Add openspec/ to git tracking

- [x] 7.1 `git add openspec/` to stage all untracked openspec files (changes/, specs/, archives/)
