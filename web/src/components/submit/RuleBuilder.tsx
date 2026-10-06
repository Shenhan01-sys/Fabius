"use client";

// P167a: pembangun aturan bot (kind=rule). Pohon aturan = JSON gerbang (kosakata dari `GET /bots/schema` -> `rule`); komponen ini hanya
// menyusunnya. Dua gambar mewakili prosesnya (bukan menjelaskannya): jalur keadaan flat / long / short dengan panah masuk-keluar yang
// menyala bila kondisinya ada, dan tangga peringkat dengan k teratas / terbawah. Validasi berwenang = gerbang (`POST /bots/typed-data`).

import { useState } from "react";
import { useLang } from "@/components/lang";
import type { Copy } from "@/lib/copy";
import {
  SLOTS,
  defCond,
  defExpr,
  describe,
  refs,
  renameParam,
  stats,
  toJson,
  workload,
  type Cond,
  type Expr,
  type Num,
  type RuleState,
  type RuleVocab,
  type Slot,
} from "@/lib/rule";

type T = Copy["submit"]["rule"];
type Cx = { vocab: RuleVocab; params: string[]; t: T };

const inp = "rounded-lg border border-ink/15 bg-white px-2 py-1 text-sm text-ink outline-none focus:border-violet";
const num = `${inp} w-20`;
const mono = "font-mono text-xs";
const ghost = "rounded-full border border-ink/15 px-2.5 py-0.5 text-xs text-ink/60 transition-colors hover:border-violet hover:text-violet disabled:cursor-not-allowed disabled:opacity-40";
const panel = "rounded-2xl border border-ink/10 bg-white/60 p-4";
const cap = "text-xs uppercase tracking-wide text-ink/50";

function Sel({ value, options, onChange, label, className = "" }: { value: string; options: { v: string; l: string }[]; onChange: (v: string) => void; label: string; className?: string }) {
  return (
    <select aria-label={label} className={`${inp} ${className}`} value={value} onChange={(e) => onChange(e.target.value)}>
      {options.map((o) => (
        <option key={o.v} value={o.v}>
          {o.l}
        </option>
      ))}
    </select>
  );
}

const refName = (v: Num | undefined): string | null => (v !== null && typeof v === "object" ? v.p : null);

/** Angka atau rujukan ke parameter bernama (jendela, lag, jendela volatilitas). */
function NumRef({ v, set, params, label, dflt, min, max }: { v: Num | undefined; set: (x: Num) => void; params: string[]; label: string; dflt: number; min?: number; max?: number }) {
  const ref = refName(v);
  return (
    <span className="inline-flex items-center gap-1">
      {params.length > 0 && (
        <select aria-label={`${label} (source)`} className={`${inp} w-16`} value={ref ?? "#"} onChange={(e) => set(e.target.value === "#" ? dflt : { p: e.target.value })}>
          <option value="#">#</option>
          {params.map((p) => (
            <option key={p} value={p}>
              {p}
            </option>
          ))}
        </select>
      )}
      {ref === null && <input aria-label={label} className={num} type="number" min={min} max={max} value={String(v ?? "")} onChange={(e) => set(e.target.value)} />}
    </span>
  );
}

// ---------------------------------------------------------------- ekspresi

type EK = "f" | "c" | "p" | "op" | "fn";
const kindOfExpr = (e: Expr): EK => ("f" in e ? "f" : "c" in e ? "c" : "p" in e ? "p" : "op" in e ? "op" : "fn");

function freshExpr(k: EK, cx: Cx): Expr {
  if (k === "c") return { c: 0 };
  if (k === "p") return { p: cx.params[0] ?? "" };
  if (k === "op") return { op: "+", a: defExpr(), b: { c: 1 } };
  if (k === "fn") return { fn: "abs", args: [defExpr()] };
  return defExpr();
}

function ExprEd({ e, set, cx }: { e: Expr; set: (x: Expr) => void; cx: Cx }) {
  const { t, vocab, params } = cx;
  const k = kindOfExpr(e);
  const kinds = (["f", "c", "p", "op", "fn"] as EK[]).map((x) => ({ v: x, l: t.expr.kinds[x] }));
  const head = <Sel label={t.expr.kind} value={k} options={kinds} onChange={(v) => set(freshExpr(v as EK, cx))} className="w-28" />;
  if (k === "c") {
    return (
      <span className="inline-flex items-center gap-1.5">
        {head}
        <input aria-label={t.expr.kinds.c} className={num} type="number" step="any" value={String((e as { c: number | string }).c)} onChange={(ev) => set({ c: ev.target.value })} />
      </span>
    );
  }
  if (k === "p") {
    const cur = (e as { p: string }).p;
    return (
      <span className="inline-flex items-center gap-1.5">
        {head}
        {params.length ? (
          <Sel label={t.expr.kinds.p} value={cur} options={[...(params.includes(cur) ? [] : [{ v: cur, l: cur || "?" }]), ...params.map((p) => ({ v: p, l: p }))]} onChange={(v) => set({ p: v })} className="w-28" />
        ) : (
          <span className="text-xs text-ink/50">{t.expr.noParams}</span>
        )}
      </span>
    );
  }
  if (k === "f") {
    const f = e as { f: string; n?: Num; lag?: Num };
    const windowed = vocab.window.includes(f.f);
    const feat = t.features as Record<string, string>;
    const opts = [
      ...vocab.price.map((x) => ({ v: x, l: `${x} · ${feat[x] ?? ""}` })),
      ...vocab.window.map((x) => ({ v: x, l: `${x}(n) · ${feat[x] ?? ""}` })),
    ];
    return (
      <span className="inline-flex flex-wrap items-center gap-1.5">
        {head}
        <Sel
          label={t.expr.kinds.f}
          value={f.f}
          options={opts}
          onChange={(v) => {
            const w = vocab.window.includes(v);
            const next: { f: string; n?: Num; lag?: Num } = { f: v };
            if (w) next.n = f.n ?? 20;
            if (f.lag !== undefined) next.lag = f.lag;
            set(next);
          }}
          className="w-52 max-w-full"
        />
        {windowed && <NumRef v={f.n} set={(x) => set({ ...f, n: x })} params={params} label={t.expr.n} dflt={20} min={vocab.limits.jendela_min} max={vocab.limits.jendela_maks} />}
        {f.lag !== undefined ? (
          <span className="inline-flex items-center gap-1 text-xs text-ink/60">
            <NumRef v={f.lag} set={(x) => set({ ...f, lag: x })} params={params} label={t.expr.lag} dflt={1} min={0} max={vocab.limits.lag_maks} />
            {t.expr.lag}
            <button type="button" aria-label={`${t.removeSlot} ${t.expr.lag}`} className="text-ink/40 hover:text-violet" onClick={() => set({ f: f.f, ...(f.n !== undefined ? { n: f.n } : {}) })}>
              ×
            </button>
          </span>
        ) : (
          <button type="button" className={ghost} onClick={() => set({ ...f, lag: 1 })}>
            {t.expr.addLag}
          </button>
        )}
      </span>
    );
  }
  if (k === "op") {
    const o = e as { op: string; a: Expr; b: Expr };
    return (
      <div className="space-y-1.5">
        {head}
        <div className="space-y-1.5 border-l-2 border-violet/25 pl-3">
          <ExprEd e={o.a} set={(a) => set({ ...o, a })} cx={cx} />
          <Sel label="op" value={o.op} options={vocab.ops.map((x) => ({ v: x, l: x }))} onChange={(v) => set({ ...o, op: v })} className="w-16 font-mono" />
          <ExprEd e={o.b} set={(b) => set({ ...o, b })} cx={cx} />
        </div>
      </div>
    );
  }
  const fn = e as { fn: string; args: Expr[] };
  const [lo, hi] = vocab.fns[fn.fn] ?? [1, 1];
  return (
    <div className="space-y-1.5">
      <span className="inline-flex items-center gap-1.5">
        {head}
        <Sel
          label="fn"
          value={fn.fn}
          options={Object.keys(vocab.fns).map((x) => ({ v: x, l: x }))}
          onChange={(v) => {
            const [l2, h2] = vocab.fns[v] ?? [1, 1];
            const args = fn.args.slice(0, h2);
            while (args.length < l2) args.push({ c: 0 });
            set({ fn: v, args });
          }}
          className="w-24 font-mono"
        />
      </span>
      <ul className="space-y-1.5 border-l-2 border-violet/25 pl-3">
        {fn.args.map((a, i) => (
          <li key={i} className="flex items-start gap-1.5">
            <div className="flex-1">
              <ExprEd e={a} set={(x) => set({ ...fn, args: fn.args.map((y, j) => (j === i ? x : y)) })} cx={cx} />
            </div>
            {fn.args.length > lo && (
              <button type="button" aria-label={t.removeSlot} className="px-1 text-ink/40 hover:text-violet" onClick={() => set({ ...fn, args: fn.args.filter((_, j) => j !== i) })}>
                ×
              </button>
            )}
          </li>
        ))}
        {fn.args.length < hi && (
          <li>
            <button type="button" className={ghost} onClick={() => set({ ...fn, args: [...fn.args, { c: 0 }] })}>
              {t.cond.add}
            </button>
          </li>
        )}
      </ul>
    </div>
  );
}

// ---------------------------------------------------------------- kondisi

type CK = "cmp" | "and" | "or" | "not";
const kindOfCond = (c: Cond): CK => ("cmp" in c ? "cmp" : "and" in c ? "and" : "or" in c ? "or" : "not");
const kids = (c: Cond): Cond[] => ("and" in c ? c.and : "or" in c ? c.or : "not" in c ? [c.not] : [c]);

function CondEd({ c, set, cx }: { c: Cond; set: (x: Cond) => void; cx: Cx }) {
  const { t, vocab } = cx;
  const k = kindOfCond(c);
  const change = (to: string) => {
    const [first] = kids(c);
    if (to === "cmp") return set(k === "cmp" ? c : kindOfCond(first) === "cmp" ? first : defCond());
    if (to === "not") return set({ not: k === "cmp" ? c : first });
    const list = k === "and" || k === "or" ? kids(c) : [c, defCond()];
    set(to === "and" ? { and: list } : { or: list });
  };
  const head = <Sel label={t.cond.kind} value={k} options={(["cmp", "and", "or", "not"] as CK[]).map((x) => ({ v: x, l: t.cond.kinds[x] }))} onChange={change} className="w-28" />;
  if (k === "cmp") {
    const o = c as { cmp: string; a: Expr; b: Expr };
    return (
      <div className="space-y-1.5">
        {head}
        <div className="grid gap-1.5 sm:grid-cols-[1fr_auto_1fr] sm:items-start">
          <ExprEd e={o.a} set={(a) => set({ ...o, a })} cx={cx} />
          <Sel label="cmp" value={o.cmp} options={vocab.cmps.map((x) => ({ v: x, l: x }))} onChange={(v) => set({ ...o, cmp: v })} className="w-16 font-mono" />
          <ExprEd e={o.b} set={(b) => set({ ...o, b })} cx={cx} />
        </div>
      </div>
    );
  }
  if (k === "not") {
    const o = c as { not: Cond };
    return (
      <div className="space-y-1.5">
        {head}
        <div className="border-l-2 border-violet/30 pl-3">
          <CondEd c={o.not} set={(x) => set({ not: x })} cx={cx} />
        </div>
      </div>
    );
  }
  const list = kids(c);
  const wrap = (xs: Cond[]): Cond => (k === "and" ? { and: xs } : { or: xs });
  return (
    <div className="space-y-1.5">
      {head}
      <ul className="space-y-2 border-l-2 border-violet/30 pl-3">
        {list.map((x, i) => (
          <li key={i} className="flex items-start gap-1.5">
            <div className="min-w-0 flex-1 rounded-xl border border-ink/10 bg-white/70 p-2">
              <CondEd c={x} set={(y) => set(wrap(list.map((z, j) => (j === i ? y : z))))} cx={cx} />
            </div>
            <button type="button" aria-label={t.removeSlot} disabled={list.length <= 2} className="px-1 text-ink/40 hover:text-violet disabled:opacity-30" onClick={() => set(wrap(list.filter((_, j) => j !== i)))}>
              ×
            </button>
          </li>
        ))}
        {list.length < 4 && (
          <li>
            <button type="button" className={ghost} onClick={() => set(wrap([...list, defCond()]))}>
              {t.cond.add}
            </button>
          </li>
        )}
      </ul>
    </div>
  );
}

// ---------------------------------------------------------------- gambar: jalur keadaan dan tangga peringkat

function StateStrip({ r, t }: { r: RuleState; t: T }) {
  const on = (s: Slot) => r[s] !== undefined;
  const arrows = [
    { id: "el", x1: 368, x2: 522, y: 52, active: on("masuk_long"), label: on("masuk_long") ? t.strip.enter : t.strip.off, dashed: false },
    { id: "xl", x1: 522, x2: 368, y: 88, active: on("masuk_long"), label: on("masuk_long") ? (on("keluar_long") ? t.strip.exit : t.strip.auto) : t.strip.off, dashed: !on("keluar_long") },
    { id: "es", x1: 272, x2: 118, y: 52, active: on("masuk_short"), label: on("masuk_short") ? t.strip.enter : t.strip.off, dashed: false },
    { id: "xs", x1: 118, x2: 272, y: 88, active: on("masuk_short"), label: on("masuk_short") ? (on("keluar_short") ? t.strip.exit : t.strip.auto) : t.strip.off, dashed: !on("keluar_short") },
  ];
  const node = (x: number, name: string, hot: boolean) => (
    <g key={name}>
      <rect x={x - 45} y={50} width={90} height={40} rx={20} className={hot ? "fill-violet" : "fill-ink/10"} />
      <text x={x} y={75} textAnchor="middle" className={`text-[16px] ${hot ? "fill-white" : "fill-ink/60"}`}>
        {name}
      </text>
    </g>
  );
  return (
    <svg viewBox="0 20 640 100" role="img" aria-label={describe(r, "en").join(" ")} className="w-full">
      <style>{`.rb-flow{stroke-dasharray:6 6;animation:rb-flow 1.2s linear infinite}@keyframes rb-flow{to{stroke-dashoffset:-12}}@media (prefers-reduced-motion:reduce){.rb-flow{animation:none}}`}</style>
      <defs>
        {(["on", "off"] as const).map((k) => (
          <marker key={k} id={`rb-head-${k}`} markerUnits="userSpaceOnUse" markerWidth="12" markerHeight="12" refX="10" refY="6" orient="auto">
            <path d="M0 1 L11 6 L0 11 z" className={k === "on" ? "fill-violet" : "fill-ink/25"} />
          </marker>
        ))}
      </defs>
      {arrows.map((a) => (
        <g key={a.id} className={a.active ? "text-violet" : "text-ink/25"}>
          <line x1={a.x1} y1={a.y} x2={a.x2} y2={a.y} stroke="currentColor" strokeWidth={2} markerEnd={`url(#rb-head-${a.active ? "on" : "off"})`} className={a.active && !a.dashed ? "rb-flow" : undefined} strokeDasharray={a.active && !a.dashed ? undefined : "3 5"} />
          <text x={(a.x1 + a.x2) / 2} y={a.y < 70 ? a.y - 8 : a.y + 20} textAnchor="middle" className={`${a.active ? "fill-ink/60" : "fill-ink/30"} text-[13px]`}>
            {a.label}
          </text>
        </g>
      ))}
      {node(70, t.strip.short, on("masuk_short"))}
      {node(320, t.strip.flat, true)}
      {node(570, t.strip.long, on("masuk_long"))}
    </svg>
  );
}

function Ladder({ r, t }: { r: RuleState; t: T }) {
  const kl = Math.max(0, Math.min(8, Number(r.long_teratas) || 0));
  const ks = Math.max(0, Math.min(8, Number(r.short_terbawah) || 0));
  const rows = 10;
  return (
    <svg viewBox="0 0 340 160" role="img" aria-label={describe(r, "en").join(" ")} className="w-full max-w-xs">
      {Array.from({ length: rows }, (_, i) => {
        const long = i < kl;
        const short = i >= rows - ks;
        const w = 215 - i * 15;
        return (
          <g key={i}>
            <rect x={32} y={6 + i * 15} width={w} height={11} rx={5.5} className={long ? "fill-violet" : short ? "fill-ink" : "fill-ink/12"} />
            <text x={26} y={15 + i * 15} textAnchor="end" className="fill-ink/40 font-mono text-[9px]">
              {i + 1}
            </text>
          </g>
        );
      })}
      <text x={338} y={19} textAnchor="end" className="fill-violet text-[11px]">
        {t.strip.long}
      </text>
      <text x={338} y={152} textAnchor="end" className="fill-ink text-[11px]">
        {t.strip.short}
      </text>
    </svg>
  );
}

// ---------------------------------------------------------------- pembangun

export default function RuleBuilder({ vocab, state, setState }: { vocab: RuleVocab; state: RuleState; setState: (s: RuleState) => void }) {
  const { t: all, lang } = useLang();
  const t = all.submit.rule;
  const [json, setJson] = useState(false);
  const names = state.params.map((p) => p.name);
  const cx: Cx = { vocab, params: names, t };
  const patch = (p: Partial<RuleState>) => setState({ ...state, ...p });
  const used = refs(state);
  const undeclared = [...used].filter((n) => !names.includes(n));
  const st = stats(state);
  const work = workload(state);
  const lim = vocab.limits;
  const cap_ = lim.gross_maks[state.mode] ?? 1;

  return (
    <div className="space-y-5">
      <div>
        <p className={cap}>{t.modeTitle}</p>
        <div className="mt-2 grid gap-2 sm:grid-cols-2" role="radiogroup" aria-label={t.modeTitle}>
          {(["per_aset", "peringkat"] as const).map((m) => (
            <button
              key={m}
              type="button"
              role="radio"
              aria-checked={state.mode === m}
              onClick={() => patch({ mode: m })}
              className={`rounded-xl border p-3 text-left transition-colors ${state.mode === m ? "border-violet bg-violet/10" : "border-ink/15 hover:border-violet/60"}`}
            >
              <span className="block text-sm font-medium text-ink">{t.modes[m].name}</span>
              <span className="mt-0.5 block text-xs text-ink/60">{t.modes[m].text}</span>
            </button>
          ))}
        </div>
      </div>

      <div className={panel}>
        <p className={cap}>{t.paramsTitle}</p>
        <p className="mt-1 text-xs text-ink/60">{t.paramsHelp}</p>
        <ul className="mt-3 space-y-2">
          {state.params.map((p, i) => {
            const dup = names.filter((n) => n === p.name).length > 1;
            return (
              <li key={i} className="flex flex-wrap items-center gap-2">
                <input aria-label={t.paramName} className={`${inp} w-28 font-mono`} value={p.name} maxLength={16} placeholder={t.paramName} onChange={(e) => setState(renameParam(state, p.name, e.target.value))} />
                <span className="text-ink/40">=</span>
                <input aria-label={t.paramValue} className={num} type="number" step="any" value={String(p.value)} onChange={(e) => patch({ params: state.params.map((q, j) => (j === i ? { ...q, value: e.target.value } : q)) })} />
                <span className={`text-xs ${dup ? "text-ink" : used.has(p.name) ? "text-violet" : "text-ink/45"}`}>{dup ? t.dup : used.has(p.name) ? t.used : t.unused}</span>
                <button type="button" aria-label={t.removeSlot} className="text-ink/40 hover:text-violet" onClick={() => patch({ params: state.params.filter((_, j) => j !== i) })}>
                  ×
                </button>
              </li>
            );
          })}
        </ul>
        <button type="button" className={`${ghost} mt-3`} disabled={state.params.length >= lim.max_parameter} onClick={() => patch({ params: [...state.params, { name: `p${state.params.length + 1}`, value: 20 }] })}>
          + {t.addParam}
        </button>
        {undeclared.length > 0 && <p className="mt-2 text-xs text-ink">{t.undeclared.replace("{n}", undeclared.join(", "))}</p>}
      </div>

      {state.mode === "per_aset" ? (
        <div className="space-y-3">
          <div className="rounded-2xl border border-ink/10 bg-lav/40 p-3">
            <StateStrip r={state} t={t} />
          </div>
          {SLOTS.map((s) => {
            const long = s.endsWith("long");
            const entry = s.startsWith("masuk");
            const needsEntry = !entry && state[long ? "masuk_long" : "masuk_short"] === undefined;
            const cur = state[s];
            const entries = (["masuk_long", "masuk_short"] as Slot[]).filter((x) => state[x] !== undefined);
            const canRemove = !entry || entries.length > 1;                     // minimal satu kondisi masuk; menghapus masuk ikut menghapus keluarnya
            const setSlot = (v: Cond | undefined) => setState({ ...state, [s]: v } as RuleState);
            const removeSlot = () => setState({ ...state, [s]: undefined, ...(entry ? { [long ? "keluar_long" : "keluar_short"]: undefined } : {}) } as RuleState);
            return (
              <div key={s} className={panel}>
                <div className="flex items-center justify-between gap-2">
                  <p className="text-sm font-medium text-ink">{t.slots[s]}</p>
                  {cur !== undefined ? (
                    canRemove && (
                      <button type="button" className={ghost} onClick={removeSlot}>
                        {t.removeSlot}
                      </button>
                    )
                  ) : (
                    <button type="button" className={ghost} disabled={needsEntry} onClick={() => setSlot(defCond())}>
                      + {t.addSlot}
                    </button>
                  )}
                </div>
                {cur !== undefined ? (
                  <div className="mt-3">
                    <CondEd c={cur} set={setSlot} cx={cx} />
                  </div>
                ) : (
                  !entry && !needsEntry && <p className="mt-1 text-xs text-ink/50">{t.slotAuto}</p>
                )}
              </div>
            );
          })}
        </div>
      ) : (
        <div className={`${panel} grid gap-4 md:grid-cols-[1fr_auto]`}>
          <div className="space-y-3">
            <div>
              <p className={cap}>{t.scoreTitle}</p>
              <div className="mt-2">
                <ExprEd e={state.skor} set={(skor) => patch({ skor })} cx={cx} />
              </div>
            </div>
            <div className="flex flex-wrap items-center gap-x-4 gap-y-2 text-sm text-ink/80">
              <label className="inline-flex items-center gap-1.5">
                {t.topK}
                <input className={num} type="number" min={0} max={lim.k_maks} value={String(state.long_teratas)} onChange={(e) => patch({ long_teratas: e.target.value })} />
              </label>
              <label className="inline-flex items-center gap-1.5">
                {t.bottomK}
                <input className={num} type="number" min={0} max={lim.k_maks} value={String(state.short_terbawah)} onChange={(e) => patch({ short_terbawah: e.target.value })} />
              </label>
              <label className="inline-flex items-center gap-1.5">
                {t.minAssets}
                <input className={num} type="number" min={2} value={String(state.min_aset)} onChange={(e) => patch({ min_aset: e.target.value })} />
                {t.assetsRanked}
              </label>
            </div>
            <label className="grid gap-1 text-sm text-ink/80">
              {t.rotation}
              <Sel label={t.rotation} value={state.rotasi} options={vocab.rotasi.map((x) => ({ v: x, l: t.rotations[x as keyof T["rotations"]] ?? x }))} onChange={(v) => patch({ rotasi: v })} className="w-full max-w-md" />
            </label>
          </div>
          <Ladder r={state} t={t} />
        </div>
      )}

      <div className={panel}>
        <p className={cap}>{t.weightsTitle}</p>
        <div className="mt-2 flex flex-wrap items-center gap-x-4 gap-y-2 text-sm text-ink/80">
          <Sel label={t.weightsTitle} value={state.bobot.skema} options={vocab.skema.map((x) => ({ v: x, l: t.schemes[x as keyof T["schemes"]] ?? x }))} onChange={(v) => patch({ bobot: { ...state.bobot, skema: v, ...(v === "inv_vol" && state.bobot.n === undefined ? { n: 30 } : {}) } })} className="w-52" />
          <label className="inline-flex items-center gap-1.5">
            {t.gross}
            <input className={num} type="number" step="any" min={0} max={cap_} value={String(state.bobot.gross_maks)} onChange={(e) => patch({ bobot: { ...state.bobot, gross_maks: e.target.value } })} />
            <span className="text-xs text-ink/50">{t.grossHelp.replace("{m}", String(cap_))}</span>
          </label>
          {state.bobot.skema === "inv_vol" && (
            <label className="inline-flex items-center gap-1.5">
              {t.volWindow}
              <NumRef v={state.bobot.n} set={(n) => patch({ bobot: { ...state.bobot, n } })} params={names} label={t.volWindow} dflt={30} min={lim.jendela_min} max={lim.jendela_maks} />
            </label>
          )}
        </div>
        <p className="mt-2 text-xs text-ink/50">{t.ours}</p>
      </div>

      <div className={`${panel} bg-lav/30`}>
        <p className={cap}>{t.readout}</p>
        <ul className="mt-2 list-disc space-y-1 pl-5 text-sm text-ink/80">
          {describe(state, lang).map((s, i) => (
            <li key={i}>{s}</li>
          ))}
        </ul>
        <p className={`mt-3 ${mono} ${st.nodes > lim.max_simpul || st.depth > lim.max_kedalaman || work > lim.anggaran_jendela ? "text-ink" : "text-ink/50"}`}>
          {t.counters.replace("{n}", String(st.nodes)).replace("{m}", String(lim.max_simpul)).replace("{d}", String(st.depth)).replace("{x}", String(lim.max_kedalaman)).replace("{w}", String(work)).replace("{b}", String(lim.anggaran_jendela))}
        </p>
        <button type="button" className={`${ghost} mt-3`} aria-expanded={json} onClick={() => setJson(!json)}>
          {t.showJson}
        </button>
        {json && <pre className="mt-2 max-h-72 overflow-auto rounded-xl bg-ink/5 p-3 font-mono text-[11px] leading-snug text-ink/80">{JSON.stringify(toJson(state), null, 2)}</pre>}
      </div>
    </div>
  );
}
