// P167a (epik 12): aturan deklaratif bot (kind=rule) di web. Kosakata + batas dibagikan gerbang (`GET /bots/schema` -> `rule`, sumbernya
// engine/rule.py); web hanya menyusun pohon, menormalkan angka, menghitung simpul, dan menuliskan aturan dalam kalimat. Validasi yang
// berwenang tetap gerbang (`POST /bots/typed-data` menjelaskan masalah sebelum penandatanganan); tidak ada logika validasi kedua di sini.
import type { Lang } from "./copy";

export type Num = number | string | { p: string };
export type Expr = { c: number | string } | { p: string } | { f: string; n?: Num; lag?: Num } | { op: string; a: Expr; b: Expr } | { fn: string; args: Expr[] };
export type Cond = { cmp: string; a: Expr; b: Expr } | { and: Cond[] } | { or: Cond[] } | { not: Cond };
export type Bobot = { skema: string; gross_maks: number | string; n?: Num };
export type Slot = "masuk_long" | "keluar_long" | "masuk_short" | "keluar_short";
export const SLOTS: Slot[] = ["masuk_long", "keluar_long", "masuk_short", "keluar_short"];

export type RuleState = {
  mode: "per_aset" | "peringkat";
  params: { name: string; value: number | string }[]; // larik supaya urutan dan penggantian nama stabil saat disunting
  masuk_long?: Cond;
  keluar_long?: Cond;
  masuk_short?: Cond;
  keluar_short?: Cond;
  skor: Expr;
  long_teratas: number | string;
  short_terbawah: number | string;
  min_aset: number | string;
  rotasi: string;
  bobot: Bobot;
};

export type RuleVocab = {
  modes: string[];
  price: string[];
  window: string[];
  cmps: string[];
  ops: string[];
  fns: Record<string, [number, number]>;
  rotasi: string[];
  skema: string[];
  limits: { max_simpul: number; max_kedalaman: number; jendela_min: number; jendela_maks: number; lag_maks: number; max_parameter: number; anggaran_jendela: number; k_maks: number; gross_maks: Record<string, number> };
  penggaris: Record<string, unknown>;
};

// ---------------------------------------------------------------- bentuk awal (kerangka netral, bukan contoh strategi)

export const defCond = (): Cond => ({ cmp: ">", a: { f: "close" }, b: { c: 0 } });
export const defExpr = (): Expr => ({ f: "close" });

export const startRule = (): RuleState => ({
  mode: "per_aset",
  params: [],
  masuk_long: defCond(),
  skor: { f: "ret", n: 20 },
  long_teratas: 3,
  short_terbawah: 3,
  min_aset: 8,
  rotasi: "tujuh_sub_buku",
  bobot: { skema: "sama", gross_maks: 1 },
});

// ---------------------------------------------------------------- penelusuran pohon

const isP = (x: unknown): x is { p: string } => !!x && typeof x === "object" && !Array.isArray(x) && Object.keys(x as object).length === 1 && "p" in (x as object);

export function slotsOf(r: RuleState): Slot[] {
  return SLOTS.filter((s) => r[s] !== undefined);
}

function roots(r: RuleState): (Cond | Expr)[] {
  return r.mode === "per_aset" ? slotsOf(r).map((s) => r[s] as Cond) : [r.skor];
}

function nodeStats(n: unknown, depth: number): { nodes: number; depth: number } {
  if (!n || typeof n !== "object") return { nodes: 0, depth };
  if (isP(n)) return { nodes: 1, depth };
  const o = n as Record<string, unknown>;
  const kids: unknown[] = [];
  if ("cmp" in o || "op" in o) kids.push(o.a, o.b);
  else if ("and" in o) kids.push(...(o.and as unknown[]));
  else if ("or" in o) kids.push(...(o.or as unknown[]));
  else if ("not" in o) kids.push(o.not);
  else if ("args" in o) kids.push(...(o.args as unknown[]));
  let nodes = 1;
  let d = depth;
  for (const k of kids) {
    const s = nodeStats(k, depth + 1);
    nodes += s.nodes;
    d = Math.max(d, s.depth);
  }
  return { nodes, depth: d };
}

export function stats(r: RuleState): { nodes: number; depth: number } {
  let nodes = 0;
  let depth = 0;
  for (const root of roots(r)) {
    const s = nodeStats(root, 1);
    nodes += s.nodes;
    depth = Math.max(depth, s.depth);
  }
  return { nodes, depth };
}

/** Nama parameter yang dipakai (di mana pun di pohon, termasuk jendela volatilitas bobot). */
export function refs(r: RuleState): Set<string> {
  const out = new Set<string>();
  const walk = (n: unknown) => {
    if (Array.isArray(n)) return n.forEach(walk);
    if (!n || typeof n !== "object") return;
    if (isP(n)) return void out.add(n.p);
    Object.values(n as object).forEach(walk);
  };
  roots(r).forEach(walk);
  walk(r.bobot.n);
  return out;
}

/** Jumlah jendela semua fitur berbeda (anggaran kerja gerbang); jendela yang masih berupa teks tak sah diabaikan. */
export function workload(r: RuleState): number {
  const val: Record<string, number> = Object.fromEntries(r.params.map((p) => [p.name, Number(p.value)]));
  const seen = new Map<string, number>();
  const note = (f: string, n: unknown) => {
    const w = isP(n) ? val[n.p] : Number(n);
    if (Number.isFinite(w)) seen.set(`${f}|${w}`, w);
  };
  const walk = (n: unknown) => {
    if (Array.isArray(n)) return n.forEach(walk);
    if (!n || typeof n !== "object") return;
    const o = n as Record<string, unknown>;
    if ("f" in o && o.n !== undefined) note(String(o.f), o.n);
    Object.values(o).forEach(walk);
  };
  roots(r).forEach(walk);
  if (r.bobot.skema === "inv_vol") note("vol", r.bobot.n);
  return [...seen.values()].reduce((a, b) => a + b, 0);
}

/** Ganti nama parameter di seluruh pohon (rujukan ikut berubah, tidak menggantung). */
export function renameParam(r: RuleState, from: string, to: string): RuleState {
  const walk = (n: unknown): unknown => {
    if (Array.isArray(n)) return n.map(walk);
    if (!n || typeof n !== "object") return n;
    if (isP(n)) return n.p === from ? { p: to } : n;
    return Object.fromEntries(Object.entries(n as object).map(([k, v]) => [k, walk(v)]));
  };
  const next = walk({ ...r, params: [] }) as RuleState;
  return { ...next, params: r.params.map((p) => (p.name === from ? { ...p, name: to } : p)) };
}

// ---------------------------------------------------------------- JSON yang dikirim ke gerbang

const NUMERIC = new Set(["c", "n", "lag", "gross_maks", "long_teratas", "short_terbawah", "min_aset"]);

function toNum(x: unknown): unknown {
  return typeof x === "string" && x.trim() !== "" && Number.isFinite(Number(x)) ? Number(x) : x;
}

function walkJson(n: unknown, key = ""): unknown {
  if (Array.isArray(n)) return n.map((x) => walkJson(x, key));
  if (n && typeof n === "object") return Object.fromEntries(Object.entries(n as object).map(([k, v]) => [k, walkJson(v, k)]));
  return NUMERIC.has(key) ? toNum(n) : n;
}

/** Aturan sebagai JSON gerbang: angka teks yang sah jadi angka; yang tidak sah dibiarkan supaya gerbang yang menjelaskan masalahnya. */
export function toJson(r: RuleState): Record<string, unknown> {
  const params = Object.fromEntries(r.params.filter((p) => p.name.trim() !== "").map((p) => [p.name.trim(), toNum(p.value)]));
  const bobot = walkJson(r.bobot) as Record<string, unknown>;
  if (r.bobot.skema !== "inv_vol") delete bobot.n;
  if (r.mode === "per_aset") {
    const out: Record<string, unknown> = { mode: "per_aset", params, bobot };
    for (const s of slotsOf(r)) out[s] = walkJson(r[s]);
    return out;
  }
  return {
    mode: "peringkat",
    params,
    skor: walkJson(r.skor),
    long_teratas: toNum(r.long_teratas),
    short_terbawah: toNum(r.short_terbawah),
    min_aset: toNum(r.min_aset),
    rotasi: r.rotasi,
    bobot,
  };
}

// ---------------------------------------------------------------- aturan dalam kalimat (dua bahasa)

const W = {
  en: {
    ago: (n: string) => `${n} days ago`,
    and: " and ",
    or: " or ",
    not: "not ",
    enterLong: "Go long an asset when ",
    exitLong: "Close the long when ",
    exitLongDefault: "Close the long as soon as the entry condition is no longer true.",
    enterShort: "Go short an asset when ",
    exitShort: "Close the short when ",
    exitShortDefault: "Close the short as soon as the entry condition is no longer true.",
    both: "If both entries are true at once the asset stays flat. A value that cannot be computed (not enough data, division by zero) never triggers anything.",
    rank: (s: string, kl: string, ks: string, m: string) =>
      `Every day score each asset by ${s}. ${Number(kl) > 0 ? `Long the top ${kl}` : ""}${Number(kl) > 0 && Number(ks) > 0 ? ", " : ""}${Number(ks) > 0 ? `short the bottom ${ks}` : ""}; no book is formed unless at least ${m} assets have a score.`,
    rotHarian: "Rebalance every day.",
    rotSeven: "Seven sub-books, each rebalanced on a different weekday and averaged: no weekday to choose.",
    sama: (g: string) => `Equal weight: each position gets ${g} ÷ the number of assets with a bar that day.`,
    sizeRank: (g: string) => `Total exposure at most ${g} (half per leg), equal weight inside each leg.`,
    inv: (g: string, n: string) => `Inverse volatility over ${n} days: smaller weight for wilder assets, total exposure at most ${g}.`,
  },
  id: {
    ago: (n: string) => `${n} hari lalu`,
    and: " dan ",
    or: " atau ",
    not: "tidak ",
    enterLong: "Masuk long pada suatu aset bila ",
    exitLong: "Tutup long bila ",
    exitLongDefault: "Tutup long begitu kondisi masuk tidak lagi benar.",
    enterShort: "Masuk short pada suatu aset bila ",
    exitShort: "Tutup short bila ",
    exitShortDefault: "Tutup short begitu kondisi masuk tidak lagi benar.",
    both: "Bila kedua kondisi masuk benar bersamaan, aset tetap flat. Nilai yang tidak bisa dihitung (data kurang, bagi nol) tidak pernah memicu apa pun.",
    rank: (s: string, kl: string, ks: string, m: string) =>
      `Tiap hari beri skor tiap aset menurut ${s}. ${Number(kl) > 0 ? `Long ${kl} teratas` : ""}${Number(kl) > 0 && Number(ks) > 0 ? ", " : ""}${Number(ks) > 0 ? `short ${ks} terbawah` : ""}; buku tidak dibentuk bila aset yang punya skor kurang dari ${m}.`,
    rotHarian: "Rebalance tiap hari.",
    rotSeven: "Tujuh sub-buku, masing-masing direbalance pada hari-minggu berbeda lalu dirata-rata: tidak ada hari yang dipilih.",
    sama: (g: string) => `Bobot sama: tiap posisi mendapat ${g} ÷ jumlah aset yang punya bar hari itu.`,
    sizeRank: (g: string) => `Eksposur total paling banyak ${g} (separuh per kaki), bobot sama di dalam tiap kaki.`,
    inv: (g: string, n: string) => `Volatilitas terbalik ${n} hari: aset yang lebih liar mendapat bobot lebih kecil, eksposur total paling banyak ${g}.`,
  },
} as const;

const show = (x: unknown): string => (typeof x === "object" && x !== null && isP(x) ? x.p : String(x ?? "?"));

export function exprText(e: Expr, lang: Lang): string {
  const o = e as Record<string, unknown>;
  if ("c" in o) return String(o.c);
  if ("p" in o) return String(o.p);
  if ("f" in o) {
    const base = o.n !== undefined ? `${o.f}(${show(o.n)})` : String(o.f);
    return o.lag !== undefined && String(show(o.lag)) !== "0" ? `${base} ${W[lang].ago(show(o.lag))}` : base;
  }
  if ("op" in o) return `(${exprText(o.a as Expr, lang)} ${o.op} ${exprText(o.b as Expr, lang)})`;
  if ("fn" in o) return `${o.fn}(${(o.args as Expr[]).map((a) => exprText(a, lang)).join(", ")})`;
  return "?";
}

export function condText(c: Cond, lang: Lang, top = true): string {
  const o = c as Record<string, unknown>;
  if ("cmp" in o) return `${exprText(o.a as Expr, lang)} ${o.cmp} ${exprText(o.b as Expr, lang)}`;
  if ("not" in o) return `${W[lang].not}(${condText(o.not as Cond, lang, false)})`;
  const key = "and" in o ? "and" : "or";
  const body = (o[key] as Cond[]).map((x) => condText(x, lang, false)).join(W[lang][key]);
  return top ? body : `(${body})`;
}

export function describe(r: RuleState, lang: Lang): string[] {
  const w = W[lang];
  const out: string[] = [];
  if (r.mode === "per_aset") {
    if (r.masuk_long) out.push(`${w.enterLong}${condText(r.masuk_long, lang)}.`);
    if (r.masuk_long) out.push(r.keluar_long ? `${w.exitLong}${condText(r.keluar_long, lang)}.` : w.exitLongDefault);
    if (r.masuk_short) out.push(`${w.enterShort}${condText(r.masuk_short, lang)}.`);
    if (r.masuk_short) out.push(r.keluar_short ? `${w.exitShort}${condText(r.keluar_short, lang)}.` : w.exitShortDefault);
    if (r.masuk_long && r.masuk_short) out.push(w.both);
  } else {
    out.push(w.rank(exprText(r.skor, lang), String(r.long_teratas), String(r.short_terbawah), String(r.min_aset)));
    out.push(r.rotasi === "harian" ? w.rotHarian : w.rotSeven);
  }
  const g = String(r.bobot.gross_maks);
  if (r.bobot.skema === "inv_vol") out.push(w.inv(g, show(r.bobot.n ?? "?")));
  else out.push(r.mode === "per_aset" ? w.sama(g) : w.sizeRank(g));
  return out;
}
