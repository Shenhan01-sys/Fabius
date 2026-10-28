// Pure helpers: every value on screen is a function of time t (seconds), so these never read a clock.
export const TAU = Math.PI * 2;
export const clamp = (x: number, a = 0, b = 1) => Math.max(a, Math.min(b, x));
export const lerp = (a: number, b: number, k: number) => a + (b - a) * k;
export const remap = (x: number, a: number, b: number, c: number, d: number) => c + ((d - c) * (x - a)) / (b - a || 1e-9);

export type Ease = (x: number) => number;
export const ease = {
  linear: (x: number) => x,
  inQuad: (x: number) => x * x,
  outQuad: (x: number) => 1 - (1 - x) * (1 - x),
  inCubic: (x: number) => x * x * x,
  outCubic: (x: number) => 1 - Math.pow(1 - x, 3),
  inOutCubic: (x: number) => (x < 0.5 ? 4 * x * x * x : 1 - Math.pow(-2 * x + 2, 3) / 2),
  inQuart: (x: number) => x * x * x * x,
  outQuart: (x: number) => 1 - Math.pow(1 - x, 4),
  inOutQuart: (x: number) => (x < 0.5 ? 8 * x * x * x * x : 1 - Math.pow(-2 * x + 2, 4) / 2),
  outQuint: (x: number) => 1 - Math.pow(1 - x, 5),
  inOutQuint: (x: number) => (x < 0.5 ? 16 * x ** 5 : 1 - Math.pow(-2 * x + 2, 5) / 2),
  outExpo: (x: number) => (x >= 1 ? 1 : 1 - Math.pow(2, -10 * x)),
  inExpo: (x: number) => (x <= 0 ? 0 : Math.pow(2, 10 * x - 10)),
  inOutExpo: (x: number) => (x <= 0 ? 0 : x >= 1 ? 1 : x < 0.5 ? Math.pow(2, 20 * x - 10) / 2 : (2 - Math.pow(2, -20 * x + 10)) / 2),
  outBack: (x: number) => {
    const c1 = 1.5, c3 = c1 + 1;
    return 1 + c3 * Math.pow(x - 1, 3) + c1 * Math.pow(x - 1, 2);
  },
  /** cinematic: a long soft tail (cubic-bezier .16, 1, .3, 1 shape) */
  cine: (x: number) => 1 - Math.pow(1 - x, 4.2),
  /** critically damped spring step response, settles by x = 1 */
  spring: (x: number) => (x >= 1 ? 1 : 1 - (1 + 7 * x) * Math.exp(-7 * x)),
};

/** progress of t through [a, b], eased, clamped */
export const prog = (t: number, a: number, b: number, ez: Ease = ease.inOutCubic) => ez(clamp((t - a) / (b - a || 1e-9)));
/** 0 -> 1 -> 0 bump of width w around c */
export const bump = (t: number, c: number, w: number) => {
  const k = clamp(1 - Math.abs(t - c) / w);
  return k * k * (3 - 2 * k);
};
/** a short pulse that starts at `at` and decays (for pops on word onsets) */
export const pulse = (t: number, at: number, len = 0.12) => (t < at ? 0 : Math.exp(-(t - at) / len));
/** fade in over [a, a + fin], out over [b - fout, b] */
export const inOut = (t: number, a: number, b: number, fin = 0.3, fout = 0.3, ez: Ease = ease.inOutCubic) =>
  Math.min(prog(t, a, a + fin, ez), 1 - prog(t, b - fout, b, ez));

/** deterministic hash -> [0, 1) */
export function hash(...n: number[]): number {
  let h = 2166136261;
  for (const v of n) {
    h ^= Math.floor(v * 1000003) | 0;
    h = Math.imul(h, 16777619);
    h ^= h >>> 13;
    h = Math.imul(h, 0x5bd1e995);
    h ^= h >>> 15;
  }
  return (h >>> 0) / 4294967296;
}
/** smooth 1D value noise in [-1, 1] */
export function noise1(x: number, seed = 0): number {
  const i = Math.floor(x), f = x - i;
  const a = hash(i, seed) * 2 - 1, b = hash(i + 1, seed) * 2 - 1;
  const u = f * f * (3 - 2 * f);
  return a + (b - a) * u;
}

export const fmtTime = (t: number, fps: number) => {
  const s = Math.floor(t), f = Math.floor((t - s) * fps);
  return `${String(Math.floor(s / 60)).padStart(2, '0')}:${String(s % 60).padStart(2, '0')}:${String(f).padStart(2, '0')}`;
};
