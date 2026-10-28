// The Fabius crystal (the site's hero object, ported to @remotion/three in src/three/) framed for a scene: transparent
// over the video's own lavender world, an orbiting camera, the site's beats (one block slides out and sparkles).
import React from 'react';
import { CrystalScene, orbitCam } from '../three';
import { ease, prog } from '../lib/util';

export const HeroCrystal: React.FC<{ t: number; t0: number; t1: number; variant: 'reveal' | 'end' }> = ({ t, t0, t1 }) => {
  const k = prog(t, t0, t1, ease.inOutCubic);
  // a slow, calm orbit: "it waits"
  const cam = orbitCam(-18 + 34 * k, 10 - 4 * k, 10.5 - 1.2 * k, [0, 0.05, 0], 30);
  return (
    <CrystalScene
      t={t - t0 + 3.0}
      cam={cam}
      background="transparent"
      assemble={1}
      position={[2.15, 0.1, 0]}
      scale={0.82}
      beatAt={[{ t: 1.2 + 3.0, block: 'verified' }, { t: 4.6 + 3.0, block: 'sealed' }]}
    />
  );
};
