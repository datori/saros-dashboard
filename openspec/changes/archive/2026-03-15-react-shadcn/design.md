## Context

The dashboard is a FastAPI app (`dashboard.py`) that currently serves a single `_HTML` Python string containing all CSS, HTML, and JS inline. The app has a well-defined REST API (`/api/*` endpoints) that the frontend fetches. Node.js 22 is available on the host. The cockpit layout (sticky sidebar + right-pane tabs on desktop, bottom nav on mobile) was implemented in a prior change and must be preserved exactly.

## Goals / Non-Goals

**Goals:**
- Modern, polished dark-theme UI via shadcn/ui components
- Type-safe React frontend with proper component separation
- Zero changes to FastAPI backend or API contracts
- Vite-based build: `cd frontend && npm run build` produces `frontend/dist/`
- FastAPI serves `frontend/dist/` as static files — single `vacuum-dashboard` command still works
- `scripts/dev.sh` launches both servers for development
- CLAUDE.md documents the new workflow

**Non-Goals:**
- Server-side rendering — pure client-side React SPA
- React Query / SWR — plain `fetch` + `useEffect` hooks, matching existing pattern
- Replacing modal dialogs with shadcn Dialog (out of scope for now)
- GraphQL or API contract changes
- PWA changes (manifest, icons stay as-is in FastAPI)

## Decisions

### D1 — Vite + React + TypeScript

Vite is the standard choice for React SPAs in 2025: fast HMR, first-class TypeScript support, simple config. CRA is deprecated. Next.js adds SSR complexity not needed here.

**Output:** `frontend/dist/` — `index.html` + hashed JS/CSS assets.

### D2 — shadcn/ui component installation

shadcn/ui is a copy-paste component library (not an npm package). Components are added via `npx shadcn@latest add <component>` and live in `frontend/src/components/ui/`. This means components are owned code — fully customizable, no version drift issues.

**Theme:** Use shadcn's built-in dark mode. Set `class="dark"` on `<html>` element. Tailwind `darkMode: 'class'` config.

**Palette:** shadcn's default neutral/zinc palette works well; keep the existing accent blue (`#4f8ef7`) as the primary color by overriding CSS variables in `globals.css`.

### D3 — FastAPI serves built dist/

`dashboard.py` mounts `frontend/dist/` as `StaticFiles`. The `/` route serves `frontend/dist/index.html`. All `/api/*` routes remain unchanged — registered before the static mount so they take priority.

```python
from fastapi.staticfiles import StaticFiles
app.mount("/", StaticFiles(directory="frontend/dist", html=True), name="frontend")
```

The `_HTML` string and `HTMLResponse` import are removed. PWA manifest/icon routes stay as explicit FastAPI routes (they don't need to live in `dist/`).

**Fallback:** If `frontend/dist/` doesn't exist (dev without build), FastAPI returns 404 for `/`. That's fine — in dev, use the Vite dev server instead.

### D4 — Vite dev proxy

In development, `npm run dev` starts Vite on port 5173. Vite proxies all `/api/*` requests to `http://localhost:8181` (uvicorn). No CORS changes needed.

```ts
// vite.config.ts
server: {
  proxy: {
    '/api': 'http://localhost:8181',
    '/manifest.json': 'http://localhost:8181',
  }
}
```

### D5 — Component structure

Keep components flat and feature-oriented — no deep nesting. One file per panel. Each panel is a self-contained component that fetches its own data.

```
frontend/src/
  App.tsx              # cockpit layout shell, mobile tab routing
  components/
    ui/                # shadcn copies (Button, Badge, Progress, Select, Tabs, RadioGroup, etc.)
    StatusPanel.tsx
    ActionsPanel.tsx
    ConsumablesPanel.tsx
    CleanRoomsPanel.tsx
    RoutinesPanel.tsx
    TriggersPanel.tsx
    WindowPlannerPanel.tsx
    CleanSettingsPanel.tsx
    SchedulePanel.tsx
    HistoryPanel.tsx
    ConnectivityBanner.tsx
    EditModal.tsx
    TriggerModal.tsx
  lib/
    utils.ts           # shadcn cn() helper
  globals.css          # Tailwind base + shadcn CSS variables
```

### D6 — Cockpit layout in React

The desktop/mobile split uses a CSS class approach identical to the current implementation:
- Tailwind `md:flex-row` for desktop cockpit layout
- Mobile bottom nav: fixed `<nav>` with 4 tab buttons, `activeTab` state in `App.tsx`
- Desktop right-pane: shadcn `<Tabs>` component, `activeRightTab` state persisted to `sessionStorage`
- Panel visibility: conditional rendering (`activeTab === 'clean'`) on mobile; all right-pane panels always rendered but tab-gated on desktop

### D7 — Data fetching pattern

Each panel component manages its own data with `useState` + `useEffect`. No global state library. `refreshAll()` replaced by a top-level interval that increments a `refreshKey` counter passed as a prop — each panel re-fetches when `refreshKey` changes.

### D8 — scripts/dev.sh

```bash
#!/bin/bash
trap 'kill $(jobs -p)' EXIT
vacuum-dashboard --port 8181 --no-browser &
cd frontend && npm run dev
```

Runs uvicorn in background, Vite in foreground. Ctrl+C kills both via the trap.

## Risks / Trade-offs

**[Risk] dist/ not committed to git** → `frontend/dist/` should be in `.gitignore`. Anyone cloning the repo must run `npm run build` before `vacuum-dashboard` works. Mitigation: document clearly in CLAUDE.md; consider adding a check in the FastAPI startup that warns if dist/ is missing.

**[Risk] Node.js version drift** → The project now has a Node.js dependency. Mitigation: add `.node-version` or `engines` field in `package.json` to pin Node ≥ 20.

**[Risk] shadcn component API changes** → Since components are copied into the repo, they don't auto-update. This is a feature (stability) not a bug. Mitigation: re-run `npx shadcn add` to refresh when needed.

**[Risk] `frontend/dist/` path relative to CWD** → `StaticFiles(directory="frontend/dist")` resolves relative to CWD at server startup. Must be run from repo root. Mitigation: use `Path(__file__).parent.parent.parent / "frontend" / "dist"` for an absolute path.

## Migration Plan

1. Set up `frontend/` Vite project, install deps, configure shadcn
2. Build React components panel by panel, verifying API integration
3. Update `dashboard.py` to serve `frontend/dist/`
4. Add `scripts/dev.sh`
5. Update `CLAUDE.md`
6. Test full build + serve flow
7. Rollback: `git revert` restores `_HTML` string; remove `frontend/` directory
