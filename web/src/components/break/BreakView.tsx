"use client";

// /break (P178): empat cara curang terhadap SignalAnchor sungguhan, dijalankan sebagai simulasi (eth_call, `from` = committer resmi) lewat /api/break.
// Yang ditampilkan = nama + argumen revert kontrak apa adanya. Gagal baca chain = pesan galat (T8), bukan "lolos".

import Link from "next/link";
import { useState } from "react";
import { motion } from "motion/react";
import { LangProvider, useLang } from "../lang";
import Nav from "../Nav";
import IsoCube from "../ui/IsoCube";
import { Claims, Footer } from "../sections/Closing";
import { LINKS } from "@/lib/copy";
import type { Snapshot } from "@/lib/snapshot";
import type { Attack, BreakResult } from "@/lib/break";

type Res = { state: "idle" | "loading" } | { state: "done"; result: BreakResult } | { state: "error"; error: string };

const COPY = {
  en: {
    tag: "TRY TO CHEAT — NO KEY, NO GAS",
    t1: "Rewrite the record.",
    t2: "Watch it fail.",
    sub: "Four ways a signal seller fakes a track record. Each one runs here as a simulation against the real SignalAnchor contract on BNB Chain testnet, from our own official committer address. Nothing is sent: you see the contract's own rejection, word for word.",
    run: "Try it",
    runAll: "Try all four",
    running: "Asking the contract…",
    rejected: "Rejected by the contract",
    accepted: "Accepted — this would be a bug. Report it.",
    args: "What the contract said",
    repro: "Reproduce it yourself (Foundry)",
    sim: "Simulation (eth_call) at block",
    from: "from the official committer",
    verify: "See a day that passed instead →",
    attacks: {
      late: { title: "Write yesterday's call after the market moved", why: "A signal can only be sealed within 12 hours of the bar closing. Later = rejected." },
      prelock: { title: "Claim a call from before the strategy existed", why: "Each strategy is locked on-chain first. A day before that lock cannot carry a signal." },
      respec: { title: "Quietly tweak the strategy after seeing the data", why: "A different strategy has a different fingerprint, and that fingerprint was never locked." },
      extra: { title: "Add a winning signal to a day already sealed", why: "B2-RS sealed 4 signals on 2026-10-05 and opened all 4. A fifth cannot appear." },
    } as Record<Attack, { title: string; why: string }>,
  },
  id: {
    tag: "COBA CURANGI — TANPA KUNCI, TANPA GAS",
    t1: "Tulis ulang rekamnya.",
    t2: "Lihat ia gagal.",
    sub: "Empat cara penjual sinyal memalsukan track record. Masing-masing dijalankan di sini sebagai simulasi terhadap kontrak SignalAnchor sungguhan di BNB Chain testnet, dari alamat committer resmi kami sendiri. Tidak ada yang dikirim: yang tampil adalah penolakan kontrak itu sendiri, kata per kata.",
    run: "Coba",
    runAll: "Coba keempatnya",
    running: "Menanyai kontrak…",
    rejected: "Ditolak oleh kontrak",
    accepted: "Diterima — ini berarti bug. Laporkan.",
    args: "Kata kontrak",
    repro: "Ulangi sendiri (Foundry)",
    sim: "Simulasi (eth_call) di blok",
    from: "dari committer resmi",
    verify: "Lihat hari yang lolos →",
    attacks: {
      late: { title: "Tulis sinyal kemarin sesudah pasar bergerak", why: "Sinyal hanya bisa disegel paling lambat 12 jam sesudah bar tutup. Lewat dari itu = ditolak." },
      prelock: { title: "Klaim sinyal dari sebelum strateginya ada", why: "Tiap strategi dikunci on-chain lebih dulu. Hari sebelum kunci itu tidak boleh punya sinyal." },
      respec: { title: "Ubah strategi diam-diam sesudah melihat data", why: "Strategi yang berbeda punya sidik jari berbeda, dan sidik jari itu tidak pernah dikunci." },
      extra: { title: "Tambah sinyal pemenang ke hari yang sudah disegel", why: "B2-RS menyegel 4 sinyal pada 2026-10-05 dan membuka keempatnya. Sinyal kelima tidak bisa muncul." },
    } as Record<Attack, { title: string; why: string }>,
  },
};

const ORDER: Attack[] = ["late", "prelock", "respec", "extra"];

export default function BreakView({ s }: { s: Snapshot }) {
  return (
    <LangProvider>
      <div className="p-2 sm:p-3">
        <Nav />
        <Break />
        <Claims />
        <Footer s={s} />
      </div>
    </LangProvider>
  );
}

function Break() {
  const { lang } = useLang();
  const c = COPY[lang === "id" ? "id" : "en"];
  const [res, setRes] = useState<Record<Attack, Res>>({ late: { state: "idle" }, prelock: { state: "idle" }, respec: { state: "idle" }, extra: { state: "idle" } });

  async function attack(a: Attack) {
    setRes((r) => ({ ...r, [a]: { state: "loading" } }));
    try {
      const r = await fetch(`/api/break?attack=${a}`, { cache: "no-store" });
      const body = await r.json().catch(() => ({ error: `HTTP ${r.status}` }));
      setRes((x) => ({ ...x, [a]: body.result ? { state: "done", result: body.result as BreakResult } : { state: "error", error: String(body.error ?? `HTTP ${r.status}`) } }));
    } catch (e) {
      setRes((x) => ({ ...x, [a]: { state: "error", error: String(e) } }));
    }
  }

  return (
    <section id="top" className="relative overflow-hidden rounded-[30px] bg-gradient-to-b from-lav via-lav to-white px-6 pb-24 pt-32 sm:px-12 sm:pt-40 lg:px-16">
      <span className="tag text-violet">{c.tag}</span>
      <h1 className="mt-4 font-display leading-[0.9] tracking-[-0.035em] text-ink">
        <span className="block text-[clamp(3rem,9vw,8.5rem)] font-[300]" style={{ fontStretch: "112%" }}>{c.t1}</span>
        <span className="block text-[clamp(3rem,9vw,8.5rem)] font-[800] italic text-violet" style={{ fontStretch: "78%" }}>{c.t2}</span>
      </h1>
      <p className="mt-6 max-w-2xl text-lg text-ink/65">{c.sub}</p>
      <button type="button" onClick={() => ORDER.forEach((a) => attack(a))}
        className="mt-8 rounded-full bg-violet px-7 py-3 text-sm font-semibold text-white shadow-[0_14px_40px_-12px_rgba(110,75,255,.8)] transition hover:bg-ink">
        {c.runAll}
      </button>

      <div className="mt-10 grid gap-5 lg:grid-cols-2">
        {ORDER.map((a, i) => {
          const r = res[a];
          const done = r.state === "done" ? r.result : null;
          return (
            <motion.article key={a} initial={{ opacity: 0, y: 16 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: i * 0.06 }}
              className={`glass flex flex-col rounded-[26px] border p-6 ${done ? (done.rejected ? "border-violet/40" : "border-gap/60") : "border-white/60"}`}>
              <div className="flex items-start justify-between gap-4">
                <div>
                  <span className="tag text-ink/45">0{i + 1}</span>
                  <h2 className="mt-2 font-display text-2xl font-semibold leading-tight text-ink">{c.attacks[a].title}</h2>
                  <p className="mt-2 text-sm text-ink/60">{c.attacks[a].why}</p>
                </div>
                <IsoCube kind={done ? (done.rejected ? "sealed" : "missed") : "empty"} size={34} />
              </div>
              <button type="button" disabled={r.state === "loading"} onClick={() => attack(a)}
                className="mt-5 self-start rounded-full bg-ink px-5 py-2.5 text-sm font-semibold text-white transition hover:bg-violet disabled:opacity-60">
                {r.state === "loading" ? c.running : c.run}
              </button>
              {r.state === "error" && <p className="mt-4 rounded-2xl bg-white/70 p-3 font-mono text-xs text-gap">{r.error}</p>}
              {done && (
                <div className="mt-5 rounded-2xl bg-white/75 p-4">
                  <div className={`font-display text-lg font-semibold ${done.rejected ? "text-violet" : "text-gap"}`}>
                    {done.rejected ? c.rejected : c.accepted}
                    {done.error && <span className="ml-2 font-mono text-base text-ink">{done.error}</span>}
                  </div>
                  <p className="mt-1 font-mono text-[11px] text-ink/55 break-words">{done.call}</p>
                  {Object.keys(done.args).length > 0 && (
                    <dl className="mt-3 grid grid-cols-[auto_1fr] gap-x-3 gap-y-1 font-mono text-xs">
                      <dt className="col-span-2 tag text-ink/45">{c.args}</dt>
                      {Object.entries(done.args).map(([k, v]) => (
                        <div key={k} className="contents">
                          <dt className="text-ink/55">{k}</dt>
                          <dd className="break-all text-ink">{v}</dd>
                        </div>
                      ))}
                    </dl>
                  )}
                  <p className="mt-3 font-mono text-[11px] text-ink/55">
                    {c.sim} #{done.block.toLocaleString("en-US")} · {c.from}{" "}
                    <a className="underline-offset-4 hover:underline" href={`${LINKS.scan}${done.contract}`} target="_blank" rel="noreferrer">SignalAnchor ↗</a>
                  </p>
                  <details className="mt-2">
                    <summary className="cursor-pointer font-mono text-[11px] text-ink/55">{c.repro}</summary>
                    <pre className="mt-2 overflow-x-auto rounded-xl bg-ink p-3 font-mono text-[10.5px] leading-relaxed text-white/85">{done.cast}</pre>
                  </details>
                </div>
              )}
            </motion.article>
          );
        })}
      </div>

      <Link href="/verify?bot=B2-RS&bar=2026-10-05" className="mt-10 inline-block font-mono text-sm text-violet underline-offset-4 hover:underline">{c.verify}</Link>
    </section>
  );
}
