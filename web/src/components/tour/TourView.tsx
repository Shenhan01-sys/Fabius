"use client";

// /tour (P178): tur juri - satu (bot, bar) dari kunci strategi sampai vonis, lima langkah pada satu rel. Tiap langkah = waktu + tx on-chain (dibaca
// dari event-nya sendiri lewat /api/tour) + satu cek urutan. Gagal baca chain = pesan galat (T8), bukan langkah yang "lolos".

import Link from "next/link";
import { useEffect, useState, type ReactNode } from "react";
import { motion } from "motion/react";
import { LangProvider, useLang } from "../lang";
import Nav from "../Nav";
import IsoCube from "../ui/IsoCube";
import { Claims, Footer } from "../sections/Closing";
import { LINKS } from "@/lib/copy";
import { short, type Snapshot } from "@/lib/snapshot";
import type { TourResult } from "@/lib/tour";

type Res = { state: "loading" } | { state: "done"; result: TourResult } | { state: "error"; error: string };

const COPY = {
  en: {
    tag: "60-SECOND TOUR — NO LOGIN, NO KEY",
    t1: "One bot. One day.",
    t2: "Five on-chain steps.",
    sub: (bot: string, bar: string) => `Follow ${bot} through the trading day ${bar}, from the moment its rules were locked to the moment anyone can re-check its calls. Every step below is read live from BNB Chain testnet and links to its transaction.`,
    loading: "Reading BNB Chain…",
    retry: "Try again",
    ok: "holds",
    broken: "BROKEN",
    tx: "tx",
    block: "block",
    after: (h: string) => `${h} later`,
    before: (h: string) => `${h} before the day closed`,
    steps: {
      lock: { title: "The rules are locked first", body: "The strategy's fingerprint is written to LockRegistry. From here on, the bot can only publish calls under exactly these rules." },
      close: { title: "The trading day closes", body: "The market answers. A call sealed after this moment would be hindsight, so the contract only accepts the seal within a fixed window." },
      commit: { title: "Calls sealed, not shown", body: "One Merkle root of all the day's calls goes on-chain. Nobody can read the calls yet, and nobody can change them anymore." },
      reveal: { title: "Calls opened, one by one", body: "Each call is revealed with its salt. The contract checks it against the sealed root; a call that was not sealed cannot be opened." },
      verify: { title: "Anyone re-checks", body: "Each revealed call is hashed again and matched with the public ledger tick written before the seal. Same code as the MCP tool." },
    },
    checks: {
      lock_before_close: "locked before the day closed",
      commit_after_close: "sealed after the day closed",
      commit_within_lag: (h: number) => `sealed within ${h} h`,
      reveal_after_commit: "opened after the seal",
      leaves: "every call recomputes from its payload",
      tick: "every call is in the ledger tick",
    },
    noCommit: "No seal for this day.",
    calls: (n: number) => `${n} call${n === 1 ? "" : "s"} sealed`,
    root: "root",
    verdict: "Verdict",
    verdicts: { SAH: "VERIFIED" } as Record<string, string>,
    next: "Now try to break it →",
    deep: "Open the full check →",
  },
  id: {
    tag: "TUR 60 DETIK — TANPA LOGIN, TANPA KUNCI",
    t1: "Satu bot. Satu hari.",
    t2: "Lima langkah on-chain.",
    sub: (bot: string, bar: string) => `Ikuti ${bot} melewati hari dagang ${bar}, dari saat aturannya dikunci sampai saat siapa pun bisa memeriksa ulang sinyalnya. Setiap langkah di bawah dibaca langsung dari BNB Chain testnet dan menaut ke transaksinya.`,
    loading: "Membaca BNB Chain…",
    retry: "Coba lagi",
    ok: "terpenuhi",
    broken: "RUSAK",
    tx: "tx",
    block: "blok",
    after: (h: string) => `${h} kemudian`,
    before: (h: string) => `${h} sebelum hari tutup`,
    steps: {
      lock: { title: "Aturan dikunci lebih dulu", body: "Sidik jari strategi ditulis ke LockRegistry. Sejak itu bot hanya bisa menerbitkan sinyal di bawah aturan yang persis ini." },
      close: { title: "Hari dagang tutup", body: "Pasar menjawab. Sinyal yang disegel sesudah titik ini adalah hindsight, jadi kontrak hanya menerima segel dalam jendela waktu tetap." },
      commit: { title: "Sinyal disegel, belum ditampilkan", body: "Satu akar Merkle dari semua sinyal hari itu masuk on-chain. Belum ada yang bisa membaca sinyalnya, dan tidak ada yang bisa mengubahnya lagi." },
      reveal: { title: "Sinyal dibuka satu per satu", body: "Tiap sinyal dibuka beserta salt-nya. Kontrak mencocokkannya dengan akar yang disegel; sinyal yang tidak disegel tidak bisa dibuka." },
      verify: { title: "Siapa pun memeriksa ulang", body: "Tiap sinyal yang dibuka di-hash ulang dan dicocokkan dengan tick ledger publik yang ditulis sebelum segel. Kode sama dengan alat MCP." },
    },
    checks: {
      lock_before_close: "dikunci sebelum hari tutup",
      commit_after_close: "disegel sesudah hari tutup",
      commit_within_lag: (h: number) => `disegel dalam ${h} jam`,
      reveal_after_commit: "dibuka sesudah segel",
      leaves: "tiap sinyal terhitung ulang dari isinya",
      tick: "tiap sinyal ada di tick ledger",
    },
    noCommit: "Tidak ada segel untuk hari ini.",
    calls: (n: number) => `${n} sinyal disegel`,
    root: "akar",
    verdict: "Vonis",
    verdicts: { SAH: "SAH" } as Record<string, string>,
    next: "Sekarang coba curangi →",
    deep: "Buka pemeriksaan lengkap →",
  },
};

const hours = (a: string, b: string) => {
  const h = Math.abs(Date.parse(b) - Date.parse(a)) / 3_600_000;
  return h >= 48 ? `${(h / 24).toFixed(1)} d` : `${h.toFixed(1)} h`;
};
const utc = (s: string) => s.replace("T", " ").replace("Z", " UTC");

export default function TourView({ s }: { s: Snapshot }) {
  return (
    <LangProvider>
      <div className="p-2 sm:p-3">
        <Nav />
        <Tour />
        <Claims />
        <Footer s={s} />
      </div>
    </LangProvider>
  );
}

function Tour() {
  const { lang } = useLang();
  const c = COPY[lang === "id" ? "id" : "en"];
  const [res, setRes] = useState<Res>({ state: "loading" });
  const [nonce, setNonce] = useState(0);

  useEffect(() => {
    let alive = true;
    fetch("/api/tour", { cache: "no-store" })
      .then(async (r) => {
        const body = await r.json().catch(() => ({ error: `HTTP ${r.status}` }));
        if (alive) setRes(body.result ? { state: "done", result: body.result as TourResult } : { state: "error", error: String(body.error ?? `HTTP ${r.status}`) });
      })
      .catch((e) => alive && setRes({ state: "error", error: String(e) }));
    return () => {
      alive = false;
    };
  }, [nonce]);

  const r = res.state === "done" ? res.result : null;

  return (
    <section id="top" className="relative overflow-hidden rounded-[30px] bg-gradient-to-b from-lav via-lav to-white px-6 pb-24 pt-32 sm:px-12 sm:pt-40 lg:px-16">
      <span className="tag text-violet">{c.tag}</span>
      <h1 className="mt-4 font-display leading-[0.9] tracking-[-0.035em] text-ink">
        <span className="block text-[clamp(2.6rem,8vw,7.5rem)] font-[300]" style={{ fontStretch: "112%" }}>{c.t1}</span>
        <span className="block text-[clamp(2.6rem,8vw,7.5rem)] font-[800] italic text-violet" style={{ fontStretch: "78%" }}>{c.t2}</span>
      </h1>
      <p className="mt-6 max-w-2xl text-lg text-ink/65">{c.sub(r?.bot ?? "B2-RS", r?.bar ?? "2026-10-05")}</p>

      {res.state === "loading" && <p className="mt-10 font-mono text-sm text-ink/55">{c.loading}</p>}
      {res.state === "error" && (
        <div className="mt-10 max-w-2xl rounded-2xl bg-white/75 p-4">
          <p className="font-mono text-xs text-gap">{res.error}</p>
          <button type="button" onClick={() => { setRes({ state: "loading" }); setNonce((n) => n + 1); }}
            className="mt-3 rounded-full bg-ink px-5 py-2 text-sm font-semibold text-white transition hover:bg-violet">{c.retry}</button>
        </div>
      )}

      {r && (
        <ol className="relative mt-12 max-w-4xl space-y-5 border-l-2 border-violet/25 pl-6 sm:pl-10">
          <Step i={0} title={c.steps.lock.title} body={c.steps.lock.body} at={r.lock.at_utc} gap={c.before(hours(r.lock.at_utc, r.close.at_utc))}
            tx={r.lock.tx} block={r.lock.block} c={c} checks={[[c.checks.lock_before_close, r.order.lock_before_close]]}
            extra={<Mono label="spec" value={r.spec_sha} />} />
          <Step i={1} title={c.steps.close.title} body={c.steps.close.body} at={r.close.at_utc} c={c} checks={[]} />
          {r.commit ? (
            <Step i={2} title={c.steps.commit.title} body={c.steps.commit.body} at={r.commit.at_utc} gap={c.after(hours(r.close.at_utc, r.commit.at_utc))}
              tx={r.commit.tx} block={r.commit.block} c={c}
              checks={[[c.checks.commit_after_close, r.order.commit_after_close], [c.checks.commit_within_lag(r.commit.max_lag_hours), r.order.commit_within_lag]]}
              extra={<><p className="font-display text-base font-semibold text-ink">{c.calls(r.commit.n)}</p><Mono label={c.root} value={r.commit.root} /></>} />
          ) : (
            <Step i={2} title={c.steps.commit.title} body={c.noCommit} c={c} checks={[]} />
          )}
          <Step i={3} title={c.steps.reveal.title} body={c.steps.reveal.body} c={c} checks={[[c.checks.reveal_after_commit, r.order.reveal_after_commit]]}
            extra={
              <ul className="grid gap-2 sm:grid-cols-2">
                {r.reveals.map((x, k) => (
                  <li key={k} className="flex items-center justify-between gap-3 rounded-xl bg-lav/60 px-3 py-2 font-mono text-xs">
                    <span className="text-ink"><b>{x.asset}</b> {x.action}</span>
                    {x.tx && <a className="text-violet underline-offset-4 hover:underline" href={`${LINKS.tx}${x.tx}`} target="_blank" rel="noreferrer">{c.tx} {short(x.tx)} ↗</a>}
                  </li>
                ))}
              </ul>
            } />
          <Step i={4} title={c.steps.verify.title} body={c.steps.verify.body} c={c}
            checks={[[c.checks.leaves, r.reveals.every((x) => x.leaf_recomputes)], [c.checks.tick, r.reveals.every((x) => x.in_ledger_tick)]]}
            extra={
              <div className="flex items-center gap-4">
                <IsoCube kind={r.verify.verdict === "SAH" ? "verified" : r.verify.verdict === "ALARM" ? "missed" : "sealed"} size={48} glow />
                <div>
                  <span className="tag text-ink/45">{c.verdict}</span>
                  <p className={`font-display text-3xl font-[800] italic ${r.verify.verdict === "SAH" ? "text-violet" : "text-gap"}`}>{c.verdicts[r.verify.verdict] ?? r.verify.verdict}</p>
                  {r.verify.problems.map((p) => <p key={p} className="font-mono text-xs text-gap">{p}</p>)}
                </div>
              </div>
            } />
        </ol>
      )}

      <div className="mt-12 flex flex-wrap gap-3">
        <Link href="/break" className="rounded-full bg-violet px-7 py-3 text-sm font-semibold text-white shadow-[0_14px_40px_-12px_rgba(110,75,255,.8)] transition hover:bg-ink">{c.next}</Link>
        <Link href={`/verify?bot=${r?.bot ?? "B2-RS"}&bar=${r?.bar ?? "2026-10-05"}`} className="glass rounded-full px-7 py-3 text-sm font-semibold text-ink transition hover:-translate-y-0.5">{c.deep}</Link>
      </div>
      {r && <p className="mt-6 font-mono text-[11px] text-ink/45">chain 97 · SignalAnchor {short(r.contracts.signal_anchor)} · LockRegistry {short(r.contracts.lock_registry)} · {r.checked_utc}</p>}
    </section>
  );
}

type C = (typeof COPY)["en"] | (typeof COPY)["id"];

function Step({ i, title, body, at, gap, tx, block, checks, extra, c }: {
  i: number; title: string; body: string; at?: string; gap?: string; tx?: string; block?: number; checks: [string, boolean][]; extra?: ReactNode; c: C;
}) {
  const bad = checks.some(([, ok]) => !ok);
  return (
    <motion.li initial={{ opacity: 0, x: -14 }} animate={{ opacity: 1, x: 0 }} transition={{ delay: 0.15 + i * 0.35, duration: 0.45 }}
      className={`glass relative rounded-[26px] border p-5 sm:p-6 ${bad ? "border-gap/60" : "border-white/60"}`}>
      <span className={`absolute -left-[37px] top-6 grid h-6 w-6 place-items-center rounded-full font-mono text-[11px] font-semibold text-white sm:-left-[53px] ${bad ? "bg-gap" : "bg-violet"}`}>{i + 1}</span>
      <div className="flex flex-wrap items-baseline justify-between gap-x-4 gap-y-1">
        <h2 className="font-display text-2xl font-semibold leading-tight text-ink">{title}</h2>
        {at && <span className="font-mono text-xs text-ink/55">{utc(at)}{gap && <span className="text-violet"> · {gap}</span>}</span>}
      </div>
      <p className="mt-2 max-w-2xl text-sm text-ink/60">{body}</p>
      {extra && <div className="mt-4 space-y-2">{extra}</div>}
      {(tx || checks.length > 0) && (
        <div className="mt-4 flex flex-wrap items-center gap-2 font-mono text-[11px]">
          {tx && (
            <a className="rounded-full bg-ink px-3 py-1 text-white transition hover:bg-violet" href={`${LINKS.tx}${tx}`} target="_blank" rel="noreferrer">
              {c.tx} {short(tx)} · {c.block} #{block?.toLocaleString("en-US")} ↗
            </a>
          )}
          {checks.map(([label, ok]) => (
            <span key={label} className={`rounded-full px-3 py-1 ${ok ? "bg-violet/10 text-violet" : "bg-gap/15 text-gap"}`}>{ok ? "✓" : "✗"} {label} {ok ? "" : `· ${c.broken}`}</span>
          ))}
        </div>
      )}
    </motion.li>
  );
}

function Mono({ label, value }: { label: string; value: string }) {
  return <p className="break-all font-mono text-[11px] text-ink/55"><span className="text-ink/40">{label}</span> {value}</p>;
}
