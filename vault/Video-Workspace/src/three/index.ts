// Public API of the 3D ports (see README.md). Import from 'src/three' in a Remotion scene.

export * from './camera';
export { Stage, type Background, type BloomDesc, type FogDesc, type StageProps, type ToneMap } from './Stage';
export { Tag3D, type TagLine, type TagSpec } from './labels';
export { loadThreeFonts, useThreeFonts, MONO, SANS } from './fonts';
export { C, DESK_BACKDROP_CSS, HERO_BACKDROP_CSS } from './palette';
export * from './util';

export {
  Crystal,
  crystalLayout,
  beatables,
  beatAt,
  assembleEnd,
  blockPose,
  crystalTransform,
  crystalBlockWorld,
  facingBlock,
  BEAT_S,
  BEAT_LEN,
  SETTLE_S,
  FLY_S,
  type Block,
  type BlockKind,
  type BeatSpec,
  type BeatState,
  type Counts,
  type CrystalProps,
} from './crystal/Crystal';
export {
  CrystalScene,
  CrystalEnvironment,
  CrystalLights,
  CRYSTAL_SITE_CAM,
  CRYSTAL_BLOOM,
  CRYSTAL_FOG,
  crystalSiteLayout,
  crystalBeatInfo,
  type CrystalSceneProps,
} from './crystal/CrystalScene';

export {
  LiveBookScene,
  LiveBookWorld,
  liveBookSiteCam,
  liveBookLabels,
  liveBookAgentPositions,
  LIVEBOOK_ANCHORS,
  LIVEBOOK_POINTS,
  CYCLE,
  X as LIVEBOOK_X,
  PAD as LIVEBOOK_PAD,
  type LiveBookProps,
  type LiveBookSceneProps,
  type Station,
} from './desk/LiveBookScene';
export { FloorScene, FloorWorld, floorSiteCam, floorAnchors, floorLabels, seatToWorld, TOWER, type FloorAnchors, type FloorProps, type FloorSceneProps } from './desk/FloorScene';
export { LIVE_CYCLE, REVEALED_CYCLE, DEFAULT_CYCLE, BOTS, liveCycle, revealedCycle, revealedDecision, type PipelineCycle, type CycleAgent } from './desk/cycle';
export { Npc, npcJoints, mat, faceTexture, type NpcProps } from './desk/parts';
export { seats, layout as seatLayout, pose, hubBook, fmtPct, glyph, poseWord, type Pose, type Seat, type Look } from './desk/model';
export { lookFor } from './desk/looks';
export type { Buku, Desk, LiveBookData, Lock, Siklus } from './desk/types';
export {
  DESK,
  LIVE_BOOK,
  LOCKS,
  CHAIN,
  CRYSTAL_COUNTS,
  FLOOR_NOW,
  SNAPSHOT_FETCHED_UTC,
  SNAPSHOT_NOTE,
  SNAPSHOT_SOURCES,
  deskSeats,
  deskHub,
  deskCycles,
  deskLooks,
} from './snapshot';
