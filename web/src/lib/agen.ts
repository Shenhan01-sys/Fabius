// P169 (F-D123): pendaftaran agent luar di halaman sendiri (/submit-agent). Semua yang tampil (aturan, batas, bentuk pesan, daftar agent) dibaca dari gerbang
// (`GET /desk/external`, sumbernya tools/agen_luar.py) supaya web tidak menyalin teks pesan atau angka batas dan tidak menyimpang.
import { GATE } from "./x402-buy";

export type Seat = "aktif" | "uji" | "antre" | "keluar" | null;

export type AgenRow = {
  slug: string;
  agent_id: number;
  name: string;
  since: number;
  seat: Seat;
  removed_for_failures: boolean;
  answers_observed: number | null;
  valid_pct: number | null;
  online: boolean;
};

export type ExternalInfo = {
  what: string;
  params: {
    maks_terdaftar: number;
    join_per_jam: number;
    join_ttl_s: number;
    hadir_s: number;
    jawaban_maks_byte: number;
    tarik_ttl_s: number;
    percobaan_per_siklus: number;
  };
  params_sha: string;
  endpoints: Record<string, string>;
  sign: { scheme: string; signer: string; formats?: { join: string; pull: string; answer: string } };
  seats: string;
  deadline: string;
  agents: AgenRow[];
};

export async function externalInfo(): Promise<ExternalInfo> {
  const r = await fetch(`${GATE}/desk/external`, { cache: "no-store" });
  if (!r.ok) throw new Error(`/desk/external HTTP ${r.status}`);
  return r.json();
}

export type JoinReply = { ok: boolean; status: number; body: Record<string, unknown> };

export async function joinAgent(agentId: number, deadline: number, signature: string): Promise<JoinReply> {
  const r = await fetch(`${GATE}/desk/external/join`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ agent_id: agentId, deadline, signature }),
  });
  return { ok: r.ok, status: r.status, body: await r.json().catch(() => ({})) };
}

/** Isi bentuk pesan dari gerbang (`sign.formats.join`) - tempat pengganti `{agent_id}` dan `{deadline}`. */
export const joinMessage = (format: string, agentId: number, deadline: number) => format.replace("{agent_id}", String(agentId)).replace("{deadline}", String(deadline));
