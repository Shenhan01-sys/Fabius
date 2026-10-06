// Motion everywhere: a keyframed 3D camera over each plate's 1920x1080 world (push-ins, pans, tilts) plus a
// continuous handheld drift, and an ambient layer (soft orbs and dust) that sits at its own depth so the
// camera produces parallax. Pure functions of t.
import React from 'react';
import { AbsoluteFill } from 'remotion';
import { rgba } from '../lib/palette';
import { clamp, ease, hash, lerp, noise1, type Ease } from '../lib/util';
import { GlassCube } from './glass';

export interface CamKey { t: number; x?: number; y?: number; s?: number; rx?: number; ry?: number; rz?: number; ez?: Ease }
export interface Cam { x: number; y: number; s: number; rx: number; ry: number; rz: number }
const BASE: Cam = { x: 0, y: 0, s: 1, rx: 0, ry: 0, rz: 0 };

/** Camera state at t: keys hold their values; each move eases into the key that ends it. */
export function camAt(keys: CamKey[], t: number): Cam {
  const ks = [...keys].sort((a, b) => a.t - b.t);
  const full = (k: CamKey, prev: Cam): Cam => ({ x: k.x ?? prev.x, y: k.y ?? prev.y, s: k.s ?? prev.s, rx: k.rx ?? prev.rx, ry: k.ry ?? prev.ry, rz: k.rz ?? prev.rz });
  if (!ks.length) return BASE;
  let prev = full(ks[0]!, BASE);
  if (t <= ks[0]!.t) return prev;
  for (let i = 1; i < ks.length; i++) {
    const b = full(ks[i]!, prev);
    if (t <= ks[i]!.t) {
      const k = (ks[i]!.ez ?? ease.inOutCubic)(clamp((t - ks[i - 1]!.t) / Math.max(1e-4, ks[i]!.t - ks[i - 1]!.t)));
      return { x: lerp(prev.x, b.x, k), y: lerp(prev.y, b.y, k), s: Math.exp(lerp(Math.log(prev.s), Math.log(b.s), k)), rx: lerp(prev.rx, b.rx, k), ry: lerp(prev.ry, b.ry, k), rz: lerp(prev.rz, b.rz, k) };
    }
    prev = b;
  }
  return prev;
}

/** Slow handheld drift (px, deg). */
export function drift(t: number, amp = 1): Cam {
  return { x: 7 * amp * noise1(t * 0.35, 11), y: 5 * amp * noise1(t * 0.31, 12), s: 1, rx: 0.5 * amp * noise1(t * 0.27, 13), ry: 0.6 * amp * noise1(t * 0.23, 14), rz: 0.18 * amp * noise1(t * 0.2, 15) };
}

/**
 * The camera: the world is shifted by (-x, -y) (camera looks at screen centre + (x, y)), scaled about the
 * centre, and rotated in 3D with perspective. `depth` < 1 = a far layer (parallax: it moves and scales less).
 */
export const Camera: React.FC<{ t: number; keys: CamKey[]; drift?: number; depth?: number; perspective?: number; children: React.ReactNode; style?: React.CSSProperties }> = ({ t, keys, drift: d = 1, depth = 1, perspective = 1800, children, style }) => {
  const c = camAt(keys, t), n = drift(t, d);
  const x = (c.x + n.x) * depth, y = (c.y + n.y) * depth;
  const s = Math.pow(c.s, depth);
  const tf = `perspective(${perspective}px) rotateX(${(c.rx + n.rx) * depth}deg) rotateY(${(c.ry + n.ry) * depth}deg) rotateZ(${(c.rz + n.rz) * depth}deg) scale(${s}) translate(${-x}px, ${-y}px)`;
  return <AbsoluteFill style={{ transform: tf, transformOrigin: '50% 50%', ...style }}>{children}</AbsoluteFill>;
};

/** Soft out-of-focus orbs drifting at their own depth (bokeh), and fine dust. */
export const Ambient: React.FC<{ t: number; light?: boolean; n?: number; seed?: number; dust?: number; strength?: number; cubes?: number }> = ({ t, light = false, n = 7, seed = 1, dust = 40, strength = 1, cubes = 0 }) => {
  const orbs = Array.from({ length: n }, (_, i) => {
    const r = 120 + 260 * hash(i, seed, 1);
    const x = 1920 * hash(i, seed, 2) + 140 * noise1(t * 0.08 + i * 3.1, seed + i);
    const y = 1080 * hash(i, seed, 3) + 110 * noise1(t * 0.07 + i * 5.3, seed + 40 + i);
    const a = (light ? 0.5 : 0.22) * (0.5 + 0.5 * hash(i, seed, 4)) * strength;
    const col = light ? (hash(i, seed, 5) > 0.5 ? 'white' : 'lav3') : hash(i, seed, 5) > 0.35 ? 'violet' : 'violet2';
    return (
      <div key={i} style={{ position: 'absolute', left: x - r, top: y - r, width: 2 * r, height: 2 * r, borderRadius: '50%', background: `radial-gradient(circle, ${rgba(col, a)} 0%, ${rgba(col, a * 0.45)} 38%, ${rgba(col, 0)} 70%)` }} />
    );
  });
  const motes = Array.from({ length: dust }, (_, i) => {
    const sp = 6 + 14 * hash(i, seed, 7);
    const x = (1920 * hash(i, seed, 8) + t * sp * (hash(i, seed, 9) - 0.3)) % 1920;
    const y = (1080 * hash(i, seed, 10) - t * sp * 0.6 + 2160) % 1080;
    const s = 1 + 2.2 * hash(i, seed, 11);
    const a = (light ? 0.35 : 0.5) * (0.3 + 0.7 * hash(i, seed, 12)) * (0.6 + 0.4 * Math.sin(t * 1.3 + i));
    return <div key={`d${i}`} style={{ position: 'absolute', left: x, top: y, width: s, height: s, borderRadius: '50%', background: light ? rgba('violet', a * 0.6) : rgba('lav', a) }} />;
  });
  // floating glass blocks: mostly empty glass, some sealed indigo, one lit (the web's three block states)
  const blocks = Array.from({ length: cubes }, (_, i) => {
    const sz = 16 + 30 * hash(i, seed, 20);
    const x = 1920 * (0.04 + 0.92 * hash(i, seed, 21)) + 50 * noise1(t * 0.12 + i * 2.3, seed + 80 + i);
    const y = 1080 * (0.06 + 0.88 * hash(i, seed, 22)) + 26 * Math.sin(t * (0.5 + 0.4 * hash(i, seed, 23)) + i * 1.7);
    const st = hash(i, seed, 24);
    const state = st < 0.62 ? 'empty' : st < 0.9 ? 'sealed' : 'open';
    return <GlassCube key={`c${i}`} x={x} y={y} s={sz} state={state} k={1} light={light} opacity={(light ? 0.55 : 0.45) + 0.4 * hash(i, seed, 25)} />;
  });
  return (
    <AbsoluteFill style={{ pointerEvents: 'none' }}>
      {orbs}{motes}
      {cubes > 0 && <svg width={1920} height={1080} style={{ position: 'absolute', inset: 0, overflow: 'visible' }}>{blocks}</svg>}
    </AbsoluteFill>
  );
};
