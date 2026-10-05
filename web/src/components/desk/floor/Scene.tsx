"use client";

// Lantai trading 3D (P158, docs/design/desk.md). Diorama isometrik clay putih + garis cahaya violet: tiap agent = NPC kotak-kotak di meja kerja
// (monitor menampilkan kurva ekuitasnya), hub Fabius di tengah, menara 12 blok BNB Chain di belakang. Kamera ortografis TETAP (tanpa zoom/orbit);
// zoom dihitung dari ukuran kontainer supaya seluruh diorama selalu muat satu bingkai. Label = tombol DOM biasa di Floor (satu root React,
// terbaca pembaca layar); posisinya disinkronkan ke titik jangkar 3D tiap frame lewat ref (`Bridge`), tanpa render ulang.

import { Canvas, useFrame, useThree } from "@react-three/fiber";
import { Environment, Lightformer, RoundedBox } from "@react-three/drei";
import { useEffect, useLayoutEffect, useMemo, useRef, useState } from "react";
import * as THREE from "three";
import type { Buku, Siklus } from "@/lib/desk";
import type { Bridge } from "./bridge";
import { fmtPct, type Look, type Pose, type Seat } from "./model";

export type Rect = { x: number; y: number; w: number; h: number };
type Open = (name: string, rect: Rect) => void;

const C = { clay: "#fbfaff", lav: "#ece8fa", lav2: "#ddd5f6", lav3: "#c9bdf2", ink: "#15122b", night: "#1a1442", violet: "#6e4bff", violet2: "#9d86ff", mist: "#8b86a6", gap: "#ff5a6e" };
const W = 11.2; // lebar adegan terproyeksi (satuan dunia) - dipakai menghitung zoom supaya muat
const H = 8.0;
const TOWER: [number, number, number] = [-2.75, 0, -2.75];

function mat(color: string, extra: Partial<THREE.MeshStandardMaterialParameters> = {}) {
  return new THREE.MeshStandardMaterial({ color, roughness: 0.82, metalness: 0, ...extra });
}

function projectRect(obj: THREE.Object3D, hw: number, hh: number, camera: THREE.Camera, size: { width: number; height: number }): Rect {
  const pts = [
    [-hw, -hh],
    [hw, -hh],
    [hw, hh],
    [-hw, hh],
  ].map(([x, y]) => new THREE.Vector3(x, y, 0).applyMatrix4(obj.matrixWorld).project(camera));
  const xs = pts.map((p) => ((p.x + 1) / 2) * size.width);
  const ys = pts.map((p) => ((1 - p.y) / 2) * size.height);
  const x = Math.min(...xs), y = Math.min(...ys);
  return { x, y, w: Math.max(...xs) - x, h: Math.max(...ys) - y };
}

// ---------------------------------------------------------------- kamera tetap yang selalu memuat seluruh diorama

function Fit() {
  const get = useThree((s) => s.get);
  const width = useThree((s) => s.size.width);
  const height = useThree((s) => s.size.height);
  useLayoutEffect(() => {
    const cam = get().camera as THREE.OrthographicCamera;
    cam.position.set(10, 10, 10);
    cam.zoom = Math.min(width / W, height / H);
    cam.lookAt(0, 0.35, 0);
    cam.updateProjectionMatrix();
  }, [get, width, height]);
  return null;
}

function LabelSync({ bridge }: { bridge: Bridge }) {
  useFrame(({ camera, size }) => bridge.sync(camera, size.width, size.height));
  return null;
}

// ---------------------------------------------------------------- monitor: kurva ekuitas 24 jam di layar (CanvasTexture)

function Screen({ b, pose, screenRef }: { b: Buku; pose: Pose; screenRef: React.RefObject<THREE.Mesh> }) {
  const [cv] = useState(() => {
    const c = document.createElement("canvas");
    c.width = 320;
    c.height = 192;
    return c;
  });
  const [tex] = useState(() => {
    const t = new THREE.CanvasTexture(cv);
    t.colorSpace = THREE.SRGBColorSpace;
    t.anisotropy = 4;
    return t;
  });
  const screenMat = useRef<THREE.MeshBasicMaterial>(null);
  useEffect(() => {
    const g = cv.getContext("2d")!;
    g.fillStyle = C.night;
    g.fillRect(0, 0, 320, 192);
    g.fillStyle = "rgba(110,75,255,0.18)";
    g.fillRect(0, 0, 320, 6);
    g.fillStyle = pose === "fail" ? C.gap : C.violet2;
    g.font = "600 22px Inter, system-ui, sans-serif";
    g.fillText(`${b.ekuitas.toLocaleString("en-US", { maximumFractionDigits: 0 })} USDT`, 16, 36);
    g.fillStyle = b.hasil_pct >= 0 ? "#b9a6ff" : "#a8a3c4";
    g.font = "500 18px Inter, system-ui, sans-serif";
    g.fillText(fmtPct(b.hasil_pct), 16, 62);
    const pts = b.deret.map((p) => p[1]);
    if (pts.length > 1) {
      const lo = Math.min(...pts), hi = Math.max(...pts), span = hi - lo || 1;
      g.strokeStyle = "#b9a6ff";
      g.lineWidth = 6;
      g.beginPath();
      pts.forEach((v, i) => {
        const x = 16 + (i / (pts.length - 1)) * 288;
        const y = 176 - ((v - lo) / span) * 100;
        if (i) g.lineTo(x, y);
        else g.moveTo(x, y);
      });
      g.stroke();
    }
    g.fillStyle = "rgba(157,134,255,0.25)";
    g.fillRect(16, 178, 288, 2);
    if (screenMat.current?.map) screenMat.current.map.needsUpdate = true;
  }, [b, pose, cv]);
  return (
    <mesh ref={screenRef} position={[0, 1.18, 0.812]} rotation-y={Math.PI}>
      <planeGeometry args={[0.78, 0.46]} />
      <meshBasicMaterial ref={screenMat} map={tex} toneMapped={false} />
    </mesh>
  );
}

// ---------------------------------------------------------------- NPC kotak-kotak (gaya Minecraft), duduk menghadap +z lokal

function faceTexture(skin: string, hair: string) {
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

function Npc({ look, pose, reduced }: { look: Look; pose: Pose; reduced: boolean }) {
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
    const p = P[pose];
    torso.current.rotation.x = THREE.MathUtils.lerp(torso.current.rotation.x, p.lean + k * Math.sin(t * 1.6) * 0.012, 0.12);
    armL.current.rotation.x = THREE.MathUtils.lerp(armL.current.rotation.x, p.arm + k * Math.sin(t * p.spd) * p.amp, 0.3);
    armR.current.rotation.x = THREE.MathUtils.lerp(armR.current.rotation.x, p.arm + k * Math.sin(t * p.spd + Math.PI) * p.amp, 0.3);
    head.current.rotation.x = THREE.MathUtils.lerp(head.current.rotation.x, pose === "fail" ? 0.45 : pose === "hold" ? k * Math.sin(t * 1.3) * 0.05 : 0.08, 0.1);
    head.current.rotation.y = THREE.MathUtils.lerp(head.current.rotation.y, pose === "flat" ? k * Math.sin(t * 0.6) * 0.45 : pose === "think" ? k * Math.sin(t * 1.4) * 0.12 : 0, 0.08);
  });
  return (
    <group>
      {[-0.1, 0.1].map((x) => (
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
      ))}
      <group ref={torso} position={[0, 0.6, -0.08]}>
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

// ---------------------------------------------------------------- satu meja kerja

function Desk({ seat, bridge, onOpen, reduced }: { seat: Seat; bridge: Bridge; onOpen: Open; reduced: boolean }) {
  const screen = useRef<THREE.Mesh>(null!);
  const glow = useRef<THREE.PointLight>(null!);
  const { camera, size } = useThree();
  const [hover, setHover] = useState(false);
  const m = useMemo(
    () => ({ base: mat(C.lav), top: mat(C.clay), leg: mat(C.lav2), ink: mat(C.ink, { roughness: 0.45 }), key: mat(C.lav), chair: mat(seat.trial ? C.lav2 : C.lav3), paper: mat("#ffffff"), mug: mat(C.violet), leaf: mat(C.violet2) }),
    [seat.trial],
  );
  const open = () => onOpen(seat.main.agent, projectRect(screen.current, 0.39, 0.23, camera, size));
  useEffect(() => {
    bridge.setOpen(seat.slug, open);
    return () => bridge.setOpen(seat.slug, null);
  });
  useFrame(({ clock }) => {
    // cahaya monitor ke wajah: berkedip saat bertransaksi, redup saat gagal
    const base = seat.pose === "fail" ? 0.15 : 0.7;
    const k = seat.pose === "trade" && !reduced ? 0.55 + 0.45 * Math.abs(Math.sin(clock.elapsedTime * 5)) : 1;
    glow.current.intensity = base * k * 1.6;
  });
  return (
    <group position={seat.pos} rotation-y={seat.rotY} scale={seat.scale * (hover ? 1.04 : 1)}>
      <group
        onClick={(e) => {
          e.stopPropagation();
          open();
        }}
        onPointerOver={(e) => {
          e.stopPropagation();
          setHover(true);
          document.body.style.cursor = "pointer";
        }}
        onPointerOut={() => {
          setHover(false);
          document.body.style.cursor = "";
        }}
      >
        {/* alas meja (pulau kecil, seperti slab referensi) */}
        <RoundedBox args={[2.0, 0.08, 1.9]} radius={0.04} position={[0, 0.04, 0.3]} material={m.base} receiveShadow />
        <RoundedBox args={[1.5, 0.06, 0.72]} radius={0.025} position={[0, 0.74, 0.55]} material={m.top} castShadow receiveShadow />
        {[
          [-0.68, 0.27],
          [0.68, 0.27],
          [-0.68, 0.83],
          [0.68, 0.83],
        ].map(([x, z]) => (
          <mesh key={`${x}${z}`} material={m.leg} position={[x, 0.36, z]} castShadow>
            <boxGeometry args={[0.06, 0.66, 0.06]} />
          </mesh>
        ))}
        {/* monitor: layar menghadap NPC (-z lokal) = menghadap kamera */}
        <RoundedBox args={[0.86, 0.54, 0.05]} radius={0.02} position={[0, 1.18, 0.84]} material={m.ink} castShadow />
        <Screen b={seat.main} pose={seat.pose} screenRef={screen} />
        <mesh material={m.ink} position={[0, 0.93, 0.87]}>
          <boxGeometry args={[0.07, 0.34, 0.05]} />
        </mesh>
        <mesh material={m.ink} position={[0, 0.785, 0.86]}>
          <boxGeometry args={[0.3, 0.02, 0.18]} />
        </mesh>
        <pointLight ref={glow} position={[0, 1.15, 0.6]} color={seat.pose === "fail" ? C.gap : C.violet2} distance={1.6} decay={1.5} />
        {/* keyboard + mouse */}
        <RoundedBox args={[0.58, 0.03, 0.18]} radius={0.01} position={[0, 0.785, 0.42]} material={m.key} castShadow />
        <mesh material={m.key} position={[0.42, 0.785, 0.44]}>
          <boxGeometry args={[0.07, 0.03, 0.11]} />
        </mesh>
        {seat.look.prop === "paper" && (
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
        {seat.look.prop === "mug" && (
          <mesh material={m.mug} position={[-0.55, 0.83, 0.62]} castShadow>
            <cylinderGeometry args={[0.045, 0.045, 0.11, 16]} />
          </mesh>
        )}
        {seat.look.prop === "plant" && (
          <group position={[-0.58, 0.77, 0.66]}>
            <mesh material={m.top} position={[0, 0.05, 0]} castShadow>
              <cylinderGeometry args={[0.06, 0.05, 0.1, 12]} />
            </mesh>
            {[
              [0, 0.16, 0, 0.09],
              [0.05, 0.22, 0.02, 0.07],
              [-0.04, 0.24, -0.02, 0.06],
            ].map(([x, y, z, r]) => (
              <mesh key={`${x}${y}`} material={m.leaf} position={[x, y, z]} castShadow>
                <boxGeometry args={[r, r, r]} />
              </mesh>
            ))}
          </group>
        )}
        {seat.look.prop === "books" && (
          <group position={[-0.55, 0.77, 0.62]} rotation-y={0.2}>
            {[C.violet, C.lav3, C.ink].map((c, i) => (
              <mesh key={c} material={i === 0 ? m.mug : i === 1 ? m.chair : m.ink} position={[0, 0.02 + i * 0.04, 0]} castShadow>
                <boxGeometry args={[0.24 - i * 0.02, 0.035, 0.17]} />
              </mesh>
            ))}
          </group>
        )}
        {/* kursi */}
        <RoundedBox args={[0.52, 0.07, 0.5]} radius={0.025} position={[0, 0.46, -0.05]} material={m.chair} castShadow />
        <RoundedBox args={[0.52, 0.56, 0.07]} radius={0.025} position={[0, 0.8, -0.3]} material={m.chair} castShadow />
        <mesh material={m.ink} position={[0, 0.23, -0.05]}>
          <cylinderGeometry args={[0.035, 0.035, 0.4, 10]} />
        </mesh>
        <mesh material={m.ink} position={[0, 0.1, -0.05]}>
          <cylinderGeometry args={[0.24, 0.24, 0.03, 20]} />
        </mesh>
        <Npc look={seat.look} pose={seat.pose} reduced={reduced} />
      </group>
      <group ref={bridge.anchor(seat.slug)} position={[0, 2.12, 0.1]} />
    </group>
  );
}

// ---------------------------------------------------------------- hub Fabius (putusan rumus terkunci)

function Hub({ book, bridge, onOpen, reduced }: { book?: Buku; bridge: Bridge; onOpen: Open; reduced: boolean }) {
  const ring = useRef<THREE.Mesh>(null!);
  const core = useRef<THREE.Mesh>(null!);
  const { camera, size } = useThree();
  const ringMat = useMemo(() => mat(C.violet, { emissive: C.violet, emissiveIntensity: 1.4 }), []);
  const hm = useMemo(() => ({ clay: mat(C.clay), lav: mat(C.lav) }), []);
  useFrame(({ clock }) => {
    const t = clock.elapsedTime;
    if (!reduced) {
      core.current.rotation.y = t * 0.4;
      core.current.position.y = 0.98 + Math.sin(t * 1.2) * 0.04;
    }
    (ring.current.material as THREE.MeshStandardMaterial).emissiveIntensity = reduced ? 1.4 : 1.1 + Math.sin(t * 2) * 0.4;
  });
  const open = () => book && onOpen(book.agent, projectRect(core.current, 0.25, 0.25, camera, size));
  useEffect(() => {
    bridge.setOpen("hub", () => void open());
    return () => bridge.setOpen("hub", null);
  });
  return (
    <group>
      <group onClick={(e) => (e.stopPropagation(), open())}>
        <mesh material={hm.clay} position={[0, 0.11, 0]} castShadow receiveShadow>
          <cylinderGeometry args={[1.05, 1.1, 0.22, 64]} />
        </mesh>
        <mesh material={hm.lav} position={[0, 0.225, 0]} receiveShadow>
          <cylinderGeometry args={[0.82, 0.82, 0.015, 64]} />
        </mesh>
        <mesh ref={ring} material={ringMat} position={[0, 0.235, 0]} rotation-x={Math.PI / 2}>
          <torusGeometry args={[0.86, 0.035, 12, 96]} />
        </mesh>
        <mesh material={hm.clay} position={[0, 0.45, 0]} castShadow>
          <cylinderGeometry args={[0.16, 0.22, 0.44, 24]} />
        </mesh>
        <RoundedBox ref={core} args={[0.36, 0.36, 0.36]} radius={0.05} position={[0, 0.98, 0]} castShadow>
          <meshStandardMaterial color={C.violet2} emissive={C.violet} emissiveIntensity={0.55} roughness={0.35} />
        </RoundedBox>
      </group>
      <group ref={bridge.anchor("hub")} position={[0, 1.62, 0]} />
    </group>
  );
}

// ---------------------------------------------------------------- menara 12 blok BNB Chain (siklus dikomit)

function Tower({ cycles, bridge, beat, reduced }: { cycles: Siklus[]; bridge: Bridge; beat: number; reduced: boolean }) {
  const top = useRef<THREE.Group>(null!);
  const drop = useRef(0);
  const first = useRef(true);
  useEffect(() => {
    if (first.current) {
      first.current = false;
      return;
    }
    drop.current = reduced ? 0 : 1;
  }, [beat, reduced]);
  useFrame((_, dt) => {
    drop.current = Math.max(0, drop.current - dt * 1.4);
    if (top.current) top.current.position.y = drop.current * drop.current * 0.9;
  });
  const lit = useMemo(() => mat(C.violet, { emissive: C.violet, emissiveIntensity: 0.55, roughness: 0.4 }), []);
  const dim = useMemo(() => mat(C.lav2), []);
  const clay = useMemo(() => mat(C.clay), []);
  const list = cycles.slice(-12);
  return (
    <group position={TOWER}>
      <RoundedBox args={[0.95, 0.14, 0.95]} radius={0.04} position={[0, 0.07, 0]} material={clay} castShadow receiveShadow />
      {list.map((c, i) => {
        const block = <RoundedBox args={[0.62, 0.1, 0.62]} radius={0.025} material={c.status === "dikomit" ? lit : dim} castShadow />;
        return i === list.length - 1 ? (
          <group key={c.siklus} ref={top}>
            <group position={[0, 0.21 + i * 0.125, 0]}>{block}</group>
          </group>
        ) : (
          <group key={c.siklus} position={[0, 0.21 + i * 0.125, 0]}>
            {block}
          </group>
        );
      })}
      <group ref={bridge.anchor("tower")} position={[0, 0.45 + list.length * 0.125, 0]} />
    </group>
  );
}

// ---------------------------------------------------------------- garis cahaya di lantai + denyut

function Wire({ from, to, beat, delay, reduced, dim = false }: { from: THREE.Vector3; to: THREE.Vector3; beat: number; delay: number; reduced: boolean; dim?: boolean }) {
  const dot = useRef<THREE.Mesh>(null!);
  const burst = useRef(-1);
  const first = useRef(true);
  const curve = useMemo(() => {
    const mid = from.clone().lerp(to, 0.5);
    const side = new THREE.Vector3(-(to.z - from.z), 0, to.x - from.x).normalize().multiplyScalar(0.35);
    return new THREE.CatmullRomCurve3([from, mid.add(side), to]);
  }, [from, to]);
  const geo = useMemo(() => new THREE.TubeGeometry(curve, 48, 0.022, 6, false), [curve]);
  useEffect(() => {
    if (first.current) {
      first.current = false;
      return;
    }
    burst.current = 0;
  }, [beat]);
  useFrame(({ clock }, dt) => {
    if (reduced || dim) {
      dot.current.visible = false; // kursi uji: suaranya belum mengalir ke hub
      return;
    }
    let u: number;
    let s = 1;
    if (burst.current >= 0) {
      burst.current += dt;
      u = Math.min(1, Math.max(0, (burst.current - delay) / 0.9));
      s = 2.2;
      if (burst.current - delay > 0.9) burst.current = -1;
    } else u = ((clock.elapsedTime * 0.22 + delay * 0.37) % 1 + 1) % 1;
    dot.current.position.copy(curve.getPointAt(u));
    dot.current.scale.setScalar(s);
    dot.current.visible = true;
  });
  return (
    <group>
      <mesh geometry={geo}>
        <meshBasicMaterial color={dim ? C.lav3 : C.violet2} transparent opacity={dim ? 0.35 : 0.75} toneMapped={false} />
      </mesh>
      <mesh ref={dot}>
        <sphereGeometry args={[0.055, 12, 12]} />
        <meshBasicMaterial color="#ffffff" toneMapped={false} />
      </mesh>
    </group>
  );
}

// ---------------------------------------------------------------- adegan

function Floor() {
  const fm = useMemo(() => ({ clay: mat(C.clay), lav2: mat(C.lav2) }), []);
  return (
    <group>
      <mesh material={fm.clay} position={[0, -0.15, 0]} receiveShadow>
        <cylinderGeometry args={[5.4, 5.4, 0.3, 128]} />
      </mesh>
      <mesh material={fm.lav2} position={[0, -0.33, 0]}>
        <cylinderGeometry args={[5.46, 5.5, 0.08, 128]} />
      </mesh>
      <mesh position={[0, 0.003, 0]} rotation-x={Math.PI / 2}>
        <torusGeometry args={[5.32, 0.02, 8, 160]} />
        <meshBasicMaterial color={C.violet2} transparent opacity={0.85} toneMapped={false} />
      </mesh>
    </group>
  );
}

function Tilt({ children, reduced }: { children: React.ReactNode; reduced: boolean }) {
  const g = useRef<THREE.Group>(null!);
  useFrame(({ pointer }) => {
    if (reduced) return;
    g.current.rotation.y = THREE.MathUtils.lerp(g.current.rotation.y, pointer.x * 0.035, 0.05);
  });
  return <group ref={g}>{children}</group>;
}

export default function Scene({
  seats,
  hub,
  cycles,
  beat,
  bridge,
  onOpen,
  active,
  reduced,
}: {
  seats: Seat[];
  hub?: Buku;
  cycles: Siklus[];
  beat: number;
  bridge: Bridge;
  onOpen: Open;
  active: boolean;
  reduced: boolean;
}) {
  const wires = useMemo(() => {
    const hubEdge = (p: THREE.Vector3) => p.clone().setY(0).normalize().multiplyScalar(1.12).setY(0.012);
    const out = seats.map((s, i) => {
      const p = new THREE.Vector3(...s.pos);
      return { from: p.clone().multiplyScalar(0.62).setY(0.012), to: hubEdge(p), delay: i * 0.25, dim: s.trial };
    });
    const t = new THREE.Vector3(...TOWER);
    out.push({ from: hubEdge(t), to: t.clone().multiplyScalar(0.83).setY(0.012), delay: 1.1, dim: false });
    return out;
  }, [seats]);
  return (
    <Canvas
      orthographic
      shadows
      frameloop={active ? "always" : "never"}
      camera={{ position: [10, 10, 10], zoom: 60, near: 0.1, far: 100 }}
      dpr={[1, 1.75]}
      gl={{ antialias: true, alpha: true, toneMapping: THREE.NeutralToneMapping, toneMappingExposure: 1.08 }}
      style={{ position: "absolute", inset: 0 }}
      onPointerMissed={() => (document.body.style.cursor = "")}
    >
      <Fit />
      <LabelSync bridge={bridge} />
      <hemisphereLight args={["#ffffff", C.lav2, 1.25]} />
      <ambientLight intensity={0.35} />
      <directionalLight
        position={[6, 12, 4]}
        intensity={1.5}
        castShadow
        shadow-mapSize={[2048, 2048]}
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
      <Tilt reduced={reduced}>
        <Floor />
        {wires.map((w, i) => (
          <Wire key={i} from={w.from} to={w.to} beat={beat} delay={w.delay} reduced={reduced} dim={w.dim} />
        ))}
        <Hub book={hub} bridge={bridge} onOpen={onOpen} reduced={reduced} />
        <Tower cycles={cycles} bridge={bridge} beat={beat} reduced={reduced} />
        {seats.map((s) => (
          <Desk key={s.slug} seat={s} bridge={bridge} onOpen={onOpen} reduced={reduced} />
        ))}
      </Tilt>
    </Canvas>
  );
}
