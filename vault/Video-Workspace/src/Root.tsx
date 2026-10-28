import React from 'react';
import { Composition } from 'remotion';
import { Video, type VideoProps } from './Video';
import { DURATION } from './lib/vo';

export const FPS = 60;

export const Root: React.FC = () => (
  <>
    <Composition
      id="Fabius"
      component={Video}
      durationInFrames={Math.ceil(DURATION * FPS)}
      fps={FPS}
      width={1920}
      height={1080}
      defaultProps={{ audio: 'audio/mix_v2.mp3', only: '', captions: true } satisfies VideoProps}
    />
  </>
);
