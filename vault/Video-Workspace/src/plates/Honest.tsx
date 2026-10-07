// 10 HONEST — "Because here's what we don't claim: profit. / The forward clock started on October 1st. / To pass,
// a bot needs 20 signals, 20 days, 2 months, and a confidence interval above zero. / Today, zero of six have passed."
// PROFIT is struck out (the web's marquee runs underneath); the real "track record, day by day" page with its clock
// started 2026-10-01; four glass tanks for the F-D16 conditions; the six bots' real progress
// (python -X utf8 -m engine.cli ledger fd16, 06 Oct) and 0 / 6.
import React from 'react';
import { AbsoluteFill } from 'remotion';
import type { PlateProps } from '../timeline';
import { C, rgba } from '../lib/palette';
import { F } from '../lib/fonts';
import { lineOf, wordOf } from '../lib/lyrics';
import { clamp, ease, env, hash, lerp, prog, pulse, shake } from '../lib/util';
import { Karaoke, LavBg, GraphPaper, Mono, span, stampStyle, StampBox, W, H } from '../components/kit';
import { Ambient, Camera, type CamKey } from '../components/camera';
import { BrowserFrame } from '../components/devices';

const L24 = lineOf('Because here');
const L25 = lineOf('The forward clock');
const L26 = lineOf('To pass, a bot needs');
const L27 = lineOf('Today, zero of six');
const w24 = (q: string) => wordOf(L24, q), w25 = (q: string) => wordOf(L25, q), w26 = (q: string) => wordOf(L26, q), w27 = (q: string) => wordOf(L27, q);

// engine.cli ledger fd16 (06 Oct 2026): forward signals / settled days / months, per bot
const FD = [
  { id: 'B1-TREND', s: 0, d: 0, m: 0 }, { id: 'B2-RS', s: 10, d: 0, m: 0 }, { id: 'B3-CARRY', s: 4, d: 3, m: 1 },
  { id: 'B4-LISTING-FADE', s: 1, d: 0, m: 0 }, { id: 'B5-CORE-RWA', s: 0, d: 1, m: 1 }, { id: 'B6-BOUNCE', s: 0, d: 2, m: 1 },
];
const MARQUEE = 'PAPER ONLY · NO EDGE CLAIMED · F-D16 NOT MET · VERIFY, DON’T TRUST · ';

const Tank: React.FC<{ x: number; y: number; level: number; label: string; sub: string; a: number }> = ({ x, y, level, label, sub, a }) => (
  <div style={{ position: 'absolute', left: x, top: y, width: 300, opacity: a, transform: `translateY(${(1 - a) * 50}px) scale(${0.9 + 0.1 * a})` }}>
    <div style={{ position: 'relative', width: 150, height: 330, margin: '0 auto', borderRadius: 75, background: 'linear-gradient(90deg, rgba(255,255,255,0.75), rgba(255,255,255,0.35) 60%, rgba(255,255,255,0.65))', border: '1px solid rgba(255,255,255,0.9)', boxShadow: '0 24px 60px -28px rgba(62,37,160,0.45), 0 1px 0 #fff inset', overflow: 'hidden' }}>
      <div style={{ position: 'absolute', left: 0, right: 0, bottom: 0, height: `${clamp(level) * 100}%`, background: `linear-gradient(180deg, ${C.violet2}, ${C.violet})` }} />
      <div style={{ position: 'absolute', left: 14, top: 14, width: 14, bottom: 14, borderRadius: 7, background: 'rgba(255,255,255,0.55)' }} />
    </div>
    <div style={{ textAlign: 'center', marginTop: 14, ...F.archivo(30, 900, 105), color: C.ink }}>{label}</div>
    <div style={{ textAlign: 'center', ...F.mono(13, 500), color: rgba('ink', 0.6) }}>{sub}</div>
  </div>
);

export default function Honest({ t, start, end }: PlateProps) {
  const tProfit = w24('profit.').start, tStrike = tProfit + 0.45;
  const tClock = w25('clock').start, tOct = w25('October').start;
  const tS = w26('signals,').start, tD = w26('days,').start, tM = w26('months,').start, tCI = w26('confidence').start;
  const tToday = L27.start, tPassed = w27('passed.').start;
  const sh = shake(t, 9 * pulse(t, tStrike + 0.12, 0.05) + 7 * pulse(t, tPassed + 0.1, 0.05));
  const beat1 = 1 - prog(t, L25.start - 0.35, L25.start);
  const beat2 = env(t, L25.start - 0.3, L26.start + 0.1, 0.35, 0.35);
  const tanksA = env(t, L26.start - 0.2, tToday + 0.15, 0.3, 0.3);

  const cam: CamKey[] = [
    { t: start - 0.4, s: 1.1 },
    { t: tProfit, s: 1.0 },
    { t: tStrike + 0.15, s: 1.05, ez: ease.outQuart },
    { t: L25.start, s: 1.0 },
    { t: L26.start - 0.1, s: 1.04, rx: 6, y: 10 },
    { t: tToday, s: 1.0, rx: 0, y: 0 },
    { t: end + 0.3, s: 1.08 },
  ];
  // the strike: a rough marker line across PROFIT
  const strikeK = prog(t, tStrike, tStrike + 0.28, ease.outQuad);
  const pts = Array.from({ length: 30 }, (_, i) => ({ x: lerp(560, 1360, i / 29), y: 540 + (hash(i, 7) - 0.5) * 10 + (i / 29) * -18 }));

  return (
    <AbsoluteFill>
      <LavBg />
      <Camera t={t} keys={cam} depth={0.3}><Ambient t={t} light seed={11} n={6} dust={20} cubes={9} /></Camera>
      <Camera t={t} keys={cam}>
        <AbsoluteFill style={{ transform: `translate(${sh[0]}px, ${sh[1]}px)` }}>
          <GraphPaper paper opacity={0.4} />
          {/* beat 1: PROFIT, struck out */}
          <div style={{ position: 'absolute', left: 0, right: 0, top: 410, textAlign: 'center', opacity: beat1 * prog(t, tProfit - 0.1, tProfit + 0.15), transform: `scale(${1 + 0.05 * pulse(t, tProfit, 0.1)})` }}>
            <span style={{ ...F.archivo(250, 900, 125), color: C.ink, letterSpacing: -2 }}>PROFIT</span>
          </div>
          <svg width={W} height={H} style={{ position: 'absolute', inset: 0, opacity: beat1 }}>
            {strikeK > 0 && <path d={'M' + pts.slice(0, Math.max(2, Math.ceil(30 * strikeK))).map((p) => `${p.x} ${p.y}`).join('L')} fill="none" stroke={C.gap} strokeWidth={30} strokeLinecap="round" strokeLinejoin="round" opacity={0.92} />}
          </svg>
          <div style={{ position: 'absolute', left: 0, right: 0, top: 800, height: 64, overflow: 'hidden', background: C.ink, opacity: beat1 * prog(t, tStrike, tStrike + 0.3), display: 'flex', alignItems: 'center' }}>
            <div style={{ whiteSpace: 'nowrap', ...F.mono(22, 600), letterSpacing: 4, color: C.lav, transform: `translateX(${-((t - start) * 140) % 1200}px)` }}>{MARQUEE.repeat(6)}</div>
          </div>

          {/* beat 2: the forward clock (the real track-record page) */}
          <div style={{ position: 'absolute', left: 300, top: 250, opacity: beat2, transform: `perspective(1800px) rotateX(${lerp(14, 6, prog(t, tClock, tOct + 1))}deg) translateY(${(1 - prog(t, L25.start - 0.3, L25.start + 0.3, ease.outCubic)) * 120}px)`, transformOrigin: '50% 100%' }}>
            <BrowserFrame src="ui/sec-record.jpg" url="fabius-one.vercel.app/#proof-feed" w={1320} h={760} imgW={2160} scroll={lerp(0, 160, prog(t, tClock, L26.start))} glint={prog(t, tClock, tClock + 1.0)} />
          </div>
          <div style={{ position: 'absolute', left: 1230, top: 214, opacity: beat2 * prog(t, tOct, tOct + 0.3), transform: `scale(${1 + 0.1 * pulse(t, tOct, 0.1)})` }}>
            <div style={{ borderRadius: 18, background: C.violet, padding: '14px 22px', ...F.mono(20, 600), color: C.lav, letterSpacing: 2, boxShadow: `0 20px 50px -20px ${rgba('violet', 0.8)}` }}>CLOCK STARTED · 2026-10-01</div>
          </div>

          {/* beat 3: the F-D16 tanks (best progress among the six) */}
          <div style={{ opacity: tanksA }}>
            <Tank x={190} y={300} level={10 / 20} label="20 SIGNALS" sub="best so far 10 / 20 (B2-RS)" a={prog(t, tS - 0.1, tS + 0.3, ease.outBack)} />
            <Tank x={590} y={300} level={3 / 20} label="20 DAYS" sub="best so far 3 / 20 (B3-CARRY)" a={prog(t, tD - 0.1, tD + 0.3, ease.outBack)} />
            <Tank x={990} y={300} level={1 / 2} label="2 MONTHS" sub="best so far 1 / 2" a={prog(t, tM - 0.1, tM + 0.3, ease.outBack)} />
            <Tank x={1390} y={300} level={0} label="CI > 0" sub="95% lower bound above zero: not yet" a={prog(t, tCI - 0.1, tCI + 0.3, ease.outBack)} />
          </div>

          {/* beat 4: the six, and the count */}
          <div style={{ position: 'absolute', left: 300, top: 300, width: 1320, opacity: prog(t, tToday - 0.2, tToday + 0.2) }}>
            {FD.map((b, i) => {
              const a = prog(t, tToday + 0.06 * i, tToday + 0.06 * i + 0.3, ease.outCubic);
              return (
                <div key={b.id} style={{ display: 'flex', alignItems: 'center', height: 78, borderBottom: `1px solid ${rgba('ink', 0.12)}`, opacity: a, transform: `translateX(${(1 - a) * 40}px)` }}>
                  <div style={{ width: 330, ...F.archivo(30, 850, 100), color: C.ink }}>{b.id}</div>
                  {[['signals', b.s, 20], ['days', b.d, 20], ['months', b.m, 2]].map(([k, v, n]) => (
                    <div key={k as string} style={{ width: 230, display: 'flex', alignItems: 'center', gap: 12 }}>
                      <div style={{ width: 120, height: 12, borderRadius: 6, background: rgba('ink', 0.1), overflow: 'hidden' }}><div style={{ width: `${((v as number) / (n as number)) * 100 * a}%`, height: '100%', background: C.violet }} /></div>
                      <span style={{ ...F.mono(15, 500), color: rgba('ink', 0.7) }}>{v as number}/{n as number} {k as string}</span>
                    </div>
                  ))}
                  <div style={{ marginLeft: 'auto', ...F.mono(14, 600), letterSpacing: 1.5, color: C.gap }}>NOT ENOUGH DATA</div>
                </div>
              );
            })}
          </div>
          <div style={{ position: 'absolute', left: 0, right: 0, top: 800, textAlign: 'center', ...stampStyle(t, tPassed + 0.05, -3) }}>
            <StampBox col={C.ink} size={64}>0 / 6 passed</StampBox>
          </div>
        </AbsoluteFill>
      </Camera>

      <Camera t={t} keys={[]} drift={0.4}>
        <div style={{ position: 'absolute', left: 150, right: 150, top: 230, opacity: beat1 }}>
          <Karaoke t={t} words={span(L24, 0, 5)} st={{ font: F.serif(96, 500), light: true }} align="center" />
        </div>
        <div style={{ position: 'absolute', left: 150, right: 150, top: 120, opacity: beat2 }}>
          <Karaoke t={t} words={L25.words} st={{ font: F.archivo(60, 900, 105), light: true }} align="center" />
        </div>
        <div style={{ position: 'absolute', left: 150, right: 150, top: 120, opacity: tanksA }}>
          <Karaoke t={t} words={span(L26, 0, 4)} st={{ font: F.archivo(56, 900, 105), light: true }} align="center" />
          <div style={{ height: 8 }} />
          <Karaoke t={t} words={span(L26, 5)} st={{ font: F.serif(52, 500), light: true }} align="center" wrap />
        </div>
        <div style={{ position: 'absolute', left: 150, right: 150, top: 150, opacity: prog(t, tToday - 0.2, tToday + 0.2) }}>
          <Karaoke t={t} words={L27.words} st={{ font: F.archivo(72, 900, 110), light: true, hot: 'gap' }} align="center" />
        </div>
        <div style={{ position: 'absolute', left: 0, right: 0, top: 800, textAlign: 'center', opacity: tanksA * prog(t, tCI + 0.4, tCI + 0.8) }}>
          <Mono size={14} col={rgba('ink', 0.6)}>forward only: settled days after the clock started · 95% block-bootstrap CI · best month dropped · BH across bots</Mono>
        </div>
      </Camera>
    </AbsoluteFill>
  );
}
