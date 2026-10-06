"use client";

// Bagian 3D bersama lantai trading + strip pipeline Live Book (P158/P164): palet Fabius, material clay, NPC kotak-kotak. NPC yang SAMA dipakai
// duduk di meja kerja (lantai) dan berdiri di platform agent (Live Book), supaya satu agent selalu terlihat sebagai satu pekerja yang sama.

import { useFrame } from "@react-three/fiber";
import { useMemo, useRef } from "react";
import * as THREE from "three";
import type { Look, Pose } from "./model";

export const C = { clay: "#fbfaff", lav: "#ece8fa", lav2: "#ddd5f6", lav3: "#c9bdf2", ink: "#15122b", night: "#1a1442", violet: "#6e4bff", violet2: "#9d86ff", mist: "#8b86a6", gap: "#ff5a6e" };

export function mat(color: string, extra: Partial<THREE.MeshStandardMaterialParameters> = {}) {
  return new THREE.MeshStandardMaterial({ color, roughness: 0.82, metalness: 0, ...extra });
}

// ---------------------------------------------------------------- NPC kotak-kotak (gaya Minecraft), duduk menghadap +z lokal

export function faceTexture(skin: string, hair: string) {
  const c = document.createElement("canvas");
  c.width = c.height = 8;
  const g = c.getContext("2d")!;
  g.fillStyle = skin;
  g.fillRect(0, 0, 8, 8);
  g.fillStyle = hair;
  g.fillRect(0, 0, 8, 2);
  g.fillStyle = C.ink;
  g.fillRect(2, 4, 1, 1);
  g.fillRect(5, 4, 1, 1);
  g.fillStyle = "rgba(21,18,43,0.35)";
  g.fillRect(3, 6, 2, 1);
  const t = new THREE.CanvasTexture(c);
  t.magFilter = THREE.NearestFilter;
  t.minFilter = THREE.NearestFilter;
  t.colorSpace = THREE.SRGBColorSpace;
  return t;
}

export function Npc({ look, pose, reduced, stand = false }: { look: Look; pose: Pose; reduced: boolean; stand?: boolean }) {
  const torso = useRef<THREE.Group>(null!);
  const head = useRef<THREE.Group>(null!);
  const armL = useRef<THREE.Group>(null!);
  const armR = useRef<THREE.Group>(null!);
  const m = useMemo(() => {
    const face = faceTexture(look.skin, look.hair);
    const skin = mat(look.skin);
    const hair = mat(look.hair);
    return {
      shirt: mat(look.shirt),
      pants: mat("#2a2140"),
      shoe: mat(C.ink),
      skin,
      hair,
      acc: mat(C.ink, { roughness: 0.5 }),
      knit: mat(look.shirt === C.lav3 ? C.violet : C.lav3),
      mic: mat(C.violet, { emissive: C.violet, emissiveIntensity: 0.6 }),
      // urutan sisi BoxGeometry: +x, -x, +y, -y, +z (wajah), -z (belakang kepala)
      head: [skin, skin, hair, skin, new THREE.MeshStandardMaterial({ map: face, roughness: 0.85 }), hair],
    };
  }, [look]);
  useFrame(({ clock }) => {
    const t = clock.elapsedTime;
    const k = reduced ? 0 : 1;
    const P: Record<Pose, { lean: number; arm: number; amp: number; spd: number }> = {
      trade: { lean: 0.1, arm: -1.22, amp: 0.13, spd: 22 },
      think: { lean: 0.05, arm: -1.18, amp: 0.06, spd: 7 },
      hold: { lean: -0.12, arm: -0.95, amp: 0.02, spd: 2 },
      flat: { lean: -0.18, arm: -0.55, amp: 0.0, spd: 1 },
      fail: { lean: 0.55, arm: -1.45, amp: 0.0, spd: 1 },
    };
    // berdiri (strip pipeline Live Book): lengan menggantung, bukan mengetik; gagal = membungkuk, berpikir = tangan ke dagu
    const S: Record<Pose, { lean: number; arm: number; amp: number; spd: number }> = {
      trade: { lean: 0.04, arm: -0.35, amp: 0.1, spd: 6 },
      think: { lean: 0.02, arm: 0.05, amp: 0.03, spd: 2 },
      hold: { lean: 0, arm: 0.06, amp: 0.05, spd: 1.6 },
      flat: { lean: 0, arm: 0.06, amp: 0.04, spd: 1.2 },
      fail: { lean: 0.28, arm: 0.12, amp: 0, spd: 1 },
    };
    const p = (stand ? S : P)[pose];
    torso.current.rotation.x = THREE.MathUtils.lerp(torso.current.rotation.x, p.lean + k * Math.sin(t * 1.6) * 0.012, 0.12);
    armL.current.rotation.x = THREE.MathUtils.lerp(armL.current.rotation.x, p.arm + k * Math.sin(t * p.spd) * p.amp, 0.3);
    armR.current.rotation.x = THREE.MathUtils.lerp(armR.current.rotation.x, (stand && pose === "think" ? -1.95 : p.arm) + k * Math.sin(t * p.spd + Math.PI) * p.amp, 0.3);
    head.current.rotation.x = THREE.MathUtils.lerp(head.current.rotation.x, pose === "fail" ? 0.45 : pose === "hold" ? k * Math.sin(t * 1.3) * 0.05 : 0.08, 0.1);
    head.current.rotation.y = THREE.MathUtils.lerp(head.current.rotation.y, pose === "flat" ? k * Math.sin(t * 0.6) * 0.45 : pose === "think" ? k * Math.sin(t * 1.4) * 0.12 : 0, 0.08);
  });
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
      <group ref={torso} position={stand ? [0, 0.68, 0] : [0, 0.6, -0.08]}>
        <mesh material={m.shirt} position={[0, 0.27, 0]} castShadow>
          <boxGeometry args={[0.44, 0.54, 0.24]} />
        </mesh>
        <group ref={head} position={[0, 0.54, 0]}>
          <mesh material={m.head} position={[0, 0.2, 0]} castShadow>
            <boxGeometry args={[0.4, 0.4, 0.4]} />
          </mesh>
          <mesh material={m.hair} position={[0, 0.42, -0.02]} castShadow>
            <boxGeometry args={[0.42, 0.06, 0.44]} />
          </mesh>
          {look.extra === "headset" && (
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
          {look.extra === "cap" && (
            <>
              <mesh material={m.acc} position={[0, 0.45, 0]}>
                <boxGeometry args={[0.44, 0.1, 0.44]} />
              </mesh>
              <mesh material={m.acc} position={[0, 0.41, 0.29]}>
                <boxGeometry args={[0.42, 0.03, 0.2]} />
              </mesh>
            </>
          )}
          {look.extra === "glasses" && (
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
          {look.extra === "beanie" && (
            <>
              <mesh material={m.knit} position={[0, 0.44, -0.01]}>
                <boxGeometry args={[0.44, 0.16, 0.44]} />
              </mesh>
              <mesh material={m.knit} position={[0, 0.55, -0.01]}>
                <boxGeometry args={[0.1, 0.06, 0.1]} />
              </mesh>
            </>
          )}
          {look.extra === "hood" && (
            <mesh material={m.shirt} position={[0, 0.12, -0.24]} castShadow>
              <boxGeometry args={[0.46, 0.3, 0.1]} />
            </mesh>
          )}
        </group>
        {[
          [armL, -0.29],
          [armR, 0.29],
        ].map(([ref, x]) => (
          <group key={x as number} ref={ref as React.RefObject<THREE.Group>} position={[x as number, 0.5, 0]}>
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
}
