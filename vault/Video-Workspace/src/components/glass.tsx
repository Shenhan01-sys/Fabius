// The web's core object (docs/design/landing.md): a glass block = one signal, in three states —
// empty (fogged clear glass: a slot not yet filled), sealed (deep indigo: committed, contents hidden),
// open (glowing white-violet: revealed and recomputed, SAH). Plus the web's glass panel.
import React from 'react';
import { C, glass, rgba } from '../lib/palette';
import { clamp } from '../lib/util';

export type BlockState = 'empty' | 'sealed' | 'open';

/** Isometric cube centred at (x, y), edge s. `k` blends sealed -> open (0..1) when state is 'open'. Use inside <svg>. */
export const GlassCube: React.FC<{ x: number; y: number; s: number; state: BlockState; k?: number; light?: boolean; opacity?: number; rot?: number }> = ({ x, y, s, state, k = 1, light = false, opacity = 1, rot = 0 }) => {
  const c30 = Math.cos(Math.PI / 6), h = s * 0.5;
  const T = { x, y: y - s }; // top vertex
  const top = [T, { x: x + s * c30, y: y - h }, { x, y }, { x: x - s * c30, y: y - h }];
  const left = [{ x: x - s * c30, y: y - h }, { x, y }, { x, y: y + s }, { x: x - s * c30, y: y + h }];
  const right = [{ x, y }, { x: x + s * c30, y: y - h }, { x: x + s * c30, y: y + h }, { x, y: y + s }];
  const pts = (ps: { x: number; y: number }[]) => ps.map((p) => `${p.x.toFixed(1)},${p.y.toFixed(1)}`).join(' ');
  let f: [string, string, string], edge: string, glow = 0;
  if (state === 'empty') {
    f = light ? ['rgba(255,255,255,0.75)', 'rgba(255,255,255,0.45)', 'rgba(255,255,255,0.3)'] : ['rgba(255,255,255,0.10)', 'rgba(255,255,255,0.05)', 'rgba(255,255,255,0.03)'];
    edge = light ? rgba('violet', 0.35) : 'rgba(255,255,255,0.32)';
  } else if (state === 'sealed') {
    f = [C.night3, C.night2, C.indigo];
    edge = rgba('violet', 0.95);
  } else {
    const kk = clamp(k);
    const m = (a: string, b: string) => (kk >= 1 ? b : kk <= 0 ? a : b);
    f = [m(C.night3, '#F7F4FF'), m(C.night2, C.lav3), m(C.indigo, C.violet2)];
    edge = kk > 0.5 ? 'rgba(255,255,255,0.9)' : rgba('violet', 0.95);
    glow = kk;
  }
  return (
    <g opacity={opacity} transform={rot ? `rotate(${rot} ${x} ${y})` : undefined} style={glow ? { filter: `drop-shadow(0 0 ${10 + 14 * glow}px ${rgba('violet2', 0.85 * glow)})` } : undefined}>
      <polygon points={pts(left)} fill={f[1]} stroke={edge} strokeWidth={1.2} strokeLinejoin="round" />
      <polygon points={pts(right)} fill={f[2]} stroke={edge} strokeWidth={1.2} strokeLinejoin="round" />
      <polygon points={pts(top)} fill={f[0]} stroke={edge} strokeWidth={1.2} strokeLinejoin="round" />
    </g>
  );
};

/** A real 3D cube (CSS 3D, six faces) — the web's crystal: sealed indigo glass with violet edges, or lit white-violet. */
export const Cube3D: React.FC<{ x: number; y: number; s: number; rx: number; ry: number; lit?: number; opacity?: number; perspective?: number }> = ({ x, y, s, rx, ry, lit = 0, opacity = 1, perspective = 1400 }) => {
  const h = s / 2;
  const face = (tf: string, shade: number) => {
    const sealed = `linear-gradient(135deg, rgba(${Math.round(40 + 30 * shade)},${Math.round(30 + 24 * shade)},${Math.round(110 + 60 * shade)},0.92), rgba(18,14,46,0.95))`;
    const open = `linear-gradient(135deg, rgba(255,255,255,${0.95 - 0.2 * shade}), rgba(201,189,242,${0.85 - 0.2 * shade}))`;
    return (
      <div style={{ position: 'absolute', width: s, height: s, transform: tf, background: lit >= 1 ? open : sealed, border: `2px solid ${lit > 0.5 ? 'rgba(255,255,255,0.95)' : rgba('violet2', 0.9)}`, boxShadow: `inset 0 0 ${s * 0.25}px rgba(157,134,255,${0.35 + 0.4 * lit})`, backfaceVisibility: 'visible' }} />
    );
  };
  return (
    <div style={{ position: 'absolute', left: x - h, top: y - h, width: s, height: s, perspective, opacity, filter: lit > 0 ? `drop-shadow(0 0 ${30 * lit}px ${rgba('violet2', 0.9 * lit)})` : undefined }}>
      <div style={{ position: 'absolute', inset: 0, transformStyle: 'preserve-3d', transform: `rotateX(${rx}deg) rotateY(${ry}deg)` }}>
        {face(`translateZ(${h}px)`, 0.6)}
        {face(`rotateY(180deg) translateZ(${h}px)`, 0.2)}
        {face(`rotateY(90deg) translateZ(${h}px)`, 0.4)}
        {face(`rotateY(-90deg) translateZ(${h}px)`, 0.3)}
        {face(`rotateX(90deg) translateZ(${h}px)`, 1)}
        {face(`rotateX(-90deg) translateZ(${h}px)`, 0.1)}
      </div>
    </div>
  );
};

/** A glass panel (absolute positioned div). */
export const Panel: React.FC<{ dark?: boolean; style?: React.CSSProperties; children?: React.ReactNode; radius?: number }> = ({ dark = true, style, children, radius = 22 }) => (
  <div style={{ position: 'absolute', borderRadius: radius, ...glass(dark), ...style }}>{children}</div>
);
