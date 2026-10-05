// Agent analis (P141-P145, F-D102/F-D104): pilihan bot per bar dari gerbang x402 (tools/x402_sinyal.py). Bagian publik = bot, keyakinan agent,
// reasonHash, tx (semuanya on-chain); alasan bar yang belum tutup tersegel. Alasan lengkap = /analis/lengkap dengan token akses Privy,
// hanya untuk akun yang membeli >= 1 sinyal dalam 7 hari terakhir (gerbang memeriksa token + catatan pembelian).

import { GATE } from "./x402-buy";

export type Pilihan = { bot: string; keyakinan: number; alasan: string; risiko?: string };
export type AnalisRec = {
  agent: string;
  bot: string;
  keyakinan: number;
  reasonHash: string;
  status?: string;
  tx?: string;
  alasan: {
    agent_id: number;
    nama: string;
    model?: string;
    penyedia?: string;
    effort?: string;
    bar_close: number;
    dibuat_utc?: string;
    terkunci?: string;
    pilihan?: Pilihan;
    masukan_sha256?: string;
    prompt_sha256?: string;
    jawaban_mentah_sha256?: string;
  };
};
export type PapanRow = { agent: string; agent_id: number; pilihan: number; terskor: number; final: number; jumlah_selisih_bps: number; rata_selisih_bps: number | null };
export type Aktif = { bot: string; alasan_en?: string; bar_close: number | null };
export type Publik = { aktif: Aktif; barClose: number | null; pilihan: AnalisRec[]; papan: PapanRow[]; anchor?: string };
export type Akses = { dompet: string; pembelian_terakhir: { t: number; bot: string; bar: string; tx: string }; berlaku_sampai: number };
export type Lengkap =
  | { ok: true; pilihan: AnalisRec[]; papan: PapanRow[]; akses: Akses; anchor?: string }
  | { ok: false; status: number; error: string; beli?: string };

const get = async (path: string) => {
  const r = await fetch(`${GATE}${path}`, { cache: "no-store" });
  if (!r.ok) throw new Error(`${path}: HTTP ${r.status}`);
  return r.json();
};

export async function publik(): Promise<Publik> {
  const [ak, an, sk] = await Promise.all([get("/aktif"), get("/analis"), get("/analis/skor")]);
  return { aktif: ak, barClose: an.bar_close ?? null, pilihan: an.pilihan ?? [], papan: sk.papan ?? [], anchor: an.selection_anchor };
}

export async function lengkap(accessToken: string): Promise<Lengkap> {
  const r = await fetch(`${GATE}/analis/lengkap`, { headers: { Authorization: `Bearer ${accessToken}` }, cache: "no-store" });
  const b = await r.json().catch(() => ({}));
  if (!r.ok) return { ok: false, status: r.status, error: String(b.error ?? `HTTP ${r.status}`), beli: b.beli };
  return { ok: true, pilihan: b.pilihan ?? [], papan: b.papan ?? [], akses: b.akses, anchor: b.selection_anchor };
}

export const utc = (s: number) => new Date(s * 1000).toISOString().slice(0, 16).replace("T", " ") + " UTC";
export const short = (h?: string) => (h ? `${h.slice(0, 10)}…${h.slice(-6)}` : "-");
