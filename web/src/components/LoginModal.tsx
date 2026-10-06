"use client";

// P165 (revisi builder 6 Okt): login = popup ala web2, bukan halaman. Google dan Telegram langsung ke penyedianya lewat Privy headless
// (`useLoginWithOAuth`, `useLoginWithTelegram`), email = kode 6 digit di dalam popup (`useLoginWithEmail`). Sudah login -> kartu akun: dompet,
// status anggota (gerbang GET /access), beli 1 sinyal, keluar. Dibuka dari chip navbar dan "Sign in" di halaman alpha; dipasang sekali di Nav.

import Link from "next/link";
import { AnimatePresence, motion, useReducedMotion } from "motion/react";
import { useEffect, useRef, useState } from "react";
import { useLoginWithEmail, useLoginWithOAuth, useLoginWithTelegram } from "@privy-io/react-auth";
import { useAkses } from "./akses";
import { useLang } from "./lang";
import IsoCube from "./ui/IsoCube";

const tgl = (s?: number) => (s ? new Date(s * 1000).toISOString().slice(0, 16).replace("T", " ") + "Z" : "-");
const pendek = (w?: string | null) => (w ? `${w.slice(0, 6)}…${w.slice(-4)}` : "-");
const pesan = (e: unknown) => (e instanceof Error ? e.message : String(e)).replace(/^Error:\s*/, "").slice(0, 160);

function GoogleIcon() {
  return (
    <svg viewBox="0 0 48 48" className="h-5 w-5" aria-hidden>
      <path fill="#FFC107" d="M43.6 20.5H42V20H24v8h11.3C33.6 32.7 29.2 36 24 36c-6.6 0-12-5.4-12-12s5.4-12 12-12c3.1 0 5.8 1.2 7.9 3.1l5.7-5.7C34 6.1 29.3 4 24 4 12.9 4 4 12.9 4 24s8.9 20 20 20 20-8.9 20-20c0-1.3-.1-2.4-.4-3.5z" />
      <path fill="#FF3D00" d="M6.3 14.7l6.6 4.8C14.7 15.1 19 12 24 12c3.1 0 5.8 1.2 7.9 3.1l5.7-5.7C34 6.1 29.3 4 24 4 16.3 4 9.7 8.3 6.3 14.7z" />
      <path fill="#4CAF50" d="M24 44c5.2 0 9.9-2 13.4-5.2l-6.2-5.2C29.2 35.1 26.7 36 24 36c-5.2 0-9.6-3.3-11.3-8l-6.5 5C9.5 39.6 16.2 44 24 44z" />
      <path fill="#1976D2" d="M43.6 20.5H42V20H24v8h11.3c-.8 2.2-2.2 4.2-4.1 5.6l6.2 5.2C37 39.2 44 34 44 24c0-1.3-.1-2.4-.4-3.5z" />
    </svg>
  );
}

function TelegramIcon() {
  return (
    <svg viewBox="0 0 24 24" className="h-5 w-5" aria-hidden>
      <circle cx="12" cy="12" r="12" fill="#229ED9" />
      <path fill="#fff" d="M17.6 7.2 15.7 16.6c-.1.6-.5.8-1 .5l-2.9-2.1-1.4 1.3c-.2.2-.3.3-.6.3l.2-2.9 5.3-4.8c.2-.2 0-.3-.3-.1l-6.6 4.1-2.8-.9c-.6-.2-.6-.6.1-.9l11-4.2c.5-.2.9.1.9.4z" />
    </svg>
  );
}

const Spin = () => <span className="inline-block h-4 w-4 animate-spin rounded-full border-2 border-current border-r-transparent" aria-hidden />;

export default function LoginModal() {
  const ak = useAkses();
  const reduced = useReducedMotion();
  const kartu = useRef<HTMLDivElement>(null);
  const { tutupLogin, popup } = ak;

  useEffect(() => {
    if (!popup) return;
    const prev = document.activeElement as HTMLElement | null;
    const t = setTimeout(() => kartu.current?.querySelector<HTMLElement>("button, input")?.focus(), 60);
    const key = (e: KeyboardEvent) => {
      if (e.key === "Escape") tutupLogin();
      if (e.key === "Tab" && kartu.current) {
        const f = kartu.current.querySelectorAll<HTMLElement>("button:not([disabled]), input, a[href]");
        if (!f.length) return;
        const first = f[0], last = f[f.length - 1];
        if (e.shiftKey && document.activeElement === first) {
          e.preventDefault();
          last.focus();
        } else if (!e.shiftKey && document.activeElement === last) {
          e.preventDefault();
          first.focus();
        }
      }
    };
    window.addEventListener("keydown", key);
    const overflow = document.body.style.overflow;
    document.body.style.overflow = "hidden";
    return () => {
      clearTimeout(t);
      window.removeEventListener("keydown", key);
      document.body.style.overflow = overflow;
      prev?.focus?.();
    };
  }, [popup, tutupLogin]);

  return (
    <AnimatePresence>
      {popup && (
        <motion.div
          key="latar"
          className="fixed inset-0 z-[70] flex items-end justify-center bg-ink/30 p-3 backdrop-blur-sm sm:items-center sm:p-6"
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          exit={{ opacity: 0 }}
          transition={{ duration: reduced ? 0 : 0.2 }}
          onMouseDown={(e) => e.target === e.currentTarget && tutupLogin()}
        >
          <motion.div
            ref={kartu}
            role="dialog"
            aria-modal="true"
            aria-labelledby="login-judul"
            className="relative w-full max-w-[420px] overflow-hidden rounded-[28px] border border-white/70 bg-white shadow-[0_30px_80px_-20px_rgba(21,18,43,0.45)]"
            initial={reduced ? false : { y: 28, scale: 0.96, opacity: 0 }}
            animate={{ y: 0, scale: 1, opacity: 1 }}
            exit={reduced ? { opacity: 0 } : { y: 16, scale: 0.98, opacity: 0 }}
            transition={{ type: "spring", stiffness: 380, damping: 32 }}
          >
            <div className="pointer-events-none absolute inset-x-0 top-0 h-36 bg-gradient-to-b from-lav to-white" aria-hidden />
            <button
              onClick={tutupLogin}
              className="absolute right-4 top-4 z-10 grid h-9 w-9 place-items-center rounded-full text-ink/50 transition-colors hover:bg-ink/5 hover:text-ink"
              aria-label="close"
            >
              ✕
            </button>
            <div className="relative px-7 pb-7 pt-9 sm:px-8">{ak.authenticated ? <Akun /> : <Masuk />}</div>
          </motion.div>
        </motion.div>
      )}
    </AnimatePresence>
  );
}

function Masuk() {
  const { t } = useLang();
  const v = t.login;
  const reduced = useReducedMotion();
  const [langkah, setLangkah] = useState<"awal" | "kode">("awal");
  const [email, setEmail] = useState("");
  const [kode, setKode] = useState("");
  const [sibuk, setSibuk] = useState<"" | "google" | "telegram" | "kirim" | "cek">("");
  const [galat, setGalat] = useState("");
  const oauth = useLoginWithOAuth();
  const tg = useLoginWithTelegram();
  const em = useLoginWithEmail();

  const jalan = async (k: typeof sibuk, f: () => Promise<void>, sesudah?: () => void) => {
    setSibuk(k);
    setGalat("");
    try {
      await f();
      sesudah?.();
    } catch (e) {
      setGalat(pesan(e));
    } finally {
      setSibuk("");
    }
  };
  const geser = reduced ? {} : { initial: { opacity: 0, x: 24 }, animate: { opacity: 1, x: 0 }, exit: { opacity: 0, x: -24 }, transition: { duration: 0.22 } };
  const tombol = "flex w-full items-center justify-center gap-3 rounded-2xl border px-4 py-3 text-[15px] font-medium transition-colors disabled:cursor-not-allowed disabled:opacity-50";

  return (
    <>
      <div className="flex flex-col items-center text-center">
        <IsoCube kind="sealed" size={44} />
        <h2 id="login-judul" className="mt-4 font-display text-[1.7rem] font-[400] leading-tight tracking-[-0.01em] text-ink">
          {v.welcome}
        </h2>
        <p className="mt-1.5 text-sm leading-snug text-ink/60">{v.welcomeSub}</p>
      </div>
      <AnimatePresence mode="wait" initial={false}>
        {langkah === "awal" ? (
          <motion.div key="awal" className="mt-7 space-y-3" {...geser}>
            <button
              className={`${tombol} border-ink/15 bg-white text-ink hover:border-ink/30 hover:bg-ink/[0.02]`}
              disabled={!!sibuk}
              onClick={() => jalan("google", () => oauth.initOAuth({ provider: "google" }))}
            >
              {sibuk === "google" ? <Spin /> : <GoogleIcon />}
              {sibuk === "google" ? v.redirecting.replace("{p}", "Google") : v.google}
            </button>
            <button
              className={`${tombol} border-transparent bg-[#229ED9] text-white hover:bg-[#1c8cc2]`}
              disabled={!!sibuk}
              onClick={() => jalan("telegram", () => tg.login())}
            >
              {sibuk === "telegram" ? <Spin /> : <TelegramIcon />}
              {sibuk === "telegram" ? v.redirecting.replace("{p}", "Telegram") : v.telegram}
            </button>
            <div className="flex items-center gap-3 py-2 text-xs text-ink/40">
              <span className="h-px flex-1 bg-ink/10" />
              {v.orEmail}
              <span className="h-px flex-1 bg-ink/10" />
            </div>
            <form
              className="space-y-3"
              onSubmit={(e) => {
                e.preventDefault();
                jalan("kirim", () => em.sendCode({ email: email.trim() }), () => setLangkah("kode"));
              }}
            >
              <input
                type="email"
                required
                autoComplete="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                placeholder={v.emailPlaceholder}
                className="w-full rounded-2xl border border-ink/15 bg-white px-4 py-3 text-[15px] text-ink outline-none transition-shadow placeholder:text-ink/35 focus:border-violet focus:shadow-[0_0_0_4px_rgba(110,75,255,0.12)]"
              />
              <button className={`${tombol} border-transparent bg-ink text-white hover:bg-violet`} disabled={!!sibuk || !email.includes("@")}>
                {sibuk === "kirim" && <Spin />}
                {sibuk === "kirim" ? v.sending : v.continue}
              </button>
            </form>
          </motion.div>
        ) : (
          <motion.form
            key="kode"
            className="mt-7 space-y-3"
            {...geser}
            onSubmit={(e) => {
              e.preventDefault();
              jalan("cek", () => em.loginWithCode({ code: kode.trim() }));
            }}
          >
            <p className="text-center text-sm text-ink/70">{v.codeSent.replace("{e}", email)}</p>
            <label className="sr-only" htmlFor="kode-login">
              {v.codeLabel}
            </label>
            <input
              id="kode-login"
              inputMode="numeric"
              autoComplete="one-time-code"
              maxLength={6}
              value={kode}
              onChange={(e) => setKode(e.target.value.replace(/\D/g, ""))}
              placeholder="••••••"
              className="w-full rounded-2xl border border-ink/15 bg-white px-4 py-3 text-center font-mono text-2xl tracking-[0.6em] text-ink outline-none focus:border-violet focus:shadow-[0_0_0_4px_rgba(110,75,255,0.12)]"
            />
            <button className={`${tombol} border-transparent bg-ink text-white hover:bg-violet`} disabled={!!sibuk || kode.length !== 6}>
              {sibuk === "cek" && <Spin />}
              {sibuk === "cek" ? v.verifying : v.verify}
            </button>
            <div className="flex justify-between text-xs">
              <button type="button" className="text-ink/50 underline-offset-2 hover:underline" onClick={() => (setLangkah("awal"), setKode(""), setGalat(""))}>
                ← {v.otherEmail}
              </button>
              <button type="button" className="text-violet underline-offset-2 hover:underline" disabled={!!sibuk} onClick={() => jalan("kirim", () => em.sendCode({ email }))}>
                {v.resend}
              </button>
            </div>
          </motion.form>
        )}
      </AnimatePresence>
      {galat && (
        <p role="alert" className="mt-3 rounded-xl bg-ink/5 px-3 py-2 text-xs text-ink/70">
          {v.error}: {galat}
        </p>
      )}
      <p className="mt-6 text-center text-[11px] leading-snug text-ink/45">{v.newHere}</p>
    </>
  );
}

function Akun() {
  const { t } = useLang();
  const v = t.login;
  const ak = useAkses();
  const a = ak.anggota;
  const [salin, setSalin] = useState(false);
  const nama = ak.email ?? pendek(ak.wallet);
  const huruf = (nama.replace(/^@/, "")[0] ?? "F").toUpperCase();
  const link = "rounded-2xl border border-ink/10 px-4 py-2.5 text-center text-sm text-ink transition-colors hover:border-violet hover:text-violet";
  return (
    <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ duration: 0.2 }}>
      <p className="text-xs uppercase tracking-wide text-ink/45">{v.account}</p>
      <div className="mt-3 flex items-center gap-3">
        <span className="grid h-12 w-12 shrink-0 place-items-center rounded-full bg-violet text-lg font-semibold text-white">{huruf}</span>
        <div className="min-w-0">
          <p id="login-judul" className="truncate font-display text-lg text-ink">
            {nama}
          </p>
          {ak.metode && <p className="text-xs text-ink/50">{v.via.replace("{m}", ak.metode)}</p>}
        </div>
      </div>
      <div className="mt-4 flex items-center justify-between gap-2 rounded-2xl bg-lav/60 px-4 py-2.5">
        <span className="min-w-0 truncate font-mono text-xs text-ink/70">
          {v.wallet} {pendek(ak.wallet)}
        </span>
        {ak.wallet && (
          <button
            className="shrink-0 text-xs font-medium text-violet"
            onClick={() => {
              navigator.clipboard?.writeText(ak.wallet ?? "").then(() => {
                setSalin(true);
                setTimeout(() => setSalin(false), 1500);
              });
            }}
          >
            {salin ? v.copied : v.copy}
          </button>
        )}
      </div>
      <div className={`mt-3 rounded-2xl border p-4 ${a?.live ? "border-violet/30 bg-violet/5" : "border-ink/10"}`}>
        {!a ? (
          <p className="flex items-center gap-2 text-sm text-ink/50">
            <Spin /> {v.checking}
          </p>
        ) : a.live ? (
          <>
            <p className="flex items-center gap-2 font-medium text-violet">
              <span className="inline-block h-2 w-2 rounded-full bg-violet" aria-hidden />
              {v.member.replace("{d}", tgl(a.berlaku_sampai))}
            </p>
            {a.pembelian_terakhir && <p className="mt-1 text-xs text-ink/60">{v.lastBuy.replace("{bot}", a.pembelian_terakhir.bot).replace("{bar}", a.pembelian_terakhir.bar)}</p>}
          </>
        ) : a.status === 402 ? (
          <>
            <p className="font-medium text-ink">🔒 {v.notMember}</p>
            <p className="mt-1 text-sm leading-snug text-ink/60">{v.notMemberSub}</p>
            <Link
              href="/buy"
              onClick={ak.tutupLogin}
              className="mt-3 block rounded-2xl bg-ink px-4 py-3 text-center text-[15px] font-medium text-white transition-colors hover:bg-violet"
            >
              {v.buy}
            </Link>
          </>
        ) : (
          <p className="break-all text-sm text-ink/70">
            {v.error}: {a.error ?? `HTTP ${a.status}`}
          </p>
        )}
      </div>
      <div className="mt-3 grid grid-cols-2 gap-2">
        <Link href="/desk" onClick={ak.tutupLogin} className={link}>
          {v.openDesk}
        </Link>
        <Link href="/analysts" onClick={ak.tutupLogin} className={link}>
          {v.openAnalysts}
        </Link>
      </div>
      <button
        className="mt-4 w-full text-center text-sm text-ink/50 underline-offset-2 hover:text-ink hover:underline"
        onClick={() => {
          ak.logout();
          ak.tutupLogin();
        }}
      >
        {v.signOut}
      </button>
    </motion.div>
  );
}
