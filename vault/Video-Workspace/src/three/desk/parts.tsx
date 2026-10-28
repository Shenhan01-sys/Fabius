// Port of web/src/components/desk/floor/parts.tsx: clay materials and the boxy NPC worker (same geometry, colours and accessories).
// Change: no useFrame. The pose is a pure function of `t` (seconds). The site eases every joint toward its target with a per-frame lerp;
// smoothedSin() reproduces that filter's steady-state amplitude and lag, so the motion matches the site without carrying state.

import React, { useMemo } from 'react';
import * as THREE from 'three';
import { C } from '../palette';
import { lerp, smoothedSin } from '../util';
import type { Look, Pose } from './model';

export { C };

export function mat(color: string, extra: Partial<THREE.MeshStandardMaterialParameters> = {}) {
  return new THREE.MeshStandardMaterial({ color, roughness: 0.82, metalness: 0, ...extra });
}

const faces = new Map<string, THREE.CanvasTexture>();

/** 8x8 pixel face (skin, hair band, two eyes, mouth), nearest-filtered. Cached per skin/hair pair. */
export function faceTexture(skin: string, hair: string) {
  const key = `${skin}|${hair}`;
  const hit = faces.get(key);
  if (hit) return hit;
  const c = document.createElement('canvas');
  c.width = c.height = 8;
  const g = c.getContext('2d')!;
  g.fillStyle = skin;
  g.fillRect(0, 0, 8, 8);
  g.fillStyle = hair;
  g.fillRect(0, 0, 8, 2);
  g.fillStyle = C.ink;
  g.fillRect(2, 4, 1, 1);
  g.fillRect(5, 4, 1, 1);
  g.fillStyle = 'rgba(21,18,43,0.35)';
  g.fillRect(3, 6, 2, 1);
  const t = new THREE.CanvasTexture(c);
  t.magFilter = THREE.NearestFilter;
  t.minFilter = THREE.NearestFilter;
  t.generateMipmaps = false;
  t.colorSpace = THREE.SRGBColorSpace;
  faces.set(key, t);
  return t;
}

type PoseParams = { lean: number; arm: number; amp: number; spd: number };
// seated at a desk (the floor)
const SEATED: Record<Pose, PoseParams> = {
  trade: { lean: 0.1, arm: -1.22, amp: 0.13, spd: 22 },
  think: { lean: 0.05, arm: -1.18, amp: 0.06, spd: 7 },
  hold: { lean: -0.12, arm: -0.95, amp: 0.02, spd: 2 },
  flat: { lean: -0.18, arm: -0.55, amp: 0.0, spd: 1 },
  fail: { lean: 0.55, arm: -1.45, amp: 0.0, spd: 1 },
};
// standing (Live Book agents platform)
const STANDING: Record<Pose, PoseParams> = {
  trade: { lean: 0.04, arm: -0.35, amp: 0.1, spd: 6 },
  think: { lean: 0.02, arm: 0.05, amp: 0.03, spd: 2 },
  hold: { lean: 0, arm: 0.06, amp: 0.05, spd: 1.6 },
  flat: { lean: 0, arm: 0.06, amp: 0.04, spd: 1.2 },
  fail: { lean: 0.28, arm: 0.12, amp: 0, spd: 1 },
};

export type Joints = { torso: number; armL: number; armR: number; headX: number; headY: number };

export function npcJoints(pose: Pose, t: number, stand: boolean, reduced = false): Joints {
  const k = reduced ? 0 : 1;
  const p = (stand ? STANDING : SEATED)[pose];
  return {
    torso: p.lean + k * smoothedSin(t, 1.6, 0.12) * 0.012,
    armL: p.arm + k * smoothedSin(t, p.spd, 0.3) * p.amp,
    armR: (stand && pose === 'think' ? -1.95 : p.arm) + k * smoothedSin(t, p.spd, 0.3, Math.PI) * p.amp,
    headX: pose === 'fail' ? 0.45 : pose === 'hold' ? k * smoothedSin(t, 1.3, 0.1) * 0.05 : 0.08,
    headY: pose === 'flat' ? k * smoothedSin(t, 0.6, 0.08) * 0.45 : pose === 'think' ? k * smoothedSin(t, 1.4, 0.08) * 0.12 : 0,
  };
}

export type NpcProps = {
  look: Look;
  pose: Pose;
  /** seconds */
  t: number;
  stand?: boolean;
  reduced?: boolean;
  /** time offset so a row of workers does not move in lockstep (the site shares one clock; 0 = identical to the site) */
  phase?: number;
  /** blend from another pose (0 = `from`, 1 = `pose`) for deterministic pose changes */
  from?: Pose;
  blend?: number;
};

export const Npc: React.FC<NpcProps> = ({ look, pose, t, stand = false, reduced = false, phase = 0, from, blend = 1 }) => {
  const m = useMemo(() => {
    const face = faceTexture(look.skin, look.hair);
    const skin = mat(look.skin);
    const hair = mat(look.hair);
    return {
      shirt: mat(look.shirt),
      pants: mat('#2a2140'),
      shoe: mat(C.ink),
      skin,
      hair,
      acc: mat(C.ink, { roughness: 0.5 }),
      knit: mat(look.shirt === C.lav3 ? C.violet : C.lav3),
      mic: mat(C.violet, { emissive: C.violet, emissiveIntensity: 0.6 }),
      // BoxGeometry face order: +x, -x, +y, -y, +z (face), -z (back of the head)
      head: [skin, skin, hair, skin, new THREE.MeshStandardMaterial({ map: face, roughness: 0.85 }), hair],
    };
  }, [look]);
  const tt = t + phase;
  const a = npcJoints(pose, tt, stand, reduced);
  const j = from && blend < 1 ? npcJoints(from, tt, stand, reduced) : a;
  const k = from && blend < 1 ? Math.max(0, blend) : 1;
  const J: Joints = {
    torso: lerp(j.torso, a.torso, k),
    armL: lerp(j.armL, a.armL, k),
    armR: lerp(j.armR, a.armR, k),
    headX: lerp(j.headX, a.headX, k),
    headY: lerp(j.headY, a.headY, k),
  };
  return (
    <group>
      {[-0.1, 0.1].map((x) =>
        stand ? (
          <group key={x}>
            <mesh material={m.pants} position={[x, 0.37, 0]} castShadow>
              <boxGeometry args={[0.17, 0.62, 0.17]} />
            </mesh>
            <mesh material={m.shoe} position={[x, 0.04, 0.04]} castShadow>
              <boxGeometry args={[0.18, 0.08, 0.25]} />
            </mesh>
          </group>
        ) : (
          <group key={x}>
            <mesh material={m.pants} position={[x, 0.58, 0.12]} castShadow>
              <boxGeometry args={[0.17, 0.17, 0.42]} />
            </mesh>
            <mesh material={m.pants} position={[x, 0.34, 0.33]} castShadow>
              <boxGeometry args={[0.17, 0.46, 0.17]} />
            </mesh>
            <mesh material={m.shoe} position={[x, 0.06, 0.37]} castShadow>
              <boxGeometry args={[0.18, 0.08, 0.25]} />
            </mesh>
          </group>
        ),
      )}
      <group position={stand ? [0, 0.68, 0] : [0, 0.6, -0.08]} rotation-x={J.torso}>
        <mesh material={m.shirt} position={[0, 0.27, 0]} castShadow>
          <boxGeometry args={[0.44, 0.54, 0.24]} />
        </mesh>
        <group position={[0, 0.54, 0]} rotation={[J.headX, J.headY, 0]}>
          <mesh material={m.head} position={[0, 0.2, 0]} castShadow>
            <boxGeometry args={[0.4, 0.4, 0.4]} />
          </mesh>
          <mesh material={m.hair} position={[0, 0.42, -0.02]} castShadow>
            <boxGeometry args={[0.42, 0.06, 0.44]} />
          </mesh>
          {look.extra === 'headset' && (
            <>
              <mesh material={m.acc} position={[0, 0.47, 0]}>
                <boxGeometry args={[0.46, 0.04, 0.07]} />
              </mesh>
              {[-0.22, 0.22].map((x) => (
                <mesh key={x} material={m.acc} position={[x, 0.2, 0]}>
                  <boxGeometry args={[0.07, 0.15, 0.13]} />
                </mesh>
              ))}
              <mesh material={m.mic} position={[0.2, 0.08, 0.16]}>
                <boxGeometry args={[0.03, 0.03, 0.14]} />
              </mesh>
            </>
          )}
          {look.extra === 'cap' && (
            <>
              <mesh material={m.acc} position={[0, 0.45, 0]}>
                <boxGeometry args={[0.44, 0.1, 0.44]} />
              </mesh>
              <mesh material={m.acc} position={[0, 0.41, 0.29]}>
                <boxGeometry args={[0.42, 0.03, 0.2]} />
              </mesh>
            </>
          )}
          {look.extra === 'glasses' && (
            <>
              {[-0.09, 0.09].map((x) => (
                <mesh key={x} material={m.acc} position={[x, 0.22, 0.205]}>
                  <boxGeometry args={[0.12, 0.07, 0.02]} />
                </mesh>
              ))}
              {[-0.205, 0.205].map((x) => (
                <mesh key={x} material={m.acc} position={[x, 0.23, 0.1]}>
                  <boxGeometry args={[0.02, 0.025, 0.22]} />
                </mesh>
              ))}
            </>
          )}
          {look.extra === 'beanie' && (
            <>
              <mesh material={m.knit} position={[0, 0.44, -0.01]}>
                <boxGeometry args={[0.44, 0.16, 0.44]} />
              </mesh>
              <mesh material={m.knit} position={[0, 0.55, -0.01]}>
                <boxGeometry args={[0.1, 0.06, 0.1]} />
              </mesh>
            </>
          )}
          {look.extra === 'hood' && (
            <mesh material={m.shirt} position={[0, 0.12, -0.24]} castShadow>
              <boxGeometry args={[0.46, 0.3, 0.1]} />
            </mesh>
          )}
        </group>
        {(
          [
            [J.armL, -0.29],
            [J.armR, 0.29],
          ] as const
        ).map(([rot, x]) => (
          <group key={x} position={[x, 0.5, 0]} rotation-x={rot}>
            <mesh material={m.shirt} position={[0, -0.2, 0]} castShadow>
              <boxGeometry args={[0.14, 0.44, 0.14]} />
            </mesh>
            <mesh material={m.skin} position={[0, -0.47, 0]} castShadow>
              <boxGeometry args={[0.13, 0.12, 0.13]} />
            </mesh>
          </group>
        ))}
      </group>
    </group>
  );
};
