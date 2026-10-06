"use client";

// Strip pipeline Fabius Live Book (P164, docs/design/desk.md §Fabius Live Book). Satu siklus = jalur produksi kiri -> kanan: agent (NPC pekerja
// yang SAMA dengan lantai, berdiri; ✓ kubus violet / ✕ silang merah) -> mesin rumus (6 kubus mengorbit = 6 bot, ukuran = skor, pemenang menyala)
// -> robot aturan bot (ID bot di dadanya, lengan menunjuk ke buku) -> buku (batang posisi: tinggi = bobot, violet = long, ink = short) -> tumpukan
// blok BNB Chain (blok teratas menyala bila root dikomit). Titik cahaya mengalir kiri -> kanan saat siklus baru masuk. Label = DOM lewat Bridge.

import { Canvas, useFrame, useThree } from "@react-three/fiber";
import { Environment, Lightformer, RoundedBox } from "@react-three/drei";
import { useEffect, useLayoutEffect, useMemo, useRef, useState } from "react";
import * as THREE from "three";
import type { LiveBook } from "@/lib/desk";
import type { Bridge } from "./bridge";
import type { Look } from "./model";
import { C, mat, Npc } from "./parts";

const W = 17.6; // lebar adegan (satuan dunia) untuk zoom muat-bingkai
const H = 4.5;
export const X = { agents: -6.3, formula: -2.0, bot: 1.6, book: 4.9, chain: 7.9 };
const PAD = { agents: 3.4, formula: 2.2, bot: 2.0, book: 2.2, chain: 1.8 };
const BOTS = ["B1-TREND", "B2-RS", "B3-CARRY", "B4-LISTING-FADE", "B5-CORE-RWA", "B6-BOUNCE"];

function Fit() {
  const get = useThree((s) => s.get);
  const width = useThree((s) => s.size.width);
  const height = useThree((s) => s.size.height);
  useLayoutEffect(() => {
    const cam = get().camera as THREE.OrthographicCamera;
    cam.position.set(1.4, 5.2, 14);
    cam.zoom = Math.min(width / W, height / H);
    cam.lookAt(0.8, 0.95, 0);
    cam.updateProjectionMatrix();
  }, [get, width, height]);
  return null;
}

function Pad({ x, w, round = false }: { x: number; w: number; round?: boolean }) {
  const m = useMemo(() => ({ clay: mat(C.clay), seam: new THREE.MeshBasicMaterial({ color: C.violet2, toneMapped: false }) }), []);
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

// ---------------------------------------------------------------- 1. agent berdiri

function Agents({ agents, looks, reduced, bridge }: { agents: LiveBook["pipa"]["agen"]; looks: Record<string, Look>; reduced: boolean; bridge: Bridge }) {
  const n = Math.max(1, agents.length);
  const gap = Math.min(0.62, (PAD.agents - 0.5) / n);
  const m = useMemo(() => ({ ok: mat(C.violet, { emissive: C.violet, emissiveIntensity: 0.6 }), bad: mat(C.gap, { emissive: C.gap, emissiveIntensity: 0.5 }) }), []);
  return (
    <group position={[X.agents, 0.18, 0]}>
      {agents.map((a, i) => {
        const ok = a.status === "ok";
        const look = looks[a.slug];
        return (
          <group key={a.slug} position={[(i - (n - 1) / 2) * gap, 0, (i % 2) * 0.22 - 0.1]} rotation-y={0.35} scale={0.82}>
            {look && <Npc look={look} pose={ok ? "trade" : "fail"} reduced={reduced} stand />}
            {ok ? (
              <mesh material={m.ok} position={[0, 1.95, 0]}>
                <boxGeometry args={[0.16, 0.16, 0.16]} />
              </mesh>
            ) : (
              [0.78, -0.78].map((r) => (
                <mesh key={r} material={m.bad} position={[0, 1.95, 0]} rotation-z={r}>
                  <boxGeometry args={[0.26, 0.05, 0.05]} />
                </mesh>
              ))
            )}
          </group>
        );
      })}
      <group ref={bridge.anchor("agents")} position={[0, 2.35, 0]} />
    </group>
  );
}

// ---------------------------------------------------------------- 2. mesin rumus: 6 bot mengorbit, pemenang menyala

function Formula({ nilai, winner, reduced, bridge }: { nilai: Record<string, number>; winner: string | null; reduced: boolean; bridge: Bridge }) {
  const ringA = useRef<THREE.Mesh>(null!);
  const ringB = useRef<THREE.Mesh>(null!);
  const orbit = useRef<THREE.Group>(null!);
  const core = useRef<THREE.Mesh>(null!);
  const m = useMemo(
    () => ({
      clay: mat(C.clay),
      glass: new THREE.MeshStandardMaterial({ color: C.violet2, transparent: true, opacity: 0.22, roughness: 0.1, metalness: 0.1 }),
      core: mat(C.violet, { emissive: C.violet, emissiveIntensity: 0.9 }),
      ring: new THREE.MeshBasicMaterial({ color: C.violet2, toneMapped: false }),
      win: mat(C.violet, { emissive: C.violet2, emissiveIntensity: 1.2 }),
      lose: mat(C.lav3),
    }),
    [],
  );
  const vals = BOTS.map((b) => nilai[b] ?? 0);
  const top = Math.max(1, ...vals.map((v) => Math.abs(v)));
  useFrame(({ clock }) => {
    const t = clock.elapsedTime;
    if (reduced) return;
    ringA.current.rotation.x = t * 0.7;
    ringB.current.rotation.z = t * 0.5;
    orbit.current.rotation.y = t * 0.35;
    core.current.scale.setScalar(1 + Math.sin(t * 2.2) * 0.05);
  });
  return (
    <group position={[X.formula, 0, 0]}>
      <mesh material={m.clay} position={[0, 0.45, 0]} castShadow>
        <cylinderGeometry args={[0.28, 0.36, 0.55, 24]} />
      </mesh>
      <RoundedBox args={[0.82, 0.82, 0.82]} radius={0.08} position={[0, 1.2, 0]} material={m.glass} />
      <mesh ref={core} material={m.core} position={[0, 1.2, 0]}>
        <boxGeometry args={[0.3, 0.3, 0.3]} />
      </mesh>
      <mesh ref={ringA} material={m.ring} position={[0, 1.2, 0]}>
        <torusGeometry args={[0.62, 0.018, 8, 64]} />
      </mesh>
      <mesh ref={ringB} material={m.ring} position={[0, 1.2, 0]} rotation-x={Math.PI / 2}>
        <torusGeometry args={[0.7, 0.014, 8, 64]} />
      </mesh>
      <group ref={orbit} position={[0, 1.2, 0]}>
        {BOTS.map((b, i) => {
          const a = (i / BOTS.length) * Math.PI * 2;
          const s = 0.07 + 0.13 * (Math.max(0, vals[i]) / top);
          return (
            <mesh key={b} material={b === winner ? m.win : m.lose} position={[Math.cos(a) * 0.98, Math.sin(a * 2) * 0.12, Math.sin(a) * 0.98]}>
              <boxGeometry args={[s, s, s]} />
            </mesh>
          );
        })}
      </group>
      <group ref={bridge.anchor("formula")} position={[0, 2.35, 0]} />
    </group>
  );
}

// ---------------------------------------------------------------- 3. robot aturan bot

function useLabelTexture(text: string) {
  const [cv] = useState(() => {
    const c = document.createElement("canvas");
    c.width = 256;
    c.height = 128;
    return c;
  });
  const [tex] = useState(() => {
    const t = new THREE.CanvasTexture(cv);
    t.colorSpace = THREE.SRGBColorSpace;
    return t;
  });
  const matRef = useRef<THREE.MeshBasicMaterial>(null);
  useEffect(() => {
    const g = cv.getContext("2d")!;
    g.fillStyle = C.night;
    g.fillRect(0, 0, 256, 128);
    g.fillStyle = C.violet2;
    g.font = "700 34px JetBrains Mono, ui-monospace, monospace";
    g.textAlign = "center";
    const [a, b] = text.split("-");
    g.fillText(a ?? "", 128, b ? 56 : 76);
    if (b) {
      g.font = "600 24px JetBrains Mono, ui-monospace, monospace";
      g.fillText(text.slice(a.length + 1), 128, 96);
    }
    if (matRef.current?.map) matRef.current.map.needsUpdate = true;
  }, [text, cv]);
  return { tex, matRef };
}

function Robot({ bot, reduced, bridge }: { bot: string | null; reduced: boolean; bridge: Bridge }) {
  const body = useRef<THREE.Group>(null!);
  const tip = useRef<THREE.Mesh>(null!);
  const { tex, matRef } = useLabelTexture(bot ?? "—");
  const m = useMemo(
    () => ({
      clay: mat(C.clay),
      ink: mat(C.ink, { roughness: 0.4 }),
      eye: new THREE.MeshBasicMaterial({ color: C.violet2, toneMapped: false }),
      tip: mat(C.violet, { emissive: C.violet, emissiveIntensity: 1 }),
      joint: mat(C.lav3),
    }),
    [],
  );
  useFrame(({ clock }) => {
    const t = clock.elapsedTime;
    body.current.position.y = reduced ? 0 : Math.sin(t * 1.6) * 0.04;
    (tip.current.material as THREE.MeshStandardMaterial).emissiveIntensity = reduced ? 1 : 0.6 + Math.abs(Math.sin(t * 3)) * 0.8;
  });
  return (
    <group position={[X.bot, 0.18, 0]} rotation-y={-0.15}>
      <group ref={body}>
        {[-0.17, 0.17].map((x) => (
          <mesh key={x} material={m.joint} position={[x, 0.2, 0]} castShadow>
            <boxGeometry args={[0.16, 0.4, 0.18]} />
          </mesh>
        ))}
        <RoundedBox args={[0.74, 0.78, 0.5]} radius={0.08} position={[0, 0.8, 0]} material={m.clay} castShadow />
        <mesh position={[0, 0.82, 0.255]}>
          <planeGeometry args={[0.52, 0.3]} />
          <meshBasicMaterial ref={matRef} map={tex} toneMapped={false} />
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
        <mesh ref={tip} material={m.tip} position={[0, 1.86, 0]}>
          <sphereGeometry args={[0.05, 12, 12]} />
        </mesh>
        <mesh material={m.joint} position={[-0.45, 0.82, 0]} rotation-z={0.15} castShadow>
          <boxGeometry args={[0.14, 0.5, 0.14]} />
        </mesh>
        {/* lengan kanan menunjuk ke buku: aturan bot menghasilkan posisi */}
        <mesh material={m.joint} position={[0.52, 0.98, 0.05]} rotation-z={-1.25} castShadow>
          <boxGeometry args={[0.14, 0.5, 0.14]} />
        </mesh>
      </group>
      <group ref={bridge.anchor("bot")} position={[0, 2.35, 0]} />
    </group>
  );
}

// ---------------------------------------------------------------- 4. buku: batang posisi

function Book({ target, bridge }: { target: Record<string, number>; bridge: Bridge }) {
  const m = useMemo(() => ({ long: mat(C.violet, { emissive: C.violet, emissiveIntensity: 0.25 }), short: mat(C.ink, { roughness: 0.5 }), flat: mat(C.lav3) }), []);
  const rows = Object.entries(target)
    .sort((a, b) => Math.abs(b[1]) - Math.abs(a[1]))
    .slice(0, 8);
  return (
    <group position={[X.book, 0.18, 0]}>
      {rows.length === 0 && (
        <mesh material={m.flat} position={[0, 0.04, 0]}>
          <boxGeometry args={[1.2, 0.06, 0.6]} />
        </mesh>
      )}
      {rows.map(([a, w], i) => {
        const h = 0.12 + Math.min(Math.abs(w), 0.25) * 5.2;
        return (
          <mesh key={a} material={w >= 0 ? m.long : m.short} position={[((i % 4) - 1.5) * 0.4, h / 2, i < 4 ? -0.25 : 0.3]} castShadow>
            <boxGeometry args={[0.26, h, 0.26]} />
          </mesh>
        );
      })}
      <group ref={bridge.anchor("book")} position={[0, 2.35, 0]} />
    </group>
  );
}

// ---------------------------------------------------------------- 5. BNB Chain

function Chain({ sealed, beat, reduced, bridge }: { sealed: boolean; beat: number; reduced: boolean; bridge: Bridge }) {
  const top = useRef<THREE.Group>(null!);
  const drop = useRef(0);
  const first = useRef(true);
  const m = useMemo(() => ({ lit: mat(C.violet, { emissive: C.violet, emissiveIntensity: 0.55, roughness: 0.4 }), base: mat(C.lav2), dim: mat(C.lav3) }), []);
  useEffect(() => {
    if (first.current) {
      first.current = false;
      return;
    }
    drop.current = reduced ? 0 : 1;
  }, [beat, reduced]);
  useFrame((_, dt) => {
    drop.current = Math.max(0, drop.current - dt * 1.3);
    top.current.position.y = drop.current * drop.current * 0.8;
  });
  return (
    <group position={[X.chain, 0.18, 0]}>
      {[0, 1, 2].map((i) => (
        <RoundedBox key={i} args={[0.62, 0.16, 0.62]} radius={0.03} position={[0, 0.1 + i * 0.19, 0]} material={m.base} castShadow />
      ))}
      <group ref={top}>
        <RoundedBox args={[0.62, 0.16, 0.62]} radius={0.03} position={[0, 0.1 + 3 * 0.19, 0]} material={sealed ? m.lit : m.dim} castShadow />
      </group>
      <group ref={bridge.anchor("chain")} position={[0, 2.35, 0]} />
    </group>
  );
}

// ---------------------------------------------------------------- kabel + denyut kiri -> kanan

function Flow({ beat, reduced }: { beat: number; reduced: boolean }) {
  const dot = useRef<THREE.Mesh>(null!);
  const burst = useRef(-1);
  const first = useRef(true);
  const segs = useMemo(() => {
    const order = ["agents", "formula", "bot", "book", "chain"] as const;
    return order.slice(0, -1).map((k, i) => {
      const n = order[i + 1];
      return [X[k] + PAD[k] / 2, X[n] - PAD[n] / 2] as [number, number];
    });
  }, []);
  const total = segs.reduce((s, [a, b]) => s + (b - a), 0);
  const m = useMemo(() => new THREE.MeshBasicMaterial({ color: C.violet2, transparent: true, opacity: 0.8, toneMapped: false }), []);
  useEffect(() => {
    if (first.current) {
      first.current = false;
      return;
    }
    burst.current = 0;
  }, [beat]);
  useFrame(({ clock }, dt) => {
    if (reduced) {
      dot.current.visible = false;
      return;
    }
    let u: number;
    if (burst.current >= 0) {
      burst.current += dt;
      u = Math.min(1, burst.current / 2.2);
      dot.current.scale.setScalar(1.8);
      if (u >= 1) burst.current = -1;
    } else {
      u = (clock.elapsedTime * 0.12) % 1;
      dot.current.scale.setScalar(1);
    }
    let d = u * total;
    for (const [a, b] of segs) {
      if (d <= b - a) {
        dot.current.position.set(a + d, 0.12, 0);
        break;
      }
      d -= b - a;
    }
    dot.current.visible = true;
  });
  return (
    <group>
      {segs.map(([a, b]) => (
        <mesh key={a} material={m} position={[(a + b) / 2, 0.12, 0]} rotation-z={Math.PI / 2}>
          <cylinderGeometry args={[0.022, 0.022, b - a, 8]} />
        </mesh>
      ))}
      <mesh ref={dot}>
        <sphereGeometry args={[0.07, 12, 12]} />
        <meshBasicMaterial color="#ffffff" toneMapped={false} />
      </mesh>
    </group>
  );
}

function LabelSync({ bridge }: { bridge: Bridge }) {
  useFrame(({ camera, size }) => bridge.sync(camera, size.width, size.height));
  return null;
}

export default function PipelineScene({
  pipa,
  nilai,
  looks,
  beat,
  bridge,
  active,
  reduced,
}: {
  pipa: LiveBook["pipa"];
  nilai: Record<string, number>;
  looks: Record<string, Look>;
  beat: number;
  bridge: Bridge;
  active: boolean;
  reduced: boolean;
}) {
  return (
    <Canvas
      orthographic
      shadows
      frameloop={active ? "always" : "never"}
      camera={{ position: [1.4, 5.2, 14], zoom: 60, near: 0.1, far: 100 }}
      dpr={[1, 1.75]}
      gl={{ antialias: true, alpha: true, toneMapping: THREE.NeutralToneMapping, toneMappingExposure: 1.08 }}
      style={{ position: "absolute", inset: 0 }}
    >
      <Fit />
      <LabelSync bridge={bridge} />
      <hemisphereLight args={["#ffffff", C.lav2, 1.25]} />
      <ambientLight intensity={0.35} />
      <directionalLight position={[4, 10, 8]} intensity={1.4} castShadow shadow-mapSize={[1024, 1024]} shadow-camera-left={-10} shadow-camera-right={10} shadow-camera-top={5} shadow-camera-bottom={-5} shadow-bias={-0.0004} />
      <Environment resolution={128} frames={1}>
        <Lightformer form="rect" intensity={1.6} position={[0, 6, -3]} scale={[12, 5, 1]} color="#ffffff" />
      </Environment>
      <Pad x={X.agents} w={PAD.agents} />
      <Pad x={X.formula} w={PAD.formula} round />
      <Pad x={X.bot} w={PAD.bot} />
      <Pad x={X.book} w={PAD.book} />
      <Pad x={X.chain} w={PAD.chain} round />
      <Flow beat={beat} reduced={reduced} />
      <Agents agents={pipa.agen} looks={looks} reduced={reduced} bridge={bridge} />
      <Formula nilai={nilai} winner={pipa.bot} reduced={reduced} bridge={bridge} />
      <Robot bot={pipa.bot} reduced={reduced} bridge={bridge} />
      <Book target={pipa.target} bridge={bridge} />
      <Chain sealed={pipa.status === "dikomit"} beat={beat} reduced={reduced} bridge={bridge} />
    </Canvas>
  );
}
