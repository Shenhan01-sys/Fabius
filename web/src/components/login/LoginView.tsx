"use client";

// /login (P165): satu tempat login untuk seluruh situs. Belum login -> tombol Privy (Google / Telegram / email; dompet BNB testnet dibuat otomatis).
// Sudah login -> akun, dompet, status anggota dari gerbang (`useAkses().anggota`, GET /access), jalan ke beli 1 sinyal bila belum anggota, dan
// kembali ke halaman asal (?next=). Navbar menampilkan status yang sama.

import Link from "next/link";
import { useAkses } from "@/components/akses";
import Nav from "@/components/Nav";
import { LangProvider, useLang } from "@/components/lang";

const tgl = (s?: number) => (s ? new Date(s * 1000).toISOString().slice(0, 16).replace("T", " ") + "Z" : "-");
const pendek = (w?: string | null) => (w ? `${w.slice(0, 6)}…${w.slice(-4)}` : "-");
const btn = "inline-block rounded-full bg-ink px-5 py-2.5 text-sm text-white transition-colors hover:bg-violet disabled:cursor-not-allowed disabled:opacity-40";
const ghost = "inline-block rounded-full border border-ink/15 px-5 py-2.5 text-sm text-ink transition-colors hover:border-violet hover:text-violet";
const panel = "min-w-0 rounded-2xl border border-ink/10 bg-white/70 p-6";

export default function LoginView({ next }: { next?: string }) {
  return (
    <LangProvider>
      <div className="p-2 sm:p-3">
        <Nav />
        <Body next={next} />
      </div>
    </LangProvider>
  );
}

function Body({ next }: { next?: string }) {
  const { t } = useLang();
  const v = t.login;
  const ak = useAkses();
  const a = ak.anggota;
  const nama: Record<string, string> = { "/desk": t.nav.desk, "/analysts": t.nav.analysts, "/buy": v.buy, "/": "Fabius" };
  const kembali = next ? (nama[next.split("?")[0]] ?? next) : null;
  return (
    <section className="relative overflow-hidden rounded-[30px] bg-gradient-to-b from-lav via-lav to-white px-6 pb-20 pt-32 sm:px-12 sm:pt-40 lg:px-16">
      <div className="mx-auto max-w-3xl text-center">
        <span className="tag text-violet">{v.tag}</span>
        <h1 className="mt-3 font-display text-[clamp(2.2rem,5vw,4.4rem)] font-[300] leading-[0.95] tracking-[-0.03em] text-ink" style={{ fontStretch: "112%" }}>
          {v.title}
        </h1>
        <p className="mx-auto mt-4 max-w-2xl text-ink/60">{v.sub}</p>
      </div>

      <div className="mx-auto mt-10 grid max-w-5xl gap-6 lg:grid-cols-[1.2fr_1fr]">
        <div className={panel}>
          {!ak.ready ? (
            <p className="text-ink/50">{v.loading}</p>
          ) : !ak.authenticated ? (
            <button className={btn} onClick={ak.login}>
              {v.button}
            </button>
          ) : (
            <div className="space-y-5">
              <div>
                <p className="font-display text-xl text-ink">{v.who.replace("{who}", ak.email ?? pendek(ak.wallet))}</p>
                {ak.metode && <p className="text-sm text-ink/50">{v.via.replace("{m}", ak.metode)}</p>}
                <p className="mt-2 font-mono text-xs text-ink/60">
                  {v.wallet} {ak.wallet ?? "-"}
                </p>
              </div>

              <div className={`rounded-xl border p-4 ${a?.live ? "border-violet/30 bg-violet/5" : "border-ink/10"}`}>
                {!a ? (
                  <p className="text-sm text-ink/50">{v.checking}</p>
                ) : a.live ? (
                  <>
                    <p className="flex items-center gap-2 font-medium text-violet">
                      <span className="inline-block h-2 w-2 rounded-full bg-violet" aria-hidden />
                      {v.member.replace("{d}", tgl(a.berlaku_sampai))}
                    </p>
                    {a.pembelian_terakhir && (
                      <p className="mt-1 text-xs text-ink/60">{v.lastBuy.replace("{bot}", a.pembelian_terakhir.bot).replace("{bar}", a.pembelian_terakhir.bar)}</p>
                    )}
                  </>
                ) : a.status === 402 ? (
                  <>
                    <p className="font-medium text-ink">🔒 {v.notMember}</p>
                    <p className="mt-1 text-sm text-ink/60">{v.notMemberSub}</p>
                    <Link className={`${btn} mt-3`} href="/buy">
                      {v.buy}
                    </Link>
                  </>
                ) : (
                  <p className="break-all text-sm text-ink/70">
                    {v.error}: {a.error ?? `HTTP ${a.status}`}
                  </p>
                )}
              </div>

              <div className="flex flex-wrap items-center gap-3">
                {kembali && next && (
                  <Link className={btn} href={next}>
                    {v.back.replace("{p}", kembali)}
                  </Link>
                )}
                <Link className={ghost} href="/desk">
                  {v.openDesk}
                </Link>
                <Link className={ghost} href="/analysts">
                  {v.openAnalysts}
                </Link>
                <button className="text-sm text-ink/50 underline" onClick={ak.logout}>
                  {v.signOut}
                </button>
              </div>
            </div>
          )}
        </div>

        <div className={panel}>
          <p className="text-sm uppercase tracking-wide text-ink/50">{v.getsTitle}</p>
          <ul className="mt-3 space-y-3 text-sm text-ink/75">
            {v.gets.map((g) => (
              <li key={g} className="flex gap-2">
                <span className="mt-1.5 inline-block h-1.5 w-1.5 shrink-0 rounded-full bg-violet" aria-hidden />
                {g}
              </li>
            ))}
          </ul>
        </div>
      </div>
    </section>
  );
}
