## 1. Remove Rooms Panel

- [x] 1.1 Delete the Rooms `<div class="panel">` HTML block from `_HTML`
- [x] 1.2 Remove the `refreshRooms()` JS function
- [x] 1.3 Remove the `refreshRooms()` call from `refreshAll()`

## 2. Table Overflow Fix

- [x] 2.1 Add `.table-scroll { overflow-x: auto; -webkit-overflow-scrolling: touch; }` CSS rule
- [x] 2.2 Add `@media (max-width: 639px) { .hide-mobile { display: none !important; } }` CSS rule
- [x] 2.3 Wrap History table in `<div class="table-scroll">` (in the JS template string)
- [x] 2.4 Add `class="hide-mobile"` to History `<th>` and `<td>` for: Started by, Type, Finish reason
- [x] 2.5 Wrap Schedule table in `<div class="table-scroll">` (in the JS template string)
- [x] 2.6 Add `class="hide-mobile"` to Schedule `<th>` and `<td>` for: Last Vacuumed, Last Mopped

## 3. Tab Bar CSS

- [x] 3.1 Add `data-tab` attribute to each of the 8 remaining panels in HTML (`home`, `clean`, or `info`)
- [x] 3.2 Add `<nav id="tab-bar">` with three `<button>` elements (Home, Clean, Info) before `</body>`
- [x] 3.3 Add CSS: `#tab-bar { display: none; }` (hidden by default / on desktop)
- [x] 3.4 Add `@media (max-width: 639px)` block: show `#tab-bar` as `display: flex`, fixed bottom, safe-area padding
- [x] 3.5 Add CSS for tab bar buttons: flex column (icon + label), active accent color, inactive muted color
- [x] 3.6 Add `@media (max-width: 639px)` CSS: add `padding-bottom` to `body` equal to tab bar height (~60px) so content isn't hidden behind fixed bar
- [x] 3.7 Add `@media (max-width: 639px)` CSS: `.tabs-active [data-tab]:not([data-tab="<active>"])` — hide non-active tab panels

## 4. Tab Bar JavaScript

- [x] 4.1 Add `activateTab(tab)` JS function: sets `data-active-tab` on `<body>` (or wrapper), saves to `sessionStorage`, updates button active classes
- [x] 4.2 On page load, call `activateTab(sessionStorage.getItem('activeTab') || 'home')`
- [x] 4.3 Wire each tab button's `onclick` to `activateTab('home'|'clean'|'info')`
- [x] 4.4 Verify CSS selector approach works: body `[data-active-tab="home"]` hides panels with `data-tab` ≠ `home` on mobile
