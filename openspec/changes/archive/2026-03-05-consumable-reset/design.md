## Context

The `python-roborock` library exposes `ConsumableTrait.reset_consumable(ConsumableAttribute)` which sends `RESET_CONSUMABLE` command to the device. Our `VacuumClient` currently reads consumables but has no reset capability. The dashboard's consumables panel shows progress bars but has no interactive controls.

## Goals / Non-Goals

**Goals:**
- Expose reset per-consumable via `VacuumClient.reset_consumable(attribute: str)`
- Add `POST /api/consumables/reset/{attribute}` REST endpoint
- Add a small "Reset" button next to each consumable bar in the UI with confirmation + feedback

**Non-Goals:**
- Bulk reset all consumables at once
- Scheduled/automated resets
- Reset for consumables not tracked by the current device (e.g., mop roller)

## Decisions

**Use attribute string directly as URL param**: The 4 valid values (`sensor_dirty_time`, `filter_work_time`, `side_brush_work_time`, `main_brush_work_time`) are used as-is in the API path. The endpoint validates against the known set and returns 400 for unknown values. No mapping layer needed.

**Client method takes a string, not enum**: `VacuumClient` should accept a plain string to stay consistent with the rest of the client API (no roborock types leak into callers). Internally converts to `ConsumableAttribute`.

**UI: button with confirm dialog**: A reset is irreversible (resets the wear counter). A browser `confirm()` prompt before POSTing prevents accidental resets. On success, the consumables panel auto-refreshes.

## Risks / Trade-offs

- [Cloud command may fail silently] → The library's `reset_consumable` refreshes after sending; if the device rejects it, the refresh will show unchanged values. The endpoint returns the error to the UI.
- [User resets wrong consumable] → Mitigated by confirm dialog showing the consumable name.

## Migration Plan

No migration needed. Additive changes only. Rolling back is as simple as reverting the 3 changed files.
