// Solid objects in real 3D (CSS preserve-3d): a stage with its own perspective camera, boxes with six lit
// faces, thick glass slabs that carry UI on their front face, the web's glass blocks as true cubes, padlocks.
// Used where a plate should show the thing itself rather than a diagram of it. Pure functions of t.
//
// Chrome flattens a 3D context under opacity < 1, filter or overflow: hidden, so inside a Stage those go on
// the faces (or on the Stage itself), never on an <At> or <Box> wrapper.
import React from 'react';
import { C, rgba } from '../lib/palette';
import { F } from '../lib/fonts';
import { clamp, ease, lerp, noise1, type Ease } from '../lib/util';

export interface StageCam { rx?: number; ry?: number; rz?: number; x?: number; y?: number; z?: number; s?: number }
export interface StageKey extends StageCam { t: number; ez?: Ease }

/** Stage camera at t: keys hold their values; each move eases into the key that ends it (scale in log space). */
export function stageAt(keys: StageKey[], t: number): Required<StageCam> {
  const ks = [...keys].sort((a, b) => a.t - b.t);
  const base = { rx: 0, ry: 0, rz: 0, x: 0, y: 0, z: 0, s: 1 };
  const full = (k: StageKey, p: Required<StageCam>): Required<StageCam> => ({ rx: k.rx ?? p.rx, ry: k.ry ?? p.ry, rz: k.rz ?? p.rz, x: k.x ?? p.x, y: k.y ?? p.y, z: k.z ?? p.z, s: k.s ?? p.s });
  if (!ks.length) return base;
  let prev = full(ks[0]!, base);
  if (t <= ks[0]!.t) return prev;
  for (let i = 1; i < ks.length; i++) {
    const b = full(ks[i]!, prev);
    if (t <= ks[i]!.t) {
      const k = (ks[i]!.ez ?? ease.inOutCubic)(clamp((t - ks[i - 1]!.t) / Math.max(1e-4, ks[i]!.t - ks[i - 1]!.t)));
      return { rx: lerp(prev.rx, b.rx, k), ry: lerp(prev.ry, b.ry, k), rz: lerp(prev.rz, b.rz, k), x: lerp(prev.x, b.x, k), y: lerp(prev.y, b.y, k), z: lerp(prev.z, b.z, k), s: Math.exp(lerp(Math.log(prev.s), Math.log(b.s), k)) };
    }
    prev = b;
  }
  return prev;
}

/**
 * A 3D stage: world origin at screen (cx, cy), +y down, +z towards the viewer. The camera orbits the origin:
 * rx > 0 looks down from above (top faces show), ry > 0 swings to the right (right faces show); it looks at
 * (x, y) and dollies by z (positive = closer). `drift` adds a slow handheld wobble.
 */
export const Stage: React.FC<{ cam: StageCam; t?: number; drift?: number; perspective?: number; cx?: number; cy?: number; opacity?: number; style?: React.CSSProperties; children: React.ReactNode }> = ({ cam, t = 0, drift = 0, perspective = 1700, cx = 960, cy = 540, opacity = 1, style, children }) => {
  const d = drift;
  const rx = (cam.rx ?? 0) + 0.8 * d * noise1(t * 0.27, 31), ry = (cam.ry ?? 0) + 1.1 * d * noise1(t * 0.23, 32);
  const rz = (cam.rz ?? 0) + 0.25 * d * noise1(t * 0.2, 33);
  const x = (cam.x ?? 0) + 8 * d * noise1(t * 0.35, 34), y = (cam.y ?? 0) + 6 * d * noise1(t * 0.31, 35);
  return (
    <div style={{ position: 'absolute', inset: 0, perspective, perspectiveOrigin: `${cx}px ${cy}px`, opacity, pointerEvents: 'none', ...style }}>
      <div style={{ position: 'absolute', left: cx, top: cy, width: 0, height: 0, transformStyle: 'preserve-3d', transform: `translateZ(${cam.z ?? 0}px) rotateX(${-rx}deg) rotateY(${-ry}deg) rotateZ(${rz}deg) scale(${cam.s ?? 1}) translate3d(${-x}px, ${-y}px, 0)` }}>
        {children}
      </div>
    </div>
  );
};

/** Place children at (x, y, z) in the stage (their own origin at that point), rotated and scaled. */
export const At: React.FC<{ x?: number; y?: number; z?: number; rx?: number; ry?: number; rz?: number; s?: number; children: React.ReactNode }> = ({ x = 0, y = 0, z = 0, rx = 0, ry = 0, rz = 0, s = 1, children }) => (
  <div style={{ position: 'absolute', left: 0, top: 0, width: 0, height: 0, transformStyle: 'preserve-3d', transform: `translate3d(${x}px, ${y}px, ${z}px) rotateX(${rx}deg) rotateY(${ry}deg) rotateZ(${rz}deg) scale(${s})` }}>
    {children}
  </div>
);

/** A flat plane w × h centred on the origin, facing the viewer (for labels, rays, shadows inside a stage). */
export const Plane: React.FC<{ w: number; h: number; style?: React.CSSProperties; children?: React.ReactNode }> = ({ w, h, style, children }) => (
  <div style={{ position: 'absolute', left: -w / 2, top: -h / 2, width: w, height: h, ...style }}>{children}</div>
);

export interface Faces { front: string; back?: string; left?: string; right?: string; top?: string; bottom?: string }

/**
 * A box w × h × d centred on the origin. `faces` are CSS backgrounds; `edge` draws the glass edges; the front
 * face carries `children` (laid out in a w × h div). `alpha` fades every face (the box stays 3D).
 */
export const Box: React.FC<{ w: number; h: number; d: number; faces: Faces; edge?: string; edgeW?: number; radius?: number; alpha?: number; glow?: string; frontStyle?: React.CSSProperties; children?: React.ReactNode }> = ({ w, h, d, faces, edge, edgeW = 1.5, radius = 0, alpha = 1, glow, frontStyle, children }) => {
  const side = faces.left ?? faces.right ?? faces.front;
  const f = (key: string, W: number, Hh: number, tf: string, bg: string, extra?: React.CSSProperties, kids?: React.ReactNode) => (
    <div key={key} style={{ position: 'absolute', left: -W / 2, top: -Hh / 2, width: W, height: Hh, transform: tf, background: bg, border: edge ? `${edgeW}px solid ${edge}` : undefined, boxSizing: 'border-box', borderRadius: radius, opacity: alpha, backfaceVisibility: 'hidden', ...extra }}>{kids}</div>
  );
  return (
    <div style={{ position: 'absolute', left: 0, top: 0, width: 0, height: 0, transformStyle: 'preserve-3d' }}>
      {f('bk', w, h, `rotateY(180deg) translateZ(${d / 2}px)`, faces.back ?? faces.front)}
      {f('l', d, h, `rotateY(-90deg) translateZ(${w / 2}px)`, faces.left ?? side, { borderRadius: Math.min(radius, d / 2) })}
      {f('r', d, h, `rotateY(90deg) translateZ(${w / 2}px)`, faces.right ?? side, { borderRadius: Math.min(radius, d / 2) })}
      {f('t', w, d, `rotateX(90deg) translateZ(${h / 2}px)`, faces.top ?? side, { borderRadius: Math.min(radius, d / 2) })}
      {f('b', w, d, `rotateX(-90deg) translateZ(${h / 2}px)`, faces.bottom ?? side, { borderRadius: Math.min(radius, d / 2) })}
      {f('fr', w, h, `translateZ(${d / 2}px)`, faces.front, { boxShadow: glow, ...frontStyle }, children)}
    </div>
  );
};

export type BlockState = 'empty' | 'sealed' | 'open';

/** The web's glass block as a true cube (edge s): empty fogged glass, sealed indigo, or open (lit white-violet). */
export const Block: React.FC<{ s: number; state: BlockState; alpha?: number; light?: boolean; label?: string }> = ({ s, state, alpha = 1, light = false, label }) => {
  let faces: Faces, edge: string, glow: string | undefined;
  if (state === 'empty') {
    faces = light
      ? { front: 'linear-gradient(135deg, rgba(255,255,255,0.78), rgba(255,255,255,0.4))', left: 'rgba(255,255,255,0.35)', right: 'rgba(236,232,250,0.55)', top: 'rgba(255,255,255,0.9)', bottom: 'rgba(201,189,242,0.4)' }
      : { front: 'linear-gradient(135deg, rgba(255,255,255,0.16), rgba(255,255,255,0.05))', left: 'rgba(255,255,255,0.06)', right: 'rgba(255,255,255,0.09)', top: 'rgba(255,255,255,0.2)', bottom: 'rgba(255,255,255,0.03)' };
    edge = light ? rgba('violet', 0.4) : 'rgba(255,255,255,0.45)';
  } else if (state === 'sealed') {
    faces = { front: `linear-gradient(135deg, ${C.night3}, ${C.indigo})`, left: `linear-gradient(135deg, #1d1650, ${C.indigo})`, right: `linear-gradient(135deg, #2a2168, #161038)`, top: `linear-gradient(135deg, #3a2f86, ${C.night3})`, bottom: C.indigo };
    edge = rgba('violet2', 0.95);
    glow = `inset 0 0 ${s * 0.3}px ${rgba('violet', 0.55)}`;
  } else {
    faces = { front: 'linear-gradient(135deg, #ffffff, #e4dcff)', left: 'linear-gradient(135deg, #d9cffd, #b7a6f7)', right: 'linear-gradient(135deg, #e9e3ff, #c5b8fa)', top: '#ffffff', bottom: C.violet2 };
    edge = 'rgba(255,255,255,0.95)';
    glow = `0 0 ${s * 0.6}px ${rgba('violet2', 0.9)}, inset 0 0 ${s * 0.25}px ${rgba('violet2', 0.7)}`;
  }
  return (
    <Box w={s} h={s} d={s} faces={faces} edge={edge} edgeW={Math.max(1.2, s * 0.025)} alpha={alpha} glow={glow}>
      {label ? <div style={{ position: 'absolute', inset: 0, display: 'flex', alignItems: 'center', justifyContent: 'center', ...F.mono(s * 0.125, 600), whiteSpace: 'nowrap', color: state === 'open' ? C.violet : rgba('lav', 0.85), letterSpacing: 0.5 }}>{label}</div> : null}
    </Box>
  );
};

/** A solid padlock (body box + shackle). `shut` 0 = shackle up and open, 1 = closed. Origin = body centre. */
export const Padlock3D: React.FC<{ s?: number; shut?: number; col?: string; alpha?: number }> = ({ s = 1, shut = 1, col = C.violet, alpha = 1 }) => {
  const w = 46 * s, h = 38 * s, d = 18 * s;
  const lift = (1 - shut) * 16 * s;
  const sh = (z: number) => (
    <div style={{ position: 'absolute', left: -17 * s, top: -h / 2 - 30 * s - lift, width: 34 * s, height: 40 * s, transform: `translateZ(${z}px)`, opacity: alpha }}>
      <svg width={34 * s} height={40 * s} viewBox="0 0 34 40" style={{ overflow: 'visible' }}>
        <path d="M 5 40 L 5 17 A 12 12 0 0 1 29 17 L 29 40" fill="none" stroke={z > 0 ? '#d6ccff' : '#8f7cf0'} strokeWidth={6.5} strokeLinecap="round" />
      </svg>
    </div>
  );
  return (
    <div style={{ position: 'absolute', left: 0, top: 0, width: 0, height: 0, transformStyle: 'preserve-3d' }}>
      {sh(-d * 0.18)}
      {sh(d * 0.18)}
      <Box w={w} h={h} d={d} radius={6 * s} alpha={alpha} faces={{ front: `linear-gradient(160deg, #9b84ff 0%, ${col} 55%, #4b2fd0 100%)`, left: '#4b2fd0', right: '#5a3ce6', top: '#b9a9ff', bottom: '#3a22b0' }} edge="rgba(255,255,255,0.35)" edgeW={1}>
        <div style={{ position: 'absolute', left: '50%', top: '42%', width: 9 * s, height: 9 * s, marginLeft: -4.5 * s, borderRadius: '50%', background: C.indigo }} />
        <div style={{ position: 'absolute', left: '50%', top: '42%', width: 3.5 * s, height: 13 * s, marginLeft: -1.75 * s, marginTop: 5 * s, borderRadius: 2 * s, background: C.indigo }} />
      </Box>
    </div>
  );
};

/** A soft floor shadow under an object (a flat ellipse lying on the plane y = 0 of its <At>). */
export const FloorShadow: React.FC<{ w: number; d?: number; a?: number; col?: string }> = ({ w, d, a = 0.35, col = '10,6,40' }) => (
  <div style={{ position: 'absolute', left: -w / 2, top: -(d ?? w * 0.5) / 2, width: w, height: d ?? w * 0.5, transform: 'rotateX(90deg)', borderRadius: '50%', background: `radial-gradient(ellipse at 50% 50%, rgba(${col},${a}) 0%, rgba(${col},0) 70%)` }} />
);
