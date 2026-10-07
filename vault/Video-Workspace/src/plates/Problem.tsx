// 02 PROBLEM — "Most trading bots want the battle. / They charge in, then show you a screenshot of profit,
// taken after the market moved. / You can't check what they decided, or when."
// A wall of order prints (the battle), a profit card that gets screenshotted AFTER the move, then the two
// questions nobody can answer stamped over it.
import React from 'react';
import { AbsoluteFill } from 'remotion';
import type { PlateProps } from '../timeline';
import { C, mix, rgba } from '../lib/palette';
import { F } from '../lib/fonts';
import { lineOf, wordOf } from '../lib/lyrics';
import { clamp, ease, env, hash, prog, pulse, shake } from '../lib/util';
import { Ink, Karaoke, NightBg, seg, span, stampStyle, Typer, W, H } from '../components/kit';
import { Ambient, Camera, type CamKey } from '../components/camera';

const L3 = lineOf('Most trading bots');
const L4 = lineOf('They charge in');
const L5 = lineOf('You can’t check');
const w3 = (q: string) => wordOf(L3, q), w4 = (q: string) => wordOf(L4, q), w5 = (q: string) => wordOf(L5, q);

const SYMS = ['BTC', 'ETH', 'SOL', 'BNB', 'DOGE', 'PEPE', 'XRP', 'WIF', 'TRUMP', 'SUI', 'ARB', 'ORDI'];
function print(i: number) {
  const s = SYMS[Math.floor(hash(i, 1) * SYMS.length)]!;
  const buy = hash(i, 2) > 0.48;
  const lev = [5, 10, 20, 25, 50, 75, 100][Math.floor(hash(i, 3) * 7)]!;
  const q = (hash(i, 4) * 9 + 0.1).toFixed(2);
  return { s, buy, txt: `${buy ? 'LONG ' : 'SHORT'}  ${s.padEnd(5)} ${String(lev).padStart(3)}x  ${q.padStart(5)}  MKT` };
}

/** The fake profit chart: rises, with the screenshot taken at the top (after the move). */
function chartPts(x: number, y: number, w: number, h: number, k: number) {
  const n = 60, pts: { x: number; y: number }[] = [];
  for (let i = 0; i <= n * k; i++) {
    const u = i / n;
    const base = 0.12 + 0.1 * Math.sin(u * 9) * (1 - u) + 0.78 * Math.pow(u, 2.6);
    const nz = (hash(i, 9) - 0.5) * 0.05;
    pts.push({ x: x + u * w, y: y + h - (base + nz) * h });
  }
  return pts;
}

export default function Problem({ t, start, end }: PlateProps) {
  const tShot = w4('screenshot').start + 0.1;
  const tCard = w4('show').start - 0.15;
  const tAfter = w4('taken').start;
  const tWhat = w5('what').start, tWhen = w5('when').start;
  const flash = 0.7 * pulse(t, tShot, 0.045);
  const sh = shake(t, 10 * pulse(t, tShot, 0.05) + 8 * pulse(t, tWhat, 0.05) + 8 * pulse(t, tWhen, 0.05));

  // A: the order wall (fast, then it freezes when the screenshot is taken)
  const wallA = env(t, start, tCard + 1.2, 0.3, 0.8);
  const scroll = (Math.min(t, tShot) - start) * 520;
  const rows = 30, rowH = 34;
  const first = Math.floor(scroll / rowH);
  const textA = 1 - prog(t, L4.start - 0.35, L4.start - 0.05);

  // B: the card
  const cardIn = prog(t, tCard, tCard + 0.5, ease.outQuart);
  const cardX = 1040, cardY = 210, cardW = 640, cardH = 560;
  const shot = prog(t, tShot, tShot + 0.35, ease.outBack);
  const blur = 7 * prog(t, tWhat - 0.1, tWhat + 0.4) ;
  const chartK = prog(t, tCard + 0.2, tShot, ease.inOutCubic);
  const pts = chartPts(cardX + 40, cardY + 170, cardW - 80, 270, chartK);
  const pnl = 312.4 * ease.inOutCubic(chartK);

  // the order of events: the market moved, THEN the screenshot
  const tlY = 905, tlX0 = 1040, tlX1 = 1680;


  const cam: CamKey[] = [
    { t: 13.0, s: 1.04 },
    { t: 15.2, s: 1.1, rz: -0.8 },
    { t: 15.9, s: 1.03, x: 40, rz: 0 },
    { t: 17.38, s: 1.04, x: 60 },
    { t: 17.5, s: 1.1, x: 90, ez: ease.outQuart },
    { t: 18.5, s: 1.05, x: 60 },
    { t: 20.8, s: 1.05, x: 60, ry: 0 },
    { t: 23.8, s: 1.12, x: 150, ry: -8 },
  ];

  return (
    <AbsoluteFill>
      <NightBg glow={0.8} />
      <Camera t={t} keys={cam} depth={0.35}><Ambient t={t} seed={2} /></Camera>
      <Camera t={t} keys={cam}>
        <AbsoluteFill style={{ transform: `translate(${sh[0]}px, ${sh[1]}px)` }}>
          {/* the order wall */}
          <div style={{ position: 'absolute', left: 140, right: 140, top: 0, bottom: 0, overflow: 'hidden', opacity: wallA * 0.5 }}>
            {Array.from({ length: rows }, (_, k) => {
              const i = first + k;
              const p = print(i);
              const y = k * rowH - (scroll % rowH) - 20;
              const col = (i * 3) % 4;
              return (
                <div key={i} style={{ position: 'absolute', top: y, left: col * 410, ...F.mono(17, 500), whiteSpace: 'pre', color: p.buy ? rgba('violet2', 0.5 + 0.45 * hash(i, 6)) : rgba('lav', 0.25 + 0.3 * hash(i, 7)) }}>
                  {p.txt}
                </div>
              );
            })}
          </div>

          {/* the profit card */}
          {t >= tCard && (
            <div style={{ position: 'absolute', left: cardX, top: cardY, width: cardW, height: cardH, opacity: cardIn, transform: `translateY(${(1 - cardIn) * 60}px) rotate(${-5 * shot}deg) scale(${1 - 0.06 * shot})`, transformOrigin: '50% 50%', filter: blur > 0.05 ? `blur(${blur}px) grayscale(${clamp(blur / 7)})` : undefined }}>
              <div style={{ position: 'absolute', inset: -18 * shot, background: rgba('lav', shot), boxShadow: shot > 0 ? `0 30px 80px rgba(0,0,0,${0.6 * shot})` : undefined }} />
              <div style={{ position: 'absolute', inset: 0, background: C.night2, border: `1px solid ${rgba('lav', 0.14)}`, overflow: 'hidden' }}>
                <div style={{ position: 'absolute', left: 40, top: 34, ...F.mono(15, 500), letterSpacing: 2.5, color: rgba('lav', 0.55) }}>SOME BOT · PNL 30D</div>
                <div style={{ position: 'absolute', left: 36, top: 66, ...F.archivo(84, 900, 110), color: C.lav, letterSpacing: -1 }}>+{pnl.toFixed(1)}%</div>
                <svg width={cardW} height={cardH} style={{ position: 'absolute', left: -cardX, top: -cardY, overflow: 'visible' }}>
                  <path d={'M' + pts.map((p) => `${p.x.toFixed(1)} ${p.y.toFixed(1)}`).join('L')} fill="none" stroke={C.lav} strokeWidth={3} strokeLinejoin="round" style={{ filter: `drop-shadow(0 0 8px ${rgba('lav', 0.5)})` }} />
                </svg>
                <div style={{ position: 'absolute', left: 40, right: 40, bottom: 36, display: 'flex', justifyContent: 'space-between', ...F.mono(14, 500), color: rgba('lav', 0.5), letterSpacing: 1.5 }}>
                  <span>WIN RATE 94%</span><span>TRADES 1,284</span><span>14:32</span>
                </div>
              </div>
              {shot > 0 && (
                <div style={{ position: 'absolute', left: -18, right: -18, bottom: -18 - 70 * shot, height: 70 * shot, background: C.lav, display: 'flex', alignItems: 'center', paddingLeft: 30, overflow: 'hidden' }}>
                  <span style={{ ...F.serif(36, 500), color: C.ink }}>screenshot, 14:32</span>
                </div>
              )}
            </div>
          )}

          {/* WHAT? / WHEN? */}
          <div style={{ position: 'absolute', left: cardX + 20, top: cardY + 120, ...stampStyle(t, tWhat, -7) }}>
            <div style={{ ...F.archivo(130, 900, 120), color: 'transparent', WebkitTextStroke: `3px ${C.gap}` }}>WHAT?</div>
          </div>
          <div style={{ position: 'absolute', left: cardX + 210, top: cardY + 330, ...stampStyle(t, tWhen, 5) }}>
            <div style={{ ...F.archivo(130, 900, 120), color: C.gap }}>WHEN?</div>
          </div>

          {/* the order of events */}
          <svg width={W} height={H} style={{ position: 'absolute', inset: 0, opacity: env(t, tAfter - 0.1, tWhat + 0.2, 0.2, 0.4) }}>
            <Ink t={t} t0={tAfter} t1={tAfter + 0.5} pts={seg(tlX0, tlY, tlX1, tlY)} col={rgba('lav', 0.5)} w={1.4} />
            <circle cx={tlX0 + 120} cy={tlY} r={9 * prog(t, w4('market').start, w4('market').start + 0.15, ease.outBack)} fill={C.lav} />
            <rect x={tlX1 - 140 - 9} y={tlY - 9} width={18 * prog(t, w4('moved').start + 0.15, w4('moved').start + 0.3, ease.outBack)} height={18} fill={C.violet} />
          </svg>
          <div style={{ position: 'absolute', left: tlX0 + 40, top: tlY + 22, opacity: env(t, tAfter - 0.1, tWhat + 0.2, 0.2, 0.4) }}>
            <Typer t={t} t0={w4('market').start} text="14:05  MARKET MOVED" size={14} spacing={2} col={rgba('lav', 0.8)} caret={false} />
          </div>
          <div style={{ position: 'absolute', left: tlX1 - 290, top: tlY + 22, opacity: env(t, tAfter - 0.1, tWhat + 0.2, 0.2, 0.4) }}>
            <Typer t={t} t0={w4('moved').start + 0.15} text="14:32  SCREENSHOT" size={14} spacing={2} col={C.violet} caret={false} />
          </div>

        </AbsoluteFill>
      </Camera>
      <Camera t={t} keys={[]} drift={0.5}>
          {/* L3 */}
          <div style={{ position: 'absolute', left: 140, right: 140, top: 330, opacity: textA }}>
            <Karaoke t={t} words={span(L3, 0, 2)} st={{ font: F.archivo(150, 900, 118), pop: 0.05 }} align="center" lineHeight={1} />
            <div style={{ height: 14 }} />
            <Karaoke t={t} words={span(L3, 3)} st={{ font: F.serif(120, 500), outline: rgba('mist', 0.4), hot: 'violet', done: 'violet' }} align="center" />
          </div>

          {/* L4 + L5 karaoke, left column */}
          <div style={{ position: 'absolute', left: 150, width: 800, top: 250, opacity: env(t, L4.start - 0.3, end + 1, 0.3, 0.3) }}>
            <Karaoke t={t} words={span(L4, 0, 2)} st={{ font: F.archivo(66, 850, 100), pop: 0.04 }} wrap />
            <div style={{ height: 10 }} />
            <Karaoke t={t} words={span(L4, 3, 9)} st={{ font: F.serif(64, 500), outline: rgba('mist', 0.35) }} wrap lineHeight={1.12} />
            <div style={{ height: 10 }} />
            <Karaoke t={t} words={span(L4, 10)} st={{ font: F.serif(64, 500), outline: rgba('mist', 0.35) }} wrap lineHeight={1.12} />
            <div style={{ height: 40, opacity: 1 }} />
            <Karaoke t={t} words={span(L5, 0, 5)} st={{ font: F.archivo(56, 800, 100), hot: 'gap' }} wrap lineHeight={1.1} />
            <div style={{ height: 6 }} />
            <Karaoke t={t} words={span(L5, 6)} st={{ font: F.archivo(56, 800, 100), hot: 'gap' }} wrap />
          </div>

      </Camera>
      {/* shutter flash */}
      <AbsoluteFill style={{ background: mix('lav', '#ffffff', 0.5, 0.85 * flash), pointerEvents: 'none' }} />
    </AbsoluteFill>
  );
}
