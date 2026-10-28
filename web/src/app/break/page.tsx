// /break (P178): coba curangi Fabius - empat kecurangan dijalankan sebagai simulasi terhadap kontrak sungguhan; yang tampil = revert kontrak apa adanya.
import type { Metadata } from "next";
import snapshot from "../../../public/data/snapshot.json";
import BreakView from "@/components/break/BreakView";
import type { Snapshot } from "@/lib/snapshot";

export const metadata: Metadata = {
  title: "Try to cheat — Fabius",
  description: "Four ways to rewrite a trading track record, run as simulations against the real SignalAnchor contract on BNB Chain testnet. No key, no gas, no transaction: you see the contract's own rejection.",
};

export default function Page() {
  return <BreakView s={snapshot as unknown as Snapshot} />;
}
