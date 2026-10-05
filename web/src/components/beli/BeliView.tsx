"use client";

// /buy (P146; dulu /beli): sinyal HARI INI = bot yang dipakai Fabius (gerbang `/active`, aturan terkunci engine/pemilih.py) - pembeli tidak memilih bot.
// /buy/<bot> tetap ada untuk tautan eksplisit (agent, `/buy <BOT>`).
// (P138c, F-D100/F-D101): beli satu paket sinyal dengan x402 di testnet 97. Login Privy (Google / Telegram / email) -> embedded wallet ->
// FAB gratis dari gerbang -> dua tanda tangan EIP-712 (nol gas) -> paket tampil. Di dalam Telegram (Mini App) Privy login otomatis lewat Telegram;
// akun Google yang ditautkan memakai wallet yang SAMA. Skrip Mini App Telegram dimuat dulu supaya Privy melihat `window.Telegram`.

import Link from "next/link";
import Script from "next/script";
import { useCallback, useEffect, useState } from "react";
import { PrivyProvider, useLinkAccount, usePrivy, useSignTypedData, useSigners, useWallets } from "@privy-io/react-auth";
import type { Hex } from "viem";
import Nav from "@/components/Nav";
import { LangProvider, useLang } from "@/components/lang";
import { GATE, PRIVY_APP_ID, PRIVY_CONFIG, PRIVY_KEY_QUORUM_ID, PRIVY_POLICY_ID, buy, fabBalance, faucet, teaser, type Package, type RincianAset, type Teaser } from "@/lib/x402-buy";

const px = (x: number) => (x >= 100 ? x.toLocaleString("en-US", { maximumFractionDigits: 2 }) : x >= 1 ? x.toFixed(4) : x.toFixed(6));
const pct = (x: number) => `${x >= 0 ? "+" : ""}${(x * 100).toFixed(1)}%`;

export default function BeliView({ bot }: { bot?: string }) {
  const [scriptDone, setScriptDone] = useState(false);
  return (
    <LangProvider>
      <Script src="https://telegram.org/js/telegram-web-app.js" strategy="afterInteractive" onReady={() => setScriptDone(true)} onError={() => setScriptDone(true)} />
      <div className="p-2 sm:p-3">
        <Nav />
        {scriptDone ? (
          <PrivyProvider appId={PRIVY_APP_ID} config={PRIVY_CONFIG}>
            <Buy fixed={bot} />
          </PrivyProvider>
        ) : (
          <Shell bot={bot} />
        )}
      </div>
    </LangProvider>
  );
}

function Shell({ bot, children }: { bot?: string; children?: React.ReactNode }) {
  const { t } = useLang();
  const v = t.beli;
  return (
    <section className="relative overflow-hidden rounded-[30px] bg-gradient-to-b from-lav via-lav to-white px-6 pb-20 pt-32 sm:px-12 sm:pt-40 lg:px-16">
      <div className="mx-auto max-w-4xl text-center">
        <span className="tag text-violet">{v.tag}</span>
        <h1 className="mt-3 font-display text-[clamp(2.2rem,5vw,4.4rem)] font-[300] leading-[0.95] tracking-[-0.03em] text-ink" style={{ fontStretch: "112%" }}>
          {bot ? v.title.replace("{bot}", bot) : v.titleToday}
        </h1>
        <p className="mx-auto mt-4 max-w-2xl text-ink/60">{bot ? v.sub : v.subToday}</p>
      </div>
      <div className="mx-auto mt-10 grid max-w-5xl gap-6 lg:grid-cols-2">{children}</div>
    </section>
  );
}

function Step({ n, title, wide, children }: { n: number; title: string; wide?: boolean; children: React.ReactNode }) {
  return (
    <div className={`min-w-0 rounded-2xl border border-ink/10 bg-white/70 p-5 ${wide ? "lg:col-span-2" : ""}`}>
      <p className="text-sm uppercase tracking-wide text-ink/50">
        {String(n).padStart(2, "0")} · {title}
      </p>
      <div className="mt-3 text-ink">{children}</div>
    </div>
  );
}

const btn = "rounded-full bg-ink px-5 py-2.5 text-sm text-white transition hover:bg-violet disabled:cursor-not-allowed disabled:opacity-40";

function Buy({ fixed }: { fixed?: string }) {
  const { t, lang } = useLang();
  const v = t.beli;
  const { ready, authenticated, login, logout, user } = usePrivy();
  const [izinMsg, setIzinMsg] = useState<string>("");
  const { linkTelegram, linkOAuth } = useLinkAccount({
    onSuccess: () => setIzinMsg(v.tgDone),
    onError: (err) => setIzinMsg(`${v.tgFail}: ${String(err)}`),
  });
  const tgLinked = !!user?.telegram;
  const { wallets } = useWallets();
  const { signTypedData } = useSignTypedData();
  const { addSigners, removeSigners } = useSigners();
  const [izin, setIzin] = useState<string>("");
  const w = wallets.find((x) => x.walletClientType === "privy") ?? wallets[0];
  const owner = w?.address as Hex | undefined;
  const [tz, setTz] = useState<Teaser | null>(null);
  const [bal, setBal] = useState<bigint | null>(null);
  const [busy, setBusy] = useState<string | null>(null);
  const [note, setNote] = useState<string>("");
  const [pkg, setPkg] = useState<Package | null>(null);
  const [aktif, setAktif] = useState<{ bot: string; en?: string; id?: string } | null>(null);

  useEffect(() => {
    if (fixed) return;
    fetch(`${GATE}/active`, { cache: "no-store" })
      .then((r) => r.json())
      .then((a) => setAktif({ bot: a.bot, en: a.alasan_en, id: a.alasan }), (e: unknown) => setNote(String(e)));
  }, [fixed]);
  const bot = fixed ?? aktif?.bot;
  useEffect(() => {
    if (bot) teaser(bot).then(setTz, (e: unknown) => setNote(String(e)));
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
    if (!owner || !tz || !bot) return;
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
    <Shell bot={fixed}>
      <Step n={1} title={v.offer}>
        {tz ? (
          <>
            {!fixed && bot && (
              <div className="mb-3">
                <p className="text-sm text-ink/50">{v.today}</p>
                <p className="font-display text-4xl font-[300]">{bot}</p>
                {(lang === "id" ? aktif?.id : aktif?.en) && <p className="mt-1 text-xs text-ink/50">{lang === "id" ? aktif?.id : aktif?.en}</p>}
              </div>
            )}
            <p className="font-display text-3xl font-[300]">
              {tz.harga.fab} FAB <span className="text-base text-ink/50">· bar {tz.harga.bar}</span>
            </p>
            <p className="mt-2 text-sm text-ink/70">
              {v.confidence}: {c?.confidence_pct == null ? v.notMeasured : `${c.confidence_pct}% (${t.label.conf[c.label] ?? c.label})`} · {v.gate}:{" "}
              {c?.gerbang_v1 ? (t.label.verdict[c.gerbang_v1] ?? c.gerbang_v1) : "-"} · F-D16: {c?.fd16 ? (t.label.fd16[c.fd16] ?? c.fd16) : "-"}
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
      {authenticated && owner && (
        <Step n={3} title={v.botTitle}>
          <p className="text-sm text-ink/70">{v.botSub}</p>
          {!tgLinked && (
            <div className="mt-3 rounded-xl bg-lav/60 p-3 text-sm">
              <p>{v.tgNeed}</p>
              <button
                className={`${btn} mt-2`}
                onClick={async () => {
                  const raw = (window as unknown as { Telegram?: { WebApp?: { initData?: string } } }).Telegram?.WebApp?.initData;
                  const msg = (e: unknown) => (e instanceof Error ? e.message : String(e));
                  setIzinMsg(v.tgWorking);
                  // linkTelegram = mode bot-token (HMAC); app Privy yang dikonfigurasi lewat Telegram OAuth (OIDC) harus lewat linkOAuth.
                  // Keduanya async: galat datang sebagai promise ditolak, bukan lemparan sinkron - tanpa await label macet di "Linking…".
                  try {
                    if (raw) await linkTelegram({ launchParams: { initDataRaw: raw } });
                    else await linkTelegram();
                  } catch (e) {
                    if (!/HMAC/i.test(msg(e))) return setIzinMsg(`${v.tgFail}: ${msg(e)}`);
                    try {
                      await linkOAuth({ provider: "telegram" });
                    } catch (e2) {
                      setIzinMsg(`${v.tgFail}: ${msg(e2)}`);
                    }
                  }
                }}
              >
                {v.tgLink}
              </button>
              {izinMsg && <p className="mt-2 break-all text-sm text-ink/80">{izinMsg}</p>}
            </div>
          )}
          {tgLinked && <p className="mt-2 text-sm text-ink/60">{v.tgOk.replace("{u}", user?.telegram?.username ? "@" + user.telegram.username : String(user?.telegram?.telegramUserId ?? ""))}</p>}
          <div className="mt-3 flex flex-wrap gap-3">
            <button
              className={btn}
              disabled={busy != null}
              onClick={async () => {
                setBusy("izin");
                try {
                  // Ganti izin lama (tanpa policy) dengan izin ber-policy: bot hanya bisa membayar FAB ke gerbang, <= 1 FAB (P148).
                  await removeSigners({ address: owner }).catch(() => undefined);
                  await addSigners({ address: owner, signers: [{ signerId: PRIVY_KEY_QUORUM_ID, policyIds: [PRIVY_POLICY_ID] }] });
                  setIzin(v.botOn);
                } catch (e) {
                  setIzin(e instanceof Error ? e.message : String(e));
                }
                setBusy(null);
              }}
            >
              {busy === "izin" ? "…" : v.botAllow}
            </button>
            <button
              className="text-sm text-ink/50 underline"
              disabled={busy != null}
              onClick={async () => {
                try {
                  await removeSigners({ address: owner });
                  setIzin(v.botOff);
                } catch (e) {
                  setIzin(e instanceof Error ? e.message : String(e));
                }
              }}
            >
              {v.botRevoke}
            </button>
          </div>
          {izin && <p className="mt-2 break-all text-sm text-ink/70">{izin}</p>}
        </Step>
      )}
      <Step n={4} title={v.payTitle} wide={!(authenticated && owner)}>
        <button className={btn} disabled={!authenticated || !owner || !enough || busy != null || !tz} onClick={pay}>
          {busy === "pay" ? v.paying : v.pay.replace("{fab}", String(tz?.harga.fab ?? "…"))}
        </button>
        {authenticated && owner && !enough && bal != null && <p className="mt-2 text-sm text-ink/50">{v.needTopup}</p>}
        {note && <p className="mt-3 break-all text-sm text-ink/70">{note}</p>}
      </Step>
      {pkg && (
        <Step n={5} title={v.result} wide>
          {pkg.rincian && (
            <div className="mb-4 text-sm">
              <p>
                <span className="text-ink/50">{v.rule}:</span> {lang === "id" ? pkg.rincian.aturan : (pkg.rincian.aturan_en ?? pkg.rincian.aturan)} (param {pkg.rincian.param})
              </p>
              <p className="mt-1">
                <span className="text-ink/50">{v.changes}:</span> {v.enter} {pkg.rincian.perubahan.masuk.join(", ") || "-"} · {v.exit} {pkg.rincian.perubahan.keluar.join(", ") || "-"}
              </p>
              <p className="mt-1 text-ink/60">{v.noTp}</p>
            </div>
          )}
          {pkg.rincian && Object.values(pkg.rincian.aset).some((d) => d.keluar_berikut) ? (
            <div className="overflow-x-auto">
              <table className="w-full min-w-[560px] text-xs">
                <thead className="text-left text-ink/50">
                  <tr>
                    <th className="py-1">{v.colAsset}</th>
                    <th>{v.colSide}</th>
                    <th className="text-right">{v.colWeight}</th>
                    <th className="text-right">{v.colEntry}</th>
                    <th className="text-right">PnL</th>
                    <th className="text-right">{v.colExit}</th>
                  </tr>
                </thead>
                <tbody>
                  {Object.entries(pkg.rincian.aset)
                    .sort((a, b) => (b[1].keluar_berikut?.jarak ?? -9) - (a[1].keluar_berikut?.jarak ?? -9))
                    .map(([a, d]: [string, RincianAset]) => (
                      <tr key={a} className="border-b border-ink/5 font-mono">
                        <td className="py-1">{a}</td>
                        <td>{d.sisi}</td>
                        <td className="text-right">{(d.bobot * 100).toFixed(2)}%</td>
                        <td className="text-right">{d.masuk ? `${d.masuk.bar} @ ${px(d.masuk.harga)}` : d.masuk_bila ? `> ${px(d.masuk_bila.di_atas)}` : "-"}</td>
                        <td className="text-right">{d.masuk ? pct(d.masuk.pnl) : "-"}</td>
                        <td className="text-right">{d.keluar_berikut ? `${px(d.keluar_berikut.level)} (${pct(d.keluar_berikut.jarak)})` : "-"}</td>
                      </tr>
                    ))}
                </tbody>
              </table>
              <p className="mt-2 text-xs text-ink/50">{v.trailing}</p>
            </div>
          ) : (
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
          )}
          <p className="mt-3 break-all text-xs text-ink/60">
            commitId {pkg.commitId} · {v.committed}: {pkg.komit?.ada ? "✓" : "…"}
            {pkg.validasi_erc8004?.dijawab ? ` · ERC-8004 ${pkg.validasi_erc8004.skor}` : ""}
          </p>
          <p className="mt-1 break-all text-xs">
            <a className="underline" href={`https://testnet.bscscan.com/tx/${pkg.pembayaran.tx}`} target="_blank" rel="noreferrer">
              {v.paidTx}
            </a>
          </p>
          <Link className="mt-3 inline-block text-sm text-violet underline" href="/analysts">
            {v.analystsOpen}
          </Link>
          <p className="mt-3 text-xs text-ink/50">{v.disclaimer}</p>
        </Step>
      )}
    </Shell>
  );
}
