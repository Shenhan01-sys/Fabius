// /verify (docs/design/verify.md): pemeriksaan publik satu (bot, bar) di peramban. Data live dari /api/verify; nilai awal dari URL.
import type { Metadata } from "next";
import snapshot from "../../../public/data/snapshot.json";
import VerifyView from "@/components/verify/VerifyView";
import type { Snapshot } from "@/lib/snapshot";

export const metadata: Metadata = {
  title: "Verify a signal — Fabius",
  description: "Pick a bot and a day: this page reads the public ledger and BNB Chain, rebuilds every signal from its on-chain payload and checks it against what was sealed. No key, no gas.",
};

const realDate = (v: string) => /^\d{4}-\d{2}-\d{2}$/.test(v) && new Date(`${v}T00:00:00Z`).toISOString().startsWith(v);

export default async function Page({ searchParams }: { searchParams: Promise<Record<string, string | string[] | undefined>> }) {
  const q = await searchParams;
  const s = snapshot as unknown as Snapshot;
  const bots = s.bots.filter((b) => b.forward).map((b) => b.id);
  const busiest = [...bots].sort((a, b) => (s.ledger[b]?.n_signals ?? 0) - (s.ledger[a]?.n_signals ?? 0))[0];
  const bot = typeof q.bot === "string" && bots.includes(q.bot) ? q.bot : busiest;
  const bar = typeof q.bar === "string" && realDate(q.bar) ? q.bar : "";
  return <VerifyView s={s} bots={bots} bot={bot} bar={bar} />;
}
