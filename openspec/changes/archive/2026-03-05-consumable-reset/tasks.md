## 1. VacuumClient

- [x] 1.1 Add `reset_consumable(attribute: str)` async method to `VacuumClient` that validates the attribute against the 4 known values and calls `ConsumableTrait.reset_consumable(ConsumableAttribute)`

## 2. Dashboard API

- [x] 2.1 Add `POST /api/consumables/reset/{attribute}` endpoint that validates the attribute, calls `client.reset_consumable(attribute)`, returns `{ok: true}` on success or HTTP 400 for unknown attributes

## 3. Dashboard UI

- [x] 3.1 Add a "Reset" button next to each consumable progress bar in the consumables panel HTML
- [x] 3.2 Add JS `resetConsumable(attribute, label)` function that shows a confirm dialog, POSTs to the reset endpoint, and refreshes the consumables panel on success
- [x] 3.3 Show error alert if the reset API call fails

## 4. Verification

- [x] 4.1 Verify dashboard serves correctly and consumables panel renders with reset buttons
- [x] 4.2 Test reset flow end-to-end (sensor reset since it's at ~0%)
