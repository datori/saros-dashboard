## ADDED Requirements

### Requirement: Apple touch icon endpoint
The dashboard server SHALL serve an icon at `GET /icons/apple-touch-icon.png`. The icon SHALL be an SVG (served with `Content-Type: image/svg+xml`) depicting the vacuum brand mark on a dark background matching `#22272e`.

#### Scenario: Icon is reachable
- **WHEN** a client requests `GET /icons/apple-touch-icon.png`
- **THEN** the server returns HTTP 200 with a valid SVG or PNG image

#### Scenario: Icon background matches theme
- **WHEN** iOS displays the icon on the home screen
- **THEN** the icon background color SHALL be `#22272e` (matching `--bg` in the dashboard theme)

#### Scenario: Icon is legible at small sizes
- **WHEN** rendered at 60×60 points (120×120 retina) on the iOS home screen
- **THEN** the icon mark SHALL be clearly visible against the dark background

### Requirement: Manifest references icon
The Web App Manifest `icons` array SHALL reference `/icons/apple-touch-icon.png` with size `192x192` and type `image/png` (or `image/svg+xml` if SVG is served).

#### Scenario: Manifest icon URL is consistent with served route
- **WHEN** the manifest is parsed
- **THEN** the `src` value in the `icons` array SHALL resolve to the same route that returns HTTP 200
