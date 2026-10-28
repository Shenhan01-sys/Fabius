// REVEAL - "So we built the opposite. Meet Fabius. It seals every signal on BNB Chain, before the market answers."
// The hero plate is the Motion.so generation (public/motion/reveal-motion-so.mp4, made 7 Oct from our brief +
// site screenshots: dissolving cards -> a glowing core -> the glass crystal assembles -> the site's headline types),
// time-mapped onto the voiceover. On "answers" the camera pulls back: the same composition becomes the REAL home
// page (capture public/web/clips/home-hero.mp4) in a browser window floating in the lavender world.
import React from 'react';
import { AbsoluteFill, Freeze, OffthreadVideo, staticFile } from 'remotion';
import { At, camAt, Space } from '../cam/space';
import { LavWorld } from '../fx/world';
import { Headline } from '../ui/text';
import { BrowserWindow, Clip } from '../ui/browser';
import { C } from '../lib/palette';
import { clamp, ease, prog } from '../lib/util';
import { at, line } from '../lib/vo';
import type { SceneProps } from '../timeline';

/** piecewise-linear map through [t, value] keys */
export const pw = (t: number, keys: [number, number][]) => {
  if (t <= keys[0]![0]) return keys[0]![1];
  for (let i = 1; i < keys.length; i++) {
    const [a, va] = keys[i - 1]!, [b, vb] = keys[i]!;
    if (t <= b) return va + ((vb - va) * (t - a)) / (b - a || 1e-9);
  }
  return keys[keys.length - 1]![1];
};

const MotionPlate: React.FC<{ src: number }> = ({ src }) => (
  <Freeze frame={Math.max(0, Math.round(src * 60))}>
    <OffthreadVideo src={staticFile('motion/reveal-motion-so.mp4')} muted pauseWhenBuffering={false} style={{ position: 'absolute', inset: 0, width: '100%', height: '100%', objectFit: 'cover' }} />
  </Freeze>
);

export const S2Reveal: React.FC<SceneProps> = ({ t, t0, t1 }) => {
  const r1 = line('rev1'), r2 = line('rev2');
  const tMeet = at('rev2', 'Meet'), tSeals = at('rev2', 'seals'), tChain = at('rev2', 'Chain'), tBefore = at('rev2', 'before');
  // Motion.so source time for each moment of the voiceover
  const src = pw(t, [[t0, 10.25], [tMeet - 0.1, 10.7], [tSeals, 11.45], [tChain + 0.3, 13.7], [tBefore, 14.25], [r2.end - 0.2, 16.4], [t1, 17.0]]);
  const back = prog(t, r2.end - 0.55, t1 - 0.05, ease.inOutCubic); // pull back to the real page
  const plateA = 1 - prog(t, r2.end - 0.45, r2.end + 0.05, ease.inOutCubic);
  // the window: starts filling the frame (z large), ends floating, tilted
  const cam = camAt([
    { t: r2.end - 0.6, z: 610, rx: 0, ry: 0, x: 0, y: 0 },
    { t: t1 + 0.2, z: -80, rx: 7, ry: -16, x: 40, y: 10, ez: ease.inOutCubic },
  ], t);
  const siteF = 330 + Math.max(0, (t - (r2.end - 0.6)) * 60); // the settled hero (headline typed, crystal turning), cursor near the CTA
  return (
    <AbsoluteFill>
      <LavWorld t={t} seed={2} />
      {back > 0 && (
        <Space cam={cam} perspective={1700}>
          <At x={0} y={0} z={0}>
            <div style={{ opacity: clamp(back * 3) }}>
              <BrowserWindow w={1280} h={846} url="fabius-one.vercel.app" sweep={prog(t, r2.end - 0.2, t1 + 0.3)}>
                <Clip name="home-hero" f={Math.min(419, siteF)} />
              </BrowserWindow>
            </div>
          </At>
        </Space>
      )}
      <AbsoluteFill style={{ opacity: plateA, transform: `scale(${1 - 0.3 * back})`, transformOrigin: '50% 50%' }}>
        <MotionPlate src={src} />
      </AbsoluteFill>
      {/* our words over the plate (the plate's own headline arrives on "before the market answers") */}
      <AbsoluteFill style={{ justifyContent: 'center', alignItems: 'center', paddingBottom: 380 }}>
        <Headline t={t} size={84} col={C.ink} out={r1.end + 0.15} align="center"
          segs={[{ text: 'So we built', at: r1.words[0]!.start, voice: 'calm' }, { text: 'the opposite.', at: at('rev1', 'opposite') - 0.1, voice: 'accent' }]} />
      </AbsoluteFill>
      <AbsoluteFill style={{ padding: '0 0 0 130px', justifyContent: 'center' }}>
        <Headline t={t} size={150} col={C.ink} out={tChain - 0.35}
          segs={[{ text: 'Meet', at: tMeet, voice: 'calm' }, { text: 'Fabius.', at: at('rev2', 'Fabius'), voice: 'accent', br: true }]} />
      </AbsoluteFill>
    </AbsoluteFill>
  );
};
