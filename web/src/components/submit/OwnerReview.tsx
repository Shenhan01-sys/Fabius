"use client";

// P168 (epik 12 §5): kartu peninjau LLM "agent pemilik Fabius" di papan /submit, dari `owner_review` di `GET /bots/submissions`.
// Teks model = TEKS BIASA: dirender sebagai node teks React (di-escape), tidak pernah sebagai HTML. Peninjau hanya bisa menahan / menolak.

import { useLang } from "@/components/lang";
import type { OwnerReview as Kartu } from "@/lib/pengajuan";

const L = {
  en: {
    title: "Owner-agent review",
    notCal: "not in the path yet (calibration pending)",
    pending: "not done yet - held until it is",
    failed: "review failed - held",
    coerced: "held by a machine rule",
    note: "The LLM review can only hold or reject. LANJUT is not a slot: the 60-day forward shadow and the slot rules still decide.",
  },
  id: {
    title: "Tinjauan agent pemilik",
    notCal: "belum di jalur (menunggu kalibrasi)",
    pending: "belum selesai - ditahan sampai selesai",
    failed: "tinjauan gagal - ditahan",
    coerced: "ditahan aturan mesin",
    note: "Tinjauan LLM hanya bisa menahan atau menolak. LANJUT bukan slot: bayangan maju 60 hari dan aturan slot tetap yang memutuskan.",
  },
};

export default function OwnerReview({ r }: { r?: Kartu | null }) {
  const { lang } = useLang();
  if (!r) return null;
  const l = L[lang === "id" ? "id" : "en"];
  const state = r.state === "not calibrated" ? l.notCal : r.state === "pending" ? l.pending : null;
  return (
    <p className="mt-1 text-xs text-ink/60" title={l.note}>
      <span className="text-ink/45">{l.title}: </span>
      {state ?? <span className="font-mono">{r.verdict}</span>}
      {r.state === "failed" && <span className="text-ink/45"> · {l.failed}</span>}
      {r.state === "done" && (r.coerced?.length ?? 0) > 0 && <span className="text-ink/45"> · {l.coerced}</span>}
      {(r.tags?.length ?? 0) > 0 && <span className="font-mono text-ink/45"> · {r.tags?.join(", ")}</span>}
      {r.one_line && <span className="text-ink/55"> · {r.one_line}</span>}
    </p>
  );
}
