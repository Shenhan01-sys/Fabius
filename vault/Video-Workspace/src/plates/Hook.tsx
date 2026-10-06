// 01 HOOK — "Over two thousand years ago, Rome kept losing to Hannibal in open battle. / So one general did
// something radical: he refused the battles Hannibal wanted. / His name was Fabius."
// The spark arrives, becomes the pen, rules a time axis, crosses out three Roman defeats — Rome's glass blocks
// topple, one per battle — rings the one general who refused battle (his block stays standing), and writes his name.
import React from 'react';
import { AbsoluteFill } from 'remotion';
import type { PlateProps } from '../timeline';
import { C, rgba } from '../lib/palette';
import { F } from '../lib/fonts';
import { lineOf, wordOf } from '../lib/lyrics';
import { clamp, ease, env, prog, pulse, shake } from '../lib/util';
import { Ambient, Camera, type CamKey } from '../components/camera';
import { arcPts, GraphPaper, NightBg, handwriting, Ink, Karaoke, makePen, seg, Spark, span, Sputter, Typer, W, H, type Poly } from '../components/kit';
import { At, Block, Box, Stage } from '../components/solid';

const L0 = lineOf('Over two thousand');
const L1 = lineOf('So one general');
const L2 = lineOf('His name was');
const w0 = (q: string) => wordOf(L0, q), w1 = (q: string) => wordOf(L1, q), w2 = (q: string) => wordOf(L2, q);

const AX_Y = 760, AX0 = 190, AX1 = 1730;
const BATTLES = [
  { name: 'TICINUS', year: '218 BC', x: 330, at: w0('kept').start },
  { name: 'TREBIA', year: '218 BC', x: 590, at: w0('losing').start },
  { name: 'TRASIMENE', year: '217 BC', x: 880, at: w0('Hannibal').start },
];
const FAB_X = 1170;

/** The time the axis pen (inOutQuart over [t0, t1]) passes x. */
function passTime(x: number, t0: number, t1: number) {
  const k = clamp((x - AX0) / (AX1 - AX0));
  let lo = 0, hi = 1;
  for (let i = 0; i < 24; i++) {
    const m = (lo + hi) / 2;
    if (ease.inOutQuart(m) < k) lo = m; else hi = m;
  }
  return t0 + (t1 - t0) * lo;
}

/** Rome's block at a battle: stands on the axis, is struck as the cross is drawn, and topples. */
const Legion: React.FC<{ t: number; x: number; tIn: number; tHit: number; i: number }> = ({ t, x, tIn, tHit, i }) => {
  const s = 74;
  const a = prog(t, tIn, tIn + 0.35, ease.outBack);
  if (a <= 0) return null;
  const fall = prog(t, tHit + 0.12, tHit + 0.55, ease.inQuad);
  const settle = Math.sin(clamp((t - tHit - 0.55) / 0.25) * Math.PI) * 6 * (t > tHit + 0.55 ? 1 : 0);
  const red = prog(t, tHit, tHit + 0.15);
  const dir = 1; void i;
  return (
    <At x={x - W / 2 + dir * s / 2} y={0}>
      <At rz={dir * (88 * fall - settle)}>
        <At x={-dir * s / 2} y={-s / 2 - 1} s={a}>
          <Box w={s} h={s} d={s} radius={3} edge={red > 0 ? `rgba(255,90,110,${0.5 + 0.4 * red})` : 'rgba(255,255,255,0.5)'} edgeW={1.6} alpha={1 - 0.45 * fall}
            faces={{ front: `linear-gradient(135deg, rgba(255,255,255,${0.2 - 0.08 * red}), rgba(255,90,110,${0.3 * red}))`, left: `rgba(236,232,250,${0.08 + 0.05 * red})`, right: `rgba(255,90,110,${0.06 + 0.2 * red})`, top: `rgba(255,255,255,${0.26 - 0.1 * red})`, bottom: 'rgba(255,255,255,0.04)', back: 'rgba(255,255,255,0.05)' }}
            glow={red > 0 ? `0 0 ${30 * pulse(t, tHit, 0.12)}px rgba(255,90,110,0.8)` : undefined} />
        </At>
      </At>
    </At>
  );
};

export default function Hook({ t, end }: PlateProps) {
  const tAxis0 = w0('Over').start + 0.12, tAxis1 = w0('ago').end + 0.15;
  const tRing = w1('refused').start;
  const tName = w2('Fabius').start;
  const out1 = L1.start - 0.3; // L0 text leaves
  const out2 = L2.start - 0.35; // L1 text + diagram dim

  // the pen's strokes
  const axis: Poly = seg(AX0, AX_Y, AX1, AX_Y);
  const crosses = BATTLES.flatMap((b) => [
    { pts: seg(b.x - 15, AX_Y - 15, b.x + 15, AX_Y + 15), t0: b.at, t1: b.at + 0.09 },
    { pts: seg(b.x + 15, AX_Y - 15, b.x - 15, AX_Y + 15), t0: b.at + 0.11, t1: b.at + 0.2 },
  ]);
  const ring = arcPts(FAB_X, AX_Y, 30, -Math.PI / 2, Math.PI * 1.5);
  const dashT0 = tRing + 0.45, dashT1 = w1('wanted').end + 0.2;
  const intro = arcPts(W / 2, H / 2, 62, -Math.PI / 2, Math.PI * 1.5);
  const name = handwriting('Fabius', 'script', 470, W / 2, 700, { t0: tName - 0.02, t1: tName + 1.05 }, 'center');
  const pen = makePen(
    [
      { pts: intro, t0: 0.35, t1: 0.95 },
      { pts: axis, t0: tAxis0, t1: tAxis1, ez: ease.inOutQuart },
      ...crosses,
      { pts: ring, t0: tRing, t1: tRing + 0.4 },
      { pts: seg(FAB_X + 30, AX_Y, AX1, AX_Y), t0: dashT0, t1: dashT1, ez: ease.linear },
    ],
    { from: { x: W / 2, y: H / 2 - 62 } },
  );
  const head = (tb: number) => (tb < 0.35 ? null : tb >= name.start && tb <= name.end ? name.head(tb) : tb < out2 + 0.2 ? pen(tb) : null);
  const h = head(t);

  // the arrival: a dot that becomes the pen
  const dotA = prog(t, 0.1, 0.45, ease.outBack);
  const sh = shake(t, 9 * pulse(t, tRing, 0.06) + 6 * pulse(t, w1('refused').start + 0.02, 0.05));
  const dimDiagram = 1 - 0.85 * prog(t, out2, out2 + 0.4);

  const cam: CamKey[] = [
    { t: 0, s: 1.35 },
    { t: 2.7, s: 1.0, ez: ease.inOutQuart },
    { t: 5.4, s: 1.04, x: 20 },
    { t: 8.45, s: 1.07, rx: 5, x: 60 },
    { t: 8.62, s: 1.11, rx: 5, x: 70, ez: ease.outQuart },
    { t: 9.5, s: 1.06, rx: 4, x: 60 },
    { t: 10.7, s: 1.02, rx: 0, x: 0, y: 0 },
    { t: 13.4, s: 1.15, y: 30 },
  ];

  return (
    <AbsoluteFill>
      <NightBg glow={prog(t, 0.2, 2.5)} />
      <Camera t={t} keys={cam} depth={0.35}><Ambient t={t} strength={prog(t, 0.6, 3)} /></Camera>
      <Camera t={t} keys={cam}>
        <AbsoluteFill style={{ transform: `translate(${sh[0]}px, ${sh[1]}px)` }}>
          <GraphPaper reveal={{ x: W / 2, y: H / 2, r: 2400 * prog(t, 0.6, 2.8, ease.inOutCubic) }} />

          {/* the arrival dot inside its ring */}
          {t < tAxis0 + 0.4 && (
            <svg width={W} height={H} style={{ position: 'absolute', inset: 0, opacity: 1 - prog(t, tAxis0, tAxis0 + 0.4) }}>
              <circle cx={W / 2} cy={H / 2} r={9 * dotA} fill={C.violet2} />
              <Ink t={t} t0={0.35} t1={0.95} pts={intro} col={rgba('mist', 0.55)} w={1.4} />
            </svg>
          )}

          {/* the time axis and its marks */}
          <svg width={W} height={H} style={{ position: 'absolute', inset: 0, opacity: dimDiagram }}>
            <Ink t={t} t0={tAxis0} t1={tAxis1} pts={axis} col={rgba('lav', 0.55)} w={1.5} ez={ease.inOutQuart} />
            {Array.from({ length: 25 }, (_, i) => {
              const x = AX0 + ((AX1 - AX0) * i) / 24;
              const tk = tAxis0 + (tAxis1 - tAxis0) * ease.inOutQuart(clamp(i / 24)) * 0.98;
              const big = i % 6 === 0;
              return <Ink key={i} t={t} t0={tk} t1={tk + 0.05} pts={seg(x, AX_Y + 6, x, AX_Y + (big ? 20 : 12))} col={rgba('lav', 0.35)} w={1} hot={false} />;
            })}
            {crosses.map((c, i) => <Ink key={i} t={t} t0={c.t0} t1={c.t1} pts={c.pts} col={C.gap} w={3.2} ez={ease.outQuad} />)}
            <Ink t={t} t0={tRing} t1={tRing + 0.4} pts={ring} col={C.lav} w={2.4} />
            <Ink t={t} t0={dashT0} t1={dashT1} pts={seg(FAB_X + 30, AX_Y, AX1, AX_Y)} col={rgba('violet2', 0.95)} w={2.6} dash="12 9" ez={ease.linear} />
          </svg>
          {/* Rome's blocks topple, battle by battle; Fabius's block stays standing */}
          <Stage cam={{ rx: 12 }} perspective={1500} cy={AX_Y} opacity={dimDiagram}>
            {BATTLES.map((b, i) => <Legion key={b.name} t={t} x={b.x} i={i} tIn={passTime(b.x, tAxis0, tAxis1) - 0.1} tHit={b.at} />)}
            {t >= tRing - 0.1 && (
              <At x={FAB_X - W / 2} y={-84 - 6 * Math.sin(t * 2.2)} rx={-8} ry={(t - tRing) * 30 + 30} s={prog(t, tRing - 0.1, tRing + 0.3, ease.outBack)}>
                <Block s={84} state="sealed" />
              </At>
            )}
          </Stage>
          <div style={{ position: 'absolute', inset: 0, opacity: dimDiagram }}>
            {BATTLES.map((b) => (
              <div key={b.name} style={{ position: 'absolute', left: b.x - 120, width: 240, top: AX_Y + 34, textAlign: 'center' }}>
                <Typer t={t} t0={b.at + 0.12} text={b.name} size={15} weight={600} col={rgba('lav', 0.85)} spacing={2.5} caret={false} />
                <br />
                <Typer t={t} t0={b.at + 0.25} text={`${b.year} · LOST`} size={12.5} col={rgba('gap', 0.95)} spacing={2} caret={false} />
              </div>
            ))}
            <div style={{ position: 'absolute', left: FAB_X - 150, width: 300, top: AX_Y + 34, textAlign: 'center' }}>
              <Typer t={t} t0={tRing + 0.18} text="FABIUS" size={15} weight={600} col={C.lav} spacing={2.5} caret={false} />
              <br />
              <Typer t={t} t0={tRing + 0.32} text="217 BC · NO BATTLE" size={12.5} col={rgba('violet2', 1)} spacing={2} caret={false} />
            </div>
            <div style={{ position: 'absolute', left: (FAB_X + AX1) / 2 - 220, width: 440, top: AX_Y - 44, textAlign: 'center' }}>
              <Typer t={t} t0={dashT0 + 0.2} text="shadow · harass · delay" size={14} col={rgba('mist', 0.85)} spacing={1} caret={false} style={{ fontStyle: 'italic' }} />
            </div>
          </div>

          <svg width={W} height={H} style={{ position: 'absolute', inset: 0 }}>{name.draw(t, C.lav, 3.4)}</svg>
          <div style={{ position: 'absolute', left: 0, right: 0, top: 812, textAlign: 'center' }}>
            <Typer t={t} t0={name.end - 0.1} text="QUINTUS FABIUS MAXIMUS · “CUNCTATOR” — THE DELAYER" size={16} spacing={3.5} col={rgba('lav', 0.7)} weight={500} />
          </div>

          {h && <Sputter t={t} headAt={head} rate={45} seed={3} from={0.35} />}
          {h && <Spark x={h.x} y={h.y} t={t} scale={0.85} />}
          {t < tAxis0 + 0.3 && <Spark x={W / 2} y={H / 2} t={t} scale={0.55 + 0.35 * dotA} intensity={dotA * (1 - prog(t, tAxis0 - 0.1, tAxis0 + 0.3))} />}
        </AbsoluteFill>
      </Camera>
      <Camera t={t} keys={[]} drift={0.5}>
          {/* L0 — the setting */}
          <div style={{ position: 'absolute', left: 160, right: 160, top: 250, opacity: 1 - prog(t, out1, out1 + 0.3), transform: `translateY(${-50 * prog(t, out1, out1 + 0.3, ease.inCubic)}px)` }}>
            <Karaoke t={t} words={span(L0, 0, 4)} st={{ font: F.serif(104, 500), outline: rgba('mist', 0.35) }} align="center" />
            <div style={{ height: 26 }} />
            <Karaoke t={t} words={span(L0, 5, 9)} st={{ font: F.archivo(84, 850, 100), pop: 0.04 }} align="center" />
            <div style={{ height: 8 }} />
            <Karaoke t={t} words={span(L0, 10)} st={{ font: F.archivo(84, 850, 100), pop: 0.04 }} align="center" />
          </div>

          {/* L1 — the radical idea */}
          <div style={{ position: 'absolute', left: 140, right: 140, top: 165, opacity: env(t, L1.start - 0.4, out2 + 0.35, 0.3, 0.35), transform: `translateY(${-40 * prog(t, out2, out2 + 0.35, ease.inCubic)}px)` }}>
            <Karaoke t={t} words={span(L1, 0, 5)} st={{ font: F.serif(88, 500), outline: rgba('mist', 0.35) }} align="center" />
            <div style={{ height: 6 }} />
            <Karaoke t={t} words={span(L1, 6, 7)} st={{ font: F.archivo(178, 900, 125), hot: 'violet', done: 'violet', pop: 0.06, ant: 0.25 }} align="center" lineHeight={1.02} />
            <div style={{ height: 4 }} />
            <Karaoke t={t} words={span(L1, 8)} st={{ font: F.serif(78, 500), outline: rgba('mist', 0.35) }} align="center" />
          </div>

          {/* L2 — the name */}
          <div style={{ position: 'absolute', left: 0, right: 0, top: 236, textAlign: 'center', opacity: env(t, L2.start - 0.2, end + 1, 0.25, 0.3) }}>
            <Karaoke t={t} words={span(L2, 0, 2)} st={{ font: F.mono(30, 400), outline: rgba('mist', 0.4), done: 'mist', hot: 'lav', upper: true, gap: 0.6 }} align="center" style={{ letterSpacing: 6 }} />
          </div>
      </Camera>
    </AbsoluteFill>
  );
}
