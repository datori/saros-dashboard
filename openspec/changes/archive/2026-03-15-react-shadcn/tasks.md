## 1. Vite Project Setup

- [x] 1.1 Scaffold Vite + React + TypeScript project in `frontend/`: `npm create vite@latest frontend -- --template react-ts`
- [x] 1.2 Install Tailwind CSS and configure: `npm install -D tailwindcss @tailwindcss/vite` and add to `vite.config.ts`
- [x] 1.3 Install shadcn/ui peer deps and init: `npx shadcn@latest init` (choose zinc/neutral theme, dark mode class, CSS variables)
- [x] 1.4 Configure `vite.config.ts` dev proxy: `/api` and `/manifest.json` → `http://localhost:8181`
- [x] 1.5 Add `"@": "./src"` path alias to `tsconfig.json` and `vite.config.ts`
- [x] 1.6 Set up `globals.css`: Tailwind base layers + shadcn CSS variable overrides for accent blue (`--primary: 217 91% 65%` to match `#4f8ef7`), dark background (`--background: 216 13% 16%`), surface (`--card: 216 12% 19%`)
- [x] 1.7 Verify `npm run build` succeeds with empty App.tsx

## 2. shadcn Component Installation

- [x] 2.1 Install shadcn components used in the dashboard: `npx shadcn@latest add button badge progress select tabs radio-group`
- [x] 2.2 Install additional shadcn components: `npx shadcn@latest add dialog table checkbox`
- [x] 2.3 Install lucide-react for icons (bundled with shadcn): verify `lucide-react` is in package.json

## 3. App Shell & Layout

- [x] 3.1 Create `App.tsx` with cockpit layout: header, `#cockpit` flex container, `#sidebar` div, `#right-pane` div, mobile `<nav>` tab bar
- [x] 3.2 Implement mobile tab state: `activeTab` useState (`'now'|'clean'|'plan'|'info'`), persist to sessionStorage, restore on load
- [x] 3.3 Implement desktop right-pane tabs using shadcn `<Tabs>`: `activeRightTab` state (`'rooms'|'routines'|'triggers'|'info'`), persist to sessionStorage
- [x] 3.4 Add CSS for cockpit layout in `App.css` or Tailwind classes: desktop ≥900px flex-row, sidebar 320px sticky, right-pane flex-1 max-w-640px; mobile stacked with bottom nav
- [x] 3.5 Add `ConnectivityBanner` component: polls `/api/health`, shows warning banner when device unreachable
- [x] 3.6 Implement `refreshKey` pattern: top-level `refreshKey` counter incremented every 30s (and on manual refresh), passed as prop to all panels to trigger re-fetch

## 4. Sidebar Panels

- [x] 4.1 Create `StatusPanel.tsx`: fetches `/api/status`, renders state/dock/error as `<Badge>`, battery as `<Progress>`, handles stale indicator
- [x] 4.2 Create `ActionsPanel.tsx`: five `<Button>` components (Start/Stop/Pause/Dock/Locate), calls `POST /api/action/{name}`, shows feedback, disables all during request
- [x] 4.3 Create `ConsumablesPanel.tsx`: fetches `/api/consumables`, renders four `<Progress>` bars with reset buttons, color-codes low/medium/high

## 5. Right-Pane Panels — Rooms & Routines

- [x] 5.1 Create `CleanRoomsPanel.tsx`: scope radio group (All/Select), room checkbox list (fetches `/api/rooms`), override selects (Clean Mode, Fan Speed, Mop Mode, Water Flow, Route), Repeat input, Start Clean button
- [x] 5.2 Create `RoutinesPanel.tsx`: fetches `/api/routines`, renders list with Run `<Button>` per routine, shows loading state on button during run
- [x] 5.3 Wire `applyCleanMode` logic in `CleanRoomsPanel`: when Clean Mode changes, auto-set fan speed / water flow selects accordingly

## 6. Right-Pane Panels — Triggers & Planner

- [x] 6.1 Create `TriggersPanel.tsx`: trigger fire buttons grid, window status display, trigger management list (Edit/Del per trigger), Dispatch Settings section with per-mode selects
- [x] 6.2 Create `TriggerModal.tsx`: shadcn `<Dialog>` for Add/Edit trigger (name, budget, mode, notes fields)
- [x] 6.3 Create `WindowPlannerPanel.tsx`: budget range slider, greedy room queue preview, Open Window button; re-renders on slider change

## 7. Right-Pane Panels — Info

- [x] 7.1 Create `CleanSettingsPanel.tsx`: Fan Speed / Mop Mode / Water Flow `<Select>` components populated from `/api/settings`, Save Settings button
- [x] 7.2 Create `SchedulePanel.tsx`: fetches `/api/schedule`, renders table with overdue colour-coding, Edit button per row
- [x] 7.3 Create `EditModal.tsx`: shadcn `<Dialog>` for editing room schedule intervals (vacuum_days, mop_days, priority_weight, duration_min, notes)
- [x] 7.4 Create `HistoryPanel.tsx`: fetches `/api/history`, renders scrollable table with `<Badge>` for complete column

## 8. FastAPI Integration

- [x] 8.1 Update `dashboard.py`: remove `_HTML` string, `HTMLResponse` import, and old index route
- [x] 8.2 Add `StaticFiles` mount using absolute path: `Path(__file__).parent.parent.parent / "frontend" / "dist"`
- [x] 8.3 Add startup warning if `frontend/dist/` does not exist: log to stderr with clear message
- [x] 8.4 Verify all `/api/*` routes are registered before the static mount so they take priority

## 9. Dev Workflow & Documentation

- [x] 9.1 Create `scripts/dev.sh`: launches `vacuum-dashboard --port 8181 --no-browser` in background and `cd frontend && npm run dev` in foreground; trap EXIT to kill background jobs
- [x] 9.2 Make `scripts/dev.sh` executable: `chmod +x scripts/dev.sh`
- [x] 9.3 Add `frontend/dist/` and `frontend/node_modules/` to `.gitignore`
- [x] 9.4 Update `CLAUDE.md` with Frontend section: directory structure, `npm run build` requirement, dev workflow (`bash scripts/dev.sh`), note about dist not in git

## 10. Verification

- [x] 10.1 `npm run build` completes without errors or TypeScript warnings
- [ ] 10.2 `vacuum-dashboard --port 8181` serves the React app at `http://localhost:8181`
- [ ] 10.3 All panels load data correctly from the API in production build
- [ ] 10.4 Desktop cockpit layout: sticky sidebar, right-pane tabs (Rooms/Routines/Triggers/Info) work and persist
- [ ] 10.5 Mobile layout: bottom nav (Now/Clean/Plan/Info) shows correct panels on each tab
- [ ] 10.6 `bash scripts/dev.sh` starts both servers; Ctrl+C kills both cleanly
- [ ] 10.7 No TypeScript errors (`npx tsc --noEmit` passes)
