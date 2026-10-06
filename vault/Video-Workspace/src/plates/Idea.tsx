// 03 IDEA — "Fabius is a paper-trading desk that commits its decisions to BNB Chain before the outcome exists.
// / Even the decision to do nothing."
// The web's hero surface (pale lavender), the giant name, then the web's own motif: one glass block walks a time
// axis and is sealed on chain at the COMMIT station while the OUTCOME station is still a ghost. Real data:
// B2-RS bar 05 Oct (4 signals, SAH); B1-TREND bars 02-05 Oct (n = 0, SAH).
import React from 'react';
import { AbsoluteFill } from 'remotion';
import type { PlateProps } from '../timeline';
import { C, rgba } from '../lib/palette';
import { F } from '../lib/fonts';
import { lineOf, wordOf } from '../lib/lyrics';
import { clamp, ease, env, lerp, prog, pulse, shake } from '../lib/util';
import { GraphPaper, Ink, Karaoke, LavBg, Mono, seg, span, Typer, W, H, type Poly } from '../components/kit';
import { Cube3D } from '../components/glass';
import { BrowserFrame, FlipBook } from '../components/devices';

const JOURNEY = Array.from({ length: 16 }, (_, i) => `ui/sec-journey-${String(i + 2).padStart(2, '0')}.jpg`);
import { Ambient, Camera, type CamKey } from '../components/camera';

const L6 = lineOf('Fabius is a paper');
const L7 = lineOf('Even the decision');
const w6 = (q: string) => wordOf(L6, q), w7 = (q: string) => wordOf(L7, q);

const AX_Y = 720, S1 = 330, S2 = 860, S3 = 1560;

export default function Idea({ t, end }: PlateProps) {
  // the name
  const tName = w6('Fabius').start;
  const NAME = 'FABIUS';
  const tUp0 = w6('that').start - 0.25, tUp1 = tUp0 + 0.6; // the name becomes a header
  const up = prog(t, tUp0, tUp1, ease.inOutCubic);
  const nameScale = lerp(1, 0.3, up);
  const nameX = lerp(W / 2, 150, up), nameY = lerp(470, 175, up);
  const breathe = 1 + 0.015 * Math.sin((t - tName) * 2.1) * (1 - up);

  // the axis + stations
  const tAx0 = tUp0 + 0.15, tAx1 = w6('decisions').start + 0.2;
  const tCommit = w6('commits').start, tChain = w6('BNB').start, tSeal = w6('Chain').start + 0.1;
  const tBefore = w6('before').start, tOut = w6('outcome').start;
  const blockX = lerp(S1, S2, prog(t, tChain - 0.05, tSeal, ease.inOutCubic));
  const sealed = t >= tSeal;
  const tNothing = w7('nothing').start;
  const sh = shake(t, 7 * pulse(t, tSeal, 0.05) + 6 * pulse(t, tName + 0.25, 0.05) + 5 * pulse(t, tNothing + 0.25, 0.05));
  // the web's journey frames: bar closes -> decides -> sealed -> committed on BNB Chain (hold there: the outcome is still to come)
  const journeyK = prog(t, w6('that').start, w6('Chain').end + 0.3, ease.inOutCubic) * (11 / 15);
  const squiggle: Poly = Array.from({ length: 40 }, (_, i) => ({ x: S3 - 110 + i * 5.6, y: AX_Y - 95 + Math.sin(i * 0.7) * 16 + (i % 3) * 4 - i * 0.9 }));

  const cam: CamKey[] = [
    { t: 23.4, s: 1.25 },
    { t: 25.0, s: 1.0, ez: ease.outQuart },
    { t: 26.1, s: 1.0 },
    { t: 27.6, s: 1.03, rx: 4, x: -40, y: 40 },
    { t: 30.4, s: 1.06, rx: 3, x: 60, y: 60 },
    { t: 31.2, s: 1.0, rx: 0, x: 0, y: 40 },
    { t: 33.6, s: 1.08, rx: 0, x: 0, y: 60 },
  ];

  return (
    <AbsoluteFill>
      <LavBg />
      <Camera t={t} keys={cam} depth={0.35}><Ambient t={t} light seed={3} n={6} dust={24} cubes={11} /></Camera>
      <Camera t={t} keys={cam}>
        <AbsoluteFill style={{ transform: `translate(${sh[0]}px, ${sh[1]}px)` }}>
          <GraphPaper paper opacity={0.45 * prog(t, tUp0, tUp1)} />
          {/* the product: the web's own 'from candle close to proof' section, played through */}
          <div style={{ position: 'absolute', left: 330, top: 380, opacity: prog(t, tUp0, tUp1) * (1 - 0.82 * prog(t, L7.start - 0.3, L7.start + 0.2)),
            transform: `perspective(1900px) rotateX(${lerp(16, 7, prog(t, tUp0, tChain))}deg) translateY(${(1 - prog(t, tUp0, tUp1 + 0.2, ease.outCubic)) * 220}px) scale(${1 - 0.06 * prog(t, L7.start - 0.3, L7.start + 0.4)})`, transformOrigin: '50% 0%' }}>
            <BrowserFrame url="fabius-one.vercel.app/#how-it-works" w={1260} h={650} imgW={2160} glint={prog(t, tUp1, tUp1 + 1.1)}>
              <FlipBook frames={JOURNEY} k={journeyK} />
            </BrowserFrame>
          </div>
          {/* doing nothing is a decision too: two empty commits, sealed */}
          {t >= L7.start - 0.2 && [0, 1].map((i) => (
            <Cube3D key={i} x={W / 2 - 170 + 340 * i} y={700 + 8 * Math.sin(t * 2 + i)} s={170} rx={-22} ry={(t - L7.start) * 26 + 35 + i * 20}
              lit={t >= tNothing + 0.2 ? 0 : 0} opacity={prog(t, L7.start - 0.2 + 0.12 * i, L7.start + 0.25 + 0.12 * i)} />
          ))}
          {t >= L7.start && (
            <div style={{ position: 'absolute', left: 0, right: 0, top: 860, textAlign: 'center', opacity: prog(t, tNothing + 0.1, tNothing + 0.4) }}>
              <Typer t={t} t0={tNothing + 0.1} text="B1-TREND · bars 02–05 Oct · n = 0 · committed, SAH" size={20} weight={600} spacing={2} col={C.violet} caret={false} />
            </div>
          )}
        </AbsoluteFill>
      </Camera>

      <Camera t={t} keys={[]} drift={0.4}>
        {/* FABIUS: letters slam in, then the name moves up to be the header */}
        <div style={{ position: 'absolute', left: nameX, top: nameY, transform: `translate(${-50 * (1 - up)}%, -50%) scale(${nameScale * breathe})`, transformOrigin: up > 0 ? '0% 50%' : '50% 50%', display: 'flex', whiteSpace: 'pre' }}>
          {Array.from(NAME).map((ch, i) => {
            const at = tName - 0.12 + i * 0.045;
            const k = prog(t, at, at + 0.24, ease.outQuart);
            return (
              <span key={i} style={{ ...F.archivo(300, 900, 125), color: C.ink, lineHeight: 1, display: 'inline-block', opacity: clamp(k * 2), transform: `translateY(${(1 - k) * -140}px) scale(${1 + (1 - k) * 0.4})`, filter: k < 1 ? `blur(${(1 - k) * 12}px)` : undefined }}>{ch}</span>
            );
          })}
        </div>
        <div style={{ position: 'absolute', left: 0, right: 0, top: 650, opacity: 1 - up }}>
          <Karaoke t={t} words={span(L6, 1, 4)} st={{ font: F.serif(92, 500), light: true }} align="center" />
        </div>
        <div style={{ position: 'absolute', left: 150, top: 236, width: 1620, opacity: prog(t, tUp0 + 0.2, tUp1) * (1 - prog(t, L7.start - 0.3, L7.start)) }}>
          <Karaoke t={t} words={span(L6, 5, 12)} st={{ font: F.archivo(54, 800, 100), light: true, gap: 0.24 }} wrap lineHeight={1.08} />
          <div style={{ height: 4 }} />
          <Karaoke t={t} words={span(L6, 13)} st={{ font: F.serif(58, 600), light: true, gap: 0.24 }} wrap />
        </div>
        <div style={{ position: 'absolute', left: 150, right: 150, top: 300, opacity: env(t, L7.start - 0.25, end + 1, 0.25, 0.3) }}>
          <Karaoke t={t} words={L7.words} st={{ font: F.serif(110, 500), light: true, hot: 'violet', done: 'ink' }} align="left" />
        </div>
      </Camera>
    </AbsoluteFill>
  );
}
