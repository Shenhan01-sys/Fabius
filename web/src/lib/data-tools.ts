// Alat data untuk agent analis (P140, F-D102): sumber PUBLIK tanpa kunci, hanya baca, disajikan lewat MCP. Konteks pasar memecoin/DEX - relevansinya
// rendah untuk 16 perp mayor yang diperdagangkan bot Fabius (paling relevan: B4 listing baru); agent tetap hanya MEMILIH di antara bot terkunci.
// Akses diukur 5 Okt: DexScreener search + token-pairs 200, RugCheck report/summary 200, Bubblemaps legacy map-availability 200 (map-metadata 500,
// map-data 404 -> hanya ketersediaan peta), GMGN route publik 403 (tidak disediakan). Gagal membaca sumber = galat dengan alasannya, bukan daftar kosong.

export const CHAIN_RE = /^[a-z0-9-]{2,20}$/;
export const ADDR_RE = /^[A-Za-z0-9]{20,64}$/;
export const MINT_RE = /^[1-9A-HJ-NP-Za-km-z]{32,44}$/;

const UA = { "User-Agent": "fabius-mcp/1.0 (+https://fabius-one.vercel.app/mcp)" };

async function getJson(url: string, revalidate: number): Promise<unknown> {
  const r = await fetch(url, { headers: UA, next: { revalidate } });
  if (!r.ok) throw new Error(`${new URL(url).host} answered HTTP ${r.status}`);
  return r.json();
}

type DsPair = {
  chainId: string;
  dexId: string;
  pairAddress: string;
  url?: string;
  baseToken: { address: string; symbol: string };
  quoteToken: { symbol: string };
  priceUsd?: string;
  liquidity?: { usd?: number };
  volume?: { h24?: number };
  priceChange?: { h24?: number };
  fdv?: number;
  pairCreatedAt?: number;
  txns?: { h24?: { buys: number; sells: number } };
};

/** DexScreener: pasangan DEX untuk kata kunci (`query`) atau satu token (`chain` + `token`); 10 teratas menurut likuiditas. */
export async function dexscreener(a: { query?: string; chain?: string; token?: string }) {
  if (!(a.chain && a.token) && !a.query) throw new Error("give `query`, or `chain` + `token`");
  const raw =
    a.chain && a.token
      ? await getJson(`https://api.dexscreener.com/token-pairs/v1/${a.chain}/${a.token}`, 60)
      : await getJson(`https://api.dexscreener.com/latest/dex/search?q=${encodeURIComponent(a.query ?? "")}`, 60);
  const pairs: DsPair[] = Array.isArray(raw) ? raw : ((raw as { pairs?: DsPair[] }).pairs ?? []);
  return pairs
    .slice()
    .sort((x, y) => (y.liquidity?.usd ?? 0) - (x.liquidity?.usd ?? 0))
    .slice(0, 10)
    .map((p) => ({
      chain: p.chainId,
      dex: p.dexId,
      pair: p.pairAddress,
      base: { symbol: p.baseToken.symbol, address: p.baseToken.address },
      quote: p.quoteToken.symbol,
      price_usd: p.priceUsd ? Number(p.priceUsd) : null,
      liquidity_usd: p.liquidity?.usd ?? null,
      volume_24h_usd: p.volume?.h24 ?? null,
      change_24h_pct: p.priceChange?.h24 ?? null,
      fdv_usd: p.fdv ?? null,
      buys_sells_24h: p.txns?.h24 ? [p.txns.h24.buys, p.txns.h24.sells] : null,
      pair_created: p.pairCreatedAt ? new Date(p.pairCreatedAt).toISOString() : null,
      url: p.url ?? null,
    }));
}

type RcSummary = { score?: number; score_normalised?: number; lpLockedPct?: number; risks?: { name: string; level: string; description: string; score: number }[] };

/** RugCheck (Solana): skor risiko + daftar risiko + persen LP terkunci untuk satu mint. */
export async function rugcheck(mint: string) {
  const d = (await getJson(`https://api.rugcheck.xyz/v1/tokens/${mint}/report/summary`, 300)) as RcSummary;
  return {
    score: d.score ?? null,
    score_normalised: d.score_normalised ?? null,
    lp_locked_pct: d.lpLockedPct ?? null,
    risks: (d.risks ?? []).map((r) => ({ name: r.name, level: r.level, description: r.description, score: r.score })),
    report: `https://rugcheck.xyz/tokens/${mint}`,
  };
}

/** Bubblemaps: API publik hanya menjawab apakah peta klaster pemegang tersedia; isi peta dibuka di app-nya. */
export async function bubblemaps(chain: string, token: string) {
  const d = (await getJson(`https://api-legacy.bubblemaps.io/map-availability?chain=${chain}&token=${token}`, 3600)) as { availability?: boolean; status?: string };
  return {
    available: !!d.availability,
    status: d.status ?? null,
    map: `https://app.bubblemaps.io/${chain}/token/${token}`,
    note: "The public Bubblemaps API only exposes map availability (metadata/data endpoints answered 500/404 on 5 Oct); open the map for holder clusters.",
  };
}

// FOMO API (fomoapi.io, fomo.family): leaderboard trader + "thesis" (alasan trader di balik trade). Kunci `FOMO_API_KEY` hanya di env Vercel.
// Paket gratis 250.000 kredit/bulan: leaderboard 250, thesis 1.250 per halaman (dok fomoapi.io/docs, 5 Okt). Supaya agent tidak bisa menguras kuota:
// hanya 3 tampilan tetap + cache server (leaderboard 12 jam, thesis 6 jam) -> terburuk ±180.000 kredit/bulan; posisi per handle TIDAK disediakan.
export const FOMO_VIEWS = ["leaderboard_24h", "leaderboard_7d", "theses"] as const;
export type FomoView = (typeof FOMO_VIEWS)[number];

function trim(o: unknown, n = 20): unknown {
  if (Array.isArray(o)) return o.slice(0, n);
  if (o && typeof o === "object") return Object.fromEntries(Object.entries(o as Record<string, unknown>).map(([k, v]) => [k, Array.isArray(v) ? v.slice(0, n) : v]));
  return o;
}

export async function fomo(view: FomoView) {
  const key = process.env.FOMO_API_KEY;
  if (!key) throw new Error("FOMO_API_KEY is not set on the Fabius server yet");
  const path = view === "theses" ? "/v2/thesis?sort=recent&limit=20" : `/v2/leaderboard/${view === "leaderboard_7d" ? "7d" : "24h"}`;
  const r = await fetch(`https://api.fomoapi.io${path}`, { headers: { ...UA, authorization: `Bearer ${key}` }, next: { revalidate: view === "theses" ? 21_600 : 43_200 } });
  if (!r.ok) {
    const b = (await r.json().catch(() => ({}))) as { error?: string };
    throw new Error(`fomoapi.io answered HTTP ${r.status}${b.error ? ` (${b.error})` : ""}`);
  }
  return trim(await r.json());
}
