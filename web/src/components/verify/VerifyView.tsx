"use client";

// /verify (docs/design/verify.md): satu sinyal berjalan melewati EMPAT stasiun pada satu rel - tick ledger -> komit di chain -> dibuka -> dihitung ulang.
// Tiap stasiun menyala saat pemeriksaannya selesai; tiap sinyal = satu blok yang berubah keadaan (tersegel -> terbuka -> SAH). Vonis = kubus besar.
// Data live dari /api/verify (kode sama dengan MCP `fabius_verify`); gagal baca = pesan galat, bukan vonis (T8).

import { useEffect, useState, type FormEvent } from "react";
import { motion } from "motion/react";
import { LangProvider, useLang } from "../lang";
import Nav from "../Nav";
import IsoCube from "../ui/IsoCube";
import { Claims, Footer } from "../sections/Closing";
import { LINKS } from "@/lib/copy";
import { short, type CellState, type Snapshot } from "@/lib/snapshot";
import type { VerifyResult } from "@/lib/verify";

type Kind = CellState | "empty";
type St = "ok" | "fail" | "wait" | "skip";
type Run = { bot: string; bar: string; nonce: number };
type Res = { state: "idle" | "loading" } | { state: "done"; result: VerifyResult } | { state: "error"; error: string };

const VERDICT_KIND: Record<string, Kind> = {
  SAH: "verified",
  SEALED_NOT_YET_REVEALED: "sealed",
  ALARM: "missed",
  NO_TICK: "empty",
  BEFORE_LOCK: "prelock",
  BAR_NOT_CLOSED: "future",
  AWAITING_COMMIT: "pending",
  NOT_COMMITTED: "missed",
};
const ST_RING: Record<St, string> = {
  ok: "border-violet/40 shadow-[0_24px_60px_-30px_rgba(110,75,255,.55)]",
  fail: "border-gap/60 shadow-[0_24px_60px_-30px_rgba(255,90,110,.55)]",
  wait: "border-violet-2/40",
  skip: "border-white/60 opacity-60",
};
const scan = (h: string) => `${LINKS.tx}${h}`;

export default function VerifyView({ s, bots, bot, bar }: { s: Snapshot; bots: string[]; bot: string; bar: string }) {
  return (
    <LangProvider>
      <div className="p-2 sm:p-3">
        <Nav />
        <Verify s={s} bots={bots} initialBot={bot} initialBar={bar} />
        <Claims />
        <Footer s={s} />
      </div>
    </LangProvider>
  );
}

function Verify({ s, bots, initialBot, initialBar }: { s: Snapshot; bots: string[]; initialBot: string; initialBar: string }) {
  const { t } = useLang();
  const v = t.verify;
  const [bot, setBot] = useState(initialBot);
  const [bar, setBar] = useState(initialBar);
  const [run, setRun] = useState<Run>({ bot: initialBot, bar: initialBar, nonce: 0 });
  const [res, setRes] = useState<Res>({ state: "loading" });
  const genesis = s.ledger[bot]?.genesis;

  useEffect(() => {
    let alive = true;
    const q = new URLSearchParams({ bot: run.bot, ...(run.bar ? { bar: run.bar } : {}) });
    fetch(`/api/verify?${q}`, { cache: "no-store" })
      .then(async (r) => {
        const body = await r.json().catch(() => ({ error: `HTTP ${r.status}` }));
        if (!alive) return;
        if (body.result) {
          setRes({ state: "done", result: body.result as VerifyResult });
          setBar((b) => b || (body.result as VerifyResult).bar);
        } else setRes({ state: "error", error: String(body.error ?? `HTTP ${r.status}`) });
      })
      .catch((e) => alive && setRes({ state: "error", error: String(e) }));
    return () => {
      alive = false;
    };
  }, [run]);

  function submit(e?: FormEvent) {
    e?.preventDefault();
    setRes({ state: "loading" });
    setRun({ bot, bar, nonce: Date.now() });
    const q = new URLSearchParams({ bot, ...(bar ? { bar } : {}) });
    window.history.replaceState(null, "", `/verify?${q}`);
  }

  return (
    <section id="top" className="relative overflow-hidden rounded-[30px] bg-gradient-to-b from-lav via-lav to-white px-6 pb-24 pt-32 sm:px-12 sm:pt-40 lg:px-16">
      <span className="tag text-violet">{v.tag}</span>
      <h1 className="mt-4 font-display leading-[0.9] tracking-[-0.035em] text-ink">
        <span className="block text-[clamp(3rem,9vw,8.5rem)] font-[300]" style={{ fontStretch: "112%" }}>{v.t1}</span>
        <span className="block text-[clamp(3rem,9vw,8.5rem)] font-[800] italic text-violet" style={{ fontStretch: "78%" }}>{v.t2}</span>
      </h1>
      <p className="mt-6 max-w-2xl text-lg text-ink/65">{v.sub}</p>

      {/* pilih bot + hari */}
      <form onSubmit={submit} className="glass mt-10 flex flex-col gap-5 rounded-[26px] p-5 sm:flex-row sm:items-end sm:p-6">
        <div>
          <div className="tag mb-2 text-ink/45">{v.bot}</div>
          <div className="flex flex-wrap gap-2">
            {bots.map((b) => (
              <button key={b} type="button" onClick={() => setBot(b)}
                className={`flex items-center gap-2 rounded-full px-4 py-2.5 text-sm font-semibold transition ${b === bot ? "bg-ink text-white" : "bg-white/70 text-ink/70 hover:bg-white"}`}>
                <IsoCube kind={b === bot ? "sealed" : "empty"} size={18} />
                {b}
              </button>
            ))}
          </div>
        </div>
        <label className="flex flex-col">
          <span className="tag mb-2 text-ink/45">{v.bar}</span>
          <input type="date" value={bar} min={genesis} onChange={(e) => setBar(e.target.value)}
            className="rounded-full border border-white/80 bg-white/80 px-4 py-2.5 font-mono text-sm text-ink outline-none focus:border-violet" />
        </label>
        <button type="button" onClick={() => setBar("")} className="rounded-full px-3 py-2.5 font-mono text-xs text-ink/55 underline-offset-4 hover:underline">
          {v.latest}
        </button>
        <button type="submit" className="rounded-full bg-violet px-7 py-3 text-sm font-semibold text-white shadow-[0_14px_40px_-12px_rgba(110,75,255,.8)] transition hover:bg-ink sm:ml-auto">
          {v.go} →
        </button>
      </form>

      {res.state === "loading" && <Travelling label={v.checking} />}
      {res.state === "error" && (
        <div className="mt-10 rounded-[26px] border border-gap/50 bg-white/80 p-6">
          <div className="flex items-center gap-3 font-semibold text-ink"><IsoCube kind="gap" size={26} />{v.error}</div>
          <pre className="mt-3 whitespace-pre-wrap break-all font-mono text-xs text-ink/55">{res.error}</pre>
        </div>
      )}
      {res.state === "done" && <Result r={res.result} />}
    </section>
  );
}

/** Saat membaca chain: satu blok tersegel berjalan di rel melewati empat stasiun. */
function Travelling({ label }: { label: string }) {
  return (
    <div className="glass relative mt-10 overflow-hidden rounded-[26px] px-6 py-10">
      <div className="absolute inset-x-10 top-1/2 h-px bg-violet/25" />
      <motion.div className="relative w-fit" animate={{ x: ["0%", "1200%"] }} transition={{ duration: 2.4, repeat: Infinity, ease: "easeInOut" }}>
        <IsoCube kind="sealed" size={34} />
      </motion.div>
      <div className="tag mt-4 text-center text-ink/50">{label}</div>
    </div>
  );
}

function stations(r: VerifyResult): { st: St; kind: Kind }[] {
  const c = r.commit;
  const s1: St = r.tick ? "ok" : "fail";
  const s2: St = c.committed ? "ok" : r.verdict === "NOT_COMMITTED" ? "fail" : r.verdict === "AWAITING_COMMIT" || r.verdict === "BAR_NOT_CLOSED" ? "wait" : "skip";
  const s3: St = !c.committed ? "skip" : c.revealed < c.n ? "wait" : "ok";
  const s4: St = !c.committed ? "skip" : r.verdict === "ALARM" ? "fail" : r.verdict === "SAH" ? "ok" : "wait";
  return [
    { st: s1, kind: r.tick ? "verified" : "empty" },
    { st: s2, kind: c.committed ? "sealed" : (VERDICT_KIND[r.verdict] ?? "empty") },
    { st: s3, kind: !c.committed ? "empty" : c.revealed < c.n ? "sealed" : "verified" },
    { st: s4, kind: !c.committed ? "empty" : (VERDICT_KIND[r.verdict] ?? "empty") },
  ];
}

function Result({ r }: { r: VerifyResult }) {
  const { t } = useLang();
  const v = t.verify;
  const sts = stations(r);
  const c = r.commit;
  const pending = Math.max(0, c.n - r.signals.length);
  const share = `/verify?bot=${r.bot}&bar=${r.bar}`;
  return (
    <div key={r.checked_utc} className="mt-10">
      {/* rel + empat stasiun */}
      <div className="relative">
        <div className="absolute left-8 right-8 top-[46px] hidden h-px bg-gradient-to-r from-violet/10 via-violet/40 to-violet/10 lg:block" />
        <div className="grid gap-4 lg:grid-cols-4">
          {v.stations.map((stn, i) => (
            <motion.div key={stn.k} initial={{ opacity: 0, y: 18 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.15 + i * 0.32, type: "spring", stiffness: 110, damping: 16 }}
              className={`glass relative rounded-[24px] border p-5 ${ST_RING[sts[i].st]}`}>
              <div className="flex items-center justify-between">
                <span className="tag text-violet">{stn.k}</span>
                <motion.div initial={{ scale: 0.6, opacity: 0 }} animate={{ scale: 1, opacity: 1 }} transition={{ delay: 0.35 + i * 0.32, type: "spring", stiffness: 160, damping: 12 }}
                  className={sts[i].st === "wait" ? "animate-breathe" : ""}>
                  <IsoCube kind={sts[i].kind} size={34} glow={sts[i].st === "ok" && sts[i].kind === "verified"} />
                </motion.div>
              </div>
              <div className="mt-3 font-display text-xl font-[700] tracking-tight text-ink">{stn.h}</div>
              <div className="mt-1 text-[0.8rem] text-ink/50">{stn.d}</div>
              <div className="mt-4 space-y-1.5 font-mono text-[0.72rem] text-ink/70">
                {i === 0 && (r.tick ? (
                  <>
                    <div>{r.tick.signal_ids.length} {v.signals}</div>
                    {r.tick.emitted_utc && <div>{v.emitted} {r.tick.emitted_utc}</div>}
                    {r.tick.lag_hours != null && <div>{r.tick.lag_hours} {v.afterClose}</div>}
                  </>
                ) : <div className="text-gap">{v.verdicts.NO_TICK}</div>)}
                {i === 1 && (c.committed ? (
                  <>
                    <div>{v.committed} {c.committed_utc}</div>
                    <div>{c.lag_hours} {v.afterClose}</div>
                    <div>{v.root} {short(c.root, 6)}</div>
                    <a className="text-violet underline-offset-2 hover:underline" href={`${LINKS.scan}${r.contracts.signal_anchor}`} target="_blank" rel="noreferrer">SignalAnchor ↗</a>
                  </>
                ) : <div>{v.verdicts[r.verdict] ?? r.verdict}</div>)}
                {i === 2 && c.committed && (c.n === 0 ? <div className="font-sans text-[0.78rem] text-ink/60">{v.silent}</div> : (
                  <div className="flex flex-wrap gap-1.5">
                    {r.signals.map((x) => <IsoCube key={x.signal_id} kind="verified" size={22} />)}
                    {Array.from({ length: pending }).map((_, k) => <IsoCube key={`p${k}`} kind="sealed" size={22} />)}
                  </div>
                ))}
                {i === 3 && c.committed && (c.n === 0 ? <div>{v.root} 0x0 · n 0 ✓</div> : (
                  <div>{r.signals.filter((x) => x.leaf_recomputes && x.in_ledger_tick).length}/{c.n} ✓</div>
                ))}
              </div>
            </motion.div>
          ))}
        </div>
      </div>

      {/* sinyal yang dibuka */}
      {r.signals.length > 0 && (
        <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ delay: 1.2 }} className="glass mt-4 overflow-x-auto rounded-[24px] p-5">
          <table className="w-full min-w-[720px] text-left font-mono text-[0.75rem] text-ink/75">
            <tbody>
              {r.signals.map((x) => (
                <tr key={x.signal_id} className="border-b border-white/70 last:border-0">
                  <td className="py-2.5 pr-3"><IsoCube kind={x.leaf_recomputes && x.in_ledger_tick ? "verified" : "missed"} size={22} glow={x.leaf_recomputes && x.in_ledger_tick} /></td>
                  <td className="pr-4 font-sans text-sm font-semibold text-ink">{x.asset}</td>
                  <td className="pr-4">{x.action}</td>
                  <td className="pr-4">{x.weight_before} → {x.weight_after}</td>
                  <td className="pr-4">{x.reference_price ?? "—"}</td>
                  <td className="pr-4">{x.leaf_recomputes ? "✓" : "✗"} {v.leafOk}</td>
                  <td className="pr-4">{x.in_ledger_tick ? "✓" : "✗"} {v.inLedger}</td>
                  <td>{x.tx ? <a className="text-violet underline-offset-2 hover:underline" href={scan(x.tx)} target="_blank" rel="noreferrer">{v.tx} {short(x.tx, 4)} ↗</a> : "—"}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </motion.div>
      )}

      {/* vonis */}
      <motion.div initial={{ opacity: 0, y: 24 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 1.45, type: "spring", stiffness: 90, damping: 16 }}
        className="relative mt-4 grid items-center gap-8 overflow-hidden rounded-[28px] bg-night p-8 text-white sm:p-10 lg:grid-cols-[auto_1fr]">
        <div className={r.verdict === "AWAITING_COMMIT" ? "animate-breathe" : ""}>
          <IsoCube kind={VERDICT_KIND[r.verdict] ?? "empty"} size={132} glow={r.verdict === "SAH"} />
        </div>
        <div>
          <div className="tag text-white/45">{r.bot} · {r.bar} · {v.checkedAt} {r.checked_utc}</div>
          <div className={`mt-2 font-display text-[clamp(2.2rem,5vw,4rem)] font-[800] italic leading-none tracking-tight ${r.verdict === "ALARM" || r.verdict === "NOT_COMMITTED" ? "text-gap" : ""}`} style={{ fontStretch: "80%" }}>
            {v.verdicts[r.verdict] ?? r.verdict}
          </div>
          <p className="mt-3 max-w-2xl text-white/65">{v.explain[r.verdict]}</p>
          {r.problems.length > 0 && (
            <div className="mt-4">
              <div className="tag text-gap">{v.problems}</div>
              <ul className="mt-2 space-y-1 font-mono text-xs text-white/80">{r.problems.map((p) => <li key={p}>· {p}</li>)}</ul>
            </div>
          )}
          <a href={share} className="mt-5 inline-block font-mono text-xs text-violet-2 underline-offset-4 hover:underline">{v.share} ↗</a>
        </div>
      </motion.div>

      {/* periksa sendiri */}
      <div className="mt-4 grid gap-4 lg:grid-cols-2">
        <div className="min-w-0 rounded-[24px] bg-night-2 p-6 text-white">
          <div className="tag text-white/45">{v.self}</div>
          <p className="mt-2 text-sm text-white/60">{v.selfNote}</p>
          <pre className="glass-dark mt-3 overflow-x-auto rounded-2xl p-4 font-mono text-[0.74rem] leading-relaxed text-violet-2">{`git clone ${LINKS.repo}
python -X utf8 tools/verify_signals.py

# MCP (agen): fabius_verify {"bot":"${r.bot}","bar":"${r.bar}"}`}</pre>
        </div>
        <details className="glass min-w-0 self-start rounded-[24px] p-6">
          <summary className="tag cursor-pointer text-ink/55">{v.raw}</summary>
          <pre className="mt-3 max-h-80 overflow-auto font-mono text-[0.68rem] text-ink/70">{JSON.stringify(r, null, 2)}</pre>
        </details>
      </div>
    </div>
  );
}
