// Shared building blocks, all pure functions of t (seconds). Ported in spirit from the kit's _vo.ts:
// karaoke words, typed mono notes with a signal caret, the spark pen, graph paper, stamps.
import React from 'react';
import { AbsoluteFill, staticFile } from 'remotion';
import { C, mix, rgba, type Col } from '../lib/palette';
import { F } from '../lib/fonts';
import { Lyrics, type Line, type Word } from '../lib/lyrics';
import { clamp, ease, hash, prog, pulse, TAU } from '../lib/util';
import { pointAt, polyD, strokeText, type P, type StrokeFontName } from '../lib/stroke';

export const W = 1920, H = 1080;

// ------------------------------------------------------------------ text
/** Spaced mono caps label: the plates' UI voice. */
export const Mono: React.FC<{ children: React.ReactNode; size?: number; col?: string; spacing?: number; weight?: number; style?: React.CSSProperties }> = ({ children, size = 14, col = rgba('lav', 0.6), spacing = 3, weight = 500, style }) => (
  <span style={{ ...F.mono(size, weight), letterSpacing: spacing, color: col, textTransform: 'uppercase', whiteSpace: 'pre', ...style }}>{children}</span>
);

/** Mono text typed in from t0 (chars per second `cps`), with the signal caret while typing. */
export const Typer: React.FC<{
  t: number; t0: number; text: string; cps?: number; size?: number; col?: string; weight?: number; caret?: string | false;
  style?: React.CSSProperties; upper?: boolean; spacing?: number; dur?: number;
}> = ({ t, t0, text, cps = 38, size = 18, col = rgba('lav', 0.9), weight = 400, caret = C.violet, style, upper, spacing = 0, dur }) => {
  if (t < t0) return null;
  const d = dur ?? text.length / cps;
  const n = Math.min(text.length, Math.floor(text.length * clamp((t - t0) / Math.max(0.01, d)) + 1e-6));
  const typing = n < text.length;
  return (
    <span style={{ ...F.mono(size, weight), color: col, whiteSpace: 'pre', letterSpacing: spacing, textTransform: upper ? 'uppercase' : undefined, ...style }}>
      {text.slice(0, n)}
      {caret && (typing || Math.floor((t - t0 - d) * 2.2) % 2 === 0) && (t - t0 - d) < 1.2 ? (
        <span style={{ display: 'inline-block', width: size * 0.62, height: size * 1.05, background: caret, verticalAlign: -size * 0.18, marginLeft: 2 }} />
      ) : null}
    </span>
  );
};

export interface KaraokeStyle {
  font: React.CSSProperties;
  hot?: Col | string; // colour while being said
  done?: Col | string; // colour once said
  outline?: string | false; // unsaid glyph outline colour
  ant?: number; // seconds a word appears (as outline) before it is said
  pop?: number; // scale pop at each onset
  gap?: number; // em gap between words
  upper?: boolean;
  /** light surface: hot = violet, done = ink, outline = ink hairline */
  light?: boolean;
}
/**
 * Karaoke: unsaid words are hairline outlines, the word being said wipes in `hot`, said words cool to `done`.
 * `words` default = the whole line; pass a slice to set a phrase. Layout is a flex row (wraps if `wrap`).
 */
export const Karaoke: React.FC<{ t: number; words: Word[]; st: KaraokeStyle; texts?: string[]; style?: React.CSSProperties; wrap?: boolean; align?: 'left' | 'center' | 'right'; lineHeight?: number }> = ({ t, words, st, texts, style, wrap, align = 'left', lineHeight = 1 }) => {
  const hot = st.hot ?? (st.light ? 'violet' : 'violet2'), done = st.done ?? (st.light ? 'ink' : 'lav');
  const fs = (st.font.fontSize as number) ?? 100;
  return (
    <div style={{ display: 'flex', flexWrap: wrap ? 'wrap' : 'nowrap', justifyContent: align === 'center' ? 'center' : align === 'right' ? 'flex-end' : 'flex-start', columnGap: (st.gap ?? 0.26) * fs, lineHeight, ...style }}>
      {words.map((w, i) => {
        const txt = texts?.[i] ?? w.w;
        const tAnt = w.start - (st.ant ?? 0.35);
        const a = prog(t, tAnt, tAnt + 0.3, ease.outCubic);
        const p = Lyrics.wordProgress(w, t);
        const d = prog(t, w.end, w.end + 0.35);
        const pop = st.pop ? 1 + st.pop * pulse(t, w.start, 0.07) : 1;
        const shown = st.upper ? txt.toUpperCase() : txt;
        return (
          <span key={i} style={{ position: 'relative', display: 'inline-block', whiteSpace: 'pre', opacity: a, transform: `translateY(${((1 - a) * 0.3 * fs).toFixed(1)}px) scale(${pop})`, filter: a < 1 && a > 0 ? `blur(${((1 - a) * 9).toFixed(1)}px)` : undefined, transformOrigin: '50% 70%', ...st.font }}>
            <span style={{ color: 'transparent', WebkitTextStroke: st.outline === false ? undefined : `1.4px ${st.outline ?? (st.light ? rgba('ink', 0.22) : rgba('mist', 0.5))}` }}>{shown}</span>
            <span style={{ position: 'absolute', left: 0, top: 0, color: d < 1 ? mix(hot, done, d) : rgba(done), clipPath: `inset(-20% ${(1 - p) * 100}% -20% -2%)` }}>{shown}</span>
          </span>
        );
      })}
    </div>
  );
};

/** Words of a line from index a to b (inclusive). */
export const span = (l: Line, a: number, b = l.words.length - 1) => l.words.slice(a, b + 1);

// ------------------------------------------------------------------ the spark
/** The spark: white-hot core, orange halo, four flickering rays. Screen-blended. */
export const Spark: React.FC<{ x: number; y: number; t: number; scale?: number; intensity?: number }> = ({ x, y, t, scale = 1, intensity = 1 }) => {
  const fl = 0.85 + 0.15 * Math.sin(t * 91.7) * Math.sin(t * 57.3);
  const I = clamp(intensity * fl, 0, 2);
  const R = 46 * scale;
  return (
    <div style={{ position: 'absolute', left: x - R, top: y - R, width: 2 * R, height: 2 * R, pointerEvents: 'none', mixBlendMode: 'screen' }}>
      <div style={{ position: 'absolute', inset: 0, borderRadius: '50%', background: `radial-gradient(circle, ${rgba('violet', 0.55 * I)} 0%, ${rgba('violet', 0.18 * I)} 35%, ${rgba('violet', 0)} 70%)` }} />
      <div style={{ position: 'absolute', inset: R * 0.62, borderRadius: '50%', background: `radial-gradient(circle, rgba(250,248,255,${I}) 0%, rgba(196,180,255,${0.95 * I}) 40%, ${rgba('violet', 0)} 100%)` }} />
      <svg width={2 * R} height={2 * R} style={{ position: 'absolute', inset: 0 }}>
        {[0, 1, 2, 3].map((i) => {
          const a = i * (TAU / 4) + t * 3 + 0.4;
          const r = (12 + 7 * hash(Math.floor(t * 30), i)) * scale;
          return <line key={i} x1={R} y1={R} x2={R + Math.cos(a) * r} y2={R + Math.sin(a) * r} stroke={`rgba(222,214,255,${0.8 * I})`} strokeWidth={1.4 * scale} strokeLinecap="round" />;
        })}
      </svg>
    </div>
  );
};

/** Sputtering particles off a moving head `headAt(tb)` (deterministic births, ballistic streaks). SVG lines. */
export const Sputter: React.FC<{ t: number; headAt: (tb: number) => P | null; rate?: number; life?: number; speed?: number; seed?: number; from?: number; gravity?: number; width?: number }> = ({ t, headAt, rate = 55, life = 0.45, speed = 230, seed = 1, from = -1e9, gravity = 520, width = 1.6 }) => {
  const out: React.ReactNode[] = [];
  const n0 = Math.floor((t - life) * rate), n1 = Math.floor(t * rate);
  for (let n = n0; n <= n1; n++) {
    const tb = n / rate;
    if (tb > t || tb < from) continue;
    const h = headAt(tb);
    if (!h) continue;
    const age = t - tb, lf = life * (0.35 + 0.65 * hash(n, seed + 2));
    if (age > lf) continue;
    const a = hash(n, seed) * TAU, sp = speed * (0.25 + hash(n, seed + 1) ** 2 * 1.2);
    const vx = Math.cos(a) * sp, vy = Math.sin(a) * sp - speed * 0.3;
    const pos = (s: number) => ({ x: h.x + vx * s, y: h.y + vy * s + 0.5 * gravity * s * s });
    const p0 = pos(Math.max(0, age - 0.018)), p1 = pos(age);
    const k = 1 - age / lf, heat = k * k;
    out.push(<line key={n} x1={p0.x} y1={p0.y} x2={p1.x} y2={p1.y} stroke={mix('violet2', '#ffffff', heat * 0.8, Math.min(1, k * 1.4))} strokeWidth={width * (0.5 + k * 0.7)} strokeLinecap="round" />);
  }
  return <svg width={W} height={H} style={{ position: 'absolute', inset: 0, overflow: 'visible', mixBlendMode: 'screen' }}>{out}</svg>;
};

// ------------------------------------------------------------------ plotted lines
export type Poly = P[];
export const polyLen = (ps: Poly) => {
  let l = 0;
  for (let i = 1; i < ps.length; i++) l += Math.hypot(ps[i]!.x - ps[i - 1]!.x, ps[i]!.y - ps[i - 1]!.y);
  return l;
};
/**
 * A polyline laid down from t0 to t1: the fresh end glows ember and cools to `col`.
 * Returns nothing before t0. Use inside an <svg>.
 */
export const Ink: React.FC<{ t: number; t0: number; t1: number; pts: Poly; col?: string; w?: number; ez?: (x: number) => number; dash?: string; hot?: boolean; opacity?: number; e0?: number; e1?: number }> = ({ t, t0, t1, pts, col = rgba('lav', 0.85), w = 1.6, ez = ease.inOutCubic, dash, hot = true, opacity = 1, e0, e1 }) => {
  if (t < t0 || pts.length < 2) return null;
  const L = polyLen(pts);
  const k = ez(clamp((t - t0) / Math.max(1e-4, t1 - t0)));
  const head = k * L;
  const tail = e0 !== undefined && e1 !== undefined ? ease.inOutCubic(clamp((t - e0) / Math.max(1e-4, e1 - e0))) * L : 0;
  if (tail >= head && tail > 0) return null;
  const d = 'M' + pts.map((p) => `${p.x.toFixed(1)} ${p.y.toFixed(1)}`).join('L');
  const age = t - t1;
  const cool = hot ? clamp(age / 0.35) : 1;
  const base = (
    <path d={d} fill="none" stroke={cool < 1 ? mix('violet2', col.startsWith('#') ? col : 'lav', cool, 1) : col} strokeWidth={w} strokeLinecap="round" strokeLinejoin="round"
      strokeDasharray={dash ?? `${Math.max(0, head - tail)} ${L + 10}`} strokeDashoffset={dash ? undefined : -tail} opacity={opacity} />
  );
  if (dash) {
    // dashed strokes reveal with a mask path instead
    const id = `m${Math.round(t0 * 1000)}_${pts.length}_${Math.round(pts[0]!.x)}_${Math.round(pts[0]!.y)}`;
    return (
      <g opacity={opacity}>
        <defs>
          <mask id={id}><path d={d} fill="none" stroke="#fff" strokeWidth={w + 6} strokeDasharray={`${head} ${L + 10}`} /></mask>
        </defs>
        <path d={d} fill="none" stroke={col} strokeWidth={w} strokeDasharray={dash} mask={`url(#${id})`} />
      </g>
    );
  }
  const fresh = hot && k < 1 ? (
    <path d={d} fill="none" stroke={C.violet2} strokeWidth={w * 1.6} strokeLinecap="round" strokeDasharray={`${Math.min(head, 46)} ${L + 10}`} strokeDashoffset={-(head - Math.min(head, 46))} style={{ filter: `drop-shadow(0 0 6px ${rgba('violet', 0.9)})` }} />
  ) : null;
  return <>{base}{fresh}</>;
};
/** Where the pen is on a polyline drawn over [t0, t1]. */
export function headOn(pts: Poly, t: number, t0: number, t1: number, ez = ease.inOutCubic): P | null {
  if (t < t0 || t > t1) return null;
  const k = ez(clamp((t - t0) / Math.max(1e-4, t1 - t0)));
  return pointAt([pts], k * polyLen(pts));
}

/**
 * The plotter's pen over a list of timed strokes: on a stroke it rides the stroke's head; between strokes it
 * travels to the next start with a quick ease (rapid plotter moves); before the first and after the last it rests.
 */
export function makePen(strokes: { pts: Poly; t0: number; t1: number; ez?: (x: number) => number }[], rest?: { from?: P; until?: number }) {
  const ss = [...strokes].sort((a, b) => a.t0 - b.t0);
  return (t: number): P | null => {
    if (!ss.length) return null;
    if (rest?.until !== undefined && t > rest.until) return null;
    let prev: (typeof ss)[number] | null = null;
    for (const s of ss) {
      if (t < s.t0) {
        const from = prev ? prev.pts[prev.pts.length - 1]! : rest?.from ?? s.pts[0]!;
        const to = s.pts[0]!;
        const tPrev = prev ? prev.t1 : s.t0 - 0.3;
        const d = Math.hypot(to.x - from.x, to.y - from.y);
        const dur = Math.min(s.t0 - tPrev, clamp(0.1 + d * 0.0004, 0.1, 0.32));
        const k = ease.inOutCubic(clamp((t - (s.t0 - dur)) / Math.max(1e-4, dur)));
        return { x: from.x + (to.x - from.x) * k, y: from.y + (to.y - from.y) * k };
      }
      if (t <= s.t1) return headOn(s.pts, t, s.t0, s.t1, s.ez) ?? s.pts[0]!;
      prev = s;
    }
    return prev ? prev.pts[prev.pts.length - 1]! : null;
  };
}

export const rect = (x: number, y: number, w: number, h: number): Poly => [{ x, y }, { x: x + w, y }, { x: x + w, y: y + h }, { x, y: y + h }, { x, y }];
export const seg = (x0: number, y0: number, x1: number, y1: number): Poly => [{ x: x0, y: y0 }, { x: x1, y: y1 }];
export function arcPts(cx: number, cy: number, r: number, a0: number, a1: number, n = 72): Poly {
  const out: Poly = [];
  for (let i = 0; i <= n; i++) {
    const a = a0 + ((a1 - a0) * i) / n;
    out.push({ x: cx + r * Math.cos(a), y: cy + r * Math.sin(a) });
  }
  return out;
}

// ------------------------------------------------------------------ handwriting (single-stroke fonts)
/**
 * Text written by the pen in a single-stroke font, word k drawn while words[k] is said (or over [t0, t1]
 * when no words are given). (x, y) = left end of the baseline. Returns the svg group; `onHead` is not needed:
 * the head is drawn as a Spark by the caller via `penHead`.
 */
export function handwriting(text: string, font: StrokeFontName, size: number, x0: number, y: number, timing: { words?: Word[]; t0?: number; t1?: number }, align: 'left' | 'center' = 'left') {
  const lay = strokeText(text, font, size);
  const x = align === 'center' ? x0 - lay.width / 2 : x0;
  // per glyph [a, b] time spans, proportional to ink length inside each word
  const spans: [number, number][] = [];
  const byWord = new Map<number, number[]>();
  lay.glyphs.forEach((g, i) => { if (!byWord.has(g.word)) byWord.set(g.word, []); byWord.get(g.word)!.push(i); });
  for (const [wk, ids] of byWord) {
    let a: number, b: number;
    if (timing.words && timing.words.length) {
      const w = timing.words[Math.min(wk, timing.words.length - 1)]!;
      a = w.start; b = Math.max(w.start + 0.15, w.end - 0.03);
    } else {
      const n = lay.words, t0 = timing.t0 ?? 0, t1 = timing.t1 ?? 1;
      a = t0 + ((t1 - t0) * wk) / n; b = t0 + ((t1 - t0) * (wk + 1)) / n;
    }
    const tot = ids.reduce((s, i) => s + lay.glyphs[i]!.len, 0) || 1;
    let acc = 0;
    for (const i of ids) {
      const g = lay.glyphs[i]!;
      spans[i] = [a + ((b - a) * acc) / tot, a + ((b - a) * (acc + g.len)) / tot];
      acc += g.len;
    }
  }
  const draw = (t: number, col: string, w = 2.4) => (
    <g transform={`translate(${x} ${y})`}>
      {lay.glyphs.map((g, i) => {
        const [a, b] = spans[i]!;
        if (t < a) return null;
        const k = clamp((t - a) / Math.max(1e-4, b - a));
        const age = t - b;
        const c = age < 0 ? C.violet2 : mix('violet2', col, clamp(age / 0.4));
        return <path key={i} d={polyD(g.polys)} fill="none" stroke={c} strokeWidth={w} strokeLinecap="round" strokeLinejoin="round" strokeDasharray={`${k * g.len} ${g.len + 10}`} />;
      })}
    </g>
  );
  const head = (t: number): P | null => {
    for (let i = 0; i < lay.glyphs.length; i++) {
      const [a, b] = spans[i]!;
      if (t >= a && t <= b) {
        const g = lay.glyphs[i]!;
        const p = pointAt(g.polys, ((t - a) / Math.max(1e-4, b - a)) * g.len);
        return p ? { x: x + p.x, y: y + p.y } : null;
      }
    }
    return null;
  };
  return { draw, head, width: lay.width, start: spans[0]?.[0] ?? 0, end: spans[spans.length - 1]?.[1] ?? 0 };
}

// ------------------------------------------------------------------ backgrounds and overlays
/** Night indigo with the web's soft violet depth (no hard light). */
export const NightBg: React.FC<{ glow?: number; x?: number; y?: number }> = ({ glow = 1, x = 50, y = 115 }) => (
  <AbsoluteFill style={{ background: `radial-gradient(ellipse 70% 60% at ${x}% ${y}%, ${rgba('violet', 0.2 * glow)} 0%, ${rgba('violet', 0)} 70%), radial-gradient(ellipse 50% 40% at 12% -5%, ${rgba('violet2', 0.08 * glow)} 0%, ${rgba('violet2', 0)} 70%), ${C.night}` }} />
);
/** Pale lavender surface (the web's hero), lit from the top. */
export const LavBg: React.FC<{ glow?: number }> = ({ glow = 1 }) => (
  <AbsoluteFill style={{ background: `radial-gradient(ellipse 80% 60% at 50% -10%, rgba(255,255,255,${0.75 * glow}) 0%, rgba(255,255,255,0) 70%), radial-gradient(ellipse 60% 50% at 100% 110%, ${rgba('lav3', 0.55 * glow)} 0%, ${rgba('lav3', 0)} 70%), ${C.lav}` }} />
);
/** Graph paper (minor/major lines) under a plate; `reveal` grows from a centre in px. */
export const GraphPaper: React.FC<{ paper?: boolean; minor?: number; major?: number; opacity?: number; reveal?: { x: number; y: number; r: number }; ox?: number; oy?: number; scale?: number }> = ({ paper, minor = 24, major = 96, opacity = 1, reveal, ox = 0, oy = 0, scale = 1 }) => {
  const line = paper ? C.ink : C.lav;
  const a1 = paper ? 0.07 : 0.035, a2 = paper ? 0.16 : 0.075;
  const id = `gp${paper ? 1 : 0}${minor}${major}`;
  const m = minor * scale, M = major * scale;
  return (
    <svg width={W} height={H} style={{ position: 'absolute', inset: 0, opacity }}>
      <defs>
        <pattern id={`${id}a`} width={m} height={m} patternUnits="userSpaceOnUse" x={ox} y={oy}>
          <path d={`M ${m} 0 L 0 0 0 ${m}`} fill="none" stroke={rgba(line, a1)} strokeWidth={1} />
        </pattern>
        <pattern id={`${id}b`} width={M} height={M} patternUnits="userSpaceOnUse" x={ox} y={oy}>
          <path d={`M ${M} 0 L 0 0 0 ${M}`} fill="none" stroke={rgba(line, a2)} strokeWidth={1.2} />
        </pattern>
        {reveal && (
          <radialGradient id={`${id}r`} gradientUnits="userSpaceOnUse" cx={reveal.x} cy={reveal.y} r={Math.max(1, reveal.r)}>
            <stop offset="0.75" stopColor="#fff" stopOpacity={1} />
            <stop offset="1" stopColor="#fff" stopOpacity={0} />
          </radialGradient>
        )}
        {reveal && <mask id={`${id}m`}><rect width={W} height={H} fill={`url(#${id}r)`} /></mask>}
      </defs>
      <g mask={reveal ? `url(#${id}m)` : undefined}>
        <rect width={W} height={H} fill={`url(#${id}a)`} />
        <rect width={W} height={H} fill={`url(#${id}b)`} />
      </g>
    </svg>
  );
};

/** Film grain: one tileable texture, offset per frame (deterministic). */
export const Grain: React.FC<{ frame: number; opacity?: number }> = ({ frame, opacity = 0.075 }) => {
  // the grain moves on every second frame: still alive, and an encoder can keep the bitrate sane
  const g = Math.floor(frame / 2);
  return <AbsoluteFill style={{ backgroundImage: `url(${staticFile('img/grain.png')})`, backgroundSize: '768px 768px', backgroundPosition: `${Math.floor(hash(g, 1) * 768)}px ${Math.floor(hash(g, 2) * 768)}px`, opacity, pointerEvents: 'none' }} />;
};
export const Vignette: React.FC<{ strength?: number }> = ({ strength = 0.42 }) => (
  <AbsoluteFill style={{ background: `radial-gradient(ellipse at 50% 50%, rgba(8,5,26,0) 55%, rgba(8,5,26,${strength}) 100%)`, pointerEvents: 'none' }} />
);

/** A stamp that slams in at `at`: overscale -> 1 with a hard ease, a little rotation. */
export function stampStyle(t: number, at: number, rot = -4, from = 1.9): React.CSSProperties {
  if (t < at) return { opacity: 0 };
  const k = prog(t, at, at + 0.14, ease.outQuart);
  return { opacity: clamp(k * 3), transform: `scale(${from + (1 - from) * k}) rotate(${rot * (1 - 0.5 * k)}deg)` };
}

/** Bordered stamp box (rubber-stamp look). */
export const StampBox: React.FC<{ children: React.ReactNode; col?: string; size?: number; style?: React.CSSProperties }> = ({ children, col = C.violet, size = 34, style }) => (
  <div style={{ display: 'inline-block', border: `${Math.max(2, size * 0.09)}px solid ${col}`, color: col, padding: `${size * 0.12}px ${size * 0.4}px`, ...F.archivo(size, 900, 112), letterSpacing: size * 0.06, textTransform: 'uppercase', lineHeight: 1, ...style }}>{children}</div>
);

/** A thin rule with end ticks (engineering dimension feel). */
export const Rule: React.FC<{ x: number; y: number; w: number; col?: string; k?: number }> = ({ x, y, w, col = rgba('lav', 0.35), k = 1 }) => (
  <div style={{ position: 'absolute', left: x, top: y, width: w * k, height: 1, background: col }} />
);
