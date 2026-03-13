## 1. Database Schema

- [ ] 1.1 Add `profiles` table to `scheduler.init_db()` using `CREATE TABLE IF NOT EXISTS` with columns: `id`, `name`, `fan_speed`, `mop_mode`, `water_flow`, `route`, `is_default`, `sort_order`
- [ ] 1.2 Verify table is created on dashboard startup without affecting existing schedule data

## 2. Backend API

- [ ] 2.1 Add `get_profiles()` async function in `scheduler.py` — returns all profiles ordered by `sort_order, id`
- [ ] 2.2 Add `create_profile(name, fan_speed, mop_mode, water_flow, route, is_default)` in `scheduler.py` — clears other defaults if `is_default=True`
- [ ] 2.3 Add `update_profile(id, **fields)` in `scheduler.py` — updates only provided fields; clears other defaults if `is_default=True`
- [ ] 2.4 Add `delete_profile(id)` in `scheduler.py` — returns False if not found
- [ ] 2.5 Add `GET /api/profiles` endpoint in `dashboard.py`
- [ ] 2.6 Add `POST /api/profiles` endpoint in `dashboard.py` with request model validation (setting names validated against enum members)
- [ ] 2.7 Add `PUT /api/profiles/{id}` endpoint in `dashboard.py` — 404 if not found
- [ ] 2.8 Add `DELETE /api/profiles/{id}` endpoint in `dashboard.py` — 404 if not found

## 3. Profile Chip Bar UI

- [ ] 3.1 Add `loadProfiles()` JS function that fetches `GET /api/profiles` and renders chip bar in both the start-clean and room-clean panels
- [ ] 3.2 Render a permanent "Device defaults" chip (id=null) as the first chip, no edit button
- [ ] 3.3 Render each profile as a selectable chip with a small ✎ edit icon button
- [ ] 3.4 Render a "+" chip/button at the end to open the create modal
- [ ] 3.5 Implement chip selection: clicking a chip marks it active (CSS), clears override dropdowns, then populates non-null profile fields
- [ ] 3.6 On page load, auto-select the default profile chip (or "Device defaults" if none) and populate dropdowns accordingly

## 4. Profile Edit Modal

- [ ] 4.1 Add a single modal HTML element reused for both create and edit
- [ ] 4.2 Implement `openProfileModal(profile=null)` JS function — null = create mode, object = edit mode; pre-fills fields when editing
- [ ] 4.3 Modal contains: name text input, fan_speed dropdown (with "— device default —"), mop_mode dropdown (same), water_flow dropdown (same), route dropdown (same)
- [ ] 4.4 Add "Set as default" checkbox in modal
- [ ] 4.5 Add "Save" button that calls `POST /api/profiles` (create) or `PUT /api/profiles/{id}` (edit), refreshes chip bar on success, closes modal
- [ ] 4.6 Add "Delete profile" button (hidden in create mode) that calls `DELETE /api/profiles/{id}`, refreshes chip bar, closes modal
- [ ] 4.7 Ensure modal is mobile-friendly: full-width on narrow viewports, min 44px touch targets on all buttons and dropdowns

## 5. Clean Flow Integration

- [ ] 5.1 Verify that start-clean JS reads from the override dropdowns (already pre-filled by profile selection) without additional changes — confirm no wiring needed
- [ ] 5.2 Verify room-clean JS likewise reads from its override dropdowns — confirm no wiring needed
- [ ] 5.3 Manual smoke test: select "Mop" profile → start clean → confirm fan_speed/water_flow values appear in request payload

## 6. Polish

- [ ] 6.1 Call `loadProfiles()` in `refreshAll()` so profiles reload on dashboard refresh
- [ ] 6.2 Add error handling in `loadProfiles()` — on API error, show "Device defaults" only, no crash
- [ ] 6.3 Seed two default profiles on first run if `profiles` table is empty: "Vacuum" (fan_speed=TURBO, water_flow=OFF, is_default=1) and "Mop" (fan_speed=BALANCED, water_flow=VAC_THEN_MOP, route=STANDARD)
