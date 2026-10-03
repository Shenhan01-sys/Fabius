"use client";

import { useLang } from "../lang";
import IsoCube from "../ui/IsoCube";
import { LINKS } from "@/lib/copy";
import type { Snapshot } from "@/lib/snapshot";

// Yang tidak kami klaim: marquee (motif berulang) - batas kejujuran tampil sebesar judul, bukan catatan kaki.
export function Claims() {
  const { t } = useLang();
  const run = t.claims.repeat(3);
  return (
    <section className="mt-3 overflow-hidden rounded-[30px] bg-violet py-7 text-white">
      <div className="flex w-max animate-marquee whitespace-nowrap font-display text-[clamp(2rem,4.6vw,4rem)] font-[800] italic tracking-tight" style={{ fontStretch: "75%" }}>
        <span className="pr-6">{run}</span>
        <span className="pr-6" aria-hidden>
          {run}
        </span>
      </div>
    </section>
  );
}

export function Footer({ s }: { s: Snapshot }) {
  const { t } = useLang();
  const c = s.chain;
  const contracts: [string, string | undefined][] = [
    ["SignalAnchor", c?.signal_anchor],
    ["LockRegistry", c?.lock_registry],
    ["DecisionAnchor", c?.decision_anchor],
  ];
  const cmds = ["python -X utf8 tools/verify_signals.py", "python -X utf8 -m engine.cli ledger verify", "python -X utf8 tools/worker_watch.py"];
  return (
    <footer className="mt-3 rounded-[30px] bg-night px-6 py-16 text-white sm:px-12 lg:px-16">
      <div className="grid gap-12 lg:grid-cols-3">
        <div>
          <div className="flex items-center gap-3 font-display text-2xl font-[700]">
            <IsoCube kind="sealed" size={30} /> Fabius
          </div>
          <a href={LINKS.repo} target="_blank" rel="noreferrer" className="mt-6 inline-block font-mono text-sm text-violet-2 hover:underline">
            {t.foot.repo} ↗
          </a>
          <div className="mt-6 font-mono text-[0.7rem] leading-relaxed text-white/40">
            {t.foot.snapshot} {s.generated_utc}
            <br />
            repo {s.repo_head.slice(0, 10)} · {c ? `block #${c.block.toLocaleString("en-US")}` : s.chain_error ?? "—"}
          </div>
        </div>
        <div>
          <div className="tag text-white/45">{t.foot.contracts}</div>
          <div className="mt-4 space-y-3">
            {contracts.map(([n, a]) => (
              <a key={n} href={a ? `${LINKS.scan}${a}` : undefined} target="_blank" rel="noreferrer" className="block">
                <div className="text-sm font-semibold">{n}</div>
                <div className="break-all font-mono text-[0.72rem] text-white/50 hover:text-violet-2">{a ?? "—"}</div>
              </a>
            ))}
          </div>
        </div>
        <div>
          <div className="tag text-white/45">{t.foot.check}</div>
          <div className="mt-4 space-y-2">
            {cmds.map((x) => (
              <div key={x} className="glass-dark rounded-xl px-3 py-2 font-mono text-[0.72rem] text-white/75">
                <span className="text-violet-2">$ </span>
                {x}
              </div>
            ))}
          </div>
        </div>
      </div>
    </footer>
  );
}
