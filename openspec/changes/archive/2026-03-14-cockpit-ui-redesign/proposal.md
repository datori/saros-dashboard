## Why

The dashboard presents all panels simultaneously with no visual hierarchy, making it hard to find the controls you actually need — especially on desktop where 10 panels flood the screen at once. The "cockpit" layout solves this by keeping status and quick controls always visible in a fixed sidebar, while secondary content lives in a tabbed right pane.

## What Changes

- Add a fixed left sidebar (~240px) containing: Status, quick-action buttons, and Consumables — always visible on desktop
- Add a tabbed right pane with four tabs: **Rooms**, **Routines**, **Triggers**, **Info**
- Triggers panel moves from the home grid to its own dedicated tab (alongside Window Planner)
- Clean Settings (device defaults) moves to the Info tab
- Eliminate duplicate override dropdowns — "start all rooms" and "select rooms" share one set of override controls in the Rooms tab
- Mobile: 4-tab bottom nav (**Now** / **Clean** / **Plan** / **Info**) replacing the current 3-tab set
- Responsive breakpoint raised from 640px to 900px so the sidebar layout kicks in on tablets and small laptops

## Capabilities

### New Capabilities
- `cockpit-layout`: Desktop sidebar + tabbed right pane layout, replacing the auto-fill grid for viewports ≥ 900px

### Modified Capabilities
- `mobile-tabs`: Tab count changes from 3 to 4 (Now / Clean / Plan / Info), panel assignments change, breakpoint changes from 640px to 900px

## Impact

- `src/vacuum/dashboard.py`: HTML/CSS/JS rewrite of layout, tab logic, and panel placement; JS action handlers remain but wiring changes
- No backend API changes
- No changes to Python server logic, client, scheduler, or MCP server
