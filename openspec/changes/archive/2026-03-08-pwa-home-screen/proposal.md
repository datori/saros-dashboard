## Why

The dashboard is only accessible via a browser URL, which creates friction on mobile. Making it a PWA enables "Add to Home Screen" on iOS, giving the vacuum dashboard a native app-like experience (standalone window, no browser chrome, proper icon on the home screen).

## What Changes

- Add a Web App Manifest (`/manifest.json` route) declaring standalone display mode, theme color, and icons
- Add iOS-specific `<meta>` tags (`apple-mobile-web-app-capable`, status bar style, title) to the HTML
- Add an `<link rel="apple-touch-icon">` pointing to a served icon
- Add a `/icons/apple-touch-icon.png` route serving a simple generated icon
- Add `safe-area-inset` CSS so content doesn't clip under iPhone notch/home indicator in standalone mode

## Capabilities

### New Capabilities
- `pwa-manifest`: Web App Manifest endpoint and iOS meta tags enabling "Add to Home Screen" with standalone display
- `pwa-icon`: Icon serving endpoint providing the apple-touch-icon and manifest icons

### Modified Capabilities
<!-- None — no existing spec-level behavior changes -->

## Impact

- `src/vacuum/dashboard.py`: add 2-3 new FastAPI GET routes; modify `_HTML` `<head>` section
- No new dependencies
- No breaking changes to existing API endpoints
- Works over plain HTTP (no HTTPS required for Tier 1 PWA / Add to Home Screen)
