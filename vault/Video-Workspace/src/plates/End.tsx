// 11 END — "So Fabius does what Fabius does best. / It waits. / Fabius. Refuse the battle. Prove the decision."
// The crystal (the web's glass cube) turns slowly inside a ticking ring while nothing happens — then the
// lavender hero opens from it: the name, the two lines, and the product on desktop, phone and Telegram.
import React from 'react';
import { AbsoluteFill } from 'remotion';
import type { PlateProps } from '../timeline';
import { C, rgba } from '../lib/palette';
import { F } from '../lib/fonts';
import { lineOf, wordOf } from '../lib/lyrics';
import { clamp, ease, env, lerp, prog, pulse, TAU } from '../lib/util';
import { Karaoke, LavBg, Mono, NightBg, span, W, H } from '../components/kit';
import { Ambient, Camera, type CamKey } from '../components/camera';
import { Cube3D } from '../components/glass';
import { BrowserFrame, PhoneFrame, TelegramChat, type ChatMsg } from '../components/devices';

const L28 = lineOf('So Fabius does what');
const L29 = lineOf('It waits');
const L30 = lineOf('Fabius. Refuse');
const w30 = (q: string) => wordOf(L30, q);

const CHAT: ChatMsg[] = [
  { at: -10, from: 'me', text: '/buy' },
  { at: -10, from: 'bot', text: 'B1-TREND · bar 2026-10-05 · 0.01 FAB\n\nTap the button: sign in with Telegram (or Google), get free FAB, pay with x402 (no gas). The signal is also sent here.', button: 'Buy B1-TREND · 0.01 FAB' },
  { at: -10, from: 'me', text: '/analysts' },
  { at: -10, from: 'bot', text: 'Bot Fabius trades now (locked rule): B1-TREND — no analyst picks for this bar -> identity bot' },
];

export default function End({ t, start, end }: PlateProps) {
  const tWait = L29.start, tHero = L30.start - 0.45;
  const hero = prog(t, tHero, tHero + 0.8, ease.inOutCubic);
  const tName = w30('Fabius.').start;
  const spin = (t - start) * 22;
  const cam: CamKey[] = [
    { t: start - 0.3, s: 1.08 },
    { t: tWait, s: 1.0 },
    { t: tHero, s: 1.12, ez: ease.inOutQuart },
    { t: tHero + 0.9, s: 1.0 },
    { t: end, s: 1.04 },
  ];
  const tick = Math.floor((t - start) * 2);
  const nameA = (i: number) => prog(t, tName - 0.1 + i * 0.05, tName + 0.16 + i * 0.05, ease.outQuart);

  return (
    <AbsoluteFill>
      {/* night: the wait */}
      <AbsoluteFill style={{ opacity: 1 - prog(t, tHero + 0.5, tHero + 0.9) }}>
        <NightBg glow={0.9} />
        <Camera t={t} keys={cam} depth={0.3}><Ambient t={t} seed={12} n={5} /></Camera>
        <Camera t={t} keys={cam}>
          <svg width={W} height={H} style={{ position: 'absolute', inset: 0 }}>
            <circle cx={W / 2} cy={H / 2 + 20} r={250} fill="none" stroke={rgba('lav', 0.18)} strokeWidth={2} />
            {Array.from({ length: 60 }, (_, i) => {
              const a = (i / 60) * TAU - Math.PI / 2, big = i % 5 === 0;
              const on = i <= tick % 60;
              return <line key={i} x1={W / 2 + 250 * Math.cos(a)} y1={H / 2 + 20 + 250 * Math.sin(a)} x2={W / 2 + (big ? 222 : 234) * Math.cos(a)} y2={H / 2 + 20 + (big ? 222 : 234) * Math.sin(a)} stroke={on ? rgba('violet2', 0.95) : rgba('lav', 0.25)} strokeWidth={big ? 3 : 1.5} />;
            })}
          </svg>
          <Cube3D x={W / 2} y={H / 2 + 20} s={190} rx={-24} ry={spin} lit={0.25 + 0.15 * Math.sin(t * 1.4)} />
        </Camera>
        <Camera t={t} keys={[]} drift={0.4}>
          <div style={{ position: 'absolute', left: 150, right: 150, top: 150, opacity: env(t, L28.start - 0.3, tWait - 0.2, 0.3, 0.4) }}>
            <Karaoke t={t} words={L28.words} st={{ font: F.serif(92, 500), outline: rgba('mist', 0.4) }} align="center" />
          </div>
          <div style={{ position: 'absolute', left: 0, right: 0, top: 880, textAlign: 'center', opacity: env(t, tWait - 0.2, tHero + 0.2, 0.4, 0.3) }}>
            <Karaoke t={t} words={L29.words} st={{ font: F.serif(84, 500), hot: 'lav', done: 'lav', outline: rgba('mist', 0.4) }} align="center" />
          </div>
        </Camera>
      </AbsoluteFill>

      {/* lavender: the hero opens from the crystal */}
      <AbsoluteFill style={{ clipPath: `circle(${hero * 120}% at ${W / 2}px ${H / 2 + 20}px)` }}>
        <LavBg />
        <Camera t={t} keys={cam} depth={0.3}><Ambient t={t} light seed={13} n={6} dust={20} cubes={10} /></Camera>
        <Camera t={t} keys={[{ t: tHero, s: 1.06 }, { t: end, s: 1.0 }]}>
          {/* product: desktop, phone, Telegram */}
          <div style={{ position: 'absolute', left: 70, top: 620, opacity: prog(t, tHero + 0.5, tHero + 1.0), transform: `perspective(1800px) rotateY(20deg) rotateX(6deg) translateY(${(1 - prog(t, tHero + 0.5, tHero + 1.2, ease.outCubic)) * 160}px)`, transformOrigin: '0% 50%' }}>
            <BrowserFrame src="ui/home-d-top.jpg" url="fabius-one.vercel.app" w={640} h={400} imgW={2160} glint={prog(t, tHero + 1.2, tHero + 2.1)} />
          </div>
          <div style={{ position: 'absolute', left: 1390, top: 520, opacity: prog(t, tHero + 0.7, tHero + 1.2), transform: `perspective(1600px) rotateY(-16deg) rotateZ(3deg) translateY(${(1 - prog(t, tHero + 0.7, tHero + 1.4, ease.outCubic)) * 160}px)` }}>
            <PhoneFrame src="ui/home-m-top.jpg" w={215} glint={prog(t, tHero + 1.4, tHero + 2.3)} />
          </div>
          <div style={{ position: 'absolute', left: 1625, top: 590, opacity: prog(t, tHero + 0.9, tHero + 1.4), transform: `perspective(1600px) rotateY(-24deg) rotateZ(5deg) translateY(${(1 - prog(t, tHero + 0.9, tHero + 1.6, ease.outCubic)) * 160}px)` }}>
            <TelegramChat t={t} msgs={CHAT} w={215} />
          </div>
          {/* the crystal, now in the hero */}
          <Cube3D x={W / 2} y={405 + 6 * Math.sin(t * 1.3)} s={105} rx={-24} ry={spin} lit={0.6} opacity={prog(t, tHero + 0.2, tHero + 0.6)} />
        </Camera>
        <Camera t={t} keys={[]} drift={0.3}>
          <div style={{ position: 'absolute', left: 0, right: 0, top: 120, display: 'flex', justifyContent: 'center' }}>
            {Array.from('FABIUS').map((ch, i) => {
              const k = nameA(i);
              return <span key={i} style={{ ...F.archivo(180, 900, 125), color: C.ink, display: 'inline-block', lineHeight: 1, opacity: clamp(k * 2), transform: `translateY(${(1 - k) * -90}px)`, filter: k < 1 ? `blur(${(1 - k) * 10}px)` : undefined }}>{ch}</span>;
            })}
          </div>
          <div style={{ position: 'absolute', left: 0, right: 0, top: 520, opacity: prog(t, w30('Refuse').start - 0.3, w30('Refuse').start) }}>
            <Karaoke t={t} words={span(L30, 1, 3)} st={{ font: F.serif(78, 500), light: true }} align="center" />
            <div style={{ height: 2 }} />
            <Karaoke t={t} words={span(L30, 4)} st={{ font: F.serif(78, 600), light: true, hot: 'violet', done: 'violet' }} align="center" />
          </div>
          <div style={{ position: 'absolute', left: 0, right: 0, top: 992, textAlign: 'center', opacity: prog(t, w30('decision.').end, w30('decision.').end + 0.5) }}>
            <Mono size={16} col={rgba('ink', 0.75)} spacing={2.5}>fabius-one.vercel.app  ·  github.com/Shenhan01-sys/Fabius  ·  BSC testnet (97)  ·  Telegram: /buy</Mono>
          </div>
          {/* the web's rotating badge */}
          <div style={{ position: 'absolute', left: 250, top: 330, width: 150, height: 150, opacity: prog(t, tName + 0.5, tName + 0.9), transform: `rotate(${(t - tName) * 30}deg)` }}>
            <svg width={150} height={150}>
              <defs><path id="badgeArc" d="M 75 75 m -58 0 a 58 58 0 1 1 116 0 a 58 58 0 1 1 -116 0" /></defs>
              <circle cx={75} cy={75} r={32} fill={C.ink} />
              <text style={{ ...F.mono(12.5, 600), letterSpacing: 3.2 }} fill={C.ink}><textPath href="#badgeArc">VERIFY · NO KEY · NO GAS · VERIFY · NO KEY ·</textPath></text>
            </svg>
          </div>
        </Camera>
      </AbsoluteFill>
    </AbsoluteFill>
  );
}
