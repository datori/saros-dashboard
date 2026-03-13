## 1. Command Semaphore

- [ ] 1.1 Add `_command_semaphore = asyncio.Semaphore(2)` module-level in `dashboard.py`
- [ ] 1.2 Wrap the `fn()` call inside `_cached()` with `async with _command_semaphore` so all read-path device commands are gated
- [ ] 1.3 Wrap device calls in `_tracked_action()` (from connectivity-quick-wins) with `async with _command_semaphore` so write-path commands are also gated
- [ ] 1.4 Wrap the `client.clean_rooms()` call in `_check_dispatch()` with `async with _command_semaphore` so auto-window dispatch commands are also gated by the same concurrency limit

## 2. Connectivity Gate

- [ ] 2.1 Add connectivity check in `_cached()`: before calling `fn()`, if `_client` and not `_client.is_connected` and stale data exists for key, return stale data immediately (skip the device call)
- [ ] 2.2 Add connectivity check in `_tracked_action()`: if `_client` and not `_client.is_connected`, raise `HTTPException(503, "Device disconnected")` immediately
- [ ] 2.3 Add connectivity check in `_check_dispatch()`: skip dispatch if `_client` is None or not `_client.is_connected` (don't attempt device commands during disconnection)

## 3. Tiered Reconnect

- [ ] 3.1 Rewrite `_maybe_reconnect()`: if `_client.is_connected` is True AND `_last_contact` is within 120s, reset failure counter and return (errors are device-side)
- [ ] 3.2 In `_maybe_reconnect()`, if `_client.is_connected` is True BUT `_last_contact` is stale (>120s ago or None), skip library wait and proceed directly to full VacuumClient recreation (zombie connection)
- [ ] 3.3 In `_maybe_reconnect()`, if not connected, poll `_client.is_connected` every 5s for up to 60s waiting for library self-heal
- [ ] 3.4 In `_maybe_reconnect()`, if still not connected after 60s, proceed with full VacuumClient recreation (existing behavior)

## 4. Broader Cache Warming

- [ ] 4.1 Expand `_health_poll_loop()` to warm `settings` and `consumables` (in addition to existing `status`) in sequence with `await asyncio.sleep(2)` between each. Place cache warming before the completion monitor and dispatch checks so status is warm before those run.
- [ ] 4.2 Add early abort: if any cache-warming fetch in the cycle raises, skip remaining cache warming but still run `_check_active_clean()` and `_check_dispatch()` (completion monitoring and window dispatch must not be skipped due to a transient fetch error)
