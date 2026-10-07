// Server MCP Fabius (P114): https://<host>/mcp - Streamable HTTP, stateless (spesifikasi 2026-07-28 + cadangan untuk klien 2025).
// Bawaan: tingkat 0, umpan bukti gratis, hanya baca. P157 (F5, F-D111): `FABIUS_MCP_BERBAYAR=hidup` (env Vercel; bawaan MATI) membuka set alat berbayar:
// gratis hanya fabius_pricing + fabius_account, sisanya dipotong dari deposit FAB lewat kunci API di header `Authorization: Bearer fabk_...`.
// Handler mode berbayar dibuat per permintaan supaya kunci pemanggil ikut ke alat (server stateless). Daftar alat: src/lib/mcp-tools.ts.
import { createMcpHandler } from "mcp-handler";
import snapshot from "../../../public/data/snapshot.json";
import { registerFabiusTools } from "@/lib/mcp-tools";
import { berbayar, kunciDari } from "@/lib/akun";
import type { Snapshot } from "@/lib/snapshot";

export const runtime = "nodejs";
export const dynamic = "force-dynamic";
export const maxDuration = 60;

const gratis = createMcpHandler((server) => registerFabiusTools(server, snapshot as unknown as Snapshot), {
  serverInfo: { name: "fabius", version: "0.1.0" },
});

async function handler(req: Request): Promise<Response> {
  if (!berbayar()) return gratis(req);
  const kunci = kunciDari(req.headers);
  return createMcpHandler((server) => registerFabiusTools(server, snapshot as unknown as Snapshot, { berbayar: true, kunci }), {
    serverInfo: { name: "fabius", version: "0.2.0" },
  })(req);
}

export { handler as GET, handler as POST, handler as DELETE };
