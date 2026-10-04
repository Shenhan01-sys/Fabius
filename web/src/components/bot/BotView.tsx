"use client";

// /bot/[id] (docs/design/bot.md): satu bot = satu MESIN TERKUNCI. Kepala (aturan asli + kunci) -> buku paper hari ini (universe = deret kubus; terang =
// dipegang, bening = flat) -> hari demi hari (satu kubus per hari tutup, menaut ke /verify) -> kunci yang mengikatnya, urut waktu bersama tick pertama ->
// tangki F-D16 -> kapan ia dimatikan (teks asli terkunci + syarat mesin). Bot tanpa jam maju: kepala + kunci + pembunuh saja. Nomor section dihitung,
// jadi bot tanpa jam maju tidak punya nomor yang bolong.

import Link from "next/link";
import { motion } from "motion/react";
import type { ReactNode } from "react";
import { LangProvider, useLang } from "../lang";
import Nav from "../Nav";
import IsoCube from "../ui/IsoCube";
import StatusBadge from "../ui/StatusBadge";
import { Claims, Footer } from "../sections/Closing";
import { Tank } from "../sections/ProofFeed";
import { GLOSS, LINKS } from "@/lib/copy";
import { addDays, cellState, short, type Bot, type CellState, type Snapshot } from "@/lib/snapshot";

export type LiveTick = { date: string; signals: number; held: number; lag_s: number | null };
export type Live =
  | {
      ok: true;
      read_utc: string;
      ticks: LiveTick[];
      gaps: string[];
      latest: null | { date: string; emitted_utc: string | null; signals: number; targets: Record<string, number>; prev: Record<string, number> };
    }
  | { ok: false; error: string };

export type ExecOrder = {
  aset: string;
  sisi: string;
  qty: number;
  px: number;
  ref_tutup: number | null;
  kertas_px: number | null;
  fee_bps: number | null;
  geser_bps: number | null;
  slip_bps: number | null;
  selisih_kertas_bps: number | null;
};
export type ExecRow = {
  bar: string;
  susulan?: boolean;
  mode: string;
  n_order: number;
  komit_utc: string | null;
  latensi_s: number | null;
  fee: number;
  notional: number;
  bobot_terpenuhi: number | null;
  pelanggaran: string[];
  orders: ExecOrder[];
};
export type Exec = { ok: true; rows: ExecRow[] } | { ok: false; error: string } | null;

const SHADOW_NEED = 60;
const EPS = 1e-12;
const tag = (n: number, label: string) => `${String(n).padStart(2, "0")} — ${label}`;
const utc = (iso: string | null | undefined) => (iso ? `${iso.slice(0, 10)} ${iso.slice(11, 16)} UTC` : "—");

function Lock({ className = "" }: { className?: string }) {
  return (
    <svg viewBox="0 0 20 20" width="14" height="14" className={className} aria-hidden>
      <rect x="4" y="9" width="12" height="9" rx="2" fill="currentColor" fillOpacity=".15" stroke="currentColor" strokeWidth="1.6" />
      <path d="M7 9V6.5a3 3 0 0 1 6 0V9" fill="none" stroke="currentColor" strokeWidth="1.6" />
    </svg>
  );
}

export default function BotView({ s, id, live, exec = null }: { s: Snapshot; id: string; live: Live | null; exec?: Exec }) {
  const b = s.bots.find((x) => x.id === id)!;
  const fwd = b.forward && !!s.ledger[b.id];
  let n = 0;
  return (
    <LangProvider>
      <div className="p-2 sm:p-3">
        <Nav />
        <Head s={s} b={b} fwd={fwd} />
        {fwd && <Paper n={++n} b={b} live={live} />}
        {fwd && <Days n={++n} s={s} b={b} live={live} />}
        {fwd && exec && <Executed n={++n} exec={exec} />}
        <Locks n={++n} s={s} b={b} fwd={fwd} />
        {fwd && <Fd16 n={++n} s={s} b={b} />}
        <Kill n={++n} s={s} b={b} />
        <Claims />
        <Footer s={s} />
      </div>
    </LangProvider>
  );
}

function Title({ label, title, sub, dark = false }: { label: string; title: string; sub: string; dark?: boolean }) {
  return (
    <>
      <span className={`tag ${dark ? "text-violet-2" : "text-violet"}`}>{label}</span>
      <div className="mt-3 flex flex-col gap-4 lg:flex-row lg:items-end lg:justify-between">
        <h2 className={`max-w-3xl font-display text-[clamp(2.2rem,5vw,4.4rem)] font-[300] leading-[0.95] tracking-[-0.03em] ${dark ? "text-white" : "text-ink"}`} style={{ fontStretch: "112%" }}>
          {title}
        </h2>
        <p className={`max-w-md ${dark ? "text-white/60" : "text-ink/60"}`}>{sub}</p>
      </div>
    </>
  );
}

function Chip({ children, dark = false }: { children: ReactNode; dark?: boolean }) {
  return <span className={`inline-flex max-w-full flex-wrap items-center gap-1.5 rounded-[18px] px-3.5 py-1.5 font-mono text-[0.72rem] ${dark ? "bg-white/10 text-white/75" : "bg-white/80 text-ink/70"}`}>{children}</span>;
}

// ---------------------------------------------------------------- kepala: nama, aturan asli, kunci spesifikasi, peran di buku
function Head({ s, b, fwd }: { s: Snapshot; b: Bot; fwd: boolean }) {
  const { t, lang } = useLang();
  const v = t.bot;
  const [code, ...rest] = b.id.split("-");
  const slot = s.book.occupants.findIndex((o) => o.id === b.id);
  const ch = s.book.challengers.find((c) => c.id === b.id);
  const shadow = ch ? (s.ledger[b.id]?.days_live ?? ch.shadow_days) : 0;
  const specLock = s.locks.find((l) => l.label === `SPEC ${b.id}`);
  const kind = slot >= 0 ? "core" : ch ? "sealed" : "empty";
  const gloss = lang === "en" ? GLOSS.methods[b.id] : null;
  return (
    <section id="top" className="relative overflow-hidden rounded-[30px] bg-gradient-to-b from-lav via-lav to-white px-6 pb-20 pt-32 sm:px-12 sm:pt-40 lg:px-16">
      <div className="pointer-events-none absolute -right-32 top-24 h-[420px] w-[420px] rounded-full bg-violet/15 blur-[130px]" />
      <span className="tag text-violet">{v.tag}</span>
      <div className="relative mt-4 grid gap-10 lg:grid-cols-[1fr_auto] lg:items-end">
        <div className="min-w-0">
          <h1 className="font-display leading-[0.88] tracking-[-0.035em] text-ink">
            <span className="block text-[clamp(3rem,9vw,8.5rem)] font-[300]" style={{ fontStretch: "112%" }}>{code}</span>
            <span className="block break-words text-[clamp(2.4rem,7.6vw,7.2rem)] font-[800] italic text-violet" style={{ fontStretch: "78%" }}>{rest.join("-")}</span>
          </h1>
          <div className="mt-6 inline-flex items-center gap-2 rounded-full bg-ink px-4 py-2 text-sm font-semibold text-white">
            <IsoCube kind={kind} size={18} glow={kind === "core"} />
            {slot >= 0 ? `${v.role.identity} ${String(slot + 1).padStart(2, "0")}` : ch ? `${v.role.challenger} ${shadow}/${SHADOW_NEED} d · gate ${ch.gate}` : v.role.idle}
          </div>
          <div className="mt-3 max-w-xl">
            <StatusBadge b={b} note />
          </div>
        </div>
        <motion.div initial={{ opacity: 0, scale: 0.85, rotate: -6 }} animate={{ opacity: 1, scale: 1, rotate: 0 }} transition={{ type: "spring", stiffness: 70, damping: 12 }}
          className="hidden justify-self-end lg:block">
          <div className="animate-breathe">
            <IsoCube kind={kind} size={190} glow={kind === "core"} />
          </div>
        </motion.div>
      </div>

      {/* aturan, persis seperti dikunci */}
      <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.25, type: "spring", stiffness: 90, damping: 16 }}
        className="glass relative mt-12 rounded-[26px] p-6 sm:p-8">
        <div className="tag text-ink/45">{v.rule}</div>
        <p className="mt-3 max-w-4xl font-display text-[clamp(1.25rem,2.2vw,1.7rem)] font-[400] leading-snug text-ink" lang="id">“{b.method}”</p>
        {gloss && (
          <p className="mt-4 max-w-3xl border-l-2 border-violet/30 pl-4 text-[0.95rem] text-ink/60">
            <span className="tag mb-1 block text-ink/35">{v.gloss}</span>
            {gloss}
          </p>
        )}
        <div className="mt-6 flex flex-wrap gap-2">
          <Chip>{v.param} · {b.param}</Chip>
          <Chip>{v.tier} {b.tier}</Chip>
          <Chip>{b.universe?.length ?? b.assets} {v.assets}</Chip>
          {fwd && <Chip>{v.clock} {s.ledger[b.id].genesis}</Chip>}
          {specLock?.tx ? (
            <a href={`${LINKS.tx}${specLock.tx}`} target="_blank" rel="noreferrer"
              className="inline-flex max-w-full flex-wrap items-center gap-x-1.5 rounded-[18px] bg-violet px-3.5 py-1.5 font-mono text-[0.72rem] text-white transition hover:bg-ink">
              <Lock /> <span>{v.specLocked}</span> <span>· {short(b.spec_sha, 6)}</span> <span>· {utc(specLock.at_utc)} ↗</span>
            </a>
          ) : (
            <Chip><Lock className="text-ink/40" /> {v.specHashed} · {short(b.spec_sha, 6)}</Chip>
          )}
        </div>
      </motion.div>

      {!fwd && (
        <div className="glass mt-4 flex items-center gap-4 rounded-[24px] p-5">
          <IsoCube kind="empty" size={34} />
          <p className="max-w-3xl text-sm text-ink/65">{v.idle}</p>
        </div>
      )}
    </section>
  );
}

// ---------------------------------------------------------------- 01 buku paper hari ini: universe sebagai deret kubus
function Paper({ n, b, live }: { n: number; b: Bot; live: Live | null }) {
  const { t } = useLang();
  const v = t.bot.book;
  const head = <Title label={tag(n, v.tag)} title={v.title} sub={v.sub} dark />;
  const wrap = (body: ReactNode) => (
    <section id="book" className="relative mt-3 overflow-hidden rounded-[30px] bg-night px-6 py-20 text-white sm:px-12 lg:px-16">
      <div className="pointer-events-none absolute -right-40 top-10 h-[480px] w-[480px] rounded-full bg-violet/20 blur-[150px]" />
      {head}
      {body}
    </section>
  );
  if (!live || !live.ok)
    return wrap(
      <div className="mt-10 rounded-[26px] border border-gap/50 bg-white/5 p-6">
        <div className="flex items-center gap-3 font-semibold"><IsoCube kind="gap" size={26} />{v.error}</div>
        {live && !live.ok && <pre className="mt-3 whitespace-pre-wrap break-all font-mono text-xs text-white/55">{live.error}</pre>}
      </div>,
    );
  const L = live.latest;
  if (!L) return wrap(<div className="glass-dark mt-10 rounded-[26px] p-6 text-white/60">{v.none}</div>);
  const uni = b.universe ?? [];
  const assets = [...uni, ...Object.keys(L.targets).filter((a) => !uni.includes(a))];
  const w = (a: string) => L.targets[a] ?? 0;
  const held = assets.filter((a) => Math.abs(w(a)) > EPS);
  const gross = held.reduce((x, a) => x + Math.abs(w(a)), 0);
  return wrap(
    <div className="glass-dark relative mt-10 rounded-[26px] p-5 sm:p-8">
      <div className="flex flex-wrap items-center gap-x-6 gap-y-2 font-mono text-[0.75rem] text-white/55">
        <span className="font-display text-2xl font-[700] tabular-nums text-white">
          {held.length}<span className="text-white/35">/{assets.length}</span> <span className="font-sans text-sm font-medium text-white/55">{v.held}</span>
        </span>
        <span>{v.asof} {L.date}</span>
        <span>{v.written} {utc(L.emitted_utc)}</span>
        <span>{v.gross} {(gross * 100).toFixed(2)} %</span>
        <Link href={`/verify?bot=${b.id}&bar=${L.date}`} className="text-violet-2 underline-offset-4 hover:underline sm:ml-auto">{v.verify} →</Link>
      </div>
      <div className="mt-8 grid grid-cols-4 gap-x-2 gap-y-7 sm:grid-cols-8">
        {assets.map((a, i) => {
          const x = w(a);
          const was = L.prev[a] ?? 0;
          const on = Math.abs(x) > EPS;
          const badge = on && Math.abs(was) <= EPS ? v.entered : !on && Math.abs(was) > EPS ? v.exited : null;
          return (
            <motion.div key={a} initial={{ opacity: 0, y: 14 }} whileInView={{ opacity: 1, y: 0 }} viewport={{ once: true }}
              transition={{ delay: i * 0.03, type: "spring", stiffness: 180, damping: 16 }} className="relative flex flex-col items-center"
              title={`${a} · ${on ? `${(x * 100).toFixed(2)} %` : v.flat}`}>
              <div className={on ? "animate-breathe" : "opacity-25"}>
                <IsoCube kind={x > EPS ? "core" : x < -EPS ? "sealed" : "empty"} size={52} glow={x > EPS} />
              </div>
              <div className={`mt-2 font-display text-sm font-[700] ${on ? "text-white" : "text-white/40"}`}>{a.replace(/USDT$/, "")}</div>
              <div className={`font-mono text-[0.68rem] ${on ? "text-violet-2" : "text-white/30"}`}>{on ? `${x < 0 ? `${v.short} ` : ""}${(Math.abs(x) * 100).toFixed(2)} %` : v.flat}</div>
              {badge && (
                <span className={`absolute -top-2 right-0 rounded-full px-1.5 py-0.5 font-mono text-[0.55rem] font-bold uppercase ${badge === v.entered ? "bg-violet text-white" : "border border-white/25 bg-night-2 text-white/60"}`}>
                  {badge}
                </span>
              )}
            </motion.div>
          );
        })}
      </div>
      <div className="mt-8 flex flex-wrap gap-x-6 gap-y-2 text-[0.8rem] text-white/60">
        <span className="flex items-center gap-2"><IsoCube kind="core" size={18} glow />{v.held}</span>
        <span className="flex items-center gap-2"><IsoCube kind="sealed" size={18} />{v.short}</span>
        <span className="flex items-center gap-2"><span className="opacity-25"><IsoCube kind="empty" size={18} /></span>{v.flat}</span>
        <span className="font-mono text-[0.68rem] text-white/35 sm:ml-auto">ledger/paper/{b.id}.jsonl · {live.read_utc}</span>
      </div>
    </div>,
  );
}

// ---------------------------------------------------------------- 02 hari demi hari: satu kubus per hari tutup sejak jam mulai
function Days({ n, s, b, live }: { n: number; s: Snapshot; b: Bot; live: Live | null }) {
  const { t } = useLang();
  const v = t.bot.days;
  const L = s.ledger[b.id];
  const lv = live?.ok ? live : null;
  const ticks = new Map<string, LiveTick>([...L.ticks, ...(lv?.ticks ?? [])].map((x) => [x.date, x])); // live menimpa snapshot
  const gaps = new Set([...L.gaps.map((g) => g.date), ...(lv?.gaps ?? [])]);
  const end = [L.last_closed, ...ticks.keys()].sort().at(-1)!;
  const days: string[] = [];
  for (let d = L.genesis; d <= end; d = addDays(d, 1)) days.push(d);
  return (
    <section id="days" className="relative mt-3 overflow-hidden rounded-[30px] bg-gradient-to-b from-lav to-white px-6 py-20 sm:px-12 lg:px-16">
      <Title label={tag(n, v.tag)} title={v.title} sub={v.sub} />
      <div className="glass mt-10 overflow-x-auto rounded-[26px] p-5 sm:p-8">
        <div className="relative flex w-max min-w-full gap-3 sm:gap-5">
          <div className="absolute left-6 right-6 top-[38px] h-px bg-gradient-to-r from-violet/10 via-violet/35 to-violet/10" />
          {days.map((d, i) => {
            const tk = ticks.get(d);
            const raw = cellState(s, b.id, d);
            const st: CellState = gaps.has(d) ? "gap" : raw === "future" ? "pending" : raw; // hari sudah tutup: tidak pernah "belum"
            const label = st === "pending" && !tk ? v.noTick : t.proof.states[st];
            return (
              <motion.div key={d} initial={{ opacity: 0, y: 14 }} whileInView={{ opacity: 1, y: 0 }} viewport={{ once: true }}
                transition={{ delay: i * 0.06, type: "spring", stiffness: 170, damping: 16 }}>
                <Link href={`/verify?bot=${b.id}&bar=${d}`} aria-label={`${t.verify.fromCalendar}: ${b.id} ${d}`}
                  className="group relative flex w-[118px] flex-col items-center rounded-2xl px-2 pb-3 pt-2 transition hover:-translate-y-0.5 hover:bg-white/70">
                  <div className={st === "pending" ? "animate-breathe" : ""}>
                    <IsoCube kind={st} size={56} glow={st === "verified"} />
                  </div>
                  {tk && tk.signals > 0 && (
                    <span className="absolute right-4 top-1 grid h-5 min-w-5 place-items-center rounded-full bg-violet px-1 font-mono text-[0.62rem] font-bold text-white">{tk.signals}</span>
                  )}
                  <div className="mt-2 font-mono text-sm font-semibold text-ink">{d.slice(5)}</div>
                  <div className="text-center text-[0.7rem] leading-tight text-ink/55 group-hover:text-violet">{label}</div>
                  {tk?.lag_s != null && <div className="mt-1 whitespace-nowrap font-mono text-[0.62rem] text-ink/40">{(tk.lag_s / 3600).toFixed(1)} {v.afterClose}</div>}
                </Link>
              </motion.div>
            );
          })}
          <div className="flex w-[118px] flex-col items-center px-2 pt-2 opacity-70">
            <IsoCube kind="future" size={56} />
            <div className="mt-2 font-mono text-sm text-ink/45">{addDays(end, 1).slice(5)}</div>
            <div className="text-[0.7rem] text-ink/40">{v.next}</div>
          </div>
        </div>
      </div>
    </section>
  );
}

// ---------------------------------------------------------------- eksekusi demo: keputusan yang sama tiga kali - paper, kertas, isi nyata (P119)
const median = (xs: number[]) => {
  if (!xs.length) return null;
  const a = [...xs].sort((p, q) => p - q);
  const m = Math.floor(a.length / 2);
  return a.length % 2 ? a[m] : (a[m - 1] + a[m]) / 2;
};
const worseBps = (side: string, px: number, ref: number) => (px / ref - 1) * 1e4 * (side === "BUY" ? 1 : -1); // + = lebih buruk bagi kita
const dur = (s: number | null) => (s == null ? "—" : s < 3600 ? `${Math.round(s / 60)} min` : `${(s / 3600).toFixed(1)} h`);
const sbps = (x: number | null) => (x == null ? "—" : `${x > 0 ? "+" : ""}${x.toFixed(1)} bps`);
const ubps = (x: number | null) => (x == null ? "—" : `${x.toFixed(1)} bps`); // tanpa tanda: fee selalu biaya

/** Sumbu bps: 0 = penutupan bar (isi paper), lalu posisi isi kertas dan isi nyata. Kanan = lebih buruk bagi kita. */
function Axis({ kertas, real }: { kertas: number | null; real: number | null }) {
  const { t } = useLang();
  const v = t.bot.exec;
  const r = Math.max(20, Math.ceil(Math.max(Math.abs(kertas ?? 0), Math.abs(real ?? 0)) / 10) * 10);
  const pos = (b: number) => 50 + (b / r) * 46;
  // label di dekat tepi kartu disejajarkan ke dalam supaya tidak terpotong
  const align = (p: number) => (p > 72 ? "-translate-x-full text-right" : p < 28 ? "text-left" : "-translate-x-1/2 text-center");
  const mark = (b: number | null, kind: "sealed" | "verified", label: string, top: boolean) =>
    b == null ? null : (
      <div className={`absolute ${align(pos(b))}`} style={{ left: `${pos(b)}%`, top: top ? 0 : 34 }}>
        {!top && <div className={`inline-block ${pos(b) > 72 ? "translate-x-1/2" : pos(b) < 28 ? "-translate-x-1/2" : ""}`}><IsoCube kind={kind} size={18} glow={kind === "verified"} /></div>}
        <div className="whitespace-nowrap font-mono text-[0.6rem] text-ink/60">{label} {sbps(b)}</div>
        {top && <div className={`inline-block ${pos(b) > 72 ? "translate-x-1/2" : pos(b) < 28 ? "-translate-x-1/2" : ""}`}><IsoCube kind={kind} size={18} /></div>}
      </div>
    );
  return (
    <div className="mt-4">
      <div className="relative h-[72px]">
        <div className="absolute inset-x-[4%] top-[33px] h-px bg-violet/25" />
        <div className="absolute top-[24px] h-[18px] w-px -translate-x-1/2 bg-ink/50" style={{ left: "50%" }} title={v.paper} />
        {mark(kertas, "sealed", v.kertas, true)}
        {mark(real, "verified", v.real, false)}
      </div>
      <div className="mt-1 flex items-center gap-1.5 font-mono text-[0.58rem] text-ink/40">
        <span className="inline-block h-2.5 w-px bg-ink/50" /> {v.paper}
      </div>
    </div>
  );
}

function Executed({ n, exec }: { n: number; exec: NonNullable<Exec> }) {
  const { t } = useLang();
  const v = t.bot.exec;
  const head = <Title label={tag(n, v.tag)} title={v.title} sub={v.sub} />;
  const wrap = (body: ReactNode) => (
    <section id="executed" className="relative mt-3 overflow-hidden rounded-[30px] bg-gradient-to-b from-white to-lav px-6 py-20 sm:px-12 lg:px-16">
      {head}
      {body}
    </section>
  );
  if (!exec.ok)
    return wrap(
      <div className="mt-10 rounded-[26px] border border-gap/50 bg-white/80 p-6">
        <div className="flex items-center gap-3 font-semibold text-ink"><IsoCube kind="gap" size={26} />{v.error}</div>
        <pre className="mt-3 whitespace-pre-wrap break-all font-mono text-xs text-ink/55">{exec.error}</pre>
      </div>,
    );
  const rows = exec.rows;
  const demoRows = rows.filter((r) => r.mode !== "live");                     // ringkasan mekanisme dari akun demo; uang NYATA ditampilkan terpisah
  const realFilled = rows.filter((r) => r.mode === "live").flatMap((r) => r.orders.filter((o) => o.qty > 0));
  const filled = demoRows.flatMap((r) => r.orders.filter((o) => o.qty > 0));
  const fee = median(filled.flatMap((o) => (o.fee_bps == null ? [] : [o.fee_bps])));
  const vsK = median(filled.flatMap((o) => (o.selisih_kertas_bps == null ? [] : [o.selisih_kertas_bps])));
  const lat = median(demoRows.flatMap((r) => (r.latensi_s == null ? [] : [r.latensi_s])));
  const viol = rows.reduce((k, r) => k + (r.pelanggaran?.length ?? 0), 0);
  const chips: [string, string, string, boolean][] = [
    [v.fee, ubps(fee), "≤ 7 bps", fee == null || fee <= 7],
    [v.vsKertas, sbps(vsK), v.info, true],
    [v.latency, dur(lat), "p95 ≤ 10 min", lat == null || lat <= 600],
    [v.violations, String(viol), "0", viol === 0],
  ];
  if (realFilled.length) {
    const rf = median(realFilled.flatMap((o) => (o.fee_bps == null ? [] : [o.fee_bps])));
    chips.push([v.realFills, `${realFilled.length} · ${ubps(rf)}`, v.realNote, true]);
  }
  return wrap(
    <>
      <div className={`mt-10 grid grid-cols-2 gap-3 ${chips.length > 4 ? "lg:grid-cols-5" : "lg:grid-cols-4"}`}>
        {chips.map(([k, val, target, ok]) => (
          <div key={k} className={`glass rounded-[22px] border p-4 ${ok ? "border-white/70" : "border-gap/50"}`}>
            <div className="tag text-ink/45">{k}</div>
            <div className={`mt-2 font-mono text-2xl font-semibold tabular-nums ${ok ? "text-ink" : "text-gap"}`}>{val}</div>
            <div className="mt-1 font-mono text-[0.62rem] text-ink/40">{v.target} {target}</div>
          </div>
        ))}
      </div>
      <div className="glass mt-4 overflow-x-auto rounded-[26px] p-5 sm:p-7">
        <div className="flex w-max min-w-full gap-4">
          {rows.map((r, i) => {
            const fo = r.orders.filter((o) => o.qty > 0);
            const kGeser = median(fo.flatMap((o) => (o.kertas_px && o.ref_tutup ? [worseBps(o.sisi, o.kertas_px, o.ref_tutup)] : [])));
            const rGeser = median(fo.flatMap((o) => (o.geser_bps == null ? [] : [o.geser_bps])));
            return (
              <motion.div key={`${r.bar}-${r.mode}`} initial={{ opacity: 0, y: 14 }} whileInView={{ opacity: 1, y: 0 }} viewport={{ once: true }}
                transition={{ delay: i * 0.08, type: "spring", stiffness: 150, damping: 16 }}
                className={`w-[300px] shrink-0 rounded-[22px] border bg-white/70 p-4 ${r.pelanggaran?.length ? "border-gap/60" : r.mode === "live" ? "border-violet ring-1 ring-violet/40" : "border-white/80"}`}>
                <div className="flex items-start justify-between gap-2">
                  <div>
                    <div className="font-mono text-sm font-semibold text-ink">{r.bar}</div>
                    <div className="font-mono text-[0.62rem] text-ink/45">{r.mode} · {v.latency} {dur(r.latensi_s)}</div>
                  </div>
                  <div className="flex items-center gap-2">
                    <span className={`rounded-full px-2 py-0.5 font-mono text-[0.55rem] font-bold uppercase ${r.mode === "live" ? "bg-violet text-white" : "border border-ink/20 text-ink/55"}`}>
                      {r.mode === "live" ? v.badgeReal : v.badgeDemo}
                    </span>
                    {r.susulan && <span className="rounded-full border border-ink/20 px-2 py-0.5 font-mono text-[0.55rem] uppercase text-ink/55">{v.backfill}</span>}
                    <span className="grid h-6 min-w-6 place-items-center rounded-full bg-violet px-1.5 font-mono text-[0.68rem] font-bold text-white">{r.n_order}</span>
                  </div>
                </div>
                {fo.length ? (
                  <Axis kertas={kGeser} real={rGeser} />
                ) : (
                  <div className="mt-4 flex h-[72px] items-center gap-3 text-[0.78rem] text-ink/60">
                    <IsoCube kind="core" size={26} glow />
                    <span>{v.none}{r.bobot_terpenuhi != null ? ` · ${v.filled} ${(r.bobot_terpenuhi * 100).toFixed(1)} %` : ""}</span>
                  </div>
                )}
                <div className="mt-2 flex flex-wrap gap-x-3 gap-y-1 font-mono text-[0.62rem] text-ink/55">
                  {fo.length > 0 && <span>{v.fee} {ubps(median(fo.flatMap((o) => (o.fee_bps == null ? [] : [o.fee_bps]))))}</span>}
                  {fo.length > 0 && <span>{v.notional} {r.notional.toFixed(0)}</span>}
                  <span className={r.pelanggaran?.length ? "font-semibold text-gap" : ""}>{v.violations} {r.pelanggaran?.length ?? 0}</span>
                </div>
              </motion.div>
            );
          })}
        </div>
      </div>
      <p className="mt-4 max-w-3xl text-[0.8rem] text-ink/50">{v.note}</p>
    </>,
  );
}

// ---------------------------------------------------------------- 03 kunci yang mengikatnya, urut waktu, bersama tick maju pertama
function Locks({ n, s, b, fwd }: { n: number; s: Snapshot; b: Bot; fwd: boolean }) {
  const { t } = useLang();
  const v = t.bot.locks;
  const inBook = s.book.occupants.some((o) => o.id === b.id) || s.book.challengers.some((c) => c.id === b.id);
  const mine = s.locks.filter(
    (l) =>
      l.label === "THRESHOLDS-v1" ||
      l.label === "FABIUS-FD16-MAJU-v1" ||
      l.label === "FABIUS-ANGGARAN-v1" ||
      l.label === `SPEC ${b.id}` ||
      (inBook && l.label.startsWith("FABIUS-BUKU-")) ||
      ((b.kill_rules?.length ?? 0) > 0 && l.label === "FABIUS-PEMBUNUH-v1"),
  );
  const first = fwd ? s.ledger[b.id].ticks[0] : undefined;
  type Ev = { at: string | null; name: string; where: string; tx: string | null; tick?: boolean };
  const evs: Ev[] = mine.map((l) => ({ at: l.at_utc, name: t.book.lockNames[l.label] ?? l.label, where: l.where, tx: l.tx }));
  if (first?.emitted_utc) evs.push({ at: first.emitted_utc, name: v.firstTick, where: `bar ${first.date} · ledger/paper`, tx: null, tick: true });
  evs.sort((a, c) => (a.at ?? "").localeCompare(c.at ?? ""));
  return (
    <section id="locks" className="relative mt-3 overflow-hidden rounded-[30px] bg-night px-6 py-20 text-white sm:px-12 lg:px-16">
      <div className="pointer-events-none absolute -left-40 bottom-0 h-[420px] w-[420px] rounded-full bg-violet/20 blur-[150px]" />
      <Title label={tag(n, v.tag)} title={v.title} sub={v.sub} dark />
      <div className="relative mt-12">
        <div className="absolute bottom-4 left-[19px] top-4 w-px bg-white/15" />
        <ol className="relative">
          {evs.map((e, i) => (
            <li key={`${e.name}${e.at}`}>
              <motion.a
                href={e.tx ? `${LINKS.tx}${e.tx}` : undefined}
                target="_blank"
                rel="noreferrer"
                initial={{ opacity: 0.2, x: -8 }}
                whileInView={{ opacity: 1, x: 0 }}
                viewport={{ once: true, margin: "-40px" }}
                transition={{ delay: 0.1 + i * 0.12 }}
                className="group relative flex items-start gap-5 py-3"
              >
                <span className={`relative z-10 grid h-10 w-10 shrink-0 place-items-center rounded-xl border ${e.tick ? "border-white/25 bg-night-2" : "border-violet-2/50 bg-[#3a29b8]"}`}>
                  {e.tick ? <IsoCube kind="pending" size={22} /> : <Lock className="text-violet-2" />}
                </span>
                <div className="min-w-0 pt-0.5">
                  <div className={`font-display text-lg font-[650] leading-tight ${e.tx ? "group-hover:text-violet-2" : "text-white/80"}`}>{e.name}{e.tx ? " ↗" : ""}</div>
                  <div className="mt-1 font-mono text-[0.7rem] text-white/50">
                    {utc(e.at)} · <span className="text-violet-2/80">{e.where}</span>{e.tx ? ` · ${short(e.tx, 4)}` : ""}
                  </div>
                </div>
              </motion.a>
            </li>
          ))}
        </ol>
      </div>
    </section>
  );
}

// ---------------------------------------------------------------- 04 uji maju F-D16: tiga tangki
function Fd16({ n, s, b }: { n: number; s: Snapshot; b: Bot }) {
  const { t } = useLang();
  const v = t.bot.fd16;
  const q = s.fd16.required;
  const x = s.fd16.bots[b.id] ?? { signals: 0, days: 0, months: 0 };
  const c = s.confidence?.[b.id];
  return (
    <section id="fd16" className="relative mt-3 overflow-hidden rounded-[30px] bg-gradient-to-b from-white to-lav px-6 py-20 sm:px-12 lg:px-16">
      <Title label={tag(n, v.tag)} title={v.title} sub={v.sub} />
      <div className="mt-12 flex flex-wrap gap-10 sm:gap-16">
        <Tank value={x.signals} need={q.signals} label={t.proof.signals} />
        <Tank value={x.days} need={q.days} label={t.proof.days} />
        <Tank value={x.months} need={q.months} label={t.proof.months} />
      </div>
      {c && (
        <div className="mt-14 max-w-3xl">
          <span className="tag text-violet">{v.conf}</span>
          <p className="mt-3 font-display text-[clamp(2.6rem,6vw,4.6rem)] font-[300] leading-none tracking-[-0.03em] text-ink" style={{ fontStretch: "112%" }}>
            {c.confidence_pct == null ? "—" : `${c.confidence_pct}%`}
          </p>
          <p className="mt-3 text-ink">
            {c.confidence_pct == null ? v.confNone : c.fd16 === "BELUM CUKUP DATA" ? v.confEarly : v.confOk}
            {c.rekam.mean_bps != null && ` · ${c.rekam.mean_bps >= 0 ? "+" : ""}${c.rekam.mean_bps.toFixed(2)} bps/${v.day} · CI [${c.rekam.ci_lo_bps?.toFixed(2)}, ${c.rekam.ci_hi_bps?.toFixed(2)}]`}
          </p>
          <p className="mt-2 max-w-2xl text-sm text-ink/60">{v.confBasis}</p>
        </div>
      )}
    </section>
  );
}

// ---------------------------------------------------------------- 05 kapan ia dimatikan: teks asli terkunci + syarat yang diperiksa mesin
function Kill({ n, s, b }: { n: number; s: Snapshot; b: Bot }) {
  const { t, lang } = useLang();
  const v = t.bot.kill;
  const rules = b.kill_rules ?? [];
  const lock = rules.length ? s.locks.find((l) => l.label === "FABIUS-PEMBUNUH-v1") : undefined;
  const gloss = lang === "en" ? GLOSS.killers[b.id] : null;
  return (
    <section id="kill" className="relative mt-3 overflow-hidden rounded-[30px] bg-night-2 px-6 py-20 text-white sm:px-12 lg:px-16">
      <div className="pointer-events-none absolute -right-40 top-0 h-[420px] w-[420px] rounded-full bg-gap/10 blur-[150px]" />
      <Title label={tag(n, v.tag)} title={v.title} sub={v.sub} dark />
      <motion.blockquote initial={{ opacity: 0, y: 18 }} whileInView={{ opacity: 1, y: 0 }} viewport={{ once: true }} transition={{ type: "spring", stiffness: 80, damping: 16 }}
        className="mt-12 max-w-5xl font-display text-[clamp(1.6rem,3.4vw,2.9rem)] font-[300] italic leading-[1.12] tracking-[-0.01em]" style={{ fontStretch: "92%" }} lang="id">
        “{b.killer}”
      </motion.blockquote>
      {gloss && (
        <p className="mt-5 max-w-3xl border-l-2 border-violet-2/40 pl-4 text-white/60">
          <span className="tag mb-1 block text-white/35">{t.bot.gloss}</span>
          {gloss}
        </p>
      )}
      <div className="mt-12">
        <div className="tag text-white/45">{v.clauses}</div>
        {rules.length ? (
          <div className="mt-5 grid gap-4 lg:grid-cols-2">
            {rules.map((r) => (
              <div key={r.id} className="glass-dark min-w-0 rounded-[22px] p-5">
                <div className="flex items-center gap-3">
                  <span className="rounded-lg bg-violet/30 px-2 py-1 font-mono text-xs font-bold text-violet-2">{r.id}</span>
                  <Lock className="text-violet-2/70" />
                </div>
                <p className="mt-3 font-mono text-[0.78rem] leading-relaxed text-white/80" lang="id">{r.rule}</p>
                {lang === "en" && GLOSS.clauses[r.id] && <p className="mt-2 text-[0.85rem] text-white/50">{GLOSS.clauses[r.id]}</p>}
              </div>
            ))}
          </div>
        ) : (
          <p className="mt-4 max-w-2xl text-white/60">{v.textOnly}</p>
        )}
        {lock?.tx && (
          <a href={`${LINKS.tx}${lock.tx}`} target="_blank" rel="noreferrer" className="mt-6 inline-flex items-center gap-2 font-mono text-xs text-violet-2 underline-offset-4 hover:underline">
            <Lock /> {v.locked} · {utc(lock.at_utc)} · {short(lock.tx, 4)} ↗
          </a>
        )}
      </div>
    </section>
  );
}
