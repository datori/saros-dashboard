## Context

The dashboard is a single `_HTML` string in `dashboard.py` — no build step, no npm, no bundler. All JS is vanilla. Shoelace is the only mainstream component library that ships as ES module web components loadable directly from a CDN with no compilation, making it uniquely suited to this constraint.

Current state: native `<button>`, `<select>`, `<input type=radio>`, hand-rolled progress bars and badges. These work but look dated and are hard to theme consistently.

## Goals / Non-Goals

**Goals:**
- Polished, dark-theme-native controls for buttons, selects, badges, progress bars, tabs, and the scope toggle
- Zero build-step: everything loads from CDN at page load
- Dark theme via Shoelace's built-in `sl-theme-dark` class — no manual token overriding required
- JS logic unchanged: `sl-select.value`, `sl-radio-group.value` work identically to native equivalents

**Non-Goals:**
- Full design system adoption — only the components that map cleanly to existing elements
- Removing all native HTML — `<input type=number>`, `<input type=range>`, `<input type=checkbox>`, `<input type=text>` stay native (Shoelace equivalents add complexity without clear visual gain in this context)
- Replacing modal dialogs with `sl-dialog` (separate concern)

## Decisions

### D1 — Shoelace version: pin to 2.x latest minor via CDN

Use `https://cdn.jsdelivr.net/npm/@shoelace-style/shoelace@2/cdn/themes/dark.css` and the autoloader at `@2/cdn/shoelace-autoloader.js`. The `@2` tag tracks latest 2.x — stable API, no breaking changes within major. Pinning to an exact version (e.g. `@2.20.1`) reduces CDN cache churn but requires manual bumps; `@2` is acceptable for a personal dashboard.

**Alternative**: Use unpkg.com — jsDelivr has better CDN performance globally and explicit versioning support.

### D2 — Theme: use Shoelace dark theme class, map onto existing CSS variables

Add `class="sl-theme-dark"` to `<body>`. Shoelace's dark theme sets its own `--sl-*` tokens. Our existing `--bg`, `--surface`, `--accent` etc. are separate and still used for layout/panels. The two systems coexist without conflict — Shoelace components use `--sl-*`; panels/layout use our custom variables.

**Alternative**: Override every `--sl-*` token to match our palette exactly. Too much maintenance; the dark theme is close enough and users won't notice minor token differences between components.

### D3 — Right-pane tab bar: replace with sl-tab-group

`<sl-tab-group>` manages tabs declaratively. Each `<sl-tab slot="nav">` + `<sl-tab-panel>` pair replaces the current `#right-tab-bar` buttons + CSS `[data-right-tab]` visibility rules. `sl-tab-group` emits `sl-tab-show` event on switch — replace `onclick="activateRightTab()"` with an event listener.

Session storage persistence: listen to `sl-tab-show`, write `activeRightTab` to sessionStorage. On init, call `tabGroup.show(stored)`.

**Alternative**: Keep custom tab bar, only swap the button elements to `<sl-button>`. Leaves CSS visibility logic in place — simpler but wastes the best Shoelace component.

### D4 — sl-select value access: unchanged

`<sl-select>` exposes `.value` as a string property, identical to native `<select>`. No JS changes needed for reading values. Event is `sl-change` instead of `change` — update `onchange=` attributes to use JS event listeners or `sl-change` attribute handlers. Simplest: keep inline `onchange` but change attribute name to `@sl-change` ... actually Shoelace doesn't support `@` syntax in vanilla HTML. Use `addEventListener('sl-change', ...)` in the init block, or just replace `onchange=` with the `sl-change` event handler string: Shoelace fires `sl-change` which bubbles — `onsl-change` is NOT a valid HTML attribute. Must wire via addEventListener.

Cleanest approach: add a small init block at bottom of script that wires all `sl-select` `sl-change` events to their handler functions. The handlers themselves are unchanged.

### D5 — sl-button: map variants to existing semantic colours

| Current class | sl-button variant | Additional |
|---|---|---|
| `btn-primary` | `variant="primary"` | — |
| `btn-danger` | `variant="danger"` | — |
| `btn-warning` | `variant="warning"` | — |
| `btn-neutral` | `variant="default"` | — |
| `btn-purple` | `variant="primary"` | `style="--sl-color-primary-600: var(--accent2)"` or custom class |
| `btn-sm` | `size="small"` | — |

### D6 — Keep native inputs for: number, range, checkbox, text

These are inside panels and modals where Shoelace equivalents (`sl-input`, `sl-range`) would require more wiring for no meaningful visual improvement in the dark context. Scope is buttons, selects, badges, progress bars, tabs, scope toggle.

## Risks / Trade-offs

**[Risk] CDN availability** → Shoelace loads from jsDelivr. If CDN is down, components don't render. Mitigation: dashboard is a personal local tool; CDN downtime is an acceptable risk. Could self-host later if needed.

**[Risk] sl-tab-group init timing** → Custom elements upgrade asynchronously. If JS runs `tabGroup.show(stored)` before the element upgrades, it silently fails. Mitigation: call `customElements.whenDefined('sl-tab-group').then(...)` before restoring tab state.

**[Risk] sl-select value on page load** → `sl-select` renders asynchronously; setting `.value` before upgrade is a no-op. `loadSettings()` already calls `populateSelect()` after fetch — this should be fine since the fetch takes >0ms. If flickers occur, wrap in `customElements.whenDefined('sl-select')`.

**[Risk] applyCleanMode sets .value directly** → Currently sets `el.value = 'OFF'` etc. on native selects. On `sl-select`, setting `.value` programmatically works but requires the element to be defined. Same mitigation as above — negligible in practice.

## Migration Plan

Pure frontend change within `_HTML`. No API changes. Rollback = git revert. CDN resources are cached by browser after first load.
