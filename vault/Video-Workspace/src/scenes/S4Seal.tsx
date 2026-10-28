// SEAL - "Every day, the candle closes, the bot makes its call, and Fabius seals it with a timestamp no one can
// change. Not even us."
// The site's journey ("From candle close to proof") staged as objects: a glass candle closes at 00:00 UTC, the bot
// turns it into a decision block, the block seals (indigo) and docks onto a chain of blocks with its time; a hand
// tries to drag it and it does not move. Real values: B1-TREND bar 2026-10-06, `python -X utf8 tools/verify_signals.py
// --json` on the origin/master ledger (7 Oct 16:25Z): SAH, committed 36,402 s after the close (2026-10-07 10:06:42
// UTC), commit id 0xc73c4df3…; spec sha 0x23cb026b… (ledger/paper/B1-TREND.jsonl).
import React from 'react';
import { AbsoluteFill } from 'remotion';
import { At, camAt, Space, withDrift } from '../cam/space';
import { LavWorld } from '../fx/world';
import { GlowBlob, Sweep } from '../fx/fx';
import { Headline, Label } from '../ui/text';
import { Cursor, curAt } from '../ui/cursor';
import { BrowserWindow, Clip } from '../ui/browser';
import { pw } from './S2Reveal';
import { appear, LockIcon, Tag } from '../ui/bits';
import { C, rgba } from '../lib/palette';
import { archivo, inter, label, mono } from '../lib/fonts';
import { bump, clamp, ease, lerp, noise1, prog } from '../lib/util';
import { at, line } from '../lib/vo';
import type { SceneProps } from '../timeline';

/** A glass block (CSS 3D cube): empty / sealed / open, the site's three states. */
export const GlassBlock: React.FC<{ s: number; seal: number; glow?: number; rx?: number; ry?: number; children?: React.ReactNode }> = ({ s, seal, glow = 0, rx = -18, ry = 32, children }) => {
  const h = s / 2;
  const face = (tf: string, shade: number, front = false) => {
    const clear = `linear-gradient(135deg, rgba(255,255,255,${0.82 - 0.25 * shade}), rgba(221,213,246,${0.55 - 0.2 * shade}))`;
    const ind = `linear-gradient(135deg, rgba(${Math.round(58 + 30 * (1 - shade))},${Math.round(38 + 20 * (1 - shade))},${Math.round(170 + 30 * (1 - shade))},0.96), rgba(26,18,94,0.98))`;
    return (
      <div style={{ position: 'absolute', left: -h, top: -h, width: s, height: s, transform: tf, borderRadius: s * 0.1, background: seal > 0.5 ? ind : clear, border: `${Math.max(1, s * 0.012)}px solid ${seal > 0.5 ? rgba('violet2', 0.9) : 'rgba(255,255,255,0.95)'}`, boxShadow: `inset 0 0 ${s * 0.3}px ${rgba(seal > 0.5 ? 'violet' : 'white', 0.55)}${glow ? `, 0 0 ${s * 0.6 * glow}px ${rgba('violet2', 0.8 * glow)}` : ''}`, backfaceVisibility: 'hidden' }}>
        {front ? children : null}
      </div>
    );
  };
  return (
    <div style={{ position: 'absolute', left: 0, top: 0, width: 0, height: 0, transformStyle: 'preserve-3d', transform: `rotateX(${rx}deg) rotateY(${ry}deg)` }}>
      {face(`rotateY(180deg) translateZ(${h}px)`, 0.8)}
      {face(`rotateY(-90deg) translateZ(${h}px)`, 0.55)}
      {face(`rotateX(90deg) translateZ(${h}px)`, 0.1)}
      {face(`rotateX(-90deg) translateZ(${h}px)`, 0.9)}
      {face(`rotateY(90deg) translateZ(${h}px)`, 0.4)}
      {face(`translateZ(${h}px)`, 0.2, true)}
    </div>
  );
};

/** A daily candlestick made of glass; `close` 0..1 = the body settling as the bar closes. */
const Candle: React.FC<{ t: number; close: number; up?: boolean }> = ({ close, up = true }) => {
  const bodyH = 220 * (0.45 + 0.55 * ease.outCubic(close));
  const col = up ? '#22b07d' : C.gap;
  return (
    <div style={{ position: 'absolute', left: -50, top: -260, width: 100, height: 520 }}>
      <div style={{ position: 'absolute', left: 47, top: 20, width: 6, height: 480, borderRadius: 3, background: `linear-gradient(180deg, ${rgba('ink', 0.15)}, ${rgba('ink', 0.4)}, ${rgba('ink', 0.15)})` }} />
      <div style={{ position: 'absolute', left: 6, top: 260 - bodyH / 2, width: 88, height: bodyH, borderRadius: 14, background: `linear-gradient(135deg, rgba(255,255,255,0.65), ${col})`, border: '1.5px solid rgba(255,255,255,0.9)', boxShadow: `0 30px 70px -20px ${rgba(col, 0.6)}, inset 0 0 30px rgba(255,255,255,0.4)` }} />
    </div>
  );
};

export const S4Seal: React.FC<SceneProps> = ({ t, t0, t1 }) => {
  const l1 = line('seal1'), l2 = line('seal2');
  const tDay = l1.words[0]!.start, tCandle = at('seal1', 'candle'), tCloses = at('seal1', 'closes'), tBot = at('seal1', 'bot'), tCall = at('seal1', 'call');
  const tSeals = at('seal2', 'seals'), tStamp = at('seal2', 'timestamp'), tChange = at('seal2', 'change'), tNot = at('seal2', 'Not');
  const cam = withDrift(camAt([
    { t: t0, x: -420, y: 0, z: -60, rx: 6, ry: 18 },
    { t: tBot, x: -120, y: -10, z: 40, rx: 4, ry: 8, ez: ease.inOutCubic },
    { t: tSeals + 0.2, x: 120, y: -20, z: 160, rx: 3, ry: -4, ez: ease.inOutQuart },
    { t: tChange, x: 380, y: -10, z: 120, rx: 8, ry: -16, ez: ease.inOutCubic },
    { t: t1, x: 420, y: 0, z: 40, rx: 10, ry: -22, ez: ease.inOutCubic },
  ], t), t, 0.8, 41);
  const close = prog(t, tCloses - 0.1, tCloses + 0.7);
  const decide = prog(t, tBot - 0.1, tCall + 0.3, ease.cine);
  const seal = prog(t, tSeals - 0.05, tSeals + 0.35, ease.inOutCubic);
  const dock = prog(t, tStamp - 0.2, tStamp + 0.9, ease.inOutQuart);
  // the decision block travels: candle -> centre -> docks onto the chain (right)
  const bx = lerp(lerp(-430, -60, decide), 470, dock), by = lerp(lerp(-40, -40, decide), 40, dock), bz = lerp(lerp(40, 160, decide), 0, dock);
  const tug = t > tChange - 0.3 && t < tNot + 0.2 ? 10 * Math.sin((t - tChange) * 9) * bump(t, tChange + 0.45, 0.7) : 0;
  const chain = Array.from({ length: 5 }, (_, i) => i);
  const curKeys = [{ t: tChange - 0.7, x: 1380, y: 840 }, { t: tChange - 0.05, x: 1070, y: 560 }, { t: tChange + 0.6, x: 1180, y: 600 }, { t: tNot + 0.3, x: 1240, y: 760 }];
  const cur = curAt(curKeys, t);
  const curOn = clamp((t - (tChange - 0.7)) * 3) * (1 - prog(t, tNot + 0.3, tNot + 0.6));
  return (
    <AbsoluteFill>
      <LavWorld t={t} cam={cam} seed={4} />
      <Space cam={cam} perspective={1500}>
        {/* the real page behind: "From candle close to proof", stations in step with the words (capture home-journey) */}
        <At x={60} y={-90} z={-900} ry={10} rx={2}>
          <div style={{ filter: 'blur(1.6px)', opacity: 0.92 }}>
            <BrowserWindow w={1500} h={940} url="fabius-one.vercel.app · How it works" dark>
              <Clip name="home-journey" f={pw(t, [[t0, 0], [tCandle, 40], [tBot, 135], [tSeals, 258], [tStamp + 0.4, 381], [t1, 470]])} />
            </BrowserWindow>
          </div>
        </At>
        {/* time label */}
        <At x={-430} y={330} z={60}>
          <div style={{ position: 'absolute', left: -150, top: -26, width: 300, textAlign: 'center', ...appear(t, tDay - 0.1, 0.5) }}>
            <Label t={t} at={tDay} text="Daily bar · 00:00 UTC" size={18} />
          </div>
        </At>
        {/* the candle */}
        <At x={-430} y={30} z={0} ry={12}>
          <div style={{ ...appear(t, tCandle - 0.3, 0.6, 40), opacity: (appear(t, tCandle - 0.3, 0.6).opacity as number) * (1 - 0.6 * dock) }}>
            <div style={{ transform: 'scale(1.25)' }}><Candle t={t} close={close} /></div>
          </div>
          <div style={{ position: 'absolute', left: -110, top: -300, width: 220, textAlign: 'center', ...label(15, 700), color: C.violet, opacity: close }}>closed</div>
        </At>
        {/* the bot */}
        <At x={-60} y={150} z={200}>
          <div style={{ position: 'absolute', left: -150, top: -40, ...appear(t, tBot - 0.2, 0.5) , opacity: (appear(t, tBot - 0.2, 0.5).opacity as number) * (1 - dock) }}>
            <Tag size={20}>B1-TREND · locked rule · spec 0x23cb026b…</Tag>
          </div>
        </At>
        {/* the chain of blocks: older blocks recede up and back, linked */}
        {chain.slice(0, 4).map((i) => {
          const back = 4 - i;
          return (
            <At key={i} x={470 + back * 165} y={40 - back * 55} z={-back * 230}>
              <div style={{ opacity: 0.55 + 0.1 * i, ...appear(t, tSeals - 0.7 + i * 0.08, 0.6, 20) }}>
                <GlassBlock s={170} seal={1} ry={26 + 2 * noise1(t * 0.4, i)} />
              </div>
            </At>
          );
        })}
        {chain.slice(0, 4).map((i) => {
          const back = 4 - i;
          return (
            <At key={`l${i}`} x={470 + (back - 0.5) * 165} y={40 - (back - 0.5) * 55} z={-(back - 0.5) * 230}>
              <div style={{ position: 'absolute', left: -6, top: -6, width: 12, height: 12, borderRadius: 6, background: C.violet2, boxShadow: `0 0 14px ${rgba('violet2', 0.9)}`, opacity: prog(t, tSeals - 0.3, tSeals + 0.3) * (back === 1 ? dock : 1) }} />
            </At>
          );
        })}
        {/* the decision block */}
        <At x={bx} y={by + tug * 0.3} z={bz} >
          <div style={{ opacity: decide, transform: `translateX(${tug}px)` }}>
            <GlassBlock s={220} seal={seal} glow={bump(t, tSeals + 0.2, 0.5) + 0.3 * seal} ry={30 + 20 * (1 - decide)}>
              <div style={{ position: 'absolute', inset: 0, display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', gap: 6 }}>
                <div style={{ ...label(13, 700), color: seal > 0.5 ? C.lav : C.violet }}>{seal > 0.5 ? 'sealed' : 'signal'}</div>
                <div style={{ ...archivo(22, 800, 90), color: seal > 0.5 ? '#fff' : C.ink }}>bar 10-06</div>
              </div>
            </GlassBlock>
          </div>
        </At>
        {/* timestamp + hashes */}
        <At x={470} y={-250} z={60}>
          <div style={{ position: 'absolute', left: -260, top: -60, width: 520, ...appear(t, tStamp, 0.5) }}>
            <div style={{ padding: '16px 22px', borderRadius: 18, background: 'rgba(255,255,255,0.9)', border: `1px solid ${rgba('violet', 0.2)}`, boxShadow: `0 24px 60px -20px ${rgba('violet', 0.5)}` }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}><LockIcon s={20} /><span style={{ ...label(14, 700), color: C.violet }}>sealed on BNB Chain · block time</span></div>
              <div style={{ ...mono(18, 600), color: C.ink, marginTop: 8 }}>2026-10-07 10:06:42 UTC</div>
              <div style={{ ...mono(14, 500), color: C.mist, marginTop: 4 }}>B1-TREND · bar 2026-10-06 · commit 0xc73c4df3…</div>
            </div>
          </div>
        </At>
      </Space>
      <GlowBlob x={960 + (bx - cam.x) * 0.8} y={540} r={360} col="violet2" a={0.35 * bump(t, tSeals + 0.15, 0.6)} />
      <AbsoluteFill style={{ pointerEvents: 'none' }}>
        <Cursor t={t} x={cur.x} y={cur.y} clicks={[tChange - 0.05]} scale={1.2} opacity={curOn} />
      </AbsoluteFill>
      <AbsoluteFill style={{ justifyContent: 'flex-end', alignItems: 'flex-end', padding: '0 140px 190px 0', pointerEvents: 'none' }}>
        <Headline t={t} size={120} align="right" segs={[{ text: 'Not even', at: tNot, voice: 'calm' }, { text: 'us.', at: at('seal2', 'us'), voice: 'accent' }]} />
      </AbsoluteFill>
      <div style={{ position: 'absolute', inset: 0, pointerEvents: 'none' }}><Sweep k={prog(t, tSeals, tSeals + 0.9)} width={18} strength={0.3} /></div>
    </AbsoluteFill>
  );
};
