// Pembaca bukti on-chain untuk server MCP (P114). Hanya baca, tanpa kunci. Hash dihitung PERSIS seperti engine Python (`engine/sinyal.py`,
// `tools/signal_commit.py`) dan kontrak (`contracts/SignalAnchor.sol`): leaf = keccak256(abi.encode(Signal, salt)), id = keccak256(abi.encode(Signal)),
// commitId = keccak256(abi.encode(committer, botId, specSha, asof)). Prinsip T8: gagal membaca chain = GALAT (ChainReadError), tidak pernah "tidak ada".

import { createPublicClient, encodeAbiParameters, fallback, hexToString, http, keccak256, pad, parseAbi, parseAbiItem, stringToHex, type Hex } from "viem";
import { bscTestnet } from "viem/chains";

export const SIGNAL_ANCHOR = "0x9B78200beFbbBe836585d31bd5b6dB32587064f3" as const;
export const LOCK_REGISTRY = "0xcF6fBF95fc04DEd8d670512CEc0723a2246Fbb0C" as const;
export const COMMITTER = "0xCA9c7322210E9a7F7d0953c862d4Ef60cC0D64A4" as const;
export const ANCHOR_DEPLOY_BLOCK = 134442917n;
const RAW = "https://raw.githubusercontent.com/Shenhan01-sys/Fabius/master";
const DAY_S = 86_400;
const CHUNK = 5_000n;

export class ChainReadError extends Error {}

const client = createPublicClient({
  chain: bscTestnet,
  transport: fallback([http("https://bsc-testnet.publicnode.com"), http("https://bsc-testnet-rpc.publicnode.com"), http("https://bsc-testnet.drpc.org")]),
});

const ANCHOR_ABI = parseAbi([
  "function getCommit(bytes32 id) view returns ((address committer, uint64 asof, uint64 committedAt, uint32 n, uint32 revealed, bool missed, bytes32 botId, bytes32 specSha, bytes32 root))",
  "function commitCount() view returns (uint256)",
  "function maxLag() view returns (uint64)",
  "function revealWindow() view returns (uint64)",
]);
const REGISTRY_ABI = parseAbi(["function lockedAt(address locker, bytes32 botId, bytes32 specSha) view returns (uint64)"]);
const REVEALED = parseAbiItem(
  "event Revealed(bytes32 indexed id, bytes32 indexed leaf, bytes32 asset, uint8 aksi, int256 bobotLama, int256 bobotBaru, uint256 hargaRef, bytes32 dataHash, bytes32 salt)",
);

const SIGNAL_TYPES = [
  { type: "uint8" }, { type: "bytes32" }, { type: "bytes32" }, { type: "uint64" }, { type: "bytes32" },
  { type: "uint8" }, { type: "int256" }, { type: "int256" }, { type: "uint256" }, { type: "bytes32" },
] as const;

export const ACTIONS: Record<number, { id: string; en: string }> = {
  1: { id: "MASUK_LONG", en: "ENTER_LONG" },
  2: { id: "MASUK_SHORT", en: "ENTER_SHORT" },
  3: { id: "KELUAR", en: "EXIT" },
  4: { id: "UBAH_BOBOT", en: "RESIZE" },
};

export const ascii32 = (s: string): Hex => pad(stringToHex(s), { dir: "right", size: 32 });
export const fromAscii32 = (h: Hex) => hexToString(h, { size: 32 }).replace(/\0+$/, "");
export const closeOf = (bar: string) => Math.floor(Date.parse(`${bar}T00:00:00Z`) / 1000) + DAY_S; // asof = penutupan bar (detik)
const isZero = (h: string) => /^0x0*$/.test(h);

async function read<T>(what: string, f: () => Promise<T>): Promise<T> {
  try {
    return await f();
  } catch (e) {
    throw new ChainReadError(`${what}: chain 97 tak terbaca (${e instanceof Error ? e.message.split("\n")[0].slice(0, 140) : String(e)}) - bukan berarti tidak ada`);
  }
}

export function commitIdOf(bot: string, specSha: Hex, bar: string, committer: Hex = COMMITTER): Hex {
  return keccak256(
    encodeAbiParameters([{ type: "address" }, { type: "bytes32" }, { type: "bytes32" }, { type: "uint64" }], [committer, ascii32(bot), specSha, BigInt(closeOf(bar))]),
  );
}

type RevealedArgs = { asset: Hex; aksi: number; bobotLama: bigint; bobotBaru: bigint; hargaRef: bigint; dataHash: Hex; salt: Hex };

export function signalHashes(c: { botId: Hex; specSha: Hex; asof: bigint }, ev: RevealedArgs) {
  const fields = [1, c.botId, c.specSha, c.asof, ev.asset, ev.aksi, ev.bobotLama, ev.bobotBaru, ev.hargaRef, ev.dataHash] as const;
  const id = keccak256(encodeAbiParameters(SIGNAL_TYPES, fields));
  const leaf = keccak256(encodeAbiParameters([...SIGNAL_TYPES, { type: "bytes32" }], [...fields, ev.salt]));
  return { id, leaf };
}

export async function getCommit(id: Hex) {
  const c = await read("getCommit", () => client.readContract({ address: SIGNAL_ANCHOR, abi: ANCHOR_ABI, functionName: "getCommit", args: [id] }));
  return { ...c, exists: !isZero(c.committer) };
}

export async function lockedAt(bot: string, specSha: Hex, committer: Hex = COMMITTER) {
  return Number(await read("lockedAt", () => client.readContract({ address: LOCK_REGISTRY, abi: REGISTRY_ABI, functionName: "lockedAt", args: [committer, ascii32(bot), specSha] })));
}

export async function windows() {
  const [lag, win] = await Promise.all([
    read("maxLag", () => client.readContract({ address: SIGNAL_ANCHOR, abi: ANCHOR_ABI, functionName: "maxLag" })),
    read("revealWindow", () => client.readContract({ address: SIGNAL_ANCHOR, abi: ANCHOR_ABI, functionName: "revealWindow" })),
  ]);
  return { maxLag: Number(lag), revealWindow: Number(win) };
}

export async function commitCount() {
  return Number(await read("commitCount", () => client.readContract({ address: SIGNAL_ANCHOR, abi: ANCHOR_ABI, functionName: "commitCount" })));
}

/** Event Revealed untuk satu commitId. Jendela blok ditaksir dari `committedAt`; bila jumlah event < `expected`, pindai penuh sejak deploy (dicacah 5.000 blok). */
export async function getReveals(id: Hex, committedAt: number, expected: number) {
  const latest = await read("blockNumber", () => client.getBlock());
  const back = latest.number > 100_000n ? latest.number - 100_000n : 0n;
  const old = await read("getBlock", () => client.getBlock({ blockNumber: back }));
  const spb = Number(latest.timestamp - old.timestamp) / Number(latest.number - back); // detik per blok, diukur
  const est = latest.number - BigInt(Math.max(0, Math.floor((Number(latest.timestamp) - committedAt) / Math.max(spb, 0.05))));
  type Row = { args: Record<string, unknown>; transactionHash: Hex | null; blockNumber: bigint | null };
  const scan = async (from: bigint, to: bigint) => {
    const out: Row[] = [];
    for (let a = from; a <= to; a += CHUNK) {
      const b = a + CHUNK - 1n > to ? to : a + CHUNK - 1n;
      const got = await read("getLogs", () => client.getLogs({ address: SIGNAL_ANCHOR, event: REVEALED, args: { id }, fromBlock: a, toBlock: b }));
      out.push(...(got as unknown as Row[]));
    }
    return out;
  };
  const lo = est > 4_000n ? est - 4_000n : 0n;
  let logs = await scan(lo < ANCHOR_DEPLOY_BLOCK ? ANCHOR_DEPLOY_BLOCK : lo, est + 6_000n > latest.number ? latest.number : est + 6_000n);
  if (logs.length < expected) logs = await scan(ANCHOR_DEPLOY_BLOCK, latest.number);
  return logs.map((l) => ({
    leaf: l.args.leaf as Hex,
    tx: l.transactionHash,
    block: Number(l.blockNumber ?? 0n),
    args: {
      asset: l.args.asset as Hex,
      aksi: Number(l.args.aksi),
      bobotLama: l.args.bobotLama as bigint,
      bobotBaru: l.args.bobotBaru as bigint,
      hargaRef: l.args.hargaRef as bigint,
      dataHash: l.args.dataHash as Hex,
      salt: l.args.salt as Hex,
    } as RevealedArgs,
  }));
}

export function describe(ev: RevealedArgs) {
  return {
    asset: fromAscii32(ev.asset),
    action: ACTIONS[ev.aksi]?.en ?? `UNKNOWN_${ev.aksi}`,
    action_id: ACTIONS[ev.aksi]?.id ?? null,
    weight_before: Number(ev.bobotLama) / 1e9,
    weight_after: Number(ev.bobotBaru) / 1e9,
    reference_price: ev.hargaRef === 0n ? null : Number(ev.hargaRef) / 1e8,
    data_hash: ev.dataHash,
  };
}

// ---------------------------------------------------------------- ledger publik (GitHub raw): tick + id sinyal yang dikomit
export type LedgerRecord = { type: string; asof?: number; asof_date?: string; signal_ids?: string[]; targets?: Record<string, number>; lag_s?: number; emitted_utc?: string; bar_date?: string; net?: number; reason?: string; spec_sha?: string; first_asof_date?: string };

export async function ledger(bot: string): Promise<LedgerRecord[]> {
  let res: Response;
  try {
    res = await fetch(`${RAW}/ledger/paper/${bot}.jsonl`, { next: { revalidate: 120 } });
  } catch (e) {
    throw new ChainReadError(`ledger ${bot}: GitHub tak terjangkau (${e instanceof Error ? e.message : e}) - bukan berarti ledger kosong`);
  }
  if (!res.ok) throw new ChainReadError(`ledger ${bot}: HTTP ${res.status} dari GitHub - bukan berarti ledger kosong`);
  return (await res.text())
    .split("\n")
    .filter((l) => l.trim())
    .map((l) => JSON.parse(l) as LedgerRecord);
}
