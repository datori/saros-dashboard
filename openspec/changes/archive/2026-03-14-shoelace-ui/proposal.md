## Why

The dashboard uses raw HTML form controls (native `<select>`, `<button>`, `<input>`) that are visually inconsistent and hard to style uniformly in a dark theme. Replacing them with Shoelace web components gives polished, accessible, theme-aware controls with zero build-step overhead via CDN.

## What Changes

- Add Shoelace CDN links (dark theme CSS + autoloader JS) to `<head>`
- Replace action `<button>` elements with `<sl-button>` (variant-mapped to existing btn-primary/danger/warning/neutral)
- Replace all `<select>/<option>` dropdowns with `<sl-select>/<sl-option>` (fan speed, water flow, mop mode, route, clean mode, device settings)
- Replace status/battery/consumable badges with `<sl-badge>`
- Replace consumable progress bars with `<sl-progress-bar>`
- Replace right-pane tab bar (`#right-tab-bar` + `.right-tab-btn`) with `<sl-tab-group>/<sl-tab>/<sl-tab-panel>`
- Replace scope toggle (All rooms / Select rooms) with `<sl-radio-group>/<sl-radio-button>`
- Map Shoelace CSS custom properties onto existing `--bg`, `--surface`, `--accent`, `--text` etc. variables so the dark theme carries through without rewriting colour tokens
- Update JS references from `.value` on native selects to `.value` on `<sl-select>` (same API, no logic changes)

## Capabilities

### New Capabilities
- `shoelace-integration`: Shoelace CDN loading, theme token mapping, and component usage conventions for the dashboard

### Modified Capabilities
- (none — no spec-level behaviour changes, only implementation detail changes)

## Impact

- `src/vacuum/dashboard.py`: HTML/CSS changes throughout `_HTML` string; JS value reads unchanged (sl-select exposes `.value`); `sl-tab-group` emits `sl-tab-show` event instead of `onclick` — tab switching JS updated accordingly
- No backend, API, or scheduler changes
- CDN dependency added: `cdn.jsdelivr.net/npm/@shoelace-style/shoelace` (pinned minor version)
