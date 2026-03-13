## Why

The dashboard's cloud connectivity resilience has three low-effort gaps: the stale cache (our safety net during outages) is cleared on reconnect, write-action failures don't contribute to the reconnect decision, and the health endpoint lacks enough detail to diagnose problems. These are all small fixes in `dashboard.py` that improve reliability without architectural changes.

## What Changes

- **Preserve stale cache on reconnect**: Stop clearing `_stale_cache` in `_maybe_reconnect()`. Only the hot cache (`_cache`) should be cleared. Stale data is the fallback for outages — clearing it defeats the purpose.
- **Track write-action failures**: POST endpoints (`api_action`, `api_settings_post`, `api_rooms_clean`, `api_routine`) don't go through `_cached()`, so failures never trigger `_record_failure()`. Add failure/success tracking to write endpoints so they contribute to the reconnect decision.
- **Richer health endpoint**: Expose MQTT connection state (`device.is_connected`), current failure count, and whether a reconnect is in progress, alongside the existing `ok`/`last_contact_seconds_ago`/`reconnect_count` fields.

## Capabilities

### New Capabilities

- `write-failure-tracking`: Write (POST) endpoints contribute to the connectivity failure counter used by the auto-reconnect mechanism.
- `enhanced-health-endpoint`: The `/api/health` endpoint exposes MQTT connection state, failure count, and reconnect-in-progress status.

### Modified Capabilities

- `dashboard-response-cache`: Stale cache is no longer cleared during reconnect, preserving fallback data across connectivity disruptions.

## Impact

- **Code**: `dashboard.py` only — `_maybe_reconnect()`, POST endpoint handlers, `/api/health` endpoint
- **API**: `/api/health` response gains new fields (`mqtt_connected`, `failures`, `reconnecting`); existing fields unchanged
- **Frontend**: Health banner JS could optionally use new fields (not required for this change)
