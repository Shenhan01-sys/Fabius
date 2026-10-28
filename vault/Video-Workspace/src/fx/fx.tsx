// Finishing layers: grain, vignette, light sweeps across glass, soft glows, a flash for hard cuts, and particles that
// let a card dissolve softly (never a crash or a shatter: the client's rule).
import React from 'react';
import { AbsoluteFill, staticFile } from 'remotion';
import { rgba } from '../lib/palette';
import { clamp, ease, hash, TAU } from '../lib/util';

export const Grain: React.FC<{ frame: number; opacity?: number }> = ({ frame, opacity = 0.05 }) => {
  const g = Math.floor(frame / 2); // moves every second frame: alive, and kind to the encoder
  return <AbsoluteFill style={{ backgroundImage: `url(${staticFile('img/grain.png')})`, backgroundSize: '768px 768px', backgroundPosition: `${Math.floor(hash(g, 1) * 768)}px ${Math.floor(hash(g, 2) * 768)}px`, opacity, mixBlendMode: 'overlay', pointerEvents: 'none' }} />;
};

export const Vignette: React.FC<{ strength?: number; col?: string }> = ({ strength = 0.25, col = '21,18,43' }) => (
  <AbsoluteFill style={{ background: `radial-gradient(ellipse 75% 70% at 50% 50%, rgba(${col},0) 60%, rgba(${col},${strength}) 100%)`, pointerEvents: 'none' }} />
);

/** A diagonal light band crossing its parent (k = 0..1 through the sweep). Parent needs overflow hidden + radius. */
export const Sweep: React.FC<{ k: number; width?: number; strength?: number; angle?: number }> = ({ k, width = 30, strength = 0.45, angle = -18 }) =>
  k <= 0 || k >= 1 ? null : (
    <div style={{ position: 'absolute', inset: 0, overflow: 'hidden', pointerEvents: 'none', borderRadius: 'inherit' }}>
      <div style={{ position: 'absolute', top: '-30%', bottom: '-30%', width: `${width}%`, left: `${-50 + 170 * ease.inOutCubic(k)}%`, transform: `skewX(${angle}deg)`, background: `linear-gradient(90deg, rgba(255,255,255,0) 0%, rgba(255,255,255,${strength}) 50%, rgba(255,255,255,0) 100%)`, mixBlendMode: 'screen' }} />
    </div>
  );

/** Soft round glow (screen-blended). */
export const GlowBlob: React.FC<{ x: number; y: number; r: number; col?: string; a?: number }> = ({ x, y, r, col = 'violet', a = 0.5 }) => (
  <div style={{ position: 'absolute', left: x - r, top: y - r, width: 2 * r, height: 2 * r, borderRadius: '50%', background: `radial-gradient(circle, ${rgba(col, a)} 0%, ${rgba(col, a * 0.35)} 35%, ${rgba(col, 0)} 70%)`, mixBlendMode: 'screen', pointerEvents: 'none' }} />
);

/** A short flash around a cut (light, not white-out). */
export const Flash: React.FC<{ t: number; at: number; col?: string; strength?: number; len?: number }> = ({ t, at, col = 'white', strength = 0.65, len = 0.18 }) => {
  const k = t < at ? Math.pow(clamp((t - (at - 0.06)) / 0.06), 2) : Math.exp(-(t - at) / len);
  if (k < 0.004) return null;
  return <AbsoluteFill style={{ background: rgba(col, strength * k), pointerEvents: 'none' }} />;
};

/**
 * Soft dissolve: a rectangle (x, y, w, h) breaks into slowly drifting glowing motes from `t0` over `len` seconds -
 * use it on top of a card that fades out at the same time. Gentle drift upward, no explosion.
 */
export const Dissolve: React.FC<{ t: number; t0: number; len?: number; x: number; y: number; w: number; h: number; n?: number; col?: string; seed?: number }> = ({ t, t0, len = 1.4, x, y, w, h, n = 90, col = 'violet2', seed = 7 }) => {
  if (t < t0 || t > t0 + len + 0.6) return null;
  return (
    <AbsoluteFill style={{ pointerEvents: 'none' }}>
      {Array.from({ length: n }, (_, i) => {
        const d = hash(i, seed, 0) * 0.5; // stagger: left-to-right sweep
        const k = clamp((t - t0 - d * len * 0.6) / (len * 0.8));
        if (k <= 0 || k >= 1) return null;
        const px = x + w * hash(i, seed, 1), py = y + h * hash(i, seed, 2);
        const a = hash(i, seed, 3) * TAU;
        const dist = 30 + 90 * hash(i, seed, 4);
        const e = ease.outCubic(k);
        const s = 1.5 + 3 * hash(i, seed, 5);
        return <div key={i} style={{ position: 'absolute', left: px + Math.cos(a) * dist * e * 0.6, top: py - dist * e + Math.sin(a) * dist * 0.3 * e, width: s, height: s, borderRadius: '50%', background: rgba(col, (1 - k) * 0.9), boxShadow: `0 0 ${3 * s}px ${rgba(col, (1 - k) * 0.6)}` }} />;
      })}
    </AbsoluteFill>
  );
};

/** Horizontal motion blur (SVG filter) for whip moves; use `blur(id)` as a CSS filter value. */
export const HBlurDef: React.FC<{ id: string; sx: number }> = ({ id, sx }) => (
  <svg width={0} height={0} style={{ position: 'absolute' }}>
    <filter id={id} x="-20%" y="-5%" width="140%" height="110%"><feGaussianBlur stdDeviation={`${sx.toFixed(1)} 0`} /></filter>
  </svg>
);
