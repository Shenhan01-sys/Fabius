// Lantai trading /desk (P158, docs/design/desk.md): dari data `/desk` ke meja kerja. Satu meja = satu agent (buku v2 bila ada, v1 selama
// berdampingan); keadaan NPC dibaca dari rekaman terakhir buku itu, bukan dikarang. P159: jumlah agent bebas - meja disusun melingkar di depan
// hub (menara BNB Chain di belakang) dan mengecil bila padat; penampilan dari template `looks.ts`.

import type { Buku, Desk } from "@/lib/desk";
import { dedupeShort, lookFor, type Look, type NpcHint } from "./looks";

export type { Look } from "./looks";
export type Pose = "trade" | "hold" | "flat" | "fail" | "think";
export type Seat = {
  slug: string;
  nama: string;
  main: Buku;
  v1?: Buku;
  v2?: Buku;
  pose: Pose;
  look: Look;
  pos: [number, number, number];
  rotY: number;
  scale: number;
  trial: boolean; // P160: kursi uji - suaranya belum dihitung di konsensus
};

// penampilan tiga agent pertama bila gerbang belum mengirim `npc` (sama dengan config/agents.json)
const FALLBACK: Record<string, NpcHint> = {
  glm: { shirt: "#6e4bff", hair: "#2a2140", skin: "#c68e63", extra: "headset", prop: "mug", short: "DeepSeek" },
  qwen: { shirt: "#9d86ff", hair: "#15122b", skin: "#f1c9a5", extra: "cap", prop: "mug", short: "Qwen" },
  berita: { shirt: "#15122b", hair: "#3b2a1e", skin: "#8d5a3b", extra: "none", prop: "paper", short: "News" },
};

export const RING = 3.5; // jari-jari lingkaran meja untuk <= 3 agent (satuan dunia)

export function pose(b: Buku, lastCycle: number | undefined, now: number): Pose {
  if (b.status_terakhir && b.status_terakhir !== "ok") return "fail";
  if (lastCycle && now - lastCycle >= 300) return "think"; // siklus berikutnya sedang berjalan, rekamannya belum tercatat
  if ((b.isi_terakhir ?? 0) > 0) return "trade";
  return Object.keys(b.posisi).length ? "hold" : "flat";
}

/** Susunan meja untuk n agent: sudut layar dari kiri lewat depan ke kanan (n > 3: sampai belakang-samping), skala meja dari jarak antarmeja. */
export function layout(n: number, i: number) {
  const [a0, a1] = n <= 3 ? [180, 360] : [150, 390];
  const ring = n <= 3 ? RING : Math.min(4.1, RING + (n - 3) * 0.15);
  const step = n === 1 ? 0 : (a1 - a0) / (n - 1);
  const phi = ((n === 1 ? 270 : a0 + i * step) * Math.PI) / 180;
  const sx = ring * Math.cos(phi);
  const depth = -ring * Math.sin(phi);
  const chord = n === 1 ? 9 : 2 * ring * Math.sin(((step / 2) * Math.PI) / 180);
  return {
    pos: [(sx + depth) / Math.SQRT2, 0, (depth - sx) / Math.SQRT2] as [number, number, number],
    // punggung NPC ke kamera dengan sudut 3/4 supaya layar monitor + tangan yang mengetik terlihat dari balik bahu
    rotY: (5 * Math.PI) / 4 - 0.55 * (sx / ring),
    scale: Math.max(0.6, Math.min(1, chord / 2.9)),
  };
}

export function seats(d: Desk, now: number): Seat[] {
  // agent yang dinonaktifkan builder (kursi `keluar`) tidak punya meja di lantai
  const keluar = (slug: string) => (d.buku.find((b) => b.agent === `v2:${slug}`)?.kursi ?? d.kursi?.[slug]) === "keluar";
  const slugs = Array.from(
    new Set(d.buku.filter((b) => b.agent !== "konsensus" && b.agent !== "v2" && !b.agent.startsWith("_")).map((b) => b.agent.replace(/^v2:/, ""))),
  )
    .filter((s) => !keluar(s))
    .sort();
  const last = d.siklus_terakhir?.siklus;
  const out = slugs.map((slug, i) => {
    const v1 = d.buku.find((b) => b.agent === slug);
    const v2 = d.buku.find((b) => b.agent === `v2:${slug}`);
    const main = (v2 ?? v1)!;
    const nama = (v1?.nama ?? main.nama).replace(/^v2 · /, "").replace(/^Fabius Analyst · /, "");
    return {
      slug,
      nama,
      main,
      v1,
      v2,
      pose: pose(main, last, now),
      look: lookFor(slug, nama, main.npc ?? v1?.npc ?? FALLBACK[slug]),
      trial: (v2?.kursi ?? d.kursi?.[slug]) === "uji",
      ...layout(slugs.length, i),
    };
  });
  return dedupeShort(out);
}

export function hubBook(d: Desk): Buku | undefined {
  return d.buku.find((b) => b.agent === "v2") ?? d.buku.find((b) => b.agent === "konsensus");
}

export const fmtPct = (x: number) => `${x >= 0 ? "+" : ""}${x.toFixed(2)}%`;
export const glyph: Record<Pose, string> = { trade: "⇄", hold: "■", flat: "■", fail: "✕", think: "…" };
