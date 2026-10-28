// Transitions between scenes, centred on the cut: both scenes render inside [cut - d/2, cut + d/2].
//   bloom  - dark to light: the outgoing scene brightens into a soft violet-white bloom, the incoming one resolves out of it
//   zoom   - the outgoing scene rushes past the camera (blur), the incoming one settles from behind
//   whip   - a whip pan with horizontal motion blur
//   portal - the incoming scene opens as a rounded window from a point (diving into a screen)
//   push   - the incoming scene pushes the outgoing one up
//   dip    - a quick dip through night (light to dark)
import React from 'react';
import { AbsoluteFill } from 'remotion';
import { clamp, ease } from '../lib/util';
import { HBlurDef } from './fx';

export type TrType = 'bloom' | 'zoom' | 'whip' | 'portal' | 'push' | 'dip' | 'fade' | 'cut';
export interface Tr { type: TrType; d: number; x?: number; y?: number; dir?: 1 | -1 }

const W = 1920, H = 1080;

export const TrLayer: React.FC<{ id: string; trIn?: Tr; trOut?: Tr; kin: number; kout: number; children: React.ReactNode }> = ({ id, trIn, trOut, kin, kout, children }) => {
  let tf = '', op = 1, filter = '', clip: string | undefined, blurX = 0;
  if (trIn && kin < 1) {
    const k = clamp(kin);
    switch (trIn.type) {
      case 'bloom': { const e = ease.outCubic(k); op *= clamp(k * 1.6); filter += ` brightness(${1 + 0.9 * (1 - e)}) blur(${(1 - e) * 10}px)`; tf += ` scale(${1.06 - 0.06 * e})`; break; }
      case 'zoom': { const e = ease.outCubic(k); tf += ` scale(${0.7 + 0.3 * e})`; op *= clamp(k * 1.8); filter += ` blur(${(1 - e) * 16}px)`; break; }
      case 'whip': { const e = ease.outQuart(k); tf += ` translateX(${(1 - e) * W * 0.6 * (trIn.dir ?? 1)}px)`; blurX = Math.max(blurX, (1 - e) * 110); op *= clamp(k * 2.4); break; }
      case 'portal': { const e = ease.inOutCubic(k); const x = trIn.x ?? W / 2, y = trIn.y ?? H / 2; const r = 12 + 100 * e; clip = `inset(${(y * (1 - e)).toFixed(1)}px ${((W - x) * (1 - e)).toFixed(1)}px ${((H - y) * (1 - e)).toFixed(1)}px ${(x * (1 - e)).toFixed(1)}px round ${r.toFixed(1)}px)`; tf += ` scale(${1.12 - 0.12 * e})`; break; }
      case 'push': { const e = ease.inOutCubic(k); tf += ` translateY(${(1 - e) * H}px)`; break; }
      case 'dip': { op *= clamp((k - 0.35) / 0.65); break; }
      case 'fade': { op *= k; break; }
      default: break;
    }
  }
  if (trOut && kout > 0) {
    const k = clamp(kout);
    switch (trOut.type) {
      case 'bloom': { const e = ease.inCubic(k); filter += ` brightness(${1 + 1.4 * e}) blur(${e * 8}px)`; op *= 1 - clamp((k - 0.55) / 0.45); tf = ` scale(${1 + 0.08 * e})` + tf; break; }
      case 'zoom': { const e = ease.inCubic(k); const ox = trOut.x ?? W / 2, oy = trOut.y ?? H / 2; tf = `translate(${ox - W / 2}px, ${oy - H / 2}px) scale(${1 + 1.6 * e}) translate(${W / 2 - ox}px, ${H / 2 - oy}px)` + tf; op *= 1 - clamp((k - 0.35) / 0.65); filter += ` blur(${e * 18}px)`; break; }
      case 'whip': { const e = ease.inQuart(k); tf += ` translateX(${-e * W * 0.6 * (trOut.dir ?? 1)}px)`; blurX = Math.max(blurX, e * 110); op *= 1 - clamp((k - 0.6) / 0.4); break; }
      case 'portal': { const e = ease.inOutCubic(k); tf += ` scale(${1 + 0.35 * e})`; filter += ` blur(${e * 6}px) brightness(${1 + 0.2 * e})`; break; }
      case 'push': { const e = ease.inOutCubic(k); tf += ` translateY(${-e * H * 0.35}px) scale(${1 - 0.08 * e})`; filter += ` brightness(${1 - 0.4 * e})`; break; }
      case 'dip': { op *= 1 - clamp(k / 0.65); filter += ` brightness(${1 - 0.6 * k})`; break; }
      case 'fade': { op *= 1 - k; break; }
      default: break;
    }
  }
  const bid = `hb-${id}`;
  if (blurX > 0.5) filter += ` url(#${bid})`;
  return (
    <AbsoluteFill style={{ transform: tf.trim() || undefined, opacity: op, filter: filter.trim() || undefined, clipPath: clip, transformOrigin: '50% 50%' }}>
      {blurX > 0.5 && <HBlurDef id={bid} sx={blurX} />}
      {children}
    </AbsoluteFill>
  );
};

/** Light bloom over a bloom cut (soft radial lavender-white light). */
export const BloomLight: React.FC<{ t: number; at: number; d: number }> = ({ t, at, d }) => {
  const k = clamp(1 - Math.abs(t - at) / (d / 2));
  if (k <= 0.01) return null;
  const e = ease.inOutCubic(k);
  return <AbsoluteFill style={{ background: `radial-gradient(ellipse 70% 60% at 50% 50%, rgba(255,255,255,${0.95 * e}) 0%, rgba(236,232,250,${0.85 * e}) 45%, rgba(157,134,255,${0.25 * e}) 100%)`, pointerEvents: 'none' }} />;
};

/** Night dip veil (light to dark cuts). */
export const DipVeil: React.FC<{ t: number; at: number; d: number }> = ({ t, at, d }) => {
  const k = clamp(1 - Math.abs(t - at) / (d / 2));
  if (k <= 0.01) return null;
  return <AbsoluteFill style={{ background: `rgba(15,11,38,${0.85 * ease.inOutCubic(k)})`, pointerEvents: 'none' }} />;
};
