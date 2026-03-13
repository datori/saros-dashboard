## Context

The dashboard is a single FastAPI app with all HTML/CSS/JS embedded in one Python string (`_HTML` in `dashboard.py`). There are no static files, no asset pipeline. The server runs over plain HTTP on the local network (e.g. `http://<your-lan-ip>:8181`).

iOS "Add to Home Screen" requires:
1. A Web App Manifest (`/manifest.json`) with `"display": "standalone"` and icon references
2. Apple-specific `<meta>` tags in the HTML `<head>`
3. An icon image reachable at a URL

Service workers (needed for true offline/Tier 2 PWA) require HTTPS and are explicitly out of scope.

## Goals / Non-Goals

**Goals:**
- Enable iOS "Add to Home Screen" with standalone display (no browser chrome)
- Dark theme integration in the status bar and splash background
- Proper icon on iOS home screen
- iPhone notch/home-indicator safe-area handling in standalone mode

**Non-Goals:**
- Service worker / offline caching (requires HTTPS, no practical value for this dashboard)
- Android PWA install prompt
- Push notifications
- Splash screen images (iOS auto-generates from icon + background color)
- Separate static files directory or asset pipeline

## Decisions

### Icon generation: SVG route, no external dependencies
**Decision**: Serve the icon as an SVG from a FastAPI route. iOS Safari renders SVG as apple-touch-icon since iOS 9.

**Alternatives considered**:
- Base64-encoded PNG embedded in HTML: works, but produces ~3KB of noise in the Python source
- Canvas-rendered icon via JS: clever but fragile; requires JS execution before the icon is registered
- Pillow/cairosvg to generate PNG: adds a dependency for a ~100-line feature

SVG route is ~10 lines of Python, zero dependencies, perfectly readable.

**Icon design**: Dark circle (`#22272e`) with a white robot-style stylized "V" — matches the dashboard's `--bg` color.

### Manifest served as FastAPI route, not a static file
**Decision**: `GET /manifest.json` returns `JSONResponse` built from a Python dict.

Keeps everything in one file. No `StaticFiles` mount, no new directories. The manifest content is static data — there's no need to read it from disk.

### iOS meta tags: inline in `_HTML`
The `<head>` of `_HTML` gets 4 new `<meta>` tags and 1 `<link>` tag. Minimal diff, no structural changes to how the HTML is assembled.

### Status bar style: `black-translucent`
Allows the dark `#22272e` header to extend behind the iOS status bar, giving a seamless full-screen feel. The `<meta name="theme-color">` is set to the same `#22272e`.

### Safe-area CSS: `env(safe-area-inset-*)` on `body`
In standalone mode, `padding-top: env(safe-area-inset-top)` etc. prevents content from being obscured by the notch (top) and home indicator (bottom). Uses `max()` to preserve the existing `20px` body padding: `padding: max(20px, env(safe-area-inset-top)) max(20px, env(safe-area-inset-right)) max(20px, env(safe-area-inset-bottom)) max(20px, env(safe-area-inset-left))`.

The `<meta name="viewport">` gets `viewport-fit=cover` to enable safe area insets.

## Risks / Trade-offs

**SVG icon on older iOS**: SVG apple-touch-icon works from iOS 9+. The device is iPhone with recent iOS — acceptable.
→ Mitigation: none needed; iOS 9 is 10 years old.

**`black-translucent` status bar**: Content under status bar can be partially obscured if `safe-area-inset-top` CSS is missing or wrong.
→ Mitigation: safe-area padding on body handles this.

**Manifest ignored without HTTPS on some Android browsers**: Not a concern for this iOS-only target.
→ Accept: Android support is not a goal.

**Icon not appearing until iOS caches it**: First "Add to Home Screen" may show a page preview instead of icon if iOS hasn't loaded `/icons/apple-touch-icon.png` yet.
→ Mitigation: The `<link rel="apple-touch-icon">` in `<head>` tells iOS to preload the icon URL before the user adds to home screen.

## Open Questions

None — scope is well-defined.
