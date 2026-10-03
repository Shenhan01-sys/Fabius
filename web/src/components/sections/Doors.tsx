"use client";

// 04 — Dua pintu (docs/design/landing.md §5). Manusia dan agen masuk ke bukti yang SAMA. Tingkat 0 (umpan bukti) terbuka; tingkat 1
// (sinyal waktu-nyata berbayar) terkunci dengan cincin syarat yang terisi sesuai data (F-D72, F-D16, P80) - bukan produk yang bisa dibeli hari ini.

import { useSyncExternalStore } from "react";
import { motion } from "motion/react";
import { useLang } from "../lang";
import IsoCube from "../ui/IsoCube";
import { LINKS } from "@/lib/copy";
import type { Snapshot } from "@/lib/snapshot";

function Stream({ dark = false }: { dark?: boolean }) {
  // blok kecil yang terus mengalir masuk ke pintu: umpan yang hidup
  return (
    <div className="pointer-events-none absolute inset-y-0 right-6 w-10 overflow-hidden opacity-70">
      {Array.from({ length: 6 }).map((_, i) => (
        <motion.div
          key={i}
          className="absolute left-1"
          initial={{ y: -60 }}
          animate={{ y: 520 }}
          transition={{ duration: 6, repeat: Infinity, delay: i, ease: "linear" }}
        >
          <IsoCube kind={i % 3 === 0 ? "verified" : dark ? "sealed" : "empty"} size={28} glow={i % 3 === 0} />
        </motion.div>
      ))}
    </div>
  );
}

function KeyRings({ values, labels }: { values: number[]; labels: readonly string[] }) {
  const sizes = [190, 146, 102];
  return (
    <div className="relative grid h-[200px] w-[200px] place-items-center">
      {values.map((v, i) => {
        const s = sizes[i];
        const r = s / 2 - 5;
        const c = 2 * Math.PI * r;
        return (
          <svg key={i} width={s} height={s} className="absolute -rotate-90" aria-hidden>
            <circle cx={s / 2} cy={s / 2} r={r} fill="none" stroke="rgba(255,255,255,.08)" strokeWidth="6" />
            <motion.circle
              cx={s / 2}
              cy={s / 2}
              r={r}
              fill="none"
              stroke={i === 0 ? "#9d86ff" : "#6e4bff"}
              strokeWidth="6"
              strokeLinecap="round"
              strokeDasharray={c}
              initial={{ strokeDashoffset: c }}
              whileInView={{ strokeDashoffset: c * (1 - Math.max(v, 0.008)) }}
              viewport={{ once: true }}
              transition={{ duration: 1.4, delay: 0.2 + i * 0.2 }}
            />
          </svg>
        );
      })}
      <svg width="34" height="40" viewBox="0 0 34 40" className="relative" aria-hidden>
        <path d="M9 17 V11 a8 8 0 0 1 16 0 V17" fill="none" stroke="#c8b8ff" strokeWidth="3.2" strokeLinecap="round" />
        <rect x="3" y="17" width="28" height="21" rx="5" fill="#6e4bff" stroke="#c8b8ff" strokeWidth="1.5" />
        <circle cx="17" cy="26" r="3" fill="#0f0b26" />
        <path d="M17 28 V32" stroke="#0f0b26" strokeWidth="2.6" strokeLinecap="round" />
      </svg>
      <div className="absolute -right-2 top-1/2 translate-x-full -translate-y-1/2 space-y-2 max-lg:hidden">
        {labels.map((l, i) => (
          <div key={l} className="flex items-center gap-2 font-mono text-[0.72rem] text-white/60">
            <span className="h-1.5 w-1.5 rounded-full" style={{ background: i === 0 ? "#9d86ff" : "#6e4bff" }} />
            {l} · {Math.round(values[i] * 100)}%
          </div>
        ))}
      </div>
    </div>
  );
}

// Alamat server MCP (P114) = asal halaman ini + /mcp. Server merender penampung; klien menggantinya sesudah hidrasi.
const noop = () => () => {};
const originOf = () => window.location.origin;

export default function Doors({ s }: { s: Snapshot }) {
  const { t } = useLang();
  const origin = useSyncExternalStore(noop, originOf, () => "https://<fabius-host>");
  const req = s.fd16.required.signals;
  const best = Math.max(0, ...Object.values(s.fd16.bots).map((b) => b.signals / req));
  const mcp = `{
  "mcpServers": {
    "fabius": { "type": "http", "url": "${origin}/mcp" }
  }
}`;

  return (
    <section id="access" className="relative mt-3 overflow-hidden rounded-[30px] bg-gradient-to-b from-white to-lav px-6 py-24 sm:px-12 lg:px-16">
      <span className="tag text-violet">{t.doors.tag}</span>
      <h2 className="mt-3 max-w-3xl font-display text-[clamp(2.4rem,5.6vw,5rem)] font-[300] leading-[0.95] tracking-[-0.03em] text-ink" style={{ fontStretch: "112%" }}>
        {t.doors.title}
      </h2>

      <div className="mt-14 grid gap-5 lg:grid-cols-2">
        {/* pintu manusia */}
        <motion.div initial={{ opacity: 0, y: 30 }} whileInView={{ opacity: 1, y: 0 }} viewport={{ once: true }} transition={{ type: "spring", stiffness: 90, damping: 16 }}
          className="glass relative min-h-[460px] overflow-hidden rounded-[28px] p-8 sm:p-10">
          <Stream />
          <div className="tag text-ink/45">{t.doors.human.k}</div>
          <div className="mt-2 font-display text-[clamp(2rem,3.4vw,3rem)] font-[750] italic tracking-tight text-ink" style={{ fontStretch: "80%" }}>
            {t.doors.human.h}
          </div>
          <span className="mt-3 inline-flex items-center gap-2 rounded-full bg-violet/10 px-3 py-1 text-xs font-semibold text-violet">
            <span className="h-1.5 w-1.5 animate-pulse rounded-full bg-violet" />
            {t.doors.human.open}
          </span>
          <ul className="mt-8 space-y-3 pr-14">
            {t.doors.human.pts.map((p) => (
              <li key={p} className="flex items-start gap-3 text-ink/75">
                <IsoCube kind="verified" size={18} className="mt-1 shrink-0" />
                {p}
              </li>
            ))}
          </ul>
          <div className="mt-10 flex flex-wrap gap-3">
            <a href="#proof" className="rounded-full bg-ink px-5 py-3 text-sm font-semibold text-white transition hover:bg-violet">{t.doors.human.cta} →</a>
            <a href={LINKS.telegram} target="_blank" rel="noreferrer" className="glass rounded-full px-5 py-3 text-sm font-semibold text-ink">{t.doors.human.cta2}</a>
          </div>
        </motion.div>

        {/* pintu agen */}
        <motion.div initial={{ opacity: 0, y: 30 }} whileInView={{ opacity: 1, y: 0 }} viewport={{ once: true }} transition={{ delay: 0.1, type: "spring", stiffness: 90, damping: 16 }}
          className="relative min-h-[460px] overflow-hidden rounded-[28px] bg-night p-8 text-white sm:p-10">
          <Stream dark />
          <div className="tag text-white/45">{t.doors.agent.k}</div>
          <div className="mt-2 font-display text-[clamp(2rem,3.4vw,3rem)] font-[750] italic tracking-tight" style={{ fontStretch: "80%" }}>
            {t.doors.agent.h}
          </div>
          <span className="mt-3 inline-flex items-center gap-2 rounded-full bg-violet/25 px-3 py-1 text-xs font-semibold text-violet-2">
            <span className="h-1.5 w-1.5 animate-pulse rounded-full bg-violet-2" />
            {t.doors.agent.open}
          </span>
          <ul className="mt-6 space-y-2.5 pr-14">
            {t.doors.agent.pts.map((p) => (
              <li key={p} className="flex items-start gap-3 text-white/75">
                <IsoCube kind="sealed" size={18} className="mt-1 shrink-0" />
                {p}
              </li>
            ))}
          </ul>
          <pre className="glass-dark mt-6 overflow-x-auto rounded-2xl p-4 pr-14 font-mono text-[0.76rem] leading-relaxed text-violet-2">{mcp}</pre>
          <a href={LINKS.agentCard} target="_blank" rel="noreferrer" className="mt-6 inline-block rounded-full border border-white/25 px-5 py-3 font-mono text-sm text-white transition hover:border-violet-2">
            {t.doors.agent.cta} ↗
          </a>
        </motion.div>
      </div>

      {/* tingkat 1: terkunci */}
      <motion.div initial={{ opacity: 0, y: 30 }} whileInView={{ opacity: 1, y: 0 }} viewport={{ once: true }} transition={{ type: "spring", stiffness: 90, damping: 16 }}
        className="relative mt-5 grid items-center gap-10 overflow-hidden rounded-[28px] bg-night-2 p-8 text-white sm:p-12 lg:grid-cols-[auto_1fr_auto]">
        <KeyRings values={[best, 0, 0]} labels={t.doors.tier1.rings} />
        <div className="lg:pl-36">
          <div className="tag text-white/45">{t.doors.tier1.k}</div>
          <div className="mt-2 font-display text-[clamp(1.8rem,3vw,2.6rem)] font-[750] tracking-tight">{t.doors.tier1.h}</div>
          <p className="mt-3 max-w-lg text-white/60">{t.doors.tier1.why}</p>
        </div>
        <div className="flex flex-col items-start gap-3 lg:items-end">
          <span className="rounded-full border border-white/20 px-3 py-1 font-mono text-xs text-white/70">{t.doors.tier1.status}</span>
          <a href={LINKS.telegram} target="_blank" rel="noreferrer" className="rounded-full bg-violet px-6 py-3 text-sm font-semibold text-white shadow-[0_14px_40px_-12px_rgba(110,75,255,.8)]">
            {t.doors.tier1.waitlist}
          </a>
        </div>
      </motion.div>
    </section>
  );
}
