// Server MCP Fabius (P114): https://<host>/mcp - Streamable HTTP, stateless (spesifikasi 2026-07-28 + cadangan untuk klien 2025).
// Tingkat 0 saja: umpan bukti gratis, hanya baca. Daftar alat: src/lib/mcp-tools.ts.
import { createMcpHandler } from "mcp-handler";
import snapshot from "../../../public/data/snapshot.json";
import { registerFabiusTools } from "@/lib/mcp-tools";
import type { Snapshot } from "@/lib/snapshot";

export const runtime = "nodejs";
export const dynamic = "force-dynamic";
export const maxDuration = 60;

const handler = createMcpHandler((server) => registerFabiusTools(server, snapshot as unknown as Snapshot), {
  serverInfo: { name: "fabius", version: "0.1.0" },
});

export { handler as GET, handler as POST, handler as DELETE };
