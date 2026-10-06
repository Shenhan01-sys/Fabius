// 09 BNB — "Signals sell over x402, and the buyer pays no gas. / All on testnet, with a test token. No real money,
// by design."
// The Telegram bot (its real replies: tools/x402_sinyal.py HELP and /buy, and the real signal image from
// tools/sinyal_gambar.py for B2-RS bar 05 Oct), the x402 handshake as objects (402 -> signature -> 200), a gas
// gauge at zero, the /buy Mini App, then the public real-money switch: off, and it will not flip
// (config/uang_nyata.json "aktif": false).
import React from 'react';
import { AbsoluteFill } from 'remotion';
import type { PlateProps } from '../timeline';
import { C, rgba } from '../lib/palette';
import { F } from '../lib/fonts';
import { lineOf, wordOf } from '../lib/lyrics';
import { clamp, ease, env, lerp, prog, pulse, shake } from '../lib/util';
import { Karaoke, Mono, NightBg, span, stampStyle, StampBox, Typer } from '../components/kit';
import { Ambient, Camera, type CamKey } from '../components/camera';
import { Cursor, PhoneFrame, TelegramChat, type ChatMsg } from '../components/devices';

const L22 = lineOf('Signals sell over');
const L23 = lineOf('All on testnet');
const w22 = (q: string) => wordOf(L22, q), w23 = (q: string) => wordOf(L23, q);

const HELP_HEAD = 'Fabius - verified trading signals, paid per signal with x402 on BNB testnet (chain 97). FAB is a test token with no value.\n\n/buy - the signal of the bot Fabius is trading now (or /buy <BOT>): pay with x402 in the Fabius app inside Telegram, no gas\n/signal - free teaser of the active bot\n/desk - the AI desk: every 5 minutes each AI agent decides, anchored on-chain';

export default function Bnb({ t, start, end }: PlateProps) {
  const t402 = w22('x402,').start, tBuyer = w22('buyer').start, tGas = w22('gas.').start;
  const tTest = w23('testnet,').start, tToken = w23('token.').start, tNo = w23('No').start, tDesign = w23('design.').start;
  // the switch is off; on "No real money" a pointer tries it, the knob gives a little and springs back, a lock shows
  const tTry = tNo + 0.12;
  const nudge = t >= tTry ? Math.sin(clamp((t - tTry) / 0.42) * Math.PI) * Math.exp(-2 * clamp((t - tTry) / 0.42)) : 0;
  const lockK = prog(t, tTry + 0.32, tTry + 0.48, ease.outBack);
  const sh = shake(t, 6 * pulse(t, t402 + 0.15, 0.06) + 6 * pulse(t, tDesign + 0.1, 0.05) + 5 * pulse(t, tTry + 0.2, 0.05));

  const msgs: ChatMsg[] = [
    { at: start - 1, from: 'me', text: '/start' },
    { at: start - 0.9, from: 'bot', text: HELP_HEAD },
    { at: start + 0.35, from: 'me', text: '/buy B2-RS' },
    { at: w22('over').start, from: 'bot', text: 'B2-RS · bar 2026-10-05 · 0.01 FAB\n\nTap the button: sign in with Telegram (or Google), get free FAB, pay with x402 (no gas). The signal is also sent here.', button: 'Buy B2-RS · 0.01 FAB', tapAt: w22('x402,').start + 0.55 },
    { at: tBuyer + 0.1, from: 'bot', img: 'ui/tg-B2-RS-2026-10-05.png' },
    { at: tGas + 0.25, from: 'bot', text: 'Fabius B2-RS · bar 2026-10-05\nProof: committed ✓' },
  ];

  const cam: CamKey[] = [
    { t: start - 0.3, s: 1.12, ry: -6 },
    { t: t402 + 0.3, s: 1.02, ry: -2 },
    { t: tGas + 0.3, s: 1.04, ry: 2 },
    { t: L23.start + 0.2, s: 1.0, ry: 0, y: 20 },
    { t: end + 0.3, s: 1.08, y: 30 },
  ];
  // the x402 steps
  const steps = [
    { at: t402 - 0.1, txt: 'GET /signal/B2-RS', sub: 'the buyer asks', col: C.lav },
    { at: t402 + 0.35, txt: '402 Payment Required', sub: 'price 0.01 FAB · pay to Fabius', col: C.violet2 },
    { at: tBuyer - 0.15, txt: 'signature (EIP-712)', sub: 'a permit, not a transaction', col: C.lav },
    { at: tGas - 0.1, txt: '200 OK · signal + proof', sub: 'the gate settles and pays the gas', col: C.violet2 },
  ];
  const gauge = prog(t, tBuyer - 0.1, tGas + 0.2, ease.inOutCubic); // needle drops to 0
  const part1 = 1 - prog(t, L23.start - 0.4, L23.start - 0.05);
  const part2 = prog(t, L23.start - 0.1, L23.start + 0.3);

  return (
    <AbsoluteFill>
      <NightBg glow={1.2} x={60} y={100} />
      <Camera t={t} keys={cam} depth={0.3}><Ambient t={t} seed={10} cubes={6} /></Camera>
      <Camera t={t} keys={cam}>
        <AbsoluteFill style={{ transform: `translate(${sh[0]}px, ${sh[1]}px)` }}>
          {/* the big 402 */}
          <div style={{ position: 'absolute', left: 120, top: 250, opacity: part1 * prog(t, t402 - 0.1, t402 + 0.2), transform: `scale(${1 + 0.12 * pulse(t, t402 + 0.1, 0.08)})`, transformOrigin: '0% 50%' }}>
            <div style={{ ...F.archivo(230, 900, 125), color: 'transparent', WebkitTextStroke: `4px ${C.violet2}`, lineHeight: 1, filter: `drop-shadow(0 0 22px ${rgba('violet', 0.8)})` }}>402</div>
            <div style={{ ...F.mono(16, 600), letterSpacing: 4, color: rgba('lav', 0.8), marginTop: 8 }}>HTTP 402 · PAYMENT REQUIRED · x402 ON BNB CHAIN</div>
          </div>
          {/* handshake steps */}
          <div style={{ position: 'absolute', left: 130, top: 560, width: 640, opacity: part1 }}>
            {steps.map((s, i) => {
              const a = prog(t, s.at, s.at + 0.3, ease.outCubic);
              return (
                <div key={i} style={{ display: 'flex', alignItems: 'center', gap: 18, height: 66, opacity: a, transform: `translateX(${(1 - a) * -40}px)` }}>
                  <div style={{ width: 38, height: 38, borderRadius: 12, background: i % 2 ? rgba('violet', 0.9) : rgba('lav', 0.14), border: `1px solid ${rgba('lav', 0.4)}`, display: 'flex', alignItems: 'center', justifyContent: 'center', ...F.mono(15, 600), color: C.lav }}>{i + 1}</div>
                  <div>
                    <div style={{ ...F.mono(21, 600), color: s.col }}>{s.txt}</div>
                    <div style={{ ...F.mono(13.5, 400), color: rgba('lav', 0.6) }}>{s.sub}</div>
                  </div>
                </div>
              );
            })}
          </div>
          {/* the gas gauge (the buyer's) */}
          <div style={{ position: 'absolute', left: 820, top: 610, width: 230, height: 170, opacity: part1 * prog(t, tBuyer - 0.3, tBuyer) }}>
            <svg width={230} height={170}>
              <path d="M 25 140 A 90 90 0 0 1 205 140" fill="none" stroke={rgba('lav', 0.25)} strokeWidth={14} strokeLinecap="round" />
              <path d="M 25 140 A 90 90 0 0 1 60 72" fill="none" stroke={C.gap} strokeWidth={14} strokeLinecap="round" opacity={0.85} />
              {(() => {
                const a = Math.PI * (1 - lerp(0.78, 0.0, gauge));
                return <line x1={115} y1={140} x2={115 + 80 * Math.cos(a)} y2={140 - 80 * Math.sin(a)} stroke={C.lav} strokeWidth={6} strokeLinecap="round" />;
              })()}
              <circle cx={115} cy={140} r={10} fill={C.lav} />
            </svg>
            <div style={{ position: 'absolute', left: 0, right: 0, top: 150, textAlign: 'center', ...F.mono(15, 600), color: C.lav, letterSpacing: 2 }}>BUYER GAS · {gauge > 0.95 ? '0' : '…'}</div>
          </div>
          {/* the Telegram bot */}
          <div style={{ position: 'absolute', left: 1120, top: 90, opacity: part1, transform: `perspective(1600px) rotateY(${-12 + 4 * Math.sin(t * 0.6)}deg) rotateZ(2deg)` }}>
            <TelegramChat t={t} msgs={msgs} w={400} />
          </div>
          {/* the Mini App */}
          <div style={{ position: 'absolute', left: 1560, top: 300, opacity: part1 * prog(t, tBuyer - 0.6, tBuyer - 0.2), transform: `perspective(1600px) rotateY(-18deg) rotateZ(4deg) translateY(${(1 - prog(t, tBuyer - 0.6, tBuyer, ease.outCubic)) * 80}px)` }}>
            <PhoneFrame src="ui/buybot-m-top.jpg" w={290} glint={prog(t, tBuyer - 0.2, tBuyer + 0.7)} />
          </div>

          {/* part 2: the switch, off */}
          <div style={{ position: 'absolute', left: 0, right: 0, top: 300, display: 'flex', justifyContent: 'center', gap: 70, alignItems: 'center', opacity: part2 }}>
            <div style={{ width: 340, height: 170, borderRadius: 85, background: `linear-gradient(180deg, ${rgba('night', 0.9)}, ${rgba('night3', 0.9)})`, border: `2px solid ${rgba('lav', 0.45)}`, position: 'relative', boxShadow: '0 2px 10px rgba(0,0,0,0.5) inset, 0 1px 0 rgba(255,255,255,0.2), 0 30px 70px -30px rgba(0,0,0,0.6)' }}>
              <div style={{ position: 'absolute', top: 15, left: 15 + 48 * nudge, width: 140, height: 140, borderRadius: 70, background: 'radial-gradient(circle at 35% 30%, #ffffff, #c9bdf2)', boxShadow: '0 12px 30px rgba(0,0,0,0.45)' }} />
              <div style={{ position: 'absolute', right: 52, top: 52, ...stampStyle(t, tTry + 0.32, 0, 1.8) }}>
                <svg width={52} height={64} viewBox="0 0 52 64">
                  <path d="M 13 30 L 13 19 A 13 13 0 0 1 39 19 L 39 30" fill="none" stroke={C.lav} strokeWidth={6} strokeLinecap="round" />
                  <rect x={4} y={28} width={44} height={34} rx={7} fill={C.lav} />
                  <circle cx={26} cy={42} r={5} fill={C.night} />
                  <rect x={24} y={44} width={4} height={10} rx={2} fill={C.night} />
                </svg>
              </div>
              <div style={{ position: 'absolute', left: 140, top: 92, width: 0, height: 0, opacity: 1 - prog(t, tTry + 0.65, tTry + 0.95) }}>
                <Cursor t={t} keys={[{ t: tTry - 0.55, x: 260, y: 150 }, { t: tTry - 0.05, x: -40, y: -10 }, { t: tTry + 0.3, x: 0, y: -10 }, { t: tTry + 0.6, x: 60, y: 60 }]} clicks={[tTry]} scale={1.6} dark />
              </div>
            </div>
            <div>
              <div style={{ ...F.mono(17, 600), letterSpacing: 4, color: rgba('lav', 0.7) }}>REAL MONEY</div>
              <div style={{ ...F.archivo(120, 900, 120), color: C.lav, lineHeight: 1, transform: `scale(${1 + 0.06 * lockK * pulse(t, tTry + 0.32, 0.12)})`, transformOrigin: '0% 50%' }}>OFF</div>
              <div style={{ ...F.mono(17, 500), color: C.violet2, marginTop: 10 }}>config/uang_nyata.json → {'{ "aktif": false }'}</div>
            </div>
          </div>
          <div style={{ position: 'absolute', left: 0, right: 0, top: 560, display: 'flex', justifyContent: 'center', gap: 22, opacity: part2 }}>
            {[[tTest, 'BSC TESTNET · CHAIN 97'], [tToken, 'FAB · A TEST TOKEN, NO VALUE'], [tNo + 0.3, 'PAPER POSITIONS ONLY']].map(([at, s]) => (
              <div key={s as string} style={{ opacity: prog(t, at as number, (at as number) + 0.3), transform: `translateY(${(1 - prog(t, at as number, (at as number) + 0.3, ease.outCubic)) * 30}px)`, ...F.mono(17, 600), letterSpacing: 2, color: C.lav, border: `1.5px solid ${rgba('lav', 0.4)}`, borderRadius: 999, padding: '12px 22px', background: rgba('lav', 0.06) }}>{s as string}</div>
            ))}
          </div>
          <div style={{ position: 'absolute', left: 0, right: 0, top: 660, textAlign: 'center', ...stampStyle(t, tDesign, -4) }}>
            <StampBox col={C.violet2} size={46}>by design</StampBox>
          </div>
        </AbsoluteFill>
      </Camera>

      <Camera t={t} keys={[]} drift={0.4}>
        <div style={{ position: 'absolute', left: 130, top: 120, width: 920, opacity: 1 - prog(t, L23.start - 0.45, L23.start - 0.2) }}>
          <Karaoke t={t} words={span(L22, 0, 3)} st={{ font: F.archivo(62, 900, 105) }} wrap />
          <div style={{ height: 4 }} />
          <Karaoke t={t} words={span(L22, 4)} st={{ font: F.serif(60, 500), outline: rgba('mist', 0.4) }} wrap />
        </div>
        <div style={{ position: 'absolute', left: 150, right: 150, top: 120, opacity: env(t, L23.start - 0.2, end + 1, 0.25, 0.3) }}>
          <Karaoke t={t} words={span(L23, 0, 6)} st={{ font: F.archivo(62, 900, 105) }} align="center" wrap />
          <div style={{ height: 6 }} />
          <Karaoke t={t} words={span(L23, 7)} st={{ font: F.serif(64, 500), outline: rgba('mist', 0.4) }} align="center" wrap />
        </div>
        <div style={{ position: 'absolute', left: 130, top: 952, opacity: part1 * prog(t, t402 + 0.6, t402 + 1) }}>
          <Mono size={13} col={rgba('lav', 0.55)}>x402 = pay-per-request over plain HTTP · the buyer signs, the gate pays the gas</Mono>
        </div>
      </Camera>
    </AbsoluteFill>
  );
}
