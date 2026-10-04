"use client";

// 02 — Umpan bukti (docs/design/landing.md §3): kalender hari x bot. Sel = keping kaca dengan keadaan bukti dari ledger + vonis chain.
// Hari bolong tetap bolong (retak merah). Tiga tabung F-D16 per bot terisi sesuai angka snapshot, bukan hiasan.

import Link from "next/link";
import { motion } from "motion/react";
import { useLang } from "../lang";
import IsoCube from "../ui/IsoCube";
import { addDays, cellState, type CellState, type Snapshot } from "@/lib/snapshot";

const DAYS = 28;

export function Tank({ value, need, label }: { value: number; need: number; label: string }) {
  const f = Math.min(value / need, 1);
  return (
    <div className="flex flex-col items-center gap-2">
      <div className="relative h-36 w-14 overflow-hidden rounded-full border border-violet/25 bg-lav-2/70 shadow-[inset_0_2px_10px_rgba(60,40,160,.15)]">
        <motion.div
          className="absolute inset-x-0 bottom-0 bg-gradient-to-t from-violet to-violet-2"
          initial={{ height: "0%" }}
          whileInView={{ height: `${Math.max(f * 100, value > 0 ? 6 : 0)}%` }}
          viewport={{ once: true }}
          transition={{ type: "spring", stiffness: 60, damping: 12, delay: 0.2 }}
        />
        <div className="absolute inset-x-2 top-[0%] border-t border-dashed border-ink/25" />
      </div>
      <div className="text-center">
        <div className="font-mono text-lg font-semibold tabular-nums text-ink">
          {value}
          <span className="text-ink/35">/{need}</span>
        </div>
        <div className="text-[0.72rem] text-ink/55">{label}</div>
      </div>
    </div>
  );
}

export default function ProofFeed({ s }: { s: Snapshot }) {
  const { t } = useLang();
  const bots = Object.keys(s.ledger);
  const start = bots.map((b) => s.ledger[b].genesis).sort()[0] ?? s.generated_utc.slice(0, 10);
  const lastClosed = bots.map((b) => s.ledger[b].last_closed).sort().slice(-1)[0];
  const days = Array.from({ length: DAYS }, (_, i) => addDays(start, i));
  const order: CellState[] = ["verified", "sealed", "pending", "prelock", "gap", "missed", "future"];
  const req = s.fd16.required;

  return (
    <section id="proof" className="relative mt-3 overflow-hidden rounded-[30px] bg-gradient-to-b from-lav to-white px-6 py-24 sm:px-12 lg:px-16">
      <span className="tag text-violet">{t.proof.tag}</span>
      <div className="mt-3 flex flex-col gap-4 lg:flex-row lg:items-end lg:justify-between">
        <h2 className="max-w-3xl font-display text-[clamp(2.4rem,5.6vw,5rem)] font-[300] leading-[0.95] tracking-[-0.03em] text-ink" style={{ fontStretch: "112%" }}>
          {t.proof.title}
        </h2>
        <p className="max-w-sm text-ink/60">{t.proof.sub}</p>
      </div>

      {/* kalender */}
      <div className="glass mt-12 overflow-x-auto rounded-[26px] p-5 sm:p-7">
        <div className="min-w-[980px]">
          <div className="grid items-end gap-1.5" style={{ gridTemplateColumns: `150px repeat(${DAYS}, minmax(0,1fr))` }}>
            <div className="tag text-ink/40">
              {t.proof.started} {start}
            </div>
            {days.map((d) => (
              <div key={d} className={`text-center font-mono text-[0.68rem] ${d === lastClosed ? "font-bold text-violet" : "text-ink/40"}`}>
                {d.slice(8)}
                {d.slice(8) === "01" || d === start ? <div className="text-[0.58rem] text-ink/35">{d.slice(5, 7)}</div> : null}
              </div>
            ))}
            {bots.map((b) => (
              <Row key={b} b={b} s={s} days={days} lastClosed={lastClosed} />
            ))}
          </div>
        </div>
      </div>

      {/* legenda keadaan */}
      <div className="mt-5 flex flex-wrap gap-x-6 gap-y-2">
        {order.map((k) => (
          <div key={k} className="flex items-center gap-2 text-[0.8rem] text-ink/65">
            <IsoCube kind={k} size={20} glow={k === "verified"} />
            {t.proof.states[k]}
          </div>
        ))}
      </div>

      {/* F-D16 */}
      <div className="mt-16 grid gap-10 lg:grid-cols-[1fr_auto] lg:items-end">
        <div>
          <h3 className="font-display text-2xl font-[650] tracking-tight text-ink">{t.proof.fd16}</h3>
          <p className="mt-2 max-w-md text-sm text-ink/55">{t.proof.settleNote}</p>
        </div>
        <div className="flex flex-wrap gap-10">
          {bots.map((b) => {
            const v = s.fd16.bots[b];
            return (
              <div key={b}>
                <div className="tag mb-3 text-ink/50">{b}</div>
                <div className="flex gap-4">
                  <Tank value={v.signals} need={req.signals} label={t.proof.signals} />
                  <Tank value={v.days} need={req.days} label={t.proof.days} />
                  <Tank value={v.months} need={req.months} label={t.proof.months} />
                </div>
              </div>
            );
          })}
        </div>
      </div>
    </section>
  );
}

function Row({ b, s, days, lastClosed }: { b: string; s: Snapshot; days: string[]; lastClosed: string }) {
  const { t } = useLang();
  const bot = s.bots.find((x) => x.id === b);
  const ticks = new Map(s.ledger[b].ticks.map((x) => [x.date, x]));
  return (
    <>
      <div className="py-3 pr-3">
        <Link href={`/bot/${b}`} className="font-display text-[0.98rem] font-[700] text-ink underline-offset-4 hover:text-violet hover:underline">{b}</Link>
        <div className="font-mono text-[0.66rem] text-ink/45">{bot?.param}</div>
      </div>
      {days.map((d, i) => {
        const raw = d > lastClosed ? "future" : cellState(s, b, d);
        const st: CellState = raw === "future" && d <= lastClosed ? "pending" : raw; // bar sudah tutup, tick belum masuk: menunggu, bukan masa depan
        const tk = ticks.get(d);
        return (
          <motion.div
            key={d}
            title={`${b} · ${d} · ${t.proof.states[st]}${tk ? ` · ${tk.signals} ${t.proof.signals}` : ""}`}
            initial={{ opacity: 0, y: 10 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            transition={{ delay: i * 0.018, type: "spring", stiffness: 200, damping: 18 }}
            className="group relative flex flex-col items-center"
          >
            {st === "verified" || st === "sealed" ? (
              // sel yang sudah dikomit = pintu ke pemeriksaan publiknya (/verify)
              <Link href={`/verify?bot=${b}&bar=${d}`} aria-label={`${t.verify.fromCalendar}: ${b} ${d}`} className="transition hover:-translate-y-0.5">
                <IsoCube kind={st} size={30} glow={st === "verified"} />
              </Link>
            ) : (
              <div className={st === "pending" ? "animate-breathe" : ""}>
                <IsoCube kind={st} size={30} />
              </div>
            )}
            {tk && tk.signals > 0 && <span className="absolute -top-1 right-0 grid h-4 min-w-4 place-items-center rounded-full bg-violet px-1 font-mono text-[0.56rem] font-bold text-white">{tk.signals}</span>}
          </motion.div>
        );
      })}
    </>
  );
}
