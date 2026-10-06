"use client";

// P165: SATU login untuk seluruh aplikasi (builder: login di navbar, sebagai popup ala web2 - Google / Telegram / email - bukan kartu per halaman). PrivyProvider dipasang
// sekali di root layout (`Providers`); skrip Telegram dimuat `beforeInteractive` di layout supaya login di Mini App jalan. `useAkses()` memberi status
// login + status anggota (gerbang `GET /access`: login Privy + dompet membeli >= 1 sinyal dalam 7 hari) ke navbar, /popup login (`LoginModal`, dipasang Nav), /desk, /analysts, /buy.

import { createContext, useCallback, useContext, useEffect, useMemo, useRef, useState } from "react";
import { PrivyProvider, useLoginWithOAuth, usePrivy } from "@privy-io/react-auth";
import { GATE, PRIVY_APP_ID, PRIVY_CONFIG } from "@/lib/x402-buy";

export type Anggota = {
  live: boolean;
  status: number; // 200 anggota, 402 login tapi belum membeli, 401 token tidak sah, 0 jaringan
  dompet?: string | string[];
  berlaku_sampai?: number;
  pembelian_terakhir?: { t: number; bot: string; bar: string; tx: string };
  hari?: number;
  tunda_s?: number;
  error?: string;
};

export type AksesCtx = {
  ready: boolean;
  authenticated: boolean;
  login: () => void;
  masukGoogle: () => Promise<void>; // login Google (redirect); hook-nya hidup di Jembatan supaya redirect balik DISELESAIKAN walau popup tertutup
  memproses: boolean; // OAuth sedang diselesaikan sesudah redirect balik
  logout: () => void;
  token: () => Promise<string | null>;
  anggota: Anggota | null; // null = belum diperiksa / belum login
  periksa: () => void; // baca ulang status (mis. sesudah membeli)
  email?: string | null;
  metode?: string | null;
  wallet?: string | null;
  popup: boolean; // popup login / akun terbuka
  bukaLogin: () => void;
  tutupLogin: () => void;
};

const KOSONG: AksesCtx = {
  ready: false,
  authenticated: false,
  login: () => {},
  masukGoogle: async () => {},
  memproses: false,
  logout: () => {},
  token: async () => null,
  anggota: null,
  periksa: () => {},
  popup: false,
  bukaLogin: () => {},
  tutupLogin: () => {},
};
const Ctx = createContext<AksesCtx>(KOSONG);

export const useAkses = () => useContext(Ctx);

export function Providers({ children }: { children: React.ReactNode }) {
  return (
    <PrivyProvider appId={PRIVY_APP_ID} config={PRIVY_CONFIG}>
      <Jembatan>{children}</Jembatan>
    </PrivyProvider>
  );
}

async function bacaAnggota(tok: string): Promise<Anggota> {
  try {
    const r = await fetch(`${GATE}/access`, { cache: "no-store", headers: { Authorization: `Bearer ${tok}` } });
    const b = await r.json();
    return { ...b, live: r.status === 200, status: r.status };
  } catch (e) {
    return { live: false, status: 0, error: String(e) };
  }
}

function Jembatan({ children }: { children: React.ReactNode }) {
  const { ready, authenticated, login, logout, getAccessToken, user } = usePrivy();
  // Privy menyelesaikan login OAuth hanya bila hook ini TER-MOUNT di halaman tempat penyedia mengembalikan pengguna (parameter `privy_oauth_*`).
  // Dulu hook ada di popup (`Masuk`), yang tertutup sesudah redirect: login tidak selesai sampai pengguna menekan "Sign in" lagi. Sekarang selalu hidup.
  const oauth = useLoginWithOAuth();
  const initOAuth = oauth.initOAuth;
  const masukGoogle = useCallback(() => initOAuth({ provider: "google" }).then(() => undefined), [initOAuth]);
  const memproses = oauth.loading;
  const tok = useRef(getAccessToken);
  useEffect(() => {
    tok.current = getAccessToken;
  }, [getAccessToken]);
  const [anggota, setAnggota] = useState<Anggota | null>(null);
  const [n, setN] = useState(0);
  const periksa = useCallback(() => setN((x) => x + 1), []);
  const [popup, setPopup] = useState(false);
  const bukaLogin = useCallback(() => setPopup(true), []);
  const tutupLogin = useCallback(() => setPopup(false), []);

  useEffect(() => {
    let live = true;
    if (!ready || !authenticated) {
      Promise.resolve().then(() => live && setAnggota(null));
      return () => {
        live = false;
      };
    }
    tok.current().then(async (t) => {
      const a = t ? await bacaAnggota(t) : ({ live: false, status: 401 } as Anggota);
      if (live) setAnggota(a);
    });
    return () => {
      live = false;
    };
  }, [ready, authenticated, n]);

  const metode = user?.google ? "Google" : user?.telegram ? "Telegram" : user?.email ? "Email" : null;
  const wallet = user?.wallet?.address ?? null;
  const email = user?.google?.email ?? user?.email?.address ?? (user?.telegram?.username ? `@${user.telegram.username}` : null);
  const value = useMemo<AksesCtx>(
    () => ({
      ready,
      authenticated,
      login: () => login(),
      masukGoogle,
      memproses,
      logout: () => void logout(),
      token: async () => (authenticated ? tok.current() : null),
      anggota,
      periksa,
      email,
      metode,
      wallet,
      popup,
      bukaLogin,
      tutupLogin,
    }),
    [ready, authenticated, login, masukGoogle, memproses, logout, anggota, periksa, email, metode, wallet, popup, bukaLogin, tutupLogin],
  );
  return <Ctx.Provider value={value}>{children}</Ctx.Provider>;
}
