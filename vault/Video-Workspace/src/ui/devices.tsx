// Devices for the "use it" moments: a phone (Telegram chat drawn from the bot's real reply templates in
// tools/x402_sinyal.py: HELP, _teaser_en, tg_reply) and an agent terminal (real MCP tool names from
// fabius-one.vercel.app/mcp tools/list and the gate's real HTTP 402 answer, fetched 7 Oct into public/data/live/).
import React from 'react';
import { Img, staticFile } from 'remotion';
import { C, rgba } from '../lib/palette';
import { archivo, inter, mono } from '../lib/fonts';
import { clamp, ease, prog } from '../lib/util';

export const Phone: React.FC<{ w?: number; children?: React.ReactNode; screen?: string; style?: React.CSSProperties; glare?: number }> = ({ w = 420, children, screen = '#0e0b24', style, glare = 0.5 }) => {
  const h = w * 2.06, r = w * 0.16, bez = w * 0.032;
  return (
    <div style={{ position: 'absolute', left: -w / 2, top: -h / 2, width: w, height: h, borderRadius: r, background: 'linear-gradient(145deg, #2a2450, #0b0920 40%, #1a1540)', padding: bez, boxSizing: 'border-box', boxShadow: `0 60px 140px -30px ${rgba('violet', 0.55)}, 0 0 0 1.5px rgba(255,255,255,0.14) inset, 0 0 0 1px ${rgba('violet2', 0.35)}`, ...style }}>
      <div style={{ position: 'relative', width: '100%', height: '100%', borderRadius: r - bez, overflow: 'hidden', background: screen }}>
        {children}
        <div style={{ position: 'absolute', left: '50%', top: w * 0.028, width: w * 0.3, height: w * 0.078, marginLeft: -w * 0.15, borderRadius: 999, background: '#05040f' }} />
        <div style={{ position: 'absolute', inset: 0, background: `linear-gradient(125deg, rgba(255,255,255,${0.14 * glare}) 0%, rgba(255,255,255,0) 38%)`, pointerEvents: 'none' }} />
      </div>
    </div>
  );
};

export interface ChatMsg { at: number; from: 'me' | 'bot'; text?: string; button?: string; tapAt?: number; img?: string; blur?: number; note?: string }

/** Telegram (dark theme) inside a phone screen (fills its parent). Messages appear at `at`; the newest is kept in view. */
export const TelegramChat: React.FC<{ t: number; msgs: ChatMsg[]; w: number; typingLead?: number }> = ({ t, msgs, w, typingLead = 0.8 }) => {
  const s = w / 400;
  const shown = msgs.filter((m) => t >= m.at);
  const typing = msgs.some((m) => m.from === 'bot' && t < m.at && m.at - t < typingLead);
  return (
    <div style={{ position: 'absolute', inset: 0, background: 'linear-gradient(180deg, #120e2c, #0d0a22)' }}>
      <div style={{ position: 'absolute', left: 0, right: 0, top: 0, height: 96 * s, paddingTop: 42 * s, boxSizing: 'border-box', display: 'flex', alignItems: 'center', gap: 11 * s, paddingLeft: 16 * s, background: 'rgba(29,23,66,0.96)', borderBottom: '1px solid rgba(255,255,255,0.06)', zIndex: 2 }}>
        <div style={{ width: 38 * s, height: 38 * s, borderRadius: '50%', background: `linear-gradient(135deg, ${C.violet2}, ${C.violet})`, display: 'flex', alignItems: 'center', justifyContent: 'center', ...archivo(17 * s, 900, 110), color: '#fff' }}>F</div>
        <div>
          <div style={{ ...inter(16 * s, 600), color: '#f2efff' }}>Fabius</div>
          <div style={{ ...inter(12 * s, 400), color: typing ? C.violet2 : 'rgba(242,239,255,0.55)' }}>{typing ? 'typing…' : 'bot'}</div>
        </div>
      </div>
      <div style={{ position: 'absolute', left: 10 * s, right: 10 * s, top: 100 * s, bottom: 60 * s, display: 'flex', flexDirection: 'column', justifyContent: 'flex-end', overflow: 'hidden' }}>
        {shown.map((m, i) => {
          const a = prog(t, m.at, m.at + 0.3, ease.outCubic);
          const me = m.from === 'me';
          return (
            <div key={i} style={{ display: 'flex', justifyContent: me ? 'flex-end' : 'flex-start', marginBottom: 8 * s, opacity: a, transform: `translateY(${(1 - a) * 20 * s}px) scale(${0.94 + 0.06 * a})`, transformOrigin: me ? '100% 100%' : '0% 100%' }}>
              <div style={{ maxWidth: '86%', borderRadius: 17 * s, borderBottomRightRadius: me ? 5 * s : 17 * s, borderBottomLeftRadius: me ? 17 * s : 5 * s, background: me ? `linear-gradient(135deg, #7d5cff, ${C.violet})` : '#221d4a', color: '#f2efff', padding: m.img ? 4 * s : `${9 * s}px ${12 * s}px`, ...inter(13.2 * s, 400), lineHeight: 1.42, whiteSpace: 'pre-wrap', overflow: 'hidden', boxShadow: '0 4px 14px rgba(0,0,0,0.25)' }}>
                {m.img ? (
                  <div style={{ position: 'relative', borderRadius: 13 * s, overflow: 'hidden' }}>
                    <Img src={staticFile(m.img)} style={{ display: 'block', width: '100%', filter: m.blur ? `blur(${m.blur * s}px)` : undefined }} />
                    {m.note ? <div style={{ position: 'absolute', left: 0, right: 0, bottom: 0, padding: `${8 * s}px ${10 * s}px`, background: 'rgba(14,11,36,0.82)', ...mono(11 * s, 600), color: C.violet2, letterSpacing: 0.4 }}>{m.note}</div> : null}
                  </div>
                ) : m.text}
                {m.button ? (() => {
                  const on = m.tapAt !== undefined && t >= m.tapAt;
                  const r = m.tapAt !== undefined ? clamp((t - m.tapAt) / 0.5) : 0;
                  return (
                    <div style={{ position: 'relative', overflow: 'hidden', margin: `${9 * s}px ${-12 * s}px ${-9 * s}px`, padding: `${10 * s}px`, textAlign: 'center', background: on ? 'rgba(157,134,255,0.48)' : 'rgba(157,134,255,0.2)', borderTop: '1px solid rgba(255,255,255,0.08)', ...inter(13 * s, 600), color: '#efeaff' }}>
                      {m.button} ↗
                      {r > 0 && r < 1 ? <div style={{ position: 'absolute', left: '50%', top: '50%', width: 300 * s * r, height: 300 * s * r, marginLeft: -150 * s * r, marginTop: -150 * s * r, borderRadius: '50%', background: `rgba(255,255,255,${0.35 * (1 - r)})` }} /> : null}
                    </div>
                  );
                })() : null}
              </div>
            </div>
          );
        })}
      </div>
      <div style={{ position: 'absolute', left: 0, right: 0, bottom: 0, height: 60 * s, background: 'rgba(29,23,66,0.96)', display: 'flex', alignItems: 'center', padding: `0 ${16 * s}px`, ...inter(14 * s, 400), color: 'rgba(242,239,255,0.4)', borderTop: '1px solid rgba(255,255,255,0.06)' }}>
        Message
        <div style={{ marginLeft: 'auto', width: 32 * s, height: 32 * s, borderRadius: '50%', background: C.violet }} />
      </div>
    </div>
  );
};

export interface TermLine { at: number; text: string; kind?: 'cmd' | 'out' | 'ok' | 'warn' | 'dim' | 'json'; cps?: number }

/** An agent's terminal: commands type in, answers print. Dark glass, the site's mono. */
export const Terminal: React.FC<{ t: number; lines: TermLine[]; w: number; h: number; title?: string }> = ({ t, lines, w, h, title = 'agent · mcp client' }) => {
  const s = w / 900;
  const col = (k?: TermLine['kind']) => (k === 'ok' ? '#7ef0c0' : k === 'warn' ? '#ffb86b' : k === 'dim' ? 'rgba(236,232,250,0.45)' : k === 'json' ? C.violet2 : k === 'cmd' ? '#ffffff' : 'rgba(236,232,250,0.86)');
  return (
    <div style={{ position: 'absolute', left: -w / 2, top: -h / 2, width: w, height: h, borderRadius: 18 * s, overflow: 'hidden', background: 'linear-gradient(180deg, rgba(26,20,66,0.97), rgba(15,11,38,0.98))', border: '1px solid rgba(157,134,255,0.3)', boxShadow: `0 50px 120px -30px ${rgba('violet', 0.6)}` }}>
      <div style={{ height: 40 * s, display: 'flex', alignItems: 'center', gap: 8 * s, padding: `0 ${16 * s}px`, borderBottom: '1px solid rgba(255,255,255,0.06)', background: 'rgba(255,255,255,0.03)' }}>
        {['#ff6058', '#ffbd2e', '#28c941'].map((c) => <div key={c} style={{ width: 11 * s, height: 11 * s, borderRadius: '50%', background: c, opacity: 0.85 }} />)}
        <div style={{ marginLeft: 14 * s, ...mono(13 * s, 500), color: 'rgba(236,232,250,0.55)', letterSpacing: 0.5 }}>{title}</div>
      </div>
      <div style={{ padding: `${18 * s}px ${22 * s}px`, display: 'flex', flexDirection: 'column', gap: 7 * s, justifyContent: 'flex-end', position: 'absolute', left: 0, right: 0, top: 40 * s, bottom: 0, overflow: 'hidden' }}>
        {lines.filter((l) => t >= l.at).map((l, i) => {
          const cps = l.cps ?? (l.kind === 'cmd' ? 34 : 400);
          const n = Math.min(l.text.length, Math.floor((t - l.at) * cps));
          const done = n >= l.text.length;
          return (
            <div key={i} style={{ ...mono(21 * s, l.kind === 'cmd' ? 600 : 400), color: col(l.kind), whiteSpace: 'pre-wrap', wordBreak: 'break-word' }}>
              {l.kind === 'cmd' ? <span style={{ color: C.violet2 }}>❯ </span> : null}
              {l.text.slice(0, n)}
              {l.kind === 'cmd' && !done ? <span style={{ display: 'inline-block', width: 9 * s, height: 19 * s, background: '#fff', verticalAlign: -3 * s, marginLeft: 2 }} /> : null}
            </div>
          );
        })}
      </div>
    </div>
  );
};
