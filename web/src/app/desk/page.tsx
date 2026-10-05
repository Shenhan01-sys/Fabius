// /desk (P152, F-D109): meja AI 5 menit - tiap 5 menit setiap agent analis memutuskan target posisi (paper), digabung rumus konsensus terkunci,
// dan Merkle root keputusan dikomit ke DeskAnchor sebelum siklus berakhir.
import type { Metadata } from "next";
import DeskView from "@/components/desk/DeskView";

export const metadata: Metadata = {
  title: "AI desk — Fabius",
  description: "Every 5 minutes each AI analyst decides its target positions (paper, real fees); a locked consensus formula combines them and every cycle is anchored on BNB testnet before it ends.",
};

export default function Page() {
  return <DeskView />;
}
