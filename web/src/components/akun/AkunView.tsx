"use client";

// /account (P157, F5, F-D111): akun MCP berbayar. Login Privy (sama dengan /buy) -> FAB uji dari faucet -> deposit ke gerbang lewat x402 (dua tanda
// tangan EIP-712, nol gas; alur SAMA dengan /buy lewat lib/x402-buy.ts::bayarX402) -> kunci API dari tanda tangan pesan EIP-191 dompet -> saldo, riwayat
// potongan (rantai hash per dompet), cabut kunci. Gerbang = sumber kebenaran; selama sakelar FABIUS_F5 mati halaman ini hanya menjelaskan statusnya.
// Kunci API hanya hidup di memori halaman ini (tidak disimpan di peramban); gerbang hanya menyimpan sha256-nya.

import { useCallback, useEffect, useState } from "react";
import { usePrivy, useSignMessage, useSignTypedData, useWallets } from "@privy-io/react-auth";
import type { Hex } from "viem";
import Nav from "@/components/Nav";
import { LangProvider, useLang } from "@/components/lang";
import { bayarX402, fabBalance, faucet } from "@/lib/x402-buy";
import { DEPOSIT_PILIHAN, GATE, HARGA, KUNCI_RE, akun, buatKunci, cabutKunci, fab, harga, pesanCabut, pesanKunci } from "@/lib/akun";

const TEKS = {
  en: {
    tag: "Paid MCP · account",
    title: "Your Fabius MCP account",
    sub: "Deposit FAB (BNB testnet credit, no value) with x402, get an API key by signing a message with your wallet, and every paid MCP call is charged from your balance.",
    closed: "Paid MCP is not open yet on the gate (switch FABIUS_F5 is off). The MCP server at /mcp keeps its current free tools until the builder opens it.",
    signIn: "Sign in",
    wallet: "Wallet",
    onchain: "FAB in your wallet",
    getFab: "Get free test FAB",
    deposit: "Deposit to your MCP balance",
    depositNote: "Two signatures, zero gas. The gate credits your balance only after the on-chain transfer is proven.",
    key: "API key",
    makeKey: "Create an API key (sign a message)",
    keyOnce: "Copy it now: it is shown ONCE. Fabius stores only its sha256.",
    keyUse: "Use it in your MCP client:",
    paste: "Paste an API key to see its account",
    show: "Show account",
    balance: "MCP balance",
    deposited: "deposited",
    spent: "spent",
    keys: "Keys",
    revoke: "Revoke",
    records: "Ledger records (newest last)",
    prices: "Prices",
    free: "free",
  },
  id: {
    tag: "MCP berbayar · akun",
    title: "Akun MCP Fabius kamu",
    sub: "Deposit FAB (kredit testnet BNB, tanpa nilai) lewat x402, dapatkan kunci API dengan menandatangani pesan dari dompetmu, lalu tiap panggilan MCP berbayar dipotong dari saldo.",
    closed: "MCP berbayar belum dibuka di gerbang (sakelar FABIUS_F5 mati). Server MCP di /mcp tetap dengan alat gratisnya sampai builder membukanya.",
    signIn: "Masuk",
    wallet: "Dompet",
    onchain: "FAB di dompetmu",
    getFab: "Ambil FAB uji gratis",
    deposit: "Deposit ke saldo MCP",
    depositNote: "Dua tanda tangan, nol gas. Gerbang menambah saldo hanya sesudah transfer on-chain terbukti.",
    key: "Kunci API",
    makeKey: "Buat kunci API (tanda tangani pesan)",
    keyOnce: "Salin sekarang: kunci ditampilkan SEKALI. Fabius hanya menyimpan sha256-nya.",
    keyUse: "Pakai di klien MCP-mu:",
    paste: "Tempel kunci API untuk melihat akunnya",
    show: "Lihat akun",
    balance: "Saldo MCP",
    deposited: "deposit",
    spent: "terpakai",
    keys: "Kunci",
    revoke: "Cabut",
    records: "Rekaman buku (terbaru di bawah)",
    prices: "Harga",
    free: "gratis",
  },
};

type Rekaman = { n: number; t: number; jenis: string; alat?: string; atomic?: number; tx?: string; kunci_id?: string; h: string; prev: string };
type Akun = {
  wallet: string;
  balance_atomic: number;
  deposited_atomic: number;
  spent_atomic: number;
  keys: { key_id: string; active: boolean; issued_t: number }[];
  records: Rekaman[];
  head: string;
};

export default function AkunView() {
  return (
    <LangProvider>
      <div className="p-2 sm:p-3">
        <Nav />
        <Halaman />
      </div>
    </LangProvider>
  );
}

const btn = "rounded-full bg-ink px-5 py-2.5 text-sm text-white transition hover:bg-violet disabled:cursor-not-allowed disabled:opacity-40";
const kotak = "min-w-0 rounded-2xl border border-ink/10 bg-white/70 p-5";

function Halaman() {
  const { lang } = useLang();
  const v = TEKS[lang];
  const { ready, authenticated, login } = usePrivy();
  const { wallets } = useWallets();
  const { signTypedData } = useSignTypedData();
  const { signMessage } = useSignMessage();
  const w = wallets.find((x) => x.walletClientType === "privy") ?? wallets[0];
  const owner = w?.address as Hex | undefined;
  const [buka, setBuka] = useState<boolean | null>(null);
  const [bal, setBal] = useState<bigint | null>(null);
  const [busy, setBusy] = useState<string | null>(null);
  const [note, setNote] = useState("");
  const [kunciBaru, setKunciBaru] = useState<string | null>(null);
  const [kunci, setKunci] = useState("");
  const [ak, setAk] = useState<Akun | null>(null);

  useEffect(() => {
    harga().then((j) => setBuka(j.ok), () => setBuka(false));
  }, []);
  const refresh = useCallback(() => {
    if (owner) fabBalance(owner).then(setBal, () => setBal(null));
  }, [owner]);
  useEffect(refresh, [refresh]);

  const lihat = useCallback(async (k: string) => {
    const j = await akun(k);
    if (j.ok) setAk(j.body as unknown as Akun);
    else setNote(String(j.body.error ?? `HTTP ${j.status}`));
  }, []);

  async function jalan(nama: string, f: () => Promise<void>) {
    setBusy(nama);
    setNote("");
    try {
      await f();
    } catch (e) {
      setNote(e instanceof Error ? e.message : String(e));
    }
    setBusy(null);
  }

  const setor = (atomic: number) =>
    jalan(`dep${atomic}`, async () => {
      if (!owner) return;
      const sign = async (td: Record<string, unknown>) =>
        (await signTypedData(td as unknown as Parameters<typeof signTypedData>[0], { address: owner, uiOptions: { showWalletUIs: false } })).signature;
      const r = await bayarX402<{ deposit: { tx: string }; balance_atomic: number }>(`${GATE}/account/deposit/${atomic}`, owner, sign);
      setNote(`+${fab(atomic)} FAB · tx ${r.deposit.tx} · ${v.balance} ${fab(r.balance_atomic)} FAB`);
      refresh();
      if (KUNCI_RE.test(kunci)) await lihat(kunci);
    });

  const kunciKu = () =>
    jalan("key", async () => {
      if (!owner) return;
      const ts = Math.floor(Date.now() / 1000);
      const { signature } = await signMessage({ message: pesanKunci(owner, ts) }, { address: owner });
      const j = await buatKunci(owner, ts, signature);
      if (!j.ok) throw new Error(String(j.body.error ?? `HTTP ${j.status}`));
      const k = String(j.body.key);
      setKunciBaru(k);
      setKunci(k);
      await lihat(k);
    });

  const cabut = (id: string) =>
    jalan(`rev${id}`, async () => {
      if (!owner) return;
      const ts = Math.floor(Date.now() / 1000);
      const { signature } = await signMessage({ message: pesanCabut(owner, id, ts) }, { address: owner });
      const j = await cabutKunci(owner, id, ts, signature);
      if (!j.ok) throw new Error(String(j.body.error ?? `HTTP ${j.status}`));
      if (KUNCI_RE.test(kunci)) await lihat(kunci);
    });

  return (
    <section className="relative overflow-hidden rounded-[30px] bg-gradient-to-b from-lav via-lav to-white px-6 pb-20 pt-32 sm:px-12 sm:pt-40 lg:px-16">
      <div className="mx-auto max-w-4xl text-center">
        <span className="tag text-violet">{v.tag}</span>
        <h1 className="mt-3 font-display text-[clamp(2.2rem,5vw,4.4rem)] font-[300] leading-[0.95] tracking-[-0.03em] text-ink" style={{ fontStretch: "112%" }}>
          {v.title}
        </h1>
        <p className="mx-auto mt-4 max-w-2xl text-ink/60">{v.sub}</p>
      </div>
      <div className="mx-auto mt-10 grid max-w-5xl gap-6 lg:grid-cols-2">
        <div className={`${kotak} lg:col-span-2`}>
          <p className="text-sm uppercase tracking-wide text-ink/50">{v.prices}</p>
          <p className="mt-2 text-ink">
            {Object.entries(HARGA)
              .map(([a, h]) => `${a} ${fab(h)} FAB`)
              .join(" · ")}{" "}
            · fabius_pricing, fabius_account {v.free}
          </p>
          {buka === false && <p className="mt-3 rounded-xl bg-ink/5 p-3 text-sm text-ink/70">{v.closed}</p>}
        </div>
        {buka && (
          <>
            <div className={kotak}>
              <p className="text-sm uppercase tracking-wide text-ink/50">{v.wallet}</p>
              {!ready || !authenticated ? (
                <button className={`${btn} mt-3`} onClick={login}>
                  {v.signIn}
                </button>
              ) : (
                <div className="mt-2 space-y-3 text-sm">
                  <p className="break-all font-mono">{owner ?? "…"}</p>
                  <p>
                    {v.onchain}: {bal == null ? "…" : fab(Number(bal))} FAB
                  </p>
                  <button className={btn} disabled={!owner || !!busy} onClick={() => jalan("faucet", async () => owner && setNote((await faucet(owner)).note))}>
                    {v.getFab}
                  </button>
                  <p className="pt-2 text-ink/60">{v.deposit}</p>
                  <div className="flex flex-wrap gap-2">
                    {DEPOSIT_PILIHAN.map((a) => (
                      <button key={a} className={btn} disabled={!owner || !!busy || (bal != null && bal < BigInt(a))} onClick={() => setor(a)}>
                        {busy === `dep${a}` ? "…" : `${fab(a)} FAB`}
                      </button>
                    ))}
                  </div>
                  <p className="text-xs text-ink/50">{v.depositNote}</p>
                </div>
              )}
            </div>
            <div className={kotak}>
              <p className="text-sm uppercase tracking-wide text-ink/50">{v.key}</p>
              <div className="mt-3 space-y-3 text-sm">
                <button className={btn} disabled={!owner || !!busy} onClick={kunciKu}>
                  {busy === "key" ? "…" : v.makeKey}
                </button>
                {kunciBaru && (
                  <div className="rounded-xl bg-ink/5 p-3">
                    <p className="text-ink/70">{v.keyOnce}</p>
                    <p className="mt-2 break-all font-mono text-xs">{kunciBaru}</p>
                    <p className="mt-2 text-ink/70">{v.keyUse}</p>
                    <p className="mt-1 break-all font-mono text-xs">{`claude mcp add --transport http fabius https://fabius-one.vercel.app/mcp --header "Authorization: Bearer ${kunciBaru}"`}</p>
                  </div>
                )}
                <p className="pt-2 text-ink/60">{v.paste}</p>
                <div className="flex gap-2">
                  <input
                    className="min-w-0 flex-1 rounded-full border border-ink/15 bg-white px-4 py-2 font-mono text-xs"
                    value={kunci}
                    onChange={(e) => setKunci(e.target.value.trim())}
                    placeholder="fabk_…"
                  />
                  <button className={btn} disabled={!KUNCI_RE.test(kunci) || !!busy} onClick={() => jalan("show", () => lihat(kunci))}>
                    {v.show}
                  </button>
                </div>
              </div>
            </div>
            {ak && (
              <div className={`${kotak} lg:col-span-2`}>
                <p className="text-sm uppercase tracking-wide text-ink/50">{v.balance}</p>
                <p className="mt-2 font-display text-3xl text-ink">{fab(ak.balance_atomic)} FAB</p>
                <p className="text-sm text-ink/60">
                  {v.deposited} {fab(ak.deposited_atomic)} · {v.spent} {fab(ak.spent_atomic)} · {ak.wallet}
                </p>
                <p className="mt-4 text-sm uppercase tracking-wide text-ink/50">{v.keys}</p>
                <ul className="mt-1 space-y-1 text-sm">
                  {ak.keys.map((k) => (
                    <li key={k.key_id} className="flex items-center gap-3">
                      <span className="font-mono">{k.key_id}</span>
                      <span className="text-ink/50">{k.active ? "active" : "revoked"}</span>
                      {k.active && owner?.toLowerCase() === ak.wallet && (
                        <button className="text-violet underline disabled:opacity-40" disabled={!!busy} onClick={() => cabut(k.key_id)}>
                          {v.revoke}
                        </button>
                      )}
                    </li>
                  ))}
                </ul>
                <p className="mt-4 text-sm uppercase tracking-wide text-ink/50">{v.records}</p>
                <div className="mt-1 overflow-x-auto">
                  <table className="w-full text-left font-mono text-xs">
                    <tbody>
                      {ak.records.map((r) => (
                        <tr key={r.h} className="border-t border-ink/10">
                          <td className="py-1 pr-3">{r.n}</td>
                          <td className="pr-3">{new Date(r.t * 1000).toISOString().replace(".000Z", "Z")}</td>
                          <td className="pr-3">{r.jenis}</td>
                          <td className="pr-3">{r.alat ?? r.kunci_id ?? (r.tx ? `${r.tx.slice(0, 12)}…` : "")}</td>
                          <td className="pr-3">{r.atomic != null ? `${r.jenis === "potong" ? "-" : "+"}${fab(r.atomic)}` : ""}</td>
                          <td className="pr-3" title={`prev ${r.prev}`}>
                            {r.h.slice(0, 14)}…
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
            )}
          </>
        )}
        {note && <p className="break-all text-sm text-ink/70 lg:col-span-2">{note}</p>}
      </div>
    </section>
  );
}
