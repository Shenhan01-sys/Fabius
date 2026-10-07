// Transitions between plates, centred on the cut: both plates render through the window [cut - d/2, cut + d/2].
//   zoom  — the outgoing plate rushes toward the camera and blurs away; the incoming one settles in from behind
//   whip  — a whip pan with horizontal motion blur
//   iris  — the incoming plate opens as a circle (from a point)
//   push  — the incoming plate pushes the outgoing one up
//   flash — a short lavender flash on a hard cut
import React from 'react';
import { AbsoluteFill } from 'remotion';
import { rgba } from '../lib/palette';
import { clamp, ease } from '../lib/util';

export type TrType = 'zoom' | 'whip' | 'iris' | 'push' | 'flash' | 'cut';
export interface Tr { type: TrType; d: number; x?: number; y?: number }

const W = 1920, H = 1080;

/** Directional (horizontal) blur via an SVG filter with a per-frame id. */
const HBlur: React.FC<{ id: string; sx: number }> = ({ id, sx }) => (
  <svg width={0} height={0} style={{ position: 'absolute' }}>
    <filter id={id} x="-20%" y="-5%" width="140%" height="110%">
      <feGaussianBlur stdDeviation={`${sx.toFixed(1)} 0`} />
    </filter>
  </svg>
);

/** Wrap a plate: `kin` = progress of the transition INTO it (1 = done), `kout` = progress of the one OUT of it (0 = not started). */
export const TrLayer: React.FC<{ id: string; trIn?: Tr; trOut?: Tr; kin: number; kout: number; children: React.ReactNode }> = ({ id, trIn, trOut, kin, kout, children }) => {
  let tf = '', op = 1, filter = '', clip: string | undefined;
  let blurId = '', blurX = 0;
  // the way in
  if (trIn && kin < 1) {
    const k = clamp(kin);
    switch (trIn.type) {
      case 'zoom': {
        const e = ease.outCubic(k);
        tf += ` scale(${0.72 + 0.28 * e})`;
        op *= clamp(k * 1.8);
        filter += ` blur(${(1 - e) * 14}px)`;
        break;
      }
      case 'whip': {
        const e = ease.outQuart(k);
        tf += ` translateX(${(1 - e) * W * 0.55}px)`;
        blurX = Math.max(blurX, (1 - e) * 90);
        op *= clamp(k * 2.5);
        break;
      }
      case 'iris': {
        const e = ease.inOutCubic(k);
        clip = `circle(${(e * 118).toFixed(2)}% at ${trIn.x ?? W / 2}px ${trIn.y ?? H / 2}px)`;
        break;
      }
      case 'push': {
        const e = ease.inOutCubic(k);
        tf += ` translateY(${(1 - e) * H}px)`;
        break;
      }
      case 'flash':
        break;
    }
  }
  // the way out
  if (trOut && kout > 0) {
    const k = clamp(kout);
    switch (trOut.type) {
      case 'zoom': {
        const e = ease.inCubic(k);
        const ox = trOut.x ?? W / 2, oy = trOut.y ?? H / 2;
        tf = `translate(${ox - W / 2}px, ${oy - H / 2}px) scale(${1 + 1.4 * e}) translate(${W / 2 - ox}px, ${H / 2 - oy}px)` + tf;
        op *= 1 - clamp((k - 0.35) / 0.65);
        filter += ` blur(${e * 16}px)`;
        break;
      }
      case 'whip': {
        const e = ease.inQuart(k);
        tf += ` translateX(${-e * W * 0.55}px)`;
        blurX = Math.max(blurX, e * 90);
        op *= 1 - clamp((k - 0.6) / 0.4);
        break;
      }
      case 'iris':
        tf += ` scale(${1 + 0.06 * ease.inOutCubic(k)})`;
        filter += ` brightness(${1 - 0.35 * k})`;
        break;
      case 'push': {
        const e = ease.inOutCubic(k);
        tf += ` translateY(${-e * H * 0.35}px) scale(${1 - 0.08 * e})`;
        filter += ` brightness(${1 - 0.5 * e})`;
        break;
      }
      default:
        break;
    }
  }
  if (blurX > 0.5) {
    blurId = `hb-${id}`;
    filter += ` url(#${blurId})`;
  }
  return (
    <AbsoluteFill style={{ transform: tf || undefined, opacity: op, filter: filter.trim() || undefined, clipPath: clip, transformOrigin: '50% 50%' }}>
      {blurId && <HBlur id={blurId} sx={blurX} />}
      {children}
    </AbsoluteFill>
  );
};

/** A short lavender flash around a cut (for 'flash' transitions and as an accent on others). */
export const Flash: React.FC<{ t: number; at: number; strength?: number }> = ({ t, at, strength = 0.8 }) => {
  const k = t < at ? Math.pow(clamp((t - (at - 0.08)) / 0.08), 2) : Math.pow(0.5, (t - at) / 0.06);
  if (k <= 0.003) return null;
  return <AbsoluteFill style={{ background: rgba('lav', strength * k), pointerEvents: 'none' }} />;
};
