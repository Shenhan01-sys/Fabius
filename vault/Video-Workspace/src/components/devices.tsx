// Product frames: the Fabius web app in a desktop browser and a phone, and the Fabius Telegram bot.
// Screens are real captures of web/ (scripts/capture-web.mjs); the Telegram chat is drawn from the bot's real
// message templates (tools/x402_sinyal.py HELP / _teaser_en / tg_reply) and its real signal table image.
import React from 'react';
import { Img, staticFile } from 'remotion';
import { C, rgba } from '../lib/palette';
import { F } from '../lib/fonts';
import { clamp, ease, prog } from '../lib/util';

/** A browser window showing a (tall) page capture, scrolled by `scroll` px of the capture (image px). */
export const BrowserFrame: React.FC<{ src?: string; url: string; w: number; h: number; scroll?: number; imgW?: number; style?: React.CSSProperties; dark?: boolean; children?: React.ReactNode; glint?: number }> = ({ src, url, w, h, scroll = 0, imgW = 1440, style, dark = false, children, glint }) => {
  const bar = 46;
  const k = w / imgW; // capture px -> frame px
  return (
    <div style={{ position: 'absolute', width: w, height: h, borderRadius: 18, overflow: 'hidden', background: dark ? C.night2 : '#fbfaff', border: `1px solid ${dark ? 'rgba(255,255,255,0.14)' : 'rgba(255,255,255,0.9)'}`, boxShadow: `0 40px 120px -30px ${rgba('violet', 0.55)}, 0 1px 0 rgba(255,255,255,0.5) inset`, ...style }}>
      <div style={{ height: bar, display: 'flex', alignItems: 'center', gap: 10, padding: '0 18px', background: dark ? 'rgba(255,255,255,0.05)' : 'rgba(236,232,250,0.95)', borderBottom: `1px solid ${dark ? 'rgba(255,255,255,0.08)' : 'rgba(21,18,43,0.08)'}` }}>
        {['#ff6058', '#ffbd2e', '#28c941'].map((c) => <div key={c} style={{ width: 12, height: 12, borderRadius: 6, background: c, opacity: 0.85 }} />)}
        <div style={{ marginLeft: 18, flex: 1, height: 28, borderRadius: 8, background: dark ? 'rgba(255,255,255,0.06)' : '#ffffff', display: 'flex', alignItems: 'center', padding: '0 14px', ...F.mono(14, 500), color: dark ? rgba('lav', 0.7) : rgba('ink', 0.65) }}>
          <span style={{ color: C.violet, marginRight: 8 }}>●</span>{url}
        </div>
      </div>
      <div style={{ position: 'absolute', left: 0, right: 0, top: bar, bottom: 0, overflow: 'hidden' }}>
        {src ? <Img src={staticFile(src)} style={{ position: 'absolute', left: 0, top: -scroll * k, width: w }} /> : null}
        {children}
      </div>
      {glint !== undefined ? <Glint k={glint} /> : null}
    </div>
  );
};

/** A light sweep across glass (k = 0..1 through the sweep). */
export const Glint: React.FC<{ k: number }> = ({ k }) => (k <= 0 || k >= 1 ? null : (
  <div style={{ position: 'absolute', inset: 0, overflow: 'hidden', pointerEvents: 'none', borderRadius: 'inherit' }}>
    <div style={{ position: 'absolute', top: '-20%', bottom: '-20%', width: '35%', left: `${-40 + 160 * k}%`, transform: 'skewX(-18deg)', background: 'linear-gradient(90deg, rgba(255,255,255,0) 0%, rgba(255,255,255,0.28) 50%, rgba(255,255,255,0) 100%)' }} />
  </div>
));

/** A phone showing a (tall) mobile capture, scrolled by `scroll` capture px. */
export const PhoneFrame: React.FC<{ src?: string; w?: number; scroll?: number; imgW?: number; style?: React.CSSProperties; children?: React.ReactNode; screenBg?: string; glint?: number }> = ({ src, w = 380, scroll = 0, imgW = 390, style, children, screenBg = '#fbfaff', glint }) => {
  const h = w * 2.05, r = w * 0.15, bez = w * 0.035;
  const k = (w - 2 * bez) / imgW;
  return (
    <div style={{ position: 'absolute', width: w, height: h, borderRadius: r, background: '#0b0920', padding: bez, boxSizing: 'border-box', boxShadow: `0 50px 120px -30px ${rgba('violet', 0.6)}, 0 0 0 2px rgba(255,255,255,0.08) inset, 0 0 0 1px rgba(157,134,255,0.25)`, ...style }}>
      <div style={{ position: 'relative', width: '100%', height: '100%', borderRadius: r - bez, overflow: 'hidden', background: screenBg }}>
        {src ? <Img src={staticFile(src)} style={{ position: 'absolute', left: 0, top: -scroll * k, width: '100%' }} /> : null}
        {children}
        <div style={{ position: 'absolute', left: '50%', top: w * 0.025, width: w * 0.3, height: w * 0.075, marginLeft: -w * 0.15, borderRadius: 999, background: '#05040f' }} />
        {glint !== undefined ? <Glint k={glint} /> : null}
      </div>
    </div>
  );
};

export interface ChatMsg { at: number; from: 'me' | 'bot'; text?: string; button?: string; img?: string; imgH?: number; tapAt?: number }

/** Telegram chat (dark theme) inside a phone: messages appear at their times, the latest scrolled into view. */
export const TelegramChat: React.FC<{ t: number; msgs: ChatMsg[]; w?: number; style?: React.CSSProperties; typingBefore?: number }> = ({ t, msgs, w = 400, style, typingBefore = 0.7 }) => {
  const s = w / 400; // design at 400 px wide
  const shown = msgs.filter((m) => t >= m.at);
  const next = msgs.find((m) => t < m.at && m.from === 'bot' && m.at - t < typingBefore);
  const bubble = (m: ChatMsg, i: number) => {
    const a = prog(t, m.at, m.at + 0.25, ease.outCubic);
    const me = m.from === 'me';
    return (
      <div key={i} style={{ display: 'flex', justifyContent: me ? 'flex-end' : 'flex-start', marginBottom: 8 * s, opacity: a, transform: `translateY(${(1 - a) * 18 * s}px) scale(${0.96 + 0.04 * a})`, transformOrigin: me ? '100% 100%' : '0% 100%' }}>
        <div style={{ maxWidth: '84%', borderRadius: 16 * s, borderBottomRightRadius: me ? 5 * s : 16 * s, borderBottomLeftRadius: me ? 16 * s : 5 * s, background: me ? '#6E4BFF' : '#1e1a3d', color: '#f2efff', padding: m.img ? 4 * s : `${8 * s}px ${11 * s}px`, ...F.mono(12.2 * s, 400), lineHeight: 1.42, whiteSpace: 'pre-wrap', overflow: 'hidden' }}>
          {m.img ? <Img src={staticFile(m.img)} style={{ display: 'block', width: '100%', borderRadius: 12 * s }} /> : m.text}
          {m.button ? (() => {
            const tap = m.tapAt !== undefined ? clamp((t - m.tapAt) / 0.5) : 0;
            const on = m.tapAt !== undefined && t >= m.tapAt;
            return (
              <div style={{ position: 'relative', overflow: 'hidden', marginTop: 8 * s, marginLeft: -11 * s, marginRight: -11 * s, marginBottom: -8 * s, padding: `${9 * s}px`, textAlign: 'center', background: on ? 'rgba(157,134,255,0.45)' : 'rgba(157,134,255,0.22)', color: '#efeaff', ...F.mono(12 * s, 600), borderTop: '1px solid rgba(255,255,255,0.08)' }}>
                {m.button} ↗
                {tap > 0 && tap < 1 ? <div style={{ position: 'absolute', left: '50%', top: '50%', width: 280 * s * tap, height: 280 * s * tap, marginLeft: -140 * s * tap, marginTop: -140 * s * tap, borderRadius: '50%', background: `rgba(255,255,255,${0.35 * (1 - tap)})` }} /> : null}
              </div>
            );
          })() : null}
        </div>
      </div>
    );
  };
  return (
    <PhoneFrame w={w} style={style} screenBg="#0e0b24">
      {/* header */}
      <div style={{ position: 'absolute', left: 0, right: 0, top: 0, height: 92 * s, paddingTop: 40 * s, boxSizing: 'border-box', display: 'flex', alignItems: 'center', gap: 10 * s, paddingLeft: 16 * s, background: '#17133a', borderBottom: '1px solid rgba(255,255,255,0.06)', zIndex: 2 }}>
        <div style={{ width: 36 * s, height: 36 * s, borderRadius: '50%', background: 'linear-gradient(135deg,#9D86FF,#6E4BFF)', display: 'flex', alignItems: 'center', justifyContent: 'center', ...F.archivo(16 * s, 900, 120), color: '#fff' }}>F</div>
        <div>
          <div style={{ ...F.archivo(15 * s, 700, 100), color: '#f2efff' }}>Fabius</div>
          <div style={{ ...F.mono(11 * s, 400), color: next ? '#9D86FF' : 'rgba(242,239,255,0.55)' }}>{next ? 'typing…' : 'bot'}</div>
        </div>
      </div>
      {/* messages, bottom-anchored */}
      <div style={{ position: 'absolute', left: 10 * s, right: 10 * s, top: 92 * s, bottom: 56 * s, display: 'flex', flexDirection: 'column', justifyContent: 'flex-end', overflow: 'hidden' }}>
        {shown.map(bubble)}
      </div>
      {/* input */}
      <div style={{ position: 'absolute', left: 0, right: 0, bottom: 0, height: 56 * s, background: '#17133a', display: 'flex', alignItems: 'center', padding: `0 ${14 * s}px`, ...F.mono(12 * s, 400), color: 'rgba(242,239,255,0.4)', borderTop: '1px solid rgba(255,255,255,0.06)' }}>
        Message
        <div style={{ marginLeft: 'auto', width: 30 * s, height: 30 * s, borderRadius: '50%', background: rgba('violet', 0.9), opacity: clamp(1) }} />
      </div>
    </PhoneFrame>
  );
};

/** Plays a run of stills as a flipbook (k = 0..1 through the run), crossfading between neighbours. */
export const FlipBook: React.FC<{ frames: string[]; k: number; style?: React.CSSProperties }> = ({ frames, k, style }) => {
  const x = clamp(k) * (frames.length - 1);
  const i = Math.floor(x), f = x - i;
  const a = frames[i]!, b = frames[Math.min(frames.length - 1, i + 1)]!;
  return (
    <div style={{ position: 'absolute', inset: 0, ...style }}>
      <Img src={staticFile(a)} style={{ position: 'absolute', inset: 0, width: '100%' }} />
      {f > 0.01 && b !== a ? <Img src={staticFile(b)} style={{ position: 'absolute', inset: 0, width: '100%', opacity: f }} /> : null}
    </div>
  );
};

/** A 3D stage for a device: tilt + float. */
export const Tilt: React.FC<{ x: number; y: number; rx?: number; ry?: number; rz?: number; s?: number; children: React.ReactNode; perspective?: number; opacity?: number }> = ({ x, y, rx = 0, ry = 0, rz = 0, s = 1, children, perspective = 1600, opacity = 1 }) => (
  <div style={{ position: 'absolute', left: x, top: y, opacity, transform: `perspective(${perspective}px) rotateX(${rx}deg) rotateY(${ry}deg) rotateZ(${rz}deg) scale(${s})`, transformStyle: 'preserve-3d', transformOrigin: '0 0' }}>{children}</div>
);

/** A pointer that travels between keyed positions and clicks (ripple at the tip). Coordinates in its parent's space. */
export const Cursor: React.FC<{ t: number; keys: { t: number; x: number; y: number }[]; clicks?: number[]; scale?: number; dark?: boolean }> = ({ t, keys, clicks = [], scale = 1, dark = false }) => {
  if (!keys.length || t < keys[0]!.t - 0.25) return null;
  let x = keys[0]!.x, y = keys[0]!.y;
  for (let i = 1; i < keys.length; i++) {
    const a = keys[i - 1]!, b = keys[i]!;
    if (t <= a.t) break;
    const k = ease.inOutCubic(clamp((t - a.t) / Math.max(1e-3, b.t - a.t)));
    x = a.x + (b.x - a.x) * k; y = a.y + (b.y - a.y) * k;
  }
  const appear = clamp((t - (keys[0]!.t - 0.25)) / 0.25);
  const press = clicks.reduce((m, c) => Math.max(m, t >= c && t < c + 0.18 ? 1 - Math.abs((t - c) / 0.09 - 1) : 0), 0);
  return (
    <div style={{ position: 'absolute', left: x, top: y, width: 0, height: 0, opacity: appear, pointerEvents: 'none', zIndex: 20 }}>
      {clicks.map((c, i) => {
        const r = clamp((t - c) / 0.5);
        if (t < c || r >= 1) return null;
        return <div key={i} style={{ position: 'absolute', left: -60 * r * scale, top: -60 * r * scale, width: 120 * r * scale, height: 120 * r * scale, borderRadius: '50%', border: `${2.5 * scale}px solid ${dark ? 'rgba(255,255,255,0.8)' : 'rgba(110,75,255,0.85)'}`, opacity: 1 - r }} />;
      })}
      <svg width={30 * scale} height={36 * scale} viewBox="0 0 30 36" style={{ position: 'absolute', left: -2 * scale, top: -2 * scale, transform: `scale(${1 - 0.12 * press})`, transformOrigin: '2px 2px', filter: 'drop-shadow(0 4px 6px rgba(10,6,40,0.45))' }}>
        <path d="M 2 2 L 2 27 L 8.5 21 L 12.5 31 L 17 29 L 13 19.5 L 21.5 19.5 Z" fill="#ffffff" stroke="#15122B" strokeWidth={1.6} strokeLinejoin="round" />
      </svg>
    </div>
  );
};
