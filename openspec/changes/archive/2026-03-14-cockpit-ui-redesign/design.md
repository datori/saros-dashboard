## Context

The dashboard is a single-file FastAPI app (`dashboard.py`) where all HTML, CSS, and JS live in a single `_HTML` string. The current layout is an `auto-fill` CSS Grid that dumps all 10 panels onto the screen at once on desktop. On mobile (< 640px), a fixed bottom tab bar hides non-active panels. The core problem: no visual hierarchy on desktop, and the mobile tabs ("Home/Clean/Info") are poorly named and unevenly loaded.

This change is purely frontend — no Python server logic, API, or scheduler changes needed.

## Goals / Non-Goals

**Goals:**
- Desktop (≥ 900px): fixed-width sidebar (Status + Actions + Consumables) always visible; tabbed right pane for everything else
- Mobile (< 900px): 4-tab bottom nav (Now / Clean / Plan / Info) with clear, even panel distribution
- Eliminate duplicate override dropdowns — one set of overrides in the Rooms tab covers both "start all" and "start selected"
- Raise breakpoint from 640px to 900px so tablets and small laptops get the sidebar layout

**Non-Goals:**
- No backend API changes
- No new data — panels keep their existing data sources
- No visual theme changes (colors, typography remain the same)
- No animation or transition polish beyond what already exists

## Decisions

### D1 — Sidebar via CSS Flexbox, not Grid

The top-level layout switches from `display: grid` (auto-fill) to `display: flex; flex-direction: row` at ≥ 900px. The sidebar uses `position: sticky; top: 0; height: 100vh; overflow-y: auto` so it pins in place during right-pane scroll.

**Alternative considered**: CSS Grid with named areas. More expressive but harder to reason about when the sidebar needs sticky behavior. Flexbox `position: sticky` is well-understood.

### D2 — Right pane uses its own horizontal tab bar (separate from mobile bottom nav)

The right pane gets `<div id="right-tab-bar">` with horizontal pill-style tabs (Rooms / Routines / Triggers / Info). This is a second, independent tab system that only appears on desktop. The mobile bottom nav (`#tab-bar`) only appears on mobile. The two systems do not share logic.

**Alternative considered**: One unified tab system that changes orientation by viewport. Too complex — the tab sets are different (3 tabs mobile "Now" collapses sidebar content; desktop sidebar is always visible so "Now" tab doesn't exist).

### D3 — Sidebar Actions panel: quick buttons only, no override dropdowns

Currently the Actions panel has Start/Stop/Pause/Dock/Locate buttons plus a set of fan speed / water flow / mode override selects. These overrides are duplicated in the Clean Rooms panel. In the new layout, the sidebar Actions panel keeps only the five buttons. Override selects live exclusively in the Rooms tab (covering both "all rooms" and "select rooms" scenarios via a toggle).

**Alternative considered**: Keep overrides in sidebar, remove from Rooms tab. Rejected — the Rooms tab is where the user is already thinking about "what to clean and how". Sidebar should be for instant decisions (stop, dock, locate).

### D4 — Rooms tab: single "scope" toggle (All / Select)

The Rooms tab has a radio/toggle at the top — "All rooms" or "Select rooms". When "All rooms" is active, the checkbox list is hidden. Override settings (fan, water, mode, route, repeat) appear below regardless of scope. The Start Clean button always respects the current scope.

This eliminates the conceptual split between the Actions panel (for all-rooms cleans) and Clean Rooms panel (for targeted cleans).

### D5 — Panel assignments

**Sidebar (desktop-only, always visible):**
- Status
- Actions (5 buttons, no overrides)
- Consumables

**Right pane tabs (desktop) / Mobile tab mapping:**

| Right pane tab | Panels | Mobile tab |
|---|---|---|
| Rooms | Clean Rooms + scope toggle + overrides | Clean |
| Routines | Routines | Clean |
| Triggers | Auto-Clean Triggers + Window Planner | Plan |
| Info | Clean Settings (defaults) + Schedule + History | Info |

**Mobile "Now" tab**: Status + Actions (both pulled from sidebar on mobile).
**Mobile "Info" tab**: Consumables added here (sidebar not present on mobile).

### D6 — Breakpoint raised to 900px

640px is too narrow for a sidebar. At 900px, the sidebar (240px) + right pane (660px min) comfortably fits a typical laptop. Below 900px reverts to mobile layout with bottom tabs.

## Risks / Trade-offs

**[Risk] Tab state divergence between desktop and mobile** → The right-pane tab state (`activeRightTab`) and mobile tab state (`activeTab`) are independent. Switching viewport size mid-session may leave the user on an unexpected tab. Mitigation: default each to their respective first tab on init; no cross-sync needed.

**[Risk] Sidebar height overflow on small-height screens** → On a 768px-tall screen, the sidebar content (status + 5 buttons + 4 consumable bars) may overflow. Mitigation: `overflow-y: auto` on sidebar; consumable bars can compact slightly at small heights.

**[Risk] "Start" button scope ambiguity** → With overrides moved out of the sidebar, a user pressing Start in the sidebar with no rooms selected may be confused. Mitigation: sidebar Start always means "start all rooms with device defaults". It maps to the existing `doAction('start')` call — unchanged behavior, just clearer through context.

## Migration Plan

Pure CSS/JS/HTML edit within `_HTML` string in `dashboard.py`. No data migration. No API changes. Rollback is a git revert.
