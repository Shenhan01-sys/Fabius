// Kontrak web -> gerbang (P167a): keadaan pembangun aturan di web (`web/src/lib/rule.ts`) -> JSON gerbang, dicetak ke stdout.
// Dipakai `engine/tests/test_rule.py::WebContractTests` (menjalankan berkas ini dengan Node >= 22.6 dan memvalidasi keluarannya dengan
// `engine/rule.py`), jadi web dan gerbang tidak bisa menyimpang diam-diam. Tanpa jaringan, tanpa berkas keluaran.
//   node --experimental-strip-types --no-warnings tools/web_rule_states.mjs
import { startRule, toJson, describe, stats, workload, refs, renameParam } from "../web/src/lib/rule.ts";

const cmp = (op, a, b) => ({ cmp: op, a, b });
const f = (name, n, lag) => ({ f: name, ...(n !== undefined ? { n } : {}), ...(lag !== undefined ? { lag } : {}) });

const rename = renameParam(
  { ...startRule(), params: [{ name: "N", value: 20 }], masuk_long: cmp(">", f("ret", { p: "N" }), { c: 0 }) },
  "N",
  "WIN",
);

const states = {
  start: startRule(),
  nested: {
    ...startRule(),
    params: [
      { name: "N", value: "20" },
      { name: "Z", value: "2" },
      { name: "G", value: "3" },
    ],
    masuk_long: { and: [cmp("<", f("zscore", { p: "N" }), { op: "*", a: { p: "Z" }, b: { c: "-1" } }), { not: cmp("<", f("close"), f("sma", 50, { p: "G" })) }] },
    keluar_long: { or: [cmp(">=", f("zscore", { p: "N" }), { c: "0" }), cmp("<", { fn: "min", args: [f("low", undefined, 1), f("low", undefined, 2)] }, { c: "1" })] },
    masuk_short: cmp(">", f("rsi", 14), { c: 80 }),
    keluar_short: cmp("<", f("rsi", 14), { c: "50" }),
    bobot: { skema: "inv_vol", gross_maks: "0.8", n: { p: "N" } },
  },
  rank: {
    ...startRule(),
    mode: "peringkat",
    params: [{ name: "L", value: "28" }],
    skor: { op: "-", a: f("ret", { p: "L" }), b: f("ret", 7) },
    long_teratas: "3",
    short_terbawah: "3",
    min_aset: "8",
    rotasi: "tujuh_sub_buku",
    bobot: { skema: "inv_vol", gross_maks: "2", n: 30 },
  },
  // bobot sama tidak boleh membawa `n` (sisa dari inv_vol); slot kosong tidak boleh ikut terkirim
  stale_n: { ...startRule(), bobot: { skema: "sama", gross_maks: "1", n: 30 }, keluar_long: undefined, masuk_short: undefined },
  renamed: rename,
  // ukuran: jendela yang sama (fitur + n) dihitung sekali, jendela volatilitas ikut
  sizes: {
    ...startRule(),
    masuk_long: { and: [cmp(">", f("sma", 5), f("sma", 5, 2)), { not: cmp("<", f("rsi", 14), { c: 30 }) }] },
    keluar_long: cmp(">", f("close"), { c: 1 }),
    bobot: { skema: "inv_vol", gross_maks: 1, n: 14 },
  },
};

const out = { rules: {}, sizes: {}, meta: {} };
for (const [k, s] of Object.entries(states)) {
  out.rules[k] = toJson(s);
  out.sizes[k] = { ...stats(s), work: workload(s) };
}
out.meta = { refs: [...refs(rename)], words_en: describe(rename, "en"), words_id: describe(rename, "id") };
console.log(JSON.stringify(out));
