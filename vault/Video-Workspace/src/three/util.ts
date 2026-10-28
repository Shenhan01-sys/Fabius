// Pure helpers for the 3D scenes. Everything here is a function of its arguments: no clock, no unseeded randomness.

export type Vec3 = [number, number, number];
export type Lean = { x: number; y: number };

export const TAU = Math.PI * 2;
export const DEG = Math.PI / 180;

export const clamp = (x: number, lo = 0, hi = 1) => Math.max(lo, Math.min(hi, x));
export const clamp01 = (x: number) => Math.max(0, Math.min(1, x));
export const lerp = (a: number, b: number, k: number) => a + (b - a) * k;
export const lerp3 = (a: Vec3, b: Vec3, k: number): Vec3 => [lerp(a[0], b[0], k), lerp(a[1], b[1], k), lerp(a[2], b[2], k)];
export const add3 = (a: Vec3, b: Vec3): Vec3 => [a[0] + b[0], a[1] + b[1], a[2] + b[2]];
export const scale3 = (a: Vec3, k: number): Vec3 => [a[0] * k, a[1] * k, a[2] * k];

/** 0 -> 1 between e0 and e1 with zero slope at both ends. */
export const smoothstep = (e0: number, e1: number, x: number) => {
  const u = clamp01((x - e0) / (e1 - e0 || 1e-9));
  return u * u * (3 - 2 * u);
};
/** Linear 0 -> 1 between e0 and e1. */
export const ramp = (e0: number, e1: number, x: number) => clamp01((x - e0) / (e1 - e0 || 1e-9));
export const easeInOutCubic = (u: number) => (u < 0.5 ? 4 * u * u * u : 1 - Math.pow(-2 * u + 2, 3) / 2);
export const easeOutCubic = (u: number) => 1 - Math.pow(1 - clamp01(u), 3);
/** The website crystal's overshoot ease (c1 = 1.4). */
export const easeOutBack = (u: number, c1 = 1.4) => {
  const c3 = c1 + 1;
  return 1 + c3 * Math.pow(u - 1, 3) + c1 * Math.pow(u - 1, 2);
};
/** 0 -> 1 -> 0 over u in [0, 1] (the website's `bump`). */
export const bump = (u: number) => Math.sin(Math.PI * clamp01(u));

/** mulberry32: the same seeded generator the website crystal uses. */
export function rng(seed: number) {
  let a = seed;
  return () => {
    a = (a + 0x6d2b79f5) | 0;
    let t = Math.imul(a ^ (a >>> 15), 1 | a);
    t = (t + Math.imul(t ^ (t >>> 7), 61 | t)) ^ t;
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
  };
}

/** FNV-1a 32 bit (same as the website's looks.ts). */
export function hash(s: string): number {
  let h = 0x811c9dc5;
  for (let i = 0; i < s.length; i++) {
    h ^= s.charCodeAt(i);
    h = Math.imul(h, 0x01000193) >>> 0;
  }
  return h;
}

/**
 * The website animates many values as `x = lerp(x, target, alpha)` once per display frame (60 Hz). For a sinusoidal target that filter is a
 * first-order low-pass: the visible motion has a smaller amplitude and lags behind. This returns that steady-state gain and phase lag so the
 * deterministic port moves exactly like the site does after its first second, without carrying state between frames.
 */
export function lowpass(omega: number, alpha: number, hz = 60): { gain: number; lag: number } {
  const w = omega / hz;
  const re = 1 - (1 - alpha) * Math.cos(w);
  const im = (1 - alpha) * Math.sin(w);
  return { gain: alpha / Math.hypot(re, im), lag: Math.atan2(im, re) };
}

/** sin(omega t + phase) as seen through the website's per-frame lerp(alpha). */
export function smoothedSin(t: number, omega: number, alpha: number, phase = 0) {
  const { gain, lag } = lowpass(omega, alpha);
  return gain * Math.sin(omega * t + phase - lag);
}
