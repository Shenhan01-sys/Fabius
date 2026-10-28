// Port of web/src/components/desk/floor/Scene.tsx (P158, the trading floor on /desk): white clay diorama with violet light lines. Each agent =
// a voxel worker at its own desk (monitor shows its equity curve), the Fabius hub in the middle, the 12-block BNB Chain tower behind.
// Same geometry, lights, materials and layout maths. Changes: no useFrame (all motion from `t`), perspective camera from props
// (`floorSiteCam()` = the site's isometric orthographic framing as a telephoto), the pointer tilt becomes `lean`, the data refresh "beat"
// becomes `beats` (times at which a new cycle lands: pulses run down the wires, a block drops onto the tower), optional `thinkUntilBeat`.

import { Environment, Lightformer, RoundedBox } from '@react-three/drei';
import React, { useEffect, useMemo } from 'react';
import * as THREE from 'three';
import { telephoto, type CameraDesc } from '../camera';
import { deskCycles, deskHub, deskSeats } from '../snapshot';
import { SANS } from '../fonts';
import { Tag3D, type TagSpec } from '../labels';
import { C } from '../palette';
import { Stage, type Background, type FogDesc } from '../Stage';
import { clamp01, hash, ramp, type Lean, type Vec3 } from '../util';
import { fmtPct, glyph, poseWord, type Pose, type Seat } from './model';
import { mat, Npc } from './parts';
import type { Buku, Siklus } from './types';

export const TOWER: Vec3 = [-2.75, 0, -2.75];

/** The site's framing (orthographic from (10, 10, 10) looking at (0, 0.35, 0), zoom fits 11.2 x 8.0) as a 4 deg telephoto. */
export function floorSiteCam(aspect = 16 / 9, fov = 4): CameraDesc {
  return telephoto({ position: [10, 10, 10], target: [0, 0.35, 0], fov: 30 }, Math.max(8.0, 11.2 / aspect), fov);
}

// ---------------------------------------------------------------- anchors

const local = (seat: Seat, p: Vec3, tilt: number): Vec3 => {
  const c = Math.cos(seat.rotY), s = Math.sin(seat.rotY);
  const x = seat.pos[0] + (p[0] * c + p[2] * s) * seat.scale;
  const z = seat.pos[2] + (-p[0] * s + p[2] * c) * seat.scale;
  const y = seat.pos[1] + p[1] * seat.scale;
  return tiltY([x, y, z], tilt);
};
const tiltY = (p: Vec3, a: number): Vec3 => (a ? [p[0] * Math.cos(a) + p[2] * Math.sin(a), p[1], -p[0] * Math.sin(a) + p[2] * Math.cos(a)] : p);

/**
 * World position of a point given in a desk's local frame (worker faces +z, monitor at z 0.84, seated head ~ (0, 1.34, -0.08); +x is the
 * worker's left). Use it to aim cameras at anything on a desk.
 */
export const seatToWorld = (seat: Seat, p: Vec3, lean?: Lean): Vec3 => local(seat, p, (lean?.x ?? 0) * 0.035);

export type FloorAnchors = {
  seats: Record<string, { label: Vec3; screen: Vec3; head: Vec3; desk: Vec3 }>;
  hub: { label: Vec3; core: Vec3 };
  tower: { label: Vec3; top: Vec3; base: Vec3 };
};

/** World anchors (labels as the site pins them, plus camera targets: each worker's head and monitor, hub core, tower top). */
export function floorAnchors(seats: Seat[] = deskSeats(), cycles = 12, lean?: Lean): FloorAnchors {
  const tilt = (lean?.x ?? 0) * 0.035;
  const n = Math.min(12, cycles);
  return {
    seats: Object.fromEntries(
      seats.map((s) => [
        s.slug,
        { label: local(s, [0, 2.12, 0.1], tilt), screen: local(s, [0, 1.18, 0.812], tilt), head: local(s, [0, 1.34, -0.08], tilt), desk: local(s, [0, 0.76, 0.55], tilt) },
      ]),
    ),
    hub: { label: tiltY([0, 1.62, 0], tilt), core: tiltY([0, 0.98, 0], tilt) },
    tower: { label: tiltY([TOWER[0], 0.45 + n * 0.125, TOWER[2]], tilt), top: tiltY([TOWER[0], 0.21 + (n - 1) * 0.125, TOWER[2]], tilt), base: tiltY(TOWER, tilt) },
  };
}

// ---------------------------------------------------------------- monitor texture (equity curve), drawn once per book

function screenTexture(b: Buku, pose: Pose) {
  const S = 3; // 3x the site's 320 x 192 bitmap: the video gets close to these screens
  const c = document.createElement('canvas');
  c.width = 320 * S;
  c.height = 192 * S;
  const g = c.getContext('2d')!;
  g.scale(S, S);
  g.fillStyle = C.night;
  g.fillRect(0, 0, 320, 192);
  g.fillStyle = 'rgba(110,75,255,0.18)';
  g.fillRect(0, 0, 320, 6);
  g.fillStyle = pose === 'fail' ? C.gap : C.violet2;
  g.font = `600 22px "${SANS}"`;
  g.fillText(`${b.ekuitas.toLocaleString('en-US', { maximumFractionDigits: 0 })} USDT`, 16, 36);
  g.fillStyle = b.hasil_pct >= 0 ? '#b9a6ff' : '#a8a3c4';
  g.font = `500 18px "${SANS}"`;
  g.fillText(fmtPct(b.hasil_pct), 16, 62);
  const pts = b.deret.map((p) => p[1]);
  if (pts.length > 1) {
    const lo = Math.min(...pts), hi = Math.max(...pts), span = hi - lo || 1;
    g.strokeStyle = '#b9a6ff';
    g.lineWidth = 6;
    g.lineJoin = 'round';
    g.beginPath();
    pts.forEach((v, i) => {
      const x = 16 + (i / (pts.length - 1)) * 288;
      const y = 176 - ((v - lo) / span) * 100;
      if (i) g.lineTo(x, y);
      else g.moveTo(x, y);
    });
    g.stroke();
  }
  g.fillStyle = 'rgba(157,134,255,0.25)';
  g.fillRect(16, 178, 288, 2);
  const t = new THREE.CanvasTexture(c);
  t.colorSpace = THREE.SRGBColorSpace;
  t.anisotropy = 8;
  return t;
}

// ---------------------------------------------------------------- one desk

function Desk({ seat, pose, from, blend, t, reduced, desync }: { seat: Seat; pose: Pose; from?: Pose; blend: number; t: number; reduced: boolean; desync: boolean }) {
  const m = useMemo(
    () => ({
      base: mat(C.lav),
      top: mat(C.clay),
      leg: mat(C.lav2),
      ink: mat(C.ink, { roughness: 0.45 }),
      key: mat(C.lav),
      chair: mat(seat.trial ? C.lav2 : C.lav3),
      paper: mat('#ffffff'),
      mug: mat(C.violet),
      leaf: mat(C.violet2),
    }),
    [seat.trial],
  );
  const screen = useMemo(() => {
    const tex = screenTexture(seat.main, pose);
    // polygon offset: the screen sits 3 mm in front of the monitor body; keep it on top at any camera distance
    return new THREE.MeshBasicMaterial({ map: tex, toneMapped: false, polygonOffset: true, polygonOffsetFactor: -2, polygonOffsetUnits: -2 });
  }, [seat.main, pose]);
  useEffect(() => () => (screen.map?.dispose(), screen.dispose()), [screen]);
  const phase = desync ? (hash(seat.slug) % 1000) / 137 : 0;
  // monitor glow on the face: flickers while trading, dim when failed
  const base = pose === 'fail' ? 0.15 : 0.7;
  const k = pose === 'trade' && !reduced ? 0.55 + 0.45 * Math.abs(Math.sin((t + phase) * 5)) : 1;
  return (
    <group position={seat.pos} rotation-y={seat.rotY} scale={seat.scale}>
      <RoundedBox args={[2.0, 0.08, 1.9]} radius={0.04} position={[0, 0.04, 0.3]} material={m.base} receiveShadow />
      <RoundedBox args={[1.5, 0.06, 0.72]} radius={0.025} position={[0, 0.74, 0.55]} material={m.top} castShadow receiveShadow />
      {(
        [
          [-0.68, 0.27],
          [0.68, 0.27],
          [-0.68, 0.83],
          [0.68, 0.83],
        ] as const
      ).map(([x, z]) => (
        <mesh key={`${x}${z}`} material={m.leg} position={[x, 0.36, z]} castShadow>
          <boxGeometry args={[0.06, 0.66, 0.06]} />
        </mesh>
      ))}
      <RoundedBox args={[0.86, 0.54, 0.05]} radius={0.02} position={[0, 1.18, 0.84]} material={m.ink} castShadow />
      <mesh position={[0, 1.18, 0.812]} rotation-y={Math.PI} material={screen}>
        <planeGeometry args={[0.78, 0.46]} />
      </mesh>
      <mesh material={m.ink} position={[0, 0.93, 0.87]}>
        <boxGeometry args={[0.07, 0.34, 0.05]} />
      </mesh>
      <mesh material={m.ink} position={[0, 0.785, 0.86]}>
        <boxGeometry args={[0.3, 0.02, 0.18]} />
      </mesh>
      <pointLight position={[0, 1.15, 0.6]} color={pose === 'fail' ? C.gap : C.violet2} distance={1.6} decay={1.5} intensity={base * k * 1.6} />
      <RoundedBox args={[0.58, 0.03, 0.18]} radius={0.01} position={[0, 0.785, 0.42]} material={m.key} castShadow />
      <mesh material={m.key} position={[0.42, 0.785, 0.44]}>
        <boxGeometry args={[0.07, 0.03, 0.11]} />
      </mesh>
      {seat.look.prop === 'paper' && (
        <group position={[-0.5, 0.776, 0.55]} rotation-y={0.35}>
          <mesh material={m.paper}>
            <boxGeometry args={[0.34, 0.012, 0.26]} />
          </mesh>
          {[-0.07, -0.02, 0.03, 0.08].map((z) => (
            <mesh key={z} material={m.ink} position={[0, 0.008, z]}>
              <boxGeometry args={[0.26, 0.002, 0.012]} />
            </mesh>
          ))}
        </group>
      )}
      {seat.look.prop === 'mug' && (
        <mesh material={m.mug} position={[-0.55, 0.83, 0.62]} castShadow>
          <cylinderGeometry args={[0.045, 0.045, 0.11, 16]} />
        </mesh>
      )}
      {seat.look.prop === 'plant' && (
        <group position={[-0.58, 0.77, 0.66]}>
          <mesh material={m.top} position={[0, 0.05, 0]} castShadow>
            <cylinderGeometry args={[0.06, 0.05, 0.1, 12]} />
          </mesh>
          {(
            [
              [0, 0.16, 0, 0.09],
              [0.05, 0.22, 0.02, 0.07],
              [-0.04, 0.24, -0.02, 0.06],
            ] as const
          ).map(([x, y, z, r]) => (
            <mesh key={`${x}${y}`} material={m.leaf} position={[x, y, z]} castShadow>
              <boxGeometry args={[r, r, r]} />
            </mesh>
          ))}
        </group>
      )}
      {seat.look.prop === 'books' && (
        <group position={[-0.55, 0.77, 0.62]} rotation-y={0.2}>
          {[C.violet, C.lav3, C.ink].map((c, i) => (
            <mesh key={c} material={i === 0 ? m.mug : i === 1 ? m.chair : m.ink} position={[0, 0.02 + i * 0.04, 0]} castShadow>
              <boxGeometry args={[0.24 - i * 0.02, 0.035, 0.17]} />
            </mesh>
          ))}
        </group>
      )}
      <RoundedBox args={[0.52, 0.07, 0.5]} radius={0.025} position={[0, 0.46, -0.05]} material={m.chair} castShadow />
      <RoundedBox args={[0.52, 0.56, 0.07]} radius={0.025} position={[0, 0.8, -0.3]} material={m.chair} castShadow />
      <mesh material={m.ink} position={[0, 0.23, -0.05]}>
        <cylinderGeometry args={[0.035, 0.035, 0.4, 10]} />
      </mesh>
      <mesh material={m.ink} position={[0, 0.1, -0.05]}>
        <cylinderGeometry args={[0.24, 0.24, 0.03, 20]} />
      </mesh>
      <Npc look={seat.look} pose={pose} from={from} blend={blend} t={t} phase={phase} reduced={reduced} />
    </group>
  );
}

// ---------------------------------------------------------------- hub

function Hub({ t, reduced }: { t: number; reduced: boolean }) {
  const m = useMemo(
    () => ({
      ring: mat(C.violet, { emissive: C.violet, emissiveIntensity: 1.4 }),
      clay: mat(C.clay),
      lav: mat(C.lav),
      core: new THREE.MeshStandardMaterial({ color: C.violet2, emissive: C.violet, emissiveIntensity: 0.55, roughness: 0.35 }),
    }),
    [],
  );
  m.ring.emissiveIntensity = reduced ? 1.4 : 1.1 + Math.sin(t * 2) * 0.4;
  return (
    <group>
      <mesh material={m.clay} position={[0, 0.11, 0]} castShadow receiveShadow>
        <cylinderGeometry args={[1.05, 1.1, 0.22, 64]} />
      </mesh>
      <mesh material={m.lav} position={[0, 0.225, 0]} receiveShadow>
        <cylinderGeometry args={[0.82, 0.82, 0.015, 64]} />
      </mesh>
      <mesh material={m.ring} position={[0, 0.235, 0]} rotation-x={Math.PI / 2}>
        <torusGeometry args={[0.86, 0.035, 12, 96]} />
      </mesh>
      <mesh material={m.clay} position={[0, 0.45, 0]} castShadow>
        <cylinderGeometry args={[0.16, 0.22, 0.44, 24]} />
      </mesh>
      <RoundedBox
        args={[0.36, 0.36, 0.36]}
        radius={0.05}
        position={[0, reduced ? 0.98 : 0.98 + Math.sin(t * 1.2) * 0.04, 0]}
        rotation-y={reduced ? 0 : t * 0.4}
        material={m.core}
        castShadow
      />
    </group>
  );
}

// ---------------------------------------------------------------- tower (12 cycles)

function Tower({ cycles, drop }: { cycles: Siklus[]; drop: number }) {
  const m = useMemo(() => ({ lit: mat(C.violet, { emissive: C.violet, emissiveIntensity: 0.55, roughness: 0.4 }), dim: mat(C.lav2), clay: mat(C.clay) }), []);
  const list = cycles.slice(-12);
  return (
    <group position={TOWER}>
      <RoundedBox args={[0.95, 0.14, 0.95]} radius={0.04} position={[0, 0.07, 0]} material={m.clay} castShadow receiveShadow />
      {list.map((c, i) => (
        <group key={c.siklus} position={[0, 0.21 + i * 0.125 + (i === list.length - 1 ? drop * drop * 0.9 : 0), 0]}>
          <RoundedBox args={[0.62, 0.1, 0.62]} radius={0.025} material={c.status === 'dikomit' ? m.lit : m.dim} castShadow />
        </group>
      ))}
    </group>
  );
}

// ---------------------------------------------------------------- floor wires + pulses

function Wire({ from, to, t, burst, delay, reduced, dim }: { from: Vec3; to: Vec3; t: number; burst: number | null; delay: number; reduced: boolean; dim: boolean }) {
  const { curve, geo } = useMemo(() => {
    const a = new THREE.Vector3(...from);
    const b = new THREE.Vector3(...to);
    const mid = a.clone().lerp(b, 0.5);
    const side = new THREE.Vector3(-(b.z - a.z), 0, b.x - a.x).normalize().multiplyScalar(0.35);
    const curve = new THREE.CatmullRomCurve3([a, mid.add(side), b]);
    return { curve, geo: new THREE.TubeGeometry(curve, 48, 0.022, 6, false) };
  }, [from[0], from[1], from[2], to[0], to[1], to[2]]); // eslint-disable-line react-hooks/exhaustive-deps
  const m = useMemo(
    () => ({
      line: new THREE.MeshBasicMaterial({ color: dim ? C.lav3 : C.violet2, transparent: true, opacity: dim ? 0.35 : 0.75, toneMapped: false }),
      dot: new THREE.MeshBasicMaterial({ color: '#ffffff', toneMapped: false }),
    }),
    [dim],
  );
  let dot: { u: number; s: number } | null = null;
  if (!reduced && !dim) {
    if (burst !== null && burst - delay <= 0.9) dot = { u: clamp01((burst - delay) / 0.9), s: 2.2 };
    else dot = { u: (((t * 0.22 + delay * 0.37) % 1) + 1) % 1, s: 1 };
  }
  return (
    <group>
      <mesh geometry={geo} material={m.line} />
      {dot && (
        <mesh material={m.dot} position={curve.getPointAt(dot.u)} scale={dot.s}>
          <sphereGeometry args={[0.055, 12, 12]} />
        </mesh>
      )}
    </group>
  );
}

function FloorDisc() {
  const m = useMemo(() => ({ clay: mat(C.clay), lav2: mat(C.lav2), ring: new THREE.MeshBasicMaterial({ color: C.violet2, transparent: true, opacity: 0.85, toneMapped: false }) }), []);
  return (
    <group>
      <mesh material={m.clay} position={[0, -0.15, 0]} receiveShadow>
        <cylinderGeometry args={[5.4, 5.4, 0.3, 128]} />
      </mesh>
      <mesh material={m.lav2} position={[0, -0.33, 0]}>
        <cylinderGeometry args={[5.46, 5.5, 0.08, 128]} />
      </mesh>
      <mesh material={m.ring} position={[0, 0.003, 0]} rotation-x={Math.PI / 2}>
        <torusGeometry args={[5.32, 0.02, 8, 160]} />
      </mesh>
    </group>
  );
}

// ---------------------------------------------------------------- labels

export function floorLabels(seats: Seat[], hub: Buku | undefined, cycles: Siklus[], poseOf: (s: Seat) => Pose): { seats: Record<string, TagSpec>; hub: TagSpec | null; tower: TagSpec | null } {
  const sub = (s: Seat, p: Pose) => {
    const word = p === 'fail' && s.main.status_terakhir === 'terlambat' ? 'late' : poseWord[p];
    return `${glyph[p]} ${word}${p === 'trade' && s.main.isi_terakhir ? ` · ${s.main.isi_terakhir} fills` : ''} · ${fmtPct(s.main.hasil_pct)}`;
  };
  const nInstr = hub?.keputusan_terakhir?.instrumen?.length ?? hub?.n_posisi ?? Object.keys(hub?.posisi ?? {}).length;
  const hubLine = !hub ? '-' : nInstr ? `${hub.keputusan_terakhir?.bot ?? 'consensus'} on ${nInstr} instruments` : 'flat';
  const nOk = cycles.filter((c) => c.status === 'dikomit').length;
  return {
    seats: Object.fromEntries(
      seats.map((s) => {
        const p = poseOf(s);
        const badge = `${s.trial ? ' · TRIAL' : ''}${s.luar ? ' · EXTERNAL' : ''}`;
        return [
          s.slug,
          {
            padX: 10,
            padY: 4,
            radius: 12,
            lines: [
              { text: `${s.nama}${badge}`, font: 'sans', size: 11, weight: 500, color: C.ink },
              { text: sub(s, p), size: 10, color: p === 'fail' ? C.gap : p === 'trade' ? C.violet : 'rgba(21,18,43,0.55)' },
            ],
          } satisfies TagSpec,
        ];
      }),
    ),
    hub: hub
      ? {
          dark: true,
          padX: 12,
          padY: 6,
          radius: 12,
          lines: [
            { text: 'Fabius', font: 'sans', size: 11, weight: 500, color: '#ffffff' },
            { text: `${hubLine} · ${fmtPct(hub.hasil_pct)}`, size: 10, color: C.violet2 },
          ],
        }
      : null,
    tower: cycles.length ? { lines: [{ text: `BNB Chain · ${nOk}/${cycles.length} anchored` }] } : null,
  };
}

// ---------------------------------------------------------------- scene

export type FloorProps = {
  /** seconds since the shot started */
  t: number;
  /** default: the snapshot's seats one minute into the last cycle (deskSeats()) */
  seats?: Seat[];
  hub?: Buku;
  cycles?: Siklus[];
  /** times (seconds, same clock as t) when a new cycle lands: wire pulses + tower drop (the site does this on each data refresh) */
  beats?: number[];
  /** workers show "thinking" until the first beat, then blend into their recorded pose (a new cycle arriving) */
  thinkUntilBeat?: boolean;
  /** the site's pointer tilt: lean.x -1..1 turns the diorama +-0.035 rad */
  lean?: Lean;
  labels?: boolean;
  labelScale?: number;
  /** 0..1 fade for all labels */
  labelOpacity?: number;
  reduced?: boolean;
  desync?: boolean;
  shadowMapSize?: number;
};

export const FloorWorld: React.FC<FloorProps> = ({
  t,
  seats,
  hub,
  cycles,
  beats = [],
  thinkUntilBeat = false,
  lean,
  labels = false,
  labelScale = 2,
  labelOpacity = 1,
  reduced = false,
  desync = true,
  shadowMapSize = 2048,
}) => {
  const st = useMemo(() => seats ?? deskSeats(), [seats]);
  const hb = hub ?? deskHub();
  const cy = useMemo(() => cycles ?? deskCycles(), [cycles]);
  const last = beats.filter((b) => b <= t).sort((a, b) => b - a)[0];
  const burst = last === undefined ? null : t - last;
  const drop = burst === null ? 0 : Math.max(0, 1 - burst * 1.4);
  const firstBeat = beats.length ? Math.min(...beats) : undefined;
  const poseBlend = !thinkUntilBeat || firstBeat === undefined ? 1 : ramp(firstBeat, firstBeat + 0.45, t);
  const wires = useMemo(() => {
    const hubEdge = (p: Vec3): Vec3 => {
      const l = Math.hypot(p[0], p[2]) || 1;
      return [(p[0] / l) * 1.12, 0.012, (p[2] / l) * 1.12];
    };
    const out = st.map((s, i) => ({ from: [s.pos[0] * 0.62, 0.012, s.pos[2] * 0.62] as Vec3, to: hubEdge(s.pos), delay: i * 0.25, dim: s.trial }));
    out.push({ from: hubEdge(TOWER), to: [TOWER[0] * 0.83, 0.012, TOWER[2] * 0.83], delay: 1.1, dim: false });
    return out;
  }, [st]);
  const tilt = reduced ? 0 : (lean?.x ?? 0) * 0.035;
  const tags = labels ? floorLabels(st, hb, cy, (s) => (poseBlend < 0.5 ? 'think' : s.pose)) : null;
  const anchors = labels ? floorAnchors(st, cy.length, lean) : null;
  return (
    <>
      <hemisphereLight args={['#ffffff', C.lav2, 1.25]} />
      <ambientLight intensity={0.35} />
      <directionalLight
        position={[6, 12, 4]}
        intensity={1.5}
        castShadow
        shadow-mapSize={[shadowMapSize, shadowMapSize]}
        shadow-camera-left={-8}
        shadow-camera-right={8}
        shadow-camera-top={8}
        shadow-camera-bottom={-8}
        shadow-bias={-0.0004}
      />
      <Environment resolution={128} frames={1}>
        <Lightformer form="rect" intensity={1.6} position={[0, 6, -3]} scale={[12, 5, 1]} color="#ffffff" />
        <Lightformer form="rect" intensity={1.1} position={[-6, 2, 2]} rotation-y={Math.PI / 2} scale={[8, 3, 1]} color="#d8ccff" />
      </Environment>
      <group rotation-y={tilt}>
        <FloorDisc />
        {wires.map((w, i) => (
          <Wire key={i} from={w.from} to={w.to} t={t} burst={burst} delay={w.delay} reduced={reduced} dim={w.dim} />
        ))}
        <Hub t={t} reduced={reduced} />
        <Tower cycles={cy} drop={reduced ? 0 : drop} />
        {st.map((s) => (
          <Desk key={s.slug} seat={s} pose={s.pose} from={poseBlend < 1 ? 'think' : undefined} blend={poseBlend} t={t} reduced={reduced} desync={desync} />
        ))}
      </group>
      {tags && anchors && (
        <>
          {st.map((s) => (
            <Tag3D key={s.slug} spec={tags.seats[s.slug]} position={anchors.seats[s.slug].label} scale={labelScale} opacity={labelOpacity} />
          ))}
          {tags.hub && <Tag3D spec={tags.hub} position={anchors.hub.label} scale={labelScale} opacity={labelOpacity} />}
          {tags.tower && <Tag3D spec={tags.tower} position={anchors.tower.label} scale={labelScale} opacity={labelOpacity} />}
        </>
      )}
    </>
  );
};

export type FloorSceneProps = FloorProps & { cam?: CameraDesc; background?: Background; fog?: FogDesc | false | null };

export const FloorScene: React.FC<FloorSceneProps> = ({ cam, background = 'transparent', fog = null, ...rest }) => (
  <Stage cam={cam ?? floorSiteCam()} background={background} fog={fog} toneMapping="neutral" exposure={1.08} shadows fonts>
    <FloorWorld {...rest} />
  </Stage>
);
