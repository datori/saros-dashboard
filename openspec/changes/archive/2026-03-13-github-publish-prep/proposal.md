## Why

The saros-dashboard project is ready to be open-sourced, but the repo currently contains personal/machine-specific details in documentation, lacks a LICENSE file, has database files not covered by `.gitignore`, and the project name in `pyproject.toml` is too generic. Resolving these issues before publishing protects privacy and makes the project usable by others.

## What Changes

- Sanitize `CLAUDE.md`: remove LAN IP (`192.168.0.180`), OS/machine details (Proxmox VE, kernel version), foreign process info (`finance-dashboa`, PID), and user's specific room-name table; replace with generic examples
- Rename project from `vacuum` to `saros-dashboard` in `pyproject.toml` (package name, entry points, metadata)
- Add MIT `LICENSE` file to repo root
- Add `vacuum_schedule.db`, `vacuum_schedule.db-shm`, `vacuum_schedule.db-wal` to `.gitignore`
- Add `openspec/` directory to git tracking (currently fully untracked)
- Expand `README.md` for public audience: project overview, architecture diagram, setup steps, cloud-API caveat, contributing section, license badge

## Capabilities

### New Capabilities

- `open-source-readiness`: Repository metadata, licensing, and documentation suitable for public GitHub publication

### Modified Capabilities

(none — no existing specs are affected)

## Impact

- `pyproject.toml`: name, entry-point keys, description, readme, license fields
- `CLAUDE.md`: documentation content (no code changes)
- `README.md`: complete rewrite for public audience
- `.gitignore`: three new entries for SQLite WAL files
- New file: `LICENSE` (MIT)
- Git index: `openspec/` directory added to tracking
