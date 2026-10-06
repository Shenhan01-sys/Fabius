// Stills while editing (the kit's `render.ts stills`): bundle once, render frames at given SECONDS.
//   node scripts/stills.mjs --t 1.2,5.5,11.9 [--out out/wip] [--only hook] [--scale 0.5] [--sheet]
// --sheet tiles the stills into one contact sheet (needs ffmpeg on PATH).
import { bundle } from '@remotion/bundler';
import { renderStill, selectComposition } from '@remotion/renderer';
import { execFileSync } from 'node:child_process';
import { mkdirSync } from 'node:fs';
import path from 'node:path';

const args = process.argv.slice(2);
const opt = (k, d) => {
  const i = args.indexOf(`--${k}`);
  return i >= 0 ? args[i + 1] : d;
};
const times = opt('t', '0').split(',').map(Number);
const out = opt('out', 'out/wip');
const only = opt('only', '');
const scale = Number(opt('scale', '0.5'));
mkdirSync(out, { recursive: true });

const serveUrl = await bundle({ entryPoint: path.resolve('src/index.ts') });
const inputProps = { audio: '', only, hud: true };
const browserExecutable = process.env.REMOTION_BROWSER_EXECUTABLE || null;
const composition = await selectComposition({ serveUrl, id: 'Fabius', inputProps, browserExecutable, chromiumOptions: { gl: 'swangle' } });
const files = [];
for (const s of times) {
  const frame = Math.min(composition.durationInFrames - 1, Math.round(s * composition.fps));
  const file = path.join(out, `t${s.toFixed(2).padStart(7, '0')}.png`);
  await renderStill({ composition, serveUrl, frame, output: file, inputProps, scale, browserExecutable, chromiumOptions: { gl: 'swangle' } });
  files.push(file);
  console.log(file);
}
if (args.includes('--sheet') && files.length > 1) {
  const cols = Math.min(4, files.length);
  const sheet = path.join(out, 'sheet.png');
  execFileSync('ffmpeg', ['-v', 'error', '-y', ...files.flatMap((f) => ['-i', f]), '-filter_complex',
    `${files.map((_, i) => `[${i}:v]scale=640:-2[v${i}]`).join(';')};${files.map((_, i) => `[v${i}]`).join('')}xstack=inputs=${files.length}:layout=${files.map((_, i) => `${(i % cols) * 640}_${Math.floor(i / cols) * 360}`).join('|')}:fill=gray`,
    sheet]);
  console.log(sheet);
}
