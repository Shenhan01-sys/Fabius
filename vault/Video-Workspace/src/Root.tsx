import React from 'react';
import { Composition } from 'remotion';
import { Video } from './Video';
import { LY } from './lib/lyrics';

export const FPS = 30;

export const Root: React.FC = () => (
  <>
    <Composition
      id="Fabius"
      component={Video}
      durationInFrames={Math.ceil(LY.duration * FPS)}
      fps={FPS}
      width={1920}
      height={1080}
      defaultProps={{ audio: 'audio/mix.mp3', only: '', hud: true }}
    />
  </>
);
