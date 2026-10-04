// GET /api/status - kesehatan operasi hari ini untuk halaman /status dan agen (kode sama dengan MCP `fabius_status`, src/lib/status.ts).
// Tanpa kunci. Sumber yang gagal dibaca tampil sebagai lampu "unreadable" di dalam hasil (T8); 503 hanya bila seluruh pemeriksaan gagal.
import snapshot from "../../../../public/data/snapshot.json";
import type { Snapshot } from "@/lib/snapshot";
import { getStatus } from "@/lib/status";

export const runtime = "nodejs";
export const dynamic = "force-dynamic";
export const maxDuration = 60;

const s = snapshot as unknown as Snapshot;

export async function GET() {
  try {
    return Response.json({ result: await getStatus(s) }, { headers: { "Cache-Control": "no-store" } });
  } catch (e) {
    return Response.json({ error: `error: ${e instanceof Error ? e.message : String(e)}` }, { status: 503, headers: { "Cache-Control": "no-store" } });
  }
}
