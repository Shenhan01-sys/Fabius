// The edit: which scene plays when. Every cut sits in the pause before a scene's first voiceover line (found by
// content in public/data/vo.json), so a new read re-times the whole video.
import type React from 'react';
import type { Tr } from './fx/transition';
import { cut, DURATION } from './lib/vo';

export interface SceneProps { t: number; t0: number; t1: number; frame: number; fps: number }
export interface Entry {
  id: string;
  title: string;
  t0: number;
  t1: number;
  /** transition INTO this scene, centred on t0 */
  tr?: Tr;
  /** dark scene: captions in light-on-dark */
  dark?: boolean;
  Comp: React.FC<SceneProps>;
}

export type SceneMap = Record<string, React.FC<SceneProps>>;

export function makeTimeline(S: SceneMap): Entry[] {
  const b = {
    reveal: cut('reveal'), rules: cut('rules'), seal: cut('seal'), desk: cut('desk'), use: cut('use'),
    verify: cut('verify'), open: cut('open'), honest: cut('honest'), end: cut('end'), stop: DURATION,
  };
  return [
    { id: 'hook', title: 'Perfect track records', t0: 0, t1: b.reveal, Comp: S.hook!, dark: true },
    { id: 'reveal', title: 'Meet Fabius', t0: b.reveal, t1: b.rules, Comp: S.reveal!, tr: { type: 'bloom', d: 0.9 } },
    { id: 'rules', title: 'Rules first', t0: b.rules, t1: b.seal, Comp: S.rules!, tr: { type: 'whip', d: 0.55 } },
    { id: 'seal', title: 'Sealed', t0: b.seal, t1: b.desk, Comp: S.seal!, tr: { type: 'zoom', d: 0.7 } },
    { id: 'desk', title: 'The AI desk', t0: b.desk, t1: b.use, Comp: S.desk!, tr: { type: 'dip', d: 0.8 }, dark: true },
    { id: 'use', title: 'Get the signal', t0: b.use, t1: b.verify, Comp: S.use!, tr: { type: 'bloom', d: 0.8 } },
    { id: 'verify', title: 'Check it', t0: b.verify, t1: b.open, Comp: S.verify!, tr: { type: 'portal', d: 0.8 } },
    { id: 'open', title: 'Bring yours', t0: b.open, t1: b.honest, Comp: S.open!, tr: { type: 'whip', d: 0.55, dir: -1 } },
    { id: 'honest', title: 'No profit promises', t0: b.honest, t1: b.end, Comp: S.honest!, tr: { type: 'zoom', d: 0.7 } },
    { id: 'end', title: 'Fabius', t0: b.end, t1: b.stop, Comp: S.end!, tr: { type: 'zoom', d: 0.8 } },
  ];
}
