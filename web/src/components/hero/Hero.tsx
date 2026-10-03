"use client";

import dynamic from "next/dynamic";
import { AnimatePresence, motion } from "motion/react";
import { useEffect, useMemo, useRef, useState } from "react";
import { useLang } from "../lang";
import IsoCube from "../ui/IsoCube";
import { crystalCounts, short, type Snapshot } from "@/lib/snapshot";

const Crystal = dynamic(() => import("./Crystal"), { ssr: false, loading: () => <div className="absolute inset-0 bg-lav" /> });

const fmtUtc = (iso: string | null) => (iso ? `${iso.slice(8, 10)}.${iso.slice(5, 7)} ${iso.slice(11, 16)} UTC` : "—");

function RotatingBadge({ text, onClick, done }: { text: string; onClick: () => void; done: boolean }) {
  const ring = text.repeat(2);
  return (
    <button onClick={onClick} className="group relative grid h-[124px] w-[124px] place-items-center" aria-label="verify">
      <svg viewBox="0 0 124 124" className="absolute inset-0 animate-spin-slow">
        <defs>
          <path id="ring" d="M62 62 m-48 0 a48 48 0 1 1 96 0 a48 48 0 1 1 -96 0" />
        </defs>
        <text className="fill-ink/70 font-mono text-[8.6px] tracking-[0.2em]">
          <textPath href="#ring">{ring}</textPath>
        </text>
      </svg>
      <span className="grid h-14 w-14 place-items-center rounded-full bg-ink text-white transition group-hover:scale-110 group-hover:bg-violet">
        {done ? "✓" : "⌘"}
      </span>
    </button>
  );
}

export default function Hero({ s }: { s: Snapshot }) {
  const { t } = useLang();
  const counts = useMemo(() => crystalCounts(s, 27 - 1), [s]); // 26 blok luar; inti = agen
  const [beat, setBeat] = useState<number | null>(null);
  const [copied, setCopied] = useState(false);
  const sec = useRef<HTMLElement>(null);
  const [inView, setInView] = useState(true);
  useEffect(() => {
    const el = sec.current;
    if (!el) return;
    const io = new IntersectionObserver(([e]) => setInView(e.isIntersecting), { threshold: 0.02 });
    io.observe(el);
    return () => io.disconnect();
  }, []);
  const lock = beat !== null && beat >= 0 ? s.locks[beat] : null;
  const lockName = lock ? (t.book.lockNames[lock.label] ?? lock.label) : null;
  const verify = () => {
    navigator.clipboard?.writeText(t.journey.verify).catch(() => {});
    setCopied(true);
    window.setTimeout(() => setCopied(false), 2200);
  };
  const words = [t.hero.l1, t.hero.l2, t.hero.l3];

  return (
    <section ref={sec} id="top" className="relative h-[100svh] min-h-[720px] overflow-hidden rounded-[30px] bg-lav">
      <Crystal counts={counts} onBeat={setBeat} active={inView} />

      <div className="pointer-events-none relative z-10 flex h-full flex-col justify-end px-6 pb-10 sm:px-12 sm:pb-12 lg:px-16">
        <h1 className="font-display leading-[0.86] tracking-[-0.035em] text-ink">
          {words.map((w, i) => (
            <motion.span
              key={`${i}-${w}`}
              initial={{ y: "110%", opacity: 0 }}
              animate={{ y: 0, opacity: 1 }}
              transition={{ delay: 0.35 + i * 0.14, type: "spring", stiffness: 120, damping: 16 }}
              className={
                i === 0
                  ? "block text-[clamp(3.4rem,10vw,9.5rem)] font-[200]"
                  : i === 1
                    ? "flex items-center gap-4 text-[clamp(3.6rem,11vw,10.5rem)] font-[850] italic"
                    : "block text-[clamp(2.2rem,6.4vw,6.2rem)] font-[800]"
              }
              style={{ fontStretch: i === 0 ? "125%" : i === 1 ? "72%" : "88%" }}
            >
              {i === 1 && (
                <span className="pointer-events-auto grid h-[0.62em] w-[0.62em] shrink-0 place-items-center rounded-full bg-white text-[0.32em] not-italic shadow-[0_10px_30px_-10px_rgba(80,50,200,.5)]">
                  <a href="#journey" aria-label="scroll">↓</a>
                </span>
              )}
              {w}
              {i === 2 && <span className="ml-2 inline-block h-[0.8em] w-[0.09em] translate-y-[0.06em] animate-blink bg-ink align-baseline" />}
            </motion.span>
          ))}
        </h1>

        <div className="mt-8 flex flex-col gap-6 border-t border-ink/15 pt-6 lg:flex-row lg:items-end lg:justify-between">
          <motion.p initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ delay: 1.0 }} className="max-w-xl text-[1.02rem] leading-relaxed text-ink/70">
            {t.hero.sub}
          </motion.p>
          <motion.div initial={{ opacity: 0, y: 12 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 1.15 }} className="pointer-events-auto flex flex-wrap gap-3">
            <a href="#proof" className="rounded-full bg-violet px-6 py-3.5 text-sm font-semibold text-white shadow-[0_14px_40px_-12px_rgba(110,75,255,.8)] transition hover:-translate-y-0.5">
              {t.hero.primary} →
            </a>
            <a href="#access" className="glass rounded-full px-6 py-3.5 text-sm font-semibold text-ink transition hover:-translate-y-0.5">
              {t.hero.secondary}
            </a>
          </motion.div>
        </div>
      </div>

      {/* Legenda = data: jumlah blok per keadaan, dari snapshot */}
      <div className="absolute left-6 top-28 z-20 hidden flex-wrap items-center gap-2 sm:left-12 md:flex lg:left-16 lg:top-32">
        <span className="tag mr-2 w-full text-ink/45">{t.hero.live} · {s.chain ? `#${s.chain.block.toLocaleString("en-US")}` : "—"}</span>
        {(
          [
            ["sealed", counts.sealed, t.hero.legend.sealed],
            ["verified", counts.verified, t.hero.legend.verified],
            ["empty", counts.empty, t.hero.legend.empty],
          ] as const
        ).map(([k, n, label]) => (
          <div key={k} className="glass flex items-center gap-3 rounded-2xl py-2 pl-2.5 pr-4">
            <IsoCube kind={k} size={26} glow={k === "verified"} />
            <span className="font-mono text-lg font-semibold tabular-nums text-ink">{n}</span>
            <span className="text-[0.82rem] text-ink/65">{label}</span>
          </div>
        ))}
      </div>

      {/* Detak: blok aturan yang sedang keluar dari kristal = kunci on-chain itu */}
      <div className="pointer-events-none absolute left-1/2 top-[18%] z-20 hidden -translate-x-1/2 lg:block lg:left-[63%]">
        <AnimatePresence mode="wait">
          {lock && (
            <motion.div
              key={lock.label}
              initial={{ opacity: 0, y: 10, scale: 0.96 }}
              animate={{ opacity: 1, y: 0, scale: 1 }}
              exit={{ opacity: 0, y: -8 }}
              transition={{ type: "spring", stiffness: 260, damping: 22 }}
              className="glass flex items-center gap-3 rounded-full py-2 pl-2 pr-5"
            >
              <span className="grid h-8 w-8 place-items-center rounded-full bg-[#3a29b8] text-xs text-white">⛓</span>
              <span className="text-sm font-semibold text-ink">{lockName}</span>
              <span className="font-mono text-xs text-ink/55">{fmtUtc(lock.at_utc)}</span>
              <span className="font-mono text-xs text-violet">{short(lock.tx, 4)}</span>
            </motion.div>
          )}
        </AnimatePresence>
      </div>

      <div className="absolute right-10 top-[52%] z-20 hidden xl:block">
        <RotatingBadge text={copied ? "COPIED · PASTE IN A TERMINAL · " : t.hero.badge} onClick={verify} done={copied} />
      </div>
    </section>
  );
}
