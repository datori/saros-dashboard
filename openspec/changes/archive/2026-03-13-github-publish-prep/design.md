## Context

The repo is a functional personal project ready to be shared publicly. All application code is clean (no credentials, no hardcoded personal data). The publication blockers are confined to documentation files, project metadata, and `.gitignore` coverage. No application code changes are needed.

Current state:
- `CLAUDE.md` checked in with personal machine details (LAN IP, OS info, foreign process names, user's specific room layout)
- `pyproject.toml` uses name `vacuum` with no description, readme, or license metadata
- No `LICENSE` file exists
- `vacuum_schedule.db*` files present on disk but not listed in `.gitignore`
- `openspec/` directory entirely untracked
- `README.md` is minimal (79 lines, install/usage focused), unsuitable as a public project introduction

## Goals / Non-Goals

**Goals:**
- Remove all personal/machine-specific information from tracked files
- Add standard open-source scaffolding (LICENSE, complete README, package metadata)
- Ensure the `.gitignore` covers all generated runtime files
- Bring `openspec/` design history into git tracking

**Non-Goals:**
- Application code changes of any kind
- Moving or restructuring `CLAUDE.md` (sanitize in place; it's valuable as contributor docs)
- Publishing to PyPI
- Adding CI/CD pipelines

## Decisions

**D1: Sanitize CLAUDE.md in place, not relocate it**
CLAUDE.md serves as rich contributor documentation (architecture, API reference, gotchas). Moving it to `.claude/` would hide it from GitHub's rendered view and remove the auto-loading behavior for contributors using Claude Code. Better to strip personal details and keep the file public.

Removed: LAN IP, Proxmox/kernel info, `finance-dashboa` process name, PID, user-specific room name table.
Replaced with: generic dev environment guidance, example room names (Room A / Room B / etc).

**D2: MIT License**
Permissive license appropriate for a personal utility intended for broad reuse. No copyleft requirements or patent clauses needed.

**D3: Keep openspec/ in the repo**
The `openspec/changes/` directory shows the project's design history. It's safe (no personal data after sanitizing the two leaking docs), interesting to contributors, and demonstrates the development methodology. Add all current content to tracking.

Two files in existing openspec docs need sanitization before adding:
- `openspec/changes/archive/2026-03-05-roborock-vacuum-automation/proposal.md`: contains `/home/openclaw/code/vacuum/`
- `openspec/changes/archive/2026-03-08-pwa-home-screen/design.md`: contains `192.168.0.180`

**D4: README complete rewrite**
The current README is install-focused. Public audiences need: what it is, why it exists, architecture overview, credentials setup, cloud-only API caveat (critical — affects reliability expectations), dashboard screenshot note, and contributing guidance.

**D5: pyproject.toml name → `saros-dashboard`**
`vacuum` is too generic and will collide with other packages. `saros-dashboard` is specific to the device (Roborock Saros 10R) and the primary interface (web dashboard + CLI + MCP).

Entry-point `vacuum` CLI command stays as `vacuum` (user-facing, already familiar). Only the package name changes.

## Risks / Trade-offs

**Existing CLAUDE.md content may become stale over time** → Mitigation: Document in README that CLAUDE.md is the authoritative developer reference; update it as part of normal development.

**openspec archive docs contain absolute paths** → Mitigation: Sanitize the two known instances as part of this change before committing.

**pyproject.toml rename breaks `pip install vacuum`** → Acceptable: this was never published to PyPI. Local installs use `pip install -e .` which is unaffected by the package name.
