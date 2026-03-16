/**
 * Automated screenshot generator for the Vacuum Dashboard.
 *
 * Usage:
 *   node scripts/screenshots.mjs
 *
 * Requires:
 *   - Built frontend at frontend/dist/ (run `npm run build` in frontend/)
 *   - Playwright + Chromium: npx playwright install chromium
 *   - `serve` package: npx serve (auto-downloaded by npx)
 *
 * Output: docs/screenshots/{desktop,schedule,mobile}.png
 */

import { chromium } from 'playwright';
import { spawn } from 'child_process';
import { writeFileSync, mkdirSync, readFileSync } from 'fs';
import { fileURLToPath } from 'url';
import { dirname, join } from 'path';

const __dirname = dirname(fileURLToPath(import.meta.url));
const ROOT = join(__dirname, '..');
const DIST = join(ROOT, 'frontend', 'dist');
const OUT  = join(ROOT, 'docs', 'screenshots');
const PORT = 7722;

// ─── Mock API data ──────────────────────────────────────────────────────────
// Realistic-looking data — no real device needed.

const NOW = new Date();
const daysAgo = (d) => new Date(NOW - d * 86400000).toISOString();

const MOCK = {
  '/api/status': {
    state: 'charging_complete',
    battery: 100,
    in_dock: true,
    error_code: 0,
  },

  '/api/window': {
    active: false,
    remaining_minutes: 0,
    current_clean: null,
  },

  '/api/rooms': [
    { id: 1, name: 'Living Room' },
    { id: 2, name: 'Kitchen' },
    { id: 3, name: 'Bedroom' },
    { id: 4, name: 'Office' },
    { id: 5, name: 'Hallway' },
    { id: 6, name: 'Bathroom' },
  ],

  '/api/consumables': {
    main_brush_pct: 78,
    side_brush_pct: 64,
    filter_pct: 51,
    sensor_pct: 3,
  },

  '/api/settings': {
    fan_speed: 'BALANCED',
    mop_mode: 'STANDARD',
    water_flow: 'MEDIUM',
  },

  '/api/routines': [
    'Morning Clean',
    'Quick Sweep',
    'Deep Clean',
    'Evening Mop',
  ],

  '/api/history': [
    { start_time: daysAgo(0.5), duration_seconds: 2340, area_m2: 68.4, complete: true,  start_type: 'app',      clean_type: 'all_zone',    finish_reason: 'finished_cleaning' },
    { start_time: daysAgo(1.8), duration_seconds: 1890, area_m2: 52.1, complete: true,  start_type: 'schedule', clean_type: 'select_zone', finish_reason: 'finished_cleaning' },
    { start_time: daysAgo(3.2), duration_seconds: 2480, area_m2: 71.0, complete: true,  start_type: 'routines', clean_type: 'all_zone',    finish_reason: 'finished_cleaning' },
    { start_time: daysAgo(5.1), duration_seconds: 960,  area_m2: 28.3, complete: false, start_type: 'app',      clean_type: 'select_zone', finish_reason: 'manual_interrupt'  },
    { start_time: daysAgo(6.4), duration_seconds: 2310, area_m2: 67.9, complete: true,  start_type: 'schedule', clean_type: 'all_zone',    finish_reason: 'finished_cleaning' },
  ],

  '/api/schedule': [
    {
      segment_id: 1, name: 'Living Room',
      last_vacuumed: daysAgo(3), last_mopped: daysAgo(7),
      vacuum_days: 4, mop_days: 14,
      vacuum_overdue_ratio: 0.75, mop_overdue_ratio: 0.50,
      priority_weight: 1.5, default_duration_sec: 900, notes: null,
    },
    {
      segment_id: 2, name: 'Kitchen',
      last_vacuumed: daysAgo(1), last_mopped: daysAgo(2),
      vacuum_days: 2, mop_days: 3,
      vacuum_overdue_ratio: 0.50, mop_overdue_ratio: 0.67,
      priority_weight: 2.0, default_duration_sec: 600, notes: 'High traffic',
    },
    {
      segment_id: 3, name: 'Bedroom',
      last_vacuumed: daysAgo(8), last_mopped: null,
      vacuum_days: 7, mop_days: null,
      vacuum_overdue_ratio: 1.14, mop_overdue_ratio: null,
      priority_weight: 1.0, default_duration_sec: 720, notes: null,
    },
    {
      segment_id: 4, name: 'Office',
      last_vacuumed: daysAgo(5), last_mopped: null,
      vacuum_days: 7, mop_days: null,
      vacuum_overdue_ratio: 0.71, mop_overdue_ratio: null,
      priority_weight: 1.0, default_duration_sec: 480, notes: 'Cables on floor',
    },
    {
      segment_id: 5, name: 'Hallway',
      last_vacuumed: daysAgo(2), last_mopped: daysAgo(9),
      vacuum_days: 3, mop_days: 10,
      vacuum_overdue_ratio: 0.67, mop_overdue_ratio: 0.90,
      priority_weight: 1.2, default_duration_sec: 300, notes: null,
    },
    {
      segment_id: 6, name: 'Bathroom',
      last_vacuumed: null, last_mopped: null,
      vacuum_days: 7, mop_days: 7,
      vacuum_overdue_ratio: null, mop_overdue_ratio: null,
      priority_weight: 1.0, default_duration_sec: 360, notes: null,
    },
  ],

  '/api/health': {
    ok: true,
    last_contact_seconds_ago: 8,
  },

  '/api/triggers': [
    { name: 'evening', budget_min: 45, mode: 'vacuum', notes: 'After dinner' },
    { name: 'morning', budget_min: 30, mode: 'vacuum', notes: 'Weekday mornings' },
    { name: 'deep',    budget_min: 90, mode: 'mop',    notes: 'Weekend deep clean' },
  ],
};

// ─── Server ─────────────────────────────────────────────────────────────────

function startServer() {
  return new Promise((resolve, reject) => {
    const proc = spawn('npx', ['serve', DIST, '-l', String(PORT), '--no-clipboard'], {
      stdio: ['ignore', 'pipe', 'pipe'],
    });
    proc.stdout.on('data', (d) => {
      if (d.toString().includes('Accepting connections')) resolve(proc);
    });
    proc.stderr.on('data', () => {}); // suppress noise
    proc.on('error', reject);
    // Fallback — give it 5s to start
    setTimeout(() => resolve(proc), 5000);
  });
}

// ─── Route mocking ──────────────────────────────────────────────────────────

async function mockApiRoutes(page) {
  await page.route('**/api/**', (route) => {
    const url = new URL(route.request().url());
    const path = url.pathname;

    // Strip trailing slash for lookup
    const key = path.replace(/\/$/, '');
    const data = MOCK[key];

    if (data !== undefined) {
      route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify(data),
      });
    } else {
      // Unknown endpoint — return empty 200 to avoid errors
      route.fulfill({ status: 200, contentType: 'application/json', body: '{}' });
    }
  });
}

// ─── Polish wrapper ──────────────────────────────────────────────────────────
// Takes a raw screenshot Buffer, renders it inside a styled HTML page,
// then screenshots that for a polished result with background + shadow.

async function polish(browser, rawPngPath, label) {
  const rawB64 = readFileSync(rawPngPath).toString('base64');

  const html = `<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<style>
  * { margin: 0; padding: 0; box-sizing: border-box; }
  body {
    background: linear-gradient(135deg, #0d1117 0%, #161b22 50%, #0d1117 100%);
    display: flex;
    align-items: center;
    justify-content: center;
    padding: 48px;
    min-height: 100vh;
  }
  .frame {
    border-radius: 10px;
    overflow: hidden;
    box-shadow:
      0 0 0 1px rgba(255,255,255,0.08),
      0 8px 32px rgba(0,0,0,0.6),
      0 32px 80px rgba(0,0,0,0.4);
    max-width: 100%;
  }
  img { display: block; max-width: 100%; }
  .label {
    position: fixed;
    bottom: 16px;
    right: 20px;
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
    font-size: 11px;
    color: rgba(255,255,255,0.2);
    letter-spacing: 0.5px;
  }
</style>
</head>
<body>
  <div class="frame">
    <img src="data:image/png;base64,${rawB64}" />
  </div>
  <span class="label">${label}</span>
</body>
</html>`;

  const page = await browser.newPage();
  await page.setContent(html, { waitUntil: 'networkidle' });

  // Size wrapper to content
  const box = await page.locator('.frame').boundingBox();
  await page.setViewportSize({
    width: Math.round(box.x * 2 + box.width + 96),
    height: Math.round(box.y * 2 + box.height + 96),
  });

  const buf = await page.screenshot({ fullPage: true });
  await page.close();
  return buf;
}

// ─── Main ────────────────────────────────────────────────────────────────────

async function main() {
  console.log('Starting static server…');
  const server = await startServer();

  const browser = await chromium.launch();
  mkdirSync(OUT, { recursive: true });

  try {
    // ── Screenshot 1: Desktop full view ──
    console.log('Capturing desktop view…');
    {
      const page = await browser.newPage();
      await page.setViewportSize({ width: 1400, height: 900 });
      await mockApiRoutes(page);
      await page.goto(`http://localhost:${PORT}`, { waitUntil: 'networkidle' });
      // Wait for panels to load
      await page.waitForSelector('[class*="Panel"]', { timeout: 5000 }).catch(() => {});
      await page.waitForTimeout(800);

      // Make sure desktop right-tab is on "Rooms" (default)
      const rawPath = join(OUT, '_raw_desktop.png');
      await page.screenshot({ path: rawPath, fullPage: false });
      await page.close();

      const polished = await polish(browser, rawPath, 'Vacuum Dashboard · Desktop');
      writeFileSync(join(OUT, 'desktop.png'), polished);
      console.log('  ✓ desktop.png');
    }

    // ── Screenshot 2: Schedule (Gantt) view ──
    console.log('Capturing schedule view…');
    {
      const page = await browser.newPage();
      await page.setViewportSize({ width: 1400, height: 820 });
      await mockApiRoutes(page);
      await page.goto(`http://localhost:${PORT}`, { waitUntil: 'networkidle' });
      await page.waitForTimeout(600);

      // Click the "Info" right-tab to show schedule + history
      const infoTab = page.locator('[role="tab"]').filter({ hasText: 'Info' });
      await infoTab.click();
      await page.waitForTimeout(400);

      const rawPath = join(OUT, '_raw_schedule.png');
      await page.screenshot({ path: rawPath, fullPage: false });
      await page.close();

      const polished = await polish(browser, rawPath, 'Vacuum Dashboard · Schedule');
      writeFileSync(join(OUT, 'schedule.png'), polished);
      console.log('  ✓ schedule.png');
    }

    // ── Screenshot 3: Mobile view ──
    console.log('Capturing mobile view…');
    {
      const page = await browser.newPage();
      await page.setViewportSize({ width: 390, height: 844 });
      await mockApiRoutes(page);
      await page.goto(`http://localhost:${PORT}`, { waitUntil: 'networkidle' });
      await page.waitForTimeout(600);

      const rawPath = join(OUT, '_raw_mobile.png');
      await page.screenshot({ path: rawPath, fullPage: false });
      await page.close();

      const polished = await polish(browser, rawPath, 'Vacuum Dashboard · Mobile');
      writeFileSync(join(OUT, 'mobile.png'), polished);
      console.log('  ✓ mobile.png');
    }

  } finally {
    await browser.close();
    server.kill();
  }

  console.log(`\nScreenshots saved to docs/screenshots/`);
  console.log('  desktop.png  — full cockpit layout');
  console.log('  schedule.png — Gantt cleaning schedule');
  console.log('  mobile.png   — mobile view');
}

main().catch((e) => { console.error(e); process.exit(1); });
