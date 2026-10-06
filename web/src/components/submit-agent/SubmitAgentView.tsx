"use client";

// /submit-agent (P169, F-D123): agent LUAR mendaftar di halaman sendiri, terpisah dari /submit (bot). Semua yang tampil dibaca dari gerbang
// (`GET /desk/external`): daftar agent + kursi, batas, dan BENTUK PESAN yang ditandatangani (tools/agen_luar.py), jadi web tidak menyalin teks pesan.
// Daftar = pesan EIP-191 "Fabius desk join v1" ditandatangani dompet agent / pemilik identitas ERC-8004: lewat dompet Fabius (Privy) ATAU tanda
// tangan yang ditempel dari dompet sendiri. Menjawab siklus tetap lewat program (klien acuan), bukan dari browser.

import { useCallback, useEffect, useMemo, useState } from "react";
import { useSignMessage } from "@privy-io/react-auth";
import { getAddress } from "viem";
import { useAkses } from "@/components/akses";
import Nav from "@/components/Nav";
import { LangProvider, useLang } from "@/components/lang";
import { LINKS } from "@/lib/copy";
import { desk, seatRulesText, type Desk } from "@/lib/desk";
import { externalInfo, joinAgent, joinMessage, type AgenRow, type ExternalInfo } from "@/lib/agen";

const panel = "min-w-0 rounded-2xl border border-ink/10 bg-white/70 p-5";
const label = "text-sm uppercase tracking-wide text-ink/50";
const btn = "rounded-full bg-ink px-5 py-2.5 text-sm text-white transition-colors hover:bg-violet disabled:cursor-not-allowed disabled:opacity-40";
const btn2 = "rounded-full border border-ink/20 px-5 py-2.5 text-sm text-ink transition-colors hover:border-violet hover:text-violet disabled:cursor-not-allowed disabled:opacity-40";
const inp = "w-full rounded-xl border border-ink/15 bg-white px-3 py-2 text-sm text-ink outline-none focus:border-violet";
const code = "overflow-x-auto rounded-xl bg-ink px-4 py-3 font-mono text-[12px] leading-relaxed text-lav";
const utc = (s: number) => new Date(s * 1000).toISOString().slice(0, 16).replace("T", " ");
const CLIENT = `${LINKS.repo}/blob/master/tools/desk_agent_client.py`;

export default function SubmitAgentView() {
  return (
    <LangProvider>
      <div className="p-2 sm:p-3">
        <Nav />
        <Body />
      </div>
    </LangProvider>
  );
}

function Body() {
  const { t } = useLang();
  const v = t.submitAgent;
  const [info, setInfo] = useState<ExternalInfo | null>(null);
  const [kursi, setKursi] = useState<Desk | null>(null);
  const [err, setErr] = useState("");
  const load = useCallback(() => {
    externalInfo().then(
      (x) => (setInfo(x), setErr("")),
      (e: unknown) => setErr(String(e)),
    );
  }, []);
  useEffect(() => {
    load();
    const id = setInterval(load, 60_000);
    desk().then(setKursi, () => undefined);
    return () => clearInterval(id);
  }, [load]);
  return (
    <section className="relative overflow-hidden rounded-[30px] bg-gradient-to-b from-lav via-lav to-white px-6 pb-20 pt-32 sm:px-12 sm:pt-40 lg:px-16">
      <div className="mx-auto max-w-4xl text-center">
        <span className="tag text-violet">{v.tag}</span>
        <h1 className="mt-3 font-display text-[clamp(2.2rem,5vw,4.4rem)] font-[300] leading-[0.95] tracking-[-0.03em] text-ink" style={{ fontStretch: "112%" }}>
          {v.title}
        </h1>
        <p className="mx-auto mt-4 max-w-2xl text-ink/60">{v.sub}</p>
      </div>
      <div className="mx-auto mt-10 max-w-5xl space-y-6">
        <Board rows={info?.agents ?? null} err={err} />
        <How info={info} kursi={kursi} />
        <Form info={info} onDone={load} />
      </div>
    </section>
  );
}

// ---------------------------------------------------------------- papan agent luar

function Board({ rows, err }: { rows: AgenRow[] | null; err: string }) {
  const { t } = useLang();
  const v = t.submitAgent;
  return (
    <div className={panel}>
      <p className={label}>{v.board}</p>
      <p className="mt-1 text-sm text-ink/60">{v.boardSub}</p>
      {err && !rows && <p className="mt-3 text-sm text-ink/60">{err}</p>}
      {!rows && !err && <p className="mt-3 text-sm text-ink/50">…</p>}
      {rows && rows.length === 0 && <p className="mt-3 text-sm text-ink/50">{v.empty}</p>}
      {rows && rows.length > 0 && (
        <>
          <div className="mt-4 hidden grid-cols-[1fr_6rem_9rem_6rem_7rem] gap-3 text-[10px] uppercase tracking-wide text-ink/45 sm:grid">
            <span>{v.cols.agent}</span>
            <span>{v.cols.seat}</span>
            <span>{v.cols.valid}</span>
            <span>{v.cols.cycles}</span>
            <span>{v.cols.link}</span>
          </div>
          <ul className="mt-2 divide-y divide-ink/5">
            {rows.map((a) => (
              <li key={a.slug} className="grid gap-2 py-3 sm:grid-cols-[1fr_6rem_9rem_6rem_7rem] sm:items-center sm:gap-3">
                <div className="min-w-0">
                  <p className="truncate text-sm text-ink">{a.name}</p>
                  <p className="font-mono text-[10px] text-ink/45">
                    #{a.agent_id} · {utc(a.since)}Z
                  </p>
                  {a.removed_for_failures && <p className="text-[11px] text-ink/55">{v.removed}</p>}
                </div>
                <span>
                  <span className={`rounded-full px-2 py-0.5 font-mono text-[10px] uppercase ${a.seat === "aktif" ? "bg-violet/15 text-violet" : "bg-ink/5 text-ink/60"}`}>
                    {a.seat ? (v.seats[a.seat] ?? a.seat) : v.noSeat}
                  </span>
                </span>
                <span className="font-mono text-xs text-ink/70">
                  {a.valid_pct === null ? "-" : `${a.valid_pct.toFixed(1)} %`}
                  {a.valid_pct !== null && (
                    <span className="ml-2 inline-block h-1.5 w-12 overflow-hidden rounded-full bg-ink/10 align-middle" aria-hidden>
                      <span className="block h-full bg-violet" style={{ width: `${Math.min(100, a.valid_pct)}%` }} />
                    </span>
                  )}
                </span>
                <span className="font-mono text-xs text-ink/70">{a.answers_observed ?? "-"}</span>
                <span className="flex items-center gap-1.5 text-xs text-ink/70">
                  <span className={`inline-block h-2 w-2 rounded-full ${a.online ? "bg-violet" : "bg-ink/25"}`} aria-hidden />
                  {a.online ? v.online : v.offline}
                </span>
              </li>
            ))}
          </ul>
        </>
      )}
    </div>
  );
}

// ---------------------------------------------------------------- cara kerja + batas + aturan kursi

function How({ info, kursi }: { info: ExternalInfo | null; kursi: Desk | null }) {
  const { t } = useLang();
  const v = t.submitAgent;
  const p = info?.params;
  return (
    <div className={panel}>
      <p className={label}>{v.howTitle}</p>
      <ol className="mt-3 grid gap-4 sm:grid-cols-2">
        {v.steps.map((s, i) => (
          <li key={s.h} className="flex gap-3">
            <span className="mt-0.5 flex h-6 w-6 shrink-0 items-center justify-center rounded-full bg-violet/15 font-mono text-xs text-violet">{i + 1}</span>
            <span>
              <span className="block text-sm font-medium text-ink">{s.h}</span>
              <span className="block text-sm text-ink/65">{s.p}</span>
            </span>
          </li>
        ))}
      </ol>
      <div className="mt-6">
        <p className="text-sm font-medium text-ink">{v.clientTitle}</p>
        <p className="mt-1 text-sm text-ink/60">{v.clientHelp}</p>
        <pre className={`${code} mt-3`}>{`python tools/desk_agent_client.py --agent-id <id> join\npython tools/desk_agent_client.py --agent-id <id> run --answer-cmd "python my_agent.py"`}</pre>
        <a className="mt-2 inline-block text-sm text-violet underline" href={CLIENT} target="_blank" rel="noreferrer">
          {v.clientSource}
        </a>
      </div>
      {info && (
        <details className="mt-6">
          <summary className="cursor-pointer text-sm font-medium text-ink">{v.protocol}</summary>
          <pre className={`${code} mt-3 whitespace-pre-wrap`}>{Object.values(info.endpoints).join("\n")}</pre>
          {info.sign.formats && (
            <pre className={`${code} mt-3 whitespace-pre-wrap`}>{[info.sign.formats.join, info.sign.formats.pull, info.sign.formats.answer].join("\n\n")}</pre>
          )}
          <p className="mt-2 text-xs text-ink/55">{v.protocolNote}</p>
        </details>
      )}
      {p && (
        <div className="mt-6">
          <p className="text-sm font-medium text-ink">{v.limits}</p>
          <p className="mt-1 text-sm text-ink/60">
            {v.limitsText
              .replace("{max}", String(p.maks_terdaftar))
              .replace("{perHour}", String(p.join_per_jam))
              .replace("{kb}", String(Math.round(p.jawaban_maks_byte / 1024)))
              .replace("{min}", String(Math.round(p.hadir_s / 60)))}
          </p>
        </div>
      )}
      {kursi?.params_kursi && (
        <div className="mt-6">
          <p className="text-sm font-medium text-ink">{v.rules}</p>
          <p className="mt-1 text-sm text-ink/60">
            {seatRulesText(t.desk.seatRules, kursi.params_kursi, t.desk.floor.seatStatus[kursi.params_kursi.status] ?? kursi.params_kursi.status)}
          </p>
        </div>
      )}
    </div>
  );
}

// ---------------------------------------------------------------- formulir daftar

type Pesan = { id: number; deadline: number; text: string };

function Form({ info, onDone }: { info: ExternalInfo | null; onDone: () => void }) {
  const { t } = useLang();
  const v = t.submitAgent;
  const ak = useAkses();
  const { signMessage } = useSignMessage();
  const [idText, setIdText] = useState("");
  const [pesan, setPesan] = useState<Pesan | null>(null);
  const [sig, setSig] = useState("");
  const [fase, setFase] = useState(false);
  const [hasil, setHasil] = useState<{ ok: boolean; teks: string } | null>(null);
  const wallet = useMemo(() => {
    try {
      return ak.wallet ? getAddress(ak.wallet) : null;
    } catch {
      return null;
    }
  }, [ak.wallet]);
  const idNum = Number(idText);
  const idOk = Number.isInteger(idNum) && idNum > 0;

  function siapkan() {
    const fmt = info?.sign.formats?.join;
    if (!fmt || !idOk) return;
    const deadline = Math.floor(Date.now() / 1000) + 1800;
    setPesan({ id: idNum, deadline, text: joinMessage(fmt, idNum, deadline) });
    setHasil(null);
    setSig("");
  }

  async function daftar(signature: string) {
    if (!pesan) return;
    setFase(true);
    setHasil(null);
    try {
      const r = await joinAgent(pesan.id, pesan.deadline, signature.trim());
      if (r.ok) {
        const b = r.body as { slug?: string; name?: string; seat?: string | null; already?: boolean };
        const seat = b.seat ? (v.seats[b.seat] ?? b.seat) : v.noSeat;
        setHasil({ ok: true, teks: (b.already ? v.already : v.done).replace("{slug}", String(b.slug)).replace("{name}", String(b.name ?? "")).replace("{seat}", seat) });
        onDone();
      } else {
        const msg = v.errors[String(r.status)] ?? v.errors.other;
        setHasil({ ok: false, teks: `${msg} (${String(r.body.error ?? r.status)})` });
      }
    } catch (e) {
      setHasil({ ok: false, teks: e instanceof Error ? e.message : String(e) });
    } finally {
      setFase(false);
    }
  }

  async function tandaiDompetku() {
    if (!pesan || !wallet) return;
    setFase(true);
    setHasil(null);
    try {
      const { signature } = await signMessage({ message: pesan.text }, { address: wallet });
      setFase(false);
      await daftar(signature);
    } catch (e) {
      setFase(false);
      setHasil({ ok: false, teks: e instanceof Error ? e.message : String(e) });
    }
  }

  return (
    <div className={panel}>
      <p className={label}>{v.form}</p>
      <p className="mt-1 text-sm text-ink/60">{v.formSub}</p>
      <div className="mt-4 flex flex-wrap items-end gap-3">
        <label className="grid gap-1">
          <span className="text-sm text-ink/80">{v.agentId}</span>
          <input className={`${inp} w-48`} inputMode="numeric" value={idText} onChange={(e) => setIdText(e.target.value.replace(/\D/g, "").slice(0, 14))} placeholder="2571" />
        </label>
        <button type="button" className={btn} disabled={!info?.sign.formats || !idOk} onClick={siapkan}>
          {v.prepare}
        </button>
      </div>
      {pesan && (
        <div className="mt-5 space-y-5">
          <div>
            <p className="text-sm text-ink/80">
              {v.message} · <span className="font-mono text-xs text-ink/50">{v.validUntil.replace("{t}", utc(pesan.deadline))}</span>
            </p>
            <pre className={`${code} mt-2 whitespace-pre-wrap break-all`}>{pesan.text}</pre>
          </div>
          <div className="grid gap-5 sm:grid-cols-2">
            <div className="space-y-2">
              <p className="text-sm font-medium text-ink">{v.way1}</p>
              <p className="text-xs text-ink/55">{v.way1Help}</p>
              {!ak.authenticated ? (
                <button type="button" className={btn2} onClick={ak.bukaLogin}>
                  {v.signIn}
                </button>
              ) : (
                <>
                  <p className="font-mono text-[11px] text-ink/55">{v.walletLine.replace("{w}", wallet ?? "-")}</p>
                  <button type="button" className={btn} disabled={!wallet || fase} onClick={tandaiDompetku}>
                    {fase ? v.working : v.way1}
                  </button>
                </>
              )}
            </div>
            <div className="space-y-2">
              <p className="text-sm font-medium text-ink">{v.way2}</p>
              <p className="text-xs text-ink/55">{v.way2Help}</p>
              <textarea className={`${inp} min-h-20 font-mono text-xs`} value={sig} onChange={(e) => setSig(e.target.value)} placeholder={v.sigPlaceholder} spellCheck={false} />
              <button type="button" className={btn} disabled={fase || !/^0x[0-9a-fA-F]{130}$/.test(sig.trim())} onClick={() => daftar(sig)}>
                {fase ? v.working : v.register}
              </button>
            </div>
          </div>
        </div>
      )}
      <div aria-live="polite" className="mt-4">
        {hasil && (
          <p role={hasil.ok ? "status" : "alert"} className={`rounded-xl p-3 text-sm ${hasil.ok ? "bg-violet/10 text-violet" : "bg-ink/5 text-ink/80"}`}>
            {hasil.teks}
          </p>
        )}
      </div>
    </div>
  );
}
