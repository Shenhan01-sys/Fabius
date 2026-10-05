// Meja AI 5 menit (P152, F-D109): data publik dari gerbang `GET /desk` (tools/x402_sinyal.py::Gate.meja_view). Paper saja; tiap siklus satu Merkle
// root keputusan semua agent dikomit ke DeskAnchor selama siklus berjalan.

import { GATE } from "./x402-buy";

export type Target = { w: number; k: number; alasan?: string };
export type Keputusan = { ringkasan: string; target: Record<string, Target>; diubah?: string[]; ditolak?: { aset: string; galat: string }[] };
export type Buku = {
  agent: string;
  nama: string;
  ekuitas: number;
  hasil_pct: number;
  biaya: number;
  n_trade: number;
  posisi: Record<string, number>;
  deret: [number, number][];
  status_terakhir: string | null;
  keputusan_terakhir: Keputusan | null;
};
export type Rekaman = {
  siklus: number;
  agent: string;
  status?: string;
  galat?: string;
  hash: string;
  ekuitas: number;
  keputusan?: Keputusan;
  dasar?: string;
  isi?: { aset: string; dari: number; ke: number; harga: number; fee: number }[];
};
export type Desk = {
  params: { siklus_s: number; fee: number; maks_per_aset: number; maks_gross: number; kuorum: number; ubah_min: number; modal_awal: number; aset: string[] };
  params_sha: string;
  anchor?: string;
  buku: Buku[];
  rekaman: Rekaman[];
  siklus_terakhir: { siklus: number; root: string; tx: string | null; status: string; n: number } | null;
  siklus_24j: number;
  komit_24j: number;
};

export async function desk(): Promise<Desk> {
  const r = await fetch(`${GATE}/desk`, { cache: "no-store" });
  if (!r.ok) throw new Error(`/desk HTTP ${r.status}`);
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
