"use client";

// /analysts (P145, F-D104; rute English P146): tiap pilihan agent analis digambar sebagai slip bersegel - bot + keyakinan agent + reasonHash terlihat semua orang
// (semuanya sudah on-chain); isi alasan terbuka hanya untuk akun yang login DAN membeli >= 1 sinyal dalam 7 hari (gerbang memeriksa token akses
// Privy + catatan pembelian). Papan peringkat = selisih bps vs bot identitas, digambar sebagai batang dari sumbu nol.
// Agent LUAR (P151, F-D107) ikut tampil dengan label "external" dan panel cara bergabung; mereka belum menentukan bot aktif.

import Link from "next/link";
import Script from "next/script";
import { useEffect, useRef, useState } from "react";
import { PrivyProvider, usePrivy } from "@privy-io/react-auth";
import Nav from "@/components/Nav";
import { LangProvider, useLang } from "@/components/lang";
import { LINKS } from "@/lib/copy";
import { GATE, PRIVY_APP_ID, PRIVY_CONFIG } from "@/lib/x402-buy";
import { lengkap, publik, short, utc, type AnalisRec, type Lengkap, type PapanRow, type Publik } from "@/lib/analis";

export default function AnalisView() {
  const [scriptDone, setScriptDone] = useState(false);
  return (
    <LangProvider>
      <Script src="https://telegram.org/js/telegram-web-app.js" strategy="afterInteractive" onReady={() => setScriptDone(true)} onError={() => setScriptDone(true)} />
      <div className="p-2 sm:p-3">
        <Nav />
        <Hero>
          {scriptDone ? (
            <PrivyProvider appId={PRIVY_APP_ID} config={PRIVY_CONFIG}>
              <Board />
            </PrivyProvider>
          ) : (
            <Loading />
          )}
        </Hero>
      </div>
    </LangProvider>
  );
}

function Loading() {
  const { t } = useLang();
  return <p className="text-ink/50">{t.analis.loading}</p>;
}

function Hero({ children }: { children: React.ReactNode }) {
  const { t } = useLang();
  const v = t.analis;
  return (
    <section className="relative overflow-hidden rounded-[30px] bg-gradient-to-b from-lav via-lav to-white px-6 pb-20 pt-32 sm:px-12 sm:pt-40 lg:px-16">
      <div className="mx-auto max-w-4xl text-center">
        <span className="tag text-violet">{v.tag}</span>
        <h1 className="mt-3 font-display text-[clamp(2.2rem,5vw,4.4rem)] font-[300] leading-[0.95] tracking-[-0.03em] text-ink" style={{ fontStretch: "112%" }}>
          {v.title}
        </h1>
        <p className="mx-auto mt-4 max-w-2xl text-ink/60">{v.sub}</p>
      </div>
      <div className="mx-auto mt-10 max-w-6xl space-y-6">{children}</div>
    </section>
  );
}

const btn = "inline-block rounded-full bg-ink px-5 py-2.5 text-sm text-white transition hover:bg-violet disabled:cursor-not-allowed disabled:opacity-40";
const panel = "rounded-2xl border border-ink/10 bg-white/70 p-5";
const label = "text-sm uppercase tracking-wide text-ink/50";

function Board() {
  const { t } = useLang();
  const v = t.analis;
  const { ready, authenticated, login, logout, getAccessToken } = usePrivy();
  const [pub, setPub] = useState<Publik | null>(null);
  const [err, setErr] = useState("");
  const [full, setFull] = useState<Lengkap | null>(null);
  const tokFn = useRef(getAccessToken);
  useEffect(() => {
    tokFn.current = getAccessToken;
  }, [getAccessToken]);

  useEffect(() => {
    publik().then(setPub, (e: unknown) => setErr(String(e)));
  }, []);
  useEffect(() => {
    if (!ready || !authenticated) return;
    let live = true;
    tokFn.current()
      .then((tok) => (tok ? lengkap(tok) : ({ ok: false, status: 401, error: "no access token" } as Lengkap)))
      .then(
        (r) => live && setFull(r),
        (e: unknown) => live && setFull({ ok: false, status: 0, error: String(e) }),
      );
    return () => {
      live = false;
    };
  }, [ready, authenticated]);

  if (err) return <p className="text-sm text-ink/70">{v.error}: {err}</p>;
  if (!pub) return <Loading />;

  const shown = authenticated ? full : null;
  const open = shown?.ok === true;
  const recs = open ? shown.pilihan : pub.pilihan;
  const bars = [...new Set(recs.map((r) => r.alasan.bar_close))].sort((a, b) => b - a);
  const latest = bars[0];
  const anchor = (open ? shown.anchor : undefined) ?? pub.anchor;
  const nowName: Record<number, string> = Object.fromEntries(pub.papan.map((p) => [p.agent_id, p.nama ?? p.agent]));

  return (
    <>
      <div className="grid gap-6 lg:grid-cols-2">
        <div className={panel}>
          <p className={label}>{v.active}</p>
          <p className="mt-2 font-display text-4xl font-[300]">{pub.aktif.bot}</p>
          <p className="mt-2 text-sm text-ink/60">
            {v.activeRule}: {pub.aktif.alasan_en ?? "-"}
          </p>
        </div>

        <div className={panel}>
          <p className={label}>{v.accessTitle}</p>
          <p className="mt-2 text-sm text-ink/70">{v.accessSub}</p>
          <div className="mt-3">
            {!ready ? (
              <p className="text-ink/50">{v.loading}</p>
            ) : !authenticated ? (
              <button className={btn} onClick={login}>
                {v.signIn}
              </button>
            ) : !shown ? (
              <p className="text-ink/50">{v.checking}</p>
            ) : shown.ok ? (
              <p className="text-sm">
                <span className="font-medium text-violet">{v.unlocked.replace("{d}", utc(shown.akses.berlaku_sampai))}</span>
                <span className="text-ink/60"> · {v.boughtWith.replace("{bot}", shown.akses.pembelian_terakhir.bot).replace("{bar}", shown.akses.pembelian_terakhir.bar)}</span>
              </p>
            ) : shown.status === 402 ? (
              <div className="flex flex-wrap items-center gap-3">
                <p className="text-sm text-ink/80">
                  {v.needBuy}
                  {shown.dompet?.[0] && <span className="block font-mono text-xs text-ink/50">{v.checked.replace("{w}", short(shown.dompet[0]))}</span>}
                </p>
                <Link className={btn} href="/buy">
                  {v.buy}
                </Link>
              </div>
            ) : (
              <p className="break-all text-sm text-ink/70">
                {v.error}: {shown.error}
              </p>
            )}
            {authenticated && (
              <button className="mt-3 block text-sm text-ink/50 underline" onClick={logout}>
                {v.signOut}
              </button>
            )}
          </div>
        </div>
      </div>

      {latest == null ? (
        <p className="text-ink/60">{v.noPicks}</p>
      ) : (
        bars.map((bc, i) => (
          <div key={bc}>
            <p className={label}>{(i === 0 ? v.picksFor : v.earlier).replace("{d}", utc(bc))}</p>
            <div className="mt-3 grid gap-4 sm:grid-cols-2">
              {recs
                .filter((r) => r.alasan.bar_close === bc)
                .map((r) => (
                  <Slip key={`${r.agent}-${bc}`} r={r} open={open} sealed={authenticated ? v.sealedBuy : v.sealed} now={nowName[r.alasan.agent_id]} />
                ))}
            </div>
          </div>
        ))
      )}

      <Papan rows={pub.papan} />

      <div className={panel}>
        <p className={label}>{v.joinTitle}</p>
        <p className="mt-2 text-sm text-ink/70">{v.joinSub}</p>
        <p className="mt-2 font-mono text-xs text-ink/50">
          MCP <span className="text-ink/80">fabius_analyst_join</span> · {GATE.replace("https://", "")}/analysts/input · /analysts/registry
        </p>
      </div>

      <p className="text-xs text-ink/50">
        {v.hashNote}
        {anchor && (
          <>
            {" "}
            <a className="underline" href={LINKS.scan + anchor} target="_blank" rel="noreferrer">
              SelectionAnchor {short(anchor)}
            </a>
          </>
        )}
      </p>
    </>
  );
}

function Slip({ r, open, sealed, now }: { r: AnalisRec; open: boolean; sealed: string; now?: string }) {
  const { t } = useLang();
  const v = t.analis;
  const p = r.alasan.pilihan;
  return (
    <article className={`${panel} min-w-0`}>
      <header className="flex flex-wrap items-baseline justify-between gap-x-3">
        <p className="font-display text-lg">{now ?? r.alasan.nama ?? `agent ${r.alasan.agent_id}`}</p>
        <p className="text-xs text-ink/50">
          agent {r.alasan.agent_id}
          {r.luar && <span className="ml-2 rounded-full bg-ink/10 px-2 py-0.5 text-[10px] uppercase tracking-wide text-ink/60">{v.external}</span>}
        </p>
      </header>
      {/* nama + model yang tercatat DI DALAM alasan yang di-hash = model yang benar-benar membuat pilihan ini (slot agent bisa berganti model, F-D105) */}
      {now && r.alasan.nama && now !== r.alasan.nama && <p className="mt-1 text-xs text-violet">{v.madeBy.replace("{m}", r.alasan.model ?? r.alasan.nama)}</p>}
      <p className="mt-3 font-display text-3xl font-[300]">{r.bot}</p>
      <div className="mt-3" title={v.convictionNote}>
        <div className="h-2 w-full overflow-hidden rounded-full bg-ink/10">
          <div className="h-full rounded-full bg-violet" style={{ width: `${Math.max(0, Math.min(100, r.keyakinan))}%` }} />
        </div>
        <p className="mt-1 text-xs text-ink/60">
          {v.conviction} {r.keyakinan}%
        </p>
      </div>
      {open && p ? (
        <div className="mt-4 space-y-3 text-sm">
          <p className="whitespace-pre-line text-ink/85">{p.alasan}</p>
          {p.risiko && (
            <p className="text-ink/70">
              <span className="font-medium">{v.risk}: </span>
              {p.risiko}
            </p>
          )}
          <dl className="grid grid-cols-[auto,1fr] gap-x-3 gap-y-1 font-mono text-[11px] text-ink/60">
            <dt>reasonHash</dt>
            <dd className="break-all">{r.reasonHash}</dd>
            {r.alasan.masukan_sha256 && (
              <>
                <dt>input</dt>
                <dd className="break-all">{r.alasan.masukan_sha256}</dd>
              </>
            )}
            {r.alasan.prompt_sha256 && (
              <>
                <dt>prompt</dt>
                <dd className="break-all">{r.alasan.prompt_sha256}</dd>
              </>
            )}
            {r.alasan.jawaban_mentah_sha256 && (
              <>
                <dt>raw answer</dt>
                <dd className="break-all">{r.alasan.jawaban_mentah_sha256}</dd>
              </>
            )}
          </dl>
        </div>
      ) : (
        <div className="mt-4 flex items-center gap-3 rounded-xl border border-dashed border-ink/20 bg-lav/50 p-3">
          <span aria-hidden className="grid h-9 w-9 shrink-0 place-items-center rounded-full bg-violet font-mono text-[10px] text-white">
            {r.reasonHash.slice(2, 6)}
          </span>
          <div className="min-w-0">
            <p className="text-sm text-ink/80">{r.alasan.tidak_terbit ? v.notPublished : sealed}</p>
            <p className="truncate font-mono text-[11px] text-ink/50">reasonHash {r.reasonHash}</p>
          </div>
        </div>
      )}
      <p className="mt-3 text-xs text-ink/50">
        {r.status === "dikomit" ? v.committed : v.pending}
        {r.tx && (
          <>
            {" · "}
            <a className="underline" href={LINKS.tx + r.tx} target="_blank" rel="noreferrer">
              {v.tx}
            </a>
          </>
        )}
      </p>
    </article>
  );
}

function Papan({ rows }: { rows: PapanRow[] }) {
  const { t } = useLang();
  const v = t.analis;
  const max = Math.max(1, ...rows.map((r) => Math.abs(r.jumlah_selisih_bps)));
  return (
    <div className={panel}>
      <p className={label}>{v.board}</p>
      <div className="mt-3 space-y-3">
        {rows.map((r, i) => {
          const w = (Math.abs(r.jumlah_selisih_bps) / max) * 50;
          const pos = r.jumlah_selisih_bps >= 0;
          return (
            <div key={r.agent_id}>
              <div className="flex flex-wrap items-baseline justify-between gap-x-3 text-sm">
                <span>
                  {i + 1}. agent {r.agent_id} <span className="text-ink/50">({r.nama ?? r.agent})</span>
                  {r.luar && <span className="ml-2 rounded-full bg-ink/10 px-2 py-0.5 text-[10px] uppercase tracking-wide text-ink/60">{v.external}</span>}
                </span>
                <span className="font-mono text-xs text-ink/70">
                  {r.terskor}/{r.pilihan} {v.colScored} · {r.jumlah_selisih_bps >= 0 ? "+" : ""}
                  {r.jumlah_selisih_bps.toFixed(1)} bps
                </span>
              </div>
              <div className="relative mt-1 h-2 rounded-full bg-ink/5">
                <span className="absolute inset-y-0 left-1/2 w-px bg-ink/30" />
                <span className={`absolute inset-y-0 rounded-full ${pos ? "bg-violet" : "bg-ink/40"}`} style={pos ? { left: "50%", width: `${w}%` } : { right: "50%", width: `${w}%` }} />
              </div>
            </div>
          );
        })}
      </div>
      <p className="mt-3 text-xs text-ink/50">{v.boardNote}</p>
    </div>
  );
}
