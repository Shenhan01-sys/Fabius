// /tour (P178): tur juri tanpa login - satu hari satu bot diikuti dari kunci strategi sampai vonis, tiap langkah = tx on-chain yang bisa diklik.
import type { Metadata } from "next";
import snapshot from "../../../public/data/snapshot.json";
import TourView from "@/components/tour/TourView";
import type { Snapshot } from "@/lib/snapshot";

export const metadata: Metadata = {
  title: "60-second tour — Fabius",
  description: "One bot, one day, five on-chain steps: strategy locked, bar closes, signals sealed, signals opened, anyone re-checks. Read live from BNB Chain testnet.",
};

export default function Page() {
  return <TourView s={snapshot as unknown as Snapshot} />;
}
