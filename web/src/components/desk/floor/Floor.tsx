"use client";

// Bagian "lantai trading" di /desk (P158, docs/design/desk.md): menggantikan daftar "Decisions, newest first". Adegan 3D di-load hanya di sini
// (dynamic, tanpa SSR); lapisan inklusif selalu ada: pita keterangan aria-live, tombol "View as list", daftar otomatis bila WebGL tidak ada,
// tanpa gerak bila prefers-reduced-motion.

import dynamic from "next/dynamic";
import { AnimatePresence } from "motion/react";
import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { useLang } from "@/components/lang";
import { hhmm, type Desk } from "@/lib/desk";
import AgentModal from "./AgentModal";
import { fmtPct, glyph, hubBook, seats as toSeats } from "./model";
import { Bridge } from "./bridge";
import type { Rect } from "./Scene";

const Scene = dynamic(() => import("./Scene"), { ssr: false, loading: () => <div className="absolute inset-0 animate-pulse rounded-2xl bg-lav/60" /> });

function webgl() {
  try {
    const c = document.createElement("canvas");
    return !!(c.getContext("webgl2") || c.getContext("webgl"));
  } catch {
    return false;
  }
}

export default function Floor({ d }: { d: Desk }) {
  const { t } = useLang();
  const v = t.desk;
  const f = v.floor;
  const box = useRef<HTMLDivElement>(null);
  // Floor hanya dirender di klien (data /desk dimuat sesudah hidrasi), jadi deteksi langsung di inisialisasi state
  const [gl] = useState<boolean>(() => webgl());
  const [reduced, setReduced] = useState(() => window.matchMedia("(prefers-reduced-motion: reduce)").matches);
  const [list, setList] = useState(false);
  const [inView, setInView] = useState(true);
  const [size, setSize] = useState({ w: 1000, h: 520 });
  const [open, setOpen] = useState<{ name: string; origin: Rect } | null>(null);
  const [bridge] = useState(() => new Bridge());

  useEffect(() => {
    const mq = window.matchMedia("(prefers-reduced-motion: reduce)");
    const on = () => setReduced(mq.matches);
    mq.addEventListener("change", on);
    return () => mq.removeEventListener("change", on);
  }, []);
  useEffect(() => {
    const el = box.current;
    if (!el) return;
    const io = new IntersectionObserver(([e]) => setInView(e.isIntersecting), { rootMargin: "120px" });
    const ro = new ResizeObserver(([e]) => setSize({ w: e.contentRect.width, h: e.contentRect.height }));
    io.observe(el);
    ro.observe(el);
    return () => (io.disconnect(), ro.disconnect());
  }, [gl, list]);

  const seatList = useMemo(() => toSeats(d, d.t), [d]);
  const hub = hubBook(d);
  const kh = hub?.keputusan_terakhir;
  const nInstr = kh?.instrumen?.length ?? Object.keys(hub?.posisi ?? {}).length;
  const hubLine = !hub ? "-" : nInstr ? f.onInstr.replace("{bot}", kh?.bot ?? "consensus").replace("{n}", String(nInstr)) : f.flatHub;
  // terlambat = model tidak menjawab dalam batas waktu (bukan galat model): kata "late", bukan "failed"
  const word = (s: (typeof seatList)[number]) => (s.pose === "fail" && s.main.status_terakhir === "terlambat" ? v.status.terlambat : f.poses[s.pose]);
  const last = d.siklus_terakhir;
  const caption = last
    ? f.caption
        .replace("{t}", hhmm(last.siklus))
        .replace(
          "{agents}",
          seatList
            .map((s) => `${s.nama}${s.trial ? ` (${f.trial})` : ""} ${glyph[s.pose]} ${word(s)}${s.pose === "trade" && s.main.isi_terakhir ? ` (${s.main.isi_terakhir} ${f.fills})` : ""}`)
            .join(" · "),
        )
        .replace("{hub}", hubLine)
        .replace("{seal}", last.status === "dikomit" ? f.sealOk : f.sealNo)
    : "";
  const cyc12 = (d.siklus_12 ?? []).slice(-12);
  const nOk = cyc12.filter((c) => c.status === "dikomit").length;
  // label = tombol DOM biasa; posisinya digeser tiap frame oleh LabelSync di dalam kanvas (mulai tersembunyi sampai frame pertama)
  const tagCls = "invisible absolute left-0 top-0 z-20 whitespace-nowrap";
  // HP, atau banyak agent di layar sedang: label = nama pendek + glyph; rincian tetap di aria-label + modal
  const compact = size.w < 640 || (seatList.length > 4 && size.w < 1000) || seatList.length > 6;
  const onOpen = useCallback((name: string, origin: Rect) => setOpen({ name, origin }), []);
  const close = useCallback(() => setOpen(null), []);

  // buku untuk modal: agent = v2 dulu lalu v1 (selama berdampingan); hub = v2 Fabius + v1 konsensus
  const modal = useMemo(() => {
    if (!open) return null;
    const isHub = open.name === "v2" || open.name === "konsensus";
    if (isHub) {
      const b = [{ key: "v2" as const, book: d.buku.find((x) => x.agent === "v2") }, { key: "v1" as const, book: d.buku.find((x) => x.agent === "konsensus") }];
      return { title: f.hub, books: b.filter((x) => x.book).map((x) => ({ key: x.key, book: x.book! })) };
    }
    const s = seatList.find((x) => x.main.agent === open.name);
    if (!s) return null;
    const b = [{ key: "v2" as const, book: s.v2 }, { key: "v1" as const, book: s.v1 }];
    return { title: s.nama, books: b.filter((x) => x.book).map((x) => ({ key: x.key, book: x.book! })) };
  }, [open, d, seatList, f.hub]);

  const showList = list || !gl;
  const names = Object.fromEntries(d.buku.map((b) => [b.agent, b.nama]));
  const cycles = Array.from(new Set(d.rekaman.map((r) => r.siklus))).sort((a, b) => b - a).slice(0, 5);
  return (
    <div className="min-w-0 rounded-2xl border border-ink/10 bg-white/70 p-5">
      <div className="flex flex-wrap items-end justify-between gap-2">
        <div>
          <p className="text-sm uppercase tracking-wide text-ink/50">{f.title}</p>
          <p className="mt-0.5 text-xs text-ink/50">{f.sub}</p>
        </div>
        {gl && (
          <button onClick={() => setList((x) => !x)} className="rounded-full border border-ink/15 px-3 py-1 text-xs text-ink/70 hover:border-violet focus-visible:outline focus-visible:outline-2 focus-visible:outline-violet">
            {list ? f.scene : f.list}
          </button>
        )}
      </div>
      {!showList && gl && (
        <div ref={box} className="relative mt-3 overflow-hidden rounded-2xl bg-gradient-to-b from-lav/70 to-white" style={{ height: "clamp(340px, 52vw, 560px)" }}>
          <Scene seats={seatList} hub={hub} cycles={cyc12} beat={last?.siklus ?? 0} bridge={bridge} onOpen={onOpen} active={inView && !open} reduced={reduced} />
          {seatList.map((s) => (
            <button
              key={s.slug}
              ref={bridge.el(s.slug)}
              type="button"
              onClick={() => bridge.open(s.slug)}
              aria-label={f.open.replace("{name}", s.nama)}
              className={`${tagCls} border border-violet/20 bg-white/90 text-left shadow-sm backdrop-blur transition-colors hover:border-violet focus-visible:outline focus-visible:outline-2 focus-visible:outline-violet ${compact ? "rounded-lg px-1.5 py-0.5" : "rounded-xl px-2.5 py-1"}`}
            >
              {compact ? (
                <span className={`block font-mono text-[10px] leading-tight ${s.pose === "fail" ? "text-gap" : s.pose === "trade" ? "text-violet" : "text-ink/70"}`}>
                  {glyph[s.pose]} {s.look.short}
                  {s.trial ? ` · ${f.trialShort}` : ""}
                </span>
              ) : (
                <>
                  <span className="block text-[11px] font-medium leading-tight text-ink">
                    {s.nama}
                    {s.trial && <span className="ml-1 rounded bg-lav-2 px-1 font-mono text-[9px] uppercase text-ink/60">{f.trialShort}</span>}
                  </span>
                  <span className={`block font-mono text-[10px] leading-tight ${s.pose === "fail" ? "text-gap" : s.pose === "trade" ? "text-violet" : "text-ink/55"}`}>
                    {glyph[s.pose]} {word(s)}
                    {s.pose === "trade" && s.main.isi_terakhir ? ` · ${s.main.isi_terakhir} ${f.fills}` : ""} · {fmtPct(s.main.hasil_pct)}
                  </span>
                </>
              )}
            </button>
          ))}
          {hub && (
            <button
              ref={bridge.el("hub")}
              type="button"
              onClick={() => bridge.open("hub")}
              aria-label={f.open.replace("{name}", f.hub)}
              className={`${tagCls} border border-violet/40 bg-ink/90 text-left text-white shadow-sm backdrop-blur focus-visible:outline focus-visible:outline-2 focus-visible:outline-violet-2 ${compact ? "rounded-lg px-1.5 py-0.5" : "rounded-xl px-3 py-1.5"}`}
            >
              {compact ? (
                <span className="block font-mono text-[10px] leading-tight">
                  {f.hub} · {hub.keputusan_terakhir?.bot?.split("-")[0] ?? fmtPct(hub.hasil_pct)}
                </span>
              ) : (
                <>
                  <span className="block text-[11px] font-medium leading-tight">{f.hub}</span>
                  <span className="block font-mono text-[10px] leading-tight text-violet-2">
                    {hubLine} · {fmtPct(hub.hasil_pct)}
                  </span>
                </>
              )}
            </button>
          )}
          {cyc12.length > 0 && (
            <span ref={bridge.el("tower")} className={`${tagCls} pointer-events-none z-10 rounded-lg border border-violet/20 bg-white/90 px-2 py-0.5 font-mono text-[10px] text-ink/70 shadow-sm`}>
              {compact ? `${nOk}/${cyc12.length} ✓` : `${f.chain} · ${nOk}/${cyc12.length} ${f.anchored}`}
            </span>
          )}
          <p aria-live="polite" className="pointer-events-none absolute inset-x-3 bottom-2 z-10 rounded-xl bg-white/80 px-3 py-1.5 text-center text-[11px] leading-snug text-ink/70 backdrop-blur">
            {caption}
          </p>
          <AnimatePresence>
            {open && modal && modal.books.length > 0 && (
              <AgentModal key={open.name} title={modal.title} books={modal.books} origin={open.origin} box={size} v={{ ...f, status: v.status }} reduced={reduced} onClose={close} />
            )}
          </AnimatePresence>
        </div>
      )}
      {showList && (
        <div className="mt-3 space-y-3">
          <p aria-live="polite" className="text-xs text-ink/70">{caption}</p>
          {cycles.map((c) => (
            <section key={c} className="rounded-xl border border-ink/10 p-3">
              <p className="font-mono text-[11px] text-ink/50">{hhmm(c)}</p>
              <ul className="mt-1 space-y-1">
                {d.rekaman
                  .filter((r) => r.siklus === c)
                  .map((r) => (
                    <li key={r.hash} className="grid gap-x-2 text-xs sm:grid-cols-[12rem_1fr]">
                      <span className="text-ink/80">
                        {names[r.agent] ?? r.agent}
                        {r.status && r.status !== "ok" && <span className="text-gap"> · ✕ {v.status[r.status] ?? r.status}</span>}
                        {(r.isi?.length ?? 0) > 0 && <span className="text-violet"> · ⇄ {r.isi!.length} {f.fills}</span>}
                      </span>
                      <span className="line-clamp-2 text-ink/60">{r.keputusan?.ringkasan ?? r.dasar ?? r.galat ?? ""}</span>
                    </li>
                  ))}
              </ul>
            </section>
          ))}
        </div>
      )}
    </div>
  );
}
