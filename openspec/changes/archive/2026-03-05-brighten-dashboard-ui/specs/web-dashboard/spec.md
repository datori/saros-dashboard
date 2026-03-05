## MODIFIED Requirements

### Requirement: Dashboard visual theme
The dashboard SHALL use the GitHub Dark Dimmed color palette for its base background, surface, border, text, and muted colors.

#### Scenario: Background color
- **WHEN** the dashboard page is loaded
- **THEN** the page background SHALL be `#22272e`

#### Scenario: Card/surface color
- **WHEN** any card or panel is rendered
- **THEN** its background SHALL be `#2d333b`

#### Scenario: Border color
- **WHEN** any card border or divider is rendered
- **THEN** its color SHALL be `#444c56`

#### Scenario: Primary text color
- **WHEN** primary text is rendered
- **THEN** its color SHALL be `#adbac7`

#### Scenario: Muted text color
- **WHEN** secondary/muted text is rendered
- **THEN** its color SHALL be `#768390`

#### Scenario: Badge backgrounds are proportionally lifted
- **WHEN** a status badge is rendered
- **THEN** green badge background SHALL be `#1e3a2a`, yellow `#3d2c00`, red `#3d1515`, blue `#243d5e`
