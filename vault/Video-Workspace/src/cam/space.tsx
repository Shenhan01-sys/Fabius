// A real 3D stage in CSS (preserve-3d) with an orbit camera, so every shot can move: the camera looks at a target
// point, orbits it (rx = elevation, ry = azimuth, rz = roll) and dollies (z > 0 = closer). Objects are placed with <At>.
// Chrome flattens a 3D context under opacity < 1, filter or overflow: hidden, so those go on leaf elements only.
import React from 'react';
import { clamp, ease, lerp, noise1, type Ease } from '../lib/util';

export interface Cam { x: number; y: number; z: number; tz: number; rx: number; ry: number; rz: number; s: number }
export interface CamKey extends Partial<Cam> { t: number; ez?: Ease }
export const CAM0: Cam = { x: 0, y: 0, z: 0, tz: 0, rx: 0, ry: 0, rz: 0, s: 1 };

/** Camera at t: keys hold their values; each move eases into the key that ends it (scale in log space). */
export function camAt(keys: CamKey[], t: number): Cam {
  const ks = [...keys].sort((a, b) => a.t - b.t);
  if (!ks.length) return CAM0;
  const full = (k: CamKey, p: Cam): Cam => ({
    x: k.x ?? p.x, y: k.y ?? p.y, z: k.z ?? p.z, tz: k.tz ?? p.tz, rx: k.rx ?? p.rx, ry: k.ry ?? p.ry, rz: k.rz ?? p.rz, s: k.s ?? p.s,
  });
  let prev = full(ks[0]!, CAM0);
  if (t <= ks[0]!.t) return prev;
  for (let i = 1; i < ks.length; i++) {
    const b = full(ks[i]!, prev);
    if (t <= ks[i]!.t) {
      const k = (ks[i]!.ez ?? ease.inOutCubic)(clamp((t - ks[i - 1]!.t) / Math.max(1e-4, ks[i]!.t - ks[i - 1]!.t)));
      return {
        x: lerp(prev.x, b.x, k), y: lerp(prev.y, b.y, k), z: lerp(prev.z, b.z, k), tz: lerp(prev.tz, b.tz, k),
        rx: lerp(prev.rx, b.rx, k), ry: lerp(prev.ry, b.ry, k), rz: lerp(prev.rz, b.rz, k), s: Math.exp(lerp(Math.log(prev.s), Math.log(b.s), k)),
      };
    }
    prev = b;
  }
  return prev;
}

/** Slow handheld drift added to a camera (never perfectly still). */
export function withDrift(c: Cam, t: number, amp = 1, seed = 0): Cam {
  return {
    ...c,
    x: c.x + 9 * amp * noise1(t * 0.31, seed + 1), y: c.y + 6 * amp * noise1(t * 0.27, seed + 2),
    rx: c.rx + 0.55 * amp * noise1(t * 0.23, seed + 3), ry: c.ry + 0.7 * amp * noise1(t * 0.19, seed + 4), rz: c.rz + 0.2 * amp * noise1(t * 0.17, seed + 5),
  };
}

/**
 * The stage: world origin at screen (cx, cy), +y down, +z towards the viewer. Children are placed with <At>.
 * `cam` = the orbit camera (see Cam). perspective = focal length in px (smaller = wider lens, stronger depth).
 */
export const Space: React.FC<{ cam: Cam; perspective?: number; cx?: number; cy?: number; style?: React.CSSProperties; children: React.ReactNode }> = ({
  cam, perspective = 1800, cx = 960, cy = 540, style, children,
}) => (
  <div style={{ position: 'absolute', inset: 0, perspective, perspectiveOrigin: `${cx}px ${cy}px`, overflow: 'hidden', ...style }}>
    <div
      style={{
        position: 'absolute', left: cx, top: cy, width: 0, height: 0, transformStyle: 'preserve-3d',
        transform: `translateZ(${cam.z}px) rotateZ(${cam.rz}deg) rotateX(${-cam.rx}deg) rotateY(${-cam.ry}deg) scale(${cam.s}) translate3d(${-cam.x}px, ${-cam.y}px, ${-cam.tz}px)`,
      }}
    >
      {children}
    </div>
  </div>
);

/** Place children at (x, y, z), rotated and scaled; the child's own origin sits at that point. */
export const At: React.FC<{ x?: number; y?: number; z?: number; rx?: number; ry?: number; rz?: number; s?: number; children: React.ReactNode }> = ({
  x = 0, y = 0, z = 0, rx = 0, ry = 0, rz = 0, s = 1, children,
}) => (
  <div style={{ position: 'absolute', left: 0, top: 0, width: 0, height: 0, transformStyle: 'preserve-3d', transform: `translate3d(${x}px, ${y}px, ${z}px) rotateX(${rx}deg) rotateY(${ry}deg) rotateZ(${rz}deg) scale(${s})` }}>
    {children}
  </div>
);

/** A flat plane w x h centred on its origin (a leaf: overflow / opacity / filter are safe here). */
export const Plane: React.FC<{ w: number; h: number; style?: React.CSSProperties; children?: React.ReactNode }> = ({ w, h, style, children }) => (
  <div style={{ position: 'absolute', left: -w / 2, top: -h / 2, width: w, height: h, ...style }}>{children}</div>
);

/** Soft contact shadow lying on the floor under an object (plane y = 0 of its <At>). */
export const FloorShadow: React.FC<{ w: number; d?: number; a?: number; col?: string }> = ({ w, d, a = 0.3, col = '21,18,43' }) => (
  <div style={{ position: 'absolute', left: -w / 2, top: -(d ?? w * 0.4) / 2, width: w, height: d ?? w * 0.4, transform: 'rotateX(90deg)', borderRadius: '50%', background: `radial-gradient(ellipse at 50% 50%, rgba(${col},${a}) 0%, rgba(${col},0) 70%)` }} />
);
