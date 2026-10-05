// Meja AI 5 menit (P152, F-D109): data publik dari gerbang `GET /desk` (tools/x402_sinyal.py::Gate.meja_view). Paper saja; tiap siklus satu Merkle
// root keputusan semua agent dikomit ke DeskAnchor selama siklus berjalan.

import { GATE } from "./x402-buy";

export type Target = { w: number; k: number; alasan?: string };
export type Keputusan = {
  ringkasan: string;
  target: Record<string, Target>;
  diubah?: string[];
  ditolak?: { aset?: string; faktor?: string; galat: string }[];
  // v2 (P154/P155, F-D112): agent = bot + instrumen {aset, k}; konsensus = bot dominan + daftar instrumen + skor
  bot?: string;
  skor_bot?: Record<string, number>;
  nilai_bot?: Record<string, number>;
  instrumen?: (string | { aset: string; k: number })[];
  skor_instrumen?: Record<string, number>;
  eksposur?: number;
  veto?: (string | { aset: string; faktor: string })[];
  arah_alasan?: Record<string, string>;
};
export type Buku = {
  agent: string;
  nama: string;
  versi?: number;
  ekuitas: number;
  hasil_pct: number;
  biaya: number;
  n_trade: number;
  posisi: Record<string, number>;
  deret: [number, number][];
  status_terakhir: string | null;
  keputusan_terakhir: Keputusan | null;
  siklus_terakhir?: number | null;
  isi_terakhir?: number;
  // P159: penampilan pekerja 3D dari config/agents.json (opsional)
  kursi?: "aktif" | "uji" | "antre" | null; // P160: kursi agent di meja v2
  npc?: { shirt?: string; hair?: string; skin?: string; extra?: "headset" | "cap" | "glasses" | "beanie" | "hood" | "none"; prop?: "mug" | "paper" | "plant" | "books"; short?: string } | null;
};
export type Isi = { aset: string; dari: number; ke: number; harga: number; fee: number };
export type Siklus = { siklus: number; root: string; tx: string | null; status: string; n: number };
export type Rekaman = {
  siklus: number;
  agent: string;
  status?: string;
  galat?: string;
  hash: string;
  ekuitas: number;
  keputusan?: Keputusan;
  dasar?: string;
  isi?: Isi[];
};
export type Desk = {
  t: number;
  params: { siklus_s: number; fee: number; maks_per_aset: number; maks_gross: number; kuorum: number; ubah_min: number; modal_awal: number; aset: string[] };
  params_sha: string;
  params_v2?: { universe_top: number; maks_instrumen: number; likuiditas_min_usd: number; rugi_harian_maks: number };
  // P160 (F-D113): ambang konsensus untuk jumlah kursi aktif sekarang + aturan kursi
  ambang_v2?: { kuorum: number; min_agent_instrumen: number; veto_min_agent: number; ambang_instrumen: number };
  params_kursi?: { status: string; maks_aktif: number; maks_uji: number; jendela_siklus: number; naik_sah_min: number; tukar_unggul_min: number; turun_sah_maks: number };
  kursi?: Record<string, "aktif" | "uji" | "antre">;
  params_v2_sha?: string;
  anchor?: string;
  buku: Buku[];
  rekaman: Rekaman[];
  siklus_terakhir: Siklus | null;
  siklus_12?: Siklus[];
  siklus_24j: number;
  komit_24j: number;
};

export async function desk(): Promise<Desk> {
  const r = await fetch(`${GATE}/desk`, { cache: "no-store" });
  if (!r.ok) throw new Error(`/desk HTTP ${r.status}`);
  return r.json();
}

// P158: rincian satu buku untuk modal lantai /desk (`GET /desk/agent/<nama>`, Gate.meja_agent)
export type AgentDetail = {
  buku: Buku;
  statistik: { siklus_24j: number; ok: number; gagal: number; terlambat: number; siklus_bertransaksi: number; isi_24j: number; biaya_24j: number; bot_pilihan: Record<string, number> };
  riwayat: { siklus: number; status: string; galat?: string | null; ringkasan?: string | null; bot?: string | null; target: Record<string, Target>; isi: Isi[]; ekuitas: number; hash: string }[];
  model: string | null;
  agent_id: number | null;
};

export async function agentDetail(name: string): Promise<AgentDetail> {
  const r = await fetch(`${GATE}/desk/agent/${encodeURIComponent(name)}`, { cache: "no-store" });
  if (!r.ok) throw new Error(`/desk/agent HTTP ${r.status}`);
  return r.json();
}

export type DataHealth = {
  snapshot_24j: number;
  durasi_maks_s: number | null;
  lambat_24j: number;
  registry_sha: string | null;
  sumber: Record<string, { cakupan_rata: number | null; siklus_cakupan_penuh: number; status_terakhir: string | null }>;
  terakhir: { t: number } | null;
};

export async function dataHealth(): Promise<DataHealth> {
  const r = await fetch(`${GATE}/desk/data`, { cache: "no-store" });
  if (!r.ok) throw new Error(`/desk/data HTTP ${r.status}`);
  return r.json();
}

export const hhmm = (s: number) => new Date(s * 1000).toISOString().slice(11, 16) + "Z";
