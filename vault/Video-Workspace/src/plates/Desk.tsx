// 06 DESK — "On top runs the AI desk. / Every five minutes, AI analysts, each with an ERC-8004 identity, vote on
// which bot to run, and where. / A locked formula turns their votes into one book. / And its root must reach the
// chain before the five minutes are up."
// Objects: a solid 5-minute dial (the cycle), five analyst orbs orbiting it (the active seats, real ERC-8004 ids),
// sealed ballots that drop into the hub, the hub becoming the locked formula, a five-slot book, and the cycle's
// root fired at DeskAnchor before the sweep closes (CYCLE = 300, TooLate after).
import React from 'react';
import { AbsoluteFill } from 'remotion';
import type { PlateProps } from '../timeline';
import { C, rgba } from '../lib/palette';
import { F } from '../lib/fonts';
import { lineOf, wordOf } from '../lib/lyrics';
import { clamp, ease, env, lerp, prog, pulse, shake, TAU } from '../lib/util';
import { Karaoke, Mono, span, stampStyle, Typer, W, H } from '../components/kit';
import { Ambient, Camera, type CamKey } from '../components/camera';

const L14 = lineOf('On top runs the AI desk');
const L15 = lineOf('Every five minutes');
const L16 = lineOf('A locked formula');
const L17 = lineOf('And its root must');
const w15 = (q: string) => wordOf(L15, q), w16 = (q: string) => wordOf(L16, q), w17 = (q: string) => wordOf(L17, q);

// the active seats on 06 Oct (config/agents.json + deployments/97.json analis.agents)
const AGENTS = [
  { id: 2558, model: 'DeepSeek V4.1 Flash' },
  { id: 2559, model: 'Qwen 3.8 Flash' },
  { id: 2561, model: 'Qwen 3.8 Omni · news' },
  { id: 2566, model: 'Muse Spark 1.3' },
  { id: 2567, model: 'Qwen 3.7 Plus' },
];
const CX = 960, CY = 505, R = 230, OX = 650, OY = 150;

export default function Desk({ t, start, end }: PlateProps) {
  const tDial = w15('Every').start, tAgents = w15('analysts').start, tId = w15('ERC-8004').start, tVote = w15('vote').start;
  const tFormula = w16('formula').start, tBook = w16('book').start;
  const tCycle0 = w15('Every').start, tCycle1 = w17('up').start + 0.1;
  const sweep = prog(t, tCycle0, tCycle1); // 0..1 of the 300 s cycle
  const tCommit = lerp(tCycle0, tCycle1, 0.84); // the root lands at 4:12
  const tLate = tCycle1 + 0.05;
  const sh = shake(t, 6 * pulse(t, tCommit + 0.35, 0.05) + 6 * pulse(t, tLate + 0.25, 0.05) + 5 * pulse(t, tFormula, 0.06));

  const dialIn = prog(t, start + 0.1, tDial + 0.4, ease.outBack);
  const formula = prog(t, tFormula - 0.15, tFormula + 0.35, ease.inOutCubic);
  const book = prog(t, tBook, tBook + 0.4, ease.outCubic);

  // orbit
  const orb = (i: number) => {
    const th = (i / AGENTS.length) * TAU + (t - start) * 0.22 - 0.4;
    const z = Math.sin(th);
    return { x: CX + OX * Math.cos(th), y: CY + 10 + OY * z, z, s: 0.78 + 0.3 * (z + 1) / 2 };
  };
  const agentIn = (i: number) => prog(t, tAgents + 0.12 * i, tAgents + 0.12 * i + 0.4, ease.outBack);

  const cam: CamKey[] = [
    { t: start - 0.4, s: 1.25, rx: 14 },
    { t: tDial + 0.6, s: 1.0, rx: 10, ez: ease.outQuart },
    { t: tVote, s: 1.04, rx: 12, rz: -1.2 },
    { t: tFormula + 0.2, s: 1.1, rx: 6, rz: 0, y: 0 },
    { t: L17.start, s: 1.05, rx: 8, y: -10 },
    { t: tCommit + 0.4, s: 1.0, rx: 10, y: -20 },
    { t: end + 0.4, s: 1.04, rx: 12, y: -14 },
  ];

  const ballot = (i: number) => {
    const t0 = tVote + 0.28 * i, t1 = t0 + 0.75;
    if (t < t0 || t > t1 + 0.05) return null;
    const o = orb(i);
    const k = ease.inOutCubic(clamp((t - t0) / (t1 - t0)));
    const x = lerp(o.x, CX, k), y = lerp(o.y, CY, k) - Math.sin(k * Math.PI) * 140;
    const s = lerp(1, 0.35, k);
    return (
      <g key={`b${i}`} transform={`translate(${x} ${y}) rotate(${(1 - k) * (i % 2 ? 12 : -12)}) scale(${s})`}>
        <rect x={-46} y={-30} width={92} height={60} rx={6} fill="rgba(255,255,255,0.92)" stroke={rgba('violet2', 0.9)} strokeWidth={1.5} />
        <path d="M -46 -30 L 0 6 L 46 -30" fill="none" stroke={rgba('violet', 0.7)} strokeWidth={1.6} />
        <circle cx={0} cy={6} r={9} fill={C.violet} />
        <text x={0} y={27} textAnchor="middle" style={{ ...F.mono(11, 600) }} fill={C.ink}>#{AGENTS[i]!.id}</text>
      </g>
    );
  };

  const orbNode = (i: number) => {
    const a = agentIn(i);
    if (a <= 0) return null;
    const o = orb(i), r = 38 * o.s * a;
    const glow = 0.5 + 0.5 * pulse(t, tVote + 0.28 * i, 0.2);
    return (
      <g key={`o${i}`} opacity={clamp(a * 1.5)}>
        <ellipse cx={o.x} cy={o.y + r * 1.25} rx={r * 0.9} ry={r * 0.22} fill="rgba(10,6,40,0.35)" />
        <circle cx={o.x} cy={o.y} r={r * 1.6} fill={`url(#halo)`} opacity={glow} />
        <circle cx={o.x} cy={o.y} r={r} fill="url(#orb)" stroke="rgba(255,255,255,0.7)" strokeWidth={1.2} />
        <circle cx={o.x - r * 0.32} cy={o.y - r * 0.36} r={r * 0.28} fill="rgba(255,255,255,0.55)" />
      </g>
    );
  };
  const orbLabel = (i: number) => {
    const a = agentIn(i);
    if (a <= 0) return null;
    const o = orb(i);
    return (
      <div key={`l${i}`} style={{ position: 'absolute', left: o.x - 130, width: 260, top: o.y + 50 * o.s, textAlign: 'center', opacity: a * (0.55 + 0.45 * (o.z + 1) / 2), transform: `scale(${o.s})` }}>
        <div style={{ ...F.mono(17, 600), color: C.lav, letterSpacing: 1 }}>agent #{AGENTS[i]!.id}</div>
        <div style={{ ...F.mono(13, 400), color: rgba('lav', 0.65) }}>{AGENTS[i]!.model}</div>
        <div style={{ display: 'inline-block', marginTop: 6, opacity: prog(t, tId + 0.08 * i, tId + 0.08 * i + 0.25), ...F.mono(11.5, 600), letterSpacing: 2, color: C.night, background: rgba('lav', 0.92), borderRadius: 999, padding: '3px 10px' }}>ERC-8004</div>
      </div>
    );
  };

  // dial geometry
  const ticks = Array.from({ length: 60 }, (_, i) => {
    const a = (i / 60) * TAU - Math.PI / 2, big = i % 12 === 0;
    const r0 = R + 26, r1 = R + (big ? 50 : 38);
    return <line key={i} x1={CX + r0 * Math.cos(a)} y1={CY + r0 * Math.sin(a)} x2={CX + r1 * Math.cos(a)} y2={CY + r1 * Math.sin(a)} stroke={rgba('lav', big ? 0.8 : 0.35)} strokeWidth={big ? 3 : 1.4} />;
  });
  const arc = (p: number) => {
    const a0 = -Math.PI / 2, a1 = a0 + p * TAU;
    const large = p > 0.5 ? 1 : 0;
    if (p <= 0.0005) return '';
    if (p >= 0.9999) return `M ${CX} ${CY - R} A ${R} ${R} 0 1 1 ${CX - 0.01} ${CY - R}`;
    return `M ${CX + R * Math.cos(a0)} ${CY + R * Math.sin(a0)} A ${R} ${R} 0 ${large} 1 ${CX + R * Math.cos(a1)} ${CY + R * Math.sin(a1)}`;
  };
  const hand = -Math.PI / 2 + sweep * TAU;
  const mm = Math.floor(sweep * 300 / 60), ss = Math.floor(sweep * 300) % 60;

  // the root's flight to DeskAnchor (top)
  const rootK = prog(t, tCommit - 0.45, tCommit, ease.inCubic);
  const rootX = CX, rootY = lerp(CY, 110, rootK);

  const behind = AGENTS.map((_, i) => i).filter((i) => orb(i).z < 0);
  const front = AGENTS.map((_, i) => i).filter((i) => orb(i).z >= 0);

  return (
    <AbsoluteFill>
      <AbsoluteFill style={{ background: `radial-gradient(ellipse 75% 70% at 50% 45%, ${C.violet} 0%, #4a2fd6 38%, #261a7a 72%, ${C.night2} 100%)` }} />
      <Camera t={t} keys={cam} depth={0.3}><Ambient t={t} seed={6} n={6} strength={1.3} dust={50} /></Camera>
      <Camera t={t} keys={cam}>
        <AbsoluteFill style={{ transform: `translate(${sh[0]}px, ${sh[1]}px)` }}>
          <svg width={W} height={H} style={{ position: 'absolute', inset: 0, overflow: 'visible' }}>
            <defs>
              <radialGradient id="orb" cx="35%" cy="30%" r="75%">
                <stop offset="0" stopColor="#ffffff" />
                <stop offset="0.45" stopColor={C.lav3} />
                <stop offset="1" stopColor={C.violet2} />
              </radialGradient>
              <radialGradient id="halo"><stop offset="0" stopColor="rgba(255,255,255,0.55)" /><stop offset="1" stopColor="rgba(255,255,255,0)" /></radialGradient>
              <linearGradient id="ring" x1="0" y1="0" x2="1" y2="1">
                <stop offset="0" stopColor="rgba(255,255,255,0.28)" />
                <stop offset="1" stopColor="rgba(255,255,255,0.06)" />
              </linearGradient>
            </defs>
            {/* orbit path */}
            <ellipse cx={CX} cy={CY + 10} rx={OX} ry={OY} fill="none" stroke={rgba('lav', 0.22 * prog(t, tAgents - 0.3, tAgents + 0.3))} strokeWidth={1.4} strokeDasharray="4 10" />
            {behind.map(orbNode)}
            {/* the dial: a thick glass ring with a lit sweep */}
            <g opacity={clamp(dialIn * 1.3)} transform={`translate(${CX} ${CY}) scale(${0.6 + 0.4 * dialIn}) translate(${-CX} ${-CY})`}>
              <circle cx={CX} cy={CY + 18} r={R + 8} fill="rgba(10,6,40,0.35)" />
              <circle cx={CX} cy={CY} r={R} fill="none" stroke="url(#ring)" strokeWidth={34} />
              <circle cx={CX} cy={CY} r={R} fill="none" stroke="rgba(255,255,255,0.25)" strokeWidth={1} transform={`translate(0 -17)`} opacity={0} />
              {ticks}
              <path d={arc(sweep)} fill="none" stroke={C.lav} strokeWidth={34} strokeLinecap="butt" opacity={0.95} style={{ filter: `drop-shadow(0 0 16px ${rgba('lav', 0.8)})` }} />
              {sweep > 0.84 && <path d={`M ${CX + R * Math.cos(-Math.PI / 2 + 0.84 * TAU)} ${CY + R * Math.sin(-Math.PI / 2 + 0.84 * TAU)} L ${CX + (R + 60) * Math.cos(-Math.PI / 2 + 0.84 * TAU)} ${CY + (R + 60) * Math.sin(-Math.PI / 2 + 0.84 * TAU)}`} stroke={C.ink} strokeWidth={3} />}
              <line x1={CX} y1={CY} x2={CX + (R - 30) * Math.cos(hand)} y2={CY + (R - 30) * Math.sin(hand)} stroke={C.lav} strokeWidth={5} strokeLinecap="round" />
              {/* hub: ballot box -> formula */}
              <circle cx={CX} cy={CY} r={lerp(118, 0, formula)} fill={C.night2} stroke={rgba('lav', 0.5)} strokeWidth={2} />
              <circle cx={CX} cy={CY} r={14} fill={C.lav} />
            </g>
            {AGENTS.map((_, i) => ballot(i))}
            {front.map(orbNode)}
            {/* the root to DeskAnchor */}
            {t >= tCommit - 0.45 && t < tCommit + 0.05 && (
              <circle cx={rootX} cy={rootY} r={22} fill={C.lav} style={{ filter: `drop-shadow(0 0 22px ${rgba('lav', 0.95)})` }} />
            )}
          </svg>
          {/* dial readout */}
          <div style={{ position: 'absolute', left: CX - 200, width: 400, top: CY - 40, textAlign: 'center', opacity: dialIn * (1 - clamp(formula * 3)) }}>
            <div style={{ ...F.archivo(64, 800, 110), color: C.lav, letterSpacing: 1 }}>{`${mm}:${String(ss).padStart(2, '0')}`}</div>
            <Mono size={13} col={rgba('lav', 0.7)} spacing={3}>cycle · 300 s</Mono>
          </div>
          {AGENTS.map((_, i) => orbLabel(i))}
          {/* the locked formula */}
          <div style={{ position: 'absolute', left: CX - 340, width: 680, top: CY - 150 - 40 * book, height: 300 + 80 * book, borderRadius: 26, opacity: formula, transform: `scale(${0.7 + 0.3 * formula})`, background: 'linear-gradient(135deg, rgba(38,29,110,0.97), rgba(20,15,60,0.97))', border: '1px solid rgba(255,255,255,0.35)', boxShadow: '0 1px 0 rgba(255,255,255,0.4) inset, 0 30px 80px -30px rgba(10,6,40,0.7)', display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', gap: 12 }}>
            <Mono size={13} col={rgba('lav', 0.75)} spacing={3}>🔒 locked formula · PARAMS2 r4 · 0x6f613e50…</Mono>
            <div style={{ ...F.mono(36, 600), color: C.lav }}>bot* = argmax Σ conf × score</div>
            <Mono size={13} col={rgba('lav', 0.75)} spacing={2}>direction from the bot’s locked rule · ≤ 5 positions</Mono>
            {/* one book: five slots */}
            <div style={{ display: 'flex', gap: 14, marginTop: 10 * book, height: 74 * book, opacity: book, alignItems: 'center' }}>
              {[0, 1, 2, 3, 4].map((i) => {
                const sw = pulse(t, tBook + 0.2 + 0.09 * i, 0.16);
                return <div key={i} style={{ width: 58, height: 58, borderRadius: 10, background: `linear-gradient(135deg, rgba(255,255,255,${0.14 + 0.5 * sw}), rgba(255,255,255,0.04))`, border: `1.5px solid ${rgba('lav', 0.45 + 0.5 * sw)}`, boxShadow: `0 0 ${24 * sw}px ${rgba('lav', 0.8 * sw)}` }} />;
              })}
            </div>
            <div style={{ opacity: book, height: 20 * book }}><Mono size={14} col={C.lav} spacing={4}>one book · ≤ 5 slots</Mono></div>
          </div>
          {/* DeskAnchor */}
          <div style={{ position: 'absolute', left: CX - 230, width: 460, top: 52, height: 96, borderRadius: 18, opacity: prog(t, L17.start - 0.2, L17.start + 0.2), background: t >= tCommit ? rgba('lav', 0.95) : 'rgba(255,255,255,0.1)', border: `1.5px solid ${rgba('lav', 0.7)}`, display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', transform: `scale(${1 + 0.08 * pulse(t, tCommit, 0.12)})` }}>
            <div style={{ ...F.mono(18, 600), color: t >= tCommit ? C.ink : C.lav }}>DeskAnchor · chain 97</div>
            <div style={{ ...F.mono(13, 400), color: t >= tCommit ? rgba('ink', 0.7) : rgba('lav', 0.7) }}>{t >= tCommit ? 'root committed at 4:12 ✓' : 'accepts a root only while its cycle runs'}</div>
          </div>
          <div style={{ position: 'absolute', left: CX + 260, top: 180, ...stampStyle(t, tLate + 0.2, 5) }}>
            <div style={{ ...F.mono(22, 600), color: C.gap, border: `2.5px solid ${C.gap}`, padding: '6px 14px', borderRadius: 6, background: rgba('night', 0.55) }}>at 5:00 → TooLate()</div>
          </div>
        </AbsoluteFill>
      </Camera>

      {/* the words */}
      <Camera t={t} keys={[]} drift={0.4}>
        <div style={{ position: 'absolute', left: 150, top: 150, opacity: 1 - prog(t, L15.start - 0.2, L15.start + 0.2) }}>
          <Karaoke t={t} words={L14.words} st={{ font: F.archivo(92, 900, 112), hot: 'lav', done: 'lav', outline: rgba('lav', 0.4) }} />
        </div>
        <div style={{ position: 'absolute', left: 150, right: 150, bottom: 112, opacity: env(t, L15.start - 0.3, L16.start - 0.05, 0.3, 0.25) }}>
          <Karaoke t={t} words={span(L15, 0, 9)} st={{ font: F.archivo(44, 800, 100), hot: 'lav', done: 'lav', outline: rgba('lav', 0.35) }} wrap align="center" />
          <div style={{ height: 6 }} />
          <Karaoke t={t} words={span(L15, 10)} st={{ font: F.serif(52, 500), hot: 'lav', done: 'lav', outline: rgba('lav', 0.35) }} wrap align="center" />
        </div>
        <div style={{ position: 'absolute', left: 150, right: 150, bottom: 120, opacity: env(t, L16.start - 0.25, L17.start - 0.05, 0.25, 0.25) }}>
          <Karaoke t={t} words={L16.words} st={{ font: F.archivo(50, 800, 100), hot: 'lav', done: 'lav', outline: rgba('lav', 0.35) }} wrap align="center" />
        </div>
        <div style={{ position: 'absolute', left: 150, right: 150, bottom: 120, opacity: env(t, L17.start - 0.25, end + 1, 0.25, 0.25) }}>
          <Karaoke t={t} words={L17.words} st={{ font: F.archivo(48, 800, 100), hot: 'lav', done: 'lav', outline: rgba('lav', 0.35) }} wrap align="center" />
        </div>
        <div style={{ position: 'absolute', right: 150, top: 165, textAlign: 'right', opacity: prog(t, tId, tId + 0.4) * (1 - prog(t, L16.start, L16.start + 0.3)) }}>
          <Typer t={t} t0={tId} text="ERC-8004 = an on-chain ID card for an AI agent" size={17} col={rgba('lav', 0.85)} caret={false} />
        </div>
      </Camera>
    </AbsoluteFill>
  );
}
