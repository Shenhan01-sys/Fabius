// The hero crystal as a full canvas: the site's lights, Lightformer environment, lav background + fog and bloom (deterministic, see Stage).

import { Environment, Lightformer } from '@react-three/drei';
import React from 'react';
import { type CameraDesc } from '../camera';
import { CRYSTAL_COUNTS, LOCKS } from '../snapshot';
import { C } from '../palette';
import { Stage, type Background, type BloomDesc, type FogDesc } from '../Stage';
import { bump, DEG, type Vec3 } from '../util';
import { beatAt, Crystal, crystalBlockWorld, crystalLayout, type CrystalProps } from './Crystal';

/** The site's camera: perspective at (0, 0, 11), fov 30, looking at the origin. */
export const CRYSTAL_SITE_CAM: CameraDesc = { position: [0, 0, 11], target: [0, 0, 0], fov: 30 };
/** The site's bloom: <Bloom intensity 0.22 luminanceThreshold 0.92 luminanceSmoothing 0.15 mipmapBlur /> */
export const CRYSTAL_BLOOM: BloomDesc = { intensity: 0.22, threshold: 0.92, smoothing: 0.15, mipmapBlur: true };
export const CRYSTAL_FOG: FogDesc = { color: C.lav, near: 14, far: 26 };

/**
 * Where the site puts the crystal for a frame of this aspect: on wide screens (visible width > 7.5 at z = 0) it sits right of centre at
 * (0.22 x visible width, 0.78) scaled 0.76, otherwise centred high (0, 0.2 x visible height) scaled 0.66.
 */
export function crystalSiteLayout(aspect: number): { position: Vec3; scale: number } {
  const h = 2 * 11 * Math.tan((30 * DEG) / 2);
  const w = h * aspect;
  return w > 7.5 ? { position: [w * 0.22, 0.78, 0], scale: 0.76 } : { position: [0, h * 0.2, 0], scale: 0.66 };
}

/** The site's environment: three rect Lightformers + a ring, rendered once into a 256 cube map. */
export const CrystalEnvironment: React.FC = () => (
  <Environment resolution={256} frames={1}>
    <Lightformer form="rect" intensity={2.1} position={[0, 6, -3]} scale={[12, 5, 1]} color="#ffffff" />
    <Lightformer form="rect" intensity={1.5} position={[-6, 1, 2]} rotation-y={Math.PI / 2} scale={[8, 3, 1]} color="#d8ccff" />
    <Lightformer form="rect" intensity={1.6} position={[6, -1, 2]} rotation-y={-Math.PI / 2} scale={[8, 3, 1]} color="#7a5cff" />
    <Lightformer form="ring" intensity={1.4} position={[0, 0, 6]} scale={3} color="#b9a6ff" />
  </Environment>
);

/** Lights the site adds outside the crystal group. */
export const CrystalLights: React.FC = () => (
  <>
    <ambientLight intensity={0.42} />
    <directionalLight position={[3, 7, 5]} intensity={0.85} />
  </>
);

export type CrystalSceneProps = Omit<CrystalProps, 'counts'> & {
  cam?: CameraDesc;
  /** default: the live site's counts from the snapshot (22 verified, 4 sealed, 0 empty on 7 Oct 2026) */
  counts?: CrystalProps['counts'];
  /** default lav (the site's canvas clear colour); 'transparent' lets the video's own world show through */
  background?: Background;
  /** default: the site's fog when the background is a colour, none when transparent */
  fog?: FogDesc | false | null;
  /** default: the site's bloom; false = no postprocessing (identical colours, no glow) */
  bloom?: BloomDesc | false;
};

export const CrystalScene: React.FC<CrystalSceneProps> = ({ cam = CRYSTAL_SITE_CAM, counts = CRYSTAL_COUNTS, background = C.lav, fog, bloom = CRYSTAL_BLOOM, ...crystal }) => (
  <Stage cam={cam} background={background} fog={fog === undefined ? (background === 'transparent' ? null : CRYSTAL_FOG) : fog} toneMapping="none" bloom={bloom || null}>
    <CrystalLights />
    <Crystal counts={counts} {...crystal} />
    <CrystalEnvironment />
  </Stage>
);

/**
 * What the site's onBeat callback told the DOM, as a pure function: which block is out at time t, its kind, how far out (0..1), its world
 * position (aim a camera or a 2D callout at it) and, for an indigo block, the on-chain lock it stands for (the site's beat label).
 */
export function crystalBeatInfo(props: Omit<CrystalProps, 'counts'> & { counts?: CrystalProps['counts'] }) {
  const counts = props.counts ?? CRYSTAL_COUNTS;
  const blocks = crystalLayout(counts);
  const b = beatAt(blocks, props.t, props.beatAt, props.beatEvery);
  if (b.active < 0) return null;
  const blk = blocks[b.active];
  return {
    index: b.active,
    kind: blk.kind,
    out: bump(b.phase),
    phase: b.phase,
    started: b.t0,
    world: crystalBlockWorld({ ...props, counts }, b.active),
    lock: blk.order >= 0 ? (LOCKS[blk.order] ?? null) : null,
  };
}
