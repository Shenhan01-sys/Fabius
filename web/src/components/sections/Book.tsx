"use client";

// 03 — Buku slot (docs/design/landing.md §4): rak 10 slot = kapasitas nyata. B1 menghuni (identitas), B3 mengorbit dengan cincin bayangan
// hari-hidup/60, spesifikasi lain redup di luar. Di bawahnya rantai kunci on-chain menyala berurutan sesuai waktu kuncinya.

import Link from "next/link";
import { motion } from "motion/react";
import { useLang } from "../lang";
import IsoCube from "../ui/IsoCube";
import { LINKS } from "@/lib/copy";
import { short, type Snapshot } from "@/lib/snapshot";

const SHADOW_NEED = 60;

function Ring({ value, need, size = 132 }: { value: number; need: number; size?: number }) {
  const r = size / 2 - 7;
  const c = 2 * Math.PI * r;
  const f = Math.min(value / need, 1);
  return (
    <svg width={size} height={size} viewBox={`0 0 ${size} ${size}`} className="-rotate-90" aria-hidden>
      <circle cx={size / 2} cy={size / 2} r={r} fill="none" stroke="rgba(255,255,255,.1)" strokeWidth="5" />
      <motion.circle
        cx={size / 2}
        cy={size / 2}
        r={r}
        fill="none"
        stroke="url(#rg)"
        strokeWidth="5"
        strokeLinecap="round"
        strokeDasharray={c}
        initial={{ strokeDashoffset: c }}
        whileInView={{ strokeDashoffset: c * (1 - Math.max(f, 0.012)) }}
        viewport={{ once: true }}
        transition={{ duration: 1.6, ease: [0.22, 1, 0.36, 1] }}
      />
      <defs>
        <linearGradient id="rg" x1="0" x2="1">
          <stop offset="0%" stopColor="#6e4bff" />
          <stop offset="100%" stopColor="#c8b8ff" />
        </linearGradient>
      </defs>
    </svg>
  );
}

export default function Book({ s }: { s: Snapshot }) {
  const { t } = useLang();
  const occ = new Map(s.book.occupants.map((o) => [o.id, o]));
  const slots = Array.from({ length: s.book.capacity }, (_, i) => s.book.occupants[i] ?? null);
  const challengers = s.book.challengers.map((c) => ({ ...c, live: s.ledger[c.id]?.days_live ?? c.shadow_days }));
  const others = s.bots.filter((b) => !occ.has(b.id) && !challengers.some((c) => c.id === b.id));

  return (
    <section id="book" className="relative mt-3 overflow-hidden rounded-[30px] bg-night px-6 py-24 text-white sm:px-12 lg:px-16">
      <div className="pointer-events-none absolute -right-40 top-10 h-[480px] w-[480px] rounded-full bg-violet/20 blur-[150px]" />
      <span className="tag text-violet-2">{t.book.tag}</span>
      <h2 className="mt-3 max-w-4xl font-display text-[clamp(2.2rem,5vw,4.6rem)] font-[300] leading-[0.98] tracking-[-0.03em]" style={{ fontStretch: "112%" }}>
        {t.book.title}
      </h2>
      <p className="mt-4 max-w-xl text-white/60">{t.book.sub}</p>

      <div className="mt-14 grid gap-10 xl:grid-cols-[1fr_auto] xl:items-center">
        {/* rak */}
        <div className="grid grid-cols-5 gap-3 sm:gap-4 lg:grid-cols-10">
          {slots.map((o, i) => (
            <motion.div
              key={i}
              initial={{ opacity: 0, y: 24 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true }}
              transition={{ delay: i * 0.05, type: "spring", stiffness: 160, damping: 16 }}
              className={`glass-dark relative flex aspect-[3/4] flex-col items-center justify-center rounded-2xl ${o ? "ring-1 ring-violet-2/60" : ""}`}
            >
              <span className="absolute left-2.5 top-2 font-mono text-[0.6rem] text-white/35">{String(i + 1).padStart(2, "0")}</span>
              {o ? (
                <>
                  <IsoCube kind="core" size={56} glow />
                  <Link href={`/bot/${o.id}`} className="mt-2 text-center font-display text-[0.78rem] font-[700] leading-tight underline-offset-4 hover:text-violet-2 hover:underline">{o.id}</Link>
                  {o.identity && <div className="mt-1 rounded-full bg-violet/30 px-2 py-0.5 text-[0.6rem] text-violet-2">{t.book.identity}</div>}
                </>
              ) : (
                <div className="h-8 w-8 rounded-lg border border-dashed border-white/15" />
              )}
            </motion.div>
          ))}
        </div>

        {/* penantang mengorbit */}
        <div className="flex flex-wrap gap-8">
          {challengers.map((c) => (
            <div key={c.id} className="flex items-center gap-4">
              <div className="relative grid place-items-center">
                <Ring value={c.live} need={SHADOW_NEED} />
                <div className="absolute">
                  <IsoCube kind="sealed" size={46} />
                </div>
              </div>
              <div>
                <Link href={`/bot/${c.id}`} className="font-display text-lg font-[700] underline-offset-4 hover:text-violet-2 hover:underline">{c.id}</Link>
                <div className="font-mono text-sm text-violet-2">
                  {t.book.shadow} {c.live}/{SHADOW_NEED} d
                </div>
                <div className="mt-1 font-mono text-[0.66rem] text-white/40">gate {c.gate}</div>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* spesifikasi lain: redup */}
      <div className="mt-12 flex flex-wrap gap-3">
        {others.map((b) => (
          <Link key={b.id} href={`/bot/${b.id}`} className="glass-dark flex items-center gap-3 rounded-2xl py-2 pl-2 pr-4 opacity-60 transition hover:opacity-100">
            <IsoCube kind="empty" size={26} />
            <div>
              <div className="font-display text-sm font-[700]">{b.id}</div>
              <div className="font-mono text-[0.62rem] text-white/45">
                {short(b.spec_sha, 6)} · {t.book.locked}
              </div>
            </div>
          </Link>
        ))}
      </div>

      {/* rantai kunci */}
      <div className="mt-20">
        <div className="tag text-white/45">{t.book.locks}</div>
        <div className="relative mt-8">
          <div className="absolute left-0 right-0 top-[19px] h-px bg-white/15" />
          <div className="grid grid-cols-2 gap-y-8 sm:grid-cols-4 lg:grid-cols-7">
            {s.locks.map((l, i) => (
              <motion.a
                key={l.label}
                href={l.tx ? `${LINKS.tx}${l.tx}` : undefined}
                target="_blank"
                rel="noreferrer"
                initial={{ opacity: 0.25 }}
                whileInView={{ opacity: 1 }}
                viewport={{ once: true, margin: "-60px" }}
                transition={{ delay: 0.25 + i * 0.22 }}
                className="group relative pr-3"
              >
                <motion.span
                  initial={{ scale: 0.6, backgroundColor: "#1a1442" }}
                  whileInView={{ scale: 1, backgroundColor: "#3a29b8" }}
                  viewport={{ once: true, margin: "-60px" }}
                  transition={{ delay: 0.25 + i * 0.22, type: "spring", stiffness: 300, damping: 14 }}
                  className="relative z-10 grid h-10 w-10 place-items-center rounded-xl border border-violet-2/50 text-sm"
                >
                  ⛓
                </motion.span>
                <div className="mt-3 font-display text-[0.92rem] font-[650] leading-tight group-hover:text-violet-2">{t.book.lockNames[l.label] ?? l.label}</div>
                <div className="mt-1 font-mono text-[0.66rem] text-white/45">{l.at_utc ? `${l.at_utc.slice(5, 10)} ${l.at_utc.slice(11, 16)} UTC` : "—"}</div>
                <div className="font-mono text-[0.62rem] text-violet-2/70">{l.where}</div>
              </motion.a>
            ))}
          </div>
        </div>
      </div>
    </section>
  );
}
