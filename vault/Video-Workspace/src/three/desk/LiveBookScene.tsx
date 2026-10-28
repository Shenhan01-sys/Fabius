// Port of web/src/components/desk/floor/PipelineScene.tsx (P164, the "Fabius Live Book" strip): agents (the same voxel workers as the floor,
// standing; violet cube = valid vote, red cross = failed) -> formula machine (6 orbiting bot cubes, size = score, winner lit) -> rule robot
// (bot id on its chest, arm pointing at the book) -> book (bars: height = weight, violet = long, ink = short) -> BNB Chain stack (top block lit
// when the cycle's root is committed). Same geometry, palette, lights and positions as the site.
//
// Changes for video: no useFrame (everything from `t`), perspective camera from props (`liveBookSiteCam()` = the site's orthographic framing
// as a 4 deg telephoto), and `cycleT` (0..1) plays one cycle as a story: votes rise, the formula spins up and picks the winner, the robot
// lights its chest and raises its arm, the book bars grow, a new block drops onto the chain and lights. Without cycleT the scene shows the
// site's steady state. Labels: the site's DOM labels become optional in-3D tags (labels prop); anchors are exported for 2D callouts.

import { Environment, Lightformer, RoundedBox } from '@react-three/drei';
import React, { useEffect, useMemo } from 'react';
import * as THREE from 'three';
import { telephoto, type CameraDesc } from '../camera';
import { deskLooks } from '../snapshot';
import { MONO } from '../fonts';
import { Tag3D, type TagSpec } from '../labels';
import { C } from '../palette';
import { Stage, type Background, type FogDesc } from '../Stage';
import { bump, clamp01, easeInOutCubic, easeOutBack, hash, lerp, ramp, TAU, type Vec3 } from '../util';
import { BOTS, DEFAULT_CYCLE, type PipelineCycle } from './cycle';
import type { Look } from './looks';
import { mat, Npc } from './parts';

export const X = { agents: -6.3, formula: -2.0, bot: 1.6, book: 4.9, chain: 7.9 };
export const PAD = { agents: 3.4, formula: 2.2, bot: 2.0, book: 2.2, chain: 1.8 };
export type Station = keyof typeof X;
const ORDER: Station[] = ['agents', 'formula', 'bot', 'book', 'chain'];

/** Story windows inside one cycle (fractions of cycleT). Exported so narration/callouts can sync to them. */
export const CYCLE = {
  vote: [0.02, 0.2] as const, // agents vote one by one (cube pops above the head, pose think -> result)
  toFormula: [0.06, 0.3] as const, // vote motes arc into the formula machine
  formula: [0.2, 0.42] as const, // orbit spins up
  decide: 0.36, // winner cube lights
  toBot: [0.4, 0.47] as const, // pulse formula -> robot
  robot: [0.46, 0.6] as const, // chest screen shows the bot id, arm swings to the book
  toBook: [0.57, 0.63] as const,
  book: [0.61, 0.78] as const, // bars grow
  toChain: [0.74, 0.81] as const,
  chain: [0.8, 0.92] as const, // new block drops onto the stack and lights (sealed)
};

/**
 * The site's framing (orthographic, position (1.4, 5.2, 14) looking at (0.8, 0.95, 0), zoom fits 17.6 x 4.5) as a 4 deg telephoto.
 * zoomOut > 1 leaves margin around the strip (the site's own fit puts the agents' platform on the frame edge).
 */
export function liveBookSiteCam(aspect = 16 / 9, fov = 4, zoomOut = 1): CameraDesc {
  return telephoto({ position: [1.4, 5.2, 14], target: [0.8, 0.95, 0], fov: 30 }, Math.max(17.6 / aspect, 4.5) * zoomOut, fov);
}

/** World anchors: `label` = where the site pins its DOM label (2.35 above each station), `focus` = a good camera target. */
export const LIVEBOOK_ANCHORS: Record<Station, { label: Vec3; focus: Vec3 }> = {
  agents: { label: [X.agents, 2.53, 0], focus: [X.agents, 1.2, 0] },
  formula: { label: [X.formula, 2.35, 0], focus: [X.formula, 1.2, 0] },
  bot: { label: [X.bot, 2.53, 0], focus: [X.bot, 1.05, 0] },
  book: { label: [X.book, 2.53, 0], focus: [X.book, 0.55, 0] },
  chain: { label: [X.chain, 2.53, 0], focus: [X.chain, 0.75, 0] },
};

/** Camera targets by the names a shot list uses (robot = the site's "bot" station). */
export const LIVEBOOK_POINTS: Record<'agents' | 'formula' | 'robot' | 'book' | 'chain', Vec3> = {
  agents: LIVEBOOK_ANCHORS.agents.focus,
  formula: LIVEBOOK_ANCHORS.formula.focus,
  robot: LIVEBOOK_ANCHORS.bot.focus,
  book: LIVEBOOK_ANCHORS.book.focus,
  chain: LIVEBOOK_ANCHORS.chain.focus,
};

const agentGap = (n: number) => Math.min(0.62, (PAD.agents - 0.5) / Math.max(1, n));

/** Each standing agent: feet position, head centre and vote-cube position (world). */
export function liveBookAgentPositions(n: number): { feet: Vec3; head: Vec3; vote: Vec3 }[] {
  const gap = agentGap(n);
  return Array.from({ length: n }, (_, i) => {
    const x = X.agents + (i - (n - 1) / 2) * gap;
    const z = (i % 2) * 0.22 - 0.1;
    return { feet: [x, 0.18, z], head: [x, 0.18 + 0.82 * 1.42, z], vote: [x, 0.18 + 0.82 * 1.95, z] };
  });
}

const voteStart = (i: number, n: number) => CYCLE.vote[0] + (CYCLE.vote[1] - CYCLE.vote[0] - 0.05) * (n > 1 ? i / (n - 1) : 0);

// ---------------------------------------------------------------- materials

function useMaterials() {
  return useMemo(
    () => ({
      clay: mat(C.clay),
      seam: new THREE.MeshBasicMaterial({ color: C.violet2, toneMapped: false }),
      bad: mat(C.gap, { emissive: C.gap, emissiveIntensity: 0.5 }),
      glass: new THREE.MeshStandardMaterial({ color: C.violet2, transparent: true, opacity: 0.22, roughness: 0.1, metalness: 0.1 }),
      core: mat(C.violet, { emissive: C.violet, emissiveIntensity: 0.9 }),
      ring: new THREE.MeshBasicMaterial({ color: C.violet2, toneMapped: false }),
      lose: mat(C.lav3),
      ink: mat(C.ink, { roughness: 0.4 }),
      eye: new THREE.MeshBasicMaterial({ color: C.violet2, toneMapped: false }),
      joint: mat(C.lav3),
      long: mat(C.violet, { emissive: C.violet, emissiveIntensity: 0.25 }),
      short: mat(C.ink, { roughness: 0.5 }),
      flat: mat(C.lav3),
      locked: mat(C.lav3, { roughness: 0.6 }),
      cap: mat(C.violet, { emissive: C.violet, emissiveIntensity: 0.5 }),
      base: mat(C.lav2),
      wire: new THREE.MeshBasicMaterial({ color: C.violet2, transparent: true, opacity: 0.8, toneMapped: false }),
      dot: new THREE.MeshBasicMaterial({ color: '#ffffff', toneMapped: false }),
      mote: new THREE.MeshBasicMaterial({ color: C.violet2, toneMapped: false }),
    }),
    [],
  );
}
type Mats = ReturnType<typeof useMaterials>;

const unitBox = new THREE.BoxGeometry(1, 1, 1);

function Pad({ x, w, round = false, m }: { x: number; w: number; round?: boolean; m: Mats }) {
  return (
    <group position={[x, 0, 0]}>
      {round ? (
        <mesh material={m.clay} position={[0, 0.09, 0]} receiveShadow castShadow>
          <cylinderGeometry args={[w / 2, w / 2, 0.18, 48]} />
        </mesh>
      ) : (
        <RoundedBox args={[w, 0.18, 1.7]} radius={0.06} position={[0, 0.09, 0]} material={m.clay} receiveShadow castShadow />
      )}
      <mesh material={m.seam} position={[0, 0.005, round ? w / 2 - 0.02 : 0.86]}>
        <boxGeometry args={[round ? w * 0.7 : w - 0.1, 0.02, 0.02]} />
      </mesh>
    </group>
  );
}

// ---------------------------------------------------------------- 1. agents

function Agents({ cycle, looks, t, cyc, reduced, desync, m }: { cycle: PipelineCycle; looks: Record<string, Look>; t: number; cyc?: number; reduced: boolean; desync: boolean; m: Mats }) {
  const n = Math.max(1, cycle.agents.length);
  const gap = agentGap(n);
  // one vote material per agent so each flash is its own
  const voteMats = useMemo(() => cycle.agents.map(() => mat(C.violet, { emissive: C.violet, emissiveIntensity: 0.6 })), [cycle.agents]);
  useEffect(() => () => voteMats.forEach((x) => x.dispose()), [voteMats]);
  return (
    <group position={[X.agents, 0.18, 0]}>
      {cycle.agents.map((a, i) => {
        const look = looks[a.slug];
        const v = cyc === undefined ? 1 : ramp(voteStart(i, n), voteStart(i, n) + 0.05, cyc);
        const pose = a.ok ? 'trade' : 'fail';
        const pop = v <= 0 ? 0 : easeOutBack(v, 2.2);
        voteMats[i].emissiveIntensity = 0.6 + 2.2 * bump(v);
        return (
          <group key={a.slug} position={[(i - (n - 1) / 2) * gap, 0, (i % 2) * 0.22 - 0.1]} rotation-y={0.35} scale={0.82}>
            {look && <Npc look={look} pose={pose} from={cyc === undefined ? undefined : 'think'} blend={v} t={t} phase={desync ? (hash(a.slug) % 1000) / 137 : 0} reduced={reduced} stand />}
            {pop > 0.001 &&
              (a.ok ? (
                <mesh material={voteMats[i]} geometry={unitBox} position={[0, 1.95 - (1 - v) * 0.3, 0]} scale={0.16 * pop} />
              ) : (
                [0.78, -0.78].map((r) => (
                  <mesh key={r} material={m.bad} geometry={unitBox} position={[0, 1.95 - (1 - v) * 0.3, 0]} rotation-z={r} scale={[0.26 * pop, 0.05 * pop, 0.05 * pop]} />
                ))
              ))}
          </group>
        );
      })}
    </group>
  );
}

/** Vote motes: each valid vote arcs from its agent into the formula core. */
function Motes({ cycle, cyc, m }: { cycle: PipelineCycle; cyc?: number; m: Mats }) {
  if (cyc === undefined) return null;
  const n = Math.max(1, cycle.agents.length);
  const pos = liveBookAgentPositions(n);
  const end = new THREE.Vector3(X.formula, 1.2, 0);
  return (
    <>
      {cycle.agents.map((a, i) => {
        if (!a.ok) return null;
        const s0 = Math.max(voteStart(i, n) + 0.035, CYCLE.toFormula[0]);
        const e = ramp(s0, Math.min(CYCLE.toFormula[1], s0 + 0.11), cyc);
        if (e <= 0 || e >= 1) return null;
        const k = easeInOutCubic(e);
        const p = new THREE.Vector3(...pos[i].vote).lerp(end, k);
        p.y += Math.sin(Math.PI * k) * 0.9;
        const s = 0.085 * (1 - ramp(0.82, 1, k)) * (0.6 + 0.4 * ramp(0, 0.1, k));
        return <mesh key={a.slug} material={m.mote} geometry={unitBox} position={p} rotation={[k * 4, k * 6, 0]} scale={s} />;
      })}
    </>
  );
}

// ---------------------------------------------------------------- 2. formula machine

function Formula({ cycle, t, cyc, reduced, m }: { cycle: PipelineCycle; t: number; cyc?: number; reduced: boolean; m: Mats }) {
  const win = useMemo(() => mat(C.violet, { emissive: C.violet2, emissiveIntensity: 1.2 }), []);
  useEffect(() => () => win.dispose(), [win]);
  const vals = BOTS.map((b) => cycle.nilai[b] ?? 0);
  const top = Math.max(1, ...vals.map((v) => Math.abs(v)));
  const k = reduced ? 0 : 1;
  const spin = cyc === undefined ? 0 : easeInOutCubic(ramp(CYCLE.formula[0], CYCLE.formula[1], cyc));
  const decided = cyc === undefined ? 1 : ramp(CYCLE.decide, CYCLE.decide + 0.035, cyc);
  // winner: lav3 -> violet with a flash when the formula decides
  win.color.set(C.lav3).lerp(new THREE.Color(C.violet), decided);
  win.emissive.set(C.violet2);
  win.emissiveIntensity = 1.2 * decided + 2.4 * bump(decided);
  const absorb = cyc === undefined ? 0 : bump(ramp(CYCLE.toFormula[0] + 0.05, CYCLE.formula[1], cyc));
  return (
    <group position={[X.formula, 0, 0]}>
      <mesh material={m.clay} position={[0, 0.45, 0]} castShadow>
        <cylinderGeometry args={[0.28, 0.36, 0.55, 24]} />
      </mesh>
      <RoundedBox args={[0.82, 0.82, 0.82]} radius={0.08} position={[0, 1.2, 0]} material={m.glass} />
      <mesh material={m.core} geometry={unitBox} position={[0, 1.2, 0]} scale={0.3 * (1 + k * Math.sin(t * 2.2) * 0.05 + 0.18 * absorb)} />
      <mesh material={m.ring} position={[0, 1.2, 0]} rotation-x={k * t * 0.7 + spin * TAU * 1.5}>
        <torusGeometry args={[0.62, 0.018, 8, 64]} />
      </mesh>
      <mesh material={m.ring} position={[0, 1.2, 0]} rotation={[Math.PI / 2, 0, k * t * 0.5 + spin * TAU]}>
        <torusGeometry args={[0.7, 0.014, 8, 64]} />
      </mesh>
      <group position={[0, 1.2, 0]} rotation-y={k * t * 0.35 + spin * TAU}>
        {BOTS.map((b, i) => {
          const a = (i / BOTS.length) * Math.PI * 2;
          const s = 0.07 + 0.13 * (Math.max(0, vals[i]) / top);
          const isWin = b === cycle.bot;
          return (
            <mesh
              key={b}
              material={isWin ? win : m.lose}
              geometry={unitBox}
              position={[Math.cos(a) * 0.98, Math.sin(a * 2) * 0.12, Math.sin(a) * 0.98]}
              scale={s * (isWin ? 1 + 0.55 * bump(decided) : 1)}
            />
          );
        })}
      </group>
    </group>
  );
}

// ---------------------------------------------------------------- 3. rule robot

function chestTexture(text: string) {
  const c = document.createElement('canvas');
  c.width = 512;
  c.height = 256;
  const g = c.getContext('2d')!;
  g.fillStyle = C.night;
  g.fillRect(0, 0, 512, 256);
  g.fillStyle = C.violet2;
  g.textAlign = 'center';
  const [a, ...rest] = text.split('-');
  const b = rest.join('-');
  g.font = `700 68px "${MONO}"`;
  g.fillText(a ?? '', 256, b ? 112 : 152);
  if (b) {
    g.font = `600 48px "${MONO}"`;
    g.fillText(b, 256, 192);
  }
  const t = new THREE.CanvasTexture(c);
  t.colorSpace = THREE.SRGBColorSpace;
  t.anisotropy = 8;
  return t;
}

function Robot({ bot, t, cyc, reduced, m }: { bot: string | null; t: number; cyc?: number; reduced: boolean; m: Mats }) {
  const tex = useMemo(() => ({ on: chestTexture(bot ?? '—'), off: chestTexture('—') }), [bot]);
  useEffect(() => () => (tex.on.dispose(), tex.off.dispose()), [tex]);
  const screen = useMemo(() => new THREE.MeshBasicMaterial({ toneMapped: false }), []);
  const tip = useMemo(() => mat(C.violet, { emissive: C.violet, emissiveIntensity: 1 }), []);
  useEffect(() => () => (screen.dispose(), tip.dispose()), [screen, tip]);
  const on = cyc === undefined ? 1 : ramp(CYCLE.robot[0], CYCLE.robot[0] + 0.03, cyc);
  const arm = cyc === undefined ? 1 : easeOutBack(ramp(CYCLE.robot[0] + 0.03, CYCLE.robot[1] - 0.02, cyc), 1.6);
  screen.map = on > 0 ? tex.on : tex.off; // both are textures: swapping needs no program rebuild
  screen.color.setScalar(on > 0 ? 0.55 + 0.45 * on + 0.6 * bump(on) : 0.55);
  tip.emissiveIntensity = (reduced ? 1 : 0.6 + Math.abs(Math.sin(t * 3)) * 0.8) + (cyc === undefined ? 0 : 2.5 * bump(ramp(CYCLE.robot[0] - 0.02, CYCLE.robot[0] + 0.06, cyc)));
  // right arm: hanging (mirror of the left arm) -> pointing at the book (the site's fixed pose)
  const armPos: Vec3 = [lerp(0.45, 0.52, arm), lerp(0.82, 0.98, arm), 0.05];
  const armRot = lerp(-0.15, -1.25, arm);
  return (
    <group position={[X.bot, 0.18, 0]} rotation-y={-0.15}>
      <group position-y={reduced ? 0 : Math.sin(t * 1.6) * 0.04}>
        {[-0.17, 0.17].map((x) => (
          <mesh key={x} material={m.joint} position={[x, 0.2, 0]} castShadow>
            <boxGeometry args={[0.16, 0.4, 0.18]} />
          </mesh>
        ))}
        <RoundedBox args={[0.74, 0.78, 0.5]} radius={0.08} position={[0, 0.8, 0]} material={m.clay} castShadow />
        <mesh position={[0, 0.82, 0.256]} material={screen}>
          <planeGeometry args={[0.52, 0.3]} />
        </mesh>
        <RoundedBox args={[0.58, 0.44, 0.46]} radius={0.08} position={[0, 1.45, 0]} material={m.clay} castShadow />
        <mesh material={m.ink} position={[0, 1.46, 0.235]}>
          <boxGeometry args={[0.46, 0.18, 0.02]} />
        </mesh>
        {[-0.1, 0.1].map((x) => (
          <mesh key={x} material={m.eye} position={[x, 1.46, 0.25]}>
            <boxGeometry args={[0.07, 0.05, 0.01]} />
          </mesh>
        ))}
        <mesh material={m.ink} position={[0, 1.75, 0]}>
          <cylinderGeometry args={[0.015, 0.015, 0.18, 8]} />
        </mesh>
        <mesh material={tip} position={[0, 1.86, 0]}>
          <sphereGeometry args={[0.05, 16, 16]} />
        </mesh>
        <mesh material={m.joint} position={[-0.45, 0.82, 0]} rotation-z={0.15} castShadow>
          <boxGeometry args={[0.14, 0.5, 0.14]} />
        </mesh>
        <mesh material={m.joint} position={armPos} rotation-z={armRot} castShadow>
          <boxGeometry args={[0.14, 0.5, 0.14]} />
        </mesh>
      </group>
    </group>
  );
}

// ---------------------------------------------------------------- 4. book

function Book({ cycle, cyc, m }: { cycle: PipelineCycle; cyc?: number; m: Mats }) {
  const rows = Object.entries(cycle.target)
    .sort((a, b) => Math.abs(b[1]) - Math.abs(a[1]))
    .slice(0, 8);
  const locked = rows.length ? 0 : Math.min(8, cycle.positions);
  const bars: { key: string; h: number; mat: THREE.Material; cap: boolean }[] = rows.length
    ? rows.map(([a, w]) => ({ key: a, h: 0.12 + Math.min(Math.abs(w), 0.25) * 5.2, mat: w >= 0 ? m.long : m.short, cap: false }))
    : Array.from({ length: locked }, (_, i) => ({ key: `slot${i}`, h: 0.62, mat: m.locked, cap: true }));
  return (
    <group position={[X.book, 0.18, 0]}>
      {bars.length === 0 && (
        <mesh material={m.flat} position={[0, 0.04, 0]}>
          <boxGeometry args={[1.2, 0.06, 0.6]} />
        </mesh>
      )}
      {bars.map((b, i) => {
        const g = cyc === undefined ? 1 : easeOutBack(ramp(CYCLE.book[0] + i * 0.025, CYCLE.book[0] + i * 0.025 + 0.09, cyc), 1.8);
        if (g <= 0.001) return null;
        const h = b.h * g;
        const x = ((i % 4) - 1.5) * 0.4;
        const z = i < 4 ? -0.25 : 0.3;
        return (
          <group key={b.key} position={[x, 0, z]}>
            <mesh material={b.mat} geometry={unitBox} position={[0, h / 2, 0]} scale={[0.26, Math.max(0.001, h), 0.26]} castShadow />
            {b.cap && <mesh material={m.cap} geometry={unitBox} position={[0, h + 0.012, 0]} scale={[0.27, 0.025, 0.27]} />}
          </group>
        );
      })}
    </group>
  );
}

// ---------------------------------------------------------------- 5. BNB Chain stack

function Chain({ sealed, cyc, m }: { sealed: boolean; cyc?: number; m: Mats }) {
  const top = useMemo(() => mat(C.violet, { emissive: C.violet, emissiveIntensity: 0.55, roughness: 0.4 }), []);
  useEffect(() => () => top.dispose(), [top]);
  const fall = cyc === undefined ? 1 : ramp(CYCLE.chain[0], CYCLE.chain[0] + 0.05, cyc);
  const landed = cyc === undefined ? 1 : ramp(CYCLE.chain[0] + 0.05, CYCLE.chain[1], cyc);
  const lit = sealed && landed > 0;
  top.color.set(lit ? C.violet : C.lav3);
  top.emissive.set(lit ? C.violet : '#000000');
  top.emissiveIntensity = lit ? 0.55 + 2.2 * (1 - easeInOutCubic(landed)) : 0;
  const yOff = cyc === undefined ? 0 : 1.5 * (1 - fall * fall);
  const squash = cyc === undefined ? 0 : 0.28 * bump(ramp(CYCLE.chain[0] + 0.05, CYCLE.chain[0] + 0.085, cyc));
  const visible = cyc === undefined || cyc >= CYCLE.chain[0];
  return (
    <group position={[X.chain, 0.18, 0]}>
      {[0, 1, 2].map((i) => (
        <RoundedBox key={i} args={[0.62, 0.16, 0.62]} radius={0.03} position={[0, 0.1 + i * 0.19, 0]} material={m.base} castShadow />
      ))}
      {visible && (
        <group position={[0, 0.1 + 3 * 0.19 + yOff - squash * 0.08, 0]} scale={[1 + squash * 0.5, 1 - squash, 1 + squash * 0.5]}>
          <RoundedBox args={[0.62, 0.16, 0.62]} radius={0.03} material={top} castShadow />
        </group>
      )}
    </group>
  );
}

// ---------------------------------------------------------------- wires + pulse left -> right

const SEGS: [number, number][] = ORDER.slice(0, -1).map((k, i) => [X[k] + PAD[k] / 2, X[ORDER[i + 1]] - PAD[ORDER[i + 1]] / 2]);
const TRANSIT = [CYCLE.toFormula, CYCLE.toBot, CYCLE.toBook, CYCLE.toChain];

function Flow({ t, cyc, reduced, m }: { t: number; cyc?: number; reduced: boolean; m: Mats }) {
  const total = SEGS.reduce((s, [a, b]) => s + (b - a), 0);
  let dot: { x: number; s: number } | null = null;
  if (!reduced) {
    if (cyc === undefined) {
      // site idle: one dot loops the whole line every 1 / 0.12 s
      let d = ((t * 0.12) % 1) * total;
      for (const [a, b] of SEGS) {
        if (d <= b - a) {
          dot = { x: a + d, s: 1 };
          break;
        }
        d -= b - a;
      }
    } else {
      TRANSIT.forEach(([w0, w1], j) => {
        const u = ramp(w0, w1, cyc);
        if (u > 0 && u < 1) dot = { x: lerp(SEGS[j][0], SEGS[j][1], easeInOutCubic(u)), s: 1.8 * Math.min(1, u * 8, (1 - u) * 8) };
      });
    }
  }
  const d = dot as { x: number; s: number } | null;
  return (
    <group>
      {SEGS.map(([a, b]) => (
        <mesh key={a} material={m.wire} position={[(a + b) / 2, 0.12, 0]} rotation-z={Math.PI / 2}>
          <cylinderGeometry args={[0.022, 0.022, b - a, 8]} />
        </mesh>
      ))}
      {d && d.s > 0.01 && (
        <mesh material={m.dot} position={[d.x, 0.12, 0]} scale={d.s}>
          <sphereGeometry args={[0.07, 16, 16]} />
        </mesh>
      )}
    </group>
  );
}

// ---------------------------------------------------------------- labels (the site's DOM tags, in 3D)

export function liveBookLabels(cycle: PipelineCycle, cyc?: number): Record<Station, TagSpec> {
  const n = cycle.agents.length;
  const valid = cycle.agents.filter((a, i) => a.ok && (cyc === undefined || cyc >= voteStart(i, n) + 0.03)).length;
  const after = (x: number) => cyc === undefined || cyc >= x;
  const bot = cycle.bot ?? 'locked';
  const score = cycle.score !== null ? ` ${cycle.score >= 0 ? '+' : ''}${cycle.score.toFixed(1)}` : '';
  const hidden = !Object.keys(cycle.target).length && cycle.positions > 0;
  const book = cycle.positions ? `${cycle.positions} positions${hidden ? ' · locked' : ''}` : 'flat';
  const mono = (text: string, color?: string) => ({ lines: [{ text, color }] });
  return {
    agents: mono(`Agents · ${valid}/${n} valid`),
    formula: { dark: true, lines: [{ text: `Formula ${cycle.rumus} · ${after(CYCLE.decide) ? bot + score : '…'}`, color: C.violet2 }] },
    bot: mono(`Bot rule · ${after(CYCLE.robot[0]) ? bot : '…'}`),
    book: mono(`Book · ${after(CYCLE.book[0] + 0.05) ? book : '…'}`),
    chain: mono(`BNB Chain · ${after(CYCLE.chain[0] + 0.05) ? (cycle.sealed ? 'sealed ✓' : 'not sealed') : '…'}`, cycle.sealed && after(CYCLE.chain[0] + 0.05) ? C.violet : undefined),
  };
}

// ---------------------------------------------------------------- scene

export type LiveBookProps = {
  /** seconds since the shot started (idle motion: orbit, robot bob, typing) */
  t: number;
  /** 0..1 one cycle as a story; undefined = the site's steady state */
  cycleT?: number;
  /** default DEFAULT_CYCLE (live public cycle + newest revealed winner); LIVE_CYCLE / REVEALED_CYCLE also exported */
  cycle?: PipelineCycle;
  looks?: Record<string, Look>;
  /** draw the site's labels as in-3D tags (needs fonts; LiveBookScene loads them) */
  labels?: boolean;
  /** label size in multiples of the site's CSS pixels */
  labelScale?: number;
  /** 0..1 fade for all labels */
  labelOpacity?: number;
  reduced?: boolean;
  /** offset each agent's idle motion (the site moves them in lockstep) */
  desync?: boolean;
  shadowMapSize?: number;
};

/** Lights + environment + content, for use inside your own <Stage>. */
export const LiveBookWorld: React.FC<LiveBookProps> = ({
  t,
  cycleT,
  cycle = DEFAULT_CYCLE,
  looks,
  labels = false,
  labelScale = 2,
  labelOpacity = 1,
  reduced = false,
  desync = true,
  shadowMapSize = 2048,
}) => {
  const m = useMaterials();
  const lk = useMemo(() => looks ?? deskLooks(), [looks]);
  const cyc = cycleT === undefined ? undefined : clamp01(cycleT);
  const tags = labels ? liveBookLabels(cycle, cyc) : null;
  return (
    <>
      <hemisphereLight args={['#ffffff', C.lav2, 1.25]} />
      <ambientLight intensity={0.35} />
      <directionalLight
        position={[4, 10, 8]}
        intensity={1.4}
        castShadow
        shadow-mapSize={[shadowMapSize, shadowMapSize]}
        shadow-camera-left={-10}
        shadow-camera-right={10}
        shadow-camera-top={5}
        shadow-camera-bottom={-5}
        shadow-bias={-0.0004}
      />
      <Environment resolution={128} frames={1}>
        <Lightformer form="rect" intensity={1.6} position={[0, 6, -3]} scale={[12, 5, 1]} color="#ffffff" />
      </Environment>
      <Pad x={X.agents} w={PAD.agents} m={m} />
      <Pad x={X.formula} w={PAD.formula} round m={m} />
      <Pad x={X.bot} w={PAD.bot} m={m} />
      <Pad x={X.book} w={PAD.book} m={m} />
      <Pad x={X.chain} w={PAD.chain} round m={m} />
      <Flow t={t} cyc={cyc} reduced={reduced} m={m} />
      <Agents cycle={cycle} looks={lk} t={t} cyc={cyc} reduced={reduced} desync={desync} m={m} />
      <Motes cycle={cycle} cyc={cyc} m={m} />
      <Formula cycle={cycle} t={t} cyc={cyc} reduced={reduced} m={m} />
      <Robot bot={cycle.bot} t={t} cyc={cyc} reduced={reduced} m={m} />
      <Book cycle={cycle} cyc={cyc} m={m} />
      <Chain sealed={cycle.sealed} cyc={cyc} m={m} />
      {tags && ORDER.map((k) => <Tag3D key={k} spec={tags[k]} position={LIVEBOOK_ANCHORS[k].label} scale={labelScale} opacity={labelOpacity} />)}
    </>
  );
};

export type LiveBookSceneProps = LiveBookProps & {
  cam?: CameraDesc;
  /** default transparent (the site draws this canvas over the panel's lav -> white gradient, DESK_BACKDROP_CSS) */
  background?: Background;
  fog?: FogDesc | false | null;
};

export const LiveBookScene: React.FC<LiveBookSceneProps> = ({ cam, background = 'transparent', fog = null, ...rest }) => (
  <Stage cam={cam ?? liveBookSiteCam()} background={background} fog={fog} toneMapping="neutral" exposure={1.08} shadows fonts>
    <LiveBookWorld {...rest} />
  </Stage>
);
