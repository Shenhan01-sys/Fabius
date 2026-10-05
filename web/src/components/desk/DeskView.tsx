"use client";

// /desk (P152, F-D109): meja AI 5 menit. Tiap agent = kartu dengan kurva ekuitas (SVG dari deret siklus), bacaan pasar terakhir, dan target yang
// diubah beserta alasannya; konsensus = batang bobot dari sumbu nol (long ke kanan, short ke kiri). Umpan = rekaman per siklus, masing-masing ber-hash
// dan masuk Merkle root yang dikomit ke DeskAnchor sebelum siklus berakhir. Data dimuat ulang tiap 30 detik.

import { useEffect, useState } from "react";
import Nav from "@/components/Nav";
import { LangProvider, useLang } from "@/components/lang";
import { LINKS } from "@/lib/copy";
import { dataHealth, desk, hhmm, type Buku, type DataHealth, type Desk, type Rekaman } from "@/lib/desk";

export default function DeskView() {
  return (
    <LangProvider>
      <div className="p-2 sm:p-3">
        <Nav />
        <Body />
      </div>
    </LangProvider>
  );
}

const panel = "min-w-0 rounded-2xl border border-ink/10 bg-white/70 p-5";
const label = "text-sm uppercase tracking-wide text-ink/50";
const pct = (x: number) => `${x >= 0 ? "+" : ""}${x.toFixed(2)}%`;
const short = (h?: string | null) => (h ? `${h.slice(0, 10)}…${h.slice(-6)}` : "-");

function Body() {
  const { t } = useLang();
  const v = t.desk;
  const [d, setD] = useState<Desk | null>(null);
  const [err, setErr] = useState("");
  useEffect(() => {
    let live = true;
    const load = () => desk().then((x) => live && setD(x), (e: unknown) => live && setErr(String(e)));
    load();
    const id = setInterval(load, 30_000);
    return () => {
      live = false;
      clearInterval(id);
    };
  }, []);

  const kons = d?.buku.find((b) => b.agent === "konsensus");
  const agents = d?.buku.filter((b) => b.agent !== "konsensus") ?? [];
  return (
    <section className="relative overflow-hidden rounded-[30px] bg-gradient-to-b from-lav via-lav to-white px-6 pb-20 pt-32 sm:px-12 sm:pt-40 lg:px-16">
      <div className="mx-auto max-w-4xl text-center">
        <span className="tag text-violet">{v.tag}</span>
        <h1 className="mt-3 font-display text-[clamp(2.2rem,5vw,4.4rem)] font-[300] leading-[0.95] tracking-[-0.03em] text-ink" style={{ fontStretch: "112%" }}>
          {v.title}
        </h1>
        <p className="mx-auto mt-4 max-w-2xl text-ink/60">{v.sub}</p>
      </div>
      <div className="mx-auto mt-10 max-w-6xl space-y-6">
        {err && <p className="text-sm text-ink/70">{v.error}: {err}</p>}
        {!d && !err && <p className="text-center text-ink/50">{v.loading}</p>}
        {d && !d.buku.length && <p className="text-center text-ink/60">{v.empty}</p>}
        {kons && <Consensus b={kons} d={d!} />}
        {agents.length > 0 && (
          <div className="grid gap-6 lg:grid-cols-3">
            {agents.map((b) => (
              <AgentCard key={b.agent} b={b} />
            ))}
          </div>
        )}
        {d && d.rekaman.length > 0 && <Feed rows={d.rekaman} names={Object.fromEntries(d.buku.map((b) => [b.agent, b.nama]))} />}
        <Health />
        {d && <Rules d={d} />}
      </div>
    </section>
  );
}

function Spark({ pts }: { pts: [number, number][] }) {
  if (pts.length < 2) return <div className="h-12" />;
  const ys = pts.map((p) => p[1]);
  const lo = Math.min(...ys), hi = Math.max(...ys), span = hi - lo || 1;
  const d = pts.map((p, i) => `${(i / (pts.length - 1)) * 100},${40 - ((p[1] - lo) / span) * 36 - 2}`).join(" ");
  const up = ys[ys.length - 1] >= ys[0];
  return (
    <svg viewBox="0 0 100 40" preserveAspectRatio="none" className="h-12 w-full" aria-hidden>
      <polyline points={d} fill="none" strokeWidth="1.5" vectorEffect="non-scaling-stroke" className={up ? "stroke-violet" : "stroke-ink/50"} />
    </svg>
  );
}

function Weights({ pos, max }: { pos: Record<string, number>; max: number }) {
  const { t } = useLang();
  const rows = Object.entries(pos).sort((a, b) => Math.abs(b[1]) - Math.abs(a[1]));
  if (!rows.length) return <p className="text-sm text-ink/50">{t.desk.flat}</p>;
  return (
    <div className="space-y-1.5">
      {rows.map(([a, w]) => (
        <div key={a} className="grid grid-cols-[5.5rem,1fr,3.5rem] items-center gap-2 text-xs">
          <span className="font-mono">{a.replace("USDT", "")}</span>
          <div className="relative h-2 rounded-full bg-ink/5">
            <span className="absolute inset-y-0 left-1/2 w-px bg-ink/30" />
            <span className={`absolute inset-y-0 rounded-full ${w >= 0 ? "bg-violet" : "bg-ink/40"}`}
              style={w >= 0 ? { left: "50%", width: `${(Math.abs(w) / max) * 50}%` } : { right: "50%", width: `${(Math.abs(w) / max) * 50}%` }} />
          </div>
          <span className="text-right font-mono">{(w * 100).toFixed(1)}%</span>
        </div>
      ))}
    </div>
  );
}

function Consensus({ b, d }: { b: Buku; d: Desk }) {
  const { t } = useLang();
  const v = t.desk;
  const s = d.siklus_terakhir;
  return (
    <div className={panel}>
      <div className="grid gap-6 lg:grid-cols-[1fr,1.2fr]">
        <div>
          <p className={label}>{v.consensus}</p>
          <p className="mt-2 font-display text-4xl font-[300]">
            {b.ekuitas.toLocaleString("en-US", { maximumFractionDigits: 2 })} <span className="text-base text-ink/50">USDT</span>
          </p>
          <p className={`mt-1 text-sm ${b.hasil_pct >= 0 ? "text-violet" : "text-ink/60"}`}>
            {pct(b.hasil_pct)} · {b.n_trade} {v.trades} · {v.fees} {b.biaya.toFixed(2)}
          </p>
          <Spark pts={b.deret} />
          {s && (
            <p className="mt-2 text-xs text-ink/60">
              {v.lastCycle} {hhmm(s.siklus)} · {s.status}
              {s.tx && (
                <>
                  {" · "}
                  <a className="underline" href={LINKS.tx + s.tx} target="_blank" rel="noreferrer">
                    {v.anchored}
                  </a>
                </>
              )}
              <span className="block font-mono text-[11px] text-ink/45">root {short(s.root)} · {d.komit_24j}/{d.siklus_24j} {v.committed24}</span>
            </p>
          )}
        </div>
        <div>
          <p className={label}>{v.positions}</p>
          <div className="mt-3">
            <Weights pos={b.posisi} max={d.params.maks_per_aset} />
          </div>
        </div>
      </div>
    </div>
  );
}

function AgentCard({ b }: { b: Buku }) {
  const { t } = useLang();
  const v = t.desk;
  const k = b.keputusan_terakhir;
  const changed = (k?.diubah ?? []).map((a) => [a, k!.target[a]] as const);
  return (
    <article className={panel}>
      <p className="font-display text-lg leading-tight">{b.nama}</p>
      <p className={`mt-1 text-sm ${b.hasil_pct >= 0 ? "text-violet" : "text-ink/60"}`}>
        {b.ekuitas.toFixed(2)} USDT · {pct(b.hasil_pct)} · {b.n_trade} {v.trades}
        {b.status_terakhir && b.status_terakhir !== "ok" && <span className="ml-2 rounded-full bg-ink/10 px-2 py-0.5 text-[10px] uppercase">{b.status_terakhir}</span>}
      </p>
      <Spark pts={b.deret} />
      {k && (
        <>
          <p className="mt-2 text-sm text-ink/80">{k.ringkasan}</p>
          <ul className="mt-2 space-y-1 text-xs text-ink/70">
            {changed.length === 0 && <li className="text-ink/50">{v.held}</li>}
            {changed.map(([a, x]) => (
              <li key={a}>
                <span className="font-mono">{a.replace("USDT", "")}</span>{" "}
                <span className={x.w > 0 ? "text-violet" : x.w < 0 ? "text-ink" : "text-ink/50"}>{x.w > 0 ? "long" : x.w < 0 ? "short" : "flat"} {(Math.abs(x.w) * 100).toFixed(0)}%</span>{" "}
                <span className="text-ink/45">({Math.round(x.k * 100)})</span> {x.alasan}
              </li>
            ))}
          </ul>
        </>
      )}
      <div className="mt-3">
        <Weights pos={b.posisi} max={0.25} />
      </div>
    </article>
  );
}

function Feed({ rows, names }: { rows: Rekaman[]; names: Record<string, string> }) {
  const { t } = useLang();
  const v = t.desk;
  return (
    <div className={panel}>
      <p className={label}>{v.feed}</p>
      <ul className="mt-3 divide-y divide-ink/5 text-sm">
        {[...rows].reverse().slice(0, 24).map((r) => (
          <li key={r.hash} className="grid gap-1 py-2 sm:grid-cols-[4rem,11rem,1fr]">
            <span className="font-mono text-xs text-ink/50">{hhmm(r.siklus)}</span>
            <span className="text-xs">
              {names[r.agent] ?? r.agent}
              {r.status && r.status !== "ok" && <span className="ml-1 text-ink/50">· {r.status}</span>}
            </span>
            <span className="min-w-0 text-xs text-ink/70">
              {r.keputusan?.ringkasan ?? r.dasar ?? r.galat ?? ""}
              {(r.isi?.length ?? 0) > 0 && <span className="text-violet"> · {r.isi!.length} {v.fills}</span>}
              <span className="block truncate font-mono text-[10px] text-ink/40">{r.hash}</span>
            </span>
          </li>
        ))}
      </ul>
    </div>
  );
}

// P153 (F1): kesehatan data luas yang dibaca Fabius sendiri (cakupan 24 jam per sumber) - kriteria keluar F1 di Epik 11 §8
function Health() {
  const { t } = useLang();
  const v = t.desk;
  const [h, setH] = useState<DataHealth | null>(null);
  useEffect(() => {
    let live = true;
    const load = () => dataHealth().then((x) => live && setH(x), () => undefined);
    load();
    const id = setInterval(load, 60_000);
    return () => {
      live = false;
      clearInterval(id);
    };
  }, []);
  if (!h || !h.terakhir) return null;
  return (
    <div className={panel}>
      <p className={label}>{v.dataTitle}</p>
      <p className="mt-1 text-xs text-ink/50">{v.dataSub.replace("{n}", String(h.snapshot_24j)).replace("{slow}", String(h.lambat_24j))}</p>
      <div className="mt-3 grid gap-2 sm:grid-cols-3">
        {Object.entries(h.sumber).map(([k, s]) => (
          <div key={k} className="rounded-xl border border-ink/10 p-3 text-xs">
            <p className="font-medium">{k}</p>
            <p className={s.status_terakhir === "ok" ? "text-violet" : "text-ink/60"}>{s.status_terakhir}</p>
            <p className="text-ink/50">
              {v.coverage} {s.cakupan_rata == null ? "-" : `${Math.round(s.cakupan_rata * 100)}%`}
            </p>
          </div>
        ))}
      </div>
      <p className="mt-2 font-mono text-[11px] text-ink/45">
        {v.lastSnapshot} {hhmm(h.terakhir.t)} · registry {short(h.registry_sha)}
      </p>
    </div>
  );
}

function Rules({ d }: { d: Desk }) {
  const { t } = useLang();
  const v = t.desk;
  const p = d.params;
  return (
    <div className={panel}>
      <p className={label}>{v.rulesTitle}</p>
      <p className="mt-2 text-sm text-ink/70">
        {v.rules
          .replace("{fee}", (p.fee * 100).toFixed(2))
          .replace("{per}", String(p.maks_per_aset * 100))
          .replace("{gross}", String(p.maks_gross))
          .replace("{q}", String(p.kuorum))
          .replace("{min}", String(p.ubah_min * 100))
          .replace("{n}", String(p.aset.length))}
      </p>
      <p className="mt-2 font-mono text-[11px] text-ink/50">
        params {short(d.params_sha)}
        {d.anchor && (
          <>
            {" · "}
            <a className="underline" href={LINKS.scan + d.anchor} target="_blank" rel="noreferrer">
              DeskAnchor {short(d.anchor)}
            </a>
          </>
        )}
      </p>
    </div>
  );
}
