// GET /api/break?attack=late|prelock|respec|extra[&bot=B1-TREND] - P178 "coba patahkan": satu cara curang dijalankan sebagai SIMULASI (eth_call) terhadap
// SignalAnchor di chain 97 dengan `from` = committer resmi. Tanpa kunci, tanpa gas, tanpa transaksi. Hasil = revert kontrak apa adanya (src/lib/break.ts).
// Gagal baca chain = 503 dengan alasannya (T8), bukan "lolos".
import snapshot from "../../../../public/data/snapshot.json";
import { ATTACKS, runAttack, type Attack } from "@/lib/break";
import { ChainReadError } from "@/lib/fabius-chain";
import type { Snapshot } from "@/lib/snapshot";
import { forwardBots, specOf } from "@/lib/verify";

export const runtime = "nodejs";
export const dynamic = "force-dynamic";
export const maxDuration = 30;

const s = snapshot as unknown as Snapshot;

export async function GET(request: Request) {
  const q = new URL(request.url).searchParams;
  const attack = (q.get("attack") ?? "") as Attack;
  const bot = q.get("bot") ?? "B1-TREND";
  if (!ATTACKS.includes(attack)) return Response.json({ error: `attack must be one of ${ATTACKS.join(", ")}` }, { status: 400 });
  if (!forwardBots(s).includes(bot)) return Response.json({ error: `bot must be one of ${forwardBots(s).join(", ")}` }, { status: 400 });
  try {
    const result = await runAttack(attack, bot, specOf(s, bot), (b) => specOf(s, b));
    return Response.json({ result }, { headers: { "Cache-Control": "no-store" } });
  } catch (e) {
    const msg = e instanceof ChainReadError ? e.message : `error: ${e instanceof Error ? e.message : String(e)}`;
    return Response.json({ error: msg }, { status: 503, headers: { "Cache-Control": "no-store" } });
  }
}
