// OPEN - "Got your own bot, or your own agent? Bring it. It faces the same public gates as ours."
// The real /submit page (capture submit: methods Rule / Code (soon) / Feed) and /submit-agent (live still, 7 Oct), the
// method cards lift out; then your bot and one of Fabius' own bots travel side by side through the same eleven glass
// gates (engine/gates.py G1 PIT ... G11 CAPACITY), each gate lighting as they pass.
import React from 'react';
import { AbsoluteFill } from 'remotion';
import { At, camAt, Space, withDrift } from '../cam/space';
import { LavWorld } from '../fx/world';
import { GlowBlob } from '../fx/fx';
import { Headline } from '../ui/text';
import { BrowserWindow, Clip, geom, PageCrop, Still } from '../ui/browser';
import { Check, LockIcon, Tag } from '../ui/bits';
import { C, rgba } from '../lib/palette';
import { archivo, label, mono } from '../lib/fonts';
import { clamp, ease, lerp, prog } from '../lib/util';
import { at, line } from '../lib/vo';
import { capBox } from '../data/captures';
import type { SceneProps } from '../timeline';

const GATES = ['PIT', 'DATA', 'NET', 'RECENT', 'PLATEAU', 'PHASE', 'FOLD', 'NULL', 'COST', 'MARGINAL', 'CAPACITY'];
const WW = 940, WH = 620;
const G = geom(WW, WH);

const BotCard: React.FC<{ title: string; sub: string; mine?: boolean }> = ({ title, sub, mine }) => (
  <div style={{ position: 'absolute', left: -150, top: -62, width: 300, padding: '18px 22px', borderRadius: 22, background: mine ? `linear-gradient(135deg, ${C.violet}, #4b33c7)` : 'rgba(255,255,255,0.94)', color: mine ? '#fff' : C.ink, border: `1px solid ${mine ? 'rgba(255,255,255,0.35)' : rgba('violet', 0.2)}`, boxShadow: `0 30px 70px -20px ${rgba('violet', 0.65)}` }}>
    <div style={{ ...label(12, 700), color: mine ? 'rgba(255,255,255,0.75)' : C.violet }}>{mine ? 'your bot · rule' : "Fabius' own bot"}</div>
    <div style={{ ...archivo(30, 800, 92), marginTop: 6 }}>{title}</div>
    <div style={{ ...mono(14, 500), marginTop: 4, opacity: 0.75 }}>{sub}</div>
  </div>
);

export const S8Open: React.FC<SceneProps> = ({ t, t0, t1 }) => {
  const o1 = line('open1'), o2 = line('open2');
  const tAgent = at('open1', 'agent'), tBring = at('open1', 'Bring'), tSame = at('open2', 'same'), tOurs = at('open2', 'ours');
  const gatesIn = prog(t, o2.start - 0.45, o2.start + 0.1, ease.cine);
  const travel = prog(t, tSame - 0.25, o2.end + 0.1, ease.inOutCubic); // through the corridor
  const base = withDrift(camAt([
    { t: t0, x: 0, y: -20, z: -260, rx: 4, ry: 0 },
    { t: tBring, x: 0, y: -10, z: -120, rx: 6, ry: 0, ez: ease.inOutCubic },
    { t: o2.start, x: 0, y: 70, z: 0, rx: 8, ry: -8, ez: ease.inOutQuart },
    { t: t1, x: 0, y: 80, z: 0, rx: 6, ry: 6, ez: ease.inOutCubic },
  ], t), t, 0.7, 81);
  // fly with the two cards: the camera dollies forward as they travel, so the gates stream past
  const cam = { ...base, z: base.z + 2500 * travel };
  const fSub = Math.min(479, Math.max(0, (t - t0) * 60 * 0.9 + 60));
  const cards = ['cardRule', 'cardCode', 'cardFeed'].map((k, i) => ({ k, b: capBox('submit', k, 160), a: prog(t, tAgent - 0.6 + i * 0.12, tAgent - 0.1 + i * 0.12, ease.cine) }));
  const winOut = prog(t, o2.start - 0.4, o2.start + 0.3, ease.inCubic);
  return (
    <AbsoluteFill>
      <LavWorld t={t} cam={cam} seed={8} />
      <Space cam={cam} perspective={1600}>
        {/* the two doors */}
        <At x={-500} y={-40} z={-60 - 600 * winOut} ry={14}>
          <div style={{ opacity: 1 - winOut }}>
            <BrowserWindow w={WW} h={WH} url="fabius-one.vercel.app/submit" sweep={prog(t, t0 + 0.1, t0 + 1.2)}>
              <Clip name="submit" f={fSub} />
            </BrowserWindow>
          </div>
        </At>
        <At x={500} y={-40} z={-60 - 600 * winOut} ry={-14}>
          <div style={{ opacity: 1 - winOut }}>
            <BrowserWindow w={WW} h={WH} url="fabius-one.vercel.app/submit-agent" sweep={prog(t, t0 + 0.3, t0 + 1.4)}>
              <Still src="web/stills/submit-agent-top.jpg" parentW={WW} />
            </BrowserWindow>
          </div>
        </At>
        {cards.map(({ k, b, a }, i) => {
          const c = G.centre(b);
          return (
            <At key={k} x={-500 + c.x * 1.0 + (i - 1) * 40 * a} y={-40 + c.y - 140 * a} z={-60 + 200 * a} ry={14 - 10 * a}>
              <div style={{ opacity: clamp(a * 3) * (1 - winOut) }}>
                <PageCrop b={b} s={G.s * 1.3} clip={{ name: 'submit', f: 160 }} radius={16} lift={a} glow={0.5 * a} pad={3} />
              </div>
            </At>
          );
        })}
        {/* the same eleven gates */}
        {GATES.map((g, i) => {
          const z = -i * 260;
          const lit = clamp((travel * 11 - i) * 1.5);
          return (
            <At key={g} x={0} y={60} z={z} >
              <div style={{ position: 'absolute', left: -470, top: -300, width: 940, height: 600, borderRadius: 40, border: `${3 + 3 * lit}px solid ${lit > 0.5 ? rgba('violet', 0.9) : 'rgba(255,255,255,0.85)'}`, background: `linear-gradient(135deg, rgba(255,255,255,${0.14 + 0.1 * lit}), rgba(201,189,242,${0.08 + 0.12 * lit}))`, boxShadow: lit > 0.5 ? `0 0 60px ${rgba('violet2', 0.6 * lit)}, inset 0 0 50px ${rgba('violet2', 0.35 * lit)}` : `0 0 30px ${rgba('violet', 0.15)}`, opacity: gatesIn * (1 - 0.06 * i) }}>
                <div style={{ position: 'absolute', left: 26, top: 22, display: 'flex', alignItems: 'center', gap: 10 }}>
                  <span style={{ ...archivo(30, 800, 90), color: lit > 0.5 ? C.violet : C.ink }}>G{i + 1}</span>
                  <span style={{ ...label(15, 700), color: C.mist }}>{g}</span>
                  {lit > 0.5 ? <Check s={26} k={lit} /> : null}
                </div>
              </div>
            </At>
          );
        })}
        {/* your bot and Fabius' bot, side by side through the gates */}
        <At x={lerp(-260, -200, travel)} y={110} z={lerp(260, -2240, travel)} >
          <div style={{ opacity: prog(t, tBring - 0.1, tBring + 0.35) }}><BotCard title="your-bot" sub="your rule · signed with your wallet" mine /></div>
        </At>
        <At x={lerp(260, 200, travel)} y={110} z={lerp(260, -2240, travel)}>
          <div style={{ opacity: prog(t, tBring + 0.1, tBring + 0.45) }}><BotCard title="B3-CARRY" sub="spec 0xc528abf5… · locked" /></div>
        </At>
      </Space>
      <GlowBlob x={960} y={600} r={500} col="violet2" a={0.2 * gatesIn} />
      <div style={{ position: 'absolute', left: 0, right: 0, top: 70, display: 'flex', justifyContent: 'center', gap: 14, opacity: prog(t, tOurs - 0.2, tOurs + 0.3) }}>
        <Tag size={18}><LockIcon s={16} /> same gates · same public reports</Tag>
        <Tag size={18}>then 60 days forward on paper before a slot</Tag>
      </div>
      <AbsoluteFill style={{ padding: '0 0 0 0', justifyContent: 'center', alignItems: 'center', pointerEvents: 'none' }}>
        <div style={{ marginTop: -40, opacity: 1 - prog(t, o2.start - 0.4, o2.start) }}>
          <Headline t={t} size={128} align="center" segs={[{ text: 'Bring', at: tBring - 0.05, voice: 'calm' }, { text: 'it.', at: at('open1', 'it') - 0.05, voice: 'accent' }]} />
        </div>
      </AbsoluteFill>
    </AbsoluteFill>
  );
};
