// The overlay the kit's HUD and the reference reel share: crop marks, the slate label top-left, the plate
// number top-right, timecode bottom-left, and (this video's addition) the SOURCE of the claim on screen,
// bottom-right: every number shown has a file or a command in the repo that prints it.
import React from 'react';
import { AbsoluteFill } from 'remotion';
import { rgba } from '../lib/palette';
import { F } from '../lib/fonts';
import { clamp, ease, lerp, prog, timecode } from '../lib/util';
import { W, H } from './kit';

export const Hud: React.FC<{ t: number; fps: number; duration: number; ink: boolean; plateNo: number; title: string; src?: string; srcSince?: number; frame?: number; opacity?: number }> = ({ t, fps, duration, ink, plateNo, title, src, srcSince = 0, frame = 1, opacity = 1 }) => {
  const col = ink ? rgba('ink', 0.62) : rgba('lav', 0.55);
  const dim = ink ? rgba('ink', 0.4) : rgba('lav', 0.32);
  const mark = ink ? rgba('ink', 0.5) : rgba('lav', 0.38);
  const e = ease.inOutCubic(clamp(frame));
  const m = lerp(-40, 34, e), l = 22;
  const lab = (s: React.ReactNode, style: React.CSSProperties) => (
    <div style={{ position: 'absolute', ...F.mono(12.5, 500), letterSpacing: 2.6, color: col, textTransform: 'uppercase', whiteSpace: 'pre', ...style }}>{s}</div>
  );
  const srcA = src ? prog(t, srcSince, srcSince + 0.4) : 0;
  return (
    <AbsoluteFill style={{ opacity, pointerEvents: 'none' }}>
      <svg width={W} height={H} style={{ position: 'absolute', inset: 0 }}>
        {([[m, m, 1, 1], [W - m, m, -1, 1], [m, H - m, 1, -1], [W - m, H - m, -1, -1]] as const).map(([x, y, sx, sy], i) => (
          <path key={i} d={`M ${x + sx * l} ${y} L ${x} ${y} L ${x} ${y + sy * l}`} fill="none" stroke={mark} strokeWidth={1.3} />
        ))}
      </svg>
      {lab(<>FABIUS <span style={{ color: dim }}>—</span> PITCH <span style={{ color: dim }}>·</span> 2026</>, { left: 66, top: 52 })}
      {lab(<>{String(plateNo).padStart(2, '0')} <span style={{ color: dim }}>·</span> {title}</>, { right: 66, top: 52 })}
      {lab(<>{timecode(t, fps)} <span style={{ color: dim }}>·</span> {fps} FPS</>, { left: 66, bottom: 50 })}
      {src ? lab(<><span style={{ color: dim }}>SRC</span> {src}</>, { right: 66, bottom: 50, opacity: srcA, textTransform: 'none', letterSpacing: 1.2 }) : null}
      <div style={{ position: 'absolute', left: 66, right: 66, bottom: 40, height: 1, background: dim, opacity: 0.35 }} />
      <div style={{ position: 'absolute', left: 66, bottom: 40, height: 1, width: (W - 132) * clamp(t / duration), background: rgba('violet', 0.9) }} />
    </AbsoluteFill>
  );
};
