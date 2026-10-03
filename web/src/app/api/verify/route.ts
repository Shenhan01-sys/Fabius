// GET /api/verify?bot=B3-CARRY&bar=2026-10-02 - pemeriksaan publik satu (bot, bar) untuk halaman /verify. Kode sama dengan MCP `fabius_verify`
// (src/lib/verify.ts). Tanpa `bar`: bar terakhir yang sudah di-tick di ledger publik. Gagal baca chain/GitHub = 503 dengan alasannya (T8), bukan vonis.
import snapshot from "../../../../public/data/snapshot.json";
import { ChainReadError, ledger } from "@/lib/fabius-chain";
import type { Snapshot } from "@/lib/snapshot";
import { forwardBots, verifyBar } from "@/lib/verify";

export const runtime = "nodejs";
export const dynamic = "force-dynamic";
export const maxDuration = 60;

const s = snapshot as unknown as Snapshot;
const realDate = (v: string) => /^\d{4}-\d{2}-\d{2}$/.test(v) && new Date(`${v}T00:00:00Z`).toISOString().startsWith(v);

export async function GET(request: Request) {
  const q = new URL(request.url).searchParams;
  const bot = q.get("bot") ?? "";
  let bar = q.get("bar") ?? "";
  const bots = forwardBots(s);
  if (!bots.includes(bot)) return Response.json({ error: `bot must be one of ${bots.join(", ")}` }, { status: 400 });
  if (bar && !realDate(bar)) return Response.json({ error: "bar must be a real UTC date YYYY-MM-DD" }, { status: 400 });
  try {
    if (!bar) {
      const last = [...(await ledger(bot))].reverse().find((r) => r.type === "tick");
      if (!last?.asof_date) return Response.json({ error: `${bot}: no tick in the public ledger yet` }, { status: 404 });
      bar = last.asof_date;
    }
    const result = await verifyBar(s, bot, bar);
    return Response.json({ result }, { headers: { "Cache-Control": "no-store" } });
  } catch (e) {
    const msg = e instanceof ChainReadError ? e.message : `error: ${e instanceof Error ? e.message : String(e)}`;
    return Response.json({ error: msg }, { status: 503, headers: { "Cache-Control": "no-store" } });
  }
}
