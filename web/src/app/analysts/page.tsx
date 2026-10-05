// /analysts (P145, F-D104; dulu /analis): pilihan agent analis AI + papan peringkat untuk semua orang; alasan lengkap + hash untuk akun yang login dan membeli
// >= 1 sinyal dalam 7 hari terakhir. Juga dibuka sebagai Telegram Mini App dari /analysts di bot Fabius.
import type { Metadata } from "next";
import AnalisView from "@/components/analis/AnalisView";

export const metadata: Metadata = {
  title: "AI analysts — Fabius",
  description:
    "Which locked bot each AI analyst agent (ERC-8004) picks per daily bar, committed on BNB testnet before the close and scored from the public ledger. Full reasoning for signed-in buyers.",
};

export default function Page() {
  return <AnalisView />;
}
