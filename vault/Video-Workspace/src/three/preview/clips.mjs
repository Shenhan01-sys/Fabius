// Render short mp4 clips of the 3D test compositions from one bundle and report render time per frame (bundling excluded).
// Run from vault/Video-Workspace:  node src/three/preview/clips.mjs CrystalTest:200-319 DeskTest:180-299 [--scale=0.5] [--concurrency=4]
import path from 'node:path';
import fs from 'node:fs';
import { bundle } from '@remotion/bundler';
import { openBrowser, renderMedia, selectComposition } from '@remotion/renderer';

const args = process.argv.slice(2);
const opt = Object.fromEntries(args.filter((a) => a.startsWith('--')).map((a) => a.slice(2).split('=')));
const jobs = args.filter((a) => !a.startsWith('--')).map((a) => {
  const [id, range] = a.split(':');
  const [from, to] = range.split('-').map(Number);
  return { id, from, to };
});
const scale = Number(opt.scale ?? 0.5);
const concurrency = opt.concurrency ? Number(opt.concurrency) : null;
const outDir = path.resolve(opt.out ?? 'out/three');
fs.mkdirSync(outDir, { recursive: true });
const chromiumOptions = { gl: 'angle' };
const serveUrl = await bundle({ entryPoint: path.resolve('src/three/preview/index.ts'), publicDir: path.resolve('public') });
const browser = await openBrowser('chrome', { chromiumOptions });
for (const { id, from, to } of jobs) {
  const composition = await selectComposition({ serveUrl, id, puppeteerInstance: browser, chromiumOptions });
  const out = path.join(outDir, `${id.replace(/Test$/, '').toLowerCase()}-${from}-${to}${scale === 1 ? '' : `-x${scale}`}.mp4`);
  const n = to - from + 1;
  const s = Date.now();
  await renderMedia({
    composition,
    serveUrl,
    codec: 'h264',
    crf: 18,
    outputLocation: out,
    frameRange: [from, to],
    scale,
    concurrency,
    imageFormat: 'jpeg',
    jpegQuality: 92,
    puppeteerInstance: browser,
    chromiumOptions,
    overwrite: true,
  });
  const ms = Date.now() - s;
  console.log(`${path.relative(process.cwd(), out)}  ${n} frames  ${ms} ms total  ${(ms / n).toFixed(1)} ms/frame (wall, concurrency ${concurrency ?? 'default'}, scale ${scale})`);
}
await browser.close({ silent: true });
