// P157 (F5, F-D111): akun MCP berbayar - harga, daftar alat, format pesan kunci, klien gerbang. Disalin dari tools/akun_mcp.py; tes kontrak lintas bahasa
// (engine/tests/test_akun_mcp.py::WebContractTests, Node --experimental-strip-types) menjaga keduanya sama. Gerbang = sumber kebenaran saldo + potongan.
// Berkas ini MANDIRI (tanpa impor alias / paket) supaya Node bisa memuatnya langsung untuk tes kontrak.

// tools/x402_sinyal.py di Railway fabius-x402. `FABIUS_GATE` (env server, sama dengan tools/desk_agent_client.py) hanya untuk uji lokal /mcp terhadap
// gerbang lokal; di peramban env ini tidak ada, jadi selalu alamat produksi.
export const GATE = (typeof process !== "undefined" && process.env?.FABIUS_GATE) || "https://fabius-x402-production.up.railway.app";

// Harga atomik FAB (6 desimal). F-D111 #2 - disetujui builder 5 Okt.
export const HARGA: Record<string, number> = { fabius_signal: 10_000, fabius_signal_explain: 20_000, fabius_data: 5_000 };
// USULAN (F-D111 #3 tanpa harga): alat tingkat 0 lama yang dijalankan server MCP ini lalu dipotong lewat gerbang /account/charge.
export const HARGA_MCP: Record<string, number> = Object.fromEntries(
  [
    "fabius_analysts",
    "fabius_desk",
    "fabius_analyst_join",
    "fabius_desk_join",
    "fabius_confidence",
    "fabius_list_bots",
    "fabius_track_record",
    "fabius_proof_feed",
    "fabius_locks",
    "fabius_signals",
    "fabius_latest_signals",
    "fabius_verify",
    "fabius_status",
  ].map((n) => [n, 5_000]),
);
export const GRATIS = ["fabius_pricing", "fabius_account"];
// F-D111 #3: alat data publik P140 dicabut. USULAN: fabius_overview + fabius_signal_offer dilebur ke fabius_pricing.
export const DICABUT = ["fabius_dexscreener", "fabius_rugcheck", "fabius_bubblemaps", "fabius_fomo", "fabius_overview", "fabius_signal_offer"];

export const FMT_KUNCI = "Fabius MCP API key v1\nwallet: {dompet}\nts: {ts}\nchain: 97";
export const FMT_CABUT = "Fabius MCP API key revoke v1\nwallet: {dompet}\nkey_id: {kunci_id}\nts: {ts}\nchain: 97";
export const KUNCI_RE = /^fabk_[A-Za-z0-9_-]{43}$/;
export const DEPOSIT_PILIHAN = [100_000, 250_000, 500_000]; // tombol halaman /account (USULAN; batas gerbang 50 000 - 1 000 000)

export const pesanKunci = (dompet: string, ts: number) => FMT_KUNCI.replace("{dompet}", dompet.toLowerCase()).replace("{ts}", String(Math.trunc(ts)));
export const pesanCabut = (dompet: string, kunciId: string, ts: number) =>
  FMT_CABUT.replace("{dompet}", dompet.toLowerCase()).replace("{kunci_id}", kunciId).replace("{ts}", String(Math.trunc(ts)));
export const fab = (atomic: number) => String(atomic / 1e6);

/** `FABIUS_MCP_BERBAYAR` (env server Vercel; bawaan MATI): hanya "hidup" / "nyala" / "1" yang membuka set alat F5 di /mcp. */
export function berbayar(nilai?: string): boolean {
  const v = (nilai ?? process.env.FABIUS_MCP_BERBAYAR ?? "").trim().toLowerCase();
  return v === "hidup" || v === "nyala" || v === "1";
}

/** Kunci API dari `Authorization: Bearer fabk_...` atau `X-Api-Key`; token lain (mis. Privy) bukan kunci akun. */
export function kunciDari(h: Headers): string | null {
  const auth = (h.get("authorization") ?? "").trim();
  const tok = auth.toLowerCase().startsWith("bearer ") ? auth.slice(7).trim() : (h.get("x-api-key") ?? "").trim();
  return KUNCI_RE.test(tok) ? tok : null;
}

export async function sha256hex(teks: string): Promise<string> {
  const d = await globalThis.crypto.subtle.digest("SHA-256", new TextEncoder().encode(teks));
  return "0x" + Array.from(new Uint8Array(d), (b) => b.toString(16).padStart(2, "0")).join("");
}

export type Jawab = { ok: boolean; status: number; body: Record<string, unknown> };

async function gerbang(path: string, init?: RequestInit): Promise<Jawab> {
  const r = await fetch(`${GATE}${path}`, { cache: "no-store", ...init });
  let body: Record<string, unknown> = {};
  try {
    body = (await r.json()) as Record<string, unknown>;
  } catch {
    body = { error: `gate HTTP ${r.status} (not JSON)` };
  }
  return { ok: r.ok, status: r.status, body };
}

const json = (kunci: string | null, isi: unknown): RequestInit => ({
  method: "POST",
  headers: { "Content-Type": "application/json", ...(kunci ? { Authorization: `Bearer ${kunci}` } : {}) },
  body: JSON.stringify(isi),
});

export const harga = () => gerbang("/account/pricing");
export const akun = (kunci: string) => gerbang("/account", { headers: { Authorization: `Bearer ${kunci}` } });
/** Alat yang datanya dari gerbang: potong lalu kirim (satu call_id = satu potongan). */
export const panggil = (kunci: string, tool: string, args: Record<string, unknown>, callId: string) =>
  gerbang("/account/call", json(kunci, { tool, args, call_id: callId }));
/** Alat yang dijalankan server MCP: `check` dulu (tanpa potongan), jalankan, lalu potong dengan sha hasilnya. */
export const potong = (kunci: string, tool: string, callId: string, responseSha: string | null, check: boolean) =>
  gerbang("/account/charge", json(kunci, { tool, call_id: callId, response_sha: responseSha, check }));
export const buatKunci = (wallet: string, ts: number, signature: string) => gerbang("/account/key", json(null, { wallet, ts, signature }));
export const cabutKunci = (wallet: string, keyId: string, ts: number, signature: string) =>
  gerbang("/account/key/revoke", json(null, { wallet, key_id: keyId, ts, signature }));
