"use client";

// Modal statistik + riwayat satu buku meja (P158, docs/design/desk.md). Keluar dari kotak layar monitor agent (rect terproyeksi) dan membesar ke
// tengah lantai; tutup = kembali ke monitor. Angka dari gerbang `GET /desk/agent/<nama>` (Gate.meja_agent): statistik terukur 24 jam, riwayat
// keputusan terbaru dulu, tiap baris bertaut ke bukti Merkle `/desk/proof/<hash>`.

import { motion } from "motion/react";
import { useEffect, useRef, useState } from "react";
import { useAkses } from "@/components/akses";
import { useLang } from "@/components/lang";
import { agentDetail, hhmm, type AgentDetail, type Buku } from "@/lib/desk";
import { GATE } from "@/lib/x402-buy";
import { fmtPct } from "./model";
import type { Rect } from "./Scene";

type V = {
  close: string;
  tabs: { v2: string; v1: string };
  stats: Record<string, string>;
  curve: string;
  positions: string;
  history: string;
  cols: { time: string; action: string; fills: string; proof: string };
  buy: string;
  sell: string;
  noFills: string;
  loading: string;
  agentId: string;
  status: Record<string, string>;
};

const tkr = (a: string) => a.replace("USDT", "");

function Curve({ pts }: { pts: [number, number][] }) {
  if (pts.length < 2) return <div className="h-28" />;
  const ys = pts.map((p) => p[1]);
  const lo = Math.min(...ys), hi = Math.max(...ys), span = hi - lo || 1;
  const d = pts.map((p, i) => `${(i / (pts.length - 1)) * 100},${46 - ((p[1] - lo) / span) * 42}`).join(" ");
  return (
    <div>
      <svg viewBox="0 0 100 48" preserveAspectRatio="none" className="h-36 w-full" aria-hidden>
        <polyline points={`0,48 ${d} 100,48`} className="fill-violet/10" stroke="none" />
        <polyline points={d} fill="none" strokeWidth="1.6" vectorEffect="non-scaling-stroke" className="stroke-violet" />
      </svg>
      <div className="mt-1 flex justify-between font-mono text-[10px] text-ink/45">
        <span>
          {hhmm(pts[0][0])} → {hhmm(pts[pts.length - 1][0])}
        </span>
        <span>
          {lo.toFixed(2)} – {hi.toFixed(2)} USDT
        </span>
      </div>
    </div>
  );
}

export default function AgentModal({
  title,
  books,
  origin,
  box,
  v,
  reduced,
  onClose,
}: {
  title: string;
  books: { key: "v2" | "v1"; book: Buku }[];
  origin: Rect;
  box: { w: number; h: number };
  v: V;
  reduced: boolean;
  onClose: () => void;
}) {
  const ak = useAkses();
  const va = useLang().t.desk.akses;
  const [tab, setTab] = useState(books[0].key);
  const [data, setData] = useState<Record<string, AgentDetail | string>>({});
  const closeRef = useRef<HTMLButtonElement>(null);
  const panel = useRef<HTMLDivElement>(null);
  const book = books.find((b) => b.key === tab)!.book;
  const d = data[book.agent];

  useEffect(() => {
    if (data[book.agent]) return;
    let live = true;
    ak.token()
      .then((tok) => agentDetail(book.agent, tok))
      .then(
      (x) => live && setData((o) => ({ ...o, [book.agent]: x })),
      (e: unknown) => live && setData((o) => ({ ...o, [book.agent]: String(e) })),
    );
    return () => {
      live = false;
    };
  }, [book.agent, data, ak]);

  useEffect(() => {
    closeRef.current?.focus();
    const key = (e: KeyboardEvent) => {
      if (e.key === "Escape") onClose();
      if (e.key === "Tab" && panel.current) {
        const f = panel.current.querySelectorAll<HTMLElement>("button, a[href]");
        if (!f.length) return;
        const first = f[0], last = f[f.length - 1];
        if (e.shiftKey && document.activeElement === first) {
          e.preventDefault();
          last.focus();
        } else if (!e.shiftKey && document.activeElement === last) {
          e.preventDefault();
          first.focus();
        }
      }
    };
    window.addEventListener("keydown", key);
    return () => window.removeEventListener("keydown", key);
  }, [onClose]);

  const w = Math.min(box.w * 0.94, 920), h = box.h * 0.92;
  const target = { left: (box.w - w) / 2, top: (box.h - h) / 2, width: w, height: h };
  const from = { left: origin.x, top: origin.y, width: Math.max(origin.w, 24), height: Math.max(origin.h, 16) };
  const st = typeof d === "object" ? d.statistik : null;
  const tiles: [string, string, string?][] = [
    [v.stats.equity, `${book.ekuitas.toLocaleString("en-US", { maximumFractionDigits: 2 })}`, "USDT"],
    [v.stats.ret, fmtPct(book.hasil_pct)],
    [v.stats.trades, String(book.n_trade)],
    [v.stats.fees, book.biaya.toFixed(2), "USDT"],
    [v.stats.cycles, st ? `${st.ok} ${v.stats.ok}` : "…", st ? `${st.gagal} ${v.stats.failed} · ${st.terlambat} ${v.stats.late}` : undefined],
    [v.stats.withTrades, st ? `${st.siklus_bertransaksi} / ${st.siklus_24j}` : "…"],
  ];
  return (
    <>
      <motion.div
        className="absolute inset-0 z-40 rounded-2xl bg-ink/25 backdrop-blur-[2px]"
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        exit={{ opacity: 0 }}
        transition={{ duration: reduced ? 0 : 0.25 }}
        onClick={onClose}
      />
      <motion.div
        ref={panel}
        role="dialog"
        aria-modal="true"
        aria-labelledby="desk-modal-title"
        className="absolute z-50 flex flex-col overflow-hidden rounded-2xl border border-violet/25 bg-white shadow-2xl"
        initial={{ ...from, opacity: 0.6, borderRadius: 6 }}
        animate={{ ...target, opacity: 1, borderRadius: 16 }}
        exit={{ ...from, opacity: 0, borderRadius: 6 }}
        transition={reduced ? { duration: 0 } : { type: "spring", stiffness: 260, damping: 30 }}
      >
        <div className="flex items-center gap-3 border-b border-ink/10 bg-ink px-4 py-2.5 text-white">
          <span className="grid h-7 w-7 place-items-center rounded-md bg-violet font-mono text-[11px]" aria-hidden>
            {title.slice(0, 2)}
          </span>
          <div className="min-w-0 flex-1">
            <p id="desk-modal-title" className="truncate text-sm font-medium">
              {title}
            </p>
            <p className="truncate font-mono text-[10px] text-white/55">
              {typeof d === "object" && d.model ? d.model : ""}
              {typeof d === "object" && d.agent_id ? ` · ${v.agentId} #${d.agent_id}` : ""}
            </p>
          </div>
          {books.length > 1 && (
            <div className="hidden gap-1 sm:flex" role="tablist">
              {books.map((b) => (
                <button
                  key={b.key}
                  role="tab"
                  aria-selected={tab === b.key}
                  onClick={() => setTab(b.key)}
                  className={`rounded-full px-2.5 py-0.5 text-[11px] ${tab === b.key ? "bg-violet text-white" : "bg-white/10 text-white/70"}`}
                >
                  {v.tabs[b.key]}
                </button>
              ))}
            </div>
          )}
          <button ref={closeRef} onClick={onClose} className="rounded-full bg-white/10 px-2.5 py-0.5 text-[11px] focus-visible:outline focus-visible:outline-2 focus-visible:outline-violet-2">
            {v.close} ✕
          </button>
        </div>
        <div className="min-h-0 flex-1 overflow-auto p-4">
          {books.length > 1 && (
            <div className="mb-3 flex gap-1 sm:hidden" role="tablist">
              {books.map((b) => (
                <button key={b.key} role="tab" aria-selected={tab === b.key} onClick={() => setTab(b.key)}
                  className={`rounded-full px-2.5 py-0.5 text-[11px] ${tab === b.key ? "bg-violet text-white" : "bg-ink/5 text-ink/70"}`}>
                  {v.tabs[b.key]}
                </button>
              ))}
            </div>
          )}
          <div className="grid grid-cols-2 gap-2 sm:grid-cols-3 lg:grid-cols-6">
            {tiles.map(([k, x, sub]) => (
              <div key={k} className="rounded-xl border border-ink/10 px-3 py-2">
                <p className="truncate text-[10px] uppercase tracking-wide text-ink/45">{k}</p>
                <p className="mt-0.5 truncate font-mono text-[14px] text-ink">{x}</p>
                {sub && <p className="truncate font-mono text-[10px] text-ink/45">{sub}</p>}
              </div>
            ))}
          </div>
          <div className="mt-3 grid gap-3 md:grid-cols-[1.4fr_1fr]">
            <div className="rounded-xl border border-ink/10 p-3">
              <p className="text-[10px] uppercase tracking-wide text-ink/45">{v.curve}</p>
              <div className="mt-2">
                <Curve pts={book.deret} />
              </div>
            </div>
            <div className="rounded-xl border border-ink/10 p-3">
              <p className="text-[10px] uppercase tracking-wide text-ink/45">{v.positions}</p>
              <ul className="mt-2 space-y-1">
                {book.terkunci && book.n_posisi ? <li className="text-xs text-ink/55">🔒 {va.lockedPositions.replace("{n}", String(book.n_posisi))}</li> : null}
                {Object.entries(book.posisi).length === 0 && !(book.terkunci && book.n_posisi) && <li className="text-xs text-ink/50">■ {v.noFills}</li>}
                {Object.entries(book.posisi)
                  .sort((a, b) => Math.abs(b[1]) - Math.abs(a[1]))
                  .map(([a, x]) => (
                    <li key={a} className="grid grid-cols-[6.5rem_1fr_3.2rem] items-center gap-2 text-[11px]">
                      <span className="truncate font-mono">{x >= 0 ? "▲" : "▼"} {tkr(a)}</span>
                      <span className="h-1.5 rounded-full bg-ink/5">
                        <span className={`block h-1.5 rounded-full ${x >= 0 ? "bg-violet" : "bg-ink/50"}`} style={{ width: `${Math.min(100, (Math.abs(x) / 0.25) * 100)}%` }} />
                      </span>
                      <span className="text-right font-mono">{(x * 100).toFixed(1)}%</span>
                    </li>
                  ))}
              </ul>
              {st?.bot_pilihan && Object.keys(st.bot_pilihan).length > 0 && (
                <>
                  <p className="mt-3 text-[10px] uppercase tracking-wide text-ink/45">{v.stats.picks}</p>
                  <div className="mt-1 flex flex-wrap gap-1">
                    {Object.entries(st.bot_pilihan)
                      .sort((a, b) => b[1] - a[1])
                      .map(([b, n]) => (
                        <span key={b} className="rounded-full border border-violet/30 px-2 py-0.5 font-mono text-[10px] text-violet">
                          {b} ×{n}
                        </span>
                      ))}
                  </div>
                </>
              )}
            </div>
          </div>
          <p className="mt-4 text-[10px] uppercase tracking-wide text-ink/45">{v.history}</p>
          {typeof d === "string" && <p className="mt-2 text-xs text-ink/60">{d}</p>}
          {!d && <p className="mt-2 text-xs text-ink/50">{v.loading}</p>}
          {typeof d === "object" && d.akses?.live === false && <p className="mt-1 text-[11px] text-ink/50">🔒 {va.lockedHistory}</p>}
          {typeof d === "object" && (
            <table className="mt-2 w-full text-left text-[11px]">
              <thead className="text-ink/45">
                <tr>
                  <th className="py-1 pr-2 font-normal">{v.cols.time}</th>
                  <th className="py-1 pr-2 font-normal">{v.cols.action}</th>
                  <th className="py-1 pr-2 font-normal">{v.cols.fills}</th>
                  <th className="py-1 font-normal">{v.cols.proof}</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-ink/5 align-top">
                {d.riwayat.map((r) => (
                  <tr key={r.hash}>
                    <td className="py-1.5 pr-2 font-mono text-ink/55">{hhmm(r.siklus)}</td>
                    <td className="max-w-[22rem] py-1.5 pr-2">
                      {r.status !== "ok" ? (
                        <span className="text-gap">✕ {v.status[r.status] ?? r.status}</span>
                      ) : (
                        <>
                          {r.bot && <span className="mr-1 rounded-full bg-violet/10 px-1.5 font-mono text-[10px] text-violet">{r.bot}</span>}
                          <span className="line-clamp-2 text-ink/75" title={r.ringkasan ?? ""}>{r.ringkasan}</span>
                        </>
                      )}
                    </td>
                    <td className="py-1.5 pr-2 font-mono">
                      {r.isi.length === 0 && <span className="text-ink/40">■ {v.noFills}</span>}
                      {r.isi.map((f) => (
                        <span key={f.aset} className={`block whitespace-nowrap ${f.ke > f.dari ? "text-violet" : "text-ink/70"}`}>
                          {f.ke > f.dari ? `▲ ${v.buy}` : `▼ ${v.sell}`} {tkr(f.aset)} {(f.dari * 100).toFixed(0)}→{(f.ke * 100).toFixed(0)}% @{f.harga.toLocaleString("en-US", { maximumFractionDigits: 4 })}
                        </span>
                      ))}
                    </td>
                    <td className="py-1.5">
                      <a className="font-mono text-violet underline-offset-2 hover:underline" href={`${GATE}/desk/proof/${r.hash}`} target="_blank" rel="noreferrer">
                        {r.hash.slice(0, 8)}…↗
                      </a>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </div>
      </motion.div>
    </>
  );
}
