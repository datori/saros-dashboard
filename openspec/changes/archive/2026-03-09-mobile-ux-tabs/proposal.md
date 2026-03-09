## Why

The dashboard is now a PWA saved to the iOS home screen, but the mobile experience is poor: tables overflow horizontally without warning, and the page is so long that finding controls requires significant scrolling. These friction points make the dashboard feel like a desktop page crammed onto a phone rather than a native app.

## What Changes

- Remove the Rooms panel (raw ID/name list; not useful for daily use)
- Add a mobile-only bottom tab bar with three tabs: **Home**, **Clean**, **Info**
- Assign each panel to a tab: Home (Status, Actions, Consumables), Clean (Clean Rooms, Clean Settings, Routines), Info (Schedule, History)
- On desktop (≥640px), all panels remain visible in the existing grid layout with no tabs
- Fix horizontal table overflow in History and Schedule panels: wrap in scroll container + hide non-essential columns on mobile

## Capabilities

### New Capabilities

- `mobile-tabs`: Mobile-only bottom tab bar that groups the 8 remaining panels into three tabs (Home / Clean / Info); panels outside the active tab are hidden via CSS; tab state persists in `sessionStorage`; desktop layout is unaffected
- `mobile-table-overflow`: Horizontal overflow fix for History and Schedule tables on mobile — scroll wrapper + `hide-mobile` CSS class hides secondary columns (History: Started by, Type, Finish reason; Schedule: Last Vacuumed, Last Mopped)

### Modified Capabilities

- `dashboard-ui`: Rooms panel removed from HTML and JS loader

## Impact

- `src/vacuum/dashboard.py` — all changes are in the embedded `_HTML` string (CSS, HTML structure, JS)
- No backend changes, no new routes, no new dependencies
