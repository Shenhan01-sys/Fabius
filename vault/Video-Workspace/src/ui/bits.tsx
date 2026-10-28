// Small pieces in the site's UI language: pills / chips, glass cards, callouts with a leader line, icons.
import React from 'react';
import { C, rgba } from '../lib/palette';
import { inter, label, mono } from '../lib/fonts';
import { clamp, ease, prog } from '../lib/util';

export const Check: React.FC<{ s?: number; col?: string; k?: number; tick?: string }> = ({ s = 22, col = C.violet, k = 1, tick = '#fff' }) => (
  <svg width={s} height={s} viewBox="0 0 24 24">
    <circle cx="12" cy="12" r="11" fill={col} opacity={0.14 + 0.86 * k} />
    <path d="M6.5 12.5 L10.4 16.2 L17.6 8.4" fill="none" stroke={tick} strokeWidth={2.6} strokeLinecap="round" strokeLinejoin="round" strokeDasharray="20" strokeDashoffset={20 * (1 - clamp(k))} />
  </svg>
);

export const LockIcon: React.FC<{ s?: number; col?: string; shut?: number }> = ({ s = 22, col = C.violet, shut = 1 }) => (
  <svg width={s} height={s * 1.15} viewBox="0 0 20 23">
    <rect x="2" y="10" width="16" height="12" rx="3" fill={col} />
    <path d={`M5.5 10 V${7 - 3 * (1 - shut)} a4.5 4.5 0 0 1 9 0 V${10 - 4 * (1 - shut)}`} fill="none" stroke={col} strokeWidth="2.4" strokeLinecap="round" />
    <circle cx="10" cy="15.6" r="1.8" fill="#fff" />
  </svg>
);

/** A pill (site buttons / tags). `fill` = violet button, otherwise white glass. */
export const Pill: React.FC<{ children: React.ReactNode; fill?: boolean; ink?: boolean; size?: number; icon?: React.ReactNode; style?: React.CSSProperties }> = ({ children, fill, ink, size = 22, icon, style }) => (
  <div style={{ display: 'inline-flex', alignItems: 'center', gap: size * 0.45, padding: `${size * 0.55}px ${size * 1.0}px`, borderRadius: 999, background: fill ? C.violet : ink ? C.ink : 'rgba(255,255,255,0.82)', color: fill || ink ? '#fff' : C.ink, border: fill || ink ? 'none' : `1px solid ${rgba('violet', 0.18)}`, boxShadow: fill ? `0 12px 30px -8px ${rgba('violet', 0.7)}` : `0 10px 30px -12px ${rgba('violet', 0.35)}`, ...inter(size, 600), whiteSpace: 'nowrap', ...style }}>
    {icon}
    {children}
  </div>
);

/** A white glass card in the site's style. */
export const Card: React.FC<{ w: number; h?: number; children?: React.ReactNode; style?: React.CSSProperties; dark?: boolean; pad?: number }> = ({ w, h, children, style, dark, pad = 28 }) => (
  <div style={{ width: w, height: h, boxSizing: 'border-box', padding: pad, borderRadius: 22, background: dark ? 'rgba(26,20,66,0.78)' : 'rgba(255,255,255,0.86)', border: `1px solid ${dark ? 'rgba(157,134,255,0.28)' : 'rgba(255,255,255,0.95)'}`, boxShadow: dark ? `0 40px 100px -30px rgba(0,0,0,0.6)` : `0 40px 100px -30px ${rgba('violet', 0.45)}`, backdropFilter: 'blur(16px)', color: dark ? '#f2efff' : C.ink, ...style }}>
    {children}
  </div>
);

/** Appear helper: rise + fade + slight scale from `at`. */
export function appear(t: number, at: number, dur = 0.5, dy = 26): React.CSSProperties {
  const k = prog(t, at, at + dur, ease.cine);
  return { opacity: clamp(k * 1.4), transform: `translateY(${(1 - k) * dy}px) scale(${0.96 + 0.04 * k})` };
}

/** A callout: a dot at (x, y), a leader line to (x + dx, y + dy), and a label card there. */
export const Callout: React.FC<{ t: number; at: number; x: number; y: number; dx: number; dy: number; title: string; sub?: string; dark?: boolean }> = ({ t, at, x, y, dx, dy, title, sub, dark }) => {
  const k = prog(t, at, at + 0.45, ease.outCubic), k2 = prog(t, at + 0.25, at + 0.7, ease.cine);
  if (t < at) return null;
  const len = Math.hypot(dx, dy);
  return (
    <div style={{ position: 'absolute', left: x, top: y, width: 0, height: 0 }}>
      <div style={{ position: 'absolute', left: -7, top: -7, width: 14, height: 14, borderRadius: '50%', background: C.violet, boxShadow: `0 0 0 ${6 * k}px ${rgba('violet', 0.22)}`, transform: `scale(${k})` }} />
      <div style={{ position: 'absolute', left: 0, top: 0, width: len * k, height: 2, background: rgba('violet', 0.8), transformOrigin: '0 50%', transform: `rotate(${Math.atan2(dy, dx)}rad)` }} />
      <div style={{ position: 'absolute', left: dx, top: dy, transform: `translate(${dx >= 0 ? 0 : -100}%, -50%) translateY(${(1 - k2) * 14}px)`, opacity: k2, padding: '14px 20px', borderRadius: 16, background: dark ? 'rgba(26,20,66,0.86)' : 'rgba(255,255,255,0.92)', border: `1px solid ${rgba('violet', 0.25)}`, boxShadow: `0 20px 50px -18px ${rgba('violet', 0.55)}`, whiteSpace: 'nowrap' }}>
        <div style={{ ...label(13, 600), color: C.violet }}>{title}</div>
        {sub ? <div style={{ ...inter(20, 600), color: dark ? '#f2efff' : C.ink, marginTop: 4 }}>{sub}</div> : null}
      </div>
    </div>
  );
};

/** A small mono tag (e.g. "ERC-8004 · #2558"). */
export const Tag: React.FC<{ children: React.ReactNode; dark?: boolean; size?: number; style?: React.CSSProperties }> = ({ children, dark, size = 15, style }) => (
  <div style={{ display: 'inline-flex', alignItems: 'center', gap: 6, padding: `${size * 0.4}px ${size * 0.8}px`, borderRadius: 999, background: dark ? 'rgba(157,134,255,0.16)' : 'rgba(110,75,255,0.09)', border: `1px solid ${rgba('violet', dark ? 0.4 : 0.22)}`, ...mono(size, 600), color: dark ? C.violet2 : C.violet, whiteSpace: 'nowrap', letterSpacing: 0.3, ...style }}>{children}</div>
);
