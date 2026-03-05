## Why

The dashboard background is near-black (`#0f1117`), making the UI feel oppressively dark. Lifting the palette to GitHub Dark Dimmed levels improves readability and reduces eye strain while preserving the dark-mode aesthetic.

## What Changes

- Update CSS custom property values in `dashboard.py` for background, surface, border, text, and muted colors
- Proportionally lift badge background colors so status indicators remain visually balanced against the new surface tones
- Keep all accent, action, and semantic colors unchanged

## Capabilities

### New Capabilities
<!-- none -->

### Modified Capabilities
- `web-dashboard`: Visual color palette updated — no behavioral or API changes

## Impact

- `src/vacuum/dashboard.py`: CSS variable block only (9 color values changed)
- No API, logic, or structural changes
