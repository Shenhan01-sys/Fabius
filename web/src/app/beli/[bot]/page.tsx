// /beli/<bot> (P138c): beli paket sinyal satu bot dengan x402 di testnet 97 (Privy: Google / Telegram / email, embedded wallet, nol gas).
// Juga dibuka sebagai Telegram Mini App dari bot Fabius (tautan `?tg=` bertanda: paket ikut dikirim ke chat).
import type { Metadata } from "next";
import { notFound } from "next/navigation";
import snapshot from "../../../../public/data/snapshot.json";
import BeliView from "@/components/beli/BeliView";
import type { Snapshot } from "@/lib/snapshot";

const s = snapshot as unknown as Snapshot;
const find = (id: string) => s.bots.find((b) => b.id.toLowerCase() === id.toLowerCase() && b.forward && s.ledger[b.id]);

export async function generateMetadata({ params }: { params: Promise<{ bot: string }> }): Promise<Metadata> {
  const b = find(decodeURIComponent((await params).bot));
  return {
    title: b ? `Buy ${b.id} signal — Fabius` : "Bot not found — Fabius",
    description: "Pay per signal with x402 on BNB testnet (FAB test token, zero gas): position intents plus on-chain commit and ERC-8004 validation.",
  };
}

export default async function Page({ params }: { params: Promise<{ bot: string }> }) {
  const b = find(decodeURIComponent((await params).bot));
  if (!b) notFound();
  return <BeliView bot={b.id} />;
}
