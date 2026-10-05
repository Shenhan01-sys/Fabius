// Pembayaran x402 per sinyal dari peramban (P138c, F-D100/F-D101): bentuk SAMA dengan tools/x402_client.py dan tools/x402_sinyal.py::sign_payment.
// Pembeli menandatangani dua pesan EIP-712 (Permit2 witness + EIP-2612 permit untuk Permit2) dan tidak pernah mengirim transaksi: gerbang (fasilitator)
// memanggil settleWithPermit di proxy kanonis lalu mengembalikan paket sinyal. Testnet 97, token Fabius Credit (FAB) tanpa nilai.

import { createPublicClient, http, parseAbi, type Hex } from "viem";
import { bscTestnet } from "viem/chains";

export const GATE = "https://fabius-x402-production.up.railway.app"; // tools/x402_sinyal.py di Railway fabius-x402
export const FAB = "0xc7b6d5cdbdc881daae0dbcc095d4f184b70ec881" as const; // deployments/97.json x402_sinyal.token
export const PERMIT2 = "0x000000000022D473030F116dDEE9F6B43aC78BA3" as const;
export const PROXY = "0x402085c248EeA27D92E8b30b2C58ed07f9E20001" as const; // x402ExactPermit2Proxy kanonis
export const PRIVY_APP_ID = "cmuukhkc200zo0cjh0jmqd11x"; // publik (builder, 5 Okt); secret hanya di Railway
export const PRIVY_KEY_QUORUM_ID = "pyyven7fpdtnc30uuij8ikps"; // key quorum fabius-bot1 (P138e): pasangan lokal yang tidak pernah terbuka; izin user -> /buy dari chat
const CHAIN_ID = 97;

export const chain97 = createPublicClient({ chain: bscTestnet, transport: http("https://bsc-testnet-rpc.publicnode.com") });
const ERC20 = parseAbi(["function balanceOf(address) view returns (uint256)", "function nonces(address) view returns (uint256)"]);

export type Teaser = {
  teaser: { confidence_pct: number | null; label: string; status: string | null; gerbang_v1: string | null; fd16: string; kematangan: Record<string, [number, number]> };
  harga: { bar: string; atomic: number; fab: number; alasan: string };
};
export type Accept = { amount: string; asset: string; payTo: string; network: string; maxTimeoutSeconds?: number; extra?: { name?: string; version?: string } };
export type SignFn = (typedData: Record<string, unknown>) => Promise<string>;
export type Package = {
  bot: string;
  bar: string;
  targets: Record<string, number>;
  signal_ids: string[];
  commitId: string;
  komit?: { ada: boolean; committedAt: number | null; n: number | null; terungkap: number | null };
  validasi_erc8004?: { skor: number; dijawab: boolean } | null;
  pembayaran: { tx: string; payer: string; atomic: number };
  rincian?: Rincian;
};
export type RincianAset = {
  sisi: string;
  bobot: number;
  tutup?: number;
  momentum?: number;
  masuk?: { bar: string; harga: number; pnl: number; hari: number };
  masuk_bila?: { bar: string; di_atas: number };
  keluar_berikut?: { bar: string; level: number; jarak: number };
};
export type Rincian = { aturan: string; aturan_en?: string | null; param: number; perubahan: { masuk: string[]; keluar: string[]; tetap: string[] }; aset: Record<string, RincianAset>; terdekat_keluar?: string | null };

export async function teaser(bot: string): Promise<Teaser> {
  const r = await fetch(`${GATE}/teaser/${bot}`, { cache: "no-store" });
  if (!r.ok) throw new Error(`gate HTTP ${r.status}`);
  return (await r.json()) as Teaser;
}

export const fabBalance = (owner: Hex) => chain97.readContract({ address: FAB, abi: ERC20, functionName: "balanceOf", args: [owner] });

export async function faucet(address: string): Promise<{ ok: boolean; note: string }> {
  const r = await fetch(`${GATE}/faucet`, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ address }) });
  const b = (await r.json()) as { dikirim_atomic?: number; tx?: string; error?: string; catatan?: string };
  return { ok: r.ok, note: b.tx ? `+${(b.dikirim_atomic ?? 0) / 1e6} FAB · tx ${b.tx}` : (b.error ?? b.catatan ?? "") };
}

/** v = 27/28 (Permit2 dan EIP-2612 OpenZeppelin menolak 0/1). */
function sig65(sig: string): string {
  const h = sig.startsWith("0x") ? sig.slice(2) : sig;
  const v = parseInt(h.slice(128, 130), 16);
  return "0x" + h.slice(0, 128) + (v < 27 ? v + 27 : v).toString(16).padStart(2, "0");
}

function randomNonce(): string {
  const b = new Uint8Array(16);
  crypto.getRandomValues(b);
  return BigInt("0x" + Array.from(b, (x) => x.toString(16).padStart(2, "0")).join("")).toString();
}

/** 402 -> tanda tangani dua pesan -> ulangi permintaan dengan PAYMENT-SIGNATURE -> paket. `tg` = tautan bertanda dari bot Telegram (opsional). */
export async function buy(bot: string, bar: string, owner: Hex, sign: SignFn, tg?: string | null): Promise<Package> {
  const url = `${GATE}/sinyal/${bot}/${bar}${tg ? `?tg=${encodeURIComponent(tg)}` : ""}`;
  const first = await fetch(url, { cache: "no-store" });
  if (first.status !== 402) throw new Error(`expected 402, got ${first.status}`);
  const req = JSON.parse(atob(first.headers.get("payment-required") ?? "")) as { accepts: Accept[] };
  const acc = req.accepts[0];
  if (acc.asset.toLowerCase() !== FAB.toLowerCase() || acc.network !== `eip155:${CHAIN_ID}`) throw new Error("unexpected payment requirements");
  const now = Math.floor(Date.now() / 1000);
  const validAfter = String(now - 15);
  const deadline = String(now + Math.min(110, acc.maxTimeoutSeconds ?? 110));
  const nonce = randomNonce();
  const sigP2 = await sign({
    domain: { name: "Permit2", chainId: CHAIN_ID, verifyingContract: PERMIT2 },
    types: {
      EIP712Domain: [
        { name: "name", type: "string" },
        { name: "chainId", type: "uint256" },
        { name: "verifyingContract", type: "address" },
      ],
      PermitWitnessTransferFrom: [
        { name: "permitted", type: "TokenPermissions" },
        { name: "spender", type: "address" },
        { name: "nonce", type: "uint256" },
        { name: "deadline", type: "uint256" },
        { name: "witness", type: "Witness" },
      ],
      TokenPermissions: [
        { name: "token", type: "address" },
        { name: "amount", type: "uint256" },
      ],
      Witness: [
        { name: "to", type: "address" },
        { name: "validAfter", type: "uint256" },
      ],
    },
    primaryType: "PermitWitnessTransferFrom",
    message: { permitted: { token: FAB, amount: acc.amount }, spender: PROXY, nonce, deadline, witness: { to: acc.payTo, validAfter } },
  });
  const tokNonce = await chain97.readContract({ address: FAB, abi: ERC20, functionName: "nonces", args: [owner] });
  const sig2612 = await sign({
    domain: { name: acc.extra?.name ?? "Fabius Credit", version: acc.extra?.version ?? "1", chainId: CHAIN_ID, verifyingContract: FAB },
    types: {
      EIP712Domain: [
        { name: "name", type: "string" },
        { name: "version", type: "string" },
        { name: "chainId", type: "uint256" },
        { name: "verifyingContract", type: "address" },
      ],
      Permit: [
        { name: "owner", type: "address" },
        { name: "spender", type: "address" },
        { name: "value", type: "uint256" },
        { name: "nonce", type: "uint256" },
        { name: "deadline", type: "uint256" },
      ],
    },
    primaryType: "Permit",
    message: { owner, spender: PERMIT2, value: acc.amount, nonce: tokNonce.toString(), deadline },
  });
  const payment = {
    x402Version: 2,
    resource: { url, mimeType: "application/json" },
    accepted: { scheme: "exact", network: acc.network, amount: acc.amount, asset: FAB, payTo: acc.payTo },
    payload: {
      signature: sig65(sigP2),
      permit2Authorization: { permitted: { token: FAB, amount: acc.amount }, from: owner, spender: PROXY, nonce, deadline, witness: { to: acc.payTo, validAfter } },
    },
    extensions: {
      eip2612GasSponsoring: {
        info: { from: owner, asset: FAB, spender: PERMIT2, amount: acc.amount, nonce: tokNonce.toString(), deadline, signature: sig65(sig2612), version: acc.extra?.version ?? "1" },
      },
    },
  };
  const paid = await fetch(url, { cache: "no-store", headers: { "PAYMENT-SIGNATURE": btoa(JSON.stringify(payment)) } });
  const body = (await paid.json()) as Package & { error?: string };
  if (!paid.ok) throw new Error(body.error ?? `gate HTTP ${paid.status}`);
  return body;
}
