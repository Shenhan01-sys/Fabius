// 07 SPLIT — "The AI picks the rulebook. Code computes the position."
// Left (violet, the AI): a fan of the six locked rulebooks; one lifts out; the real /analysts page on a phone
// (picks for the bar closing 06 Oct: B1-TREND). Right (night, the code): the locked rule runs and returns a
// paper position (F-D112: direction is computed by the bot's locked rule, never by the model).
import React from 'react';
import { AbsoluteFill } from 'remotion';
import type { PlateProps } from '../timeline';
import { C, rgba } from '../lib/palette';
import { F } from '../lib/fonts';
import { lineOf, wordOf } from '../lib/lyrics';
import { clamp, ease, prog, pulse } from '../lib/util';
import { Karaoke, Mono, span, Typer } from '../components/kit';
import { Ambient, Camera, type CamKey } from '../components/camera';
import { PhoneFrame } from '../components/devices';

const L18 = lineOf('The AI picks the rulebook');
const w = (q: string) => wordOf(L18, q);
const BOTS = ['B1-TREND', 'B2-RS', 'B3-CARRY', 'B4-LISTING-FADE', 'B5-CORE-RWA', 'B6-BOUNCE'];
const CODE = [
  { t: '# B1-TREND · spec 0x23cb026b… (locked)', c: 'mist' },
  { t: 'if close[t] > close[t − 60]:  LONG', c: 'lav' },
  { t: 'else:                        FLAT', c: 'lav' },
  { t: 'size  3% + 2%·c   lev ≤ 5x   max 5 slots', c: 'violet2' },
  { t: 'exit  SL −1 ATR · TP +2 ATR · or the rule', c: 'violet2' },
];

export default function Split({ t, start, end }: PlateProps) {
  const tPick = w('picks').start, tCode = w('Code').start, tPos = w('position').start;
  const open = prog(t, start - 0.15, start + 0.45, ease.outQuart);
  const cam: CamKey[] = [{ t: start - 0.2, s: 1.08 }, { t: end + 0.3, s: 1.0 }];
  const lift = prog(t, tPick, tPick + 0.45, ease.outBack);

  return (
    <AbsoluteFill>
      {/* left: the AI */}
      <AbsoluteFill style={{ clipPath: `inset(0 ${50 + 50 * (1 - open)}% 0 0)` }}>
        <AbsoluteFill style={{ background: `radial-gradient(ellipse 80% 80% at 30% 40%, ${C.violet} 0%, #3a24b0 60%, ${C.night2} 100%)` }} />
        <Camera t={t} keys={cam} depth={0.4}><Ambient t={t} seed={8} n={4} dust={20} /></Camera>
        <Camera t={t} keys={cam}>
          {/* the fan of rulebooks */}
          {BOTS.map((b, i) => {
            const chosen = i === 0;
            const a = (i - 2.5) * 9;
            const up = chosen ? lift : 0;
            return (
              <div key={b} style={{ position: 'absolute', left: 120 + i * 18, top: 600, width: 250, height: 330, borderRadius: 22, transformOrigin: '50% 120%',
                transform: `rotate(${a * (1 - up)}deg) translate(${up * 40}px, ${-up * 130}px) scale(${1 + up * 0.1})`,
                background: chosen ? 'linear-gradient(160deg, #ffffff, #e4dcff)' : 'linear-gradient(160deg, rgba(255,255,255,0.22), rgba(255,255,255,0.06))',
                border: `1px solid ${chosen ? 'rgba(255,255,255,0.9)' : 'rgba(255,255,255,0.3)'}`, boxShadow: chosen ? `0 30px 70px -20px rgba(10,6,40,0.7), 0 0 ${40 * up}px ${rgba('lav', 0.6 * up)}` : '0 20px 40px -20px rgba(10,6,40,0.6)',
                padding: 22, boxSizing: 'border-box', zIndex: chosen ? 10 : i }}>
                <div style={{ ...F.mono(12, 600), letterSpacing: 2, color: chosen ? C.violet : rgba('lav', 0.7) }}>LOCKED RULEBOOK</div>
                <div style={{ ...F.archivo(30, 900, 100), color: chosen ? C.ink : C.lav, marginTop: 12, lineHeight: 1.05 }}>{b}</div>
                <div style={{ position: 'absolute', left: 22, bottom: 20, ...F.mono(12, 500), color: chosen ? rgba('ink', 0.6) : rgba('lav', 0.6) }}>🔒 on chain 97</div>
              </div>
            );
          })}
          <PhoneFrame src="ui/analysts-m-top.jpg" w={300} glint={prog(t, start + 0.3, start + 1.2)} style={{ left: 600, top: 300, transform: `rotate(6deg) translateY(${(1 - open) * 120}px)`, opacity: open }} />
        </Camera>
        <div style={{ position: 'absolute', left: 120, top: 150, width: 720 }}>
          <Karaoke t={t} words={span(L18, 0, 4)} st={{ font: F.archivo(76, 900, 105), hot: 'lav', done: 'lav', outline: rgba('lav', 0.4) }} wrap lineHeight={1.02} />
          <div style={{ marginTop: 18, opacity: prog(t, tPick, tPick + 0.4) }}><Mono size={14} col={rgba('lav', 0.8)}>which locked bot runs: picked by the agents</Mono></div>
        </div>
      </AbsoluteFill>

      {/* right: the code */}
      <AbsoluteFill style={{ clipPath: `inset(0 0 0 ${50 + 50 * (1 - open)}%)` }}>
        <AbsoluteFill style={{ background: `radial-gradient(ellipse 70% 70% at 75% 60%, ${rgba('violet', 0.22)} 0%, ${rgba('violet', 0)} 70%), ${C.night}` }} />
        <Camera t={t} keys={cam}>
          <div style={{ position: 'absolute', left: 1030, top: 400, width: 760, borderRadius: 22, padding: '28px 30px', boxSizing: 'border-box', background: 'linear-gradient(135deg, rgba(255,255,255,0.09), rgba(255,255,255,0.02))', border: '1px solid rgba(255,255,255,0.12)', boxShadow: '0 30px 80px -40px rgba(110,75,255,0.6)', opacity: prog(t, tCode - 0.4, tCode) }}>
            {CODE.map((ln, i) => (
              <div key={i} style={{ height: 38 }}>
                <Typer t={t} t0={tCode - 0.3 + 0.16 * i} text={ln.t} size={21} col={rgba(ln.c, 0.95)} cps={120} caret={i === CODE.length - 1 ? C.violet2 : false} />
              </div>
            ))}
          </div>
          <div style={{ position: 'absolute', left: 1030, top: 640, opacity: prog(t, tPos, tPos + 0.2), transform: `scale(${1 + 0.15 * pulse(t, tPos, 0.1)})`, transformOrigin: '0% 50%' }}>
            <div style={{ display: 'inline-flex', alignItems: 'center', gap: 18, borderRadius: 18, background: C.lav, padding: '18px 26px' }}>
              <span style={{ ...F.archivo(40, 900, 110), color: C.ink }}>→ LONG</span>
              <span style={{ ...F.mono(20, 600), color: C.violet }}>paper position · from the rule</span>
            </div>
          </div>
        </Camera>
        <div style={{ position: 'absolute', left: 1030, top: 150, width: 760, opacity: prog(t, tCode - 0.5, tCode - 0.1) }}>
          <Karaoke t={t} words={span(L18, 5)} st={{ font: F.archivo(76, 900, 105) }} wrap lineHeight={1.02} />
        </div>
      </AbsoluteFill>
      <div style={{ position: 'absolute', left: 959, top: 0, bottom: 0, width: 2, background: rgba('lav', 0.5), opacity: open * (1 - 0.5 * clamp((t - start) / 2)) }} />
    </AbsoluteFill>
  );
}
