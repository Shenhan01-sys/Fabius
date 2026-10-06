"use client";

// Fabius Live Book (P164, docs/design/desk.md §Fabius Live Book): menggantikan panel "Fabius v2". Rekam jejak SELURUH buku Fabius dari
// `GET /desk/fabius`: strip pipeline 3D (siklus terakhir), statistik jujur (termasuk porsi fee terhadap rugi), kurva ekuitas sejak siklus pertama +
// pita bot, hasil per bot, dan pita keputusan dengan tautan bukti Merkle. Uang paper; keputusan + bukti nyata.

import dynamic from "next/dynamic";
import { useEffect, useMemo, useRef, useState } from "react";
import { useLang } from "@/components/lang";
import { LINKS } from "@/lib/copy";
import { hhmm, liveBook, type Desk, type LiveBook as LB } from "@/lib/desk";
import { GATE } from "@/lib/x402-buy";
import { Bridge } from "./bridge";
import { fmtPct, seats as toSeats } from "./model";

const Pipeline = dynamic(() => import("./PipelineScene"), { ssr: false, loading: () => <div className="absolute inset-0 animate-pulse rounded-2xl bg-lav/60" /> });

// warna pita per bot: keluarga palet Fabius + nama tertulis di pita/legenda (arti tidak hanya lewat warna)
const BOT_COLOR: Record<string, string> = {
  "B1-TREND": "#6e4bff",
  "B2-RS": "#9d86ff",
  "B3-CARRY": "#c9bdf2",
  "B4-LISTING-FADE": "#8b86a6",
  "B5-CORE-RWA": "#15122b",
  "B6-BOUNCE": "#4b33c7",
};
const tkr = (a: string) => a.replace("USDT", "");
const usd = (x: number) => x.toLocaleString("en-US", { maximumFractionDigits: 2 });
const day = (s: number) => new Date(s * 1000).toISOString().slice(0, 16).replace("T", " ") + "Z";

function webgl() {
  try {
    const c = document.createElement("canvas");
    return !!(c.getContext("webgl2") || c.getContext("webgl"));
  } catch {
    return false;
  }
}

function Curve({ lb, startLabel }: { lb: LB; startLabel: string }) {
  const W = 1000, Hc = 210, top = 10;
  const t0 = lb.mulai, t1 = Math.max(lb.siklus_terakhir, t0 + 1);
  const ys = [...lb.seri.map((p) => p[1]), lb.modal_awal];
  const lo = Math.min(...ys), hi = Math.max(...ys), span = hi - lo || 1;
  const x = (t: number) => ((t - t0) / (t1 - t0)) * W;
  const y = (v: number) => top + (1 - (v - lo) / span) * (Hc - top - 10);
  const d = lb.seri.map((p) => `${x(p[0]).toFixed(1)},${y(p[1]).toFixed(1)}`).join(" ");
  const base = y(lb.modal_awal);
  return (
    <svg viewBox={`0 0 ${W} ${Hc + 46}`} className="h-auto w-full" role="img" aria-label="equity curve and bot band">
      <line x1="0" x2={W} y1={base} y2={base} className="stroke-ink/25" strokeDasharray="6 6" vectorEffect="non-scaling-stroke" />
      <text x="4" y={base < 24 ? base + 20 : base - 6} className="fill-ink/45 font-mono text-[18px]">{startLabel}</text>
      <polyline points={`0,${Hc} ${d} ${W},${Hc}`} className="fill-violet/10" stroke="none" />
      <polyline points={d} fill="none" className="stroke-violet" strokeWidth="2.5" vectorEffect="non-scaling-stroke" />
      {lb.pita.map((p, i) => {
        const nx = i + 1 < lb.pita.length ? lb.pita[i + 1].dari : t1 + 300;
        const x0 = x(p.dari), w = Math.max(2, x(Math.min(nx, t1)) - x0);
        const c = BOT_COLOR[p.bot] ?? "#8b86a6";
        return (
          <g key={`${p.bot}${p.dari}`}>
            <rect x={x0} y={Hc + 8} width={w} height={26} rx={4} fill={c}>
              <title>{`${p.bot} · ${hhmm(p.dari)}–${hhmm(p.sampai)} · ${p.n} cycles`}</title>
            </rect>
            {w > 90 && (
              <text x={x0 + 8} y={Hc + 26} className="font-mono text-[15px]" fill={c === "#15122b" || c === "#4b33c7" || c === "#6e4bff" ? "#ffffff" : "#15122b"}>
                {p.bot}
              </text>
            )}
          </g>
        );
      })}
    </svg>
  );
}

export default function LiveBook({ d }: { d: Desk }) {
  const { t } = useLang();
  const f = t.desk.live;
  const [lb, setLb] = useState<LB | null>(null);
  const [err, setErr] = useState("");
  const [gl] = useState(() => webgl());
  const [reduced, setReduced] = useState(() => window.matchMedia("(prefers-reduced-motion: reduce)").matches);
  const [inView, setInView] = useState(true);
  const [w, setW] = useState(1000);
  const [bridge] = useState(() => new Bridge());
  const box = useRef<HTMLDivElement>(null);

  useEffect(() => {
    let live = true;
    const load = () =>
      liveBook().then(
        (x) => {
          if (!live) return;
          setLb(x);
          setErr("");
        },
        (e: unknown) => live && setErr(String(e)),
      );
    load();
    const id = setInterval(load, 30_000);
    const mq = window.matchMedia("(prefers-reduced-motion: reduce)");
    const on = () => setReduced(mq.matches);
    mq.addEventListener("change", on);
    return () => {
      live = false;
      clearInterval(id);
      mq.removeEventListener("change", on);
    };
  }, []);
  useEffect(() => {
    const el = box.current;
    if (!el) return;
    const io = new IntersectionObserver(([e]) => setInView(e.isIntersecting), { rootMargin: "120px" });
    const ro = new ResizeObserver(([e]) => setW(e.contentRect.width));
    io.observe(el);
    ro.observe(el);
    return () => (io.disconnect(), ro.disconnect());
  }, [lb]);

  // pekerja yang sama dengan lantai: penampilan dari template (slug + npc config)
  const looks = useMemo(() => Object.fromEntries(toSeats(d, d.t).map((s) => [s.slug, s.look])), [d]);
  const nilai = d.buku.find((b) => b.agent === "v2")?.keputusan_terakhir?.nilai_bot ?? {};
  const panel = "min-w-0 rounded-2xl border border-ink/10 bg-white/70 p-5";
  const label = "text-sm uppercase tracking-wide text-ink/50";

  if (!lb) return <div className={panel}>{err ? <p className="text-sm text-ink/60">{err}</p> : <p className="text-sm text-ink/50">{f.loading}</p>}</div>;
  if (lb.kosong) return <div className={panel}><p className="text-sm text-ink/50">{f.empty}</p></div>;

  const p = lb.pipa;
  const valid = p.agen.filter((a) => a.status === "ok").length;
  const pos = Object.entries(p.target);
  const nLong = pos.filter(([, x]) => x > 0).length, nShort = pos.length - nLong;
  // rem rugi harian (SK-M10) aktif = buku sengaja datar sampai 00:00 UTC: ditampilkan, bukan disembunyikan di pita keputusan
  const brake = /daily loss brake/.test(p.dasar ?? "");
  const posText = pos.length ? `${f.positions.replace("{n}", String(pos.length))} (▲${nLong} ▼${nShort})` : brake ? `${f.flatBook} · ${f.brakeShort}` : f.flatBook;
  const sealed = p.status === "dikomit";
  const loss = lb.modal_awal - lb.ekuitas;
  const feeShare = loss > 0 ? Math.round((lb.fee / loss) * 100) : null;
  const compact = w < 640;
  // gerbang mengirim JSON berkunci terurut abjad: urutkan per jumlah siklus di sini
  const byCycles = Object.entries(lb.per_bot).sort((a, b) => b[1].siklus - a[1].siklus);
  const summary = f.summary
    .replace("{t}", hhmm(p.siklus))
    .replace("{v}", String(valid))
    .replace("{m}", String(p.agen.length))
    .replace("{r}", p.rumus)
    .replace("{bot}", p.bot ?? "-")
    .replace("{score}", p.skor_bot != null ? ` (${p.skor_bot >= 0 ? "+" : ""}${p.skor_bot.toFixed(1)})` : "")
    .replace("{p}", posText)
    .replace("{seal}", sealed ? `${f.sealed} ✓` : p.status ?? "-");
  const tag = "invisible absolute left-0 top-0 z-20 whitespace-nowrap rounded-lg border bg-white/90 px-2 py-0.5 text-left shadow-sm backdrop-blur";
  const tiles: [string, string, string?][] = [
    [f.stats.equity, usd(lb.ekuitas), "USDT"],
    [f.stats.ret, fmtPct(lb.hasil_pct)],
    [f.stats.dd, fmtPct(lb.drawdown_maks_pct)],
    [f.stats.fees, usd(lb.fee), feeShare != null ? f.stats.feeShare.replace("{p}", String(feeShare)) : "USDT"],
    [f.stats.trades, String(lb.transaksi)],
    [f.stats.inMarket, `${lb.siklus_berposisi} / ${lb.siklus}`],
  ];
  return (
    <div className={panel}>
      <div className="flex flex-wrap items-end justify-between gap-2">
        <div>
          <p className="font-display text-2xl font-[400] tracking-[-0.01em] text-ink sm:text-3xl">{f.title}</p>
          <p className="mt-0.5 text-xs text-ink/55">{f.tagline}</p>
        </div>
        <p className="font-mono text-[11px] text-ink/45">{f.since.replace("{d}", day(lb.mulai))}</p>
      </div>

      {gl ? (
        <div ref={box} className="relative mt-4 overflow-hidden rounded-2xl bg-gradient-to-b from-lav/70 to-white" style={{ height: "clamp(150px, 24vw, 290px)" }}>
          <Pipeline pipa={p} nilai={nilai} looks={looks} beat={p.siklus} bridge={bridge} active={inView} reduced={reduced} />
          <span ref={bridge.el("agents")} className={`${tag} border-violet/20 font-mono text-[10px] text-ink/70`}>
            {compact ? `${valid}/${p.agen.length}` : `${f.stages.agents} · ${f.valid.replace("{n}", String(valid)).replace("{m}", String(p.agen.length))}`}
          </span>
          <span ref={bridge.el("formula")} className={`${tag} border-violet/40 bg-ink/90 font-mono text-[10px] text-violet-2`}>
            {compact ? `${p.rumus} · ${p.bot?.split("-")[0] ?? "-"}` : `${f.stages.formula} ${p.rumus} · ${p.bot ?? "-"}`}
            {p.skor_bot != null && !compact ? ` ${p.skor_bot >= 0 ? "+" : ""}${p.skor_bot.toFixed(1)}` : ""}
          </span>
          <span ref={bridge.el("bot")} className={`${tag} border-violet/20 font-mono text-[10px] text-ink/70`}>
            {compact ? p.bot?.split("-")[0] : `${f.stages.bot} · ${p.bot ?? "-"}`}
          </span>
          <span ref={bridge.el("book")} className={`${tag} border-violet/20 font-mono text-[10px] text-ink/70`}>
            {compact ? `${pos.length}` : `${f.stages.book} · ${posText}`}
          </span>
          {p.tx ? (
            <a ref={bridge.el("chain")} href={LINKS.tx + p.tx} target="_blank" rel="noreferrer" className={`${tag} pointer-events-auto border-violet/20 font-mono text-[10px] text-violet underline-offset-2 hover:underline`}>
              {compact ? "✓" : `${f.stages.chain} · ${sealed ? f.sealed + " ✓" : p.status} ↗`}
            </a>
          ) : (
            <span ref={bridge.el("chain")} className={`${tag} border-violet/20 font-mono text-[10px] text-ink/60`}>
              {f.stages.chain} · {p.status ?? "-"}
            </span>
          )}
        </div>
      ) : null}
      <p aria-live="polite" className="mt-2 text-xs leading-snug text-ink/65">
        {brake && <span className="mr-2 rounded-full bg-ink px-2 py-0.5 font-mono text-[10px] text-white">■ {f.brake}</span>}
        {summary}
      </p>

      <div className="mt-4 grid gap-4 lg:grid-cols-[1.6fr_1fr]">
        <div className="rounded-xl border border-ink/10 p-3">
          <p className="text-[10px] uppercase tracking-wide text-ink/45">
            {f.curve} · {f.band}
          </p>
          <div className="mt-2">
            <Curve lb={lb} startLabel={f.start.replace("{v}", usd(lb.modal_awal))} />
          </div>
          <div className="mt-1 flex flex-wrap gap-x-3 gap-y-1 text-[10px] text-ink/60">
            {byCycles.map(([b]) => (
              <span key={b} className="inline-flex items-center gap-1 font-mono">
                <span className="inline-block h-2.5 w-2.5 rounded-sm" style={{ background: BOT_COLOR[b] ?? "#8b86a6" }} aria-hidden />
                {b}
              </span>
            ))}
          </div>
        </div>
        <div className="grid grid-cols-2 gap-2 self-start">
          {tiles.map(([k, x, sub]) => (
            <div key={k} className="rounded-xl border border-ink/10 px-3 py-2">
              <p className="truncate text-[10px] uppercase tracking-wide text-ink/45">{k}</p>
              <p className={`mt-0.5 truncate font-mono text-[15px] ${k === f.stats.ret && lb.hasil_pct < 0 ? "text-ink" : "text-ink"}`}>{x}</p>
              {sub && <p className="truncate font-mono text-[10px] text-ink/45">{sub}</p>}
            </div>
          ))}
          <div className="col-span-2 rounded-xl border border-ink/10 px-3 py-2">
            <p className="text-[10px] uppercase tracking-wide text-ink/45">{f.nowPos}</p>
            <div className="mt-1 flex flex-wrap gap-1">
              {pos.length === 0 && <span className="text-xs text-ink/50">■ {f.flatBook}</span>}
              {pos
                .sort((a, b) => Math.abs(b[1]) - Math.abs(a[1]))
                .map(([a, x]) => (
                  <span key={a} className={`rounded-full border px-2 py-0.5 font-mono text-[11px] ${x >= 0 ? "border-violet/40 text-violet" : "border-ink/30 text-ink"}`}>
                    {x >= 0 ? "▲" : "▼"} {tkr(a)} {(Math.abs(x) * 100).toFixed(1)}%
                  </span>
                ))}
            </div>
          </div>
        </div>
      </div>

      <div className="mt-4 rounded-xl border border-ink/10 p-3">
        <p className={label}>{f.perBot}</p>
        <p className="mt-0.5 text-[11px] text-ink/50">{f.perBotNote}</p>
        <table className="mt-2 w-full text-left text-xs">
          <thead className="text-ink/45">
            <tr>
              <th className="py-1 font-normal">{f.cols.bot}</th>
              <th className="py-1 font-normal">{f.cols.cycles}</th>
              <th className="py-1 font-normal">{f.cols.result}</th>
              <th className="py-1 font-normal">{f.cols.fees}</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-ink/5 font-mono">
            {byCycles.map(([b, x]) => (
              <tr key={b}>
                <td className="py-1.5">
                  <span className="mr-1.5 inline-block h-2.5 w-2.5 rounded-sm align-middle" style={{ background: BOT_COLOR[b] ?? "#8b86a6" }} aria-hidden />
                  {b}
                </td>
                <td className="py-1.5">{x.siklus}</td>
                <td className={`py-1.5 ${x.hasil >= 0 ? "text-violet" : "text-ink"}`}>
                  {x.hasil >= 0 ? "+" : ""}
                  {usd(x.hasil)} USDT
                </td>
                <td className="py-1.5 text-ink/60">{usd(x.fee)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      <div className="mt-4 rounded-xl border border-ink/10 p-3">
        <p className={label}>{f.tape}</p>
        <ul className="mt-2 max-h-[22rem] divide-y divide-ink/5 overflow-auto pr-1 text-xs">
          {lb.pita_keputusan.map((r) => (
            <li key={r.hash} className="grid gap-x-3 gap-y-0.5 py-2 sm:grid-cols-[3.5rem_9rem_1fr_4.5rem]">
              <span className="font-mono text-ink/50">{hhmm(r.siklus)}</span>
              <span className="truncate">
                <span className="rounded-full px-1.5 font-mono text-[10px] text-white" style={{ background: BOT_COLOR[r.bot ?? ""] ?? "#8b86a6" }}>
                  {r.bot ?? "-"}
                </span>{" "}
                <span className="text-ink/45">{r.masuk} {f.cols.agents.toLowerCase()}</span>
              </span>
              <span className="min-w-0">
                {r.isi.length === 0 ? (
                  <span className="text-ink/45">■ {f.hold} · {r.dasar}</span>
                ) : (
                  <span className="text-ink/75">
                    {r.isi.map((x) => `${x.ke > x.dari ? "▲" : "▼"}${tkr(x.aset)} ${(x.dari * 100).toFixed(0)}→${(x.ke * 100).toFixed(0)}%`).join("  ")}
                    <span className="text-ink/45"> · fee {usd(r.isi.reduce((s, x) => s + x.fee, 0))}</span>
                  </span>
                )}
              </span>
              <a className="font-mono text-violet underline-offset-2 hover:underline sm:text-right" href={`${GATE}/desk/proof/${r.hash}`} target="_blank" rel="noreferrer">
                {f.cols.proof} ↗
              </a>
            </li>
          ))}
        </ul>
      </div>
    </div>
  );
}
