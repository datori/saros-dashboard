## Why

The auto-clean window system dispatches rooms based on priority scoring, but there's no way to see what *would* happen before committing. Users can't preview which rooms would be cleaned for a given time budget, and opening a window requires going through named triggers rather than directly specifying a duration. A visual planner that shows the priority queue against a sliding budget — and lets you open a window directly from it — makes the system transparent and testable.

## What Changes

- Add a "Window Planner" dashboard panel with a budget slider (5–90 min) that shows which rooms would be cleaned at the selected budget, with priority scores and cumulative time bars
- Add `GET /api/window/preview` endpoint returning the full scored priority queue for client-side filtering
- Add `POST /api/window/open` endpoint to open a window with an arbitrary duration (no trigger required)
- The planner doubles as the primary control surface: preview what would happen, then click to open the window

## Capabilities

### New Capabilities
- `window-planner`: Dashboard panel with budget slider, priority queue preview, and direct window opening

### Modified Capabilities
- `clean-windows`: Add `POST /api/window/open` endpoint for opening windows without a named trigger

## Impact

- `src/vacuum/dashboard.py`: New API endpoints, new HTML/CSS/JS panel
- `src/vacuum/scheduler.py`: No changes (existing `get_priority_queue()` provides all needed data)
