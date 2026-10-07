// Viewport stills of the home page's sections (the page pins and scroll-animates some of them, so full-page
// captures don't show them as a visitor sees them). Writes public/ui/sec-*.jpg, and a run of frames through the
// pinned "From candle close to proof" section (sec-journey-NN.jpg) that the video plays as a flipbook.
//   node scripts/capture-sections.mjs [--base http://127.0.0.1:3100] [--out public/ui]
import { chromium } from 'playwright-core';
import { mkdirSync } from 'node:fs';

const args = process.argv.slice(2);
const opt = (k, d) => { const i = args.indexOf(`--${k}`); return i >= 0 ? args[i + 1] : d; };
const BASE = opt('base', 'http://127.0.0.1:3100');
const OUT = opt('out', 'public/ui');
mkdirSync(OUT, { recursive: true });

const browser = await chromium.launch({ executablePath: process.env.PLAYWRIGHT_CHROMIUM || undefined, args: ['--use-angle=swiftshader', '--enable-unsafe-swiftshader', '--ignore-gpu-blocklist'] });
const ctx = await browser.newContext({ viewport: { width: 1440, height: 900 }, deviceScaleFactor: 1.5 });
const page = await ctx.newPage();
page.on('pageerror', () => {});
await page.goto(BASE + '/', { waitUntil: 'networkidle', timeout: 60000 }).catch(() => {});
await page.waitForTimeout(3000);

// section tops by their headings
const tops = await page.evaluate(() => {
  const out = {};
  for (const h of document.querySelectorAll('h1,h2,h3')) {
    const txt = h.textContent.replace(/\s+/g, ' ').trim();
    let el = h;
    while (el && el.tagName !== 'SECTION' && el.parentElement) el = el.parentElement;
    const r = (el || h).getBoundingClientRect();
    out[txt.slice(0, 48)] = { top: Math.round(r.top + window.scrollY), h: Math.round(r.height) };
  }
  out.__height = document.documentElement.scrollHeight;
  return out;
});
console.log(JSON.stringify(tops, null, 1));

async function at(y, file, settle = 900) {
  await page.evaluate((yy) => window.scrollTo(0, yy), y);
  await page.waitForTimeout(settle);
  await page.screenshot({ path: `${OUT}/${file}`, type: 'jpeg', quality: 86 });
  console.log(file, y);
}
const find = (s) => Object.entries(tops).find(([k]) => k.toLowerCase().includes(s.toLowerCase()))?.[1];

const journey = find('candle close');
if (journey) {
  const n = 18, span = Math.max(1, journey.h - 900);
  for (let i = 0; i < n; i++) await at(journey.top + Math.round((span * i) / (n - 1)), `sec-journey-${String(i).padStart(2, '0')}.jpg`, 450);
}
for (const [key, file] of [['track record', 'sec-record.jpg'], ['ten slots', 'sec-book.jpg'], ['doors', 'sec-doors.jpg'], ['claim', 'sec-claims.jpg']]) {
  const s = find(key);
  if (s) await at(Math.max(0, s.top - 40), file, 1600);
}
await browser.close();
