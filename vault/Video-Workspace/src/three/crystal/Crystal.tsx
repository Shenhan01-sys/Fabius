// Port of web/src/components/hero/Crystal.tsx: the Fabius agent as a 3x3x3 commitment crystal. Core = the agent (always glowing); the 26
// outer blocks = commitments: indigo = rule locked on-chain (in lock order), white = verified signal, clear = empty slot.
// Same layout (seeded shuffle 20261003), materials, fly-in, breathing rotation, 3.4 s beat and lights as the site, but every value is a pure
// function of `t` and props. Storytelling extras: assemble, spread, beatAt, sealWave / verifyWave, sparkles.

import React, { useEffect, useMemo } from 'react';
import * as THREE from 'three';
import { RoundedBoxGeometry } from 'three-stdlib';
import { add3, bump, clamp01, easeOutBack, lerp, lerp3, rng, smoothstep, type Lean, type Vec3 } from '../util';

export type BlockKind = 'core' | 'empty' | 'sealed' | 'verified';
export type Counts = { verified: number; sealed: number; empty: number };

export const BEAT_S = 3.4; // site: one beat every 3.4 s
export const BEAT_LEN = 1.5; // site: a beat lasts 1.5 s
export const SETTLE_S = 3.2; // site: beats start 3.2 s after mount
export const FLY_S = 1.15; // site: each block flies in over 1.15 s

export type Block = {
  index: number;
  kind: BlockKind;
  cell: Vec3;
  target: Vec3;
  start: Vec3;
  spin: Vec3;
  delay: number;
  normal: Vec3;
  /** lock order for sealed blocks (index into the snapshot's locks), -1 otherwise (site) */
  order: number;
  /** commit order used by sealWave/verifyWave: sealed blocks first in lock order, then verified; -1 = empty/core */
  rank: number;
};

/** Identical to the site's layout(): same generator, same call order, so the same cells are indigo/white/clear. */
export function crystalLayout(counts: Counts): Block[] {
  const r = rng(20261003);
  const cells: Vec3[] = [];
  for (let x = -1; x <= 1; x++) for (let y = -1; y <= 1; y++) for (let z = -1; z <= 1; z++) cells.push([x, y, z]);
  const len2 = (c: Vec3) => c[0] * c[0] + c[1] * c[1] + c[2] * c[2];
  const outer = cells.map((_, i) => i).filter((i) => len2(cells[i]) > 0);
  for (let i = outer.length - 1; i > 0; i--) {
    const j = Math.floor(r() * (i + 1));
    [outer[i], outer[j]] = [outer[j], outer[i]];
  }
  const kinds: BlockKind[] = cells.map((c) => (len2(c) === 0 ? 'core' : 'empty'));
  const order: number[] = cells.map(() => -1);
  const rank: number[] = cells.map(() => -1);
  let k = 0;
  for (let i = 0; i < counts.sealed && k < outer.length; i++, k++) {
    kinds[outer[k]] = 'sealed';
    order[outer[k]] = i;
    rank[outer[k]] = k;
  }
  for (let i = 0; i < counts.verified && k < outer.length; i++, k++) {
    kinds[outer[k]] = 'verified';
    rank[outer[k]] = k;
  }
  return cells.map((c, i) => {
    const dx = r() - 0.5;
    const dy = r() - 0.3;
    const dz = r() - 0.5;
    const dl = Math.hypot(dx, dy, dz) || 1;
    const ax = Math.abs(c[0]) >= Math.abs(c[1]) && Math.abs(c[0]) >= Math.abs(c[2]) ? 0 : Math.abs(c[1]) >= Math.abs(c[2]) ? 1 : 2;
    const normal: Vec3 = [ax === 0 ? Math.sign(c[0]) : 0, ax === 1 ? Math.sign(c[1]) : 0, ax === 2 ? Math.sign(c[2]) : 0];
    const startLen = 6 + r() * 4;
    const spin: Vec3 = [r() * 4, r() * 4, r() * 4];
    const delay = 0.25 + (kinds[i] === 'core' ? 0 : 0.18) + i * 0.028 + r() * 0.12;
    return {
      index: i,
      kind: kinds[i],
      cell: c,
      target: [c[0] * 1.02, c[1] * 1.02, c[2] * 1.02],
      start: [(dx / dl) * startLen, (dy / dl) * startLen, (dz / dl) * startLen],
      spin,
      delay,
      normal,
      order: order[i],
      rank: rank[i],
    };
  });
}

/** The site's beat sequence: non-empty blocks, verified first (cell order), then sealed in lock order. */
export function beatables(blocks: Block[]): number[] {
  const idx = blocks.map((b) => b.index).filter((i) => blocks[i].kind === 'sealed' || blocks[i].kind === 'verified');
  return idx.sort((a, b) => blocks[a].order - blocks[b].order);
}

/** Time the last block lands (seconds of the fly-in clock). */
export const assembleEnd = (blocks: Block[]) => Math.max(...blocks.map((b) => b.delay)) + FLY_S;

export type BeatSpec = number | { t: number; block?: number | 'sealed' | 'verified'; len?: number };

export type BeatState = { active: number; phase: number; t0: number; seq: number; len: number };

/**
 * Which block is out at time t. Without beatAt: the site's schedule (from 3.2 s, every 3.4 s, cycling through beatables()).
 * With beatAt: only at those times; `block` = index into beatables(), or 'sealed' / 'verified' = the next block of that kind.
 */
export function beatAt(blocks: Block[], t: number, beats?: BeatSpec[], every = BEAT_S): BeatState {
  const seq = beatables(blocks);
  const none: BeatState = { active: -1, phase: 2, t0: 0, seq: -1, len: BEAT_LEN };
  if (!seq.length) return none;
  if (!beats) {
    if (t <= SETTLE_S) return none;
    const n = Math.floor((t - SETTLE_S) / every);
    return { active: seq[n % seq.length], phase: ((t - SETTLE_S) % every) / BEAT_LEN, t0: SETTLE_S + n * every, seq: n, len: BEAT_LEN };
  }
  const list = beats.map((b) => (typeof b === 'number' ? { t: b } : b)).sort((a, b) => a.t - b.t);
  // a beat stays current for 1.6 x its length (the tail lets sparkles finish) or until the next beat starts
  let pick = -1;
  for (let i = 0; i < list.length; i++) if (list[i].t <= t && t < list[i].t + (list[i].len ?? BEAT_LEN) * 1.6) pick = i;
  if (pick < 0) return none;
  const b = list[pick];
  const len = b.len ?? BEAT_LEN;
  let active: number;
  if (typeof b.block === 'number') active = seq[((b.block % seq.length) + seq.length) % seq.length];
  else if (b.block === 'sealed' || b.block === 'verified') {
    const ofKind = seq.filter((i) => blocks[i].kind === b.block);
    const nth = list.slice(0, pick).filter((x) => x.block === b.block).length;
    active = ofKind.length ? ofKind[nth % ofKind.length] : seq[pick % seq.length];
  } else active = seq[pick % seq.length];
  return { active, phase: (t - b.t) / len, t0: b.t, seq: pick, len };
}

// ---------------------------------------------------------------- materials (site values)

type GlassParams = { color: string; opacity: number; iridescence: number; iridescenceIOR: number; envMapIntensity: number };
const EMPTY_A: GlassParams = { color: '#e4dcff', opacity: 0.24, iridescence: 0.45, iridescenceIOR: 1.3, envMapIntensity: 1.05 };
const EMPTY_B: GlassParams = { color: '#c8b8ff', opacity: 0.32, iridescence: 0.25, iridescenceIOR: 1.3, envMapIntensity: 1.05 };
const SEALED: GlassParams = { color: '#2a1a94', opacity: 0.84, iridescence: 0, iridescenceIOR: 1.3, envMapIntensity: 0.9 };

const glass = (o: Partial<THREE.MeshPhysicalMaterialParameters>) =>
  new THREE.MeshPhysicalMaterial({
    transparent: true,
    depthWrite: false,
    roughness: 0.06,
    metalness: 0,
    clearcoat: 1,
    clearcoatRoughness: 0.05,
    envMapIntensity: 1.05,
    side: THREE.DoubleSide,
    ...o,
  });

const verifiedMat = () => new THREE.MeshPhysicalMaterial({ color: '#f4f0ff', emissive: '#b9a6ff', emissiveIntensity: 0.75, roughness: 0.25, clearcoat: 1 });

function useCrystalMaterials() {
  return useMemo(
    () => ({
      emptyA: glass(EMPTY_A),
      emptyB: glass(EMPTY_B),
      sealed: glass(SEALED),
      verified: verifiedMat(),
      core: new THREE.MeshPhysicalMaterial({ color: '#efe9ff', emissive: '#cbbcff', emissiveIntensity: 1.15, roughness: 0.35 }),
      edge: new THREE.LineBasicMaterial({ color: '#ffffff', transparent: true, opacity: 0.42 }),
      edgeDark: new THREE.LineBasicMaterial({ color: '#8f78ff', transparent: true, opacity: 0.7 }),
      // HDR white (linear > 1): the bloom pass turns each mote into a small star; without bloom it clamps to plain white
      spark: new THREE.MeshBasicMaterial({ color: new THREE.Color(3.4, 3.1, 4.4), toneMapped: false }),
    }),
    [],
  );
}

const _ca = new THREE.Color();
const _cb = new THREE.Color();
function applyGlass(m: THREE.MeshPhysicalMaterial, a: GlassParams, b: GlassParams, k: number) {
  m.color.copy(_ca.set(a.color).lerp(_cb.set(b.color), k));
  m.opacity = lerp(a.opacity, b.opacity, k);
  m.iridescence = lerp(a.iridescence, b.iridescence, k);
  m.iridescenceIOR = lerp(a.iridescenceIOR, b.iridescenceIOR, k);
  m.envMapIntensity = lerp(a.envMapIntensity, b.envMapIntensity, k);
}

// ---------------------------------------------------------------- props

export type CrystalProps = {
  /** seconds since the shot started */
  t: number;
  counts: Counts;
  /** 0..1 fly-in progress; default: driven by t exactly like the site (blocks land by ~2.4 s) */
  assemble?: number;
  /** 0..1 exploded view: blocks drift apart along their cell directions */
  spread?: number;
  /** explicit beat times (seconds); default: the site's schedule (from 3.2 s, every 3.4 s) */
  beatAt?: BeatSpec[];
  beatEvery?: number;
  /** 0..1: non-empty blocks turn from clear to indigo in commit order (sealed first, in lock order). undefined = final state */
  sealWave?: number;
  /** 0..1: verified blocks turn from indigo to white in commit order (only meaningful with sealWave) */
  verifyWave?: number;
  /** pointer lean as on the site, -1..1 each */
  lean?: Lean;
  /** crystal centre (site: viewport.width * 0.22, 0.78 on wide screens) */
  position?: Vec3;
  /** site: 0.76 on wide screens, 0.66 narrow */
  scale?: number;
  /** breathing, bob and slow rotation (site); false = frozen pose (rotation from `spin`) */
  idle?: boolean;
  /** extra yaw in radians added to the site's rotation */
  yaw?: number;
  /** small light motes from the popping block's face on each beat (video addition; the site only flashes a light) */
  sparkles?: boolean;
  /** soft violet contact shadow under the crystal (3D stand-in for the site's CSS ellipse) */
  groundShadow?: boolean;
};

/** Group transform the site applies every frame (position, rotation, scale), as pure maths. */
export function crystalTransform(p: Pick<CrystalProps, 't' | 'lean' | 'position' | 'scale' | 'idle' | 'yaw'>) {
  const t = p.t;
  const lean = p.lean ?? { x: 0, y: 0 };
  const base = p.position ?? [0, 0, 0];
  const idle = p.idle ?? true;
  const breathe = idle ? 1 + Math.sin(t * 1.3) * 0.012 : 1;
  return {
    position: [base[0] + lean.x * 0.25, base[1] + lean.y * 0.15 + (idle ? Math.sin(t * 0.9) * 0.06 : 0), base[2]] as Vec3,
    rotation: [0.52 - lean.y * 0.18, Math.PI / 4 + (idle ? t * 0.11 : 0) + lean.x * 0.25 + (p.yaw ?? 0), 0] as Vec3,
    scale: (p.scale ?? 0.76) * breathe,
  };
}

const SPREAD = 1.15;

/** Local (crystal-space) position, rotation and scale of block i at time t: the site's per-frame maths plus spread. */
export function blockPose(b: Block, ta: number, beat: BeatState, spread: number) {
  const p = easeOutBack(clamp01((ta - b.delay) / FLY_S));
  let pos = lerp3(b.start, b.target, p);
  const rot: Vec3 = [b.spin[0] * (1 - p), b.spin[1] * (1 - p), b.spin[2] * (1 - p)];
  let scale: number;
  if (b.index === beat.active) {
    const k = bump(beat.phase);
    pos = add3(pos, [b.normal[0] * 0.42 * k, b.normal[1] * 0.42 * k, b.normal[2] * 0.42 * k]);
    scale = 1 + 0.05 * k;
  } else scale = clamp01((ta - b.delay) * 3) * 0.999 + 0.001;
  if (spread > 0) pos = add3(pos, [b.cell[0] * spread * SPREAD, b.cell[1] * spread * SPREAD, b.cell[2] * spread * SPREAD]);
  return { pos, rot, scale };
}

/** World position of block i (for aiming a camera at the beat block, or a 2D callout). */
export function crystalBlockWorld(props: CrystalProps, index: number): Vec3 {
  const blocks = crystalLayout(props.counts);
  const ta = props.assemble === undefined ? props.t : clamp01(props.assemble) * assembleEnd(blocks);
  const beat = beatAt(blocks, props.t, props.beatAt, props.beatEvery);
  const { pos } = blockPose(blocks[index], ta, beat, props.spread ?? 0);
  const tr = crystalTransform(props);
  const v = new THREE.Vector3(...pos).multiplyScalar(tr.scale).applyEuler(new THREE.Euler(...tr.rotation)).add(new THREE.Vector3(...tr.position));
  return [v.x, v.y, v.z];
}

/**
 * Index into beatables() (use as a beatAt `block`) of the block of `kind` whose outward face points most toward `camPos` at props.t,
 * so a beat pops the block the camera is looking at.
 */
export function facingBlock(props: CrystalProps, camPos: Vec3, kind?: 'sealed' | 'verified'): number {
  const blocks = crystalLayout(props.counts);
  const seq = beatables(blocks);
  const tr = crystalTransform(props);
  const e = new THREE.Euler(...tr.rotation);
  const centre = new THREE.Vector3(...tr.position);
  let best = 0;
  let bestDot = -Infinity;
  seq.forEach((bi, k) => {
    const b = blocks[bi];
    if (kind && b.kind !== kind) return;
    const n = new THREE.Vector3(...b.normal).applyEuler(e);
    const p = new THREE.Vector3(...b.target).multiplyScalar(tr.scale).applyEuler(e).add(centre);
    const d = n.dot(new THREE.Vector3(...camPos).sub(p).normalize());
    if (d > bestDot) {
      bestDot = d;
      best = k;
    }
  });
  return best;
}

// ---------------------------------------------------------------- component

const SPARKS = 16;

function Sparkles({ block, at, beat, mat }: { block: Block; at: Vec3; beat: BeatState; mat: THREE.Material }) {
  const r = rng(1000 + block.index * 97 + beat.seq * 7919);
  const n = new THREE.Vector3(...block.normal);
  const u = new THREE.Vector3(n.y, n.z, n.x); // a tangent (cyclic swap is perpendicular for axis normals)
  const w = new THREE.Vector3().crossVectors(n, u);
  const tau = beat.phase * beat.len - 0.28; // seconds since the block cleared the face
  const out: React.ReactNode[] = [];
  for (let i = 0; i < SPARKS; i++) {
    const a = r() * Math.PI * 2;
    const spreadR = 0.35 + r() * 0.75;
    const speed = 1.2 + r() * 1.5;
    const life = 0.7 + r() * 0.6;
    const size = 0.022 + r() * 0.03;
    const delay = r() * 0.25;
    const spinA = r() * 6;
    const local = tau - delay;
    if (local <= 0 || local >= life) {
      continue;
    }
    const f = local / life;
    const dir = n.clone().multiplyScalar(1).addScaledVector(u, Math.cos(a) * spreadR).addScaledVector(w, Math.sin(a) * spreadR).normalize();
    const travel = speed * local * (1 - 0.45 * f);
    const origin = new THREE.Vector3(...at).addScaledVector(n, 0.47);
    const p = origin.addScaledVector(dir, travel);
    const s = size * Math.sin(Math.PI * Math.min(1, f * 1.4 + 0.15)) * (1 - f * 0.5);
    out.push(
      <mesh key={i} material={mat} position={p} rotation={[spinA + local * 4, spinA * 0.7, local * 3]} scale={s}>
        <octahedronGeometry args={[1, 0]} />
      </mesh>,
    );
  }
  return <>{out}</>;
}

function useGroundShadowTexture() {
  return useMemo(() => {
    const c = document.createElement('canvas');
    c.width = c.height = 256;
    const g = c.getContext('2d')!;
    const grad = g.createRadialGradient(128, 128, 0, 128, 128, 128);
    // the site's CSS: radial-gradient(closest-side, rgba(75,47,209,.26), rgba(75,47,209,.09) 55%, transparent)
    grad.addColorStop(0, 'rgba(75,47,209,0.26)');
    grad.addColorStop(0.55, 'rgba(75,47,209,0.09)');
    grad.addColorStop(1, 'rgba(75,47,209,0)');
    g.fillStyle = grad;
    g.fillRect(0, 0, 256, 256);
    const t = new THREE.CanvasTexture(c);
    t.colorSpace = THREE.SRGBColorSpace;
    return t;
  }, []);
}

export const Crystal: React.FC<CrystalProps> = (props) => {
  const { t, counts, spread = 0, sparkles = true, groundShadow = true } = props;
  const countsKey = `${counts.verified}/${counts.sealed}/${counts.empty}`;
  const blocks = useMemo(() => crystalLayout(counts), [countsKey]); // eslint-disable-line react-hooks/exhaustive-deps
  const mats = useCrystalMaterials();
  const geo = useMemo(() => new RoundedBoxGeometry(0.94, 0.94, 0.94, 4, 0.075), []);
  const edges = useMemo(() => new THREE.EdgesGeometry(new THREE.BoxGeometry(0.9, 0.9, 0.9)), []);
  const shadowTex = useGroundShadowTexture();
  const waves = props.sealWave !== undefined || props.verifyWave !== undefined;
  // per-block material instances, only needed while a wave recolours blocks one by one
  const waveMats = useMemo(
    () =>
      waves
        ? blocks.map(() => ({
            glass: glass(EMPTY_A),
            verified: verifiedMat(),
            edge: new THREE.LineBasicMaterial({ color: '#ffffff', transparent: true, opacity: 0.42 }),
          }))
        : null,
    [waves, blocks],
  );
  useEffect(
    () => () => {
      waveMats?.forEach((m) => {
        m.glass.dispose();
        m.verified.dispose();
        m.edge.dispose();
      });
    },
    [waveMats],
  );

  const end = assembleEnd(blocks);
  const ta = props.assemble === undefined ? t : clamp01(props.assemble) * end;
  const beat = beatAt(blocks, t, props.beatAt, props.beatEvery);
  const tr = crystalTransform(props);
  const coreK = clamp01((ta - 0.2) / 1.2);
  const nRank = blocks.filter((b) => b.rank >= 0).length;
  const nVer = blocks.filter((b) => b.kind === 'verified').length;
  const sealW = props.sealWave ?? 1;
  // with only sealWave given, verified blocks stop at indigo (committed, not yet verified)
  const verW = props.verifyWave ?? (props.sealWave !== undefined ? 0 : 1);
  const W = 3; // a block recolours over a window of 3 commit ranks, so neighbours overlap

  const beatBlock = beat.active >= 0 ? blocks[beat.active] : null;
  const beatK = beatBlock ? bump(beat.phase) : 0;
  const settled = clamp01((ta - 0.6) / (end - 0.6));

  return (
    <group>
      {groundShadow && (
        <mesh
          position={[tr.position[0], tr.position[1] - 1.95 * (tr.scale / 0.76) - spread * 0.9, tr.position[2]]}
          rotation-x={-Math.PI / 2}
          scale={(3.6 + spread * 2.2) * (tr.scale / 0.76)}
          renderOrder={-1}
        >
          <planeGeometry args={[1, 1]} />
          <meshBasicMaterial map={shadowTex} transparent depthWrite={false} toneMapped={false} opacity={smoothstep(0.35, 1, settled) * (1 - spread * 0.45)} />
        </mesh>
      )}
      <group position={tr.position} rotation={tr.rotation} scale={tr.scale}>
        <pointLight color="#b49dff" distance={5} decay={1.6} intensity={coreK * (5.5 + Math.sin(t * 1.7) * 1.2)} />
        <pointLight
          color="#ffffff"
          distance={3}
          decay={1.8}
          intensity={9 * beatK}
          position={beatBlock ? add3(beatBlock.target, [beatBlock.normal[0] * 0.9, beatBlock.normal[1] * 0.9, beatBlock.normal[2] * 0.9]) : [0, 0, 0]}
        />
        {blocks.map((b, i) => {
          const pose = blockPose(b, ta, beat, spread);
          let material: THREE.Material =
            b.kind === 'core' ? mats.core : b.kind === 'sealed' ? mats.sealed : b.kind === 'verified' ? mats.verified : i % 3 === 0 ? mats.emptyB : mats.emptyA;
          let edge: THREE.LineBasicMaterial | null = b.kind === 'core' ? null : b.kind === 'sealed' ? mats.edgeDark : mats.edge;
          let scale = pose.scale;
          if (waveMats && b.kind !== 'core') {
            const wm = waveMats[i];
            const emptyLook = i % 3 === 0 ? EMPTY_B : EMPTY_A;
            // seal: clear -> indigo; verify: indigo -> white (opaque), with a short pop at the switch
            const s = b.rank < 0 ? 0 : smoothstep(0, W, sealW * (nRank + W) - b.rank);
            const verRank = b.kind === 'verified' ? b.rank - (nRank - nVer) : -1;
            const v = verRank < 0 ? 0 : Math.min(s, smoothstep(0, W, verW * (nVer + W) - verRank));
            if (v >= 0.5) {
              material = wm.verified;
              wm.verified.emissiveIntensity = 0.75 + (1 - v) * 2.4;
              edge = wm.edge;
              wm.edge.color.set('#ffffff');
              wm.edge.opacity = 0.42;
            } else {
              applyGlass(wm.glass, emptyLook, SEALED, s);
              wm.glass.emissive.set('#b9a6ff');
              wm.glass.emissiveIntensity = v * 1.6;
              material = wm.glass;
              edge = wm.edge;
              wm.edge.color.copy(_ca.set('#ffffff').lerp(_cb.set('#8f78ff'), s));
              wm.edge.opacity = lerp(0.42, 0.7, s);
            }
            scale *= 1 + 0.07 * bump(s) + 0.07 * bump(v);
          }
          return (
            <mesh key={i} geometry={geo} material={material} position={pose.pos} rotation={pose.rot} scale={scale} renderOrder={b.kind === 'core' ? 0 : 1}>
              {edge && <lineSegments geometry={edges} material={edge} />}
            </mesh>
          );
        })}
        {sparkles && beatBlock && beat.phase > 0 && beat.phase < 1.6 ? (
          <Sparkles block={beatBlock} at={blockPose(beatBlock, ta, beat, spread).pos} beat={beat} mat={mats.spark} />
        ) : null}
      </group>
    </group>
  );
};
