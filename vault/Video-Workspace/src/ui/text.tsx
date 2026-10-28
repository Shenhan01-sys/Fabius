// Kinetic type in the site's two voices, timed to the voiceover's words, and the burned-in captions (the video
// works with the sound off: inclusive by default).
import React from 'react';
import { AbsoluteFill } from 'remotion';
import { accent, calm, heavy, inter, label } from '../lib/fonts';
import { C, rgba } from '../lib/palette';
import { clamp, ease, prog } from '../lib/util';
import { VO, type Word } from '../lib/vo';

export type Voice = 'calm' | 'accent' | 'heavy' | 'label';
export interface Seg { text: string; voice?: Voice; col?: string; at: number; size?: number; br?: boolean }

const font = (v: Voice, size: number): React.CSSProperties =>
  v === 'accent' ? accent(size) : v === 'heavy' ? heavy(size, 92) : v === 'label' ? label(size * 0.22, 600) : calm(size);

/**
 * A headline made of segments; each segment rises out of a mask at its time `at` (word onset), with a short blur.
 * `out` = time the whole headline leaves (rises away). Layout = flex-wrap; `br` forces a line break before a segment.
 */
export const Headline: React.FC<{ t: number; segs: Seg[]; size?: number; out?: number; align?: 'left' | 'center' | 'right'; col?: string; style?: React.CSSProperties; lineGap?: number }> = ({
  t, segs, size = 120, out, align = 'left', col = C.ink, style, lineGap = 0.08,
}) => {
  const o = out !== undefined ? prog(t, out, out + 0.45, ease.inCubic) : 0;
  const rows: Seg[][] = [[]];
  for (const s of segs) {
    if (s.br && rows[rows.length - 1]!.length) rows.push([]);
    rows[rows.length - 1]!.push(s);
  }
  return (
    <div style={{ display: 'flex', flexDirection: 'column', alignItems: align === 'center' ? 'center' : align === 'right' ? 'flex-end' : 'flex-start', gap: size * lineGap, ...style }}>
      {rows.map((row, ri) => (
        <div key={ri} style={{ display: 'flex', alignItems: 'baseline', gap: size * 0.22, flexWrap: 'nowrap' }}>
          {row.map((s, i) => {
            const sz = s.size ?? size;
            const k = prog(t, s.at - 0.08, s.at + 0.42, ease.cine);
            const y = (1 - k) * 0.95 + o * -0.9;
            return (
              <span key={i} style={{ display: 'inline-block', overflow: 'hidden', paddingTop: sz * 0.14, marginTop: -sz * 0.14, paddingBottom: sz * 0.14, marginBottom: -sz * 0.14, paddingRight: s.voice === 'accent' ? sz * 0.1 : 0 }}>
                <span style={{ display: 'inline-block', transform: `translateY(${(y * 100).toFixed(2)}%)`, filter: k < 1 ? `blur(${((1 - k) * 10).toFixed(1)}px)` : o > 0 ? `blur(${(o * 8).toFixed(1)}px)` : undefined, opacity: clamp(k * 1.6) * (1 - o), whiteSpace: 'pre', color: s.col ?? (s.voice === 'accent' ? C.violet : col), ...font(s.voice ?? 'calm', sz) }}>
                  {s.text}
                </span>
              </span>
            );
          })}
        </div>
      ))}
    </div>
  );
};

/** Words of a voiceover line as Headline segments (voices per word index; default calm). */
export function segsOf(words: Word[], voices: Record<number, Voice> = {}, cols: Record<number, string> = {}): Seg[] {
  return words.map((w, i) => ({ text: w.w, voice: voices[i] ?? 'calm', col: cols[i], at: w.start }));
}

/** A tiny mono label that types in (site's micro-label voice). */
export const Label: React.FC<{ t: number; at: number; text: string; size?: number; col?: string; cps?: number; style?: React.CSSProperties; caret?: boolean }> = ({ t, at, text, size = 16, col = C.violet, cps = 40, style, caret = true }) => {
  if (t < at) return null;
  const n = Math.min(text.length, Math.floor((t - at) * cps));
  const typing = n < text.length;
  return (
    <span style={{ ...label(size, 600), color: col, whiteSpace: 'pre', ...style }}>
      {text.slice(0, n)}
      {caret && (typing || Math.floor((t - at) * 2.4) % 2 === 0) && t - at < text.length / cps + 1.2 ? <span style={{ display: 'inline-block', width: size * 0.55, height: size * 1.05, background: col, verticalAlign: -size * 0.15, marginLeft: 3 }} /> : null}
    </span>
  );
};

// ------------------------------------------------------------------ captions
interface Page { words: (Word & { line: string })[]; start: number; end: number }
function pages(maxWords = 7, maxGap = 0.55): Page[] {
  const out: Page[] = [];
  for (const l of VO.lines) {
    let cur: Page | null = null;
    // TTS word boundaries carry no punctuation; the script's own tokens do (same count = same words)
    const toks = l.text.split(/\s+/);
    const shown = toks.length === l.words.length ? toks : l.words.map((w) => w.w);
    for (const [i, w] of l.words.entries()) {
      const ww = { ...w, w: shown[i]!, line: l.id };
      const brk = !cur || cur.words.length >= maxWords || w.start - cur.end > maxGap || /[.?!]$/.test(cur.words[cur.words.length - 1]!.w);
      if (brk) {
        cur = { words: [ww], start: w.start, end: w.end };
        out.push(cur);
      } else {
        cur!.words.push(ww);
        cur!.end = w.end;
      }
    }
  }
  return out;
}
const PAGES = pages();

/**
 * Burned-in captions: one short page at a time, bottom centre, the word being said in violet. `hide` = time ranges
 * where a big headline already shows the same words (no double text). `dark` = light text on a dark pill.
 */
export const Captions: React.FC<{ t: number; hide?: [number, number][]; dark?: (t: number) => boolean; bottom?: number }> = ({ t, hide = [], dark, bottom = 64 }) => {
  const p = PAGES.find((pg) => t >= pg.start - 0.12 && t < pg.end + 0.35);
  if (!p) return null;
  if (hide.some(([a, b]) => p.start >= a - 0.05 && p.start < b)) return null;
  const a = Math.min(prog(t, p.start - 0.12, p.start + 0.08), 1 - prog(t, p.end + 0.2, p.end + 0.35));
  const dk = dark?.(t) ?? false;
  return (
    <AbsoluteFill style={{ justifyContent: 'flex-end', alignItems: 'center', paddingBottom: bottom, pointerEvents: 'none' }}>
      <div style={{ opacity: a, transform: `translateY(${(1 - a) * 8}px)`, padding: '12px 26px 14px', borderRadius: 999, background: dk ? 'rgba(15,11,38,0.62)' : 'rgba(255,255,255,0.72)', border: `1px solid ${dk ? 'rgba(157,134,255,0.28)' : 'rgba(110,75,255,0.16)'}`, boxShadow: dk ? '0 10px 40px rgba(0,0,0,0.35)' : '0 10px 40px rgba(110,75,255,0.14)', backdropFilter: 'blur(14px)', display: 'flex', gap: 10, maxWidth: 1500 }}>
        {p.words.map((w, i) => {
          const on = t >= w.start - 0.02;
          const now = t >= w.start - 0.02 && t < w.end + 0.05;
          return <span key={i} style={{ ...inter(34, now ? 600 : 500), color: now ? C.violet : on ? (dk ? '#f2efff' : C.ink) : dk ? 'rgba(242,239,255,0.45)' : rgba('ink', 0.4), letterSpacing: -0.2 }}>{w.w}</span>;
        })}
      </div>
    </AbsoluteFill>
  );
};
