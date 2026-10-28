// The whole video: scenes on the timeline (each wrapped in its transitions), then the finishing layers, the
// captions and the soundtrack. Every frame is a pure function of the frame number.
import React, { useMemo } from 'react';
import { AbsoluteFill, Html5Audio, staticFile, useCurrentFrame, useVideoConfig } from 'remotion';
import { loadFonts } from './lib/fonts';
import { C } from './lib/palette';
import { clamp } from './lib/util';
import { makeTimeline } from './timeline';
import { SCENES } from './scenes';
import { BloomLight, DipVeil, TrLayer } from './fx/transition';
import { Grain, Vignette } from './fx/fx';
import { Captions } from './ui/text';

loadFonts();

export type VideoProps = { audio: string; only: string; captions: boolean };

export const Video: React.FC<VideoProps> = ({ audio, only, captions }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const t = frame / fps;
  const tl = useMemo(() => makeTimeline(SCENES), []);
  const items = tl.map((e, i) => {
    const trIn = e.tr, trOut = tl[i + 1]?.tr;
    return { e, trIn, trOut, a: e.t0 - (trIn ? trIn.d / 2 : 0), b: e.t1 + (trOut ? trOut.d / 2 : 0) };
  });
  const vis = items.filter((x) => (!only || x.e.id === only) && t >= x.a && t < x.b);
  const cur = tl.find((e) => t >= e.t0 && t < e.t1) ?? tl[tl.length - 1]!;
  return (
    <AbsoluteFill style={{ background: C.lav }}>
      {vis.map(({ e, trIn, trOut }) => (
        <TrLayer key={e.id} id={e.id} trIn={trIn} trOut={trOut}
          kin={trIn ? clamp((t - (e.t0 - trIn.d / 2)) / trIn.d) : 1}
          kout={trOut ? clamp((t - (e.t1 - trOut.d / 2)) / trOut.d) : 0}>
          <e.Comp t={t} t0={e.t0} t1={e.t1} frame={frame} fps={fps} />
        </TrLayer>
      ))}
      {tl.filter((e) => e.tr?.type === 'bloom').map((e) => <BloomLight key={`b${e.id}`} t={t} at={e.t0} d={e.tr!.d} />)}
      {tl.filter((e) => e.tr?.type === 'dip').map((e) => <DipVeil key={`d${e.id}`} t={t} at={e.t0} d={e.tr!.d} />)}
      <Vignette strength={cur.dark ? 0.42 : 0.16} />
      <Grain frame={frame} opacity={cur.dark ? 0.07 : 0.045} />
      {captions ? <Captions t={t} dark={(x) => !!tl.find((e) => x >= e.t0 && x < e.t1)?.dark} hide={HIDE} /> : null}
      {audio ? <Html5Audio src={staticFile(audio)} /> : null}
    </AbsoluteFill>
  );
};

/** Caption pages hidden where a big headline already carries the same words (no double text). Filled per scene. */
import { at as voAt, line as voLine } from './lib/vo';
const whole = (id: string): [number, number] => [voLine(id).start - 0.2, voLine(id).end + 0.2];
/** Caption pages hidden where a big headline already carries the same words (no double text). */
export const HIDE: [number, number][] = [
  whole('hook1'), whole('hook2'), whole('rev1'), whole('rule1'), whole('desk1'), whole('use1'), whole('end3'), whole('end4'),
  [voLine('rev2').start - 0.2, voAt('rev2', 'It') - 0.05],
  [voAt('seal2', 'Not') - 0.1, voLine('seal2').end + 0.2],
  [voLine('end1').start - 0.2, voAt('end1', "It's") - 0.05],
];
