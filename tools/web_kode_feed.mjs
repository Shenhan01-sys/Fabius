// Kontrak web -> gerbang (P167b/P167c): `web/src/lib/kode.ts` (sha + ukuran + PARAMS kode) dan `web/src/lib/feed.ts` (teks kanonik + sha bobot ppm)
// dijalankan Node atas masukan JSON di stdin {codes: [teks], weights: [{simbol: ppm}]} dan hasilnya dicetak ke stdout. Dipakai
// `engine/tests/test_kode.py::WebContractTests` dan `engine/tests/test_feed_kind.py::WebContractTests`: web dan gerbang tidak bisa menyimpang diam-diam.
//   node --experimental-strip-types --no-warnings tools/web_kode_feed.mjs < masukan.json
import { meta } from "../web/src/lib/kode.ts";
import { bobotKanonik, weightsSha, kePpm } from "../web/src/lib/feed.ts";

const chunks = [];
for await (const c of process.stdin) chunks.push(c);
const input = JSON.parse(Buffer.concat(chunks).toString("utf8"));
const codes = [];
for (const src of input.codes ?? []) codes.push(await meta(src));
const weights = [];
for (const w of input.weights ?? []) weights.push({ text: bobotKanonik(w), sha: await weightsSha(w) });
process.stdout.write(JSON.stringify({ codes, weights, ppm: [0.25, -0.1, 1 / 3].map(kePpm) }));
