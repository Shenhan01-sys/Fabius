// The whole video: plates on the timeline (each wrapped in its transitions), then grain, vignette and the HUD,
// with the soundtrack.
import React, { useMemo } from 'react';
import { AbsoluteFill, Audio, staticFile, useCurrentFrame, useVideoConfig } from 'remotion';
import { loadFonts } from './lib/fonts';
import { loadStrokeFonts } from './lib/stroke';
import { C } from './lib/palette';
import { LY } from './lib/lyrics';
import { clamp } from './lib/util';
import { makeTimeline } from './timeline';
import { Grain, Vignette } from './components/kit';
import { Hud } from './components/Hud';
import { Flash, TrLayer } from './components/transition';

loadFonts();
loadStrokeFonts();

export const Video: React.FC<{ audio: string; only?: string; hud?: boolean }> = ({ audio, only, hud = true }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const t = frame / fps;
  const tl = useMemo(() => makeTimeline(), []);
  const items = tl.map((e, i) => {
    const trIn = e.tr, trOut = tl[i + 1]?.tr;
    return { e, trIn, trOut, a: e.start - (trIn ? trIn.d / 2 : 0), b: e.end + (trOut ? trOut.d / 2 : 0) };
  });
  const vis = items.filter((x) => (!only || x.e.id === only) && t >= x.a && t < x.b);
  const cur = tl.find((e) => t >= e.start && t < e.end) ?? tl[tl.length - 1]!;
  const no = tl.indexOf(cur) + 1;
  const src = cur.src ? [...cur.src].reverse().find((s) => t >= s.at - 0.2) : undefined;
  const light = !!cur.ink?.(t);
  return (
    <AbsoluteFill style={{ background: C.night }}>
      {vis.map(({ e, trIn, trOut }) => (
        <TrLayer key={e.id} id={e.id} trIn={trIn} trOut={trOut}
          kin={trIn ? clamp((t - (e.start - trIn.d / 2)) / trIn.d) : 1}
          kout={trOut ? clamp((t - (e.end - trOut.d / 2)) / trOut.d) : 0}>
          <e.Comp t={t} start={e.start} end={e.end} frame={frame} fps={fps} />
        </TrLayer>
      ))}
      {tl.filter((e) => e.tr?.type === 'flash').map((e) => <Flash key={e.id} t={t} at={e.start} />)}
      <Vignette strength={light ? 0.16 : 0.42} />
      <Grain frame={frame} opacity={light ? 0.035 : 0.05} />
      {hud && <Hud t={t} fps={fps} duration={LY.duration} ink={light} plateNo={no} title={cur.title} src={src?.text} srcSince={src?.at} />}
      {audio ? <Audio src={staticFile(audio)} /> : null}
    </AbsoluteFill>
  );
};
