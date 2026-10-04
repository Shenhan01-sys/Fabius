"use client";

// /status (docs/design/status.md): satu hari operasi = satu putaran jam UTC. Dial 24 jam (busur = jendela tick, jarum = sekarang, titik = kejadian bar
// hari ini) -> rel stasiun per bot (bahasa sama dengan /verify: lampu = kubus) -> mesin (tangki gas committer, kepala chain, snapshot) -> detak rantai
// GitHub. Data live dari /api/status, dibaca ulang tiap 2 menit; gagal baca = lampu "tak terbaca", bukan beres dan bukan alarm (T8).

import Link from "next/link";
import { useEffect, useState } from "react";
import { motion } from "motion/react";
import { LangProvider, useLang } from "../lang";
import Nav from "../Nav";
import IsoCube from "../ui/IsoCube";
import { Claims, Footer } from "../sections/Closing";
import { LINKS } from "@/lib/copy";
import type { CellState, Snapshot } from "@/lib/snapshot";
import type { Lamp, Run, Station, StatusResult } from "@/lib/status";

type Kind = CellState | "empty" | "core";
type Res = { state: "loading" } | { state: "done"; r: StatusResult } | { state: "error"; error: string };

const LAMP: Record<Lamp, Kind> = { ok: "verified", wait: "pending", alarm: "missed", unreadable: "empty", later: "future", private: "prelock", na: "empty" };
const OVERALL: Record<StatusResult["overall"], Kind> = { ok: "verified", wait: "pending", alarm: "missed", unreadable: "empty" };
const RING: Record<Lamp, string> = {
  ok: "border-violet/40 shadow-[0_24px_60px_-30px_rgba(110,75,255,.55)]",
  wait: "border-violet-2/50",
  alarm: "border-gap/60 shadow-[0_24px_60px_-30px_rgba(255,90,110,.55)]",
  unreadable: "border-dashed border-ink/30",
  later: "border-white/60",
  private: "border-white/70",
  na: "border-white/60 opacity-55",
};
const ACTIONS = `${LINKS.repo}/actions/workflows/paper-ledger.yml`;
const REFRESH_MS = 120_000;
const DAY = 86_400;

const secOfDay = (iso: string) => {
  const d = new Date(iso);
  return d.getUTCHours() * 3600 + d.getUTCMinutes() * 60 + d.getUTCSeconds();
};
const hm = (iso: string | null | undefined, today?: string) => (iso ? `${today && iso.slice(0, 10) !== today ? `${iso.slice(5, 10)} ` : ""}${iso.slice(11, 16)} UTC` : "—");

export default function StatusView({ s }: { s: Snapshot }) {
  return (
    <LangProvider>
      <div className="p-2 sm:p-3">
        <Nav />
        <Status />
        <Claims />
        <Footer s={s} />
      </div>
    </LangProvider>
  );
}

function Status() {
  const { t } = useLang();
  const v = t.status;
  const [nonce, setNonce] = useState(0);
  const [res, setRes] = useState<Res>({ state: "loading" });

  useEffect(() => {
    let alive = true;
    fetch("/api/status", { cache: "no-store" })
      .then(async (x) => {
        const body = await x.json().catch(() => ({ error: `HTTP ${x.status}` }));
        if (!alive) return;
        setRes(body.result ? { state: "done", r: body.result as StatusResult } : { state: "error", error: String(body.error ?? `HTTP ${x.status}`) });
      })
      .catch((e) => alive && setRes({ state: "error", error: String(e) }));
    const id = window.setTimeout(() => setNonce((n) => n + 1), REFRESH_MS);
    return () => {
      alive = false;
      window.clearTimeout(id);
    };
  }, [nonce]);

  const r = res.state === "done" ? res.r : null;
  return (
    <>
      <section id="top" className="relative overflow-hidden rounded-[30px] bg-gradient-to-b from-lav via-lav to-white px-6 pb-20 pt-32 sm:px-12 sm:pt-40 lg:px-16">
        <div className="pointer-events-none absolute -right-32 top-24 h-[420px] w-[420px] rounded-full bg-violet/15 blur-[130px]" />
        <span className="tag text-violet">{v.tag}</span>
        <div className="relative mt-4 grid gap-12 lg:grid-cols-[1fr_auto] lg:items-center">
          <div className="min-w-0">
            <h1 className="font-display leading-[0.9] tracking-[-0.035em] text-ink">
              <span className="block text-[clamp(2.8rem,8vw,7.6rem)] font-[300]" style={{ fontStretch: "112%" }}>{v.t1}</span>
              <span className="block text-[clamp(2.8rem,8vw,7.6rem)] font-[800] italic text-violet" style={{ fontStretch: "78%" }}>{v.t2}</span>
            </h1>
            <p className="mt-6 max-w-xl text-lg text-ink/65">{v.sub}</p>
            <div className="mt-8 flex flex-wrap items-center gap-3">
              {r ? (
                <div className={`inline-flex items-center gap-3 rounded-full px-5 py-3 font-semibold ${r.overall === "alarm" ? "bg-gap text-white" : "bg-ink text-white"}`}>
                  <span className={r.overall === "wait" ? "animate-breathe" : ""}><IsoCube kind={OVERALL[r.overall]} size={24} glow={r.overall === "ok"} /></span>
                  {v.overall[r.overall]}
                </div>
              ) : (
                <div className="inline-flex items-center gap-3 rounded-full bg-white/70 px-5 py-3 text-ink/60">
                  <span className="animate-breathe"><IsoCube kind="pending" size={24} /></span>
                  {res.state === "error" ? v.error : v.reading}
                </div>
              )}
              <button type="button" onClick={() => { setRes({ state: "loading" }); setNonce((n) => n + 1); }}
                className="rounded-full px-4 py-3 font-mono text-xs text-ink/60 underline-offset-4 hover:text-violet hover:underline">
                {v.refresh} ↻
              </button>
              {r && <span className="font-mono text-[0.7rem] text-ink/45">{v.checked} {r.checked_utc}</span>}
            </div>
            {res.state === "error" && <pre className="mt-4 whitespace-pre-wrap break-all font-mono text-xs text-ink/50">{res.error}</pre>}
          </div>
          <div className="justify-self-center lg:justify-self-end">
            <Dial r={r} />
          </div>
        </div>
      </section>
      {r && <Bots r={r} />}
      {r && <Plant r={r} />}
      {r && <Beat r={r} />}
    </>
  );
}

// ---------------------------------------------------------------- dial 24 jam UTC
function Dial({ r }: { r: StatusResult | null }) {
  const { t } = useLang();
  const v = t.status.dial;
  const S = 300, C = S / 2, R = 118;
  const pt = (sec: number, rad = R) => {
    const a = (sec / DAY) * 2 * Math.PI;
    return [C + rad * Math.sin(a), C - rad * Math.cos(a)] as const;
  };
  const arc = (a: number, b: number, rad = R) => {
    const [x1, y1] = pt(a, rad), [x2, y2] = pt(b, rad);
    return `M ${x1} ${y1} A ${rad} ${rad} 0 ${b - a > DAY / 2 ? 1 : 0} 1 ${x2} ${y2}`;
  };
  const now = r ? secOfDay(r.checked_utc) : null;
  const today = r?.window.open_utc.slice(0, 10);
  const events = r
    ? r.bots.flatMap((b) => b.stations.filter((x) => (x.k === "tick" || x.k === "commit") && x.lamp === "ok" && x.at?.slice(0, 10) === today).map((x) => ({ k: x.k, at: x.at! })))
    : [];
  const closedH = r ? Math.round((Date.parse(r.checked_utc) - Date.parse(`${today}T00:00:00Z`)) / 36e5 * 10) / 10 : null;
  return (
    <div className="flex flex-col items-center">
      <div className="glass grid place-items-center rounded-full p-4">
        <svg viewBox={`0 0 ${S} ${S}`} width={S} height={S} className="max-w-[78vw]" role="img" aria-label={v.title}>
          <circle cx={C} cy={C} r={R} fill="none" stroke="rgba(21,18,43,.08)" strokeWidth="10" />
          {Array.from({ length: 24 }, (_, h) => {
            const [x1, y1] = pt(h * 3600, R - 14), [x2, y2] = pt(h * 3600, R - (h % 6 === 0 ? 24 : 19));
            return <line key={h} x1={x1} y1={y1} x2={x2} y2={y2} stroke="rgba(21,18,43,.25)" strokeWidth={h % 6 === 0 ? 1.6 : 1} />;
          })}
          {[0, 6, 12, 18].map((h) => {
            const [x, y] = pt(h * 3600, R - 38);
            return <text key={h} x={x} y={y + 4} textAnchor="middle" className="fill-ink/45 font-mono text-[11px]">{String(h).padStart(2, "0")}</text>;
          })}
          {r && (
            <>
              <motion.path d={arc(secOfDay(r.window.open_utc), secOfDay(r.window.close_utc))} fill="none" stroke="#6e4bff" strokeWidth="10" strokeLinecap="round"
                initial={{ pathLength: 0 }} animate={{ pathLength: 1 }} transition={{ duration: 1.2, ease: [0.22, 1, 0.36, 1] }} />
              {(() => {
                const [x, y] = pt(secOfDay(r.window.deadline_utc), R + 12);
                return <circle cx={x} cy={y} r="3" fill="rgba(21,18,43,.35)" />;
              })()}
              {events.map((e, i) => {
                const [x, y] = pt(secOfDay(e.at), R);
                return <circle key={i} cx={x} cy={y} r={e.k === "tick" ? 6 : 4.5} fill={e.k === "tick" ? "#ffffff" : "#3a29b8"} stroke="#6e4bff" strokeWidth="1.5" />;
              })}
            </>
          )}
          {(() => {
            const [x, y] = pt(0, R);
            return <circle cx={x} cy={y} r="6" fill="#15122b" />;
          })()}
          {now != null && (
            <motion.g initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ delay: 0.6, duration: 0.6 }}>
              <line x1={C} y1={C} x2={pt(now, R - 20)[0]} y2={pt(now, R - 20)[1]} stroke="#15122b" strokeWidth="2.4" strokeLinecap="round" />
              <circle cx={pt(now, R - 20)[0]} cy={pt(now, R - 20)[1]} r="4" fill="#15122b" />
            </motion.g>
          )}
          <circle cx={C} cy={C} r="5" fill="#15122b" />
        </svg>
      </div>
      {r && (
        <div className="mt-5 text-center">
          <div className="tag text-ink/40">{v.title}</div>
          <div className="font-display text-2xl font-[700] text-ink">{r.bar}</div>
          <div className="font-mono text-[0.68rem] text-ink/50">{v.closed} {closedH} {v.ago} · {v.now} {r.checked_utc.slice(11, 16)} UTC</div>
          <div className="mt-3 flex flex-wrap justify-center gap-x-4 gap-y-1 font-mono text-[0.64rem] text-ink/55">
            <span><span className="mr-1 inline-block h-2 w-4 rounded-full bg-violet align-middle" />{v.window} {r.window.open_utc.slice(11, 16)}–{r.window.close_utc.slice(11, 16)}</span>
            {r.chain.ok && <span>{v.commitLag} {r.chain.max_lag_hours} {v.h}</span>}
            {r.chain.ok && <span>{v.revealWin} {r.chain.reveal_window_hours} {v.h}</span>}
          </div>
        </div>
      )}
    </div>
  );
}

// ---------------------------------------------------------------- 01 stasiun per bot
function say(code: string, x: Station, codes: Record<string, string>, today: string) {
  return (codes[code] ?? code).replace("{d}", x.detail ?? "").replace("{at}", hm(x.at, today));
}

function Bots({ r }: { r: StatusResult }) {
  const { t } = useLang();
  const v = t.status;
  const today = r.window.open_utc.slice(0, 10);
  return (
    <section id="stations" className="relative mt-3 overflow-hidden rounded-[30px] bg-gradient-to-b from-white to-lav px-6 py-20 sm:px-12 lg:px-16">
      <span className="tag text-violet">{v.bots.tag}</span>
      <div className="mt-3 flex flex-col gap-4 lg:flex-row lg:items-end lg:justify-between">
        <h2 className="max-w-3xl font-display text-[clamp(2.2rem,5vw,4.4rem)] font-[300] leading-[0.95] tracking-[-0.03em] text-ink" style={{ fontStretch: "112%" }}>{v.bots.title}</h2>
        <p className="max-w-md text-ink/60">{v.bots.sub}</p>
      </div>
      <div className="mt-12 space-y-8">
        {r.bots.map((b) => {
          const committed = b.stations.some((x) => x.k === "commit" && x.lamp === "ok");
          return (
            <div key={b.bot}>
              <div className="mb-3 flex flex-wrap items-baseline gap-x-4 gap-y-1">
                <Link href={`/bot/${b.bot}`} className="font-display text-2xl font-[700] text-ink underline-offset-4 hover:text-violet hover:underline">{b.bot}</Link>
                <span className="font-mono text-xs text-ink/50">bar {b.bar}</span>
                {committed && <Link href={`/verify?bot=${b.bot}&bar=${b.bar}`} className="font-mono text-xs text-violet underline-offset-4 hover:underline">{v.verifyBar} →</Link>}
              </div>
              <div className="relative">
                <div className="absolute left-8 right-8 top-[42px] hidden h-px bg-gradient-to-r from-violet/10 via-violet/40 to-violet/10 lg:block" />
                <div className="grid grid-cols-2 gap-3 sm:grid-cols-3 lg:grid-cols-6">
                  {b.stations.map((x, i) => (
                    <motion.div key={x.k} initial={{ opacity: 0, y: 16 }} whileInView={{ opacity: 1, y: 0 }} viewport={{ once: true }}
                      transition={{ delay: i * 0.12, type: "spring", stiffness: 120, damping: 16 }}
                      className={`glass relative min-w-0 rounded-[22px] border p-4 ${RING[x.lamp]}`}>
                      <div className="flex items-start justify-between gap-2">
                        <span className="tag text-violet">{String(i + 1).padStart(2, "0")}</span>
                        <div className={x.lamp === "wait" ? "animate-breathe" : ""}>
                          <IsoCube kind={LAMP[x.lamp]} size={32} glow={x.lamp === "ok"} />
                        </div>
                      </div>
                      <div className="mt-2 font-display text-[1.05rem] font-[700] leading-tight text-ink">{v.stations[x.k].h}</div>
                      <div className="text-[0.68rem] leading-snug text-ink/45">{v.stations[x.k].who}</div>
                      <div className={`mt-3 text-[0.78rem] leading-snug ${x.lamp === "alarm" ? "font-semibold text-gap" : "text-ink/75"}`}>{say(x.code, x, v.codes, today)}</div>
                      {x.at && !["TICK_BEFORE_WINDOW", "TICK_IN_WINDOW", "COMMIT_GRACE", "REVEAL_PENDING"].includes(x.code) && (
                        <div className="mt-1 font-mono text-[0.66rem] text-ink/50">{hm(x.at, today)}</div>
                      )}
                      {x.detail && (x.k === "kertas" || x.lamp === "unreadable" || x.code === "TICK_GAP") && (
                        <div className="mt-1 break-words font-mono text-[0.62rem] leading-snug text-ink/45">{x.detail}</div>
                      )}
                      <div className="tag mt-2 text-[0.58rem] text-ink/35">{v.lamps[x.lamp]}</div>
                    </motion.div>
                  ))}
                </div>
              </div>
            </div>
          );
        })}
      </div>
    </section>
  );
}

// ---------------------------------------------------------------- 02 mesin: gas, chain, snapshot
function Plant({ r }: { r: StatusResult }) {
  const { t } = useLang();
  const v = t.status;
  return (
    <section id="plant" className="relative mt-3 overflow-hidden rounded-[30px] bg-night px-6 py-20 text-white sm:px-12 lg:px-16">
      <div className="pointer-events-none absolute -left-40 bottom-0 h-[420px] w-[420px] rounded-full bg-violet/20 blur-[150px]" />
      <span className="tag text-violet-2">{v.plant.tag}</span>
      <div className="mt-3 flex flex-col gap-4 lg:flex-row lg:items-end lg:justify-between">
        <h2 className="max-w-3xl font-display text-[clamp(2.2rem,5vw,4.4rem)] font-[300] leading-[0.95] tracking-[-0.03em]" style={{ fontStretch: "112%" }}>{v.plant.title}</h2>
        <p className="max-w-md text-white/60">{v.plant.sub}</p>
      </div>
      <div className="relative mt-12 grid gap-4 lg:grid-cols-3">
        <div className="glass-dark rounded-[24px] p-6">
          <div className="tag text-white/45">{v.gas.h}</div>
          {r.gas.ok ? <Gauge g={r.gas} /> : <Unreadable error={r.gas.error} />}
        </div>
        <div className="glass-dark rounded-[24px] p-6">
          <div className="tag text-white/45">{v.chain.h}</div>
          {r.chain.ok ? (
            <div className="mt-5">
              <div className="font-mono text-3xl font-semibold tabular-nums">#{r.chain.block.toLocaleString("en-US")}</div>
              <div className="mt-1 font-mono text-xs text-white/50">{v.chain.block} · {r.chain.block_utc}</div>
              <div className="mt-6 font-display text-4xl font-[700] tabular-nums">{r.chain.commit_count}</div>
              <div className="text-sm text-white/55">{v.chain.commits}</div>
              <a href={`${LINKS.scan}${r.chain.signal_anchor}`} target="_blank" rel="noreferrer" className="mt-4 inline-block font-mono text-xs text-violet-2 underline-offset-4 hover:underline">SignalAnchor ↗</a>
            </div>
          ) : <Unreadable error={r.chain.error} />}
        </div>
        <div className="glass-dark rounded-[24px] p-6">
          <div className="tag text-white/45">{v.snap.h}</div>
          <div className="mt-5 font-mono text-xl font-semibold">{r.snapshot.generated_utc.slice(0, 10)} {r.snapshot.generated_utc.slice(11, 16)} UTC</div>
          <div className="mt-1 font-mono text-xs text-white/50">{v.snap.printed}{r.snapshot.block ? ` · ${v.snap.block} #${r.snapshot.block.toLocaleString("en-US")}` : ""}</div>
          <div className="mt-6 flex items-center gap-3">
            <IsoCube kind="sealed" size={40} />
            <code className="font-mono text-[0.7rem] text-violet-2">tools/web_snapshot.py --if-changed</code>
          </div>
        </div>
      </div>
    </section>
  );
}

function Unreadable({ error }: { error: string }) {
  const { t } = useLang();
  return (
    <div className="mt-5">
      <div className="flex items-center gap-2 text-white/75"><IsoCube kind="empty" size={26} />{t.status.lamps.unreadable}</div>
      <pre className="mt-2 whitespace-pre-wrap break-all font-mono text-[0.68rem] text-white/45">{error}</pre>
    </div>
  );
}

/** Tangki horizontal: isi = saldo; dua garis = alert operator (0,01) dan ambang isi-ulang builder (0,1). */
function Gauge({ g }: { g: Extract<StatusResult["gas"], { ok: true }> }) {
  const { t } = useLang();
  const v = t.status.gas;
  const max = Math.max(0.2, g.balance_tbnb * 1.25);
  const pct = (x: number) => `${Math.min(100, (x / max) * 100)}%`;
  return (
    <div className="mt-5">
      <div className="flex items-baseline gap-2">
        <span className={`font-mono text-3xl font-semibold tabular-nums ${g.lamp === "alarm" ? "text-gap" : ""}`}>{g.balance_tbnb}</span>
        <span className="text-sm text-white/55">{v.unit}</span>
      </div>
      <div className="relative mt-5 h-9 overflow-hidden rounded-full border border-violet-2/25 bg-white/5">
        <motion.div className={`absolute inset-y-0 left-0 ${g.lamp === "alarm" ? "bg-gap/70" : "bg-gradient-to-r from-violet to-violet-2"}`}
          initial={{ width: 0 }} whileInView={{ width: pct(g.balance_tbnb) }} viewport={{ once: true }} transition={{ type: "spring", stiffness: 50, damping: 14 }} />
        <div className="absolute inset-y-0 border-l border-dashed border-gap/80" style={{ left: pct(g.alert_below) }} />
        <div className="absolute inset-y-0 border-l border-dashed border-white/70" style={{ left: pct(g.refill_below) }} />
      </div>
      <div className="relative mt-2 h-8 font-mono text-[0.6rem] text-white/50">
        <span className="absolute -translate-x-1/2 whitespace-nowrap" style={{ left: pct(g.alert_below) }}>{g.alert_below}</span>
        <span className="absolute -translate-x-1/2 whitespace-nowrap" style={{ left: pct(g.refill_below) }}>{g.refill_below} · {v.refill}</span>
      </div>
      <div className="font-mono text-[0.62rem] text-white/40">{g.alert_below} = {v.alert}</div>
      <a href={`${LINKS.scan}${g.committer}`} target="_blank" rel="noreferrer" className="mt-3 inline-block break-all font-mono text-[0.68rem] text-violet-2 underline-offset-4 hover:underline">{g.committer} ↗</a>
    </div>
  );
}

// ---------------------------------------------------------------- 03 detak rantai GitHub
function runKind(x: Run): { kind: Kind; key: "success" | "failure" | "running" | "other" } {
  if (x.status !== "completed") return { kind: "pending", key: "running" };
  if (x.conclusion === "success") return { kind: "verified", key: "success" };
  if (x.conclusion === "failure" || x.conclusion === "timed_out") return { kind: "missed", key: "failure" };
  return { kind: "empty", key: "other" };
}

function Beat({ r }: { r: StatusResult }) {
  const { t } = useLang();
  const v = t.status.beat;
  const runs = r.actions.ok ? [...r.actions.runs].reverse() : [];
  return (
    <section id="heartbeat" className="relative mt-3 overflow-hidden rounded-[30px] bg-gradient-to-b from-lav to-white px-6 py-20 sm:px-12 lg:px-16">
      <span className="tag text-violet">{v.tag}</span>
      <div className="mt-3 flex flex-col gap-4 lg:flex-row lg:items-end lg:justify-between">
        <h2 className="max-w-3xl font-display text-[clamp(2.2rem,5vw,4.4rem)] font-[300] leading-[0.95] tracking-[-0.03em] text-ink" style={{ fontStretch: "112%" }}>{v.title}</h2>
        <p className="max-w-md text-ink/60">{v.sub}</p>
      </div>
      <div className="glass mt-10 overflow-x-auto rounded-[26px] p-5 sm:p-8">
        {r.actions.ok ? (
          <div className="flex w-max min-w-full items-end gap-4">
            {runs.map((x, i) => {
              const k = runKind(x);
              const mins = Math.round((Date.parse(x.updated_utc) - Date.parse(x.started_utc)) / 60000);
              return (
                <motion.a key={x.url} href={x.url} target="_blank" rel="noreferrer" initial={{ opacity: 0, y: 12 }} whileInView={{ opacity: 1, y: 0 }} viewport={{ once: true }}
                  transition={{ delay: i * 0.06 }} className="flex w-[96px] flex-col items-center rounded-2xl px-2 py-2 transition hover:bg-white/70" title={`${x.status} ${x.conclusion ?? ""}`}>
                  <div className={k.key === "running" ? "animate-breathe" : ""}><IsoCube kind={k.kind} size={40} glow={k.key === "success"} /></div>
                  <div className="mt-2 font-mono text-[0.68rem] text-ink">{x.started_utc.slice(5, 10)} {x.started_utc.slice(11, 16)}</div>
                  <div className="text-[0.66rem] text-ink/50">{v[k.key]} · {mins} min</div>
                </motion.a>
              );
            })}
          </div>
        ) : (
          <div>
            <div className="flex items-center gap-3 text-ink/70"><IsoCube kind="empty" size={28} />{t.status.lamps.unreadable}</div>
            <pre className="mt-2 whitespace-pre-wrap break-all font-mono text-xs text-ink/50">{r.actions.error}</pre>
          </div>
        )}
        <a href={ACTIONS} target="_blank" rel="noreferrer" className="mt-4 inline-block font-mono text-xs text-violet underline-offset-4 hover:underline">{v.open} ↗</a>
      </div>
    </section>
  );
}
