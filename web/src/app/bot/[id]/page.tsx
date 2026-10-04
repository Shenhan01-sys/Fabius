// /bot/[id] (docs/design/bot.md): satu bot = satu mesin terkunci. Spesifikasi, kunci, F-D16, pembunuh dari snapshot build; buku paper + hari terbaru
// dibaca LIVE dari ledger publik (GitHub raw) di server. Gagal baca = galat yang terlihat di halaman, bukan "flat" (T8).
import type { Metadata } from "next";
import { notFound, redirect } from "next/navigation";
import snapshot from "../../../../public/data/snapshot.json";
import BotView, { type Exec, type ExecRow, type Live } from "@/components/bot/BotView";
import { ledger } from "@/lib/fabius-chain";
import type { Snapshot } from "@/lib/snapshot";

export const dynamic = "force-dynamic";

const s = snapshot as unknown as Snapshot;
const find = (id: string) => s.bots.find((b) => b.id.toLowerCase() === id.toLowerCase());

export async function generateMetadata({ params }: { params: Promise<{ id: string }> }): Promise<Metadata> {
  const b = find(decodeURIComponent((await params).id));
  if (!b) return { title: "Bot not found — Fabius" };
  return {
    title: `${b.id} — Fabius`,
    description: `${b.id}: a locked trading rule (${b.param}). Spec hash, on-chain locks, the paper book, day-by-day proof and the kill rule. Paper only; no profit claims.`,
  };
}

async function readLive(id: string): Promise<Live> {
  try {
    const recs = await ledger(id);
    const ticks = recs.filter((r) => r.type === "tick" && r.asof_date);
    const last = ticks.at(-1);
    const held = (t: Record<string, number> = {}) => Object.values(t).filter((w) => Math.abs(w) > 1e-12).length;
    return {
      ok: true,
      read_utc: new Date().toISOString().slice(0, 19) + "Z",
      ticks: ticks.map((t) => ({ date: t.asof_date!, signals: t.signal_ids?.length ?? 0, held: held(t.targets), lag_s: t.lag_s ?? null })),
      gaps: recs.filter((r) => r.type === "gap" && r.asof_date).map((r) => r.asof_date!),
      latest: last
        ? { date: last.asof_date!, emitted_utc: last.emitted_utc ?? null, signals: last.signal_ids?.length ?? 0, targets: last.targets ?? {}, prev: ticks.at(-2)?.targets ?? {} }
        : null,
    };
  } catch (e) {
    return { ok: false, error: e instanceof Error ? e.message : String(e) };
  }
}

const RAW = process.env.FABIUS_RAW_BASE || "https://raw.githubusercontent.com/Shenhan01-sys/Fabius/master"; // override hanya untuk uji lokal

/** Satu ledger eksekusi (P119; ditulis rantai GitHub dari umpan Gist). null = berkas belum ada. */
async function readVenue(id: string, venue: string): Promise<ExecRow[] | null> {
  const res = await fetch(`${RAW}/ledger/eksekusi/${venue}/${id}.jsonl`, { next: { revalidate: 120 } });
  if (res.status === 404) return null;
  if (!res.ok) throw new Error(`ledger eksekusi ${venue}: HTTP ${res.status} dari GitHub - bukan berarti tidak ada eksekusi`);
  return (await res.text())
    .split("\n")
    .filter((l) => l.trim())
    .map((l) => JSON.parse(l) as ExecRow);
}

/** Demo (`binance-demo`) + uang NYATA (`binance-live`, canary P133). Keduanya tidak ada = section tidak tampil. */
async function readExec(id: string): Promise<Exec> {
  try {
    const [demo, real] = await Promise.all([readVenue(id, "binance-demo"), readVenue(id, "binance-live")]);
    if (demo === null && real === null) return null;
    const rows = [...(demo ?? []), ...(real ?? [])].sort((a, b) => a.bar.localeCompare(b.bar) || a.mode.localeCompare(b.mode));
    return { ok: true, rows };
  } catch (e) {
    return { ok: false, error: e instanceof Error ? e.message : String(e) };
  }
}

export default async function Page({ params }: { params: Promise<{ id: string }> }) {
  const raw = decodeURIComponent((await params).id);
  const b = find(raw);
  if (!b) notFound();
  if (b.id !== raw) redirect(`/bot/${b.id}`);
  const [live, exec] = b.forward ? await Promise.all([readLive(b.id), readExec(b.id)]) : [null, null];
  return <BotView s={s} id={b.id} live={live} exec={exec} />;
}
