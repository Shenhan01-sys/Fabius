// Capture the Fabius web app (web/) for the video's product frames: desktop + mobile, full-page JPEGs.
//   1. cd web && npm run build && npx next start -p 3100
//   2. (optional) a local gate: tools/x402_sinyal.py --local on :8050 — pages that read the Railway gate get it instead
//   3. node scripts/capture-web.mjs [--base http://127.0.0.1:3100] [--gate http://127.0.0.1:8050] [--only home,bot]
// Needs playwright-core (npm i -D playwright-core) and a Chromium (PLAYWRIGHT_CHROMIUM or the Playwright default).
import { chromium } from 'playwright-core';
import { mkdirSync } from 'node:fs';

const args = process.argv.slice(2);
const opt = (k, d) => { const i = args.indexOf(`--${k}`); return i >= 0 ? args[i + 1] : d; };
const BASE = opt('base', 'http://127.0.0.1:3100');
const GATE = opt('gate', '');
const ONLY = opt('only', '').split(',').filter(Boolean);
const OUT = opt('out', 'public/ui');
mkdirSync(OUT, { recursive: true });

const PAGES = [
  { id: 'home', path: '/', desktop: true, mobile: true },
  { id: 'bot', path: '/bot/B1-TREND', desktop: true, mobile: true },
  { id: 'buy', path: '/buy', desktop: true, mobile: true },
  { id: 'buybot', path: '/buy/B2-RS', desktop: false, mobile: true },
  { id: 'analysts', path: '/analysts', desktop: true, mobile: true },
  { id: 'desk', path: '/desk', desktop: true, mobile: false },
  { id: 'submit', path: '/submit', desktop: true, mobile: false },
  { id: 'submitagent', path: '/submit-agent', desktop: true, mobile: false },
  { id: 'verify', path: '/verify', desktop: true, mobile: true },
  { id: 'status', path: '/status', desktop: true, mobile: false },
].filter((p) => !ONLY.length || ONLY.includes(p.id));

const browser = await chromium.launch({
  executablePath: process.env.PLAYWRIGHT_CHROMIUM || undefined,
  args: ['--use-angle=swiftshader', '--enable-unsafe-swiftshader', '--ignore-gpu-blocklist'],
});

async function shoot(p, mobile) {
  const ctx = await browser.newContext(mobile
    ? { viewport: { width: 390, height: 844 }, deviceScaleFactor: 2, isMobile: true, hasTouch: true, userAgent: 'Mozilla/5.0 (iPhone; CPU iPhone OS 18_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/18.0 Mobile/15E148 Safari/604.1' }
    : { viewport: { width: 1440, height: 900 }, deviceScaleFactor: 1.5 });
  if (GATE) await ctx.route('https://fabius-x402-production.up.railway.app/**', async (route) => {
    const req = route.request();
    const u = new URL(req.url());
    const cors = { 'access-control-allow-origin': '*', 'access-control-allow-headers': '*', 'access-control-allow-methods': 'GET,POST,OPTIONS', 'access-control-expose-headers': '*' };
    if (req.method() === 'OPTIONS') return route.fulfill({ status: 204, headers: cors });
    try {
      const r = await fetch(GATE + u.pathname + u.search, { method: req.method(), headers: { 'content-type': 'application/json' }, body: req.method() === 'POST' ? req.postData() ?? undefined : undefined });
      const body = Buffer.from(await r.arrayBuffer());
      await route.fulfill({ status: r.status, headers: { ...cors, 'content-type': r.headers.get('content-type') ?? 'application/json' }, body });
    } catch { await route.abort(); }
  });
  const page = await ctx.newPage();
  page.on('pageerror', () => {});
  await page.goto(BASE + p.path, { waitUntil: 'networkidle', timeout: 60000 }).catch(() => {});
  await page.waitForTimeout(2500);
  // walk down the page so in-view animations run, then back to the top
  const hgt = await page.evaluate(() => document.documentElement.scrollHeight);
  for (let y = 0; y < hgt; y += 500) { await page.evaluate((yy) => window.scrollTo(0, yy), y); await page.waitForTimeout(220); }
  await page.evaluate(() => window.scrollTo(0, 0));
  await page.waitForTimeout(1500);
  const file = `${OUT}/${p.id}-${mobile ? 'm' : 'd'}.jpg`;
  await page.screenshot({ path: file, fullPage: true, type: 'jpeg', quality: 86 });
  const view = `${OUT}/${p.id}-${mobile ? 'm' : 'd'}-top.jpg`;
  await page.screenshot({ path: view, fullPage: false, type: 'jpeg', quality: 88 });
  console.log(file, hgt);
  await ctx.close();
}

for (const p of PAGES) {
  if (p.desktop) await shoot(p, false);
  if (p.mobile) await shoot(p, true);
}
await browser.close();
