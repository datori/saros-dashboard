## Context

The dashboard uses a CSS custom property palette defined once in a `:root {}` block inside `dashboard.py`'s inline `<style>` tag. All UI elements reference these variables. Changing the 9 color values is the entire implementation.

## Goals / Non-Goals

**Goals:**
- Lift base background from near-black to GitHub Dark Dimmed levels
- Proportionally adjust badge backgrounds so they remain visually balanced

**Non-Goals:**
- Changing accent, action, or semantic colors (blue, purple, green, yellow, red)
- Any layout, structural, or behavioral changes
- Theming system or runtime theme switching

## Decisions

**Direct value replacement over a theming layer**: This is a one-time cosmetic adjustment. Adding a runtime theme switcher would be over-engineering for a personal tool.

**GitHub Dark Dimmed as target**: Well-tested, widely recognized palette. Specific values:

| Variable    | Before    | After     |
|-------------|-----------|-----------|
| `--bg`      | `#0f1117` | `#22272e` |
| `--surface` | `#1a1d27` | `#2d333b` |
| `--border`  | `#2a2d3a` | `#444c56` |
| `--text`    | `#e2e8f0` | `#adbac7` |
| `--muted`   | `#64748b` | `#768390` |

Badge backgrounds lifted proportionally (these are hardcoded, not variables):

| Selector      | Before    | After     |
|---------------|-----------|-----------|
| `.badge-green` bg | `#14532d` | `#1e3a2a` |
| `.badge-yellow` bg | `#422006` | `#3d2c00` |
| `.badge-red` bg | `#450a0a` | `#3d1515` |
| `.badge-blue` bg | `#1e3a5f` | `#243d5e` |

## Risks / Trade-offs

- **Text contrast**: `--text` shifts from `#e2e8f0` (very light) to `#adbac7` (slightly dimmer). Both pass WCAG AA on their respective backgrounds. No contrast regression.
- **Rollback**: Trivially reversible — revert the 9 color values.
