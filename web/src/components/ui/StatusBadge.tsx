"use client";

// Label bot (F-D95): INTI = penghuni slot identitas buku (pilihan builder), SEMENTARA = berjalan terbuka, bisa diganti bot yang memenuhi kriteria.
// Vonis gerbang v1 yang tercatat ditampilkan di sampingnya apa adanya - INTI bukan bukti terbaik (B1 pun TOLAK di v1).
import { useLang } from "../lang";
import type { Bot } from "@/lib/snapshot";

export default function StatusBadge({ b, dark = false, note = false, gate = true }: { b: Bot; dark?: boolean; note?: boolean; gate?: boolean }) {
  const { t } = useLang();
  if (!b.status) return null;
  const core = b.status === "INTI";
  const pill = core
    ? "bg-violet text-white"
    : dark
      ? "border border-dashed border-white/40 text-white/80"
      : "border border-dashed border-ink/35 text-ink/70";
  return (
    <span className="inline-flex flex-wrap items-center gap-1.5 align-middle">
      <span className={`rounded-full px-2 py-0.5 font-mono text-[0.6rem] font-bold uppercase tracking-wider ${pill}`} title={t.label.note[b.status]}>
        {t.label[b.status]}
      </span>
      {gate && b.gate_v1 && (
        <span className={`font-mono text-[0.6rem] ${dark ? "text-white/45" : "text-ink/45"}`}>
          {t.label.gate} {t.label.verdict[b.gate_v1] ?? b.gate_v1}
        </span>
      )}
      {note && <span className={`basis-full text-[0.78rem] ${dark ? "text-white/55" : "text-ink/55"}`}>{t.label.note[b.status]}</span>}
    </span>
  );
}
