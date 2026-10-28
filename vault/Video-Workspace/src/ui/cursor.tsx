// The pointer that drives the real pages: positions come from the capture (where the mouse really was on every
// frame) or from keys; clicks get a press + a violet ripple. Drawn on top of the window, in the window's plane.
import React from 'react';
import { rgba } from '../lib/palette';
import { clamp, ease } from '../lib/util';

export interface CurKey { t: number; x: number; y: number }

/** Position on a keyed path (eased between keys, holds before/after). */
export function curAt(keys: CurKey[], t: number): { x: number; y: number } {
  if (!keys.length) return { x: 0, y: 0 };
  if (t <= keys[0]!.t) return keys[0]!;
  for (let i = 1; i < keys.length; i++) {
    const a = keys[i - 1]!, b = keys[i]!;
    if (t <= b.t) {
      const k = ease.inOutCubic(clamp((t - a.t) / Math.max(1e-3, b.t - a.t)));
      // a slight arc, like a hand moving a mouse
      const arc = Math.sin(Math.PI * k) * Math.min(40, Math.hypot(b.x - a.x, b.y - a.y) * 0.08);
      return { x: a.x + (b.x - a.x) * k, y: a.y + (b.y - a.y) * k - arc };
    }
  }
  return keys[keys.length - 1]!;
}

export const Cursor: React.FC<{ t: number; x: number; y: number; clicks?: number[]; scale?: number; opacity?: number; dark?: boolean }> = ({ t, x, y, clicks = [], scale = 1, opacity = 1, dark = false }) => {
  const press = clicks.reduce((m, c) => Math.max(m, t >= c - 0.06 && t < c + 0.14 ? 1 - Math.abs((t - c - 0.04) / 0.1) : 0), 0);
  return (
    <div style={{ position: 'absolute', left: x, top: y, width: 0, height: 0, opacity, pointerEvents: 'none' }}>
      {clicks.map((c, i) => {
        const r = clamp((t - c) / 0.55);
        if (t < c || r >= 1) return null;
        const e = ease.outCubic(r);
        return (
          <React.Fragment key={i}>
            <div style={{ position: 'absolute', left: -56 * e * scale, top: -56 * e * scale, width: 112 * e * scale, height: 112 * e * scale, borderRadius: '50%', border: `${2.5 * scale}px solid ${rgba('violet', 0.85 * (1 - r))}` }} />
            <div style={{ position: 'absolute', left: -22 * scale, top: -22 * scale, width: 44 * scale, height: 44 * scale, borderRadius: '50%', background: rgba('violet2', 0.45 * (1 - r)), filter: `blur(${6 * scale}px)` }} />
          </React.Fragment>
        );
      })}
      <svg width={30 * scale} height={38 * scale} viewBox="0 0 30 38" style={{ position: 'absolute', left: -3 * scale, top: -2 * scale, transform: `scale(${1 - 0.14 * press})`, transformOrigin: '3px 2px', filter: `drop-shadow(0 ${5 * scale}px ${7 * scale}px rgba(21,18,43,0.35))` }}>
        <path d="M 3 2 L 3 29 L 9.6 22.6 L 13.8 33 L 18.6 31 L 14.4 20.8 L 23.4 20.8 Z" fill={dark ? '#15122b' : '#ffffff'} stroke={dark ? '#ffffff' : '#15122b'} strokeWidth={1.7} strokeLinejoin="round" />
      </svg>
    </div>
  );
};
