// P167c: jenis `feed` di web. Bobot komit = bilangan bulat ppm (1 000 000 = 1,0) supaya teks kanonik SAMA PERSIS dengan gerbang
// (`engine/feed.py::bobot_kanonik` / `weights_sha`); kontrak lintas bahasa diuji `engine/tests/test_feed_kind.py::WebContractTests`.
// Program penerbit mengomit lewat API (`POST /bots/feed/typed-data` lalu `POST /bots/feed/commit`); formulir web hanya mendaftarkan bot.

export type FeedInfo = {
  label: string;
  shadow_days: number;
  slot: string;
  commit_cutoff_s: number;
  max_ahead_s: number;
  ppm: number;
  anchor_label: string;
  eip712: { name: string; version: string; chain_id: number; primary_type: string; types: { name: string; type: string }[] };
  weights_text: string;
  replay_gates: string;
  routes: string[];
};

export const PPM = 1_000_000;

/** Bobot desimal -> ppm bulat (dibulatkan ke terdekat). */
export const kePpm = (w: number): number => Math.round(w * PPM);

/** Teks kanonik: "BTCUSDT:250000,ETHUSDT:-100000" (urut simbol, nol dibuang; kosong = flat). */
export function bobotKanonik(bobot: Record<string, number>): string {
  return Object.keys(bobot)
    .sort()
    .filter((a) => Math.trunc(bobot[a]) !== 0)
    .map((a) => `${a}:${Math.trunc(bobot[a])}`)
    .join(",");
}

export async function weightsSha(bobot: Record<string, number>): Promise<string> {
  const buf = await crypto.subtle.digest("SHA-256", new TextEncoder().encode(bobotKanonik(bobot)));
  return "0x" + Array.from(new Uint8Array(buf), (b) => b.toString(16).padStart(2, "0")).join("");
}

/** Masalah bobot di sisi web (gerbang tetap memeriksa ulang): bulat, |w| <= 1e6, gross <= 1e6, simbol universe. */
export function masalahBobot(bobot: Record<string, number>, universe: string[]): string[] {
  const out: string[] = [];
  let gross = 0;
  for (const [a, w] of Object.entries(bobot)) {
    if (!universe.includes(a)) out.push(`${a}: not in the bot's universe`);
    else if (!Number.isInteger(w) || Math.abs(w) > PPM) out.push(`${a}: weight must be an integer ppm within ±${PPM}`);
    else gross += Math.abs(w);
  }
  if (!out.length && gross > PPM) out.push(`gross ${gross} ppm > ${PPM}`);
  return out;
}
