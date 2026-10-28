// GET /api/tour[?bot=&bar=] - P178 tur juri: satu (bot, bar) dari kunci strategi sampai vonis, tiap langkah dengan tx on-chain-nya (src/lib/tour.ts).
// Bawaan = B2-RS bar 2026-10-05 (4 sinyal, SAH). Gagal baca chain/GitHub = 503 dengan alasannya (T8), bukan vonis.
import snapshot from "../../../../public/data/snapshot.json";
import { ChainReadError } from "@/lib/fabius-chain";
import type { Snapshot } from "@/lib/snapshot";
import { TOUR, buildTour } from "@/lib/tour";
import { forwardBots } from "@/lib/verify";

export const runtime = "nodejs";
export const dynamic = "force-dynamic";
export const maxDuration = 60;

const s = snapshot as unknown as Snapshot;
const realDate = (v: string) => /^\d{4}-\d{2}-\d{2}$/.test(v) && new Date(`${v}T00:00:00Z`).toISOString().startsWith(v);

export async function GET(request: Request) {
  const q = new URL(request.url).searchParams;
  const bot = q.get("bot") ?? TOUR.bot;
  const bar = q.get("bar") ?? TOUR.bar;
  if (!forwardBots(s).includes(bot)) return Response.json({ error: `bot must be one of ${forwardBots(s).join(", ")}` }, { status: 400 });
  if (!realDate(bar)) return Response.json({ error: "bar must be a real UTC date YYYY-MM-DD" }, { status: 400 });
  try {
    const result = await buildTour(s, bot, bar);
    return Response.json({ result }, { headers: { "Cache-Control": "no-store" } });
  } catch (e) {
    const msg = e instanceof ChainReadError ? e.message : `error: ${e instanceof Error ? e.message : String(e)}`;
    return Response.json({ error: msg }, { status: 503, headers: { "Cache-Control": "no-store" } });
  }
}
