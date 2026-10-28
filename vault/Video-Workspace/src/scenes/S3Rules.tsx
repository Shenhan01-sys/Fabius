// RULES - "First, the rules. Each bot's strategy is locked on-chain, so it can't be quietly rewritten after a bad day."
// The real /bot/B1-TREND page (capture bot-b1): the rule card lifts out of the page, the "spec locked on-chain" pill
// lifts further and a lock closes on it with the real lock time; an edit is tried and refused; the six bots' rules
// line up as locked tablets with their real lock times (deployments/97.json m3.locks).
import React from 'react';
import { AbsoluteFill } from 'remotion';
import { At, camAt, Space, withDrift } from '../cam/space';
import { LavWorld } from '../fx/world';
import { GlowBlob } from '../fx/fx';
import { Headline } from '../ui/text';
import { BrowserWindow, Clip, geom, PageCrop } from '../ui/browser';
import { Cursor, curAt } from '../ui/cursor';
import { appear, LockIcon, Tag } from '../ui/bits';
import { C, rgba } from '../lib/palette';
import { archivo, inter, label, mono } from '../lib/fonts';
import { bump, clamp, ease, lerp, noise1, prog } from '../lib/util';
import { at, line } from '../lib/vo';
import { capBox, capCursor } from '../data/captures';
import type { SceneProps } from '../timeline';

// deployments/97.json m3.locks (LockRegistry, chain 97)
const LOCKS = [
  { bot: 'B1-TREND', at: '2026-10-02 15:49:20', sha: '0x23cb026b' },
  { bot: 'B2-RS', at: '2026-10-04 16:37:25', sha: '0x2dd6ccf2' },
  { bot: 'B3-CARRY', at: '2026-10-02 15:49:25', sha: '0xc528abf5' },
  { bot: 'B4-LISTING-FADE', at: '2026-10-04 16:37:29', sha: '0x78bb0e32' },
  { bot: 'B5-CORE-RWA', at: '2026-10-04 16:37:34', sha: '0x2dfb0fa4' },
  { bot: 'B6-BOUNCE', at: '2026-10-04 16:37:38', sha: '0x4a6d180d' },
];

const WW = 1180, WH = 780; // window size in the stage
const G = geom(WW, WH);

export const S3Rules: React.FC<SceneProps> = ({ t, t0, t1 }) => {
  const r1 = line('rule1'), r2 = line('rule2');
  const tStrat = at('rule2', 'strategy'), tLocked = at('rule2', 'locked'), tRew = at('rule2', 'rewritten'), tBad = at('rule2', 'bad');
  // capture time: hold the title, then the cursor travels to the lock pill and hovers it (frame 156), then stop
  const f = Math.min(200, Math.max(0, (t - t0) * 60 * 0.9));
  const FC = 160; // the frame we lift crops from (pill hovered, page not yet scrolled)
  const lift = prog(t, tStrat - 0.15, tStrat + 0.6, ease.cine);
  const lift2 = prog(t, tLocked - 0.2, tLocked + 0.45, ease.cine);
  const shut = prog(t, tLocked + 0.15, tLocked + 0.45, ease.outBack);
  const rows = prog(t, tBad - 0.55, tBad + 0.35, ease.cine);
  const cam = withDrift(camAt([
    { t: t0, x: 120, y: 40, z: -260, rx: 4, ry: -22 },
    { t: r1.end, x: 110, y: 60, z: -190, rx: 3, ry: -16, ez: ease.inOutCubic },
    { t: tStrat + 0.4, x: 170, y: 300, z: 200, rx: 8, ry: -6, ez: ease.inOutQuart },
    { t: tRew + 0.3, x: 210, y: 300, z: 270, rx: 8, ry: 4, ez: ease.inOutCubic },
    { t: t1, x: 0, y: 30, z: -80, rx: 6, ry: 6, ez: ease.inOutQuart },
  ], t), t, 0.8, 51);
  const qb = capBox('bot-b1', 'quoteCard', FC), pb = capBox('bot-b1', 'lockPill', FC);
  const qc = G.centre(qb), pc = G.centre(pb);
  const qt = capBox('bot-b1', 'quote', FC);
  const wx = 300, wy = 40; // window position in the stage
  // an edit attempt on the lifted card: our pointer clicks into the quote, characters type and are refused
  const tryT = tRew - 0.55;
  const typed = 'short when…';
  const n = Math.max(0, Math.min(typed.length, Math.floor((t - tryT) * 22)));
  const refused = prog(t, tRew + 0.05, tRew + 0.4);
  const cur = capCursor('bot-b1', f);
  const curOnPage = 1 - prog(t, tStrat - 0.2, tStrat + 0.1);
  const myCur = curAt([{ t: tStrat + 0.6, x: 1500, y: 860 }, { t: tryT - 0.05, x: 1010, y: 610 }, { t: tRew + 0.6, x: 1060, y: 650 }], t);
  return (
    <AbsoluteFill>
      <LavWorld t={t} cam={cam} seed={3} />
      <Space cam={cam} perspective={1650}>
        <At x={wx} y={wy} z={0}>
          <BrowserWindow w={WW} h={WH} url="fabius-one.vercel.app/bot/B1-TREND" dim={0.35 * lift * (1 - rows)} sweep={prog(t, t0 + 0.1, t0 + 1.2)}>
            <Clip name="bot-b1" f={f} />
            <Cursor t={t} x={cur.x * G.s} y={cur.y * G.s} scale={0.85} opacity={curOnPage} />
          </BrowserWindow>
        </At>
        {/* the rule card, lifted out of the page */}
        <At x={wx + qc.x} y={wy + qc.y - 40 * lift} z={170 * lift} rx={-4 * lift}>
          <div style={{ opacity: clamp(lift * 3) * (1 - 0.85 * rows) }}>
            <PageCrop b={qb} s={G.s} clip={{ name: 'bot-b1', f: FC }} lift={lift} glow={0.4 * lift + 0.6 * bump(t, tRew + 0.1, 0.35)} sweep={prog(t, tStrat + 0.1, tStrat + 1.0)} pad={2} />
            {/* the refused edit */}
            {t > tryT && t < tRew + 0.8 ? (
              <div style={{ position: 'absolute', left: (qt.x - qb.x) * G.s - (qb.w * G.s) / 2, top: (qt.y + qt.h - qb.y) * G.s - (qb.h * G.s) / 2 + 2, ...mono(22, 600), color: refused > 0 ? rgba('gap', 1 - refused) : C.violet, opacity: 1 - prog(t, tRew + 0.4, tRew + 0.8) }}>
                {typed.slice(0, n)}<span style={{ display: 'inline-block', width: 3, height: 28, background: C.violet, marginLeft: 2, verticalAlign: -4 }} />
              </div>
            ) : null}
          </div>
        </At>
        {/* the lock pill, lifted further, with a closing lock */}
        <At x={wx + pc.x} y={wy + pc.y - 30 * lift2} z={170 * lift + 140 * lift2}>
          <div style={{ opacity: clamp(lift2 * 3) * (1 - rows) }}>
            <PageCrop b={pb} s={G.s} clip={{ name: 'bot-b1', f: FC }} radius={14} lift={lift2} glow={0.8 * lift2} pad={3} />
            <div style={{ position: 'absolute', left: -pb.w * G.s / 2 - 64, top: -30, transform: `scale(${0.6 + 0.4 * shut})`, filter: `drop-shadow(0 6px 14px ${rgba('violet', 0.5)})` }}><LockIcon s={48} shut={shut} /></div>
            <div style={{ position: 'absolute', left: -pb.w * G.s / 2 - 70, top: 30, ...appear(t, tLocked + 0.35, 0.45), whiteSpace: 'nowrap' }}>
              <Tag size={15}>LockRegistry · locked 2026-10-02 15:49:20 UTC</Tag>
            </div>
          </div>
        </At>
        {/* refused toast */}
        <At x={wx + qc.x + 320} y={wy + qc.y - 170} z={260}>
          <div style={{ position: 'absolute', left: -230, top: -34, opacity: refused * (1 - prog(t, tBad - 0.4, tBad)), transform: `translateY(${(1 - refused) * 14}px)`, display: 'flex', alignItems: 'center', gap: 12, padding: '14px 22px', borderRadius: 16, background: 'rgba(21,18,43,0.92)', color: '#f2efff', boxShadow: `0 20px 50px -14px ${rgba('ink', 0.5)}`, ...inter(20, 600), whiteSpace: 'nowrap' }}>
            <LockIcon s={20} col={C.violet2} /> Write-once. The rule can't be edited.
          </div>
        </At>
        {/* six locked rules */}
        {LOCKS.map((l, i) => {
          const a = prog(t, tBad - 0.55 + i * 0.07, tBad - 0.05 + i * 0.07, ease.cine);
          const x = lerp(-540, 540, i / 5);
          return (
            <At key={l.bot} x={x} y={-30 + 10 * noise1(t * 0.7 + i, 90)} z={360 * rows} ry={-(x / 600) * 14}>
              <div style={{ position: 'absolute', left: -112, top: -80, width: 224, padding: '18px 18px 16px', borderRadius: 20, background: 'rgba(255,255,255,0.88)', border: `1px solid ${rgba('violet', 0.18)}`, boxShadow: `0 24px 60px -18px ${rgba('violet', 0.5)}`, opacity: a, transform: `translateY(${(1 - a) * 60}px) rotateX(${(1 - a) * 30}deg)` }}>
                <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                  <span style={{ ...archivo(i === 0 ? 24 : 21, 800, 92), color: C.ink }}>{l.bot}</span>
                  <LockIcon s={18} />
                </div>
                <div style={{ ...mono(13, 500), color: C.mist, marginTop: 8 }}>spec {l.sha}…</div>
                <div style={{ ...label(11, 700), color: C.violet, marginTop: 6 }}>locked {l.at}</div>
              </div>
            </At>
          );
        })}
      </Space>
      <GlowBlob x={1000} y={560} r={420} col="violet2" a={0.3 * bump(t, tLocked + 0.3, 0.6)} />
      <AbsoluteFill style={{ pointerEvents: 'none' }}>
        <Cursor t={t} x={myCur.x} y={myCur.y} clicks={[tryT - 0.05]} scale={1.15} opacity={clamp((t - tStrat - 0.6) * 3) * (1 - prog(t, tBad - 0.3, tBad))} />
      </AbsoluteFill>
      <AbsoluteFill style={{ padding: '0 0 0 120px', justifyContent: 'center', pointerEvents: 'none' }}>
        <Headline t={t} size={124} out={r1.end + 0.25}
          segs={[{ text: 'First,', at: r1.words[0]!.start, voice: 'calm' }, { text: 'the rules.', at: at('rule1', 'rules') - 0.05, voice: 'accent', br: true }]} />
      </AbsoluteFill>
    </AbsoluteFill>
  );
};
