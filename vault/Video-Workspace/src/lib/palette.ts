// The Fabius web palette (web/src/app/globals.css), plus the crystal's deep indigo (web/src/components/hero/Crystal.tsx).
export const C = {
  lav: '#ece8fa',
  lav2: '#ddd5f6',
  lav3: '#c9bdf2',
  ink: '#15122b',
  night: '#0f0b26',
  night2: '#1a1442',
  violet: '#6e4bff',
  violet2: '#9d86ff',
  mist: '#8b86a6',
  gap: '#ff5a6e',
  indigo: '#2a1a94',
  clay: '#fbfaff',
  white: '#ffffff',
} as const;

export type Col = keyof typeof C;

const hex = (c: string): [number, number, number] => {
  const h = c.replace('#', '');
  const f = h.length === 3 ? h.split('').map((x) => x + x).join('') : h;
  return [parseInt(f.slice(0, 2), 16), parseInt(f.slice(2, 4), 16), parseInt(f.slice(4, 6), 16)];
};
const val = (c: Col | string) => (c in C ? C[c as Col] : c);

/** rgba() of a palette colour (or any #hex) with alpha. */
export function rgba(c: Col | string, a = 1): string {
  const [r, g, b] = hex(val(c));
  return `rgba(${r},${g},${b},${+a.toFixed(4)})`;
}

/** Linear mix of two colours, k = 0 -> a, 1 -> b. */
export function mix(a: Col | string, b: Col | string, k: number, alpha = 1): string {
  const x = hex(val(a)), y = hex(val(b));
  const m = (i: number) => Math.round(x[i]! + (y[i]! - x[i]!) * Math.max(0, Math.min(1, k)));
  return `rgba(${m(0)},${m(1)},${m(2)},${+alpha.toFixed(4)})`;
}
