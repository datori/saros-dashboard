## Why

The dashboard frontend is a single `_HTML` Python string — no component model, no type safety, and hard to style consistently. Shoelace was evaluated but the visual result was unsatisfying. React + shadcn/ui delivers a genuinely polished dark-theme UI with a proper component library, at the cost of adding a build step (Node.js is available).

## What Changes

- Add `frontend/` directory: Vite + React + TypeScript + Tailwind CSS + shadcn/ui
- Replace `_HTML` Python string in `dashboard.py` with FastAPI `StaticFiles` mount serving `frontend/dist/`
- Add `scripts/dev.sh` to run both servers (uvicorn + Vite) in development
- Update `CLAUDE.md` with frontend build/dev workflow
- Vite dev server proxies `/api/*` to FastAPI on port 8181
- All existing FastAPI API endpoints unchanged
- Cockpit layout preserved exactly: sticky sidebar + right-pane tabs (desktop), bottom nav (mobile)

## Capabilities

### New Capabilities
- `react-frontend`: React + shadcn/ui frontend build system, component structure, and FastAPI static file serving

### Modified Capabilities
- `dashboard-ui`: Implementation technology changes from inline HTML string to React/shadcn/ui; layout and behaviour requirements unchanged
- `cockpit-layout`: No requirement changes — layout spec stays valid, implementation moves to React components
- `mobile-tabs`: No requirement changes — mobile tab behaviour stays identical, implementation moves to React

## Impact

- `src/vacuum/dashboard.py`: Remove `_HTML` string; add `StaticFiles` mount for `frontend/dist/`; keep all API endpoints unchanged
- `frontend/`: New directory — Vite project, React components, shadcn/ui, Tailwind config
- `scripts/dev.sh`: New file — launches both uvicorn and Vite dev server
- `CLAUDE.md`: Add frontend build/dev workflow documentation
- `pyproject.toml`: No changes needed (dashboard entry point unchanged)
- No backend, API, or scheduler changes
