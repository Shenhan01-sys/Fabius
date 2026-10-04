// /status (docs/design/status.md): kesehatan operasi hari ini - dial 24 jam UTC, stasiun per bot, gas committer, detak rantai GitHub. Data live dari
// /api/status (kode sama dengan MCP `fabius_status`); halaman ini tidak memegang kunci apa pun.
import type { Metadata } from "next";
import snapshot from "../../../public/data/snapshot.json";
import StatusView from "@/components/status/StatusView";
import type { Snapshot } from "@/lib/snapshot";

export const metadata: Metadata = {
  title: "Status — Fabius",
  description: "Is the machine alive today? Ledger tick, on-chain commit and reveal, venue-rules paper, committer gas and the GitHub chain heartbeat, read live. Health, not performance.",
};

export default function Page() {
  return <StatusView s={snapshot as unknown as Snapshot} />;
}
