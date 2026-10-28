// END - "Fabius waits for proof. Don't trust. Check it." + end card.
// The crystal turns slowly, calm (it waits); the site's verify headline in its two voices; then the end card:
// logo, the live URL with a QR code, and the plain terms (testnet, paper money, no profit claims).
import React from 'react';
import { AbsoluteFill, Img, staticFile } from 'remotion';
import { LavWorld } from '../fx/world';
import { GlowBlob, Sweep } from '../fx/fx';
import { Headline } from '../ui/text';
import { appear, Pill } from '../ui/bits';
import { C, rgba } from '../lib/palette';
import { archivo, inter, label, mono } from '../lib/fonts';
import { ease, prog } from '../lib/util';
import { at, line } from '../lib/vo';
import type { SceneProps } from '../timeline';
import { HeroCrystal } from './crystal-shot';

const Logo: React.FC<{ s?: number }> = ({ s = 1 }) => (
  <div style={{ display: 'flex', alignItems: 'center', gap: 18 * s }}>
    <svg width={64 * s} height={64 * s} viewBox="0 0 64 64">
      <defs><linearGradient id="lg" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stopColor="#7d5cff" /><stop offset="1" stopColor="#2a1a94" /></linearGradient></defs>
      <path d="M32 4 L57 18 L57 46 L32 60 L7 46 L7 18 Z" fill="url(#lg)" />
      <path d="M32 4 L57 18 L32 32 L7 18 Z" fill="#9d86ff" opacity="0.85" />
      <path d="M32 32 L57 18 L57 46 L32 60 Z" fill="#4b33c7" opacity="0.9" />
    </svg>
    <span style={{ ...archivo(84 * s, 700, 100), color: C.ink, letterSpacing: -2 * s }}>Fabius</span>
  </div>
);

export const S10End: React.FC<SceneProps> = ({ t, t0, t1 }) => {
  const l3 = line('end3'), l4 = line('end4');
  const card = prog(t, l4.end + 0.15, l4.end + 0.9, ease.cine);
  const head = 1 - card;
  return (
    <AbsoluteFill>
      <LavWorld t={t} seed={10} glow={1.1} />
      <GlowBlob x={1280} y={520} r={560} col="violet2" a={0.32} />
      <AbsoluteFill style={{ opacity: 1 - 0.65 * card, transform: `translateX(${card * 260}px) scale(${1 - 0.18 * card})` }}>
        <HeroCrystal t={t} t0={t0} t1={t1} variant="end" />
      </AbsoluteFill>
      {/* "Fabius waits for proof." then "Don't trust. Check it." */}
      <AbsoluteFill style={{ padding: '0 0 0 140px', justifyContent: 'center', opacity: head }}>
        <div style={{ position: 'relative', height: 420 }}>
          <div style={{ position: 'absolute', left: 0, top: 0 }}>
            <Headline t={t} size={92} out={l4.start - 0.25}
              segs={[{ text: 'Fabius waits', at: l3.words[0]!.start, voice: 'calm' }, { text: 'for proof.', at: at('end3', 'proof'), voice: 'accent', br: true }]} />
          </div>
          <div style={{ position: 'absolute', left: 0, top: 0 }}>
            <Headline t={t} size={150}
              segs={[{ text: "Don't trust.", at: l4.words[0]!.start, voice: 'calm' }, { text: 'Check it.', at: at('end4', 'Check'), voice: 'accent', br: true }]} />
          </div>
        </div>
      </AbsoluteFill>
      {/* end card */}
      <AbsoluteFill style={{ padding: '0 0 0 150px', justifyContent: 'center', opacity: card, pointerEvents: 'none' }}>
        <div style={{ ...appear(t, l4.end + 0.15, 0.7, 40) }}><Logo /></div>
        <div style={{ marginTop: 26, ...appear(t, l4.end + 0.35, 0.7, 30), ...archivo(54, 300, 112), color: C.ink, letterSpacing: -1 }}>
          Signals <span style={{ ...archivo(54, 800, 79, true), color: C.violet }}>sealed</span> before the outcome.
        </div>
        <div style={{ marginTop: 40, display: 'flex', alignItems: 'center', gap: 34, ...appear(t, l4.end + 0.55, 0.7, 30) }}>
          <div style={{ position: 'relative', overflow: 'hidden', borderRadius: 999 }}>
            <Pill fill size={36}>fabius-one.vercel.app</Pill>
            <Sweep k={prog(t, l4.end + 1.0, l4.end + 2.0)} />
          </div>
          <div style={{ padding: 12, borderRadius: 20, background: '#fff', boxShadow: `0 20px 50px -18px ${rgba('violet', 0.5)}` }}>
            <Img src={staticFile('img/qr-fabius.svg')} style={{ width: 132, height: 132, display: 'block' }} />
          </div>
        </div>
        <div style={{ marginTop: 34, display: 'flex', gap: 14, ...appear(t, l4.end + 0.8, 0.7, 20) }}>
          {['Live on BNB Chain testnet', 'Paper money', 'No profit claims', 'Verify: no key, no gas'].map((s) => (
            <div key={s} style={{ ...label(14, 700), color: C.violet, padding: '10px 16px', borderRadius: 999, background: 'rgba(255,255,255,0.75)', border: `1px solid ${rgba('violet', 0.18)}` }}>{s}</div>
          ))}
        </div>
        <div style={{ marginTop: 22, ...mono(18, 500), color: C.mist, ...appear(t, l4.end + 1.0, 0.7, 10) }}>github.com/Shenhan01-sys/Fabius · <span style={{ ...inter(18, 500) }}>built for BNB Chain</span></div>
      </AbsoluteFill>
    </AbsoluteFill>
  );
};
