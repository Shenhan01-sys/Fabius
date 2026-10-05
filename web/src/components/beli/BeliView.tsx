"use client";

// /beli/<bot> (P138c, F-D100/F-D101): beli satu paket sinyal dengan x402 di testnet 97. Login Privy (Google / Telegram / email) -> embedded wallet ->
// FAB gratis dari gerbang -> dua tanda tangan EIP-712 (nol gas) -> paket tampil. Di dalam Telegram (Mini App) Privy login otomatis lewat Telegram;
// akun Google yang ditautkan memakai wallet yang SAMA. Skrip Mini App Telegram dimuat dulu supaya Privy melihat `window.Telegram`.

import Script from "next/script";
import { useCallback, useEffect, useState } from "react";
import { PrivyProvider, usePrivy, useSignTypedData, useWallets } from "@privy-io/react-auth";
import { bscTestnet } from "viem/chains";
import type { Hex } from "viem";
import Nav from "@/components/Nav";
import { LangProvider, useLang } from "@/components/lang";
import { PRIVY_APP_ID, buy, fabBalance, faucet, teaser, type Package, type Teaser } from "@/lib/x402-buy";

export default function BeliView({ bot }: { bot: string }) {
  const [scriptDone, setScriptDone] = useState(false);
  return (
    <LangProvider>
      <Script src="https://telegram.org/js/telegram-web-app.js" strategy="afterInteractive" onReady={() => setScriptDone(true)} onError={() => setScriptDone(true)} />
      <div className="p-2 sm:p-3">
        <Nav />
        {scriptDone ? (
          <PrivyProvider
            appId={PRIVY_APP_ID}
            config={{
              loginMethods: ["google", "telegram", "email"],
              embeddedWallets: { ethereum: { createOnLogin: "users-without-wallets" } },
              defaultChain: bscTestnet,
              supportedChains: [bscTestnet],
              appearance: { theme: "light", accentColor: "#6E56CF", landingHeader: "Fabius" },
            }}
          >
            <Buy bot={bot} />
          </PrivyProvider>
        ) : (
          <Shell bot={bot} />
        )}
      </div>
    </LangProvider>
  );
}

function Shell({ bot, children }: { bot: string; children?: React.ReactNode }) {
  const { t } = useLang();
  const v = t.beli;
  return (
    <section className="relative overflow-hidden rounded-[30px] bg-gradient-to-b from-lav via-lav to-white px-6 pb-20 pt-32 sm:px-12 sm:pt-40 lg:px-16">
      <span className="tag text-violet">{v.tag}</span>
      <h1 className="mt-3 max-w-3xl font-display text-[clamp(2.2rem,5vw,4.4rem)] font-[300] leading-[0.95] tracking-[-0.03em] text-ink" style={{ fontStretch: "112%" }}>
        {v.title.replace("{bot}", bot)}
      </h1>
      <p className="mt-4 max-w-2xl text-ink/60">{v.sub}</p>
      <div className="mt-10 max-w-2xl space-y-6">{children}</div>
    </section>
  );
}

function Step({ n, title, children }: { n: number; title: string; children: React.ReactNode }) {
  return (
    <div className="rounded-2xl border border-ink/10 bg-white/70 p-5">
      <p className="text-sm uppercase tracking-wide text-ink/50">
        {String(n).padStart(2, "0")} · {title}
      </p>
      <div className="mt-3 text-ink">{children}</div>
    </div>
  );
}

const btn = "rounded-full bg-ink px-5 py-2.5 text-sm text-white transition hover:bg-violet disabled:cursor-not-allowed disabled:opacity-40";

function Buy({ bot }: { bot: string }) {
  const { t } = useLang();
  const v = t.beli;
  const { ready, authenticated, login, logout } = usePrivy();
  const { wallets } = useWallets();
  const { signTypedData } = useSignTypedData();
  const w = wallets.find((x) => x.walletClientType === "privy") ?? wallets[0];
  const owner = w?.address as Hex | undefined;
  const [tz, setTz] = useState<Teaser | null>(null);
  const [bal, setBal] = useState<bigint | null>(null);
  const [busy, setBusy] = useState<string | null>(null);
  const [note, setNote] = useState<string>("");
  const [pkg, setPkg] = useState<Package | null>(null);

  useEffect(() => {
    teaser(bot).then(setTz, (e: unknown) => setNote(String(e)));
  }, [bot]);
  const refresh = useCallback(() => {
    if (owner) fabBalance(owner).then(setBal, () => setBal(null));
  }, [owner]);
  useEffect(refresh, [refresh]);

  const price = tz ? tz.harga.atomic : null;
  const enough = bal != null && price != null && bal >= BigInt(price);

  async function topup() {
    if (!owner) return;
    setBusy("faucet");
    const r = await faucet(owner);
    setNote(r.note);
    setBusy(null);
    setTimeout(refresh, 4000);
  }

  async function pay() {
    if (!owner || !tz) return;
    setBusy("pay");
    setNote("");
    try {
      const tg = new URLSearchParams(window.location.search).get("tg");
      const sign = async (td: Record<string, unknown>) =>
        (await signTypedData(td as unknown as Parameters<typeof signTypedData>[0], { address: owner, uiOptions: { showWalletUIs: false } })).signature;
      setPkg(await buy(bot, tz.harga.bar, owner, sign, tg));
      refresh();
    } catch (e) {
      setNote(e instanceof Error ? e.message : String(e));
    }
    setBusy(null);
  }

  const c = tz?.teaser;
  return (
    <Shell bot={bot}>
      <Step n={1} title={v.offer}>
        {tz ? (
          <>
            <p className="font-display text-3xl font-[300]">
              {tz.harga.fab} FAB <span className="text-base text-ink/50">· bar {tz.harga.bar}</span>
            </p>
            <p className="mt-2 text-sm text-ink/70">
              {v.confidence}: {c?.confidence_pct == null ? v.notMeasured : `${c.confidence_pct}% (${c.label})`} · {v.gate}: {c?.gerbang_v1 ?? "-"} · F-D16: {c?.fd16}
            </p>
            <p className="mt-1 text-sm text-ink/50">{v.priceRule}</p>
          </>
        ) : (
          <p className="text-ink/50">{v.loading}</p>
        )}
      </Step>
      <Step n={2} title={v.wallet}>
        {!ready ? (
          <p className="text-ink/50">{v.loading}</p>
        ) : !authenticated ? (
          <button className={btn} onClick={login}>
            {v.login}
          </button>
        ) : (
          <>
            <p className="break-all font-mono text-sm">{owner ?? v.creating}</p>
            <p className="mt-2 text-sm">
              FAB: {bal == null ? "…" : (Number(bal) / 1e6).toString()} · <span className="text-ink/50">{v.noGas}</span>
            </p>
            <div className="mt-3 flex flex-wrap gap-3">
              <button className={btn} disabled={!owner || busy != null} onClick={topup}>
                {busy === "faucet" ? "…" : v.topup}
              </button>
              <button className="text-sm text-ink/50 underline" onClick={logout}>
                {v.logout}
              </button>
            </div>
          </>
        )}
      </Step>
      <Step n={3} title={v.payTitle}>
        <button className={btn} disabled={!authenticated || !owner || !enough || busy != null || !tz} onClick={pay}>
          {busy === "pay" ? v.paying : v.pay.replace("{fab}", String(tz?.harga.fab ?? "…"))}
        </button>
        {authenticated && owner && !enough && bal != null && <p className="mt-2 text-sm text-ink/50">{v.needTopup}</p>}
        {note && <p className="mt-3 break-all text-sm text-ink/70">{note}</p>}
      </Step>
      {pkg && (
        <Step n={4} title={v.result}>
          <table className="w-full text-sm">
            <tbody>
              {Object.entries(pkg.targets).length === 0 ? (
                <tr>
                  <td className="text-ink/60">{v.flat}</td>
                </tr>
              ) : (
                Object.entries(pkg.targets)
                  .sort((a, b) => Math.abs(b[1]) - Math.abs(a[1]))
                  .map(([a, wgt]) => (
                    <tr key={a} className="border-b border-ink/5">
                      <td className="py-1 font-mono">{a}</td>
                      <td className="py-1 text-right font-mono">{(wgt >= 0 ? "+" : "") + wgt.toFixed(4)}</td>
                    </tr>
                  ))
              )}
            </tbody>
          </table>
          <p className="mt-3 break-all text-xs text-ink/60">
            commitId {pkg.commitId} · {v.committed}: {pkg.komit?.ada ? "✓" : "…"}
            {pkg.validasi_erc8004?.dijawab ? ` · ERC-8004 ${pkg.validasi_erc8004.skor}` : ""}
          </p>
          <p className="mt-1 break-all text-xs">
            <a className="underline" href={`https://testnet.bscscan.com/tx/${pkg.pembayaran.tx}`} target="_blank" rel="noreferrer">
              {v.paidTx}
            </a>
          </p>
          <p className="mt-3 text-xs text-ink/50">{v.disclaimer}</p>
        </Step>
      )}
    </Shell>
  );
}
