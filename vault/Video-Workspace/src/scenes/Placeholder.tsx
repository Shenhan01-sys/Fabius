import React from 'react';
import { AbsoluteFill } from 'remotion';
import { LavWorld, NightWorld } from '../fx/world';
import { label } from '../lib/fonts';
import { C } from '../lib/palette';
import type { SceneProps } from '../timeline';

/** Temporary stand-in while a scene is being built (never in a final render). */
export const Placeholder = (name: string, dark: boolean): React.FC<SceneProps> => {
  const P: React.FC<SceneProps> = ({ t }) => (
    <AbsoluteFill>
      {dark ? <NightWorld t={t} /> : <LavWorld t={t} />}
      <AbsoluteFill style={{ alignItems: 'center', justifyContent: 'center' }}>
        <div style={{ ...label(28, 700), color: dark ? C.violet2 : C.violet }}>scene · {name} · placeholder</div>
      </AbsoluteFill>
    </AbsoluteFill>
  );
  return P;
};
