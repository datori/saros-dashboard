## 1. CDN Setup & Theme

- [x] 1.1 Add Shoelace dark theme CSS link tag to `<head>`: `cdn.jsdelivr.net/npm/@shoelace-style/shoelace@2/cdn/themes/dark.css`
- [x] 1.2 Add Shoelace autoloader script tag to `<head>`: `cdn.jsdelivr.net/npm/@shoelace-style/shoelace@2/cdn/shoelace-autoloader.js` with `type="module"`
- [x] 1.3 Add `class="sl-theme-dark"` to `<body>` element
- [x] 1.4 Remove or consolidate any custom button/select/badge CSS rules made redundant by Shoelace (`.btn`, `.btn-*`, `select { }`)

## 2. Action Buttons → sl-button

- [x] 2.1 Replace the five action buttons in the sidebar Actions panel with `<sl-button>`: Start (`variant="primary"`), Stop (`variant="danger"`), Pause (`variant="warning"`), Dock (`variant="default"`), Locate (`variant="default"`)
- [x] 2.2 Replace all small utility buttons (`btn-sm`) with `<sl-button size="small">`: schedule Edit, trigger Add/Edit/Del, planner Refresh, settings Save, rooms Start Clean
- [x] 2.3 Replace routine Run buttons in `loadRoutines()` JS template string with `<sl-button variant="primary" size="small">`
- [x] 2.4 Update `doAction()` button-disable logic: replace `document.querySelectorAll('.actions-grid .btn')` with `document.querySelectorAll('.actions-grid sl-button')`

## 3. Dropdowns → sl-select

- [x] 3.1 Replace Clean Rooms panel override selects with `<sl-select>`/`<sl-option>`: Clean Mode (`id="rooms-clean-mode"`), Fan Speed (`id="rooms-fan-speed"`), Mop Mode (`id="rooms-mop-mode"`), Water Flow (`id="rooms-water-flow"`), Route (`id="rooms-route"`)
- [x] 3.2 Replace Clean Settings panel selects with `<sl-select>`/`<sl-option>`: Fan Speed (`id="set-fan-speed"`), Mop Mode (`id="set-mop-mode"`), Water Flow (`id="set-water-flow"`)
- [x] 3.3 Update `populateSelect()` helper to build `<sl-option>` elements instead of `<option>` inside `<sl-select>`
- [x] 3.4 Add `sl-change` event listeners for Clean Mode select → `applyCleanMode()` and scope radio group → `updateCleanScope()` (replacing `onchange=` attributes, since `onsl-change=` is not a valid HTML attribute)
- [x] 3.5 Update `applyCleanMode()` to set `.value` on `sl-select` elements (API is identical to native select — verify no change needed)
- [x] 3.6 Replace Dispatch Settings selects in `_makeSelect()` JS helper with `<sl-select>`/`<sl-option>` markup; update `sl-change` wiring

## 4. Badges → sl-badge

- [x] 4.1 Update `loadStatus()` JS to emit `<sl-badge variant="...">` instead of `<span class="badge badge-*">`: map `badge-green` → `success`, `badge-yellow` → `warning`, `badge-red` → `danger`, `badge-blue` → `primary`, `badge-gray` → `neutral`
- [x] 4.2 Update `pctBadge()` helper to return `<sl-badge>` markup
- [x] 4.3 Update clean history `complete` column in `loadHistory()` to use `<sl-badge variant="success/warning">`

## 5. Progress Bars → sl-progress-bar

- [x] 5.1 Update `progressBar()` helper to return `<sl-progress-bar value="${pct ?? 0}">` with label text as slot content; include Reset button alongside
- [x] 5.2 Style low-percentage bars (≤20%) with `--indicator-color: var(--sl-color-danger-600)` and medium bars (≤50%) with `--indicator-color: var(--sl-color-warning-600)` via inline style on `<sl-progress-bar>`

## 6. Right-Pane Tabs → sl-tab-group

- [x] 6.1 Replace `<div id="right-tab-bar">` + four `<button class="right-tab-btn">` with `<sl-tab-group id="right-tab-group">`; each panel content wrapped in `<sl-tab-panel name="rooms/routines/triggers/info">`
- [x] 6.2 Add four `<sl-tab slot="nav" panel="rooms/routines/triggers/info">` labels inside the `sl-tab-group`
- [x] 6.3 Remove CSS rules for `#right-tab-bar`, `.right-tab-btn`, `.right-tab-btn.active`, and `#right-pane[data-active-right-tab=...]` — no longer needed
- [x] 6.4 Replace `activateRightTab()` JS function: add `sl-tab-show` event listener on `#right-tab-group` to persist `activeRightTab` to sessionStorage
- [x] 6.5 On page init, use `customElements.whenDefined('sl-tab-group').then(() => { tabGroup.show(stored || 'rooms') })` to restore active tab

## 7. Scope Toggle → sl-radio-group

- [x] 7.1 Replace scope toggle `<div class="scope-toggle">` + two radio `<label><input type="radio">` elements with `<sl-radio-group id="clean-scope" value="select"><sl-radio-button value="all">All rooms</sl-radio-button><sl-radio-button value="select">Select rooms</sl-radio-button></sl-radio-group>`
- [x] 7.2 Add `sl-change` event listener on `#clean-scope` → `updateCleanScope()`
- [x] 7.3 Update `updateCleanScope()` to read `document.getElementById('clean-scope').value` instead of `document.getElementById('scope-all').checked`
- [x] 7.4 Update `startCleanFromRooms()` to check `document.getElementById('clean-scope').value === 'all'` instead of `scope-all.checked`
- [x] 7.5 Remove `.scope-toggle` CSS class rules (replaced by Shoelace styling)

## 8. Verification

- [x] 8.1 All five action buttons render as Shoelace buttons with correct variants and remain functional
- [x] 8.2 All dropdowns render as sl-select; value reads work correctly in cleanRooms, saveSettings, applyCleanMode, startCleanFromRooms
- [x] 8.3 Status panel shows sl-badge elements with correct colour variants
- [x] 8.4 Consumables panel shows sl-progress-bar with correct fill and colour coding
- [x] 8.5 Right-pane tab group works on desktop; tab state persists across reload
- [x] 8.6 Scope toggle renders as segmented radio buttons; switching All/Select shows/hides room list and dispatches correctly
- [x] 8.7 No JS errors in browser console on page load
