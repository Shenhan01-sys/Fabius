// Kesehatan operasi hari ini (docs/design/status.md) - SATU kode untuk /api/status (halaman /status) dan alat MCP `fabius_status`. Hanya baca, tanpa
// kunci: ledger publik (GitHub raw), Actions GitHub (API publik, cache 5 menit), chain 97 (RPC publik). Semantik tenggang = tools/worker_watch.py.
// Gagal baca satu sumber = lampu "unreadable" dengan alasannya (T8), tidak pernah OK dan tidak pernah alarm.

import type { Hex } from "viem";
import type { Snapshot } from "./snapshot";
import { COMMITTER, SIGNAL_ANCHOR, balanceOf, closeOf, commitCount, commitIdOf, getCommit, head, ledger, windows } from "./fabius-chain";

export type Lamp = "ok" | "wait" | "alarm" | "unreadable" | "later" | "private" | "na"; // later = menunggu stasiun sebelumnya, na = tidak berlaku
export type StationKey = "close" | "tick" | "commit" | "reveal" | "kertas" | "exec";
export type Station = { k: StationKey; lamp: Lamp; code: string; at: string | null; detail?: string };
export type BotStatus = { bot: string; bar: string; stations: Station[] };
type Read<T> = ({ ok: true } & T) | { ok: false; error: string };
export type Run = { status: string; conclusion: string | null; started_utc: string; updated_utc: string; url: string };

export type StatusResult = {
  checked_utc: string;
  bar: string;
  window: { open_utc: string; close_utc: string; deadline_utc: string };
  overall: "ok" | "wait" | "alarm" | "unreadable";
  bots: BotStatus[];
  gas: Read<{ committer: string; balance_tbnb: number; alert_below: number; refill_below: number; lamp: Lamp }>;
  chain: Read<{ block: number; block_utc: string; commit_count: number; max_lag_hours: number; reveal_window_hours: number; signal_anchor: string }>;
  actions: Read<{ workflow: string; runs: Run[] }>;
  snapshot: { generated_utc: string; block: number | null };
};

const RAW = "https://raw.githubusercontent.com/Shenhan01-sys/Fabius/master";
const API = "https://api.github.com/repos/Shenhan01-sys/Fabius/actions/workflows";
const DAY_S = 86_400;
const GRACE_S = 1800; // TENGGANG_S tools/worker_watch.py: worker polling 5 menit, 30 menit tanpa komit = curiga
const WINDOW = { open: 8 * 3600 + 40 * 60, close: 11 * 3600 + 58 * 60, deadline: 12 * 3600 }; // paper-ledger.yml: jendela tick sesudah bar tutup
const ALERT_BELOW = 0.01; // ALERT_MIN_TBNB tools/operator_loop.py
const REFILL_BELOW = 0.1; // kebijakan builder: isi ulang saat < 0,1 tBNB (m3_setup.py --min 0.1)
const KERTAS_BOTS = ["B1-TREND"]; // tools/kertas_eksekusi.py --bot (bawaan)
const KERTAS = [
  { venue: "binance", modal: "10", jadwal: "komit" },
  { venue: "aster", modal: "10", jadwal: "komit" },
]; // modal 10 USDT = plafon uang asli (F-D92), jadwal komit = kenyataan hari ini
const EXEC_BOTS = ["B1-TREND"]; // EXEC_BOTS tools/eksekutor.py (bawaan)
const EXEC_VENUE = "binance-demo"; // ledger/eksekusi/<venue>/ (P119, F-D94): ditulis rantai GitHub dari umpan Gist eksekutor
const EXEC_GRACE_S = 3600; // TENGGANG_S tools/eksekusi_ledger.py: komit + 60 menit tanpa laporan = ALARM (SK-E17)

const iso = (s: number) => new Date(s * 1000).toISOString().replace(/\.\d+Z$/, "Z");
const day = (s: number) => iso(s).slice(0, 10);
const errText = (e: unknown) => (e instanceof Error ? e.message : String(e)).split("\n")[0].slice(0, 220);

async function settle<T>(f: () => Promise<T>): Promise<{ ok: true; v: T } | { ok: false; error: string }> {
  try {
    return { ok: true, v: await f() };
  } catch (e) {
    return { ok: false, error: errText(e) };
  }
}

async function kertasLast(venue: string, bot: string, modal: string, jadwal: string) {
  const res = await fetch(`${RAW}/ledger/kertas/${venue}/${bot}-${modal}-${jadwal}.jsonl`, { next: { revalidate: 120 } });
  if (!res.ok) throw new Error(`kertas ${venue}: HTTP ${res.status} dari GitHub`);
  const rows = (await res.text()).split("\n").filter((l) => l.trim());
  const last = rows.length ? (JSON.parse(rows[rows.length - 1]) as { bar: string; status: string }) : null;
  return { venue, last };
}

/** Ledger eksekusi publik satu bot; null = berkas belum ada (umpan belum menyala) - bukan galat. */
async function execLedger(bot: string): Promise<{ bar: string; n_order: number; pelanggaran?: string[] }[] | null> {
  const res = await fetch(`${RAW}/ledger/eksekusi/${EXEC_VENUE}/${bot}.jsonl`, { next: { revalidate: 120 } });
  if (res.status === 404) return null;
  if (!res.ok) throw new Error(`ledger eksekusi: HTTP ${res.status} dari GitHub`);
  return (await res.text()).split("\n").filter((l) => l.trim()).map((l) => JSON.parse(l));
}

async function runs(workflow: string): Promise<Run[]> {
  const res = await fetch(`${API}/${workflow}/runs?per_page=10`, {
    headers: { accept: "application/vnd.github+json", "user-agent": "fabius-status" },
    next: { revalidate: 300 },
  });
  if (!res.ok) throw new Error(`GitHub API HTTP ${res.status}${res.status === 403 || res.status === 429 ? " (batas tanpa token)" : ""}`);
  const body = (await res.json()) as { workflow_runs: { status: string; conclusion: string | null; run_started_at: string; updated_at: string; html_url: string }[] };
  return body.workflow_runs.map((r) => ({ status: r.status, conclusion: r.conclusion, started_utc: r.run_started_at, updated_utc: r.updated_at, url: r.html_url }));
}

async function botStatus(s: Snapshot, bot: string, bar: string, now: number): Promise<BotStatus> {
  const close = closeOf(bar);
  const st: Station[] = [{ k: "close", lamp: "ok", code: "CLOSED", at: iso(close) }];
  const execP = EXEC_BOTS.includes(bot) ? settle(() => execLedger(bot)) : null;
  const kertasP = KERTAS_BOTS.includes(bot) ? settle(() => Promise.all(KERTAS.map((k) => kertasLast(k.venue, bot, k.modal, k.jadwal)))) : null;

  // 02 tick
  const led = await settle(() => ledger(bot));
  let tickAt: number | null = null;
  if (!led.ok) st.push({ k: "tick", lamp: "unreadable", code: "UNREADABLE", at: null, detail: led.error });
  else {
    const tk = led.v.find((r) => r.type === "tick" && r.asof_date === bar);
    const gap = led.v.find((r) => r.type === "gap" && r.asof_date === bar);
    if (tk) {
      tickAt = tk.emitted_utc ? Math.floor(Date.parse(tk.emitted_utc) / 1000) : null;
      st.push({ k: "tick", lamp: "ok", code: "TICK_OK", at: tk.emitted_utc ?? null, detail: `${tk.signal_ids?.length ?? 0}` });
    } else if (gap) st.push({ k: "tick", lamp: "alarm", code: "TICK_GAP", at: null, detail: gap.reason ?? undefined });
    else if (now < close + WINDOW.deadline) st.push({ k: "tick", lamp: "wait", code: now < close + WINDOW.open ? "TICK_BEFORE_WINDOW" : "TICK_IN_WINDOW", at: iso(close + WINDOW.open) });
    else st.push({ k: "tick", lamp: "alarm", code: "TICK_MISSED", at: iso(close + WINDOW.deadline) });
  }

  // 03 komit + 04 ungkap (hanya bila tick ada)
  const tickOk = st[1].lamp === "ok";
  if (!tickOk) {
    st.push({ k: "commit", lamp: "later", code: "NEEDS_TICK", at: null }, { k: "reveal", lamp: "later", code: "NEEDS_TICK", at: null });
  } else {
    const spec = s.bots.find((b) => b.id === bot)!.spec_sha as Hex;
    const c = await settle(() => getCommit(commitIdOf(bot, spec, bar)));
    if (!c.ok) st.push({ k: "commit", lamp: "unreadable", code: "UNREADABLE", at: null, detail: c.error }, { k: "reveal", lamp: "later", code: "NEEDS_COMMIT", at: null });
    else if (!c.v.exists) {
      const silentFor = tickAt != null ? now - tickAt : 0;
      st.push(
        silentFor >= GRACE_S
          ? { k: "commit", lamp: "alarm", code: "WORKER_SILENT", at: null, detail: `${Math.round(silentFor / 60)}` }
          : { k: "commit", lamp: "wait", code: "COMMIT_GRACE", at: tickAt != null ? iso(tickAt + GRACE_S) : null },
        { k: "reveal", lamp: "later", code: "NEEDS_COMMIT", at: null },
      );
    } else {
      const at = Number(c.v.committedAt);
      st.push({ k: "commit", lamp: "ok", code: "COMMIT_OK", at: iso(at), detail: `${c.v.n}` });
      if (c.v.n === 0) st.push({ k: "reveal", lamp: "ok", code: "REVEAL_SILENT", at: null });
      else if (c.v.revealed >= c.v.n) st.push({ k: "reveal", lamp: "ok", code: "REVEAL_OK", at: null, detail: `${c.v.revealed}/${c.v.n}` });
      else
        st.push(
          now - at >= GRACE_S
            ? { k: "reveal", lamp: "alarm", code: "REVEAL_STUCK", at: null, detail: `${c.v.revealed}/${c.v.n}` }
            : { k: "reveal", lamp: "wait", code: "REVEAL_PENDING", at: iso(at + GRACE_S), detail: `${c.v.revealed}/${c.v.n}` },
        );
    }
  }

  // 05 kertas-venue: harga 1 menit di jam komit terbit di Binance Vision keesokan harinya, jadi kertas wajar tertinggal satu bar
  if (!kertasP) st.push({ k: "kertas", lamp: "na", code: "KERTAS_NA", at: null });
  else {
    const k = await kertasP;
    if (!k.ok) st.push({ k: "kertas", lamp: "unreadable", code: "UNREADABLE", at: null, detail: k.error });
    else {
      const lasts = k.v.map((x) => x.last);
      const oldest = lasts.map((x) => x?.bar ?? "").sort()[0];
      const detail = k.v.map((x) => `${x.venue} ${x.last ? `${x.last.bar} ${x.last.status}` : "-"}`).join(" · ");
      const prev = day(close - 2 * DAY_S);
      st.push({ k: "kertas", lamp: oldest && oldest >= prev ? "ok" : "wait", code: oldest && oldest >= prev ? "KERTAS_OK" : "KERTAS_BEHIND", at: null, detail });
    }
  }
  // 06 eksekusi demo: ledger publik dari umpan Gist (P119). Belum ada berkas = umpan belum menyala -> tetap "tidak publik".
  if (!execP) st.push({ k: "exec", lamp: "na", code: "EXEC_NA", at: null });
  else {
    const x = await execP;
    const commit = st.find((y) => y.k === "commit");
    if (!x.ok) st.push({ k: "exec", lamp: "unreadable", code: "UNREADABLE", at: null, detail: x.error });
    else if (x.v === null) st.push({ k: "exec", lamp: "private", code: "EXEC_PRIVATE", at: null });
    else {
      const rec = x.v.find((r) => r.bar === bar);
      const cAt = commit?.lamp === "ok" && commit.at ? Math.floor(Date.parse(commit.at) / 1000) : null;
      if (rec && rec.pelanggaran?.length) st.push({ k: "exec", lamp: "alarm", code: "EXEC_VIOLATION", at: null, detail: `${rec.pelanggaran.length}` });
      else if (rec) st.push({ k: "exec", lamp: "ok", code: "EXEC_OK", at: null, detail: `${rec.n_order}` });
      else if (cAt == null) st.push({ k: "exec", lamp: "later", code: "NEEDS_COMMIT", at: null });
      else if (now - cAt >= EXEC_GRACE_S) st.push({ k: "exec", lamp: "alarm", code: "EXEC_MISSING", at: null, detail: `${Math.round((now - cAt) / 60)}` });
      else st.push({ k: "exec", lamp: "wait", code: "EXEC_WAIT", at: iso(cAt + EXEC_GRACE_S) });
    }
  }
  return { bot, bar, stations: st };
}

export async function getStatus(s: Snapshot): Promise<StatusResult> {
  const now = Math.floor(Date.now() / 1000);
  const bar = day(Math.floor(now / DAY_S) * DAY_S - DAY_S); // bar harian terakhir yang sudah tutup
  const close = closeOf(bar);
  const fwd = s.bots.filter((b) => b.forward && s.ledger[b.id]).map((b) => b.id);
  const [bots, gas, chain, act] = await Promise.all([
    Promise.all(fwd.map((b) => botStatus(s, b, bar, now))),
    settle(() => balanceOf(COMMITTER)),
    settle(async () => {
      const [h, n, w] = await Promise.all([head(), commitCount(), windows()]);
      return { block: h.block, block_utc: iso(h.ts), commit_count: n, max_lag_hours: w.maxLag / 3600, reveal_window_hours: w.revealWindow / 3600, signal_anchor: SIGNAL_ANCHOR };
    }),
    settle(() => runs("paper-ledger.yml")),
  ]);
  const gasLamp: Lamp = !gas.ok ? "unreadable" : gas.v < ALERT_BELOW ? "alarm" : gas.v < REFILL_BELOW ? "wait" : "ok";
  const lamps = [...bots.flatMap((b) => b.stations.map((x) => x.lamp)), gasLamp];
  const overall = lamps.includes("alarm") ? "alarm" : lamps.includes("unreadable") ? "unreadable" : lamps.includes("wait") ? "wait" : "ok";
  return {
    checked_utc: iso(now),
    bar,
    window: { open_utc: iso(close + WINDOW.open), close_utc: iso(close + WINDOW.close), deadline_utc: iso(close + WINDOW.deadline) },
    overall,
    bots,
    gas: gas.ok ? { ok: true, committer: COMMITTER, balance_tbnb: +gas.v.toFixed(6), alert_below: ALERT_BELOW, refill_below: REFILL_BELOW, lamp: gasLamp } : gas,
    chain: chain.ok ? { ok: true, ...chain.v } : chain,
    actions: act.ok ? { ok: true, workflow: "paper-ledger.yml", runs: act.v } : act,
    snapshot: { generated_utc: s.generated_utc, block: s.chain?.block ?? null },
  };
}
