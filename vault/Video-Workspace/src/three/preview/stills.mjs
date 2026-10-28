// Render several stills of the 3D test compositions from ONE bundle and ONE browser (the CLI re-bundles per still).
// Run from vault/Video-Workspace:  node src/three/preview/stills.mjs CrystalTest:0,120,240 DeskTest:300 [--scale=0.5] [--out=out/three] [--suffix=-x] [--props={"bloom":false}]
// Prints ms per still (browser already warm after the first).
import path from 'node:path';
import fs from 'node:fs';
import { bundle } from '@remotion/bundler';
import { openBrowser, renderStill, selectComposition } from '@remotion/renderer';

const args = process.argv.slice(2);
const opt = Object.fromEntries(args.filter((a) => a.startsWith('--')).map((a) => a.slice(2).split('=')));
const jobs = args.filter((a) => !a.startsWith('--')).flatMap((a) => {
  const [id, frames] = a.split(':');
  return frames.split(',').map((f) => ({ id, frame: Number(f) }));
});
const outDir = path.resolve(opt.out ?? 'out/three');
const scale = Number(opt.scale ?? 1);
const suffix = opt.suffix ?? '';
const inputProps = opt.props ? JSON.parse(opt.props) : {};
fs.mkdirSync(outDir, { recursive: true });

const chromiumOptions = { gl: 'angle' };
const t0 = Date.now();
const serveUrl = await bundle({ entryPoint: path.resolve('src/three/preview/index.ts'), publicDir: path.resolve('public') });
console.log(`bundle ${Date.now() - t0} ms`);
const browser = await openBrowser('chrome', { chromiumOptions });
const comps = new Map();
for (const { id, frame } of jobs) {
  if (!comps.has(id)) comps.set(id, await selectComposition({ serveUrl, id, inputProps, puppeteerInstance: browser, chromiumOptions }));
  const output = path.join(outDir, `${id.replace(/Test$/, '').toLowerCase()}-f${String(frame).padStart(3, '0')}${suffix}.png`);
  const s = Date.now();
  await renderStill({ composition: comps.get(id), serveUrl, output, frame, scale, inputProps, puppeteerInstance: browser, chromiumOptions, overwrite: true });
  console.log(`${path.relative(process.cwd(), output)}  ${Date.now() - s} ms`);
}
await browser.close({ silent: true });
