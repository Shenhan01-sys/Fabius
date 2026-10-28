// Tur juri (P178): satu (bot, bar) diikuti dari awal sampai akhir - kunci strategi -> bar tutup -> komit -> ungkap -> periksa.
// Tiap langkah = waktu + tx on-chain yang dibaca dari event-nya sendiri; urutan waktu dicek di sini, bukan diklaim. Gagal baca = ChainReadError (T8).

import type { Hex } from "viem";
import type { Snapshot } from "./snapshot";
import { closeOf, commitTxOf, lockTxOf, lockedAt, windows } from "./fabius-chain";
import { specOf, verifyBar, type VerifyResult } from "./verify";

export const TOUR = { bot: "B2-RS", bar: "2026-10-05" };

export type TourResult = {
  bot: string;
  bar: string;
  spec_sha: Hex;
  lock: { at_utc: string; tx: Hex; block: number };
  close: { at_utc: string };
  commit: { at_utc: string; tx: Hex; block: number; lag_hours: number; max_lag_hours: number; root: Hex; n: number } | null;
  reveals: { asset: string; action: string; tx: Hex | null; block: number; leaf_recomputes: boolean; in_ledger_tick: boolean }[];
  order: { lock_before_close: boolean; commit_after_close: boolean; commit_within_lag: boolean; reveal_after_commit: boolean };
  verify: Pick<VerifyResult, "verdict" | "problems" | "tick">;
  contracts: VerifyResult["contracts"];
  checked_utc: string;
};

const iso = (s: number) => new Date(s * 1000).toISOString().replace(".000", "");

export async function buildTour(s: Snapshot, bot: string, bar: string): Promise<TourResult> {
  const spec = specOf(s, bot);
  const asof = closeOf(bar);
  const [locked, v, w] = await Promise.all([lockedAt(bot, spec), verifyBar(s, bot, bar), windows()]);
  const committedAt = v.commit.committed_utc ? Math.floor(Date.parse(v.commit.committed_utc) / 1000) : null;
  const [lockTx, commitTx] = await Promise.all([lockTxOf(bot, spec, locked), committedAt ? commitTxOf(v.commit.id, committedAt) : Promise.resolve(null)]);
  const reveals = v.signals.map((x) => ({ asset: x.asset, action: x.action, tx: x.tx, block: x.block, leaf_recomputes: x.leaf_recomputes, in_ledger_tick: x.in_ledger_tick }));
  return {
    bot,
    bar,
    spec_sha: spec,
    lock: { at_utc: iso(locked), ...lockTx },
    close: { at_utc: iso(asof) },
    commit:
      committedAt && commitTx
        ? { at_utc: iso(committedAt), ...commitTx, lag_hours: v.commit.lag_hours ?? 0, max_lag_hours: w.maxLag / 3600, root: v.commit.root as Hex, n: v.commit.n }
        : null,
    reveals,
    order: {
      lock_before_close: locked > 0 && locked <= asof,
      commit_after_close: committedAt != null && committedAt >= asof,
      commit_within_lag: committedAt != null && committedAt - asof <= w.maxLag,
      reveal_after_commit: commitTx != null && reveals.every((r) => r.block >= commitTx.block),
    },
    verify: { verdict: v.verdict, problems: v.problems, tick: v.tick },
    contracts: v.contracts,
    checked_utc: new Date().toISOString().replace(/\.\d+Z$/, "Z"),
  };
}
