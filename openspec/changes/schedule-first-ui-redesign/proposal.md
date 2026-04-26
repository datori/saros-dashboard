## Why

The current 3-column layout buries the Cleaning Schedule Gantt in a fixed right sidebar while devoting 360px to a sparse left sidebar that holds Status, Actions, and Consumables — panels that collectively show ~12 lines of content. The schedule is the most information-dense and uniquely valuable view, yet it gets the least space. Promoting it to the hero view and condensing status/actions into a persistent top bar makes the dashboard immediately more useful at a glance.

## What Changes

- **Remove** the left sidebar (StatusPanel + ActionsPanel + ConsumablesPanel as a column)
- **Add** a persistent compact status bar (~44px) at the top showing: state badge, battery, dock status, window planner status, and action icon-buttons
- **Promote** SchedulePanel to the main (flex-1) left pane — gets ~60% of desktop width
- **Consolidate** the right pane from 4 tabs to 3 tabs:
  - **Clean** — CleanRoomsPanel + RoutinesPanel
  - **Triggers** — TriggersPanel + WindowPlannerPanel
  - **History** — HistoryPanel + ConsumablesPanel + CleanSettingsPanel
- **Remove** the standalone "Info" tab (contents redistributed)
- **Simplify** mobile nav from 4 tabs to 3 tabs: Schedule | Clean | History
- Schedule becomes the default/home tab on mobile
- Room names in the Gantt no longer need to truncate (wider available width)

## Capabilities

### New Capabilities

_(none — this is a pure layout reorganization)_

### Modified Capabilities

- `cockpit-layout`: Replace 3-column sidebar layout with status-bar + 2-pane layout; right pane collapses from 4 tabs to 3 tabs (Clean, Triggers, History); left sidebar eliminated
- `mobile-tabs`: Replace 4-tab nav (Now, Clean, Plan, Info) with 3-tab nav (Schedule, Clean, History); Schedule becomes default tab

## Impact

- `frontend/src/App.tsx` — full layout overhaul (primary change)
- `frontend/src/components/StatusPanel.tsx` — repurposed into compact `StatusBar` strip (or replaced by new component)
- `frontend/src/components/ActionsPanel.tsx` — merged into `StatusBar`
- `frontend/src/components/SchedulePanel.tsx` — minor: remove truncation constraints, allow wider room name display
- No backend changes; no API changes; no new dependencies
