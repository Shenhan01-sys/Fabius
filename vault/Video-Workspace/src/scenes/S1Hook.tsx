// HOOK - "Every trading bot has a perfect track record. The catch? It's always written after the market moves."
// Night world. Glossy "profit screenshot" cards of made-up bots drift toward the camera in depth; on "after the
// market moves" the camera settles on one card: its post time slides AFTER the price spike, the stamp flips to
// "posted after the move", and every card loses its shine and dissolves softly into motes (no crash, no shatter).
import React from 'react';
import { AbsoluteFill } from 'remotion';
import { At, camAt, Space, withDrift } from '../cam/space';
import { NightWorld } from '../fx/world';
import { Dissolve, GlowBlob } from '../fx/fx';
import { Headline } from '../ui/text';
import { C, rgba } from '../lib/palette';
import { archivo, inter, label, mono } from '../lib/fonts';
import { clamp, ease, hash, prog } from '../lib/util';
import { at, line } from '../lib/vo';
import type { SceneProps } from '../timeline';

const BOTS = [
  { n: 'AlphaBot', h: '@alphabot', p: '+312%', c: 'called it' },
  { n: 'MoonSignals', h: '@moonsignals', p: '+88%', c: 'this week, easy' },
  { n: 'TrendWizard', h: '@trendwiz', p: '+146%', c: 'told you so' },
  { n: 'PumpPilot', h: '@pumppilot', p: '+57%', c: 'another win' },
  { n: 'SignalKing', h: '@signalking', p: '+203%', c: '12/12 wins' },
  { n: 'AlphaAlerts', h: '@alphaalerts', p: '+71%', c: 'perfect entry' },
  { n: 'ChartGenius', h: '@chartgenius', p: '+129%', c: 'nailed it' },
  { n: 'QuantKid', h: '@quantkid', p: '+94%', c: 'never wrong' },
];

/** A price path that spikes at `spike` (0..1 along x). */
const path = (seed: number, spike = 0.55) => {
  const pts: [number, number][] = [];
  for (let i = 0; i <= 40; i++) {
    const x = i / 40;
    const base = 0.25 * x + 0.06 * Math.sin(i * 0.9 + seed * 3) * (1 - x);
    const jump = x > spike ? 0.55 * ease.outCubic(clamp((x - spike) / 0.12)) : 0;
    pts.push([x, 0.15 + base + jump + 0.03 * (hash(i, seed) - 0.5)]);
  }
  return pts;
};

const ProfitCard: React.FC<{ i: number; t: number; tw: number; dull: number; focus?: number }> = ({ i, t, tw, dull, focus = 0 }) => {
  const b = BOTS[i % BOTS.length]!;
  const w = 430, h = 280;
  const pts = path(i);
  const d = 'M' + pts.map(([x, y]) => `${(20 + x * (w - 40)).toFixed(1)} ${(h - 30 - y * 120).toFixed(1)}`).join('L');
  // post time marker: looks "on time" first, then slides right of the spike (posted after the move)
  const postX = 0.42 + 0.4 * tw;
  const sat = 1 - 0.85 * dull;
  return (
    <div style={{ position: 'absolute', left: -w / 2, top: -h / 2, width: w, height: h, borderRadius: 22, overflow: 'hidden', background: `linear-gradient(160deg, rgba(255,255,255,${0.97 - 0.5 * dull}), rgba(240,236,255,${0.92 - 0.55 * dull}))`, border: `1px solid rgba(255,255,255,${0.9 - 0.6 * dull})`, boxShadow: `0 30px 80px -20px rgba(110,75,255,${0.55 * (1 - dull)}), 0 0 ${40 * focus}px ${rgba('violet2', 0.5 * focus)}`, filter: dull > 0.01 ? `saturate(${sat}) brightness(${1 - 0.25 * dull})` : undefined }}>
      <div style={{ position: 'absolute', left: 20, top: 18, display: 'flex', alignItems: 'center', gap: 10 }}>
        <div style={{ width: 38, height: 38, borderRadius: '50%', background: `linear-gradient(135deg, hsl(${(i * 47) % 360},70%,62%), hsl(${(i * 47 + 40) % 360},70%,48%))`, display: 'flex', alignItems: 'center', justifyContent: 'center', ...archivo(18, 800), color: '#fff' }}>{b.n[0]}</div>
        <div>
          <div style={{ ...inter(17, 700), color: C.ink }}>{b.n} <span style={{ color: '#1d9bf0' }}>●</span></div>
          <div style={{ ...inter(13, 500), color: C.mist }}>{b.h}</div>
        </div>
      </div>
      <div style={{ position: 'absolute', right: 20, top: 16, ...archivo(42, 800, 92), color: '#12a06a' }}>{b.p}</div>
      <div style={{ position: 'absolute', right: 22, top: 66, ...inter(14, 600), color: rgba('ink', 0.6) }}>{b.c} ↗</div>
      <svg width={w} height={h} style={{ position: 'absolute', inset: 0 }}>
        <defs>
          <linearGradient id={`pg${i}`} x1="0" y1="0" x2="0" y2="1"><stop offset="0" stopColor="#12a06a" stopOpacity="0.28" /><stop offset="1" stopColor="#12a06a" stopOpacity="0" /></linearGradient>
        </defs>
        <path d={`${d} L ${w - 20} ${h - 30} L 20 ${h - 30} Z`} fill={`url(#pg${i})`} />
        <path d={d} fill="none" stroke="#12a06a" strokeWidth={3} strokeLinejoin="round" />
        <line x1={20 + postX * (w - 40)} x2={20 + postX * (w - 40)} y1={96} y2={h - 26} stroke={tw > 0.5 ? C.gap : rgba('ink', 0.35)} strokeWidth={2} strokeDasharray="5 5" />
      </svg>
      <div style={{ position: 'absolute', left: 20 + postX * (w - 40), bottom: 8, transform: 'translateX(-50%)', ...label(11, 700), color: tw > 0.5 ? C.gap : rgba('ink', 0.55), whiteSpace: 'nowrap', background: 'rgba(255,255,255,0.85)', padding: '2px 8px', borderRadius: 999 }}>
        {tw > 0.5 ? 'posted after the move' : 'posted 10:42'}
      </div>
    </div>
  );
};

export const S1Hook: React.FC<SceneProps> = ({ t, t0, t1 }) => {
  const l1 = line('hook1'), l2 = line('hook2');
  const tAfter = at('hook2', 'after');
  const tMoves = at('hook2', 'moves');
  const cam = withDrift(camAt([
    { t: t0, z: -260, rx: 7, ry: -10, x: 0, y: 0 },
    { t: l1.end, z: 40, rx: 4, ry: -4, ez: ease.inOutCubic },
    { t: tAfter - 0.2, z: 210, rx: 2, ry: 6, x: 230, y: -40, ez: ease.inOutQuart },
    { t: t1, z: 330, rx: 0, ry: 9, x: 250, y: -46, ez: ease.inOutCubic },
  ], t), t, 1, 11);
  const tw = prog(t, tAfter - 0.25, tAfter + 0.35, ease.inOutCubic); // timestamps flip
  const dull = prog(t, tMoves - 0.1, tMoves + 0.6, ease.inOutCubic);
  const gone = prog(t, l2.end - 0.15, t1 + 0.1, ease.inCubic);
  const cards = Array.from({ length: 14 }, (_, i) => {
    const zr = hash(i, 5);
    return {
      i, x: -350 + hash(i, 1) * 1900, y: -560 + hash(i, 2) * 900,
      z: -1500 + 1500 * zr + (t - t0) * (60 + 40 * hash(i, 3)), ry: (hash(i, 4) - 0.5) * 30, rx: (hash(i, 6) - 0.5) * 16,
    };
  });
  const hero = { x: 250, y: -40, z: 60 };
  return (
    <AbsoluteFill>
      <NightWorld t={t} cam={cam} grid={0.35} />
      <Space cam={cam} perspective={1500}>
        {cards.map((c) => (
          <At key={c.i} x={c.x} y={c.y} z={c.z} rx={c.rx} ry={c.ry}>
            <div style={{ opacity: (1 - gone) * clamp((c.z + 1600) / 500), filter: `blur(${(Math.min(9, Math.abs(c.z - 40) / 160)).toFixed(1)}px)` }}>
              <ProfitCard i={c.i} t={t} tw={tw} dull={dull} />
            </div>
          </At>
        ))}
        <At x={hero.x} y={hero.y} z={hero.z} ry={-6}>
          <div style={{ opacity: 1 - gone, transform: `scale(${1 + 0.06 * prog(t, tAfter - 0.4, tAfter + 0.4)})` }}>
            <ProfitCard i={0} t={t} tw={tw} dull={dull} focus={1 - dull} />
          </div>
        </At>
      </Space>
      <Dissolve t={t} t0={tMoves + 0.15} len={1.3} x={560} y={300} w={800} h={480} n={140} col="violet2" />
      <GlowBlob x={960} y={540} r={700} col="violet" a={0.12} />
      <AbsoluteFill style={{ background: 'radial-gradient(ellipse 60% 55% at 12% 88%, rgba(15,11,38,0.88) 0%, rgba(15,11,38,0.55) 45%, rgba(15,11,38,0) 75%)' }} />
      <AbsoluteFill style={{ justifyContent: 'flex-end', alignItems: 'flex-start', padding: '0 0 210px 130px' }}>
        <Headline t={t} col="#f2efff" size={92} out={l1.end + 0.1}
          segs={[
            { text: 'Every trading bot has a', at: l1.words[0]!.start, voice: 'calm', size: 58 },
            { text: 'perfect track record.', at: at('hook1', 'perfect'), voice: 'accent', col: C.violet2, br: true },
          ]} />
      </AbsoluteFill>
      <AbsoluteFill style={{ justifyContent: 'flex-end', alignItems: 'flex-start', padding: '0 0 210px 130px' }}>
        <Headline t={t} col="#f2efff" size={92} out={l2.end + 0.25}
          segs={[
            { text: 'The catch? Written', at: l2.words[0]!.start, voice: 'calm', size: 58 },
            { text: 'after', at: tAfter, voice: 'accent', col: C.gap, br: true },
            { text: 'the market moves.', at: at('hook2', 'market'), voice: 'heavy', col: '#f2efff' },
          ]} />
      </AbsoluteFill>
    </AbsoluteFill>
  );
};
