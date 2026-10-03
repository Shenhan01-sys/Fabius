// Pemeriksaan publik satu (bot, bar) - SATU kode untuk halaman /verify (lewat /api/verify) dan alat MCP `fabius_verify`/`fabius_signals`.
// Leaf + id dihitung ulang dari payload on-chain dengan encoding ABI engine, lalu dicocokkan dengan tick ledger publik. Gagal baca sumber mana pun
// = ChainReadError (T8: gagal baca != tidak ada), tidak pernah vonis.

import type { Hex } from "viem";
import type { Snapshot } from "./snapshot";
import { COMMITTER, LOCK_REGISTRY, SIGNAL_ANCHOR, closeOf, commitIdOf, describe, getCommit, getReveals, ledger, lockedAt, signalHashes, windows } from "./fabius-chain";

export type Verdict = "SAH" | "SEALED_NOT_YET_REVEALED" | "ALARM" | "NO_TICK" | "BEFORE_LOCK" | "BAR_NOT_CLOSED" | "AWAITING_COMMIT" | "NOT_COMMITTED";

export type VerifiedSignal = ReturnType<typeof describe> & {
  signal_id: Hex;
  leaf: Hex;
  salt: Hex;
  leaf_recomputes: boolean;
  in_ledger_tick: boolean;
  tx: Hex | null;
  block: number;
};

export type VerifyResult = {
  bot: string;
  bar: string;
  verdict: Verdict;
  problems: string[];
  tick: { signal_ids: string[]; emitted_utc: string | null; lag_hours: number | null } | null;
  commit: {
    id: Hex;
    committed: boolean;
    committed_utc: string | null;
    lag_hours: number | null;
    root: Hex | null;
    n: number;
    revealed: number;
    silent: boolean;
  };
  signals: VerifiedSignal[];
  contracts: { chain_id: 97; signal_anchor: string; lock_registry: string; committer: string };
  checked_utc: string;
};

const iso = (s: number) => new Date(s * 1000).toISOString().replace(".000", "");
const isZero = (h: string) => /^0x0*$/.test(h);

export function forwardBots(s: Snapshot): string[] {
  return s.bots.filter((b) => b.forward).map((b) => b.id);
}

function specOf(s: Snapshot, bot: string): Hex {
  const spec = s.bots.find((b) => b.id === bot)?.spec_sha as Hex | undefined;
  if (!spec) throw new Error(`unknown bot ${bot}`);
  return spec;
}

/** Komit + ungkap satu (bot, bar) dari SignalAnchor, apa adanya (belum dicocokkan dengan ledger). */
export async function signalsFor(s: Snapshot, bot: string, bar: string) {
  const spec = specOf(s, bot);
  const id = commitIdOf(bot, spec, bar);
  const asof = closeOf(bar);
  const c = await getCommit(id);
  if (!c.exists) {
    const [locked, w] = await Promise.all([lockedAt(bot, spec), windows()]);
    const now = Math.floor(Date.now() / 1000);
    const status: Verdict = locked === 0 || locked > asof ? "BEFORE_LOCK" : now < asof ? "BAR_NOT_CLOSED" : now - asof <= w.maxLag ? "AWAITING_COMMIT" : "NOT_COMMITTED";
    return { id, asof, c, status, reveals: [] as Awaited<ReturnType<typeof getReveals>> };
  }
  const reveals = c.revealed > 0 ? await getReveals(id, Number(c.committedAt), c.revealed) : [];
  return { id, asof, c, status: null, reveals };
}

export async function verifyBar(s: Snapshot, bot: string, bar: string): Promise<VerifyResult> {
  const [recs, r] = await Promise.all([ledger(bot), signalsFor(s, bot, bar)]);
  const tk = recs.find((x) => x.type === "tick" && x.asof_date === bar);
  const ids = tk?.signal_ids ?? [];
  const committed = r.c.exists;
  const base: VerifyResult = {
    bot,
    bar,
    verdict: "NO_TICK",
    problems: [],
    tick: tk ? { signal_ids: ids, emitted_utc: tk.emitted_utc ?? null, lag_hours: tk.lag_s != null ? +(tk.lag_s / 3600).toFixed(2) : null } : null,
    commit: {
      id: r.id,
      committed,
      committed_utc: committed ? iso(Number(r.c.committedAt)) : null,
      lag_hours: committed ? +((Number(r.c.committedAt) - r.asof) / 3600).toFixed(2) : null,
      root: committed ? (r.c.root as Hex) : null,
      n: committed ? r.c.n : 0,
      revealed: committed ? r.c.revealed : 0,
      silent: committed && r.c.n === 0,
    },
    signals: [],
    contracts: { chain_id: 97, signal_anchor: SIGNAL_ANCHOR, lock_registry: LOCK_REGISTRY, committer: COMMITTER },
    checked_utc: new Date().toISOString().replace(/\.\d+Z$/, "Z"),
  };
  if (!committed) return { ...base, verdict: tk ? (r.status as Verdict) : r.status === "BEFORE_LOCK" ? "BEFORE_LOCK" : "NO_TICK" };
  if (!tk) return { ...base, verdict: "NO_TICK", problems: ["commit exists but the public ledger has no tick for this bar"] };
  const lower = ids.map((x) => x.toLowerCase());
  const problems: string[] = [];
  const signals = r.reveals.map((ev) => {
    const h = signalHashes({ botId: r.c.botId as Hex, specSha: r.c.specSha as Hex, asof: r.c.asof }, ev.args);
    const leafOk = h.leaf.toLowerCase() === ev.leaf.toLowerCase();
    const inTick = lower.includes(h.id.toLowerCase());
    const d = describe(ev.args);
    if (!leafOk) problems.push(`leaf of ${d.asset} does not recompute from its payload`);
    if (!inTick) problems.push(`revealed ${d.asset} ${d.action} is not in the ledger tick`);
    return { ...d, signal_id: h.id, leaf: ev.leaf, salt: ev.args.salt, leaf_recomputes: leafOk, in_ledger_tick: inTick, tx: ev.tx, block: ev.block };
  });
  if (r.c.n !== ids.length) problems.push(`commit n=${r.c.n} but the ledger tick has ${ids.length} signals`);
  if (isZero(r.c.root) !== (r.c.n === 0)) problems.push("zero root and n=0 disagree");
  const verdict: Verdict = problems.length ? "ALARM" : r.c.revealed < r.c.n ? "SEALED_NOT_YET_REVEALED" : "SAH";
  return { ...base, verdict, problems, signals };
}
