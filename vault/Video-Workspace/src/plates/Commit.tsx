// 05 COMMIT — "Every bar, a bot's signals become one Merkle root, committed to chain 97. / Late commits are
// rejected. Every reveal is checked against the root. / Anyone can rerun the ledger. No keys needed."
// In 3D: the bar closes (a glass candle) and four real signals of B2-RS, bar 05 Oct (ids from ledger/paper) drop
// out of it as glass blocks; light climbs the Merkle tree into one root; a copy of the root is sealed into the
// newest block of chain 97 and the chain moves on. A late commit (bar + 12 h 00 m 01 s) hits the maxLag wall; one
// block opens and its proof path lights up to the root. Then the real `ledger verify` output and the /verify page.
import React from 'react';
import { AbsoluteFill } from 'remotion';
import type { PlateProps } from '../timeline';
import { C, rgba } from '../lib/palette';
import { F } from '../lib/fonts';
import { lineOf, wordOf } from '../lib/lyrics';
import { clamp, ease, env, lerp, prog, pulse, shake } from '../lib/util';
import { GraphPaper, Karaoke, Mono, NightBg, span, stampStyle, Typer } from '../components/kit';
import { Panel } from '../components/glass';
import { BrowserFrame, Cursor } from '../components/devices';
import { Ambient } from '../components/camera';
import { At, Block, Box, Plane, Stage, stageAt, type StageKey } from '../components/solid';

const L11 = lineOf('Every bar, a bot');
const L12 = lineOf('Late commits are');
const L13 = lineOf('Anyone can rerun');
const w11 = (q: string) => wordOf(L11, q), w12 = (q: string) => wordOf(L12, q), w13 = (q: string) => wordOf(L13, q);

// B2-RS, bar 2026-10-05: four signals (ledger/paper/B2-RS.jsonl signal_ids), committed +31,458 s after the close
const LEAVES = ['0x577fe86a', '0xa53dd515', '0x8e51788b', '0xb5685818'];
const ROOT = { x: -200, y: -150 };
const PAR = [{ x: -400, y: 20 }, { x: 0, y: 20 }];
const LEAF = [-500, -300, -100, 100].map((x) => ({ x, y: 190 }));
const CANDLE = { x: -720, y: 40 };
const CH = { x: 440, y: -140, z: 40, dx: 165, dz: -300 }; // the chain: front block, then older ones recede
const BS = 165; // chain block size
// the bars before this one (01–04 Oct), dimmer: a few candles of the same chart
const PREV = [{ x: -1120, y: 70, h: 120 }, { x: -1020, y: 30, h: 170 }, { x: -920, y: 60, h: 110 }, { x: -820, y: 20, h: 150 }];

const VERIFY = [
  '$ python -X utf8 -m engine.cli ledger verify',
  'B1-TREND.jsonl: SAH  tick 5 settle 0 gap 0',
  'B2-RS.jsonl: SAH  tick 2 settle 0 gap 0',
  'B3-CARRY.jsonl: SAH  tick 5 settle 3 gap 0',
  'B4-LISTING-FADE.jsonl: SAH  tick 2 settle 0 gap 0',
  'B5-CORE-RWA.jsonl: SAH  tick 2 settle 1 gap 0',
  'B6-BOUNCE.jsonl: SAH  tick 2 settle 2 gap 0',
];

/** An SVG drawn in world coordinates on the plane z (a big plane centred on the stage origin). */
const WorldSvg: React.FC<{ z?: number; children: React.ReactNode; opacity?: number }> = ({ z = 0, children, opacity = 1 }) => (
  <At z={z}>
    <Plane w={2600} h={1600} style={{ opacity }}>
      <svg width={2600} height={1600} viewBox="-1300 -800 2600 1600" style={{ overflow: 'visible' }}>{children}</svg>
    </Plane>
  </At>
);
const Label: React.FC<{ x: number; y: number; z?: number; w?: number; children: React.ReactNode; opacity?: number }> = ({ x, y, z = 0, w = 420, children, opacity = 1 }) => (
  <At x={x} y={y} z={z}><Plane w={w} h={40} style={{ textAlign: 'center', opacity }}>{children}</Plane></At>
);

export default function Commit({ t, start, end }: PlateProps) {
  const tBar = w11('bar').start;
  const tSig = w11('signals').start;
  const tBecome = w11('become').start, tRoot = w11('root').start;
  const tCommit = w11('committed').start, tChain = w11('97').start;
  const tLate = w12('Late').start, tRej = w12('rejected').start;
  const tReveal = w12('reveal').start, tCheck = w12('checked').start, tOk = w12('root').start + 0.1;
  const tTerm = L13.start - 0.45;
  const leave = prog(t, end - 0.2, end, ease.inCubic);
  const sh = shake(t, 7 * pulse(t, tRej + 0.05, 0.05) + 5 * pulse(t, tChain + 0.2, 0.05) + 3 * pulse(t, tBar, 0.05));

  const cam: StageKey[] = [
    { t: start - 0.3, rx: 14, ry: 26, z: 260, x: -820, y: 0, s: 1.05 },
    { t: tBar + 0.35, rx: 10, ry: 16, z: 120, x: -760, y: 10, s: 1.05, ez: ease.outCubic },
    { t: tSig + 0.5, rx: 8, ry: 8, z: -60, x: -380, y: 10, s: 1.12 },
    { t: tRoot + 0.2, rx: 7, ry: 2, z: -60, x: -200, y: -10, s: 1.15 },
    { t: tCommit + 0.35, rx: 8, ry: -6, z: -160, x: 60, y: -30, s: 1.1 },
    { t: tChain + 0.6, rx: 8, ry: -10, z: -140, x: 190, y: -30, s: 1.1 },
    { t: tRej + 0.3, rx: 7, ry: -14, z: -40, x: 330, y: -40, s: 1.12 },
    { t: tReveal + 0.25, rx: 7, ry: 6, z: -110, x: -120, y: 0, s: 1.12 },
    { t: tOk + 0.3, rx: 8, ry: 10, z: -150, x: -60, y: -10, s: 1.1 },
    { t: tTerm + 0.7, rx: 12, ry: 18, z: -900, x: -260, y: 40, s: 1 },
    { t: end + 0.4, rx: 12, ry: 20, z: -960, x: -280, y: 40, s: 1 },
  ];
  const c = stageAt(cam, t);
  const dim = 1 - 0.85 * prog(t, tTerm, tTerm + 0.6);

  // the bar closes
  const candle = prog(t, start + 0.05, tBar + 0.15, ease.outCubic);
  const closeFlash = pulse(t, tBar, 0.12);
  // signals drop out of the candle
  const leafAt = (i: number) => {
    const t0 = tSig - 0.05 + 0.09 * i;
    const k = prog(t, t0, t0 + 0.55, ease.inOutCubic);
    const L = LEAF[i]!;
    return { k, x: lerp(CANDLE.x, L.x, k), y: lerp(CANDLE.y - 40, L.y, k) - Math.sin(k * Math.PI) * 170, on: t >= t0 };
  };
  const parK = prog(t, tBecome + 0.25, tBecome + 0.5, ease.outBack);
  const rootK = prog(t, tRoot - 0.12, tRoot + 0.2, ease.outBack);
  const rootBurst = pulse(t, tRoot, 0.14);
  // a copy of the root flies into the newest block
  const fly = prog(t, tCommit - 0.05, tChain + 0.15, ease.inOutCubic);
  const sealed = t >= tChain + 0.15;
  const sealFlash = pulse(t, tChain + 0.15, 0.14);
  const advance = 0;
  // the late commit
  const lateIn = prog(t, tLate - 0.25, tRej + 0.02, ease.inQuad);
  const lateOut = prog(t, tRej + 0.02, tRej + 0.6, ease.outCubic);
  const wall = pulse(t, tRej + 0.02, 0.16);
  // the reveal
  const opened = t >= tReveal + 0.05;
  const pathK = prog(t, tCheck - 0.05, tCheck + 0.5, ease.inOutCubic);
  const okPulse = pulse(t, tOk, 0.18);

  const chainBlock = (k: number) => {
    // k = 0 is the newest block; once the chain advances every block slides back one slot and a fresh empty block arrives
    const slot = k + advance;
    const x = CH.x + CH.dx * slot, z = CH.z + CH.dz * slot;
    const isNew = k === 0;
    const state = isNew ? (sealed ? 'sealed' : 'empty') : 'sealed';
    return (
      <At key={`b${k}`} x={x} y={CH.y} z={z}>
        <Block s={BS} state={state} alpha={(isNew ? prog(t, tCommit - 0.6, tCommit - 0.2) : 0.95 - 0.12 * k) * clamp(1.6 - slot * 0.3)} label={isNew ? (sealed ? 'root ✓' : '') : 'block'} />
      </At>
    );
  };
  const link = (k: number) => {
    const slot = k + advance;
    const x = CH.x + CH.dx * (slot + 0.5), z = CH.z + CH.dz * (slot + 0.5);
    const len = Math.hypot(CH.dx, CH.dz) - BS;
    const ang = (Math.atan2(-CH.dz, CH.dx) * 180) / Math.PI;
    return (
      <At key={`l${k}`} x={x} y={CH.y} z={z} ry={ang}>
        <Box w={len} h={14} d={14} radius={7} alpha={clamp(1.4 - slot * 0.3) * prog(t, tCommit - 0.6, tCommit - 0.2)} faces={{ front: rgba('violet2', 0.55), top: rgba('violet2', 0.8), left: rgba('violet', 0.5), right: rgba('violet', 0.5), bottom: rgba('violet', 0.4), back: rgba('violet2', 0.5) }} />
      </At>
    );
  };
  const lateX = lerp(900, CH.x + 30, lateIn) + 300 * lateOut, lateY = lerp(120, CH.y + 10, lateIn) + 150 * lateOut;
  const lateZ = lerp(520, CH.z + BS / 2 + 40 + 5 + 46, lateIn) + 220 * lateOut;

  return (
    <AbsoluteFill style={{ opacity: 1 - leave }}>
      <NightBg glow={0.9} x={35} y={110} />
      <Ambient t={t} seed={5} n={5} dust={30} cubes={0} />
      <GraphPaper opacity={0.7} />

      <AbsoluteFill style={{ transform: `translate(${sh[0]}px, ${sh[1]}px)` }}>
        <Stage cam={c} t={t} drift={0.8} perspective={1800} cy={600} opacity={dim}>
          {/* the floor glow under the tree */}
          <At x={-200} y={330} z={0} rx={90}>
            <Plane w={1500} h={700} style={{ background: `radial-gradient(ellipse 50% 50% at 50% 50%, ${rgba('violet', 0.28)} 0%, ${rgba('violet', 0)} 70%)` }} />
          </At>

          {/* the tree's beams (world plane z = 0) */}
          <WorldSvg z={-4}>
            <defs>
              <filter id="beamGlow" x="-50%" y="-50%" width="200%" height="200%"><feGaussianBlur stdDeviation="5" /></filter>
            </defs>
            {LEAF.map((L, i) => {
              const P = PAR[i >> 1]!;
              const k = prog(t, tBecome + 0.04 * i, tBecome + 0.3 + 0.04 * i, ease.inOutCubic);
              const x1 = L.x, y1 = L.y - 50, x2 = P.x, y2 = P.y + 34;
              return <line key={`e${i}`} x1={x1} y1={y1} x2={lerp(x1, x2, k)} y2={lerp(y1, y2, k)} stroke={rgba('lav', 0.4)} strokeWidth={5} strokeLinecap="round" />;
            })}
            {PAR.map((P, i) => {
              const k = prog(t, tBecome + 0.35 + 0.06 * i, tBecome + 0.65 + 0.06 * i, ease.inOutCubic);
              const x1 = P.x, y1 = P.y - 34, x2 = ROOT.x, y2 = ROOT.y + 60;
              return <line key={`p${i}`} x1={x1} y1={y1} x2={lerp(x1, x2, k)} y2={lerp(y1, y2, k)} stroke={rgba('lav', 0.4)} strokeWidth={5} strokeLinecap="round" />;
            })}
            {/* energy climbing the tree: leaf -> parent -> root */}
            {LEAF.map((L, i) => {
              const P = PAR[i >> 1]!;
              const out: React.ReactNode[] = [];
              for (let j = 0; j < 3; j++) {
                const t0 = tBecome + 0.1 + 0.05 * i + 0.22 * j;
                const u = prog(t, t0, t0 + 0.75, ease.inOutCubic);
                if (u <= 0 || u >= 1) continue;
                const a = u < 0.5 ? u / 0.5 : (u - 0.5) / 0.5;
                const p0 = u < 0.5 ? { x: L.x, y: L.y - 50 } : { x: P.x, y: P.y - 34 };
                const p1 = u < 0.5 ? { x: P.x, y: P.y + 34 } : { x: ROOT.x, y: ROOT.y + 60 };
                const x = lerp(p0.x, p1.x, a), y = lerp(p0.y, p1.y, a);
                out.push(<circle key={`d${i}${j}`} cx={x} cy={y} r={9} fill={C.violet2} filter="url(#beamGlow)" />, <circle key={`c${i}${j}`} cx={x} cy={y} r={4.5} fill="#ffffff" />);
              }
              return <g key={`g${i}`}>{out}</g>;
            })}
            {/* the proof path of leaf 3 lights up on reveal, and reaches the committed root */}
            {pathK > 0 && (() => {
              const pts = [{ x: LEAF[2]!.x, y: LEAF[2]!.y - 50 }, { x: PAR[1]!.x, y: PAR[1]!.y + 34 }, { x: PAR[1]!.x, y: PAR[1]!.y - 34 }, { x: ROOT.x, y: ROOT.y + 60 }];
              const d = `M ${pts[0]!.x} ${pts[0]!.y} L ${pts[1]!.x} ${pts[1]!.y} M ${pts[2]!.x} ${pts[2]!.y} L ${pts[3]!.x} ${pts[3]!.y}`;
              const L = 2 * 230;
              return (
                <g>
                  <path d={d} fill="none" stroke={C.violet2} strokeWidth={16} strokeLinecap="round" strokeDasharray={`${pathK * L} ${L}`} filter="url(#beamGlow)" opacity={0.9} />
                  <path d={d} fill="none" stroke="#ffffff" strokeWidth={6} strokeLinecap="round" strokeDasharray={`${pathK * L} ${L}`} />
                </g>
              );
            })()}
          </WorldSvg>

          {/* the bar: a glass candle that closes, then lets its signals out */}
          <At x={CANDLE.x} y={CANDLE.y}>
            <At y={0}>
              <Box w={8} h={330 * candle} d={8} faces={{ front: rgba('lav', 0.7), top: rgba('lav', 0.7) }} alpha={candle} />
            </At>
            <At y={-20 + 60 * (1 - candle)}>
              <Box w={74} h={200 * candle} d={74} radius={6} alpha={clamp(candle * 2)} edge="rgba(255,255,255,0.55)" edgeW={1.2}
                faces={{ front: `linear-gradient(180deg, ${rgba('lav', 0.32 + 0.4 * closeFlash)}, ${rgba('violet', 0.2)})`, left: rgba('violet', 0.25), right: rgba('violet2', 0.3), top: rgba('lav', 0.55 + 0.4 * closeFlash), bottom: rgba('violet', 0.2), back: rgba('violet', 0.2) }}
                glow={`0 0 ${20 + 50 * closeFlash}px ${rgba('violet2', 0.5 + 0.4 * closeFlash)}`} />
            </At>
          </At>
          {PREV.map((p, i) => (
            <At key={`pc${i}`} x={p.x} y={p.y}>
              <At y={0}><Box w={6} h={p.h + 90} d={6} faces={{ front: rgba('lav', 0.35), top: rgba('lav', 0.35) }} alpha={prog(t, start + 0.04 * i, start + 0.3 + 0.04 * i)} /></At>
              <Box w={56} h={p.h} d={56} radius={5} alpha={0.75 * prog(t, start + 0.04 * i, start + 0.3 + 0.04 * i)} edge="rgba(255,255,255,0.25)" edgeW={1}
                faces={{ front: `linear-gradient(180deg, ${rgba('lav', 0.16)}, ${rgba('violet', 0.12)})`, left: rgba('violet', 0.14), right: rgba('violet2', 0.16), top: rgba('lav', 0.3), bottom: rgba('violet', 0.1), back: rgba('violet', 0.1) }} />
            </At>
          ))}
          <Label x={CANDLE.x - 150} y={CANDLE.y + 220} w={620} opacity={prog(t, tBar, tBar + 0.3) * (1 - prog(t, tRoot, tRoot + 0.4))}>
            <span style={{ ...F.mono(19, 500), color: rgba('lav', 0.8), letterSpacing: 1.5 }}>B2-RS · BAR 05 OCT · CLOSE 06 OCT 00:00Z</span>
          </Label>

          {/* the leaves: four real signals */}
          {LEAF.map((L, i) => {
            const a = leafAt(i);
            if (!a.on) return null;
            const state = i === 2 && opened ? 'open' : t >= tCommit ? 'sealed' : 'empty';
            return (
              <React.Fragment key={`leaf${i}`}>
                <At x={a.x} y={a.y} z={0} ry={(1 - a.k) * 160 + 12 * Math.sin(t * 0.9 + i)} rx={-10}>
                  <Block s={92} state={state} alpha={clamp(a.k * 3)} />
                </At>
                <Label x={L.x} y={L.y + 84} w={220} opacity={prog(t, tSig + 0.4 + 0.09 * i, tSig + 0.7 + 0.09 * i)}>
                  <span style={{ ...F.mono(18, 500), color: i === 2 && opened ? C.violet2 : rgba('lav', 0.8) }}>{LEAVES[i]}…</span>
                </Label>
              </React.Fragment>
            );
          })}
          {/* the two parent hashes */}
          {parK > 0 && PAR.map((P, i) => (
            <At key={`par${i}`} x={P.x} y={P.y} rx={-10} ry={20 + 10 * Math.sin(t * 0.8 + i)} s={clamp(parK, 0, 1.3)}>
              <Block s={66} state={t >= tCommit ? 'sealed' : 'empty'} />
            </At>
          ))}
          {/* the root */}
          {rootK > 0 && (
            <At x={ROOT.x} y={ROOT.y} rx={-12} ry={(t - tRoot) * 40 + 25} s={rootK * (1 + 0.12 * rootBurst + 0.1 * okPulse)}>
              <Block s={120} state="open" label="ROOT" />
            </At>
          )}
          <Label x={ROOT.x} y={ROOT.y - 112} w={460} opacity={prog(t, tRoot + 0.1, tRoot + 0.4) * (1 - prog(t, tCommit, tCommit + 0.25))}>
            <span style={{ ...F.mono(17, 500), color: rgba('lav', 0.75), letterSpacing: 2 }}>ONE ROOT FOR THE WHOLE BAR</span>
          </Label>

          {/* chain 97 */}
          {[4, 3, 2, 1].map(link)}
          {[4, 3, 2, 1, 0].map(chainBlock)}
          {/* the copy of the root on its way in */}
          {fly > 0 && fly < 1 && (
            <At x={lerp(ROOT.x, CH.x, fly)} y={lerp(ROOT.y, CH.y, fly) - Math.sin(fly * Math.PI) * 160} z={lerp(0, CH.z, fly)} ry={fly * 200} rx={-12}>
              <Block s={lerp(120, 96, fly)} state="open" />
            </At>
          )}
          <Label x={CH.x} y={CH.y + 128} w={700} opacity={prog(t, tChain + 0.2, tChain + 0.5)}>
            <span style={{ ...F.mono(20, 500), color: rgba('lav', 0.9) }}>SignalAnchor · BNB Smart Chain testnet (97)</span>
          </Label>
          <Label x={CH.x} y={CH.y + 164} w={700} opacity={prog(t, tChain + 0.45, tChain + 0.75)}>
            <span style={{ ...F.mono(19, 500), color: C.violet2 }}>committed +8 h 44 m after the close</span>
          </Label>
          {sealFlash > 0.02 && (
            <At x={CH.x} y={CH.y} z={CH.z + BS / 2 + 4}>
              <Plane w={BS * (1 + 2 * (1 - sealFlash))} h={BS * (1 + 2 * (1 - sealFlash))} style={{ borderRadius: '50%', border: `3px solid ${rgba('violet2', sealFlash)}` }} />
            </At>
          )}

          {/* the maxLag wall in front of the chain, and the late commit that hits it */}
          {lateIn > 0 && t < tReveal && (
            <>
              <At x={CH.x} y={CH.y} z={CH.z + BS / 2 + 40}>
                <Box w={220} h={220} d={10} radius={10} alpha={clamp(lateIn * 2) * (1 - prog(t, tRej + 0.7, tRej + 1.1)) * (0.45 + 0.55 * clamp(wall * 2))} edge={rgba('gap', 0.9)} edgeW={2}
                  faces={{ front: `radial-gradient(circle at 50% 50%, ${rgba('gap', 0.25 + 0.45 * wall)} 0%, ${rgba('gap', 0.12)} 70%)`, left: rgba('gap', 0.4), right: rgba('gap', 0.4), top: rgba('gap', 0.5), bottom: rgba('gap', 0.3), back: rgba('gap', 0.2) }}
                  glow={`0 0 ${20 + 80 * wall}px ${rgba('gap', 0.45 + 0.45 * wall)}`} />
              </At>
              <At x={lateX} y={lateY} z={lateZ} rz={30 * lateOut} ry={-20}>
                <Box w={88} h={88} d={88} radius={8} alpha={(1 - prog(t, tRej + 0.5, tRej + 0.9)) * clamp(lateIn * 3)} edge={C.gap} edgeW={2}
                  faces={{ front: rgba('gap', 0.18), left: rgba('gap', 0.12), right: rgba('gap', 0.12), top: rgba('gap', 0.25), bottom: rgba('gap', 0.1), back: rgba('gap', 0.12) }} />
              </At>
              <Label x={lateX + 20} y={lateY - 82} z={lateZ} w={420} opacity={(1 - prog(t, tRej + 0.4, tRej + 0.8)) * clamp(lateIn * 3)}>
                <span style={{ ...F.mono(20, 600), color: C.gap, background: rgba('night', 0.75), padding: '4px 10px', borderRadius: 6 }}>commit · bar + 12 h 00 m 01 s</span>
              </Label>
            </>
          )}
        </Stage>
      </AbsoluteFill>

      {/* L11 header */}
      <div style={{ position: 'absolute', left: 150, top: 120, width: 1620, opacity: 1 - prog(t, L12.start - 0.35, L12.start - 0.1) }}>
        <Karaoke t={t} words={span(L11, 0, 8)} st={{ font: F.archivo(58, 800, 100) }} wrap />
        <div style={{ height: 4 }} />
        <Karaoke t={t} words={span(L11, 9)} st={{ font: F.serif(60, 500), outline: rgba('mist', 0.4) }} wrap />
      </div>
      <div style={{ position: 'absolute', left: 150, top: 120, width: 1620, opacity: env(t, L12.start - 0.2, tTerm + 0.2, 0.2, 0.3) }}>
        <Karaoke t={t} words={span(L12, 0, 3)} st={{ font: F.archivo(58, 800, 100), hot: 'gap' }} wrap />
        <div style={{ height: 4 }} />
        <Karaoke t={t} words={span(L12, 4)} st={{ font: F.serif(60, 500), outline: rgba('mist', 0.4) }} wrap />
      </div>
      <div style={{ position: 'absolute', left: 1080, top: 300, ...stampStyle(t, tRej + 0.12, -4), ...(t > tReveal - 0.2 ? { opacity: 1 - prog(t, tReveal - 0.2, tReveal + 0.1) } : {}) }}>
        <div style={{ ...F.mono(26, 600), color: C.gap, border: `2.5px solid ${C.gap}`, padding: '7px 16px', borderRadius: 6, background: rgba('night', 0.7) }}>revert TooLate() · maxLag 43,200 s</div>
      </div>
      <div style={{ position: 'absolute', left: 560, top: 300, ...stampStyle(t, tOk, -3, 1.5), ...(t > tTerm ? { opacity: 1 - prog(t, tTerm, tTerm + 0.3) } : {}) }}>
        <div style={{ ...F.mono(21, 600), color: C.violet2, letterSpacing: 2, border: `2px solid ${rgba('violet2', 0.8)}`, padding: '7px 16px', borderRadius: 6, background: rgba('night', 0.7) }}>REVEAL ✓ PROOF MATCHES ROOT · SAH</div>
      </div>

      {/* anyone can rerun: in a browser, or in a terminal */}
      <div style={{ position: 'absolute', left: 980, top: 150, opacity: prog(t, tTerm + 0.2, tTerm + 0.6), transform: `perspective(1600px) rotateY(-10deg) translateY(${(1 - prog(t, tTerm + 0.2, tTerm + 0.8, ease.outCubic)) * -60}px)` }}>
        <BrowserFrame src="ui/verify-d-top.jpg" url="fabius-one.vercel.app/verify" w={800} h={470} imgW={2160} glint={prog(t, tTerm + 1.55, tTerm + 2.3)}>
          <Cursor t={t} keys={[{ t: tTerm + 0.7, x: 520, y: 300 }, { t: tTerm + 1.3, x: 713, y: 389 }]} clicks={[tTerm + 1.42]} />
        </BrowserFrame>
      </div>
      <Panel dark style={{ left: 980, top: 650, width: 800, height: 310, opacity: prog(t, tTerm, tTerm + 0.4), transform: `translateY(${(1 - prog(t, tTerm, tTerm + 0.4, ease.outCubic)) * 40}px)`, background: 'linear-gradient(135deg, rgba(38,29,92,0.92), rgba(18,14,46,0.94))' }}>
        <div style={{ position: 'absolute', left: 30, top: 26 }}>
          {VERIFY.map((ln, i) => (
            <div key={i} style={{ height: 38 }}>
              <Typer t={t} t0={i === 0 ? tTerm + 0.2 : w13('rerun').start + 0.15 + 0.22 * i} text={ln} size={i === 0 ? 18 : 17} weight={i === 0 ? 500 : 400}
                col={i === 0 ? C.lav : rgba('lav', 0.85)} cps={i === 0 ? 70 : 140} caret={i === 0 ? C.violet2 : false} />
            </div>
          ))}
        </div>
      </Panel>
      <div style={{ position: 'absolute', left: 150, top: 640, width: 760, opacity: env(t, L13.start - 0.3, end + 1, 0.3, 0.3) }}>
        <Karaoke t={t} words={span(L13, 0, 4)} st={{ font: F.archivo(72, 850, 100) }} wrap lineHeight={1.05} />
        <div style={{ height: 14 }} />
        <Karaoke t={t} words={span(L13, 5)} st={{ font: F.serif(70, 500), outline: rgba('mist', 0.4) }} wrap />
      </div>
      <div style={{ position: 'absolute', left: 150, top: 920, opacity: prog(t, w13('needed').start, w13('needed').start + 0.3) }}>
        <div style={{ display: 'inline-flex', gap: 14, ...F.mono(15, 600), letterSpacing: 3, color: C.lav, border: `1px solid ${rgba('violet2', 0.6)}`, borderRadius: 999, padding: '10px 20px', background: rgba('violet', 0.18) }}>
          VERIFY · NO KEY · NO GAS
        </div>
      </div>
      <div style={{ position: 'absolute', right: 150, top: 980, opacity: prog(t, w13('needed').start + 0.3, w13('needed').start + 0.6) }}>
        <Mono size={13} col={rgba('lav', 0.55)}>snapshot 06 Oct: 16 commits · 16 SAH · 0 missed</Mono>
      </div>
    </AbsoluteFill>
  );
}
