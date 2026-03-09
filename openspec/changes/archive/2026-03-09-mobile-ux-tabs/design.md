## Context

The dashboard is a single-page FastAPI app with all HTML/CSS/JS in a single `_HTML` string in `dashboard.py`. There are 9 panels in a CSS Grid using `minmax(340px, 1fr)` — no media queries, just intrinsic responsive layout. The page was recently made a PWA (saved to iOS Home Screen), making mobile UX more prominent. On a 390px iPhone, all 9 panels stack into one long vertical scroll; two panels contain wide tables that overflow the viewport horizontally.

## Goals / Non-Goals

**Goals:**
- Remove the Rooms panel (low utility)
- Add a bottom tab bar visible only on mobile (<640px) that groups 8 remaining panels into 3 tabs
- Fix table horizontal overflow for History and Schedule
- Zero backend changes — all work is in the `_HTML` string

**Non-Goals:**
- Desktop layout changes (tabs are mobile-only)
- Offline support, service workers
- Reordering panels within tabs
- Adding swipe gesture navigation between tabs

## Decisions

### D1: Tab visibility via `@media` + CSS class toggling, not separate routes

**Decision**: One HTML page; tabs show/hide panels using CSS classes and a `@media (max-width: 639px)` block. JS sets `data-active-tab` on a wrapper element; CSS hides panels assigned to inactive tabs.

**Alternatives considered**:
- Separate `/clean`, `/info` routes → breaks single-page feel, requires navigation/back button
- JS-only show/hide with `display: none` → harder to override from desktop media query; CSS approach is declarative and clear

**Rationale**: CSS-driven is the simplest approach that also guarantees desktop is unaffected (media query scope isolates everything).

### D2: Tab assignment via `data-tab` attribute on panels

Each `<div class="panel">` gets `data-tab="home|clean|info"`. The CSS rule `.tabs-active [data-tab]:not([data-tab="<active>"])` hides non-active panels. JS only needs to set one attribute on the container.

### D3: Bottom tab bar (fixed footer, mobile only)

A `<nav id="tab-bar">` is `display: none` on desktop; `display: flex` inside the media query. Positioned `fixed` at bottom, above iOS home indicator via `padding-bottom: env(safe-area-inset-bottom)`.

**Alternatives considered**:
- Top tab bar (like Safari tabs) → harder to reach on large iPhones; native apps trend toward bottom
- Pill-style tabs inside the page → scroll away when user scrolls; fixed nav stays accessible

### D4: Tab state in `sessionStorage`

On load, restore last active tab from `sessionStorage.getItem('activeTab')`. On tab change, persist. Defaults to `'home'` if not set.

**Rationale**: Survives page reload (cache miss after reconnect) without requiring server state. Cleared when browser session ends.

### D5: Table overflow — scroll wrapper + `hide-mobile` CSS class

Wrap each table in `<div class="table-scroll">` with `overflow-x: auto; -webkit-overflow-scrolling: touch`. Secondary columns get `class="hide-mobile"`. `@media` CSS sets `.hide-mobile { display: none }`.

**Columns hidden on mobile:**
- History: "Started by", "Type", "Finish reason" (3 columns) — keep Start, Duration, Area, Complete
- Schedule: "Last Vacuumed", "Last Mopped" (2 columns) — keep Room, Vacuum Due, Mop Due, intervals, Edit

**Alternatives considered**:
- Card layout per row → much more markup change, higher risk
- Always-scroll no column hiding → fine, but 7-column table at 60px/col = 420px which still overflows 350px usable width

### D6: Rooms panel removal

Delete the `<div class="panel">` block for Rooms from HTML. Remove the `refreshRooms()` JS function and its call from `refreshAll()`. The `_rooms` global is still populated by the `loadCleanRooms()` function (used for checkbox building) — keep that fetch.

## Risks / Trade-offs

- **`_rooms` global dependency**: Two places use room data — the Rooms panel (display) and `loadCleanRooms()` (checkbox building). Must confirm only the display panel is removed, not the fetch.
- **`env(safe-area-inset-bottom)` tab bar**: On non-iOS devices this is 0, tab bar sits flush with bottom — acceptable.
- **340px minimum column width vs mobile breakpoint**: Grid switches to single column around 340–360px naturally. The 640px tab breakpoint is wider than the grid's breakpoint, meaning tabs activate before the grid collapses — fine, since the panels are still readable in 2-column mode on a tablet.

## Migration Plan

All changes are in `_HTML` in `dashboard.py`. No DB migrations, no API changes, no restarts of non-dashboard processes needed. Dashboard restart applies changes instantly.

## Open Questions

- None — scope is clear.
