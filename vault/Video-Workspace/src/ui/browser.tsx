// The real website on screen: a browser window whose page is a capture of fabius-one.vercel.app (public/web), either
// a clip (deterministic 60 fps capture, time-remapped here with <Freeze>, so a shot can play, slow down or hold) or a
// still. Crops of the same capture can be lifted out of the page as cards (<PageCrop>) at their real positions.
import React from 'react';
import { Freeze, Img, OffthreadVideo, staticFile } from 'remotion';
import { C, rgba } from '../lib/palette';
import { mono } from '../lib/fonts';
import { Sweep } from '../fx/fx';

/** Capture viewport (CSS px) - desktop captures are 1440 x 900, mobile 390 x 844. */
export const VIEW = { d: { w: 1440, h: 900 }, m: { w: 390, h: 844 } };
export const barH = (w: number) => Math.round(46 * (w / 1440));

/** Geometry of a window w x h centred on its origin: maps capture px (viewport coords) to window-local px. */
export function geom(w: number, h: number, view = VIEW.d) {
  const bar = barH(w);
  const s = w / view.w;
  return {
    bar, s,
    /** centre of a capture-space box, relative to the window centre */
    centre: (b: { x: number; y: number; w: number; h: number }) => ({ x: -w / 2 + (b.x + b.w / 2) * s, y: -h / 2 + bar + (b.y + b.h / 2) * s }),
    point: (x: number, y: number) => ({ x: -w / 2 + x * s, y: -h / 2 + bar + y * s }),
  };
}

export const BrowserWindow: React.FC<{
  w: number; h: number; url: string; dark?: boolean; children?: React.ReactNode; sweep?: number; radius?: number; shadow?: number; dim?: number; style?: React.CSSProperties;
}> = ({ w, h, url, dark = false, children, sweep, radius, shadow = 1, dim = 0, style }) => {
  const bar = barH(w), k = w / 1440, r = radius ?? 20 * k;
  return (
    <div style={{
      position: 'absolute', left: -w / 2, top: -h / 2, width: w, height: h, borderRadius: r, overflow: 'hidden', background: dark ? C.night2 : '#fbfaff',
      border: `${Math.max(1, 1.2 * k)}px solid ${dark ? 'rgba(255,255,255,0.14)' : 'rgba(255,255,255,0.95)'}`,
      boxShadow: shadow ? `0 ${60 * k}px ${140 * k}px -${30 * k}px ${rgba('violet', 0.42 * shadow)}, 0 ${18 * k}px ${40 * k}px -${10 * k}px ${rgba('ink', 0.18 * shadow)}` : undefined,
      ...style,
    }}>
      <div style={{ position: 'absolute', left: 0, right: 0, top: 0, height: bar, display: 'flex', alignItems: 'center', gap: 9 * k, padding: `0 ${18 * k}px`, background: dark ? 'rgba(255,255,255,0.05)' : 'linear-gradient(180deg, #f7f5ff, #eeeafb)', borderBottom: `1px solid ${dark ? 'rgba(255,255,255,0.08)' : 'rgba(21,18,43,0.07)'}` }}>
        {['#ff6058', '#ffbd2e', '#28c941'].map((c) => <div key={c} style={{ width: 12 * k, height: 12 * k, borderRadius: '50%', background: c, opacity: 0.9 }} />)}
        <div style={{ marginLeft: 22 * k, flex: 1, maxWidth: 620 * k, height: 28 * k, borderRadius: 9 * k, background: dark ? 'rgba(255,255,255,0.07)' : '#ffffff', border: `1px solid ${dark ? 'rgba(255,255,255,0.06)' : 'rgba(21,18,43,0.06)'}`, display: 'flex', alignItems: 'center', gap: 8 * k, padding: `0 ${12 * k}px`, ...mono(14 * k, 500), color: dark ? rgba('lav', 0.75) : rgba('ink', 0.62) }}>
          <svg width={11 * k} height={13 * k} viewBox="0 0 11 13"><rect x="1" y="5.5" width="9" height="7" rx="1.6" fill={C.violet} /><path d="M3 5.5 V4 a2.5 2.5 0 0 1 5 0 V5.5" fill="none" stroke={C.violet} strokeWidth="1.5" /></svg>
          <span>{url}</span>
        </div>
      </div>
      <div style={{ position: 'absolute', left: 0, right: 0, top: bar, bottom: 0, overflow: 'hidden' }}>
        {children}
        {dim > 0 ? <div style={{ position: 'absolute', inset: 0, background: rgba('lav', 0.55 * dim), backdropFilter: `blur(${(dim * 4).toFixed(1)}px)` }} /> : null}
      </div>
      {sweep !== undefined ? <Sweep k={sweep} /> : null}
    </div>
  );
};

/** Frame `f` (60 fps) of a capture clip, filling its parent's width (aspect follows the capture). */
export const Clip: React.FC<{ name: string; f: number; style?: React.CSSProperties }> = ({ name, f, style }) => (
  <Freeze frame={Math.max(0, Math.round(f))}>
    <OffthreadVideo src={staticFile(`web/clips/${name}.mp4`)} muted pauseWhenBuffering={false} style={{ position: 'absolute', left: 0, top: 0, width: '100%', ...style }} />
  </Freeze>
);

/** A still (full page, document coords), scrolled by `scroll` capture px, filling its parent's width. */
export const Still: React.FC<{ src: string; scroll?: number; viewW?: number; parentW: number; style?: React.CSSProperties }> = ({ src, scroll = 0, viewW = 1440, parentW, style }) => (
  <Img src={staticFile(src)} style={{ position: 'absolute', left: 0, top: -scroll * (parentW / viewW), width: parentW, ...style }} />
);

/**
 * A crop of a capture (clip frame or still) at box b (capture px), drawn at scale s (window px per capture px),
 * centred on its origin - to be placed in 3D above the window and lifted out of the page.
 */
export const PageCrop: React.FC<{
  b: { x: number; y: number; w: number; h: number }; s: number; clip?: { name: string; f: number }; still?: { src: string; scroll?: number }; view?: { w: number; h: number };
  radius?: number; lift?: number; glow?: number; sweep?: number; pad?: number;
}> = ({ b, s, clip, still, view = VIEW.d, radius = 16, lift = 1, glow = 0, sweep, pad = 0 }) => {
  const W = (b.w + 2 * pad) * s, H = (b.h + 2 * pad) * s;
  const fullW = view.w * s;
  const ox = -(b.x - pad) * s, oy = -(b.y - pad) * s;
  return (
    <div style={{
      position: 'absolute', left: -W / 2, top: -H / 2, width: W, height: H, borderRadius: radius * s, overflow: 'hidden', background: '#fbfaff',
      boxShadow: `0 ${30 * lift}px ${80 * lift}px -${10 * lift}px ${rgba('violet', 0.45 * lift)}, 0 0 ${60 * glow}px ${rgba('violet2', 0.6 * glow)}`,
      outline: glow > 0 ? `${1.5}px solid ${rgba('violet2', 0.6 * glow)}` : undefined,
    }}>
      <div style={{ position: 'absolute', left: ox, top: oy, width: fullW }}>
        {clip ? <Clip name={clip.name} f={clip.f} /> : still ? <Img src={staticFile(still.src)} style={{ position: 'absolute', left: 0, top: -(still.scroll ?? 0) * s, width: fullW }} /> : null}
      </div>
      {sweep !== undefined ? <Sweep k={sweep} /> : null}
    </div>
  );
};
