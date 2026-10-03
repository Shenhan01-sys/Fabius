"use client";

// Agen Fabius sebagai kristal komitmen (docs/design/landing.md §1). 3x3x3 blok kaca: inti = jantung agen (selalu bercahaya),
// 26 blok luar = komitmen. Indigo = aturan terkunci di chain (urut waktu kunci), putih = sinyal terbukti SAH, bening = slot rekam jejak kosong.
// Masuk: blok terbang lalu mengunci (komit). Terus-menerus: kubus bernapas + berputar pelan; tiap ~3,4 s satu blok non-kosong keluar, berkilau,
// lalu kembali (onBeat memberi tahu DOM blok mana). Interaksi: kubus condong ke arah kursor.

import { Canvas, useFrame, useThree } from "@react-three/fiber";
import { Environment, Lightformer } from "@react-three/drei";
import { Bloom, EffectComposer } from "@react-three/postprocessing";
import { useMemo, useRef } from "react";
import * as THREE from "three";
import { RoundedBoxGeometry } from "three-stdlib";

export type BlockKind = "core" | "empty" | "sealed" | "verified";
export type Counts = { verified: number; sealed: number; empty: number };

const BEAT_S = 3.4;
const BEAT_LEN = 1.5;

function rng(seed: number) {
  let a = seed;
  return () => {
    a = (a + 0x6d2b79f5) | 0;
    let t = Math.imul(a ^ (a >>> 15), 1 | a);
    t = (t + Math.imul(t ^ (t >>> 7), 61 | t)) ^ t;
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
  };
}

const easeOutBack = (t: number) => {
  const c1 = 1.4;
  const c3 = c1 + 1;
  return 1 + c3 * Math.pow(t - 1, 3) + c1 * Math.pow(t - 1, 2);
};
const clamp01 = (x: number) => Math.max(0, Math.min(1, x));
const bump = (t: number) => Math.sin(Math.PI * clamp01(t)); // 0 -> 1 -> 0

type Block = { kind: BlockKind; target: THREE.Vector3; start: THREE.Vector3; spin: THREE.Euler; delay: number; normal: THREE.Vector3; order: number };

function layout(counts: Counts): Block[] {
  const r = rng(20261003);
  const cells: THREE.Vector3[] = [];
  for (let x = -1; x <= 1; x++) for (let y = -1; y <= 1; y++) for (let z = -1; z <= 1; z++) cells.push(new THREE.Vector3(x, y, z));
  const outer = cells.map((_, i) => i).filter((i) => cells[i].lengthSq() > 0);
  for (let i = outer.length - 1; i > 0; i--) {
    const j = Math.floor(r() * (i + 1));
    [outer[i], outer[j]] = [outer[j], outer[i]];
  }
  const kinds: BlockKind[] = cells.map((c) => (c.lengthSq() === 0 ? "core" : "empty"));
  const order: number[] = cells.map(() => -1);
  let k = 0;
  for (let i = 0; i < counts.sealed && k < outer.length; i++, k++) {
    kinds[outer[k]] = "sealed";
    order[outer[k]] = i;
  }
  for (let i = 0; i < counts.verified && k < outer.length; i++, k++) kinds[outer[k]] = "verified";
  return cells.map((c, i) => {
    const dir = new THREE.Vector3(r() - 0.5, r() - 0.3, r() - 0.5).normalize();
    const n = c.clone();
    const ax = Math.abs(n.x) >= Math.abs(n.y) && Math.abs(n.x) >= Math.abs(n.z) ? "x" : Math.abs(n.y) >= Math.abs(n.z) ? "y" : "z";
    const normal = new THREE.Vector3(ax === "x" ? Math.sign(n.x) : 0, ax === "y" ? Math.sign(n.y) : 0, ax === "z" ? Math.sign(n.z) : 0);
    return {
      kind: kinds[i],
      target: c.clone().multiplyScalar(1.02),
      start: dir.multiplyScalar(6 + r() * 4),
      spin: new THREE.Euler(r() * 4, r() * 4, r() * 4),
      delay: 0.25 + (kinds[i] === "core" ? 0 : 0.18) + i * 0.028 + r() * 0.12,
      normal,
      order: order[i],
    };
  });
}

function useMaterials() {
  // Kaca TRANSPARAN (bukan transmisi): blok transmisi three.js tidak saling melihat, jadi inti yang bercahaya tak akan tembus. Dengan alfa + sorot
  // lingkungan + tepi tipis, blok-blok saling terlihat seperti kubus referensi, dan cahaya inti menembus dari dalam.
  return useMemo(() => {
    const glass = (o: THREE.MeshPhysicalMaterialParameters) =>
      new THREE.MeshPhysicalMaterial({
        transparent: true, depthWrite: false, roughness: 0.06, metalness: 0, clearcoat: 1, clearcoatRoughness: 0.05, envMapIntensity: 1.05,
        side: THREE.DoubleSide, ...o,
      });
    return {
      emptyA: glass({ color: "#e4dcff", opacity: 0.24, iridescence: 0.45, iridescenceIOR: 1.3 }),
      emptyB: glass({ color: "#c8b8ff", opacity: 0.32, iridescence: 0.25 }),
      sealed: glass({ color: "#2a1a94", opacity: 0.84, envMapIntensity: 0.9 }),
      verified: new THREE.MeshPhysicalMaterial({ color: "#f4f0ff", emissive: "#b9a6ff", emissiveIntensity: 0.75, roughness: 0.25, clearcoat: 1 }),
      core: new THREE.MeshPhysicalMaterial({ color: "#efe9ff", emissive: "#cbbcff", emissiveIntensity: 1.15, roughness: 0.35 }),
      edge: new THREE.LineBasicMaterial({ color: "#ffffff", transparent: true, opacity: 0.42 }),
      edgeDark: new THREE.LineBasicMaterial({ color: "#8f78ff", transparent: true, opacity: 0.7 }),
    };
  }, []);
}

function Blocks({ counts, onBeat }: { counts: Counts; onBeat?: (order: number) => void }) {
  const blocks = useMemo(() => layout(counts), [counts]);
  const mats = useMaterials();
  const geo = useMemo(() => new RoundedBoxGeometry(0.94, 0.94, 0.94, 4, 0.075), []);
  const edges = useMemo(() => new THREE.EdgesGeometry(new THREE.BoxGeometry(0.9, 0.9, 0.9)), []);
  const root = useRef<THREE.Group>(null!);
  const items = useRef<(THREE.Mesh | null)[]>([]);
  const coreLight = useRef<THREE.PointLight>(null!);
  const beatLight = useRef<THREE.PointLight>(null!);
  const t0 = useRef<number | null>(null);
  const lastBeat = useRef(-1);
  const { viewport } = useThree();
  const beatables = useMemo(() => {
    const idx = blocks.map((b, i) => i).filter((i) => blocks[i].kind === "sealed" || blocks[i].kind === "verified");
    return idx.sort((a, b) => blocks[a].order - blocks[b].order);
  }, [blocks]);

  const wide = viewport.width > 7.5;
  const base = useMemo(() => new THREE.Vector3(wide ? viewport.width * 0.22 : 0, wide ? 0.78 : viewport.height * 0.2, 0), [wide, viewport.width, viewport.height]);

  useFrame((state) => {
    const now = state.clock.elapsedTime;
    if (t0.current === null) t0.current = now;
    const t = now - t0.current;
    const g = root.current;
    // idle: napas + putar pelan + condong ke kursor
    const breathe = 1 + Math.sin(t * 1.3) * 0.012;
    g.position.lerp(new THREE.Vector3(base.x + state.pointer.x * 0.25, base.y + state.pointer.y * 0.15 + Math.sin(t * 0.9) * 0.06, 0), 0.06);
    g.rotation.x = THREE.MathUtils.lerp(g.rotation.x, 0.52 - state.pointer.y * 0.18, 0.05);
    g.rotation.y = Math.PI / 4 + t * 0.11 + state.pointer.x * 0.25;
    g.scale.setScalar((wide ? 0.76 : 0.66) * breathe);

    // detak: blok non-kosong berikutnya keluar, berkilau, kembali
    const settled = t > 3.2;
    const beatIdx = settled && beatables.length ? Math.floor((t - 3.2) / BEAT_S) : -1;
    const phase = settled ? ((t - 3.2) % BEAT_S) / BEAT_LEN : 2;
    const active = beatIdx >= 0 ? beatables[beatIdx % beatables.length] : -1;
    if (beatIdx !== lastBeat.current && active >= 0) {
      lastBeat.current = beatIdx;
      onBeat?.(blocks[active].order);
    }

    blocks.forEach((b, i) => {
      const m = items.current[i];
      if (!m) return;
      const p = easeOutBack(clamp01((t - b.delay) / 1.15));
      m.position.lerpVectors(b.start, b.target, p);
      m.rotation.set(b.spin.x * (1 - p), b.spin.y * (1 - p), b.spin.z * (1 - p));
      if (i === active) {
        const k = bump(phase);
        m.position.addScaledVector(b.normal, 0.42 * k);
        m.scale.setScalar(1 + 0.05 * k);
      } else {
        m.scale.setScalar(clamp01((t - b.delay) * 3) * 0.999 + 0.001);
      }
    });

    const coreK = clamp01((t - 0.2) / 1.2);
    coreLight.current.intensity = coreK * (5.5 + Math.sin(t * 1.7) * 1.2);
    if (active >= 0) {
      const k = bump(phase);
      beatLight.current.position.copy(blocks[active].target).addScaledVector(blocks[active].normal, 0.9);
      beatLight.current.intensity = 9 * k;
    } else beatLight.current.intensity = 0;
  });

  return (
    <group ref={root}>
      <pointLight ref={coreLight} color="#b49dff" distance={5} decay={1.6} />
      <pointLight ref={beatLight} color="#ffffff" distance={3} decay={1.8} />
      {blocks.map((b, i) => (
        <mesh
          key={i}
          ref={(el) => {
            items.current[i] = el;
          }}
          geometry={geo}
          material={b.kind === "core" ? mats.core : b.kind === "sealed" ? mats.sealed : b.kind === "verified" ? mats.verified : i % 3 === 0 ? mats.emptyB : mats.emptyA}
          position={b.start}
          renderOrder={b.kind === "core" ? 0 : 1}
        >
          {b.kind !== "core" && <lineSegments geometry={edges} material={b.kind === "sealed" ? mats.edgeDark : mats.edge} />}
        </mesh>
      ))}
    </group>
  );
}

export default function Crystal({ counts, onBeat, active = true }: { counts: Counts; onBeat?: (order: number) => void; active?: boolean }) {
  // active=false (hero di luar layar) = berhenti me-render: hemat baterai, scroll tetap mulus
  return (
    <Canvas frameloop={active ? "always" : "never"} camera={{ position: [0, 0, 11], fov: 30 }} dpr={[1, 1.75]} gl={{ antialias: true }} style={{ position: "absolute", inset: 0 }}>
      <color attach="background" args={["#ece8fa"]} />
      <fog attach="fog" args={["#ece8fa", 14, 26]} />
      <ambientLight intensity={0.42} />
      <directionalLight position={[3, 7, 5]} intensity={0.85} />
      <Blocks counts={counts} onBeat={onBeat} />
      <Environment resolution={256} frames={1}>
        <Lightformer form="rect" intensity={2.1} position={[0, 6, -3]} scale={[12, 5, 1]} color="#ffffff" />
        <Lightformer form="rect" intensity={1.5} position={[-6, 1, 2]} rotation-y={Math.PI / 2} scale={[8, 3, 1]} color="#d8ccff" />
        <Lightformer form="rect" intensity={1.6} position={[6, -1, 2]} rotation-y={-Math.PI / 2} scale={[8, 3, 1]} color="#7a5cff" />
        <Lightformer form="ring" intensity={1.4} position={[0, 0, 6]} scale={3} color="#b9a6ff" />
      </Environment>
      <EffectComposer>
        <Bloom intensity={0.22} luminanceThreshold={0.92} luminanceSmoothing={0.15} mipmapBlur />
      </EffectComposer>
    </Canvas>
  );
}
