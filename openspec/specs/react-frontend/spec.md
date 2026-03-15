## ADDED Requirements

### Requirement: Frontend built with Vite + React + shadcn/ui
The dashboard frontend SHALL be implemented as a React SPA in a `frontend/` directory at the project root, using Vite as the build tool, TypeScript, Tailwind CSS, and shadcn/ui components. Running `cd frontend && npm run build` SHALL produce `frontend/dist/` containing `index.html` and hashed JS/CSS assets.

#### Scenario: Build succeeds from clean state
- **WHEN** a developer runs `cd frontend && npm run build` on a clean checkout
- **THEN** `frontend/dist/index.html` and associated assets are produced with no errors

#### Scenario: Built dist is served by vacuum-dashboard
- **WHEN** `npm run build` has been run and `vacuum-dashboard` is started
- **THEN** `GET /` returns the React app's `index.html` with HTTP 200

### Requirement: Vite dev proxy for API
In development (`npm run dev`), the Vite dev server SHALL proxy all `/api/*` requests to `http://localhost:8181` so the React dev server can call FastAPI without CORS configuration.

#### Scenario: API call from Vite dev server
- **WHEN** the Vite dev server is running on port 5173 and uvicorn is running on port 8181
- **THEN** a fetch to `/api/status` from the browser on port 5173 succeeds and returns vacuum status data

### Requirement: FastAPI serves frontend/dist as static files
`dashboard.py` SHALL mount `frontend/dist/` using FastAPI `StaticFiles` with `html=True`, so that all routes not matched by `/api/*` serve the React SPA. The mount SHALL use an absolute path derived from `__file__` to be CWD-independent.

#### Scenario: SPA catch-all routing
- **WHEN** the user navigates to any non-API path (e.g. `/`, `/rooms`)
- **THEN** FastAPI returns `frontend/dist/index.html`

#### Scenario: Missing dist directory warning
- **WHEN** `vacuum-dashboard` is started but `frontend/dist/` does not exist
- **THEN** the server starts and logs a clear warning that the frontend has not been built

### Requirement: Dev script launches both servers
`scripts/dev.sh` SHALL launch both `vacuum-dashboard --port 8181 --no-browser` and `cd frontend && npm run dev` in a single terminal session. Pressing Ctrl+C SHALL terminate both processes.

#### Scenario: Dev script starts both servers
- **WHEN** a developer runs `bash scripts/dev.sh`
- **THEN** uvicorn starts on port 8181 and Vite dev server starts on port 5173

#### Scenario: Dev script cleans up on exit
- **WHEN** the developer presses Ctrl+C in the terminal running dev.sh
- **THEN** both the uvicorn process and the Vite dev process are terminated

### Requirement: CLAUDE.md documents build and dev workflow
`CLAUDE.md` SHALL include a "Frontend" section documenting: the `frontend/` directory structure, the `npm run build` step required before using `vacuum-dashboard`, the dev workflow using `scripts/dev.sh`, and a note that `frontend/dist/` is not committed to git.

#### Scenario: Agent follows build instructions
- **WHEN** an AI agent reads CLAUDE.md before modifying frontend code
- **THEN** the agent knows to run `npm run build` after making frontend changes and before testing with `vacuum-dashboard`
