## Context

The Saros 10R supports four distinct clean modes driven by the combination of `FanSpeed` and `WaterFlow`:

| Mode | FanSpeed | WaterFlow |
|------|----------|-----------|
| Vacuum only | active (e.g. 102) | OFF (200) |
| Mop only | OFF (105) | active (e.g. 202) |
| Both (simultaneous) | active | active |
| Vacuum then Mop | active | VAC_THEN_MOP (235) |

`WaterFlow.VAC_THEN_MOP = 235` matches `RoborockMopIntensitySaros10R.vac_followed_by_mop` — the device-native sequential mode. Currently missing from our enum.

The dashboard scheduler logs modes as `"vacuum"`, `"mop"`, or `"both"`. The scheduler's `_get_last_cleaned` already queries `e.mode = ? OR e.mode = 'both'` so both vacuum and mop timestamps are correctly derived from "both" events. The only gap is that the mode inference in `api_rooms_clean` and `api_action` doesn't detect `fan_speed=OFF` (mop-only), defaulting everything to `"vacuum"`.

## Goals / Non-Goals

**Goals:**
- Expose all four clean modes as a first-class concept in both the Clean Rooms panel and Start Clean action
- Add `VAC_THEN_MOP` to `WaterFlow` enum so it's reachable from the API
- Fix mode inference so mop-only dispatches log correctly in the scheduler
- Keep individual fan_speed/water_flow overrides available for fine-tuning

**Non-Goals:**
- No new API endpoints; clean mode is a UI layer over existing fan_speed + water_flow fields
- No changes to `scheduler.py` — the schema and queries already handle all three modes correctly
- No changes to MCP tools or CLI

## Decisions

### Decision 1: Clean mode as UI preset, not a new API field

**Choice**: The clean mode selector pre-populates `fan_speed` and `water_flow` in the form; the API receives the same `fan_speed`/`water_flow` fields it always has.

**Alternative**: Add a `clean_mode` field to `RoomsCleanRequest` and `StartCleanRequest` and translate it server-side.

**Rationale**: No API contract change needed. The translation is naturally UI-level. Adding a `clean_mode` API field would require handling conflicts (e.g., `clean_mode=mop` + `fan_speed=TURBO`) and versioning. The simple approach is correct here.

### Decision 2: Mode selector pre-populates but doesn't lock fields

**Choice**: Selecting "Mop only" sets `fan_speed` to `OFF` in the dropdown but leaves it editable. The submit reads whatever fan_speed/water_flow are actually set.

**Alternative**: Lock/disable fields when a mode is selected to prevent contradictory combinations.

**Rationale**: Locking creates friction and makes the UI feel less transparent. Users should be able to see what's being sent. An expert user who wants "mop only" but then overrides water flow should be able to.

### Decision 3: VAC_THEN_MOP as a WaterFlow value

**Choice**: Add `WaterFlow.VAC_THEN_MOP = 235` to the existing `WaterFlow` enum.

**Rationale**: Consistent with the existing pattern — `WaterFlow.OFF` already signals "no mopping." `VAC_THEN_MOP` is functionally a water flow setting (the device interprets it as such on the `SET_WATER_BOX_CUSTOM_MODE` command).

### Decision 4: Mop inference for scheduler logging

**Choice**: Mode is inferred from the actual `fan_speed` and `water_flow` values in the request body:
- `fan_speed == "OFF"` → `"mop"`
- `water_flow` is non-None and not `"OFF"` → `"both"` (covers `VAC_THEN_MOP` too, since it does both)
- otherwise → `"vacuum"`

This logic is extracted into a small helper `_infer_clean_mode(fan_speed_str, water_flow_str)` to avoid duplication across `api_rooms_clean` and `api_action`.

## Risks / Trade-offs

- **Risk: Start Clean action grows UI surface** → Mitigation: The clean mode + fan speed + water flow fields for Start Clean are shown below the action buttons in a compact collapsible or inline section, similar to the rooms form override section.
- **Risk: VAC_THEN_MOP value collision** → The value 235 is confirmed from `RoborockMopIntensitySaros10R.vac_followed_by_mop`; no conflict with existing `WaterFlow` values (OFF=200, LOW=201, MED=202, HIGH=203, EXTREME=250, SMART=209).
- **Risk: Stale cache after mode change** → Cache invalidation on writes is already in place (`_cache_invalidate("status")` after rooms/clean and action). No new risk.
