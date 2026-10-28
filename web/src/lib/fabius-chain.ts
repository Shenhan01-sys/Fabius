// Pembaca bukti on-chain untuk server MCP (P114). Hanya baca, tanpa kunci. Hash dihitung PERSIS seperti engine Python (`engine/sinyal.py`,
// `tools/signal_commit.py`) dan kontrak (`contracts/SignalAnchor.sol`): leaf = keccak256(abi.encode(Signal, salt)), id = keccak256(abi.encode(Signal)),
// commitId = keccak256(abi.encode(committer, botId, specSha, asof)). Prinsip T8: gagal membaca chain = GALAT (ChainReadError), tidak pernah "tidak ada".

import { createPublicClient, decodeEventLog, encodeAbiParameters, fallback, hexToString, http, keccak256, pad, parseAbi, parseAbiItem, stringToHex, toEventSelector, type Hex, type Log } from "viem";
import { bscTestnet } from "viem/chains";

export const SIGNAL_ANCHOR = "0x9B78200beFbbBe836585d31bd5b6dB32587064f3" as const;
export const LOCK_REGISTRY = "0xcF6fBF95fc04DEd8d670512CEc0723a2246Fbb0C" as const;
export const COMMITTER = "0xCA9c7322210E9a7F7d0953c862d4Ef60cC0D64A4" as const;
export const ANCHOR_DEPLOY_BLOCK = 134442917n;
const RAW = "https://raw.githubusercontent.com/Shenhan01-sys/Fabius/master";
const DAY_S = 86_400;

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

/** Saldo (tBNB) dan kepala chain 97 - untuk /status: gas committer + kesegaran. */
export async function balanceOf(addr: Hex) {
  return Number(await read("getBalance", () => client.getBalance({ address: addr }))) / 1e18;
}

export async function head() {
  const b = await read("getBlock", () => client.getBlock());
  return { block: Number(b.number), ts: Number(b.timestamp) };
}

export async function commitCount() {
  return Number(await read("commitCount", () => client.readContract({ address: SIGNAL_ANCHOR, abi: ANCHOR_ABI, functionName: "commitCount" })));
}

// P180 (28 Okt 2026): publicnode mengembalikan 0 log (BUKAN galat) untuk blok lama dan drpc gratis menolak getLogs di luar ±10k blok terakhir, jadi
// hari yang punya sinyal jatuh ke "pindai penuh sejak deploy" (±1.000 panggilan) -> 504 sesudah 60 detik. getLogs kini lewat RPC yang menyimpan riwayat log
// (onfinality, terukur: 4 reveal B2-RS bar 2026-10-05 dalam 0,5 detik; batas 10k blok/panggilan) dengan publicnode sebagai cadangan.
// P178 (28 Okt 2026): dari Vercel, onfinality kadang gagal (batas laju) lalu `fallback` diam-diam pindah ke publicnode yang menjawab 0 log -> /verify
// "0 dari 4 ungkap" di produksi. Sumber log kini daftar eksplisit TANPA publicnode, dicoba berurutan; sumber yang galat ATAU kurang hasil -> sumber berikut.
// thirdweb terukur menyimpan riwayat log (11 log blok 135176207-135176299 terbaca) dengan batas 1.000 blok/panggilan.
const LOG_SOURCES = [
  { name: "onfinality", span: 9_999n, client: createPublicClient({ chain: bscTestnet, transport: http("https://bnb-testnet.api.onfinality.io/public", { retryCount: 0, timeout: 6_000 }) }) },
  { name: "thirdweb", span: 999n, client: createPublicClient({ chain: bscTestnet, transport: http("https://97.rpc.thirdweb.com", { retryCount: 0, timeout: 8_000 }) }) },
];
const LOG_REACH = 60_000n;  // ungkap terjadi di putaran yang sama dengan komit (REVEAL_DELAY_S = 0); 60k blok (±7 jam) sudah sangat longgar

// Terukur di Vercel 28 Okt: dua getLogs paralel ke thirdweb -> batas laju, lalu ulang bawaan viem menunggu Retry-After -> fungsi habis 60 s.
// Maka panggilan log diantre satu per satu dan diulang sendiri (maks 3x, jeda 0,4/0,8 s), tanpa ulang bawaan viem.
let logQueue: Promise<unknown> = Promise.resolve();
async function logCall<T>(f: () => Promise<T>): Promise<T> {
  const run = logQueue.then(async () => {
    for (let i = 0; ; i++) {
      try {
        return await f();
      } catch (e) {
        if (i >= 2) throw e;
        await new Promise((r) => setTimeout(r, 400 * 2 ** i));
      }
    }
  });
  logQueue = run.catch(() => undefined);
  return run;
}

type LogRow = { args: Record<string, unknown>; transactionHash: Hex | null; blockNumber: bigint | null };

/** getLogs dari `start - 50` maju sampai `enough(log)` terpenuhi atau LOG_REACH habis, per sumber berurutan. Tidak cukup di semua sumber = ChainReadError. */
async function scanLogs(what: string, q: { address: Hex; event: unknown; args: Record<string, Hex> }, start: bigint, latest: bigint, enough: (n: number) => boolean) {
  const from = start > 50n ? start - 50n : start;
  const end = from + LOG_REACH > latest ? latest : from + LOG_REACH;
  const notes: string[] = [];
  for (const src of LOG_SOURCES) {
    const logs: LogRow[] = [];
    try {
      for (let a = from; a <= end && !enough(logs.length); a += src.span + 1n) {
        const b = a + src.span > end ? end : a + src.span;
        logs.push(...((await logCall(() => src.client.getLogs({ ...q, fromBlock: a, toBlock: b } as never))) as unknown as LogRow[]));
      }
      if (enough(logs.length)) return logs;
      notes.push(`${src.name} ${logs.length}`);
    } catch (e) {
      notes.push(`${src.name} galat (${e instanceof Error ? e.message.split("\n")[0].slice(0, 80) : String(e)})`);
    }
  }
  throw new ChainReadError(`getLogs ${what}: tak cukup terbaca sejak blok ${start} [${notes.join("; ")}] - RPC publik tak lengkap, bukan berarti tidak ada`);
}

/** Blok pertama dengan timestamp >= `ts`. Pencarian interpolasi (waktu blok chain 97 hampir rata, ±0,45 s) dengan langkah bagi-dua tiap putaran ke-3
 *  sebagai pengaman: ±5 getBlock alih-alih ±23 (bagi-dua murni, terukur ±8 s per panggilan dan dipanggil 3-4 kali per tur -> 504 di Vercel). */
const blockMemo = new Map<number, bigint>();   // ts lampau -> blok; tetap benar selamanya, jadi aman disimpan selama fungsi hangat
async function blockAtOrAfter(ts: number, hi: bigint): Promise<bigint> {
  const memo = blockMemo.get(ts);
  if (memo !== undefined && memo <= hi) return memo;
  const b = await searchBlock(ts, hi);
  if (b < hi) blockMemo.set(ts, b);
  return b;
}

async function searchBlock(ts: number, hi: bigint): Promise<bigint> {
  const tsOf = async (n: bigint) => Number((await read("getBlock", () => client.getBlock({ blockNumber: n }))).timestamp);
  let lo = ANCHOR_DEPLOY_BLOCK;
  let [loTs, hiTs] = await Promise.all([tsOf(lo), tsOf(hi)]);
  if (ts <= loTs) return lo;
  if (ts > hiTs) return hi;
  for (let i = 0; hi - lo > 1n; i++) {   // invarian: ts(lo) < ts <= ts(hi)
    let g = i % 3 === 2 || hiTs === loTs ? (lo + hi) / 2n : lo + (BigInt(ts - loTs) * (hi - lo)) / BigInt(hiTs - loTs);
    if (g <= lo) g = lo + 1n;
    if (g >= hi) g = hi - 1n;
    const gTs = await tsOf(g);
    if (gTs < ts) [lo, loTs] = [g, gTs];
    else [hi, hiTs] = [g, gTs];
  }
  return hi;
}

// P178 tur juri: tx komit dan tx kunci dibaca dari event-nya sendiri (bukan disalin), supaya tiap langkah tur punya bukti on-chain yang bisa diklik.
const COMMITTED = parseAbiItem("event Committed(bytes32 indexed id, address indexed committer, bytes32 indexed botId, bytes32 specSha, uint64 asof, bytes32 root, uint32 n)");
const LOCKED = parseAbiItem("event Locked(bytes32 indexed id, address indexed locker, bytes32 indexed botId, bytes32 specSha, uint64 lockedAt, string uri)");

/** Log pertama `event` sejak blok yang memuat `ts` (maju sampai LOG_REACH). Tidak ketemu = ChainReadError (T8). */
// ---------------------------------------------------------------- petunjuk tx (ledger/chain/tx-index.json, tools/tx_index.py)
// Indeks = hash tx saja, BUKAN kebenaran: tiap tx diambil strukturnya dari chain, lalu alamat kontrak + topik event dicocokkan di sini. Petunjuk yang
// hilang/tak cocok -> jatuh ke pindai getLogs di atas. Struk tx lama dilayani drpc/dataseed/thirdweb (publicnode tidak: terukur 28 Okt).
const receiptClient = createPublicClient({
  chain: bscTestnet,
  transport: fallback([http("https://bsc-testnet.drpc.org", { retryCount: 0, timeout: 6_000 }), http("https://bsc-testnet-dataseed.bnbchain.org", { retryCount: 0, timeout: 6_000 }),
    http("https://97.rpc.thirdweb.com", { retryCount: 0, timeout: 6_000 })]),
});
type TxIndex = { commits: Record<string, { tx?: Hex; block?: number; reveals: { leaf: Hex; tx: Hex; block: number }[] }>; locks: Record<string, { tx: Hex; block: number }> };

async function txIndex(): Promise<TxIndex | null> {
  try {
    const r = await fetch(`${RAW}/ledger/chain/tx-index.json`, { next: { revalidate: 300 } });
    return r.ok ? ((await r.json()) as TxIndex) : null;
  } catch {
    return null;
  }
}

/** Log `event` milik `address` dari struk tx-tx petunjuk (dibaca dari chain). Struk tak terbaca = tx itu dilewati (bukan "tidak ada"). */
async function logsFromTxs(txs: Hex[], address: Hex, event: typeof COMMITTED | typeof LOCKED | typeof REVEALED, keep: (topics: Hex[], data: Hex) => boolean) {
  const sel = toEventSelector(event).toLowerCase();
  const out: LogRow[] = [];
  for (const tx of [...new Set(txs)]) {
    const rc = await receiptClient.getTransactionReceipt({ hash: tx }).catch(() => null);
    if (!rc || rc.status !== "success") continue;
    for (const lg of rc.logs as Log[]) {
      const topics = lg.topics as Hex[];
      if (lg.address.toLowerCase() !== address.toLowerCase() || topics[0]?.toLowerCase() !== sel || !keep(topics, lg.data)) continue;
      const { args } = decodeEventLog({ abi: [event], data: lg.data, topics: topics as [Hex, ...Hex[]] });
      out.push({ args: args as Record<string, unknown>, transactionHash: lg.transactionHash, blockNumber: lg.blockNumber });
    }
  }
  return out;
}

const same = (a?: string, b?: string) => !!a && !!b && a.toLowerCase() === b.toLowerCase();

async function firstLogAt(what: string, address: Hex, event: typeof COMMITTED | typeof LOCKED, args: Record<string, Hex>, ts: number) {
  const latest = await read("blockNumber", () => client.getBlock());
  const start = await blockAtOrAfter(ts, latest.number);
  const got = await scanLogs(what, { address, event, args }, start, latest.number, (n) => n > 0);
  return { tx: got[0].transactionHash as Hex, block: Number(got[0].blockNumber) };
}

export async function commitTxOf(id: Hex, committedAt: number) {
  const hint = (await txIndex())?.commits[id.toLowerCase()];
  if (hint?.tx) {
    const got = await logsFromTxs([hint.tx], SIGNAL_ANCHOR, COMMITTED, (t) => same(t[1], id));
    if (got.length) return { tx: got[0].transactionHash as Hex, block: Number(got[0].blockNumber) };
  }
  return firstLogAt("Committed", SIGNAL_ANCHOR, COMMITTED, { id }, committedAt);
}

export async function lockTxOf(bot: string, specSha: Hex, lockedAtTs: number, committer: Hex = COMMITTER) {
  const botId = ascii32(bot);
  const hint = (await txIndex())?.locks[`${committer}|${botId}|${specSha}`.toLowerCase()];
  const mine = (t: Hex[], data: Hex) => same(t[2] && `0x${t[2].slice(-40)}`, committer) && same(t[3], botId) && same(data.slice(0, 66), specSha);
  if (hint?.tx) {
    const got = await logsFromTxs([hint.tx], LOCK_REGISTRY, LOCKED, mine);
    if (got.length) return { tx: got[0].transactionHash as Hex, block: Number(got[0].blockNumber) };
  }
  return firstLogAt("Locked", LOCK_REGISTRY, LOCKED, { locker: committer, botId }, lockedAtTs);
}

/** Event Revealed untuk satu commitId: mulai dari blok komit (dicari tepat dari `committedAt`), maju sampai LOG_REACH, per sumber log.
 *  Kurang dari `expected` sesudah itu = ChainReadError (tak terbaca), bukan "tidak ada" dan bukan pindai penuh yang berakhir timeout. */
export async function getReveals(id: Hex, committedAt: number, expected: number) {
  const hint = (await txIndex())?.commits[id.toLowerCase()];
  let logs: LogRow[] = [];
  if (hint && hint.reveals.length >= expected) logs = await logsFromTxs(hint.reveals.map((r) => r.tx), SIGNAL_ANCHOR, REVEALED, (t) => same(t[1], id));
  if (logs.length < expected) logs = await scanRevealed(id, committedAt, expected);
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

async function scanRevealed(id: Hex, committedAt: number, expected: number): Promise<LogRow[]> {
  const latest = await read("blockNumber", () => client.getBlock());
  const start = await blockAtOrAfter(committedAt, latest.number);
  return scanLogs(`Revealed (${expected})`, { address: SIGNAL_ANCHOR, event: REVEALED, args: { id } }, start, latest.number, (n) => n >= expected);
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
