// P178 (28 Okt 2026): "coba patahkan" - empat cara curang terhadap SignalAnchor yang SUNGGUHAN (chain 97), dijalankan sebagai SIMULASI (eth_call dengan
// `from` = alamat committer resmi): tanpa kunci, tanpa gas, tanpa transaksi. Yang ditampilkan adalah revert kontrak apa adanya (nama + argumen galat),
// bukan pesan buatan kami. Gagal baca chain = ChainReadError (T8), bukan "lolos".
import { BaseError, ContractFunctionRevertedError, createPublicClient, fallback, http, keccak256, parseAbi, stringToHex, type Hex } from "viem";
import { bscTestnet } from "viem/chains";
import { COMMITTER, ChainReadError, SIGNAL_ANCHOR, ascii32, closeOf, commitIdOf, lockedAt } from "./fabius-chain";

const client = createPublicClient({
  chain: bscTestnet,
  transport: fallback([http("https://bsc-testnet-rpc.publicnode.com"), http("https://bsc-testnet.publicnode.com"), http("https://bsc-testnet.drpc.org")]),
});

const ABI = parseAbi([
  "struct Signal { uint8 v; bytes32 botId; bytes32 specSha; uint64 asof; bytes32 asset; uint8 aksi; int256 bobotLama; int256 bobotBaru; uint256 hargaRef; bytes32 dataHash; }",
  "function commit(bytes32 botId, bytes32 specSha, uint64 asof, bytes32 root, uint32 n) returns (bytes32 id)",
  "function reveal(bytes32 id, Signal s, bytes32 salt, bytes32[] proof)",
  "error ZeroValue()",
  "error NotLocked()",
  "error LockedAfterBar(uint64 lockedAt, uint64 asof)",
  "error BarNotClosed(uint64 asof, uint64 nowTs)",
  "error TooLate(uint64 asof, uint64 nowTs, uint64 maxLag)",
  "error AlreadyCommitted(bytes32 id)",
  "error EmptyMismatch()",
  "error UnknownCommit(bytes32 id)",
  "error SignalMismatch()",
  "error BadProof()",
  "error AlreadyRevealed(bytes32 leaf)",
  "error TooManyReveals()",
]);

export const ATTACKS = ["late", "prelock", "respec", "extra"] as const;
export type Attack = (typeof ATTACKS)[number];

/** Bar yang sudah dikomit dengan 4 sinyal dan keempatnya sudah diungkap (dibuktikan di /verify): sasaran "tambah sinyal pemenang sesudahnya". */
const EXTRA = { bot: "B2-RS", bar: "2026-10-05" };
const DAY_S = 86_400;
const FAKE_ROOT = `0x${"11".repeat(32)}` as Hex;

export type BreakResult = {
  attack: Attack;
  bot: string;
  call: string;                // fungsi + argumen yang dicoba, dibaca manusia
  rejected: boolean;           // true = kontrak me-revert (yang diharapkan)
  error: string | null;        // nama galat kontrak, mis. "TooLate"
  args: Record<string, string>;
  from: Hex;
  contract: Hex;
  block: number;
  cast: string;                // perintah untuk mengulang sendiri dengan Foundry
  checked_utc: string;
};

const iso = (s: number) => new Date(s * 1000).toISOString().replace(".000", "");

function decodeRevert(e: unknown): { name: string; args: Record<string, string> } | null {
  if (!(e instanceof BaseError)) return null;
  const r = e.walk((x) => x instanceof ContractFunctionRevertedError);
  if (!(r instanceof ContractFunctionRevertedError) || !r.data?.errorName) return null;
  const def = ABI.find((x) => x.type === "error" && x.name === r.data!.errorName) as { inputs?: readonly { name?: string }[] } | undefined;
  const args: Record<string, string> = {};
  (r.data.args ?? []).forEach((v, i) => {
    const k = def?.inputs?.[i]?.name ?? `arg${i}`;
    const n = typeof v === "bigint" ? Number(v) : null;
    args[k] = n !== null && /asof|At|nowTs/.test(k) && n > 1_500_000_000 ? `${v} (${iso(n)})` : n !== null && k === "maxLag" ? `${v} s (${n / 3600} h)` : String(v);
  });
  return { name: r.data.errorName, args };
}

export async function runAttack(attack: Attack, bot: string, specSha: Hex, specShaOf: (bot: string) => Hex): Promise<BreakResult> {
  let block: bigint;
  try {
    block = await client.getBlockNumber();
  } catch (e) {
    throw new ChainReadError(`blockNumber: chain 97 tak terbaca (${e instanceof Error ? e.message.split("\n")[0].slice(0, 120) : String(e)})`);
  }
  const now = Math.floor(Date.now() / 1000);
  const today = Math.floor(now / DAY_S) * DAY_S;
  let call = "";
  let cast = "";
  let sim: () => Promise<unknown>;
  const B = ascii32(bot);
  if (attack === "late") {
    const asof = today - DAY_S;                                    // bar yang tutup >= 24 jam lalu, jauh lewat maxLag 12 jam
    call = `commit(${bot}, spec, asof=${iso(asof)}, root, n=1) - write yesterday's signal after the market moved`;
    cast = `cast call ${SIGNAL_ANCHOR} "commit(bytes32,bytes32,uint64,bytes32,uint32)" ${B} ${specSha} ${asof} ${FAKE_ROOT} 1 --from ${COMMITTER} --rpc-url https://bsc-testnet-rpc.publicnode.com`;
    sim = () => client.simulateContract({ address: SIGNAL_ANCHOR, abi: ABI, functionName: "commit", args: [B, specSha, BigInt(asof), FAKE_ROOT, 1], account: COMMITTER });
  } else if (attack === "prelock") {
    const locked = await lockedAt(bot, specSha);
    const asof = Math.floor((locked - DAY_S) / DAY_S) * DAY_S;    // bar SEBELUM strategi ini dikunci di LockRegistry
    call = `commit(${bot}, spec, asof=${iso(asof)}, root, n=1) - claim a signal for a day before the strategy was locked`;
    cast = `cast call ${SIGNAL_ANCHOR} "commit(bytes32,bytes32,uint64,bytes32,uint32)" ${B} ${specSha} ${asof} ${FAKE_ROOT} 1 --from ${COMMITTER} --rpc-url https://bsc-testnet-rpc.publicnode.com`;
    sim = () => client.simulateContract({ address: SIGNAL_ANCHOR, abi: ABI, functionName: "commit", args: [B, specSha, BigInt(asof), FAKE_ROOT, 1], account: COMMITTER });
  } else if (attack === "respec") {
    const edited = keccak256(stringToHex(`${bot} strategy quietly edited after the data`));
    const asof = today;                                            // bar terbaru yang sudah tutup - satu-satunya yang berubah adalah strategi
    call = `commit(${bot}, editedSpec=${edited.slice(0, 10)}…, asof=${iso(asof)}, root, n=1) - change the strategy after seeing the data`;
    cast = `cast call ${SIGNAL_ANCHOR} "commit(bytes32,bytes32,uint64,bytes32,uint32)" ${B} ${edited} ${asof} ${FAKE_ROOT} 1 --from ${COMMITTER} --rpc-url https://bsc-testnet-rpc.publicnode.com`;
    sim = () => client.simulateContract({ address: SIGNAL_ANCHOR, abi: ABI, functionName: "commit", args: [B, edited, BigInt(asof), FAKE_ROOT, 1], account: COMMITTER });
  } else {
    const spec = specShaOf(EXTRA.bot);
    const asof = closeOf(EXTRA.bar);
    const id = commitIdOf(EXTRA.bot, spec, EXTRA.bar);
    const signal = { v: 1, botId: ascii32(EXTRA.bot), specSha: spec, asof: BigInt(asof), asset: ascii32("BTCUSDT"), aksi: 1, bobotLama: 0n,
      bobotBaru: 10n ** 17n, hargaRef: 1n, dataHash: FAKE_ROOT };
    bot = EXTRA.bot;
    call = `reveal(${EXTRA.bot} ${EXTRA.bar}, extra ENTER_LONG BTCUSDT) - add a winning signal to a day that was already sealed with 4`;
    cast = `cast call ${SIGNAL_ANCHOR} "reveal(bytes32,(uint8,bytes32,bytes32,uint64,bytes32,uint8,int256,int256,uint256,bytes32),bytes32,bytes32[])" ${id} "(1,${signal.botId},${spec},${asof},${signal.asset},1,0,${signal.bobotBaru},1,${FAKE_ROOT})" ${FAKE_ROOT} "[]" --rpc-url https://bsc-testnet-rpc.publicnode.com`;
    sim = () => client.simulateContract({ address: SIGNAL_ANCHOR, abi: ABI, functionName: "reveal", args: [id, signal, FAKE_ROOT, []], account: COMMITTER });
  }
  const base = { attack, bot, call, from: COMMITTER as Hex, contract: SIGNAL_ANCHOR as Hex, block: Number(block), cast,
    checked_utc: new Date().toISOString().replace(/\.\d+Z$/, "Z") };
  try {
    await sim();
    return { ...base, rejected: false, error: null, args: {} };   // tidak boleh terjadi: berarti kontrak MENERIMA kecurangan - ditampilkan apa adanya
  } catch (e) {
    const d = decodeRevert(e);
    if (d) return { ...base, rejected: true, error: d.name, args: d.args };
    throw new ChainReadError(`simulate ${attack}: ${e instanceof Error ? e.message.split("\n")[0].slice(0, 160) : String(e)}`);
  }
}

