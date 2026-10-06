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
  // P165: tampilan publik tanpa isi yang bisa ditiru - posisi/target/keputusan kosong, jumlah posisi tetap terlihat
  n_posisi?: number;
  terkunci?: boolean;
  // P159: penampilan pekerja 3D dari config/agents.json (opsional)
  kursi?: "aktif" | "uji" | "antre" | "keluar" | null; // P160: kursi agent di meja v2 (keluar = dinonaktifkan builder)
  npc?: { shirt?: string; hair?: string; skin?: string; extra?: "headset" | "cap" | "glasses" | "beanie" | "hood" | "none"; prop?: "mug" | "paper" | "plant" | "books"; short?: string } | null;
};
// r4 (F-D116): isi membawa alasan (open / SL / TP / exit rule <bot> / daily loss brake / r4 start), bot pemilik posisi, dan pnl yang direalisasi
export type Isi = { aset: string; dari: number; ke: number; harga: number; fee: number; alasan?: string; bot?: string | null; pnl?: number };
// r4 slot posisi terbuka: bobot = notional bertanda / ekuitas, pnl = belum direalisasi, sl/tp = harga (null = bot tanpa stop, mis. B4)
export type Slot = {
  aset: string;
  bot: string;
  arah: number;
  qty: number;
  masuk: number;
  harga: number;
  w: number;
  pnl: number;
  margin: number | null;
  leverage: number | null;
  sl: number | null;
  tp: number | null;
  atr: number | null;
  t: number | null;
};
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
  kursi?: Record<string, "aktif" | "uji" | "antre" | "keluar">;
  params_v2_sha?: string;
  anchor?: string;
  buku: Buku[];
  rekaman: Rekaman[];
  siklus_terakhir: Siklus | null;
  siklus_12?: Siklus[];
  siklus_24j: number;
  komit_24j: number;
  akses?: Akses;
};

// P165: anggota (login Privy + beli >= 1 sinyal dalam 7 hari) melihat isi meja langsung; publik melihat isi keputusan sesudah `tunda_s`
export type Akses = { live: boolean; tunda_s: number; isi_sampai?: number; syarat: string; beli: string; faucet?: string };
const hdr = (token?: string | null): HeadersInit => (token ? { Authorization: `Bearer ${token}` } : {});

export async function desk(token?: string | null): Promise<Desk> {
  const r = await fetch(`${GATE}/desk`, { cache: "no-store", headers: hdr(token) });
  if (!r.ok) throw new Error(`/desk HTTP ${r.status}`);
  return r.json();
}

// P158: rincian satu buku untuk modal lantai /desk (`GET /desk/agent/<nama>`, Gate.meja_agent)
export type AgentDetail = {
  buku: Buku;
  statistik: { siklus_24j: number; ok: number; gagal: number; terlambat: number; siklus_bertransaksi: number; isi_24j: number; biaya_24j: number; bot_pilihan?: Record<string, number> };
  riwayat: { siklus: number; status: string; galat?: string | null; ringkasan?: string | null; bot?: string | null; target: Record<string, Target>; isi: Isi[]; ekuitas: number; hash: string }[];
  model: string | null;
  agent_id: number | null;
  akses?: Akses;
};

export async function agentDetail(name: string, token?: string | null): Promise<AgentDetail> {
  const r = await fetch(`${GATE}/desk/agent/${encodeURIComponent(name)}`, { cache: "no-store", headers: hdr(token) });
  if (!r.ok) throw new Error(`/desk/agent HTTP ${r.status}`);
  return r.json();
}

// P164 Fabius Live Book: seluruh riwayat buku Fabius (`GET /desk/fabius`, Gate.meja_fabius -> meja2.buku_hidup)
export type LiveAgent = { slug: string; status: string; kursi: string | null; bot: string | null };
export type LiveBook = {
  kosong?: boolean;
  mulai: number;
  siklus_terakhir: number;
  modal_awal: number;
  ekuitas: number;
  hasil_pct: number;
  drawdown_maks_pct: number;
  fee: number;
  transaksi: number;
  siklus: number;
  siklus_berposisi: number;
  seri: [number, number][];
  pita: { bot: string; dari: number; sampai: number; n: number }[];
  per_bot: Record<string, { siklus: number; hasil: number; fee: number; isi: number }>;
  pipa: {
    siklus: number;
    rumus: string;
    bot: string | null;
    skor_bot: number | null;
    dasar: string | null;
    instrumen: string[];
    target: Record<string, number>;
    isi: number;
    masuk: string[];
    aktif: string[];
    agen: LiveAgent[];
    root: string | null;
    tx: string | null;
    status: string | null;
    slot?: Slot[] | null;
    maks_slot?: number;
    slot_n?: number; // P165 publik: jumlah slot terbuka (isinya untuk anggota)
    terkunci?: boolean;
  };
  pita_keputusan: { siklus: number; bot: string | null; dasar: string | null; instrumen: string[]; masuk: number; isi: Isi[]; ekuitas: number; hash: string }[];
  akses?: Akses;
};

export async function liveBook(token?: string | null): Promise<LiveBook> {
  const r = await fetch(`${GATE}/desk/fabius`, { cache: "no-store", headers: hdr(token) });
  if (!r.ok) throw new Error(`/desk/fabius HTTP ${r.status}`);
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
