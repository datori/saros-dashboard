---
name: screenshots
description: Generate polished UI screenshots of the vacuum dashboard and update the README. Use when the user wants to refresh screenshots, update the README hero images, or capture the current state of the UI.
metadata:
  author: local
  version: "1.0"
---

Generate fresh screenshots of the Vacuum Dashboard and update the README.

## Steps

**1. Build the frontend if the dist is stale**

Check whether `frontend/dist/index.html` exists. If it does not, or if the user says UI changes were made, rebuild first:

```bash
cd frontend && npm run build
```

**2. Run the screenshot script**

```bash
node scripts/screenshots.mjs
```

This serves the built frontend, mocks all `/api/*` routes with realistic data, captures three views, and writes polished PNG files to `docs/screenshots/`:
- `desktop.png` — full 1400px cockpit layout
- `schedule.png` — Info tab (Gantt cleaning schedule + history)
- `mobile.png` — 390px mobile view

If the command fails, report the error clearly and stop.

**3. Display the screenshots to the user**

Read and display all three output files in this order so the user can see the results inline:
1. `docs/screenshots/desktop.png`
2. `docs/screenshots/schedule.png`
3. `docs/screenshots/mobile.png`

**4. Ensure the README has a prominent screenshots section**

Read `README.md` and check that it contains all three screenshots in a well-structured section. The canonical layout is:

```markdown
![Vacuum Dashboard](docs/screenshots/desktop.png)
```
as a hero image immediately after the badge line, and then after the Features list:

```markdown
| Schedule (Gantt) | Mobile |
|---|---|
| ![Schedule](docs/screenshots/schedule.png) | ![Mobile](docs/screenshots/mobile.png) |
```

If either block is missing or the paths are wrong, update `README.md` to match this layout. Do not change anything else in the README.

**5. Confirm**

Tell the user which files were written and confirm the README is up to date. Keep it brief.
