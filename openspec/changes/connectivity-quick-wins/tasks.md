## 1. Stale Cache Preservation

- [ ] 1.1 Remove `_stale_cache.clear()` from `_maybe_reconnect()` in `dashboard.py` (keep `_cache.clear()`)

## 2. VacuumClient `is_connected` Property

- [ ] 2.1 Add `is_connected` property to `VacuumClient` in `client.py` that returns `self._device.is_connected` if authenticated, `False` otherwise

## 3. Write Failure Tracking

- [ ] 3.1 Create `_tracked_action(fn)` async helper in `dashboard.py` that wraps a device call with `_record_success()` / `_record_failure()` + `_maybe_reconnect()` on threshold
- [ ] 3.2 Update `api_action()` to use `_tracked_action()` for all device commands (start, stop, pause, dock, locate). Note: the `start` branch now has post-call logic that populates `_active_clean` for completion monitoring — `_tracked_action` must wrap only the device call (`start_clean`), not the `_active_clean` setup that follows it
- [ ] 3.3 Update `api_settings_post()` to use `_tracked_action()` for set_fan_speed, set_mop_mode, set_water_flow calls
- [ ] 3.4 Update `api_rooms_clean()` to use `_tracked_action()` for the `clean_rooms` call. Note: post-call logic populates `_active_clean` for completion monitoring — `_tracked_action` must wrap only the device call, not the `_active_clean` setup that follows it
- [ ] 3.5 Update `api_routine()` to use `_tracked_action()` for the run_routine call

## 4. Enhanced Health Endpoint

- [ ] 4.1 Update `api_health()` in `dashboard.py` to include `mqtt_connected` (from `_client.is_connected`), `failures` (from `_client_failures`), and `reconnecting` (from `_reconnect_lock.locked()`)
