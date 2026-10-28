// The two worlds the video lives in, both drawn from the site: LAV (the site's light lavender, the default) and NIGHT
// (deep indigo, for the problem and the AI desk at work). Each has depth: glows, out-of-focus glass blocks and dust at
// their own distance, shifted by the camera so every camera move produces parallax.
import React from 'react';
import { AbsoluteFill } from 'remotion';
import { C, rgba } from '../lib/palette';
import { hash, noise1, TAU } from '../lib/util';
import type { Cam } from '../cam/space';

const W = 1920, H = 1080;
const par = (cam: Cam | undefined, depth: number) => ({
  x: cam ? -(cam.x * 0.15 + cam.ry * 14) * depth : 0,
  y: cam ? -(cam.y * 0.15 - cam.rx * 10) * depth : 0,
});

/** A soft out-of-focus glass block (bokeh) - the site's crystal motif, far away. */
const BokehBlock: React.FC<{ x: number; y: number; s: number; rot: number; tint: string; a: number; blur: number }> = ({ x, y, s, rot, tint, a, blur }) => (
  <div style={{
    position: 'absolute', left: x - s / 2, top: y - s / 2, width: s, height: s, borderRadius: s * 0.18, transform: `rotate(${rot}deg)`,
    background: `linear-gradient(135deg, ${rgba('white', 0.55 * a)}, ${rgba(tint, 0.35 * a)})`, border: `1px solid ${rgba('white', 0.5 * a)}`,
    boxShadow: `0 0 ${s * 0.4}px ${rgba(tint, 0.25 * a)}`, filter: blur > 0.3 ? `blur(${blur.toFixed(1)}px)` : undefined,
  }} />
);

export const LavWorld: React.FC<{ t: number; cam?: Cam; seed?: number; blocks?: number; dust?: number; glow?: number }> = ({ t, cam, seed = 1, blocks = 14, dust = 70, glow = 1 }) => {
  const far = par(cam, 0.35), mid = par(cam, 0.8), near = par(cam, 1.6);
  return (
    <AbsoluteFill style={{ background: `linear-gradient(180deg, #f6f3ff 0%, ${C.lav} 46%, #e3dcf8 100%)`, overflow: 'hidden' }}>
      <div style={{ position: 'absolute', inset: -160, transform: `translate(${far.x}px, ${far.y}px)`, background: `radial-gradient(ellipse 70% 55% at 50% -12%, rgba(255,255,255,${0.95 * glow}) 0%, rgba(255,255,255,0) 70%), radial-gradient(ellipse 45% 40% at 88% 92%, ${rgba('violet2', 0.28 * glow)} 0%, ${rgba('violet2', 0)} 70%), radial-gradient(ellipse 40% 35% at 6% 70%, ${rgba('lav3', 0.55 * glow)} 0%, ${rgba('lav3', 0)} 70%)` }} />
      <AbsoluteFill style={{ transform: `translate(${mid.x}px, ${mid.y}px)` }}>
        {Array.from({ length: blocks }, (_, i) => {
          const d = hash(i, seed, 1); // 0 far .. 1 near
          const s = 26 + 90 * d * d;
          const x = W * (-0.05 + 1.1 * hash(i, seed, 2)) + 60 * noise1(t * 0.09 + i * 1.7, seed + i) + near.x * d;
          const y = H * (-0.05 + 1.1 * hash(i, seed, 3)) + 40 * noise1(t * 0.08 + i * 2.3, seed + 30 + i) + near.y * d;
          return <BokehBlock key={i} x={x} y={y} s={s} rot={360 * hash(i, seed, 4) + t * (8 + 10 * hash(i, seed, 5)) * (hash(i, seed, 6) > 0.5 ? 1 : -1)} tint={hash(i, seed, 7) > 0.6 ? 'violet' : 'lav3'} a={0.35 + 0.45 * hash(i, seed, 8)} blur={2 + 9 * Math.abs(d - 0.55) * 2} />;
        })}
      </AbsoluteFill>
      <Dust t={t} n={dust} seed={seed + 9} col="violet" a={0.4} shift={near} />
    </AbsoluteFill>
  );
};

export const NightWorld: React.FC<{ t: number; cam?: Cam; seed?: number; dust?: number; glow?: number; grid?: number }> = ({ t, cam, seed = 2, dust = 90, glow = 1, grid = 0.6 }) => {
  const far = par(cam, 0.35), near = par(cam, 1.6);
  return (
    <AbsoluteFill style={{ background: `radial-gradient(ellipse 90% 70% at 50% 22%, #2b2168 0%, ${C.night2} 38%, ${C.night} 78%)`, overflow: 'hidden' }}>
      <div style={{ position: 'absolute', inset: -160, transform: `translate(${far.x}px, ${far.y}px)`, background: `radial-gradient(ellipse 50% 40% at ${50 + 8 * noise1(t * 0.05, 3)}% 8%, ${rgba('violet', 0.42 * glow)} 0%, ${rgba('violet', 0)} 70%), radial-gradient(ellipse 35% 30% at 85% 85%, ${rgba('violet2', 0.18 * glow)} 0%, ${rgba('violet2', 0)} 70%), radial-gradient(ellipse 30% 30% at 10% 75%, ${rgba('violet', 0.16 * glow)} 0%, ${rgba('violet', 0)} 70%)` }} />
      {grid > 0 && (
        <div style={{ position: 'absolute', left: -W * 0.5, right: -W * 0.5, top: H * 0.58, height: H * 1.2, transformOrigin: '50% 0%', transform: `translateX(${near.x * 0.6}px) perspective(900px) rotateX(72deg)`, opacity: grid,
          backgroundImage: `linear-gradient(${rgba('violet2', 0.22)} 1px, transparent 1px), linear-gradient(90deg, ${rgba('violet2', 0.22)} 1px, transparent 1px)`, backgroundSize: '90px 90px', backgroundPosition: `0px ${(t * 30) % 90}px`,
          maskImage: 'linear-gradient(180deg, rgba(0,0,0,0) 0%, rgba(0,0,0,1) 25%, rgba(0,0,0,0) 85%)', WebkitMaskImage: 'linear-gradient(180deg, rgba(0,0,0,0) 0%, rgba(0,0,0,1) 25%, rgba(0,0,0,0) 85%)' }} />
      )}
      <Dust t={t} n={dust} seed={seed + 5} col="lav" a={0.55} shift={near} />
    </AbsoluteFill>
  );
};

/** Fine motes drifting upward at their own depths. */
export const Dust: React.FC<{ t: number; n?: number; seed?: number; col?: string; a?: number; shift?: { x: number; y: number } }> = ({ t, n = 60, seed = 3, col = 'violet', a = 0.4, shift = { x: 0, y: 0 } }) => (
  <AbsoluteFill style={{ pointerEvents: 'none' }}>
    {Array.from({ length: n }, (_, i) => {
      const d = 0.3 + 0.7 * hash(i, seed, 1);
      const sp = 8 + 22 * hash(i, seed, 2);
      const x = (((W * hash(i, seed, 3) + 40 * Math.sin(t * 0.4 + i) + shift.x * d) % W) + W) % W;
      const y = (((H * hash(i, seed, 4) - t * sp * d + shift.y * d) % H) + H) % H;
      const s = 1 + 2.6 * d * hash(i, seed, 5);
      const tw = 0.55 + 0.45 * Math.sin(t * (1 + hash(i, seed, 6) * 2) + i * TAU * hash(i, seed, 7));
      return <div key={i} style={{ position: 'absolute', left: x, top: y, width: s, height: s, borderRadius: '50%', background: rgba(col, a * tw * d), boxShadow: d > 0.8 ? `0 0 ${4 * s}px ${rgba(col, 0.35 * a)}` : undefined }} />;
    })}
  </AbsoluteFill>
);
