## Why

The completion monitor uses a real-time state machine to detect clean completion, but it polls every 60 seconds — easily missing state transitions. If the vacuum encounters an error (e.g., gets stuck), the monitor clears the active clean on the error state, and when the user fixes the issue and the clean resumes and completes, nobody is watching. Result: rooms never get credit. All 5 clean events in production have `complete = 0`.

## What Changes

- Replace state-machine completion detection with **device history reconciliation**: after dispatch, match clean events against the device's authoritative clean history by timestamp correlation
- Demote `_active_clean` to a UI/dispatch-guard role — it no longer gates credit
- Add a reconciliation pass to the health poll loop that checks unreconciled events against device history
- Remove the `started_at` gate, dispatch timeout, and error-state clearing logic from the completion path

## Capabilities

### New Capabilities
- `history-reconciliation`: Reconcile scheduler clean events against device clean history to determine completion, replacing real-time state monitoring

### Modified Capabilities
- `completion-monitor`: Remove state-based completion detection; completion is now determined by history reconciliation. Keep `_active_clean` for UI feedback and double-dispatch prevention only.

## Impact

- `src/vacuum/dashboard.py`: Completion detection logic rewritten; health poll loop gains reconciliation step
- `src/vacuum/scheduler.py`: May need new query to find unreconciled events; reconciliation result storage
- `src/vacuum/client.py`: No changes (existing `get_clean_history()` is sufficient)
- Device API: One additional `get_clean_history()` call per health poll (every 60s), minor load increase
