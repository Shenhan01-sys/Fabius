// 08 OPEN — "And the desk is open. / Bring your own bot as declarative rules, or plug in your own agent. /
// Every bot runs the same gates in public, and every verdict comes with its reason."
// Two glass doors swing open; behind them the real /submit and /submit-agent pages; then a corridor of gates
// G1..G11 — solid portals on a glass floor — that a bot walks through. The run shown is real: B3-CARRY's gate report
// (ledger/book/laporan) passed every gate, and the slot book still said no — forward shadow 3 of 60 days.
import React from 'react';
import { AbsoluteFill } from 'remotion';
import type { PlateProps } from '../timeline';
import { C, rgba } from '../lib/palette';
import { F } from '../lib/fonts';
import { lineOf, wordOf } from '../lib/lyrics';
import { clamp, ease, env, lerp, prog, pulse, shake } from '../lib/util';
import { Karaoke, NightBg, span, stampStyle, Typer, W, H } from '../components/kit';
import { Ambient, Camera, type CamKey } from '../components/camera';
import { BrowserFrame, Cursor } from '../components/devices';
import { At, Block, Box, Plane, Stage, stageAt, type StageKey } from '../components/solid';

const L19 = lineOf('And the desk is open');
const L20 = lineOf('Bring your own bot');
const L21 = lineOf('Every bot runs the same');
const w19 = (q: string) => wordOf(L19, q), w20 = (q: string) => wordOf(L20, q), w21 = (q: string) => wordOf(L21, q);

// B3-CARRY gate report (ledger/book/laporan/*.json): status per gate, and a plain-language gloss
const GATES = [
  ['G1', 'PIT', 'PASS', 'no look-ahead'], ['G2', 'DATA', 'PASS', 'enough history'], ['G3', 'NET', 'PASS', 'after costs'],
  ['G4', 'RECENT', 'PASS', 'still works lately'], ['G5', 'PLATEAU', 'PASS', 'not one lucky setting'], ['G6', 'PHASE', 'N/A', 'no schedule'],
  ['G7', 'FOLD', 'PASS', 'without its best year'], ['G8', 'NULL', 'PASS', 'beats its own shuffle'], ['G9', 'COST', 'PASS', 'at 2× costs'],
  ['G10', 'MARGINAL', 'PASS', 'adds to the book'], ['G11', 'CAPACITY', 'NA', 'measured before money'],
] as const;

export default function Open({ t, start, end }: PlateProps) {
  const tOpen = w19('open').start;
  const doors = prog(t, tOpen - 0.05, tOpen + 0.7, ease.inOutCubic);
  const tBot = w20('Bring').start, tAgent = w20('plug').start;
  const tGates = L21.start - 0.35, tRun0 = w21('runs').start - 0.1, tRun1 = w21('verdict').start + 0.1;
  const tVerdict = w21('reason').start - 0.2;
  const pagesOut = prog(t, tGates, tGates + 0.5, ease.inCubic);
  const runK = prog(t, tRun0, tRun1, ease.inOutCubic);
  const sh = shake(t, 6 * pulse(t, tVerdict, 0.05) + 5 * pulse(t, tOpen + 0.1, 0.06));

  const cam: CamKey[] = [
    { t: start - 0.3, s: 1.15 },
    { t: tOpen + 0.7, s: 1.02, ez: ease.outQuart },
    { t: tAgent + 0.6, s: 1.05, rx: 0 },
    { t: tGates + 0.5, s: 1.0, rx: 0, y: 0 },
    { t: end + 0.3, s: 1.0, rx: 0, x: 0, y: 0 },
  ];

  // the gates: a row of solid portals on a glass floor (stage coordinates), and the bot that walks through them
  const GX = (i: number) => (i - (GATES.length - 1) / 2) * 150;
  const tokenX = lerp(-960, 960, runK);
  const passed = (i: number) => tokenX > GX(i);
  const gcam: StageKey[] = [
    { t: tGates - 0.1, rx: 22, ry: -16, z: -420, y: 40 },
    { t: tRun0 + 0.3, rx: 15, ry: -8, z: -80, y: 20, ez: ease.outCubic },
    { t: tRun1, rx: 13, ry: 7, z: -60, y: 20 },
    { t: end + 0.3, rx: 12, ry: 10, z: -110, y: 20 },
  ];

  return (
    <AbsoluteFill>
      <NightBg glow={1.1} />
      <Camera t={t} keys={cam} depth={0.3}><Ambient t={t} seed={9} cubes={6} /></Camera>
      <Camera t={t} keys={cam}>
        <AbsoluteFill style={{ transform: `translate(${sh[0]}px, ${sh[1]}px)` }}>
          {/* light behind the doors */}
          <div style={{ position: 'absolute', left: W / 2 - 520 * doors, width: 1040 * doors, top: 175, height: 770, background: `radial-gradient(ellipse 60% 60% at 50% 50%, ${rgba('lav', 0.55 * doors * (1 - pagesOut))} 0%, ${rgba('violet', 0.35 * doors * (1 - pagesOut))} 45%, ${rgba('violet', 0)} 75%)` }} />
          {/* the pages behind the doors */}
          <div style={{ opacity: prog(t, tBot - 0.3, tBot + 0.2) * (1 - pagesOut) }}>
            <div style={{ position: 'absolute', left: 150, top: 200, transform: `perspective(1600px) rotateY(${lerp(25, 14, prog(t, tBot, tBot + 1))}deg) translateY(${(1 - prog(t, tBot - 0.2, tBot + 0.5, ease.outCubic)) * 160}px)`, transformOrigin: '0% 50%' }}>
              <BrowserFrame src="ui/submit-d-top.jpg" url="fabius-one.vercel.app/submit" w={760} h={540} imgW={2160} scroll={lerp(0, 220, prog(t, tBot, tAgent + 1.5))} glint={prog(t, tBot + 0.2, tBot + 1.0)}>
                <Cursor t={t} keys={[{ t: tBot + 0.45, x: 520, y: 220 }, { t: tBot + 1.2, x: 204, y: 421 }]} clicks={[tBot + 1.32]} />
              </BrowserFrame>
            </div>
            <div style={{ position: 'absolute', left: 1010, top: 200, opacity: prog(t, tAgent - 0.3, tAgent + 0.2), transform: `perspective(1600px) rotateY(${lerp(-25, -14, prog(t, tAgent, tAgent + 1))}deg) translateY(${(1 - prog(t, tAgent - 0.2, tAgent + 0.5, ease.outCubic)) * 160}px)`, transformOrigin: '100% 50%' }}>
              <BrowserFrame src="ui/submitagent-d-top.jpg" url="fabius-one.vercel.app/submit-agent" w={760} h={540} imgW={2160} scroll={lerp(0, 180, prog(t, tAgent, tGates))} glint={prog(t, tAgent + 0.2, tAgent + 1.0)} />
            </div>
          </div>
          {/* the two glass doors */}
          {[-1, 1].map((s) => (
            <div key={s} style={{ position: 'absolute', top: 175, height: 770, width: 520, left: s < 0 ? W / 2 - 520 : W / 2, transformOrigin: s < 0 ? '0% 50%' : '100% 50%', transform: `perspective(1400px) rotateY(${-s * 82 * doors}deg)`, opacity: 1 - prog(t, tOpen + 0.5, tOpen + 0.9),
              background: 'linear-gradient(135deg, rgba(255,255,255,0.16), rgba(255,255,255,0.04))', border: '1px solid rgba(255,255,255,0.3)', boxShadow: '0 1px 0 rgba(255,255,255,0.25) inset' }}>
              <div style={{ position: 'absolute', top: 360, [s < 0 ? 'right' : 'left']: 28, width: 10, height: 90, borderRadius: 5, background: rgba('lav', 0.8) } as React.CSSProperties} />
              <div style={{ position: 'absolute', top: 300, width: '100%', textAlign: 'center', ...F.archivo(200, 900, 120), color: rgba('lav', 0.92) }}>{s < 0 ? 'OP' : 'EN'}</div>
            </div>
          ))}

        </AbsoluteFill>
      </Camera>

      {/* the gates, in 3D */}
      {t >= tGates - 0.1 && (
        <Stage cam={stageAt(gcam, t)} t={t} drift={0.6} perspective={1700} cy={630} opacity={prog(t, tGates + 0.12, tGates + 0.45)}>
          {/* glass floor */}
          <At y={128}>
            <Box w={1900} h={12} d={260} radius={8} edge="rgba(255,255,255,0.25)" edgeW={1}
              faces={{ front: 'linear-gradient(90deg, rgba(157,134,255,0.18), rgba(157,134,255,0.32), rgba(157,134,255,0.18))', top: `linear-gradient(90deg, ${rgba('violet', 0.12)}, ${rgba('violet2', 0.28)} 50%, ${rgba('violet', 0.12)})`, left: rgba('violet', 0.2), right: rgba('violet', 0.2), bottom: rgba('violet', 0.1), back: rgba('violet', 0.1) }} />
          </At>
          {/* the lit path the bot has walked */}
          <At y={121} rx={90}>
            <Plane w={1900} h={60} style={{ background: `linear-gradient(90deg, ${rgba('violet2', 0)} 0%, ${rgba('violet2', 0.55)} ${clamp((tokenX + 950) / 1900) * 100}%, ${rgba('violet2', 0)} ${clamp((tokenX + 950) / 1900) * 100 + 0.1}%)` }} />
          </At>
          {GATES.map((g, i) => {
            const x = GX(i);
            const rise = prog(t, tGates + 0.15 + 0.04 * i, tGates + 0.57 + 0.04 * i, ease.outBack);
            const ok = passed(i), na = g[2] !== 'PASS';
            // the flash as the bot passes through
            const u = (tokenX - x) / 120;
            const flash = ok ? Math.exp(-Math.max(0, u) * 2.2) : 0;
            const lit = ok ? (na ? 0.25 : 0.55) : 0;
            const frame = ok ? (na ? `linear-gradient(180deg, #8f8aa8, #5f5a80)` : `linear-gradient(180deg, #b9a9ff, ${C.violet})`) : `linear-gradient(180deg, #3a3170, #251d5c)`;
            const side = ok ? (na ? '#4e4870' : '#4b2fd0') : '#1d1650';
            const top = ok ? (na ? '#a9a4c4' : '#d2c8ff') : '#4a3f8f';
            const faces = { front: frame, left: side, right: side, top, bottom: side, back: side };
            const edge = ok && !na ? 'rgba(255,255,255,0.75)' : 'rgba(255,255,255,0.22)';
            const a = clamp(rise * 2);
            return (
              <At key={g[0]} x={x} y={(1 - rise) * 180}>
                {/* posts and lintel */}
                <At x={-57}><Box w={18} h={236} d={62} radius={4} faces={faces} edge={edge} edgeW={1} alpha={a} /></At>
                <At x={57}><Box w={18} h={236} d={62} radius={4} faces={faces} edge={edge} edgeW={1} alpha={a} /></At>
                <At y={-132}>
                  <Box w={150} h={34} d={70} radius={6} faces={faces} edge={edge} edgeW={1} alpha={a}
                    glow={ok && !na ? `0 0 ${18 + 40 * flash}px ${rgba('violet2', 0.6 + 0.3 * flash)}` : undefined}>
                    <div style={{ position: 'absolute', inset: 0, display: 'flex', alignItems: 'center', justifyContent: 'center', ...F.mono(20, 600), color: ok && !na ? C.ink : C.lav, letterSpacing: 1 }}>{g[0]}</div>
                  </Box>
                </At>
                {/* the light curtain */}
                <At y={0}>
                  <Plane w={96} h={236} style={{ opacity: a, background: ok ? `linear-gradient(180deg, ${rgba(na ? 'mist' : 'violet2', lit + 0.4 * flash)}, ${rgba(na ? 'mist' : 'violet', 0.08 + 0.3 * flash)})` : 'linear-gradient(180deg, rgba(255,255,255,0.07), rgba(255,255,255,0.02))', borderRadius: 4 }}>
                    <div style={{ position: 'absolute', left: 0, right: 0, top: 70, textAlign: 'center', ...F.archivo(64, 900, 100), color: na ? rgba('lav', 0.75) : '#ffffff', opacity: ok ? clamp(0.6 + flash) : 0, textShadow: na ? undefined : `0 0 24px ${rgba('violet2', 0.9)}` }}>{na ? '–' : '✓'}</div>
                  </Plane>
                </At>
                {/* name, status, and the reason in plain words */}
                <At y={206} z={40}>
                  <Plane w={148} h={140} style={{ textAlign: 'center', opacity: a }}>
                    <div style={{ ...F.mono(18, 600), color: rgba('lav', 0.95), letterSpacing: 0.5 }}>{g[1]}</div>
                    <div style={{ ...F.mono(16, 600), color: ok ? (na ? rgba('lav', 0.7) : C.violet2) : 'transparent', marginTop: 3 }}>{ok ? (na ? 'N/A' : '✓ PASS') : '·'}</div>
                    <div style={{ ...F.mono(15, 400), color: ok ? rgba('lav', 0.9) : rgba('lav', 0.45), marginTop: 6, lineHeight: 1.25 }}>{g[3]}</div>
                  </Plane>
                </At>
              </At>
            );
          })}
          {/* the bot: B3-CARRY, walking the gates */}
          <At x={tokenX} y={84} z={0} rx={-14} ry={t * 90}>
            <Block s={58} state="open" alpha={prog(t, tRun0 - 0.3, tRun0)} />
          </At>
          <At x={tokenX} y={18} z={0}>
            <Plane w={160} h={26} style={{ textAlign: 'center', opacity: prog(t, tRun0 - 0.3, tRun0) * (1 - prog(t, tRun1 + 0.2, tRun1 + 0.5)) }}>
              <span style={{ ...F.mono(14, 600), color: C.lav, background: rgba('night', 0.7), padding: '2px 8px', borderRadius: 5 }}>B3-CARRY</span>
            </Plane>
          </At>
        </Stage>
      )}

      {/* words */}
      <Camera t={t} keys={[]} drift={0.4}>
        <div style={{ position: 'absolute', left: 150, right: 150, top: 60, opacity: 1 - prog(t, L20.start - 0.45, L20.start - 0.2) }}>
          <Karaoke t={t} words={L19.words} st={{ font: F.archivo(80, 900, 110) }} align="center" />
        </div>
        <div style={{ position: 'absolute', left: 150, right: 150, top: 82, opacity: env(t, L20.start - 0.2, tGates + 0.1, 0.25, 0.3) }}>
          <Karaoke t={t} words={span(L20, 0, 6)} st={{ font: F.archivo(54, 850, 100) }} align="center" wrap />
          <div style={{ height: 4 }} />
          <Karaoke t={t} words={span(L20, 7)} st={{ font: F.serif(58, 500), outline: rgba('mist', 0.4) }} align="center" wrap />
        </div>
        <div style={{ position: 'absolute', left: 150, right: 150, top: 120, opacity: env(t, L21.start - 0.25, end + 1, 0.25, 0.3) }}>
          <Karaoke t={t} words={span(L21, 0, 7)} st={{ font: F.archivo(54, 850, 100) }} align="center" wrap />
          <div style={{ height: 4 }} />
          <Karaoke t={t} words={span(L21, 8)} st={{ font: F.serif(56, 500), outline: rgba('mist', 0.4) }} align="center" wrap />
        </div>
        <div style={{ position: 'absolute', left: 0, right: 0, top: 900, textAlign: 'center', ...stampStyle(t, tVerdict, -2, 1.6) }}>
          <div style={{ display: 'inline-block', borderRadius: 16, padding: '14px 26px', background: rgba('night', 0.85), border: `2px solid ${C.gap}` }}>
            <span style={{ ...F.mono(20, 600), color: C.lav }}>B3-CARRY · every gate passed → </span>
            <span style={{ ...F.mono(20, 600), color: C.gap }}>slot: NO · forward shadow 3 of 60 days</span>
          </div>
        </div>
        <div style={{ position: 'absolute', left: 0, right: 0, top: 972, textAlign: 'center', opacity: prog(t, tVerdict + 0.4, tVerdict + 0.8) }}>
          <Typer t={t} t0={tVerdict + 0.4} text="reviews run in the public repo · GitHub Actions bot-review.yml" size={14} col={rgba('lav', 0.6)} caret={false} />
        </div>
      </Camera>
    </AbsoluteFill>
  );
}
