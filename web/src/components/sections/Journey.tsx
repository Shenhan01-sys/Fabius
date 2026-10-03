"use client";

// 01 — Satu sinyal (docs/design/landing.md §2): sumbu waktu horizontal, satu blok berjalan mengikuti scroll dan berubah keadaan per stasiun.
// Bukan grid kartu: posisi blok = waktu, wujud blok = keadaan buktinya.

import { AnimatePresence, motion, useMotionValueEvent, useScroll, useSpring, useTransform } from "motion/react";
import { useRef, useState } from "react";
import { useLang } from "../lang";
import IsoCube from "../ui/IsoCube";

const STOPS = [0.06, 0.27, 0.5, 0.73, 0.94];

function Candle({ closed }: { closed: boolean }) {
  return (
    <svg viewBox="0 0 40 90" width="34" height="78" aria-hidden>
      <line x1="20" y1="4" x2="20" y2="86" stroke="#9d86ff" strokeWidth="2" />
      <motion.rect x="8" width="24" rx="3" fill={closed ? "#9d86ff" : "transparent"} stroke="#9d86ff" strokeWidth="2"
        initial={false} animate={{ y: closed ? 22 : 40, height: closed ? 44 : 10 }} transition={{ type: "spring", stiffness: 120, damping: 14 }} />
    </svg>
  );
}

function Fold({ on }: { on: boolean }) {
  // daun-daun Merkle melipat ke satu akar
  const leaves = [-54, -18, 18, 54];
  return (
    <svg viewBox="-80 -70 160 90" width="150" height="86" aria-hidden className="overflow-visible">
      {leaves.map((x, i) => (
        <motion.g key={i} initial={false} animate={{ x: on ? 0 : x, y: on ? 0 : -48, opacity: on ? 0 : 1 }} transition={{ delay: i * 0.05, type: "spring", stiffness: 140, damping: 15 }}>
          <rect x="-7" y="-7" width="14" height="14" rx="3" fill="#3a29b8" stroke="#9d86ff" />
        </motion.g>
      ))}
      {leaves.map((x, i) => (
        <motion.line key={`l${i}`} x1={x} y1={-40} x2={0} y2={0} stroke="#9d86ff" strokeOpacity={0.5} initial={false} animate={{ pathLength: on ? 0 : 1 }} />
      ))}
    </svg>
  );
}

export default function Journey() {
  const { t } = useLang();
  const ref = useRef<HTMLElement>(null);
  const { scrollYProgress } = useScroll({ target: ref, offset: ["start start", "end end"] });
  const p = useSpring(scrollYProgress, { stiffness: 90, damping: 22, mass: 0.4 });
  const x = useTransform(p, [0.04, 0.96], ["6%", "94%"]);
  const [stage, setStage] = useState(0);
  useMotionValueEvent(p, "change", (v) => {
    const k = STOPS.reduce((acc, s, i) => (v >= s - 0.05 ? i : acc), 0);
    setStage((old) => (old === k ? old : k));
  });
  const kind = stage === 0 ? "empty" : stage === 1 ? "pending" : stage <= 3 ? "sealed" : "verified";

  return (
    <section id="journey" ref={ref} className="relative mt-3 h-[360vh] rounded-[30px] bg-night text-white">
      <div className="sticky top-0 flex h-[100svh] flex-col overflow-hidden px-6 py-24 sm:px-12 lg:px-16">
        <div className="pointer-events-none absolute -left-40 top-1/3 h-[520px] w-[520px] rounded-full bg-violet/25 blur-[140px]" />
        <span className="tag text-violet-2">{t.journey.tag}</span>
        <h2 className="mt-3 max-w-3xl font-display text-[clamp(2.4rem,5.6vw,5rem)] font-[300] leading-[0.95] tracking-[-0.03em]" style={{ fontStretch: "112%" }}>
          {t.journey.title}
        </h2>

        <div className="relative mt-auto mb-[6vh] h-[52vh] min-h-[360px]">
          {/* sumbu waktu */}
          <div className="absolute left-[6%] right-[6%] top-[46%] h-px bg-white/15" />
          <motion.div className="absolute left-[6%] top-[46%] h-px origin-left bg-gradient-to-r from-violet to-violet-2" style={{ scaleX: p, width: "88%" }} />

          {/* stasiun */}
          {t.journey.stations.map((st, i) => {
            const on = stage >= i;
            const here = stage === i;
            return (
              <div key={i} className="absolute top-[46%] w-[19%] -translate-x-1/2" style={{ left: `${STOPS[i] * 100}%` }}>
                <motion.div
                  className="mx-auto -mt-[7px] h-3.5 w-3.5 rounded-full border-2"
                  animate={{ backgroundColor: on ? "#6e4bff" : "#0f0b26", borderColor: on ? "#9d86ff" : "rgba(255,255,255,.3)", scale: here ? 1.5 : 1 }}
                />
                <div className={`mt-6 text-center transition-opacity duration-500 ${here ? "opacity-100" : on ? "opacity-55" : "opacity-30"} ${here ? "" : "max-md:hidden"}`}>
                  <div className="tag text-violet-2">{st.t}</div>
                  <div className="mt-1.5 font-display text-[clamp(1rem,1.6vw,1.45rem)] font-[650] leading-tight">{st.h}</div>
                  <p className="mx-auto mt-1.5 max-w-[230px] text-[0.83rem] leading-snug text-white/60">{st.d}</p>
                </div>
              </div>
            );
          })}

          {/* peraga per stasiun, di atas sumbu */}
          <div className="absolute top-[4%]" style={{ left: `${STOPS[0] * 100}%`, transform: "translateX(-50%)" }}>
            <Candle closed={stage >= 0} />
          </div>
          <div className="absolute top-[2%]" style={{ left: `${STOPS[2] * 100}%`, transform: "translateX(-50%)" }}>
            <Fold on={stage >= 2} />
          </div>
          <div className="absolute top-[4%]" style={{ left: `${STOPS[3] * 100}%`, transform: "translateX(-50%)" }}>
            <motion.div
              initial={false}
              animate={{ scale: stage >= 3 ? 1 : 0.6, opacity: stage >= 3 ? 1 : 0.25, rotate: stage >= 3 ? -8 : 0 }}
              transition={{ type: "spring", stiffness: 300, damping: 14 }}
              className="grid h-[74px] w-[74px] place-items-center rounded-2xl border-2 border-dashed border-violet-2/70 font-mono text-[0.62rem] leading-tight text-violet-2"
            >
              BNB
              <br />
              block
              <br />
              #·····
            </motion.div>
          </div>

          {/* blok yang berjalan */}
          <motion.div className="absolute top-[46%] z-10 -translate-x-1/2 -translate-y-[86%]" style={{ left: x }}>
            <motion.div key={kind} initial={{ scale: 0.7, rotate: -6 }} animate={{ scale: 1, rotate: 0 }} transition={{ type: "spring", stiffness: 260, damping: 12 }}>
              <IsoCube kind={kind} size={96} glow={kind === "verified"} />
            </motion.div>
            <AnimatePresence>
              {stage === 1 && (
                <motion.div initial={{ opacity: 0, y: 6 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0 }} className="absolute -top-9 left-1/2 flex -translate-x-1/2 gap-1.5">
                  {["ENTER", "EXIT", "RESIZE"].map((w, i) => (
                    <motion.span key={w} initial={{ opacity: 0 }} animate={{ opacity: [0, 1, 0.5] }} transition={{ delay: i * 0.15 }} className="rounded-full border border-white/25 px-2 py-0.5 font-mono text-[0.6rem] text-white/80">
                      {w}
                    </motion.span>
                  ))}
                </motion.div>
              )}
              {stage === 4 && (
                <motion.div initial={{ opacity: 0, scale: 0.6 }} animate={{ opacity: 1, scale: 1 }} exit={{ opacity: 0 }} className="absolute -top-10 left-1/2 -translate-x-1/2 rounded-full bg-white px-3 py-1 font-mono text-xs font-bold text-night">
                  SAH ✓
                </motion.div>
              )}
            </AnimatePresence>
          </motion.div>
        </div>

        <div className="glass-dark mx-auto flex max-w-xl items-center gap-3 rounded-full px-5 py-3 font-mono text-[0.8rem] text-white/80">
          <span className="text-violet-2">$</span>
          {t.journey.verify}
        </div>
      </div>
    </section>
  );
}
