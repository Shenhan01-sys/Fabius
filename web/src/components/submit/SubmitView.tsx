"use client";

// /submit (P161 B1e, F-D120): pengajuan bot penerbit + papan pipa. Formulir DIBANGKITKAN dari skema gerbang (`GET /bots/schema`, sumbernya
// engine/submission.py) supaya web tidak pernah menyimpang dari validator; gerbang menghitung pesan EIP-712 (`POST /bots/typed-data`), dompet
// Privy menandatangani, lalu `POST /bots/submit`. Papan = setiap kiriman di lintasan 4 stasiun (diterima -> gerbang -> bayangan maju n/60 -> slot).

import { useEffect, useMemo, useState } from "react";
import { useSignTypedData } from "@privy-io/react-auth";
import { getAddress } from "viem";
import { useAkses } from "@/components/akses";
import Nav from "@/components/Nav";
import { LangProvider, useLang } from "@/components/lang";
import { isField, kiriman, schemaInfo, submit, typedData, type Field, type Kiriman, type Node, type SchemaInfo } from "@/lib/pengajuan";
import { meta as kodeMeta } from "@/lib/kode";
import { startRule, toJson, type RuleState } from "@/lib/rule";
import OwnerReview from "./OwnerReview";
import { CodeEditor, FeedPanel } from "./KindPanels";
import RuleBuilder from "./RuleBuilder";

const panel = "min-w-0 rounded-2xl border border-ink/10 bg-white/70 p-5";
const label = "text-sm uppercase tracking-wide text-ink/50";
const btn = "rounded-full bg-ink px-5 py-2.5 text-sm text-white transition-colors hover:bg-violet disabled:cursor-not-allowed disabled:opacity-40";
const inp = "w-full rounded-xl border border-ink/15 bg-white px-3 py-2 text-sm text-ink outline-none focus:border-violet";
const short = (a: string) => `${a.slice(0, 6)}…${a.slice(-4)}`;
const day = (s: number) => new Date(s * 1000).toISOString().slice(0, 16).replace("T", " ") + "Z";
// field yang diisi otomatis atau punya kontrol sendiri
const SKIP = new Set(["v", "kind", "spec.template", "spec.param_nama", "spec.param", "spec.konstanta", "spec.rule", "spec.kode", "spec.horizon", "spec.universe",
  "identity.issuer_wallet", "identity.payout_wallet", "evidence.komit_maju"]);
const KINDS = ["rule", "code", "feed"] as const;
type Jenis = (typeof KINDS)[number];

type V = Record<string, unknown>;

export default function SubmitView() {
  return (
    <LangProvider>
      <div className="p-2 sm:p-3">
        <Nav />
        <Body />
      </div>
    </LangProvider>
  );
}

function Body() {
  const { t } = useLang();
  const v = t.submit;
  return (
    <section className="relative overflow-hidden rounded-[30px] bg-gradient-to-b from-lav via-lav to-white px-6 pb-20 pt-32 sm:px-12 sm:pt-40 lg:px-16">
      <div className="mx-auto max-w-4xl text-center">
        <span className="tag text-violet">{v.tag}</span>
        <h1 className="mt-3 font-display text-[clamp(2.2rem,5vw,4.4rem)] font-[300] leading-[0.95] tracking-[-0.03em] text-ink" style={{ fontStretch: "112%" }}>
          {v.title}
        </h1>
        <p className="mx-auto mt-4 max-w-2xl text-ink/60">{v.sub}</p>
      </div>
      <div className="mx-auto mt-10 max-w-5xl space-y-6">
        <Board />
        <Form />
      </div>
    </section>
  );
}

// ---------------------------------------------------------------- papan pipa

function tahap(k: Kiriman): { i: number; gagal: boolean } {
  if (k.status === "in slot") return { i: 3, gagal: false };
  if (k.status === "shadow") return { i: 2, gagal: false };
  const lolos = k.review?.vonis === "LOLOS_SHADOW" || k.review?.vonis === "MAJU_FEED";      // MAJU_FEED: gerbang replay N/A, bayangan maju
  if (k.status === "rejected" || (k.status === "reviewed" && !lolos)) return { i: 1, gagal: true };
  if (k.status === "reviewed") return { i: 2, gagal: false };
  return { i: 0, gagal: false };
}

function Board() {
  const { t } = useLang();
  const v = t.submit;
  const [rows, setRows] = useState<Kiriman[] | null>(null);
  const [err, setErr] = useState("");
  useEffect(() => {
    let live = true;
    const load = () => kiriman().then((x) => live && (setRows(x), setErr("")), (e: unknown) => live && setErr(String(e)));
    load();
    const id = setInterval(load, 60_000);
    return () => {
      live = false;
      clearInterval(id);
    };
  }, []);
  const stations = [v.stages.received, v.stages.reviewed, v.stages.shadow, v.stages.slot];
  return (
    <div className={panel}>
      <p className={label}>{v.board}</p>
      <p className="mt-1 text-sm text-ink/60">{v.boardSub}</p>
      <div className="mt-4 hidden grid-cols-[10rem_1fr] gap-3 text-[10px] uppercase tracking-wide text-ink/45 sm:grid">
        <span />
        <div className="grid grid-cols-4">
          {stations.map((s) => (
            <span key={s} className="text-center">
              {s}
            </span>
          ))}
        </div>
      </div>
      {err && !rows && <p className="mt-3 text-sm text-ink/60">{err}</p>}
      {rows && rows.length === 0 && <p className="mt-3 text-sm text-ink/50">{v.empty}</p>}
      <ul className="mt-2 divide-y divide-ink/5">
        {(rows ?? []).map((k) => {
          const st = tahap(k);
          return (
            <li key={k.submission_sha} className="grid gap-2 py-3 sm:grid-cols-[10rem_1fr] sm:items-center sm:gap-3">
              <div className="min-w-0">
                <p className="truncate font-mono text-sm text-ink">{k.bot_id}</p>
                <p className="font-mono text-[10px] text-ink/45">
                  {short(k.issuer)} · {day(k.t)}
                </p>
              </div>
              <div>
                <div className="relative grid grid-cols-4 items-center" aria-label={`${k.bot_id}: ${v.status[k.status] ?? k.status}`}>
                  <span className="absolute left-[12.5%] right-[12.5%] top-1/2 h-px -translate-y-1/2 bg-ink/10" aria-hidden />
                  <span
                    className={`absolute left-[12.5%] top-1/2 h-0.5 -translate-y-1/2 ${st.gagal ? "bg-ink/40" : "bg-violet"}`}
                    style={{ width: `${(st.i / 3) * 75}%` }}
                    aria-hidden
                  />
                  {stations.map((s, i) => (
                    <span key={s} className="relative z-10 flex justify-center">
                      <span
                        className={`grid h-5 w-5 place-items-center rounded-full border-2 text-[9px] ${
                          i < st.i || (i === st.i && !st.gagal) ? "border-violet bg-violet text-white" : i === st.i && st.gagal ? "border-ink bg-ink text-white" : "border-ink/15 bg-white"
                        }`}
                      >
                        {i === st.i && st.gagal ? "✕" : i <= st.i ? "✓" : ""}
                      </span>
                    </span>
                  ))}
                </div>
                <p className="mt-1.5 text-xs text-ink/60">
                  {v.status[k.status] ?? k.status}
                  {k.review && <span className="font-mono text-ink/45"> · {k.review.vonis}</span>}
                  {k.note && <span className="text-ink/45"> · {k.note}</span>}
                </p>
                <OwnerReview r={k.owner_review} />
                {k.shadow && !k.shadow.slot && (
                  <div className="mt-1.5 flex items-center gap-2">
                    <div className="h-1.5 flex-1 rounded-full bg-ink/10">
                      <div className="h-full rounded-full bg-violet" style={{ width: `${Math.min(100, (k.shadow.days / k.shadow.of) * 100)}%` }} />
                    </div>
                    <span className="font-mono text-[10px] text-ink/50">
                      {v.days.replace("{n}", String(k.shadow.days)).replace("{m}", String(k.shadow.of))}
                      {k.shadow.label ? ` · ${k.shadow.label}` : ""}
                    </span>
                  </div>
                )}
              </div>
            </li>
          );
        })}
      </ul>
    </div>
  );
}

// ---------------------------------------------------------------- formulir dari skema

function nilaiField(f: Field, raw: unknown): unknown {
  if (f.const !== undefined) return f.const;
  if (f.t === "bool") return !!raw;
  if (raw === undefined || raw === null || raw === "") return undefined;
  if (f.t === "int") return Number.isFinite(parseInt(String(raw), 10)) ? parseInt(String(raw), 10) : raw;
  if (f.t === "number") return Number.isFinite(parseFloat(String(raw))) ? parseFloat(String(raw)) : raw;
  return typeof raw === "string" ? raw.trim() : raw;
}

function bangun(node: Node, path: string, v: V): unknown {
  if (isField(node)) {
    if (node.t === "list") {
      const arr = (v[path] as unknown[]) ?? [];
      const it = node.item;
      const out = arr
        .map((x) => (isField(it) ? nilaiField(it, x) : Object.fromEntries(Object.entries(it as Record<string, Field>).map(([k, f]) => [k, nilaiField(f, (x as V)[k])]).filter(([, y]) => y !== undefined))))
        .filter((x) => x !== undefined && x !== "" && !(typeof x === "object" && Object.keys(x as object).length === 0));
      return out.length || !node.optional ? out : undefined;
    }
    const x = nilaiField(node, v[path]);
    return x === undefined && node.optional ? undefined : x;
  }
  const o: V = {};
  for (const [k, n] of Object.entries(node)) {
    const x = bangun(n, path ? `${path}.${k}` : k, v);
    if (x !== undefined) o[k] = x;
  }
  return o;
}

function Form() {
  const { t } = useLang();
  const v = t.submit;
  const ak = useAkses();
  const { signTypedData } = useSignTypedData();
  const [info, setInfo] = useState<SchemaInfo | null>(null);
  const [nilai, setNilai] = useState<V>({ "evidence.percobaan": "1", "evidence.sumber_data": [""], "theory.referensi": [{}] });
  const [uni, setUni] = useState<string[]>([]);
  const [rule, setRule] = useState<RuleState>(startRule);
  const [jenis, setJenis] = useState<Jenis>("rule");
  const [kode, setKode] = useState<string | null>(null);
  const [fase, setFase] = useState<"" | "cek" | "tanda" | "kirim">("");
  const [masalah, setMasalah] = useState<string[]>([]);
  const [id, setId] = useState("");
  useEffect(() => {
    schemaInfo().then(setInfo, (e: unknown) => setMasalah([String(e)]));
  }, []);
  const set = (p: string, x: unknown) => setNilai((o) => ({ ...o, [p]: x }));
  const wallet = useMemo(() => {
    try {
      return ak.wallet ? getAddress(ak.wallet) : null;
    } catch {
      return null;
    }
  }, [ak.wallet]);

  if (!info) return <div className={panel}>{masalah.length ? <p className="text-sm text-ink/60">{masalah[0]}</p> : <p className="text-sm text-ink/50">…</p>}</div>;

  const tulis = (p: string, f: Field) => v.labels[p] || f.label;
  const teksKode = kode ?? info.code.template;
  const sub = async () => {
    const base = bangun(info.schema as Node, "", nilai) as V;
    const spec = base.spec as V;
    if (jenis === "rule") spec.rule = toJson(rule);
    if (jenis === "code") {
      const m = await kodeMeta(teksKode);
      if (!m) throw new Error(t.submit.code.paramsUnread);
      spec.kode = m;
    }
    spec.horizon = "1d";
    spec.universe = uni;
    (base.identity as V).issuer_wallet = wallet;
    (base.identity as V).payout_wallet = wallet;
    base.kind = jenis;
    return base;
  };

  async function kirim() {
    setMasalah([]);
    setId("");
    try {
      setFase("cek");
      const s = await sub();
      const nonce = Math.floor(Math.random() * 1_000_000_000);
      const deadline = Math.floor(Date.now() / 1000) + 1800;
      const td = await typedData(s, nonce, deadline);
      if (!td.ok) return setMasalah((td.body.problems as string[]) ?? [String(td.body.error)]);
      setFase("tanda");
      const { signature } = await signTypedData(td.body as unknown as Parameters<typeof signTypedData>[0], { address: wallet ?? undefined });
      setFase("kirim");
      const r = await submit(s, signature, nonce, deadline, jenis === "code" ? teksKode : undefined);
      if (!r.ok) return setMasalah((r.body.problems as string[]) ?? [String(r.body.error)]);
      setId(String(r.body.id));
    } catch (e) {
      setMasalah([e instanceof Error ? e.message : String(e)]);
    } finally {
      setFase("");
    }
  }

  const input = (p: string, f: Field) => {
    const val = nilai[p];
    if (f.t === "text") return <textarea className={`${inp} min-h-24`} value={String(val ?? "")} maxLength={f.max} onChange={(e) => set(p, e.target.value)} />;
    if (f.t === "enum")
      return (
        <select className={inp} value={String(val ?? "")} onChange={(e) => set(p, e.target.value)}>
          <option value="">—</option>
          {(f.values ?? []).map((x) => (
            <option key={x}>{x}</option>
          ))}
        </select>
      );
    if (f.t === "bool") return <input type="checkbox" className="h-4 w-4 accent-violet" checked={!!val} onChange={(e) => set(p, e.target.checked)} />;
    return (
      <input
        className={inp}
        type={f.t === "date" ? "date" : f.t === "int" || f.t === "number" ? "number" : "text"}
        value={String(val ?? "")}
        min={f.t === "int" || f.t === "number" ? f.min : undefined}
        max={f.t === "int" || f.t === "number" ? f.max : undefined}
        onChange={(e) => set(p, e.target.value)}
      />
    );
  };

  const baris = (p: string, f: Field) => {
    if (SKIP.has(p)) return null;
    if (f.t === "list") {
      const arr = (nilai[p] as unknown[]) ?? [];
      const it = f.item;
      return (
        <div key={p} className="space-y-2">
          <p className="text-sm text-ink/80">{tulis(p, f)}</p>
          {arr.map((x, i) => (
            <div key={i} className="flex gap-2 rounded-xl border border-ink/10 p-2">
              <div className="grid flex-1 gap-2">
                {isField(it) ? (
                  <input className={inp} value={String(x ?? "")} onChange={(e) => set(p, arr.map((y, j) => (j === i ? e.target.value : y)))} />
                ) : (
                  Object.entries(it as Record<string, Field>).map(([k, sf]) => (
                    <label key={k} className="grid gap-1 text-xs text-ink/60">
                      {tulis(`${p}.${k}`, sf)}
                      {sf.t === "text" ? (
                        <textarea className={`${inp} min-h-16`} value={String((x as V)?.[k] ?? "")} onChange={(e) => set(p, arr.map((y, j) => (j === i ? { ...(y as V), [k]: e.target.value } : y)))} />
                      ) : (
                        <input className={inp} value={String((x as V)?.[k] ?? "")} onChange={(e) => set(p, arr.map((y, j) => (j === i ? { ...(y as V), [k]: e.target.value } : y)))} />
                      )}
                    </label>
                  ))
                )}
              </div>
              <button type="button" className="self-start text-xs text-ink/45 underline" onClick={() => set(p, arr.filter((_, j) => j !== i))}>
                {v.remove}
              </button>
            </div>
          ))}
          <button type="button" className="text-xs font-medium text-violet" onClick={() => set(p, [...arr, isField(it) ? "" : {}])}>
            + {v.add}
          </button>
        </div>
      );
    }
    return (
      <label key={p} className={`grid gap-1 ${f.t === "bool" ? "grid-cols-[auto_1fr] items-center gap-2" : ""}`}>
        {f.t === "bool" ? input(p, f) : null}
        <span className="text-sm text-ink/80">
          {tulis(p, f)}
          {f.optional && <span className="text-ink/40"> · {v.optional}</span>}
          {f.t === "text" && f.min ? <span className="font-mono text-[10px] text-ink/40"> · {String(nilai[p] ?? "").length}/{f.min}+</span> : null}
        </span>
        {f.t !== "bool" ? input(p, f) : null}
      </label>
    );
  };

  const bagian = (key: string, node: Node, path: string): React.ReactNode[] =>
    Object.entries(node as Record<string, Node>).flatMap(([k, n]): React.ReactNode[] => {
      const p = path ? `${path}.${k}` : k;
      return isField(n) ? [baris(p, n)] : bagian(key, n, p);
    });

  return (
    <div className={panel}>
      <p className={label}>{v.form}</p>
      {!ak.authenticated ? (
        <div className="mt-3 flex flex-wrap items-center gap-3">
          <p className="text-sm text-ink/70">{v.signInFirst}</p>
          <button className={btn} onClick={ak.bukaLogin}>
            {v.signIn}
          </button>
        </div>
      ) : (
        <p className="mt-2 font-mono text-xs text-ink/60">{v.wallet.replace("{w}", wallet ?? "-")}</p>
      )}
      <form
        className="mt-5 space-y-8"
        onSubmit={(e) => {
          e.preventDefault();
          kirim();
        }}
      >
        <fieldset className="space-y-4">
          <legend className="font-display text-xl text-ink">{v.sections.spec}</legend>
          <div>
            <p className="text-sm text-ink/80">{v.rule.kindTitle}</p>
            <div className="mt-2 grid gap-2 sm:grid-cols-3" role="radiogroup" aria-label={v.rule.kindTitle}>
              {KINDS.map((k) => {
                const open = (info.kinds_open ?? []).includes(k);
                return (
                  <button
                    key={k}
                    type="button"
                    role="radio"
                    aria-checked={k === jenis}
                    aria-disabled={!open}
                    disabled={!open}
                    onClick={() => open && setJenis(k)}
                    className={`rounded-xl border p-3 text-left transition-colors ${k === jenis ? "border-violet bg-violet/10" : open ? "border-ink/15 bg-white hover:border-violet" : "border-ink/10 bg-ink/[0.03] opacity-60"}`}
                  >
                    <span className="flex items-center justify-between gap-2 text-sm font-medium text-ink">
                      {v.rule.kinds[k].name}
                      {!open && <span className="rounded-full bg-ink/10 px-2 py-0.5 text-[10px] font-normal uppercase tracking-wide text-ink/60">{v.rule.soon}</span>}
                    </span>
                    <span className="mt-0.5 block text-xs text-ink/60">{v.rule.kinds[k].text}</span>
                  </button>
                );
              })}
            </div>
            <p className="mt-2 text-xs text-ink/50">{v.rule.publicNote}</p>
          </div>
          {bagian("spec", (info.schema as Record<string, Node>).spec, "spec")}
          <div>
            <p className="text-sm text-ink/80">{v.universe}</p>
            <div className="mt-2 flex flex-wrap gap-1.5">
              {info.symbols.map((sym) => {
                const on = uni.includes(sym);
                return (
                  <button
                    type="button"
                    key={sym}
                    onClick={() => setUni((u) => (on ? u.filter((x) => x !== sym) : [...u, sym]))}
                    className={`rounded-full border px-2.5 py-1 font-mono text-[11px] transition-colors ${on ? "border-violet bg-violet text-white" : "border-ink/15 text-ink/70 hover:border-violet"}`}
                  >
                    {sym.replace("USDT", "")}
                  </button>
                );
              })}
            </div>
          </div>
          {jenis === "rule" && (info.rule ? <RuleBuilder vocab={info.rule} state={rule} setState={setRule} /> : <p className="text-sm text-ink/60">…</p>)}
          {jenis === "code" && info.code && <CodeEditor info={info.code} value={teksKode} onChange={setKode} />}
          {jenis === "feed" && info.feed && <FeedPanel info={info.feed} />}
        </fieldset>
        {(["identity", "theory", "evidence", "declarations"] as const).map((sec) => (
          <fieldset key={sec} className="space-y-4">
            <legend className="font-display text-xl text-ink">{v.sections[sec]}</legend>
            {sec === "identity" && <p className="text-xs text-ink/50">{v.contactNote}</p>}
            {bagian(sec, (info.schema as Record<string, Node>)[sec], sec)}
          </fieldset>
        ))}
        {masalah.length > 0 && (
          <div role="alert" className="rounded-xl bg-ink/5 p-3 text-sm text-ink/80">
            <p className="font-medium">{v.problems}</p>
            <ul className="mt-1 list-disc pl-5 text-xs">
              {masalah.map((m) => (
                <li key={m}>{m}</li>
              ))}
            </ul>
          </div>
        )}
        {id && <p className="rounded-xl bg-violet/10 p-3 text-sm text-violet">{v.sent.replace("{id}", id.slice(0, 18) + "…")}</p>}
        <button className={btn} disabled={!ak.authenticated || !wallet || !!fase}>
          {fase === "cek" ? v.checking : fase === "tanda" ? v.signing : fase === "kirim" ? v.sending : v.sign}
        </button>
      </form>
    </div>
  );
}
