## 1. StatusBar Component

- [x] 1.1 Create `frontend/src/components/StatusBar.tsx` — horizontal strip (~44px) with: state badge, battery progress bar + %, dock status badge, window planner indicator, and 5 icon-only action buttons (Start, Stop, Pause, Dock, Locate)
- [x] 1.2 Wire `StatusBar` to the same `/api/status` data and action callbacks used by the current `StatusPanel` and `ActionsPanel`
- [x] 1.3 Add stale indicator to `StatusBar`: apply `opacity-60` and show `⏱` when status data is stale
- [x] 1.4 Show error code in `StatusBar` when `error_code !== 0`

## 2. App.tsx Layout Overhaul (Desktop)

- [x] 2.1 Remove the left sidebar column (the `<aside>` or left-column div containing `StatusPanel`, `ActionsPanel`, `ConsumablesPanel`) from the desktop layout
- [x] 2.2 Add `StatusBar` as a persistent strip above the main content area (renders on all viewport widths)
- [x] 2.3 Change the main content area to a two-pane flex row: `SchedulePanel` (flex-1, min-w-0) on the left, right pane (w-[380px] flex-shrink-0) on the right
- [x] 2.4 Make right pane sticky (overflow-y-auto, height constrained to viewport) so it stays in view while schedule scrolls

## 3. Right Pane Tab Consolidation (Desktop)

- [x] 3.1 Replace the 4-tab bar (Rooms / Routines / Triggers / Info) with a 3-tab bar: **Clean** | **Triggers** | **History**
- [x] 3.2 Clean tab content: render `CleanRoomsPanel` followed by `RoutinesPanel`
- [x] 3.3 Triggers tab content: render `TriggersPanel` followed by `WindowPlannerPanel` (unchanged from current Triggers tab)
- [x] 3.4 History tab content: render `HistoryPanel`, then `ConsumablesPanel`, then `CleanSettingsPanel`
- [x] 3.5 Update `sessionStorage` key `activeRightTab` valid values to `"clean" | "triggers" | "history"`; invalid stored values fall back to `"clean"`

## 4. Mobile Tab Overhaul

- [x] 4.1 Replace the 4-tab bottom nav (Now / Clean / Plan / Info) with a 3-tab nav: **Schedule** | **Clean** | **History**
- [x] 4.2 Schedule tab: show only `SchedulePanel` (full width)
- [x] 4.3 Clean tab: show `CleanRoomsPanel`, `RoutinesPanel`, `TriggersPanel`, `WindowPlannerPanel` stacked
- [x] 4.4 History tab: show `HistoryPanel`, `ConsumablesPanel`, `CleanSettingsPanel` stacked
- [x] 4.5 Update `sessionStorage` key `activeTab` valid values to `"schedule" | "clean" | "history"`; invalid stored values (e.g. old `"now"` or `"plan"`) fall back to `"schedule"`
- [x] 4.6 Default tab on first load (no stored preference) is **Schedule**
- [x] 4.7 Update bottom nav icons to match new tabs (e.g. calendar icon for Schedule, sparkles for Clean, bar-chart for History)

## 5. SchedulePanel — Remove Truncation

- [x] 5.1 In `SchedulePanel.tsx`, remove the room name truncation constraint (e.g. remove `max-w-[10ch]`, `truncate`, or `overflow-hidden` from the room name element) so full room names display with the wider available width

## 6. Cleanup & Verification

- [x] 6.1 Confirm `StatusPanel.tsx` and `ActionsPanel.tsx` are no longer imported or rendered anywhere; remove their imports from `App.tsx`
- [x] 6.2 Run `npm run build` in `frontend/` and confirm zero TypeScript errors
- [x] 6.3 Smoke test desktop: status bar visible, schedule fills main pane, right pane tabs (Clean / Triggers / History) all render correctly
- [x] 6.4 Smoke test mobile: status bar visible, 3-tab bottom nav, Schedule tab is default, all panels appear in correct tabs
- [x] 6.5 Verify `sessionStorage` tab persistence works on both desktop and mobile after reload
- [x] 6.6 Run `make deploy` to rebuild frontend and restart the systemd service
