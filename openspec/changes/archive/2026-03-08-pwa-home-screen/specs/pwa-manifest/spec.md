## ADDED Requirements

### Requirement: Web App Manifest endpoint
The dashboard server SHALL serve a Web App Manifest at `GET /manifest.json` as `application/manifest+json`. The manifest SHALL include `name`, `short_name`, `start_url`, `display: "standalone"`, `background_color`, `theme_color`, and an `icons` array referencing the apple-touch-icon.

#### Scenario: Manifest is reachable
- **WHEN** a client requests `GET /manifest.json`
- **THEN** the server returns HTTP 200 with `Content-Type: application/manifest+json` and a JSON body containing at minimum `name`, `display`, `start_url`, and `icons`

#### Scenario: Manifest declares standalone display
- **WHEN** iOS Safari reads the manifest
- **THEN** `display` SHALL equal `"standalone"` so the app launches without browser chrome

#### Scenario: Manifest colors match dashboard theme
- **WHEN** iOS uses the manifest for splash/status bar
- **THEN** `background_color` and `theme_color` SHALL both equal `#22272e`

### Requirement: iOS PWA meta tags in HTML head
The dashboard HTML `<head>` SHALL include the following meta tags:
- `<meta name="apple-mobile-web-app-capable" content="yes">`
- `<meta name="apple-mobile-web-app-status-bar-style" content="black-translucent">`
- `<meta name="apple-mobile-web-app-title" content="Vacuum">`
- `<meta name="theme-color" content="#22272e">`
- `<link rel="manifest" href="/manifest.json">`
- `<link rel="apple-touch-icon" href="/icons/apple-touch-icon.png">`

#### Scenario: HTML head contains PWA meta tags
- **WHEN** a browser loads the dashboard root `/`
- **THEN** the HTML response SHALL contain `apple-mobile-web-app-capable` and `rel="manifest"` in the `<head>`

#### Scenario: Viewport supports safe-area insets
- **WHEN** iOS renders the page in standalone mode
- **THEN** the `<meta name="viewport">` SHALL include `viewport-fit=cover` so `env(safe-area-inset-*)` values are non-zero

### Requirement: Safe-area inset padding in standalone mode
The dashboard body SHALL apply `env(safe-area-inset-*)` padding so content is not obscured by the iPhone notch or home indicator when running in standalone mode.

#### Scenario: Content avoids notch in standalone mode
- **WHEN** the dashboard runs as an installed PWA on an iPhone with a notch
- **THEN** the body padding SHALL be at least `env(safe-area-inset-top)` on top and `env(safe-area-inset-bottom)` on bottom, preserving the existing minimum of `20px`
