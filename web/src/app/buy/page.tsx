// /buy (P146; dulu /beli): sinyal hari ini = bot yang dipakai Fabius sekarang (aturan terkunci engine/pemilih.py dari pilihan agent analis); pembeli tidak
// memilih bot - sama dengan `/buy` tanpa argumen di Telegram. /buy/<bot> tetap untuk tautan eksplisit.
import type { Metadata } from "next";
import BeliView from "@/components/beli/BeliView";

export const metadata: Metadata = {
  title: "Buy today's signal — Fabius",
  description:
    "One signal per day: the bot Fabius trades today, chosen by a locked rule from the AI analysts' picks. Pay with x402 on BNB testnet (FAB test token, zero gas).",
};

export default function Page() {
  return <BeliView />;
}
