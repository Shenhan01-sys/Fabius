// Test compositions for the 3D ports (1920x1080, 60 fps). Each flies a camera through several POVs; input props switch bloom, transparency
// and the backdrop so the same timeline checks compositing.

import React from 'react';
import { AbsoluteFill, Composition, useCurrentFrame, useVideoConfig } from 'remotion';
import { camPath, lerpCam, orbitCam, toOrbit, type CameraDesc, type CamKey } from '../camera';
import { facingBlock } from '../crystal/Crystal';
import { CRYSTAL_SITE_CAM, crystalSiteLayout, CrystalScene } from '../crystal/CrystalScene';
import { CRYSTAL_COUNTS, deskSeats } from '../snapshot';
import { floorAnchors, floorSiteCam, FloorScene, seatToWorld } from '../desk/FloorScene';
import { LIVEBOOK_ANCHORS, liveBookAgentPositions, liveBookSiteCam, LiveBookScene, X } from '../desk/LiveBookScene';
import { DEFAULT_CYCLE } from '../desk/cycle';
import { DESK_BACKDROP_CSS, HERO_BACKDROP_CSS } from '../palette';
import { easeInOutCubic, ramp, smoothstep, type Vec3 } from '../util';

const FPS = 60;
type TestProps = { bloom?: boolean; transparent?: boolean; backdrop?: string; labels?: boolean };

// ---------------------------------------------------------------- CrystalTest (8 s): site framing -> low-angle close-up -> top-down orbit

const CrystalTest: React.FC<TestProps> = ({ bloom = true, transparent = false, backdrop }) => {
  const frame = useCurrentFrame();
  const { fps, width, height } = useVideoConfig();
  const t = frame / fps;
  const site = crystalSiteLayout(width / height);
  const c = site.position;
  const keys: CamKey[] = [
    { at: 0, cam: CRYSTAL_SITE_CAM },
    { at: 2.3, cam: CRYSTAL_SITE_CAM, hold: true },
    { at: 4.0, cam: orbitCam(-28, -13, 6.0, [c[0], c[1] + 0.15, c[2]], 26, 3), hold: true },
    { at: 4.9, cam: orbitCam(-16, -7, 6.3, [c[0], c[1] + 0.1, c[2]], 27, 1.5) },
    { at: 6.3, cam: orbitCam(40, 62, 9.2, c, 30) },
    { at: 8.0, cam: orbitCam(118, 78, 9.6, c, 30) },
  ];
  const cam = camPath(keys, t);
  const base = { t, counts: CRYSTAL_COUNTS, position: site.position, scale: site.scale };
  // pop the sealed (indigo) block that faces the close-up camera, then a verified one facing the top-down camera
  const b1 = facingBlock({ ...base, t: 4.2 }, camPath(keys, 4.2).position, 'sealed');
  const b2 = facingBlock({ ...base, t: 6.6 }, camPath(keys, 6.6).position, 'verified');
  const spread = smoothstep(5.6, 6.6, t) * 0.55 * (1 - smoothstep(7.2, 7.95, t));
  return (
    <AbsoluteFill style={{ background: backdrop ?? HERO_BACKDROP_CSS }}>
      <CrystalScene
        {...base}
        cam={cam}
        bloom={bloom ? undefined : false}
        background={transparent ? 'transparent' : undefined}
        spread={spread}
        beatAt={[
          { t: 3.55, block: b1 },
          { t: 6.2, block: b2 },
        ]}
      />
    </AbsoluteFill>
  );
};

// ---------------------------------------------------------------- CrystalWaveTest (6 s): sealWave then verifyWave, slow orbit

const CrystalWaveTest: React.FC<TestProps> = ({ bloom = true, transparent = false, backdrop }) => {
  const t = useCurrentFrame() / useVideoConfig().fps;
  const cam = orbitCam(-20 + t * 9, 12 + t * 2, 8.4, [0, 0, 0], 30);
  return (
    <AbsoluteFill style={{ background: backdrop ?? HERO_BACKDROP_CSS }}>
      <CrystalScene
        t={t + 4}
        cam={cam}
        bloom={bloom ? undefined : false}
        background={transparent ? 'transparent' : undefined}
        sealWave={easeInOutCubic(ramp(0.4, 2.8, t))}
        verifyWave={easeInOutCubic(ramp(3.1, 5.6, t))}
        beatAt={[]}
      />
    </AbsoluteFill>
  );
};

// ---------------------------------------------------------------- DeskTest (10 s): one Live Book cycle

const DeskTest: React.FC<TestProps> = ({ transparent = true, backdrop, labels = true }) => {
  const frame = useCurrentFrame();
  const { fps, width, height } = useVideoConfig();
  const t = frame / fps;
  const site = liveBookSiteCam(width / height);
  const A = LIVEBOOK_ANCHORS;
  const agents = liveBookAgentPositions(DEFAULT_CYCLE.agents.length);
  const eye: Vec3 = [X.agents + 0.2, agents[0].head[1] + 0.02, 0];
  const keys: CamKey[] = [
    { at: 0, cam: site },
    { at: 0.9, cam: site, hold: true },
    // low angle at the agents' eye level (dolly-zoom out of the telephoto)
    { at: 2.5, cam: orbitCam(-32, 2, 3.7, eye, 40), hold: true },
    // orbit around the formula machine while it spins up and picks the winner
    { at: 3.4, cam: orbitCam(-60, 24, 4.9, A.formula.focus, 34) },
    { at: 4.6, cam: orbitCam(30, 26, 4.6, A.formula.focus, 34) },
    // past the robot as its chest lights and the arm swings to the book
    { at: 5.7, cam: orbitCam(18, 10, 3.6, [X.bot + 0.6, 1.0, 0], 36) },
    // the book bars grow
    { at: 7.0, cam: orbitCam(-12, 24, 4.0, [X.book + 0.4, 0.6, 0], 34) },
    // push in to the chain stack as the new block lands and lights
    { at: 8.0, cam: orbitCam(26, 18, 3.6, A.chain.focus, 34) },
    { at: 10, cam: orbitCam(12, 12, 2.7, [X.chain, 0.8, 0], 30), hold: true },
  ];
  const cam = camPath(keys, t);
  const cycleT = ramp(1.2, 9.2, t);
  // site-style labels while the camera is wide; they fade as it moves in, back for the end card
  const labelOpacity = 1 - smoothstep(1.0, 1.6, t);
  return (
    <AbsoluteFill style={{ background: backdrop ?? DESK_BACKDROP_CSS }}>
      <LiveBookScene t={t} cam={cam} cycleT={cycleT} labels={labels && labelOpacity > 0} labelOpacity={labelOpacity} background={transparent ? 'transparent' : '#f6f4fd'} />
    </AbsoluteFill>
  );
};

// ---------------------------------------------------------------- FloorTest (8 s): site iso -> over-the-shoulder -> tower beat -> top-down orbit

/** Over the worker's right shoulder onto its monitor (desk-local points, see seatToWorld). */
function shoulderCam(slug: string): CameraDesc {
  const seat = deskSeats().find((s) => s.slug === slug)!;
  return { position: seatToWorld(seat, [-0.95, 2.0, -1.45]), target: seatToWorld(seat, [0.12, 1.1, 0.84]), fov: 34 };
}

const FloorTest: React.FC<TestProps> = ({ transparent = true, backdrop, labels = true }) => {
  const frame = useCurrentFrame();
  const { fps, width, height } = useVideoConfig();
  const t = frame / fps;
  const site = floorSiteCam(width / height);
  const anchors = floorAnchors(deskSeats());
  const shoulder = toOrbit(shoulderCam('berita'));
  const keys: CamKey[] = [
    { at: 0, cam: site },
    { at: 1.1, cam: site, hold: true },
    { at: 2.9, cam: shoulder, hold: true },
    { at: 3.5, cam: lerpCam(shoulder, { ...shoulder, az: shoulder.az + 8, dist: shoulder.dist * 0.92 }, 1) },
    { at: 5.2, cam: orbitCam(-75, 22, 4.6, anchors.tower.top, 34) },
    { at: 6.4, cam: orbitCam(-20, 62, 13.5, [0, 0.4, 0], 34) },
    { at: 8.0, cam: orbitCam(40, 80, 14.5, [0, 0.4, 0], 34) },
  ];
  const cam = camPath(keys, t);
  const labelOpacity = 1 - smoothstep(0.9, 1.5, t) + smoothstep(6.6, 7.4, t);
  return (
    <AbsoluteFill style={{ background: backdrop ?? DESK_BACKDROP_CSS }}>
      <FloorScene t={t} cam={cam} beats={[4.3]} labels={labels && labelOpacity > 0} labelOpacity={Math.min(1, labelOpacity)} background={transparent ? 'transparent' : '#f6f4fd'} />
    </AbsoluteFill>
  );
};

export const Root3D: React.FC = () => (
  <>
    <Composition id="CrystalTest" component={CrystalTest} durationInFrames={8 * FPS} fps={FPS} width={1920} height={1080} defaultProps={{}} />
    <Composition id="DeskTest" component={DeskTest} durationInFrames={10 * FPS} fps={FPS} width={1920} height={1080} defaultProps={{}} />
    <Composition id="FloorTest" component={FloorTest} durationInFrames={8 * FPS} fps={FPS} width={1920} height={1080} defaultProps={{}} />
    <Composition id="CrystalWaveTest" component={CrystalWaveTest} durationInFrames={6 * FPS} fps={FPS} width={1920} height={1080} defaultProps={{}} />
  </>
);
