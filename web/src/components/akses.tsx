"use client";

// P165: satu jalur akses anggota untuk halaman alpha (/desk). Login Privy yang sama dengan /analysts (P145): anggota = akun yang dompetnya membeli
// >= 1 sinyal dalam 7 hari; gerbang memeriksa token di tiap rute meja dan menjawab isi langsung atau tampilan publik tertunda. Halaman tetap tampil
// (tampilan publik) sebelum Privy siap; skrip Telegram dimuat dulu seperti /analysts supaya login di Mini App jalan.

import Script from "next/script";
import { createContext, useContext, useEffect, useMemo, useRef, useState } from "react";
import { PrivyProvider, usePrivy } from "@privy-io/react-auth";
import { PRIVY_APP_ID, PRIVY_CONFIG } from "@/lib/x402-buy";

export type AksesCtx = {
  ready: boolean;
  authenticated: boolean;
  login: () => void;
  logout: () => void;
  token: () => Promise<string | null>;
};

const KOSONG: AksesCtx = { ready: false, authenticated: false, login: () => {}, logout: () => {}, token: async () => null };
const Ctx = createContext<AksesCtx>(KOSONG);

export const useAkses = () => useContext(Ctx);

export function AksesProvider({ children }: { children: React.ReactNode }) {
  const [scriptDone, setScriptDone] = useState(false);
  return (
    <>
      <Script src="https://telegram.org/js/telegram-web-app.js" strategy="afterInteractive" onReady={() => setScriptDone(true)} onError={() => setScriptDone(true)} />
      {scriptDone ? (
        <PrivyProvider appId={PRIVY_APP_ID} config={PRIVY_CONFIG}>
          <Jembatan>{children}</Jembatan>
        </PrivyProvider>
      ) : (
        <Ctx.Provider value={KOSONG}>{children}</Ctx.Provider>
      )}
    </>
  );
}

function Jembatan({ children }: { children: React.ReactNode }) {
  const { ready, authenticated, login, logout, getAccessToken } = usePrivy();
  const tok = useRef(getAccessToken);
  useEffect(() => {
    tok.current = getAccessToken;
  }, [getAccessToken]);
  const value = useMemo<AksesCtx>(
    () => ({ ready, authenticated, login: () => login(), logout: () => void logout(), token: async () => (authenticated ? tok.current() : null) }),
    [ready, authenticated, login, logout],
  );
  return <Ctx.Provider value={value}>{children}</Ctx.Provider>;
}
