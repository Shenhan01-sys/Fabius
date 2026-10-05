// Lantai trading /desk (P158, docs/design/desk.md): dari data `/desk` ke meja kerja. Satu meja = satu agent (buku v2 bila ada, v1 selama
// berdampingan); keadaan NPC dibaca dari rekaman terakhir buku itu, bukan dikarang.

import type { Buku, Desk } from "@/lib/desk";

export type Pose = "trade" | "hold" | "flat" | "fail" | "think";
export type Look = { shirt: string; hair: string; skin: string; extra: "headset" | "cap" | "paper" | "none"; short?: string };
export type Seat = { slug: string; nama: string; main: Buku; v1?: Buku; v2?: Buku; pose: Pose; look: Look; pos: [number, number, number]; rotY: number };

// warna kaus = keluarga violet/ink Fabius; kulit beragam; aksesori membedakan agent tanpa bergantung warna
const LOOKS: Record<string, Look> = {
  glm: { shirt: "#6e4bff", hair: "#2a2140", skin: "#c68e63", extra: "headset", short: "DeepSeek" },
  qwen: { shirt: "#9d86ff", hair: "#15122b", skin: "#f1c9a5", extra: "cap", short: "Qwen" },
  berita: { shirt: "#15122b", hair: "#3b2a1e", skin: "#8d5a3b", extra: "paper", short: "News" },
};
const LOOK_DEFAULT: Look = { shirt: "#8b86a6", hair: "#15122b", skin: "#d9a982", extra: "none" };

export const RING = 3.5; // jari-jari lingkaran meja di sekitar hub (satuan dunia)

export function pose(b: Buku, lastCycle: number | undefined, now: number): Pose {
  if (b.status_terakhir && b.status_terakhir !== "ok") return "fail";
  if (lastCycle && now - lastCycle >= 300) return "think"; // siklus berikutnya sedang berjalan, rekamannya belum tercatat
  if ((b.isi_terakhir ?? 0) > 0) return "trade";
  return Object.keys(b.posisi).length ? "hold" : "flat";
}

export function seats(d: Desk, now: number): Seat[] {
  const slugs = Array.from(
    new Set(d.buku.filter((b) => b.agent !== "konsensus" && b.agent !== "v2" && !b.agent.startsWith("_")).map((b) => b.agent.replace(/^v2:/, ""))),
  ).sort();
  const last = d.siklus_terakhir?.siklus;
  const n = slugs.length;
  return slugs.map((slug, i) => {
    const v1 = d.buku.find((b) => b.agent === slug);
    const v2 = d.buku.find((b) => b.agent === `v2:${slug}`);
    const main = (v2 ?? v1)!;
    // sudut layar: kiri (180°) -> depan (270°) -> kanan (360°); belakang dipakai menara BNB Chain
    const phi = ((n === 1 ? 270 : 180 + (i * 180) / (n - 1)) * Math.PI) / 180;
    const sx = RING * Math.cos(phi);
    const depth = -RING * Math.sin(phi);
    const x = (sx + depth) / Math.SQRT2;
    const z = (depth - sx) / Math.SQRT2;
    return {
      slug,
      nama: (v1?.nama ?? main.nama).replace(/^v2 · /, "").replace(/^Fabius Analyst · /, ""),
      main,
      v1,
      v2,
      pose: pose(main, last, now),
      look: LOOKS[slug] ?? LOOK_DEFAULT,
      pos: [x, 0, z],
      // punggung NPC ke kamera dengan sudut 3/4 supaya layar monitor + tangan yang mengetik terlihat dari balik bahu
      rotY: (5 * Math.PI) / 4 - 0.55 * (sx / RING),
    };
  });
}

export function hubBook(d: Desk): Buku | undefined {
  return d.buku.find((b) => b.agent === "v2") ?? d.buku.find((b) => b.agent === "konsensus");
}

export const fmtPct = (x: number) => `${x >= 0 ? "+" : ""}${x.toFixed(2)}%`;
export const glyph: Record<Pose, string> = { trade: "⇄", hold: "■", flat: "■", fail: "✕", think: "…" };
