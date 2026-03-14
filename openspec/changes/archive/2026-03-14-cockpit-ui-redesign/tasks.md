## 1. CSS — Cockpit Layout Structure

- [x] 1.1 Replace `.grid` auto-fill rule with flex row layout: `display: flex; gap: 16px` at ≥ 900px breakpoint
- [x] 1.2 Add `#sidebar` styles: `width: 240px; flex-shrink: 0; position: sticky; top: 20px; max-height: calc(100vh - 40px); overflow-y: auto; display: flex; flex-direction: column; gap: 16px`
- [x] 1.3 Add `#right-pane` styles: `flex: 1; min-width: 0; display: flex; flex-direction: column; gap: 16px`
- [x] 1.4 Add `#right-tab-bar` horizontal tab styles (pill/underline, accent on active, hidden at < 900px)
- [x] 1.5 Update mobile breakpoint from `max-width: 639px` to `max-width: 899px` everywhere it appears
- [x] 1.6 Ensure sidebar and right-pane tab bar are hidden (`display: none`) at < 900px

## 2. HTML — Restructure Panel Container

- [x] 2.1 Wrap Status, Actions, Consumables panels in `<div id="sidebar">`
- [x] 2.2 Create `<div id="right-pane">` with `<div id="right-tab-bar">` containing Rooms / Routines / Triggers / Info tab buttons
- [x] 2.3 Assign `data-right-tab` attributes to all right-pane panels (rooms, routines, triggers, info)
- [x] 2.4 Move Auto-Clean Triggers and Window Planner panels into right pane under `data-right-tab="triggers"`
- [x] 2.5 Move Clean Settings panel into right pane under `data-right-tab="info"`
- [x] 2.6 Move Cleaning Schedule and Clean History panels into right pane under `data-right-tab="info"`
- [x] 2.7 Remove `grid-column: 1/-1` from full-width panels (no longer needed in flex layout)

## 3. HTML — Actions Panel Simplification

- [x] 3.1 Remove the "Start clean overrides" section (fan speed, water flow, clean mode selects) from the Actions panel in the sidebar
- [x] 3.2 Keep only the five action buttons (Start, Stop, Pause, Dock, Locate) in the sidebar Actions panel

## 4. HTML — Rooms Tab Scope Toggle

- [x] 4.1 Add a scope toggle above the room checkbox list: radio group or segmented control with "All rooms" / "Select rooms" options
- [x] 4.2 Wire toggle to show/hide room checkbox list: "All rooms" hides `#room-check-list`; "Select rooms" shows it
- [x] 4.3 Consolidate override controls into one block (fan speed, water flow, clean mode, route, repeat) shared by both scopes — remove duplicate override block that was in Actions panel
- [x] 4.4 Update Start Clean button handler: if scope = "all", call `doAction('start')` with override values; if scope = "select", call `cleanRooms()` with checked IDs and override values
- [x] 4.5 Pass override values from the unified Rooms tab selects when calling `doAction('start')` (currently start ignores per-invocation overrides from the rooms form)

## 5. JS — Right-Pane Tab Logic

- [x] 5.1 Add `switchRightTab(name)` function: sets `data-active-right-tab` on `#right-pane`, updates `.right-tab-btn.active` class
- [x] 5.2 Add CSS rules: `#right-pane[data-active-right-tab="rooms"] [data-right-tab]:not([data-right-tab="rooms"]) { display: none }` (and same for routines, triggers, info)
- [x] 5.3 Persist active right tab to `sessionStorage` under `activeRightTab`; restore on page load
- [x] 5.4 Default right tab to `rooms` if no stored value

## 6. JS/CSS — Mobile Tab Updates

- [x] 6.1 Update mobile tab bar HTML: rename tabs to Now / Clean / Plan / Info (4 tabs)
- [x] 6.2 Update `data-tab` assignments on all panels to match new 4-tab scheme (see spec: mobile-tabs)
- [x] 6.3 Update tab-hide CSS rules for the 4 new tab names (`home` → `now`, `clean`, `plan` → new, `info`)
- [x] 6.4 Update `switchTab()` JS to handle 4-tab names; update `sessionStorage` default to `now`
- [x] 6.5 Ensure Consumables panel has `data-tab="info"` (moves from Now to Info on mobile)

## 7. Verification

- [x] 7.1 Desktop (≥ 900px): sidebar is sticky, right pane tabs work, all 4 tabs show correct panels
- [x] 7.2 Desktop: Actions panel has no override dropdowns
- [x] 7.3 Desktop: Rooms tab "All rooms" hides checkboxes; "Select rooms" shows them; Start Clean dispatches correctly for each
- [x] 7.4 Mobile (< 900px): bottom tab bar shows Now/Clean/Plan/Info; correct panels per tab
- [x] 7.5 Mobile: Consumables appear on Info tab; triggers appear on Plan tab
- [x] 7.6 Tab state persists across reload on both desktop and mobile
- [x] 7.7 No layout breakage at ~900px viewport width edge case
