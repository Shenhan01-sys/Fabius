// Bentuk `public/data/snapshot.json` (dicetak `tools/web_snapshot.py` dari ledger + buku + kunci + chain 97). Tidak ada angka di halaman yang tidak berasal dari sini.

export type Bot = {
  id: string;
  method: string;
  param: string;
  assets: number;
  tier: string;
  spec_sha: string;
  fingerprint: string;
  forward: boolean;
  killer: string;
  universe?: string[];
  kill_rules?: { id: string; rule: string }[];
  status?: "INTI" | "SEMENTARA"; // F-D95: label di luar spesifikasi
  gate_v1?: string; // vonis gerbang v1 tercatat (LOLOS_SHADOW / TOLAK / TIDAK_TERUKUR)
};

export type Tick = { date: string; signals: number; held: number; lag_s: number | null; emitted_utc: string | null };
export type Settle = { date: string; net_bps: number; held: number | null };
export type Gap = { date: string; reason: string | null };

export type BotLedger = {
  genesis: string;
  chain_ok: boolean;
  ticks: Tick[];
  settles: Settle[];
  gaps: Gap[];
  n_signals: number;
  n_settled_days: number;
  n_months: number;
  head: string;
  days_live: number;
  last_closed: string;
};

export type Verdict = { bot: string; bar: string; verdict: string; n: number | null; revealed: number | null; lag_s: number | null };

export type Snapshot = {
  v: number;
  generated_utc: string;
  repo_head: string;
  bots: Bot[];
  ledger: Record<string, BotLedger>;
  book: {
    epoch: number;
    recorded_utc: string;
    capacity: number;
    book_sha: string;
    occupants: { id: string; identity: boolean }[];
    challengers: { id: string; gate: string; shadow_days: number }[];
    decisions: { id: string; action: string; reason: string }[];
    killers: Record<string, string>;
  };
  locks: { label: string; what: string; at_utc: string | null; tx: string | null; where: string }[];
  fd16: { required: { signals: number; days: number; months: number }; bots: Record<string, { signals: number; days: number; months: number }>; lock: string };
  lock_states: Record<string, string>;
  chain: null | {
    id: number;
    block: number;
    block_utc: string;
    signal_anchor: string;
    lock_registry: string;
    decision_anchor: string;
    committer: string;
    commit_count: number;
    lock_count: number;
    verdicts: Verdict[];
    totals: Record<string, number>;
  };
  chain_error?: string;
};

export type CellState = "future" | "prelock" | "pending" | "sealed" | "verified" | "gap" | "missed";

/** Keadaan satu (bot, hari) untuk kalender rekam jejak. Urutan bukti: gap > vonis chain > tick ada > masa depan. */
export function cellState(s: Snapshot, bot: string, date: string): CellState {
  const L = s.ledger[bot];
  if (!L) return "future";
  if (L.gaps.some((g) => g.date === date)) return "gap";
  const v = s.chain?.verdicts.find((x) => x.bot === bot && x.bar === date);
  if (v) {
    if (v.verdict === "SAH") return "verified";
    if (v.verdict === "SEBELUM KUNCI") return "prelock";
    if (v.verdict === "BELUM DIUNGKAP") return "sealed";
    if (v.verdict === "TIDAK DIKOMIT" || v.verdict === "TIDAK DIUNGKAP" || v.verdict === "ALARM") return "missed";
    return "pending";
  }
  if (L.ticks.some((t) => t.date === date)) return "pending";
  return "future";
}

export const short = (h: string | null | undefined, n = 6) => (h ? `${h.slice(0, 2 + n)}…${h.slice(-4)}` : "—");

export function addDays(iso: string, k: number): string {
  const d = new Date(`${iso}T00:00:00Z`);
  d.setUTCDate(d.getUTCDate() + k);
  return d.toISOString().slice(0, 10);
}

/** Jumlah blok kristal hero per keadaan: indigo = komitmen aturan terkunci, putih = sinyal SAH, bening = sisanya. */
export function crystalCounts(s: Snapshot, total = 27) {
  const verified = Math.min(s.chain?.totals?.SAH ?? 0, total);
  const sealed = Math.min(s.locks.length + (s.chain?.totals?.["BELUM DIUNGKAP"] ?? 0), total - verified);
  return { verified, sealed, empty: total - verified - sealed };
}
