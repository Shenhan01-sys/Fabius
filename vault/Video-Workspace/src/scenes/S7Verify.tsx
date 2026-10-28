// VERIFY - "Then check it yourself. Pick any bot, any day. Fabius rebuilds the signal from public data and the chain.
// No key. No gas."
// The real /verify page (capture verify: B2-RS, the page's default day, a live check against BNB Chain): the bot chip
// and the day lift out as they are picked, the four stations lift into an arc and tick one by one, then the verdict
// card comes forward ("Verified": every signal of that day was committed before the outcome and recomputes exactly).
import React from 'react';
import { AbsoluteFill } from 'remotion';
import { At, camAt, Space, withDrift } from '../cam/space';
import { LavWorld } from '../fx/world';
import { GlowBlob } from '../fx/fx';
import { BrowserWindow, Clip, geom, PageCrop } from '../ui/browser';
import { Cursor } from '../ui/cursor';
import { Check, Pill } from '../ui/bits';
import { rgba } from '../lib/palette';
import { label } from '../lib/fonts';
import { bump, clamp, ease, lerp, prog } from '../lib/util';
import { at, line } from '../lib/vo';
import { capBox, capCursor } from '../data/captures';
import { pw } from './S2Reveal';
import type { SceneProps } from '../timeline';

const WW = 1200, WH = 790;
const G = geom(WW, WH);
const STATIONS = ['stationTick', 'stationCommitted', 'stationOpened', 'stationRecomputed'] as const;

export const S7Verify: React.FC<SceneProps> = ({ t, t0, t1 }) => {
  const v1 = line('ver1'), v2 = line('ver2'), v3 = line('ver3');
  const tPick = at('ver2', 'Pick'), tDay = at('ver2', 'day'), tReb = at('ver2', 'rebuilds'), tChain = at('ver2', 'chain');
  const tKey = at('ver3', 'key'), tGas = at('ver3', 'gas');
  // the capture, re-timed: chip click on "Pick", Verify click just before "rebuilds", the stations settle by "chain"
  // stations complete on the page between its marks station-1-done (307) and stations-final (365); hold there so the lifted
  // verdict (cropped from verdict-hold, 516) is the only big 'Verified' on screen
  const f = pw(t, [[t0, 20], [tPick + 0.25, 120], [tDay + 0.3, 165], [tReb - 0.1, 220], [tReb + 0.3, 250], [tChain, 365], [t1, 372]]);
  const cur = capCursor('verify', f);
  const stK = (i: number) => prog(t, tReb + 0.3 + i * 0.62, tReb + 0.85 + i * 0.62, ease.cine);
  const verdict = prog(t, v3.start - 0.25, v3.start + 0.45, ease.cine);
  const cam = withDrift(camAt([
    { t: t0, x: 0, y: 0, z: -140, rx: 6, ry: -10 },
    { t: v1.end, x: 0, y: 0, z: -90, rx: 4, ry: -6, ez: ease.inOutCubic },
    { t: tPick + 0.4, x: -260, y: 60, z: 230, rx: 6, ry: 6, ez: ease.inOutQuart },
    { t: tDay + 0.5, x: 240, y: 70, z: 240, rx: 6, ry: -8, ez: ease.inOutCubic },
    { t: tReb + 0.6, x: 0, y: 40, z: 40, rx: 8, ry: 0, ez: ease.inOutQuart },
    { t: v3.start, x: 0, y: 20, z: 60, rx: 6, ry: 4, ez: ease.inOutCubic },
    { t: t1, x: 0, y: 40, z: 180, rx: 4, ry: -4, ez: ease.inOutCubic },
  ], t), t, 0.7, 71);
  const chip = capBox('verify', 'chipB2', 125), date = capBox('verify', 'date', 165);
  const chipK = prog(t, tPick + 0.2, tPick + 0.6, ease.cine) * (1 - prog(t, tReb, tReb + 0.4));
  const dateK = prog(t, tDay - 0.05, tDay + 0.4, ease.cine) * (1 - prog(t, tReb, tReb + 0.4));
  const vb = capBox('verify', 'verdict', 516);
  return (
    <AbsoluteFill>
      <LavWorld t={t} cam={cam} seed={7} />
      <Space cam={cam} perspective={1650}>
        <At x={0} y={0} z={0}>
          <BrowserWindow w={WW} h={WH} url="fabius-one.vercel.app/verify" dim={0.45 * Math.max(stK(0), verdict)} sweep={prog(t, t0 + 0.2, t0 + 1.3)}>
            <Clip name="verify" f={f} />
            <Cursor t={t} x={cur.x * G.s} y={cur.y * G.s} clicks={[tPick + 0.2, tReb - 0.12]} scale={0.9} opacity={1 - prog(t, tReb + 0.3, tReb + 0.6)} />
          </BrowserWindow>
        </At>
        {/* the picks lift out */}
        {[[chip, 125, chipK], [date, 165, dateK]].map(([b, fr, k], i) => {
          const bb = b as ReturnType<typeof capBox>;
          const c = G.centre(bb);
          return (
            <At key={i} x={c.x} y={c.y - 30 * (k as number)} z={180 * (k as number)}>
              <div style={{ opacity: clamp((k as number) * 3) }}>
                <PageCrop b={bb} s={G.s * 1.25} clip={{ name: 'verify', f: fr as number }} radius={20} lift={k as number} glow={0.9 * (k as number)} pad={4} />
              </div>
            </At>
          );
        })}
        {/* the four stations, in an arc */}
        {STATIONS.map((key, i) => {
          const k = stK(i) * (1 - prog(t, v3.start - 0.3, v3.start + 0.2));
          if (k <= 0) return null;
          const b = capBox('verify', key, 365);
          const home = G.centre(b);
          const x = lerp(home.x, -495 + i * 330, k), y = lerp(home.y, -120, k), z = lerp(0, 260 + 40 * Math.abs(1.5 - i), k);
          return (
            <At key={key} x={x} y={y} z={z} ry={lerp(0, (1.5 - i) * 9, k)}>
              <div style={{ opacity: clamp(k * 2.5) }}>
                <PageCrop b={b} s={G.s} clip={{ name: 'verify', f: 365 }} radius={18} lift={k} glow={0.5 * k + 0.6 * bump(t, tReb + 0.85 + i * 0.62, 0.3)} pad={2} />
                <div style={{ position: 'absolute', left: (b.w * G.s) / 2 - 30, top: -(b.h * G.s) / 2 - 22, transform: `scale(${0.6 + 0.4 * stK(i)})` }}><Check s={46} k={prog(t, tReb + 0.7 + i * 0.62, tReb + 1.0 + i * 0.62)} /></div>
              </div>
            </At>
          );
        })}
        {/* the verdict */}
        <At x={0} y={-40} z={300 * verdict}>
          <div style={{ opacity: clamp(verdict * 2.5) }}>
            <PageCrop b={vb} s={G.s * 1.05} clip={{ name: 'verify', f: 516 }} radius={22} lift={verdict} glow={0.7 * verdict} sweep={prog(t, v3.start + 0.2, v3.start + 1.1)} />
          </div>
        </At>
        {[['No key', tKey], ['No gas', tGas]].map(([txt, a], i) => {
          const k = prog(t, (a as number) - 0.05, (a as number) + 0.3, ease.outBack);
          return (
            <At key={i} x={-140 + i * 300} y={230} z={340}>
              <div style={{ position: 'absolute', left: -120, top: -36, opacity: clamp(k * 2), transform: `scale(${0.7 + 0.3 * k})` }}>
                <Pill size={34} fill icon={<Check s={34} col="#ffffff" tick={'#6e4bff'} k={k} />}>{txt as string}</Pill>
              </div>
            </At>
          );
        })}
      </Space>
      <GlowBlob x={960} y={520} r={520} col="violet2" a={0.25 * verdict} />
      <div style={{ position: 'absolute', left: 80, top: 66, ...label(14, 700), color: rgba('ink', 0.55), opacity: prog(t, tReb, tReb + 0.4) * (1 - verdict) }}>
        live check · B2-RS · reads the public ledger + BNB Chain
      </div>
    </AbsoluteFill>
  );
};
