// Tangkapan layar produksi untuk deck Demo Day (DKV §6). Jalankan dari root repo: node vault/14-Deck-Demo-Day/aset/capture-deck.mjs <folder-keluaran>
// Butuh Google Chrome (macOS) + playwright-core di vault/Video-Workspace/node_modules.
import pw from '../../Video-Workspace/node_modules/playwright-core/index.js';
const OUT = process.argv[2]; const B = 'https://fabius-one.vercel.app';
const br = await pw.chromium.launch({ executablePath: '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome', args: ['--use-gl=angle', '--enable-webgl', '--ignore-gpu-blocklist'] });
const ctx = await br.newContext({ viewport: { width: 1920, height: 1080 }, deviceScaleFactor: 2 });
const p = await ctx.newPage();
const shot = async (name, opts = {}) => { await p.screenshot({ path: `${OUT}/${name}.png`, ...opts }); console.log('ok', name); };
const go = async (path, wait = 4000) => { await p.goto(B + path, { waitUntil: 'networkidle', timeout: 60000 }).catch(() => {}); await p.waitForTimeout(wait); };
await go('/', 7000); await shot('01-landing-hero');
await go('/tour', 9000); await shot('02-tour-atas');
await p.mouse.wheel(0, 700); await p.waitForTimeout(1500); await shot('03-tour-langkah-1-3');
await p.mouse.wheel(0, 900); await p.waitForTimeout(1500); await shot('04-tour-langkah-4-5-verified');
await go('/break', 3000); await shot('05-break-atas');
await p.getByRole('button', { name: 'Try all four' }).click(); await p.waitForTimeout(12000);
await p.mouse.wheel(0, 650); await p.waitForTimeout(1000); await shot('06-break-empat-ditolak');
await go('/verify?bot=B2-RS&bar=2026-10-05', 9000); await shot('07-verify-b2rs-atas');
await p.mouse.wheel(0, 800); await p.waitForTimeout(1200); await shot('08-verify-b2rs-stasiun');
await go('/desk', 8000); await shot('09-desk');
await go('/bot/B2-RS', 5000); await shot('10-bot-b2rs');
await br.close();
