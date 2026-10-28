// HONEST - "No profit promises. It's paper money on testnet, and zero of six bots have passed the forward test yet."
// Light world. The promise that is NOT made + three plain facts as floating glass tags, then the six bots' real
// forward-test progress (python -X utf8 -m engine.cli ledger fd16, printed 2026-10-07T15:57:15Z: every bot
// "BELUM CUKUP DATA") and a big 0 / 6.
import React from 'react';
import { AbsoluteFill } from 'remotion';
import { At, camAt, Space, withDrift } from '../cam/space';
import { LavWorld } from '../fx/world';
import { Headline } from '../ui/text';
import { appear, Card, Pill } from '../ui/bits';
import { C, rgba } from '../lib/palette';
import { accent, archivo, inter, label, mono } from '../lib/fonts';
import { clamp, ease, noise1, prog } from '../lib/util';
import { at, line } from '../lib/vo';
import type { SceneProps } from '../timeline';

// engine.cli ledger fd16 (7 Oct 15:57Z): signals / settled days / months; passing needs 20 / 20 / 2 and a CI above zero
export const FD16 = [
  { bot: 'B1-TREND', s: 0, d: 0, m: 0 },
  { bot: 'B2-RS', s: 15, d: 0, m: 0 },
  { bot: 'B3-CARRY', s: 4, d: 4, m: 1 },
  { bot: 'B4-LISTING-FADE', s: 4, d: 0, m: 0 },
  { bot: 'B5-CORE-RWA', s: 0, d: 2, m: 1 },
  { bot: 'B6-BOUNCE', s: 0, d: 3, m: 1 },
];

const Bar: React.FC<{ v: number; max: number; k: number; w: number }> = ({ v, max, k, w }) => (
  <div style={{ position: 'relative', width: w, height: 12, borderRadius: 99, background: rgba('lav3', 0.5), overflow: 'hidden' }}>
    <div style={{ position: 'absolute', left: 0, top: 0, bottom: 0, width: Math.max(v > 0 ? 12 : 0, w * clamp(v / max) * k), borderRadius: 99, background: `linear-gradient(90deg, ${C.violet2}, ${C.violet})` }} />
  </div>
);

export const S9Honest: React.FC<SceneProps> = ({ t, t0, t1 }) => {
  const l1 = line('end1'), l2 = line('end2');
  const tZero = at('end2', 'zero');
  const swap = prog(t, l2.start - 0.15, l2.start + 0.55, ease.inOutCubic); // facts leave, the board arrives
  const cam = withDrift(camAt([
    { t: t0, z: -140, rx: 5, ry: 12, x: -40 },
    { t: l2.start, z: -20, rx: 3, ry: 4, x: 0, ez: ease.inOutCubic },
    { t: t1, z: 110, rx: 1, ry: -7, x: 30, ez: ease.inOutCubic },
  ], t), t, 0.8, 21);
  const fill = prog(t, tZero, tZero + 1.6, ease.cine);
  const big = prog(t, at('end2', 'passed') - 0.15, at('end2', 'passed') + 0.55, ease.cine);
  const facts: [string, number][] = [['Paper money', at('end1', 'paper')], ['BNB Chain testnet', at('end1', 'testnet')], ['FAB: a test token, no value', at('end1', 'testnet') + 0.3]];
  return (
    <AbsoluteFill>
      <LavWorld t={t} cam={cam} seed={9} />
      <Space cam={cam} perspective={1700}>
        <At x={-470} y={-120} z={40} ry={10}>
          <div style={{ position: 'absolute', left: -400, top: -130, width: 820, opacity: 1 - swap, transform: `translateX(${-swap * 120}px)` }}>
            <Headline t={t} size={128} col={C.ink}
              segs={[
                { text: 'No profit', at: l1.words[0]!.start, voice: 'calm' },
                { text: 'promises.', at: at('end1', 'promises'), voice: 'accent', br: true },
              ]} />
          </div>
        </At>
        {facts.map(([txt, a], i) => {
          const bob = 10 * noise1(t * 0.6 + i * 2, 40 + i);
          return (
            <At key={i} x={430 + (i - 1) * 60} y={-170 + i * 120 + bob} z={120 - i * 40} ry={-14} rx={4}>
              <div style={{ position: 'absolute', left: -260, top: -36, ...appear(t, a, 0.55, 40), opacity: (appear(t, a, 0.55).opacity as number) * (1 - swap) }}>
                <Pill size={34} icon={<span style={{ width: 14, height: 14, borderRadius: '50%', background: C.violet, display: 'inline-block', boxShadow: `0 0 12px ${rgba('violet', 0.8)}` }} />}>{txt}</Pill>
              </div>
            </At>
          );
        })}
        <At x={-250} y={-30} z={0} ry={9} rx={2}>
          <div style={{ position: 'absolute', left: -520, top: -300, opacity: swap, transform: `translateX(${(1 - swap) * -160}px)` }}>
            <Card w={1040} pad={38}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'baseline' }}>
                <div style={{ ...label(16, 700), color: C.violet }}>Forward test · paper · clock started 2026-10-01</div>
                <div style={{ ...mono(15, 500), color: C.mist }}>to pass: 20 signals · 20 days · 2 months</div>
              </div>
              <div style={{ marginTop: 26, display: 'flex', flexDirection: 'column', gap: 16 }}>
                {FD16.map((r, i) => {
                  const a = prog(t, tZero - 0.4 + i * 0.11, tZero + 0.1 + i * 0.11, ease.cine);
                  return (
                    <div key={r.bot} style={{ display: 'grid', gridTemplateColumns: '250px 1fr 110px', alignItems: 'center', gap: 22, opacity: a, transform: `translateX(${(1 - a) * 30}px)` }}>
                      <div style={{ ...archivo(26, 700, 96), color: C.ink }}>{r.bot}</div>
                      <div style={{ display: 'flex', gap: 16, alignItems: 'center' }}>
                        <Bar v={r.s} max={20} k={fill} w={250} />
                        <Bar v={r.d} max={20} k={fill} w={190} />
                        <Bar v={r.m} max={2} k={fill} w={100} />
                      </div>
                      <div style={{ ...label(12, 700), color: C.mist, textAlign: 'right' }}>not yet</div>
                    </div>
                  );
                })}
              </div>
              <div style={{ marginTop: 16, display: 'flex', ...mono(15, 500), color: C.mist, paddingLeft: 272 }}>
                <span style={{ width: 266 }}>signals</span><span style={{ width: 206 }}>settled days</span><span>months</span>
              </div>
            </Card>
          </div>
        </At>
        <At x={560} y={-40} z={160} ry={-12}>
          <div style={{ position: 'absolute', left: -230, top: -150, width: 460, textAlign: 'center', opacity: big, transform: `scale(${0.8 + 0.2 * big})` }}>
            <div style={{ ...accent(210), color: C.violet, textShadow: `0 20px 60px ${rgba('violet', 0.35)}` }}>0 / 6</div>
            <div style={{ ...inter(30, 600), color: C.ink, marginTop: 6 }}>bots have passed so far</div>
          </div>
        </At>
      </Space>
    </AbsoluteFill>
  );
};
