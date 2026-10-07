"use client";

// P167b / P167c: panel jenis `code` (editor kode privat) dan `feed` (aturan komit maju) di /submit. Keduanya DIBANGKITKAN dari skema gerbang
// (`GET /bots/schema` -> `code`, `feed`); validasi berwenang tetap di gerbang. `code` tertutup sampai builder menyetujui jalur privat.

import { useEffect, useState } from "react";
import { useLang } from "@/components/lang";
import type { FeedInfo } from "@/lib/feed";
import { paramsDari, shaKode, ukuran, type CodeInfo } from "@/lib/kode";

const box = "rounded-2xl border border-ink/10 bg-white/60 p-4";
const cap = "text-xs uppercase tracking-wide text-ink/50";
const mono = "font-mono text-[11px] text-ink/70";

export function CodeEditor({ info, value, onChange }: { info: CodeInfo; value: string; onChange: (s: string) => void }) {
  const { t } = useLang();
  const v = t.submit.code;
  const [sha, setSha] = useState("");
  useEffect(() => {
    let live = true;
    shaKode(value).then((s) => live && setSha(s));
    return () => {
      live = false;
    };
  }, [value]);
  const n = ukuran(value);
  const params = paramsDari(value);
  return (
    <div className={`${box} space-y-3`}>
      <p className="rounded-xl bg-ink/5 p-2 text-xs text-ink/70">
        {v.trust.replace("{label}", info.label)} {v.reviewer}
      </p>
      <textarea
        aria-label={v.editor}
        className="min-h-72 w-full rounded-xl border border-ink/15 bg-white p-3 font-mono text-xs text-ink outline-none focus:border-violet disabled:opacity-60"
        spellCheck={false}
        value={value}
        disabled={!info.open}
        onChange={(e) => onChange(e.target.value)}
      />
      <div className="grid gap-1 sm:grid-cols-3">
        <p className={mono}>
          {v.size}: {n}/{info.max_bytes} B{n > info.max_bytes ? " ✕" : ""}
        </p>
        <p className={`${mono} truncate`}>sha {sha.slice(0, 18)}…</p>
        <p className={mono}>PARAMS: {params ? Object.entries(params).map(([k, x]) => `${k}=${x}`).join(", ") || "—" : v.paramsUnread}</p>
      </div>
      <p className="text-xs text-ink/55">
        <span className={cap}>{v.allowed}</span> import {info.imports.join(", ")} · {info.builtins.join(" ")}
      </p>
      <p className="text-xs text-ink/55">{v.publicCopy}</p>
      {!info.open && <p className="text-xs font-medium text-ink/70">{v.closed}</p>}
    </div>
  );
}

export function FeedPanel({ info }: { info: FeedInfo }) {
  const { t } = useLang();
  const v = t.submit.feed;
  return (
    <div className={`${box} space-y-2 text-sm text-ink/75`}>
      <p className="rounded-xl bg-ink/5 p-2 text-xs text-ink/70">{v.trust.replace("{label}", info.label)}</p>
      <ol className="list-decimal space-y-1 pl-5 text-xs">
        <li>{v.step1}</li>
        <li>{v.step2.replace("{m}", String(info.commit_cutoff_s / 60))}</li>
        <li>{v.step3.replace("{ppm}", String(info.ppm))}</li>
        <li>{v.step4.replace("{label}", info.anchor_label)}</li>
        <li>{v.step5.replace("{d}", String(info.shadow_days))}</li>
      </ol>
      <p className="text-xs text-ink/55">{v.gates}</p>
      <p className={mono}>{info.routes.join(" · ")}</p>
    </div>
  );
}
