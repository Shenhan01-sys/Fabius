// Alat MCP tingkat 0 (P114; F-D70/F-D72): umpan bukti gratis, hanya baca, tanpa kunci. Tingkat 1 (sinyal waktu-nyata berbayar lewat x402) TERKUNCI
// sampai bot lolos uji maju F-D16 + telaah hukum - tidak ada alat untuk itu di sini. Data: snapshot di build + ledger publik (GitHub raw) + chain 97 langsung.
// Gagal membaca sumber mana pun = isError dengan alasannya, tidak pernah daftar kosong (T8: gagal baca != tidak ada).

import type { McpServer } from "@modelcontextprotocol/server";
import { z } from "zod";
import type { Snapshot } from "./snapshot";
import { ChainReadError, COMMITTER, LOCK_REGISTRY, SIGNAL_ANCHOR, commitCount, describe, ledger } from "./fabius-chain";
import { signalsFor as readSignals, verifyBar } from "./verify";
import { getStatus } from "./status";

type Result = { content: { type: "text"; text: string }[]; isError?: boolean };

const X402_GATE = "https://fabius-x402-production.up.railway.app"; // P138a: gerbang x402 per sinyal (Railway fabius-x402)
const X402_FAB = "0xc7b6d5cdbdc881daae0dbcc095d4f184b70ec881"; // Fabius Credit (FAB), deployments/97.json x402_sinyal.token
const ok = (summary: string, data: unknown): Result => ({ content: [{ type: "text", text: `${summary}\n\n${JSON.stringify(data, null, 2)}` }] });
const fail = (e: unknown): Result => ({
  isError: true,
  content: [{ type: "text", text: e instanceof ChainReadError ? e.message : `galat: ${e instanceof Error ? e.message : String(e)}` }],
});
const guard = (f: () => Promise<Result>) => async () => {
  try {
    return await f();
  } catch (e) {
    return fail(e);
  }
};
const iso = (s: number) => new Date(s * 1000).toISOString().replace(".000", "");
const BAR = z
  .string()
  .regex(/^\d{4}-\d{2}-\d{2}$/, "YYYY-MM-DD (UTC date of the daily bar)")
  .refine((v) => {
    const t = Date.parse(`${v}T00:00:00Z`);
    return Number.isFinite(t) && new Date(t).toISOString().startsWith(v);
  }, "not a real calendar date");

const HONESTY = [
  "PAPER ONLY: no real money is traded.",
  "NO EDGE CLAIMED: the forward record started 2026-10-01; the forward test (F-D16: >=20 signals, >=20 settled days, >=2 months, CI lower bound > 0, BH across bots) is not met.",
  "Tier 0 (this server): proof feed, free. Tier 1 (real-time paid signals via x402): LOCKED until a bot passes F-D16 AND a legal review.",
  "Signals are position INTENTS (enter / exit / resize), not orders, not leverage advice.",
];

export function registerFabiusTools(server: McpServer, s: Snapshot) {
  const forward = s.bots.filter((b) => b.forward).map((b) => b.id);
  const BOT = z.enum(s.bots.map((b) => b.id) as [string, ...string[]]);

  // Satu pembaca untuk MCP dan halaman /verify (lib/verify.ts); bentuk keluaran MCP dipertahankan untuk klien yang sudah ada.
  async function signalsFor(bot: string, bar: string) {
    const r = await readSignals(s, bot, bar);
    if (!r.c.exists) {
      return { bot, bar, commit_id: r.id, status: r.status as string, committed: false, note: "no on-chain commit for this (bot, bar) under the official committer" };
    }
    return {
      bot,
      bar,
      commit_id: r.id,
      committed: true,
      committed_utc: iso(Number(r.c.committedAt)),
      commit_lag_hours: +((Number(r.c.committedAt) - r.asof) / 3600).toFixed(2),
      root: r.c.root,
      n: r.c.n,
      revealed: r.c.revealed,
      silent: r.c.n === 0,
      signals: r.reveals.map((x) => ({ ...describe(x.args), leaf: x.leaf, salt: x.args.salt, tx: x.tx, block: x.block })),
    };
  }

  server.registerTool(
    "fabius_overview",
    {
      title: "Fabius: what this is",
      description:
        "Start here. Fabius runs locked trading bots and commits every signal on BNB Chain testnet (97) BEFORE the outcome; anyone can verify. Returns the honesty boundaries, tiers, contracts, snapshot time and which tools to call next.",
      inputSchema: z.object({}),
    },
    guard(async () =>
      ok("Fabius - signals sealed before the outcome (tier 0 proof feed).", {
        honesty: HONESTY,
        bots_with_forward_clock: forward,
        contracts: { chain_id: 97, SignalAnchor: SIGNAL_ANCHOR, LockRegistry: LOCK_REGISTRY, DecisionAnchor: s.chain?.decision_anchor ?? null, official_committer: COMMITTER },
        how_signals_work: "bar closes 00:00 UTC -> bot computes intents -> salted Merkle root committed to SignalAnchor within 12 h -> payloads revealed -> anyone recomputes them from public bars",
        tools: {
          fabius_latest_signals: "latest committed signals for each bot, read live from chain",
          fabius_signals: "signals of one (bot, bar), live from chain",
          fabius_verify: "full public check of one (bot, bar): leaves recomputed from revealed payloads and matched to the public ledger tick",
          fabius_track_record: "forward ledger of one bot (ticks, settles, gaps) + forward-test progress",
          fabius_proof_feed: "verdict per (bot, bar) as of the build snapshot",
          fabius_list_bots: "the six bot specifications and the slot book",
          fabius_locks: "rules locked on-chain before the data, in order",
          fabius_status: "operations health today: tick, commit, reveal, venue-rules paper, gas, GitHub chain heartbeat (health, not performance)",
          fabius_confidence: "free teaser per bot: confidence from the forward record (1 - p of the locked F-D16 bootstrap) and why - never assets, direction or size",
          fabius_analysts: "which bot Fabius trades now (locked rule over AI analyst agents' on-chain picks), today's picks with reasons, and the analyst leaderboard",
          fabius_signal_offer: "buy one bot's latest signal package with x402 (testnet 97, FAB token, zero gas for the buyer): live price, teaser, pay URL and how to pay",
        },
        verify_yourself: ["git clone https://github.com/Shenhan01-sys/Fabius", "python -X utf8 tools/verify_signals.py", "python -X utf8 -m engine.cli ledger verify"],
        snapshot_utc: s.generated_utc,
      }),
    ),
  );

  server.registerTool(
    "fabius_analysts",
    {
      title: "Analyst agents: active bot, picks, leaderboard",
      description:
        "Fabius analyst agents (ERC-8004 identities; today GLM 5.3 = agent 2558 and Qwen 3.8 Flash = agent 2559) each pick ONE locked bot per daily bar; picks are committed to SelectionAnchor on BNB testnet before the bar closes and scored later from the public paper ledger (excess vs the identity bot; provisional until Binance's monthly funding file, then final), with ERC-8004 reputation feedback. The active bot (what /buy sells) follows a rule locked before any scored pick (engine/pemilih.py). Agents never invent trades.",
      inputSchema: z.object({}),
    },
    guard(async () => {
      const [ak, picks, board] = await Promise.all(
        [`${X402_GATE}/aktif`, `${X402_GATE}/analis`, `${X402_GATE}/analis/skor`].map(async (u) => {
          const r = await fetch(u, { next: { revalidate: 120 } });
          if (!r.ok) throw new Error(`analyst endpoint HTTP ${r.status}`);
          return r.json();
        }),
      );
      return ok(`Active bot: ${(ak as { bot: string }).bot}`, { active: ak, latest_picks: picks, leaderboard: (board as { papan: unknown }).papan, selection_anchor: (picks as { selection_anchor: string }).selection_anchor });
    }),
  );

  server.registerTool(
    "fabius_signal_offer",
    {
      title: "Offer: buy one bot's latest signal package (x402, testnet)",
      description:
        "Live from the x402 gate: the price of the latest (bot, bar) signal package in FAB (Fabius Credit, BNB testnet 97, no value), the free teaser, and the paid URL. Pay with x402 v2 `exact` (Permit2 + EIP-2612 gas sponsoring: the buyer signs two messages and pays no gas). Price comes from the locked table in engine/harga.py (from forward confidence). What you buy is delivery + proof (intents, commit, ERC-8004 validation), not a secret: the bots are deterministic and open.",
      inputSchema: z.object({ bot: BOT }),
    },
    async ({ bot }) => {
      try {
        const res = await fetch(`${X402_GATE}/teaser/${bot}`, { next: { revalidate: 60 } });
        if (!res.ok) return fail(`x402 gate answered HTTP ${res.status} for ${bot}`);
        const t = (await res.json()) as { teaser: unknown; harga: { bar: string; atomic: number; fab: number; alasan: string } };
        return ok(`${bot} bar ${t.harga.bar}: ${t.harga.fab} FAB via x402 at ${X402_GATE}/sinyal/${bot}`, {
          price: t.harga,
          teaser: t.teaser,
          pay_url: `${X402_GATE}/sinyal/${bot}/${t.harga.bar}`,
          how_to_pay: "GET pay_url -> 402 with PAYMENT-REQUIRED (x402 v2, scheme exact, asset FAB, extra.name 'Fabius Credit') -> sign Permit2 witness + EIP-2612 permit for exactly that amount -> repeat GET with PAYMENT-SIGNATURE. Reference client: tools/x402_client.py",
          get_test_tokens: `POST ${X402_GATE}/faucet {"address": "0x..."} (FAB sent to you; you need no tBNB)`,
          token: { symbol: "FAB", address: X402_FAB, decimals: 6, network: "eip155:97" },
        });
      } catch (e) {
        return fail(e);
      }
    },
  );

  server.registerTool(
    "fabius_confidence",
    {
      title: "Confidence teaser of one bot (free)",
      description:
        "What a buyer may see before paying for a signal: confidence = 1 - p of the locked F-D16 block bootstrap on the bot's forward settles (how sure the forward record is that the mean net daily return is above zero - NOT the chance today's signal is right), its maturity toward the F-D16 thresholds, status and gate verdict. Never contains assets, direction, size or signal ids.",
      inputSchema: z.object({ bot: BOT }),
    },
    async ({ bot }) => {
      const c = s.confidence?.[bot];
      if (!c) return fail(`no confidence teaser for ${bot} in the build snapshot (bot without a forward clock, or snapshot older than P137)`);
      const head = c.confidence_pct == null ? `${bot}: not measured yet (${c.kematangan.hari[0]} settled forward days; needs >= 2 for any number)` : `${bot}: ${c.confidence_pct}% (${c.label})`;
      return ok(head, { ...c, snapshot_utc: s.generated_utc });
    },
  );

  server.registerTool(
    "fabius_list_bots",
    {
      title: "Bot specifications and slot book",
      description: "The six locked bot specifications (one method, one parameter each, spec hash), which ones run a forward clock, and the current slot book (occupants, challengers).",
      inputSchema: z.object({}),
    },
    guard(async () =>
      ok(`${s.bots.length} specifications; forward clock: ${forward.join(", ")}.`, {
        bots: s.bots.map((b) => ({ id: b.id, method: b.method, parameter: b.param, assets: b.assets, tier: b.tier, spec_sha: b.spec_sha, forward_clock: b.forward, kill_rule_text: b.killer, status: b.status ?? null, gate_v1: b.gate_v1 ?? null })),
        book: s.book,
        snapshot_utc: s.generated_utc,
      }),
    ),
  );

  server.registerTool(
    "fabius_track_record",
    {
      title: "Forward track record of one bot",
      description:
        "Live from the public hash-chained ledger: every daily tick (bar, number of signals, lag after close), every final settle (net bps, paper), gaps (unmeasured days are NOT zero) and progress toward the forward test F-D16.",
      inputSchema: z.object({ bot: BOT }),
    },
    async ({ bot }) => {
      try {
        const recs = await ledger(bot);
        const g = recs.find((r) => r.type === "genesis");
        const ticks = recs.filter((r) => r.type === "tick").map((r) => ({ bar: r.asof_date, signals: r.signal_ids?.length ?? 0, lag_hours: r.lag_s != null ? +(r.lag_s / 3600).toFixed(2) : null, emitted_utc: r.emitted_utc }));
        const settles = recs.filter((r) => r.type === "settle").map((r) => ({ bar: r.bar_date, net_bps: r.net != null ? +(r.net * 1e4).toFixed(2) : null }));
        const gaps = recs.filter((r) => r.type === "gap").map((r) => ({ bar: r.asof_date, reason: r.reason }));
        const months = new Set(settles.map((x) => String(x.bar).slice(0, 7))).size;
        const signals = ticks.reduce((a, t) => a + t.signals, 0);
        const req = s.fd16.required;
        return ok(`${bot}: ${ticks.length} ticks, ${signals} forward signals, ${settles.length} settled days, ${gaps.length} gaps. Paper only; not an edge claim.`, {
          bot,
          forward_clock_started: g?.first_asof_date ?? null,
          ticks,
          settles,
          gaps,
          forward_test_F_D16: { signals: `${signals}/${req.signals}`, settled_days: `${settles.length}/${req.days}`, months: `${months}/${req.months}`, met: false },
          note: "final settles wait for Binance's monthly funding file; provisional numbers are not published as results",
        });
      } catch (e) {
        return fail(e);
      }
    },
  );

  server.registerTool(
    "fabius_proof_feed",
    {
      title: "Proof feed (build snapshot)",
      description: "Verdict per (bot, bar) from the public verifier at build time: SAH (verified), BELUM DIUNGKAP (sealed), MENUNGGU KOMIT, TIDAK DIKOMIT, SEBELUM KUNCI, ALARM. For a live check call fabius_verify.",
      inputSchema: z.object({}),
    },
    guard(async () => {
      if (!s.chain) return fail(new ChainReadError(`snapshot has no chain section (${s.chain_error ?? "not read at build"}) - call fabius_verify for a live check`));
      return ok(`${s.chain.totals.SAH ?? 0} verified (SAH), ${s.chain.totals.ALARM ?? 0} alarms, ${s.chain.commit_count} commits as of block ${s.chain.block}.`, {
        verdicts: s.chain.verdicts,
        totals: s.chain.totals,
        block: s.chain.block,
        block_utc: s.chain.block_utc,
        snapshot_utc: s.generated_utc,
      });
    }),
  );

  server.registerTool(
    "fabius_locks",
    {
      title: "Rules locked on-chain",
      description: "Everything Fabius fixed on-chain BEFORE the forward data existed (gate thresholds, bot specs, forward-test rules, slot book, kill rules, gate error budget), with timestamps and transactions.",
      inputSchema: z.object({}),
    },
    guard(async () => ok(`${s.locks.length} locks, oldest first.`, { locks: s.locks.map((l) => ({ ...l, explorer: l.tx ? `https://testnet.bscscan.com/tx/${l.tx}` : null })), states: s.lock_states })),
  );

  server.registerTool(
    "fabius_signals",
    {
      title: "Signals of one bot on one bar (live)",
      description: "Reads SignalAnchor on chain 97: the commit for (bot, bar) under the official committer, and every revealed signal (asset, action, weight before/after, reference price, salt, leaf, tx). A silent bot commits a zero root.",
      inputSchema: z.object({ bot: BOT, bar: BAR }),
    },
    async ({ bot, bar }) => {
      try {
        const r = await signalsFor(bot, bar);
        const line = r.committed ? `${bot} ${bar}: committed ${"committed_utc" in r ? r.committed_utc : ""}, ${"revealed" in r ? r.revealed : 0}/${"n" in r ? r.n : 0} revealed.` : `${bot} ${bar}: ${r.status}.`;
        return ok(line, r);
      } catch (e) {
        return fail(e);
      }
    },
  );

  server.registerTool(
    "fabius_latest_signals",
    {
      title: "Latest signals (live)",
      description: "For every bot with a forward clock: its latest ledger tick and the matching on-chain commit + revealed signals. The usual entry point for an agent following Fabius (paper; intents, not orders).",
      inputSchema: z.object({}),
    },
    guard(async () => {
      const out = [];
      for (const bot of forward) {
        const recs = await ledger(bot);
        const last = [...recs].reverse().find((r) => r.type === "tick");
        if (!last?.asof_date) {
          out.push({ bot, status: "NO_TICK_YET" });
          continue;
        }
        out.push(await signalsFor(bot, last.asof_date));
      }
      return ok(`Latest bar per bot: ${out.map((x) => `${x.bot} ${"bar" in x ? x.bar : "-"}`).join(", ")}. Total commits on chain: ${await commitCount()}.`, { latest: out });
    }),
  );

  server.registerTool(
    "fabius_verify",
    {
      title: "Verify one bot/bar publicly (live)",
      description:
        "Independent check, no key: recomputes every revealed leaf and signal id from its on-chain payload with the engine's ABI encoding, and matches the ids to the public ledger tick for that bar. Verdict SAH only if counts, leaves and ids all agree.",
      inputSchema: z.object({ bot: BOT, bar: BAR }),
    },
    async ({ bot, bar }) => {
      try {
        const v = await verifyBar(s, bot, bar);
        if (v.verdict === "NO_TICK") return ok(`${bot} ${bar}: no ledger tick - nothing to verify.`, { bot, bar, verdict: "NO_TICK", problems: v.problems });
        if (!v.commit.committed) return ok(`${bot} ${bar}: ${v.verdict}.`, { bot, bar, verdict: v.verdict, ledger_signals: v.tick?.signal_ids.length ?? 0 });
        return ok(`${bot} ${bar}: ${v.verdict}${v.problems.length ? ` - ${v.problems.join("; ")}` : ` (${v.commit.revealed}/${v.commit.n} revealed, all ids match the ledger)`}.`, {
          bot,
          bar,
          verdict: v.verdict,
          problems: v.problems,
          commit: { id: v.commit.id, root: v.commit.root, n: v.commit.n, revealed: v.commit.revealed, committed_utc: v.commit.committed_utc },
          signals: v.signals,
          ledger_tick: { signal_ids: v.tick?.signal_ids ?? [], emitted_utc: v.tick?.emitted_utc ?? null },
        });
      } catch (e) {
        return fail(e);
      }
    },
  );

  server.registerTool(
    "fabius_status",
    {
      title: "Operations health today (live)",
      description:
        "Is the machine alive today? For the last closed daily bar and each bot with a forward clock: ledger tick (GitHub chain), on-chain commit and reveal (Railway worker), venue-rules paper (kertas), demo execution (private). Plus committer gas, chain head and the GitHub chain heartbeat. Lamps: ok / wait (with reason) / alarm / unreadable (a failed read, never a verdict) / private / na. Health, not performance.",
      inputSchema: z.object({}),
    },
    guard(async () => {
      const r = await getStatus(s);
      const lines = r.bots.map((b) => `${b.bot} bar ${b.bar}: ${b.stations.map((x) => `${x.k} ${x.lamp}`).join(", ")}`);
      return ok(`Overall ${r.overall.toUpperCase()} at ${r.checked_utc}. ${lines.join(" | ")}.`, r);
    }),
  );
}
