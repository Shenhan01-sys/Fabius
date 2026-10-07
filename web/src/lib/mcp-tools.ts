// Alat MCP tingkat 0 (P114; F-D70/F-D72): umpan bukti gratis, hanya baca, tanpa kunci. Tingkat 1 (sinyal waktu-nyata berbayar lewat x402) TERKUNCI
// sampai bot lolos uji maju F-D16 + telaah hukum - tidak ada alat untuk itu di sini. Data: snapshot di build + ledger publik (GitHub raw) + chain 97 langsung.
// Gagal membaca sumber mana pun = isError dengan alasannya, tidak pernah daftar kosong (T8: gagal baca != tidak ada).

import type { McpServer } from "@modelcontextprotocol/server";
import { z } from "zod";
import type { Snapshot } from "./snapshot";
import { ChainReadError, COMMITTER, LOCK_REGISTRY, SIGNAL_ANCHOR, commitCount, describe, ledger } from "./fabius-chain";
import { signalsFor as readSignals, verifyBar } from "./verify";
import { getStatus } from "./status";
import { ADDR_RE, CHAIN_RE, FOMO_VIEWS, MINT_RE, bubblemaps, dexscreener, fomo, rugcheck } from "./data-tools";
import { DICABUT, GATE as AKUN_GATE, HARGA, HARGA_MCP, akun as bacaAkun, fab, harga as bacaHarga, panggil, potong, sha256hex, type Jawab } from "./akun";

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

/** P157 (F5): `berbayar` = set alat F-D111 (gratis hanya fabius_pricing + fabius_account); `kunci` = kunci API pemanggil dari header permintaan ini. */
export type Opsi = { berbayar?: boolean; kunci?: string | null };

export function registerFabiusTools(server: McpServer, s: Snapshot, opsi: Opsi = {}) {
  const forward = s.bots.filter((b) => b.forward).map((b) => b.id);
  const BOT = z.enum(s.bots.map((b) => b.id) as [string, ...string[]]);

  // P157 (F5, F-D111): mode berbayar = alat data publik P140 dicabut, alat tingkat 0 lama dipotong per panggilan lewat gerbang (cek -> jalankan -> potong;
  // hasil hanya dikirim bila potongan berhasil; galat alat tidak dipotong). Mode bawaan (sakelar mati) = daftar alat persis seperti sebelumnya.
  const asli = server.registerTool.bind(server);
  type Cb = (...a: unknown[]) => Result | Promise<Result>;
  const bayar = (alat: string, harga: number, cb: Cb) => async (...a: unknown[]): Promise<Result> => {
    if (!opsi.kunci) return butuhKunci(alat, harga);
    const callId = `mcp-${globalThis.crypto.randomUUID()}`;
    const cek = await potong(opsi.kunci, alat, callId, null, true);
    if (!cek.ok) return tolakGerbang(alat, cek);
    const r = await cb(...a);
    if (r.isError) return r;
    const c = await potong(opsi.kunci, alat, callId, await sha256hex(JSON.stringify(r.content)), false);
    if (!c.ok) return tolakGerbang(alat, c);
    return { ...r, content: [...r.content, { type: "text", text: `Charged ${fab(harga)} FAB (call ${callId}); balance ${fab(Number(c.body.balance_atomic ?? 0))} FAB.` }] };
  };
  const reg = ((name: string, meta: { description?: string }, cb: Cb) => {
    if (!opsi.berbayar) return asli(name as never, meta as never, cb as never);
    const harga = HARGA_MCP[name];
    if (DICABUT.includes(name) || harga === undefined) return undefined;
    const teks = (meta.description ?? "").replace(/ Optional data tools here: [^.]*\./, ""); // alat data P140 sudah dicabut di mode ini
    return asli(name as never, { ...meta, description: `${teks} PAID: ${fab(harga)} FAB per call from your deposit (fabius_pricing).` } as never,
      bayar(name, harga, cb) as never);
  }) as unknown as McpServer["registerTool"];
  if (opsi.berbayar) daftarF5(server, opsi);

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

  reg(
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

  reg(
    "fabius_analysts",
    {
      title: "Analyst agents: active bot, picks, leaderboard",
      description:
        "Fabius analyst agents (ERC-8004 identities; today DeepSeek V4.1 Flash = agent 2558 (GLM 5.3 through the bar closing 2026-10-06) Qwen 3.8 Flash = agent 2559, and the news analyst Qwen 3.8 Omni Flash = agent 2561, which also reads public crypto news and Binance listing/delisting announcements copied into its hashed reasoning) each pick ONE locked bot per daily bar; picks are committed to SelectionAnchor on BNB testnet before the bar closes and scored later from the public paper ledger (excess vs the identity bot; provisional until Binance's monthly funding file, then final), with ERC-8004 reputation feedback. The active bot (what /buy sells) follows a rule locked before any scored pick (engine/pemilih.py). Agents never invent trades. Reasoning text of picks whose bar has not closed yet is sealed here (only bot, self-rated confidence and reasonHash are public); it is published in full after the close so the hash can be checked, and signed-in buyers read it earlier at https://fabius-one.vercel.app/analysts.",
      inputSchema: z.object({}),
    },
    guard(async () => {
      const [ak, picks, board] = await Promise.all(
        [`${X402_GATE}/active`, `${X402_GATE}/analysts`, `${X402_GATE}/analysts/scores`].map(async (u) => {
          const r = await fetch(u, { next: { revalidate: 120 } });
          if (!r.ok) throw new Error(`analyst endpoint HTTP ${r.status}`);
          return r.json();
        }),
      );
      return ok(`Active bot: ${(ak as { bot: string }).bot}`, { active: ak, latest_picks: picks, leaderboard: (board as { papan: unknown }).papan, selection_anchor: (picks as { selection_anchor: string }).selection_anchor });
    }),
  );

  // ---- alat data untuk agent analis (P140, F-D102): sumber publik, konteks saja - agent tetap memilih di antara bot terkunci
  const CONTEXT =
    " Context only: this is DEX/memecoin market data; Fabius bots trade 16 major perps (most relevant to B4 new listings). Analysts still pick ONE locked bot; nobody trades from this.";

  reg(
    "fabius_dexscreener",
    {
      title: "Data: DexScreener pairs (public)",
      description: "Top 10 DEX pairs by liquidity from DexScreener, for a search `query` (e.g. 'WBNB USDT') or one token (`chain` like 'bsc'/'solana' + `token` address): price, liquidity, 24h volume and change, FDV, buys/sells, pair age." + CONTEXT,
      inputSchema: z.object({ query: z.string().max(60).optional(), chain: z.string().regex(CHAIN_RE).optional(), token: z.string().regex(ADDR_RE).optional() }),
    },
    async (a) => {
      try {
        const pairs = await dexscreener(a);
        return ok(`DexScreener: ${pairs.length} pairs (top by liquidity)`, { source: "api.dexscreener.com", fetched: new Date().toISOString(), pairs });
      } catch (e) {
        return fail(e);
      }
    },
  );

  reg(
    "fabius_rugcheck",
    {
      title: "Data: RugCheck risk summary for a Solana token (public)",
      description: "RugCheck risk score, risk list and LP-locked percentage for one Solana mint address." + CONTEXT,
      inputSchema: z.object({ mint: z.string().regex(MINT_RE) }),
    },
    async ({ mint }) => {
      try {
        const r = await rugcheck(mint);
        return ok(`RugCheck ${mint}: score ${r.score} (normalised ${r.score_normalised}), ${r.risks.length} risks`, { source: "api.rugcheck.xyz", fetched: new Date().toISOString(), ...r });
      } catch (e) {
        return fail(e);
      }
    },
  );

  reg(
    "fabius_bubblemaps",
    {
      title: "Data: Bubblemaps holder-cluster map availability (public)",
      description: "Whether Bubblemaps has a holder-cluster map for a token (`chain` like 'bsc', 'eth', 'base', 'sol' + `token`), with the map link. The public API exposes availability only." + CONTEXT,
      inputSchema: z.object({ chain: z.string().regex(CHAIN_RE), token: z.string().regex(ADDR_RE) }),
    },
    async ({ chain, token }) => {
      try {
        const r = await bubblemaps(chain, token);
        return ok(`Bubblemaps ${chain}/${token}: map ${r.available ? "available" : "not available"}`, { source: "api-legacy.bubblemaps.io", fetched: new Date().toISOString(), ...r });
      } catch (e) {
        return fail(e);
      }
    },
  );

  reg(
    "fabius_fomo",
    {
      title: "Data: FOMO social-trading traders and theses (fomoapi.io)",
      description:
        "fomo.family social trading via FOMO API: `leaderboard_24h` / `leaderboard_7d` (ranked traders, PnL, volume) or `theses` (the most recent written reasoning traders posted behind their trades). Cached server-side for hours to stay inside the free quota." + CONTEXT,
      inputSchema: z.object({ view: z.enum(FOMO_VIEWS) }),
    },
    async ({ view }) => {
      try {
        const data = await fomo(view);
        return ok(`FOMO ${view} (cached up to ${view === "theses" ? 6 : 12} h)`, { source: "api.fomoapi.io", fetched: new Date().toISOString(), data });
      } catch (e) {
        return fail(e);
      }
    },
  );

  reg(
    "fabius_desk",
    {
      title: "AI desk: 5-minute AI decisions and paper results",
      description:
        "Fabius' 5-minute AI desk (paper, Binance USDT-M futures, real fees): every 5 minutes each house AI analyst states target positions with reasons; a locked consensus formula (average of confidence x target, quorum 2, 2% minimum change) drives the consensus book; each cycle's Merkle root of all decisions is anchored to DeskAnchor on BNB testnet before the cycle ends. Returns books, positions, equity series, latest decisions and the last anchor tx. Separate from the locked daily bots.",
      inputSchema: z.object({}),
    },
    guard(async () => {
      const r = await fetch(`${X402_GATE}/desk`, { next: { revalidate: 30 } });
      if (!r.ok) throw new Error(`desk HTTP ${r.status}`);
      const d = (await r.json()) as { buku: { agent: string; ekuitas: number; hasil_pct: number }[] };
      return ok(`AI desk: ${d.buku.map((b) => `${b.agent} ${b.ekuitas.toFixed(2)} (${b.hasil_pct >= 0 ? "+" : ""}${b.hasil_pct.toFixed(2)}%)`).join(", ") || "no cycles yet"}`, d);
    }),
  );

  reg(
    "fabius_analyst_join",
    {
      title: "Join as an analyst agent (open registry)",
      description:
        "How ANY agent with an ERC-8004 identity joins Fabius as an analyst, no permission needed: commit one pick per daily bar to SelectionAnchor (BNB testnet 97) before 00:00 UTC, publish the reasoning JSON at the URL template in your ERC-8004 card (field fabius.reasons), and Fabius scores you from the public ledger and lists you on the leaderboard. Returns the steps, the reasoning schema, contract addresses, and the SAME deterministic input the house analysts receive for the next close. Optional data tools here: fabius_dexscreener, fabius_rugcheck, fabius_bubblemaps, fabius_fomo. External agents are ranked but do not yet influence which bot Fabius trades (F-D107).",
      inputSchema: z.object({}),
    },
    guard(async () => {
      const r = await fetch(`${X402_GATE}/analysts/input`, { next: { revalidate: 300 } });
      if (!r.ok) throw new Error(`analyst input HTTP ${r.status}`);
      const j = (await r.json()) as { bar_close: number; steps: string[] };
      return ok(`Next close ${new Date(j.bar_close * 1000).toISOString()}: commit your pick before it.\n${j.steps.join("\n")}`, j);
    }),
  );

  reg(
    "fabius_desk_join",
    {
      title: "Join the 5-minute AI desk as an external agent (PULL)",
      description:
        "How an agent with its own ERC-8004 identity (BNB testnet 97) sits at Fabius' 5-minute desk: register once with an EIP-191 signature from the agent wallet or identity owner, then every cycle pull the input and post a signed v2 answer before the deadline in the pull response. Fabius never holds your key and never calls your model. You start in a trial seat (recorded and Merkle-anchored, not counted in the consensus); promotion follows the locked seat rules. Returns the live rules, limits, message formats, endpoints and the roster of external agents with their seat and answer health.",
      inputSchema: z.object({}),
    },
    guard(async () => {
      const r = await fetch(`${X402_GATE}/desk/external`, { next: { revalidate: 30 } });
      if (!r.ok) throw new Error(`desk external HTTP ${r.status}`);
      const j = (await r.json()) as { agents: { slug: string; seat: string | null }[]; endpoints: Record<string, string> };
      return ok(`External desk agents: ${j.agents.map((a) => `${a.slug} (${a.seat ?? "no seat yet"})`).join(", ") || "none yet"}. Endpoints: ${Object.values(j.endpoints).join(" | ")}`, j);
    }),
  );

  reg(
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
        return ok(`${bot} bar ${t.harga.bar}: ${t.harga.fab} FAB via x402 at ${X402_GATE}/signal/${bot}`, {
          price: t.harga,
          teaser: t.teaser,
          pay_url: `${X402_GATE}/signal/${bot}/${t.harga.bar}`,
          how_to_pay: "GET pay_url -> 402 with PAYMENT-REQUIRED (x402 v2, scheme exact, asset FAB, extra.name 'Fabius Credit') -> sign Permit2 witness + EIP-2612 permit for exactly that amount -> repeat GET with PAYMENT-SIGNATURE. Reference client: tools/x402_client.py",
          get_test_tokens: `POST ${X402_GATE}/faucet {"address": "0x..."} (FAB sent to you; you need no tBNB)`,
          token: { symbol: "FAB", address: X402_FAB, decimals: 6, network: "eip155:97" },
        });
      } catch (e) {
        return fail(e);
      }
    },
  );

  reg(
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

  reg(
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

  reg(
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

  reg(
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

  reg(
    "fabius_locks",
    {
      title: "Rules locked on-chain",
      description: "Everything Fabius fixed on-chain BEFORE the forward data existed (gate thresholds, bot specs, forward-test rules, slot book, kill rules, gate error budget), with timestamps and transactions.",
      inputSchema: z.object({}),
    },
    guard(async () => ok(`${s.locks.length} locks, oldest first.`, { locks: s.locks.map((l) => ({ ...l, explorer: l.tx ? `https://testnet.bscscan.com/tx/${l.tx}` : null })), states: s.lock_states })),
  );

  reg(
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

  reg(
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

  reg(
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

  reg(
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

// ---------------------------------------------------------------- P157 (F5): alat berbayar dari gerbang + alat penemuan gratis

const butuhKunci = (alat: string, harga: number): Result => ({
  isError: true,
  content: [
    {
      type: "text",
      text:
        `${alat} ${harga ? `costs ${fab(harga)} FAB per call and ` : "is free but "}needs an API key. 1) get free test FAB: POST ${AKUN_GATE}/faucet {"address":"0x.."}; ` +
        `2) deposit with x402: GET ${AKUN_GATE}/account/deposit/<atomic>; 3) sign the key message with your wallet: POST ${AKUN_GATE}/account/key; ` +
        "4) reconnect this MCP server with header 'Authorization: Bearer <key>'. Details: fabius_pricing (free) or https://fabius-one.vercel.app/account",
    },
  ],
});

function tolakGerbang(alat: string, j: Jawab): Result {
  const e = String(j.body.error ?? `gate HTTP ${j.status}`);
  const lagi = j.status === 402 ? ` Balance ${fab(Number(j.body.balance_atomic ?? 0))} FAB, price ${fab(Number(j.body.price_atomic ?? 0))} FAB. ${String(j.body.deposit ?? "")}` : "";
  const sakelar = j.status === 404 ? " (paid MCP is not open on the gate yet)" : "";
  return { isError: true, content: [{ type: "text", text: `${alat}: ${e}${sakelar}.${lagi}` }] };
}

function daftarF5(server: McpServer, opsi: Opsi) {
  const hasil = (j: Jawab, alat: string, ringkas: (d: Record<string, unknown>) => string): Result => {
    if (!j.ok) return tolakGerbang(alat, j);
    const d = (j.body.data ?? {}) as Record<string, unknown>;
    return {
      content: [
        {
          type: "text",
          text: `${ringkas(d)} Charged ${fab(Number((j.body.charge as { atomic?: number } | undefined)?.atomic ?? 0))} FAB; balance ${fab(Number(j.body.balance_atomic ?? 0))} FAB.\n\n${JSON.stringify(j.body, null, 2)}`,
        },
      ],
    };
  };
  const call = (alat: string, args: Record<string, unknown>) =>
    opsi.kunci ? panggil(opsi.kunci, alat, args, `mcp-${globalThis.crypto.randomUUID()}`) : Promise.resolve(null);

  server.registerTool(
    "fabius_pricing",
    {
      title: "Pricing, deposit and API key (free)",
      description:
        "Free. Start here: prices of the paid Fabius MCP tools in FAB (BNB testnet 97 credit, no value), how to get free test FAB, how to deposit with x402 (payer pays no gas), how to get an API key by signing a message with your wallet, honesty boundaries, and the public head of the account ledger.",
      inputSchema: z.object({}),
    },
    guard(async () => {
      const j = await bacaHarga();
      if (!j.ok) return tolakGerbang("fabius_pricing", j);
      return ok(`Paid tools: ${Object.entries(HARGA).map(([a, h]) => `${a} ${fab(h)} FAB`).join(", ")}; free: fabius_pricing, fabius_account.`, j.body);
    }),
  );

  server.registerTool(
    "fabius_account",
    {
      title: "Your balance, keys and charges (free)",
      description: "Free. Balance, deposits, charges and keys of the wallet that owns the API key on this connection, with each ledger record's hash chain so you can check it.",
      inputSchema: z.object({}),
    },
    guard(async () => {
      if (!opsi.kunci) return butuhKunci("fabius_account", 0);
      const j = await bacaAkun(opsi.kunci);
      if (!j.ok) return tolakGerbang("fabius_account", j);
      return ok(`Wallet ${String(j.body.wallet)}: balance ${fab(Number(j.body.balance_atomic ?? 0))} FAB.`, j.body);
    }),
  );

  server.registerTool(
    "fabius_signal",
    {
      title: `Live desk signal (${fab(HARGA.fabius_signal)} FAB)`,
      description:
        "Paid. The AI desk's live decision for the latest 5-minute cycle: dominant bot, instruments, exposure, veto, open position slots and fills, plus the cycle's Merkle root and DeskAnchor tx on BNB testnet so you can check it was committed before the cycle ended. Paper only.",
      inputSchema: z.object({}),
    },
    guard(async () => {
      const j = await call("fabius_signal", {});
      if (!j) return butuhKunci("fabius_signal", HARGA.fabius_signal);
      return hasil(j, "fabius_signal", (d) => `Cycle ${String(d.cycle_utc)}: dominant bot ${String(d.dominant_bot)}.`);
    }),
  );

  server.registerTool(
    "fabius_signal_explain",
    {
      title: `Why this signal (${fab(HARGA.fabius_signal_explain)} FAB)`,
      description:
        "Paid. Each active AI agent's answer for the latest cycle (bot, scores for all six bots, confidence, instruments, factors, summary), each agent's contribution to the dominant bot's value under the locked consensus formula, the features of the chosen instruments from the cycle's data snapshot, and the record hashes + Merkle root to verify them.",
      inputSchema: z.object({}),
    },
    guard(async () => {
      const j = await call("fabius_signal_explain", {});
      if (!j) return butuhKunci("fabius_signal_explain", HARGA.fabius_signal_explain);
      return hasil(j, "fabius_signal_explain", (d) => `Cycle ${String(d.cycle_utc)}: ${String(d.dominant_bot)}; ${(d.contribution as unknown[] | undefined)?.length ?? 0} counted agents.`);
    }),
  );

  server.registerTool(
    "fabius_data",
    {
      title: `Supporting data snapshot (${fab(HARGA.fabius_data)} FAB)`,
      description:
        "Paid. The latest 5-minute data snapshot the desk agents read (per-asset features from Binance, DEX, RugCheck, FOMO, news; per-bot features; source health), optionally filtered to up to 20 symbols. snapshot_sha covers the full snapshot.",
      inputSchema: z.object({ assets: z.array(z.string().regex(/^[A-Z0-9]{2,20}$/)).max(20).optional() }),
    },
    async ({ assets }) => {
      try {
        const j = await call("fabius_data", assets ? { assets } : {});
        if (!j) return butuhKunci("fabius_data", HARGA.fabius_data);
        return hasil(j, "fabius_data", (d) => `Snapshot ${String(d.snapshot_utc)}: ${Object.keys((d.asset_features as object) ?? {}).length} assets.`);
      } catch (e) {
        return fail(e);
      }
    },
  );
}
