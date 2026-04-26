## Context

The dashboard currently uses a 3-column layout: a 360px left sidebar (Status + Actions + Consumables), a flex-1 center pane (tabbed: Rooms / Routines / Triggers / Info), and a 360px right sidebar (Schedule, always visible on lg+). The left sidebar holds ~12 lines of content in 360px of real estate — a poor use of space. The Schedule Gantt, the most information-rich view, is locked into a narrow right sidebar. This design promotes Schedule to the primary view.

All changes are frontend-only (`App.tsx` + `StatusPanel.tsx` + `ActionsPanel.tsx`). No API changes. No new dependencies.

## Goals / Non-Goals

**Goals:**
- Eliminate the left sidebar; replace with a ~44px persistent status bar
- Give SchedulePanel the majority of horizontal desktop space (flex-1)
- Right pane: fixed ~380px, 3 tabs (Clean, Triggers, History)
- Mobile: 3-tab bottom nav (Schedule, Clean, History) with Schedule as default
- Preserve all existing functionality; no features removed

**Non-Goals:**
- Redesigning individual panel internals (other than removing truncation from SchedulePanel)
- Any backend or API changes
- Accessibility audit or performance optimization
- New features (triggers, window planner, etc. are untouched internally)

## Decisions

### 1. New `StatusBar` component vs. repurposing `StatusPanel`

**Decision**: Create a new `StatusBar.tsx` component; keep `StatusPanel.tsx` intact but unused by App.

**Rationale**: StatusPanel renders a full card with vertical layout. StatusBar needs a horizontal strip — different DOM structure, different styling, different props surface. Trying to make StatusPanel render both modes via a prop would add complexity for marginal reuse. A clean new component keeps both readable. StatusPanel can be deleted in a follow-up once confirmed unused.

**Alternative considered**: `isCompact` prop on StatusPanel. Rejected: too much conditional branching inside a single component.

### 2. Status bar content

**Decision**: Status bar shows state badge | battery (bar + %) | dock status | window indicator | 5 action icon-buttons (▶ ■ ⏸ ⏏ ☎). Stale indicator via opacity on the whole bar.

**Rationale**: Actions must remain always-accessible (currently in left sidebar). Collapsing them into the status bar as icon-only buttons keeps them prominent without dedicating a panel. Error code shown only when non-zero to avoid clutter.

### 3. Desktop layout structure

**Decision**: Two-pane layout under the status bar: `SchedulePanel` (flex-1, min-w-0) + right pane (w-[380px] flex-shrink-0, tabbed).

**Rationale**: flex-1 on Schedule lets it expand into all available space regardless of viewport width — naturally adaptive. Fixed 380px right pane is slightly wider than the current center pane to accommodate CleanRooms comfortably.

### 4. Right pane tab consolidation: 4 → 3

**Decision**: **Clean** (CleanRooms + Routines) | **Triggers** (Triggers + WindowPlanner) | **History** (History + Consumables + CleanSettings).

**Rationale**: Routines are a "start a clean" action, so they logically group with CleanRooms. Consumables and CleanSettings are maintenance/reference info, grouping naturally with History. Triggers and WindowPlanner already shared a tab.

**Alternative considered**: Keeping Routines as its own tab. Rejected: 4 tabs in a 380px pane is cramped.

### 5. Mobile tab reduction: 4 → 3

**Decision**: **Schedule** (default) | **Clean** (CleanRooms + Routines) | **History** (History + Consumables + CleanSettings). Triggers moves into a fourth hidden panel accessible via Clean tab or collapsed section.

**Rationale**: Matches desktop tab structure. Schedule as default replaces "Now" — on mobile the most important glanceable view is the schedule urgency, not the status (which is now always in the status bar). Triggers are advanced; consolidating them into Clean is acceptable.

**Alternative considered**: Schedule | Clean | Plan | History (keep 4). Rejected: goal is to reduce, not shuffle.

### 6. SchedulePanel truncation

**Decision**: In SchedulePanel, remove the `max-w-[10ch]` (or equivalent) truncation on room name display. No other internal changes to SchedulePanel.

**Rationale**: With flex-1 giving Schedule more width, room names have room to breathe. Truncation was a workaround for the narrow sidebar.

## Risks / Trade-offs

- **[Risk] Tab state key collision** — `activeRightTab` sessionStorage key currently holds `"rooms" | "routines" | "triggers" | "info"`. After this change valid values are `"clean" | "triggers" | "history"`. Old stored value will not match any new tab → defaults to "clean". Acceptable; no migration needed.
- **[Risk] Mobile "Triggers" discoverability** — Triggers panel moves from its own "Plan" tab into a subsection of the Clean tab. Power users who rely on Triggers may not immediately find it. Mitigation: ensure it appears visibly within the Clean tab (not behind an expand/collapse).
- **[Trade-off] StatusBar loses StalePanel wrapper** — The current StatusPanel uses the `Panel` card wrapper with stale-title support. The new StatusBar is a raw strip; stale state should be indicated by a visual cue (e.g., `opacity-60` on the bar or a `⏱` badge on the timestamp).

## Migration Plan

1. Implement `StatusBar.tsx`
2. Rewrite `App.tsx` layout
3. Update `SchedulePanel.tsx` (remove truncation)
4. Build frontend, restart service, smoke test
5. Delete `StatusPanel.tsx` and `ActionsPanel.tsx` in a follow-up cleanup commit once confirmed

No rollback complexity — purely frontend. Git revert is sufficient if needed.

## Open Questions

- Should Triggers panel be a collapsible section inside Clean tab, or rendered inline (always visible)? → **Inline for now** (simpler, consistent with current UX).
- Should the status bar "Locate" button show a label or icon-only? → **Icon-only** (space constrained; tooltip on hover for desktop).
