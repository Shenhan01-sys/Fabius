// USE IT - "Want today's signal? Get it on the web, in Telegram, or let your AI agent fetch it over MCP.
// Pay per signal with x402. No gas, no subscription, and it arrives with its proof."
// Three ways in, side by side in depth: the real /buy page (capture), the Fabius Telegram bot (its real reply
// templates, tools/x402_sinyal.py `_teaser_en` + `tg_reply`, with today's teaser data from GET /teaser/B1-TREND),
// and an agent's terminal (real MCP tool list + the gate's real HTTP 402, public/data/live/, fetched 7 Oct).
import React from 'react';
import { AbsoluteFill } from 'remotion';
import { At, camAt, Space, withDrift } from '../cam/space';
import { LavWorld } from '../fx/world';
import { GlowBlob } from '../fx/fx';
import { Headline } from '../ui/text';
import { BrowserWindow, Clip } from '../ui/browser';
import { Phone, Terminal, TelegramChat, type ChatMsg, type TermLine } from '../ui/devices';
import { Cursor } from '../ui/cursor';
import { appear, Check, Pill } from '../ui/bits';
import { C, rgba } from '../lib/palette';
import { accent, inter, label, mono } from '../lib/fonts';
import { clamp, ease, noise1, prog } from '../lib/util';
import { at, line } from '../lib/vo';
import type { SceneProps } from '../timeline';
import { capCursor, capMark } from '../data/captures';

const TEASER = 'B1-TREND · bar 2026-10-06\nTrack-record confidence (forward results): not measured yet\nRole: core (identity bot) · locked backtest gate: rejected · forward test F-D16: not enough data yet\nProgress: signals 0/20, settled days 0/20, months 0/2\nPrice: 0.01 FAB (base price, locked table)\n\nTap the button: sign in with Telegram (or Google), get free FAB, pay with x402 (no gas). The signal is also sent here.';

export const S6Use: React.FC<SceneProps> = ({ t, t0, t1 }) => {
  const l1 = line('use1'), l3 = line('use3');
  const tWeb = at('use2', 'web'), tTg = at('use2', 'Telegram'), tAgent = at('use2', 'agent'), tMcp = at('use2', 'MCP');
  const tPay = at('use3', 'x402'), tGas = at('use3', 'gas'), tSub = at('use3', 'subscription'), tProof = at('use3', 'proof');
  // camera: headline -> web -> telegram -> agent -> pull back to all three for the payment
  const cam = withDrift(camAt([
    { t: t0, z: -380, x: 0, y: -40, rx: 4, ry: 0 },
    { t: tWeb - 0.3, z: -300, x: 0, y: 0, rx: 3, ry: 0, ez: ease.inOutCubic },
    { t: tWeb + 0.5, z: 140, x: -700, y: 10, rx: 2, ry: 14, ez: ease.inOutQuart },
    { t: tTg + 0.45, z: 190, x: 0, y: 30, rx: 1, ry: 0, ez: ease.inOutQuart },
    { t: tAgent + 0.5, z: 170, x: 700, y: 10, rx: 2, ry: -14, ez: ease.inOutQuart },
    { t: l3.start + 0.2, z: -260, x: 0, y: -10, rx: 5, ry: 0, ez: ease.inOutQuart },
    { t: t1, z: -170, x: 0, y: -10, rx: 3, ry: -3, ez: ease.inOutCubic },
  ], t), t, 0.7, 31);

  const msgs: ChatMsg[] = [
    { at: tTg - 0.25, from: 'me', text: '/signal' },
    { at: tTg + 0.45, from: 'bot', text: TEASER, button: 'Buy B1-TREND · 0.01 FAB', tapAt: tPay - 0.1 },
    { at: tProof - 0.3, from: 'bot', img: 'ui/tg-B2-RS-2026-10-05.png', blur: 7, note: 'SIGNAL + COMMIT PROOF · SEALED BEFORE THE OUTCOME' },
  ];
  const term: TermLine[] = [
    { at: tAgent - 0.3, kind: 'cmd', text: 'mcp connect fabius-one.vercel.app/mcp' },
    { at: tAgent + 0.75, kind: 'dim', text: '18 tools · fabius_signal (paid) · fabius_verify · fabius_status …' },
    { at: tMcp - 0.15, kind: 'cmd', text: 'GET /signal/B1-TREND' },
    { at: tMcp + 0.65, kind: 'warn', text: 'HTTP 402 Payment Required' },
    { at: tMcp + 0.85, kind: 'json', text: 'exact · eip155:97 · 10000 = 0.01 FAB · permit2' },
    { at: tPay + 0.1, kind: 'cmd', text: 'sign permit   # signature only, no gas' },
    { at: tGas + 0.35, kind: 'ok', text: '✓ PAYMENT-SIGNATURE · settled by the gate' },
    { at: tProof - 0.45, kind: 'ok', text: 'HTTP 200 · signal + commit proof' },
  ];
  // the /buy capture runs slower than real time so the Privy sign-in (Google / Telegram / email) opens as the camera pulls back
  const buyStart = tWeb - 1.5, modalAt = tPay - 1.0; // the modal opens as the camera pulls back for the payment
  const buyRate = capMark('buy', 'modal-open') / ((modalAt - buyStart) * 60);
  const fBuy = Math.max(0, Math.min(501, (t - buyStart) * 60 * buyRate));
  const buyClick = buyStart + capMark('buy', 'signin-click') / (60 * buyRate);
  const cur = capCursor('buy', fBuy);
  const pay = prog(t, tPay - 0.2, tPay + 0.45, ease.cine);
  return (
    <AbsoluteFill>
      <LavWorld t={t} cam={cam} seed={6} />
      <Space cam={cam} perspective={1600}>
        {/* headline */}
        <At x={0} y={-330} z={-120}>
          <div style={{ position: 'absolute', left: -700, top: -80, width: 1400, display: 'flex', justifyContent: 'center' }}>
            <Headline t={t} size={104} align="center" out={tWeb + 0.2}
              segs={[{ text: 'Want', at: l1.words[0]!.start, voice: 'calm' }, { text: "today's signal?", at: at('use1', "today's"), voice: 'accent' }]} />
          </div>
        </At>
        {/* the web: /buy */}
        <At x={-700} y={40} z={0} ry={16} rx={2}>
          <div style={appear(t, t0 + 0.2, 0.7, 60)}>
            <BrowserWindow w={860} h={560} url="fabius-one.vercel.app/buy" sweep={prog(t, tWeb, tWeb + 1.1)}>
              <Clip name="buy" f={fBuy} />
              <Cursor t={t} x={cur.x * (860 / 1440)} y={cur.y * (860 / 1440)} clicks={[buyClick]} scale={0.8} />
            </BrowserWindow>
          </div>
          <div style={{ position: 'absolute', left: -430, top: -340, ...appear(t, tWeb, 0.5) }}><Pill size={22} fill>Web</Pill></div>
        </At>
        {/* Telegram */}
        <At x={0} y={60} z={-10} rx={1}>
          <div style={appear(t, t0 + 0.35, 0.7, 60)}>
            <Phone w={380} glare={0.6}>
              <TelegramChat t={t} msgs={msgs} w={380 - 2 * 380 * 0.032} />
            </Phone>
          </div>
          <div style={{ position: 'absolute', left: -60, top: -470, ...appear(t, tTg, 0.5) }}><Pill size={22} fill>Telegram</Pill></div>
        </At>
        {/* agent over MCP */}
        <At x={700} y={40} z={0} ry={-16} rx={2}>
          <div style={appear(t, t0 + 0.5, 0.7, 60)}>
            <Terminal t={t} lines={term} w={860} h={520} title="your AI agent · MCP + x402" />
          </div>
          <div style={{ position: 'absolute', left: 260, top: -330, ...appear(t, tAgent, 0.5) }}><Pill size={22} fill>AI agent · MCP</Pill></div>
        </At>
        {/* the x402 payment, centre front */}
        <At x={0} y={-300} z={330}>
          <div style={{ position: 'absolute', left: -330, top: -70, width: 660, opacity: pay * (1 - prog(t, t1 - 0.4, t1)), transform: `scale(${0.85 + 0.15 * pay})`, display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 18, padding: '18px 30px', borderRadius: 28, background: 'rgba(255,255,255,0.9)', border: `1px solid ${rgba('violet', 0.2)}`, boxShadow: `0 30px 80px -20px ${rgba('violet', 0.55)}` }}>
            <span style={{ ...accent(64), color: C.violet }}>x402</span>
            <span style={{ ...inter(26, 600), color: C.ink }}>pay per signal</span>
            <span style={{ ...mono(20, 600), color: C.mist }}>0.01 FAB</span>
          </div>
        </At>
        {[['No gas', tGas], ['No subscription', tSub]].map(([txt, a], i) => (
          <At key={i} x={-190 + i * 380} y={-150 + 8 * noise1(t + i, 70)} z={360}>
            <div style={{ position: 'absolute', left: -170, top: -34, ...appear(t, a as number, 0.45, 30), opacity: (appear(t, a as number, 0.45).opacity as number) * (1 - prog(t, t1 - 0.4, t1)) }}>
              <Pill size={28} icon={<Check s={30} k={prog(t, (a as number) + 0.1, (a as number) + 0.5)} />}>{txt as string}</Pill>
            </div>
          </At>
        ))}
      </Space>
      <GlowBlob x={960} y={300} r={420} col="violet2" a={0.25 * pay} />
      <AbsoluteFill style={{ pointerEvents: 'none' }}>
        <div style={{ position: 'absolute', right: 70, top: 60, ...label(14, 700), color: rgba('ink', 0.5), opacity: prog(t, tPay, tPay + 0.4) }}>BNB testnet · FAB is a test token with no value</div>
      </AbsoluteFill>
    </AbsoluteFill>
  );
};
