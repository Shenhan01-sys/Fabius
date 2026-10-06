"use client";

import Link from "next/link";
import { useEffect, useRef, useState } from "react";
import { useAkses } from "./akses";
import LoginModal from "./LoginModal";
import { useLang } from "./lang";
import IsoCube from "./ui/IsoCube";

const itemCls = "rounded-full px-2.5 py-2 text-[0.86rem] font-medium text-ink/80 transition hover:bg-white/70 hover:text-ink xl:px-4 xl:text-[0.92rem]";

// Menu pengajuan (disclosure): tombol + daftar tautan; tutup dengan klik di luar, Escape, atau memilih tautan.
function SubmitMenu({ label, items }: { label: string; items: [string, string][] }) {
  const [open, setOpen] = useState(false);
  const box = useRef<HTMLDivElement>(null);
  useEffect(() => {
    if (!open) return;
    const away = (e: MouseEvent) => {
      if (box.current && !box.current.contains(e.target as Node)) setOpen(false);
    };
    const esc = (e: KeyboardEvent) => e.key === "Escape" && setOpen(false);
    document.addEventListener("mousedown", away);
    document.addEventListener("keydown", esc);
    return () => {
      document.removeEventListener("mousedown", away);
      document.removeEventListener("keydown", esc);
    };
  }, [open]);
  return (
    <div ref={box} className="relative">
      <button type="button" aria-expanded={open} aria-haspopup="true" onClick={() => setOpen((o) => !o)} className={`${itemCls} flex items-center gap-1`}>
        {label}
        <span aria-hidden className={`text-[0.7em] transition-transform ${open ? "rotate-180" : ""}`}>
          ▾
        </span>
      </button>
      {open && (
        <ul className="glass absolute left-0 top-full z-10 mt-2 min-w-40 rounded-2xl p-1.5 shadow-sm">
          {items.map(([href, text]) => (
            <li key={href}>
              <Link href={href} onClick={() => setOpen(false)} className="block whitespace-nowrap rounded-xl px-3.5 py-2 text-[0.9rem] font-medium text-ink/80 transition hover:bg-white/80 hover:text-ink">
                {text}
              </Link>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}

export default function Nav() {
  const { t, lang, setLang } = useLang();
  const ak = useAkses();
  // Satu nav untuk semua halaman: bagian landing lewat "/#...", halaman lain lewat path sendiri.
  const links: [string, string][] = [
    ["/#journey", t.nav.journey],
    ["/#proof", t.nav.proof],
    ["/#book", t.nav.book],
    ["/verify", t.nav.verify],
    ["/status", t.nav.status],
    ["/analysts", t.nav.analysts],
    ["/desk", t.nav.desk],
    ["/#access", t.nav.access],
  ];
  // F-D123: bot dan agent punya halaman pengajuan SENDIRI-sendiri; satu menu "Submit" supaya navbar tidak melebar.
  const submits: [string, string][] = [
    ["/submit", t.nav.submit],
    ["/submit-agent", t.nav.submitAgent],
  ];
  const pos = links.findIndex(([h]) => h === "/desk") + 1;
  return (
    <header className="fixed inset-x-0 top-0 z-50 flex items-center justify-between px-5 pt-5 sm:px-9 sm:pt-7">
      <Link href="/" className="glass flex items-center gap-2.5 rounded-full py-1.5 pl-2 pr-4 font-display text-[1.1rem] font-semibold tracking-tight text-ink">
        <IsoCube kind="sealed" size={26} />
        Fabius
      </Link>
      <nav className="glass hidden items-center gap-1 rounded-full px-2 py-1.5 md:flex">
        {[...links.slice(0, pos), ["menu", t.nav.submitMenu] as [string, string], ...links.slice(pos)].map(([href, label]) =>
          href === "menu" ? (
            <SubmitMenu key="menu" label={label} items={submits} />
          ) : (
            <Link key={href} href={href} className={itemCls}>
              {label}
            </Link>
          ),
        )}
      </nav>
      <div className="flex items-center gap-2">
        <button
          onClick={() => setLang(lang === "en" ? "id" : "en")}
          className="glass rounded-full px-3.5 py-2 font-mono text-xs font-semibold tracking-widest text-ink/80"
          aria-label="language"
        >
          <span className={lang === "en" ? "text-violet" : ""}>EN</span>
          <span className="mx-1 text-ink/30">/</span>
          <span className={lang === "id" ? "text-violet" : ""}>ID</span>
        </button>
        {/* P165: satu login untuk seluruh situs = popup (LoginModal); status anggota sama dengan yang dipakai /desk + /analysts */}
        <button
          onClick={ak.bukaLogin}
          className={`glass flex items-center gap-1.5 rounded-full px-3.5 py-2 text-xs font-semibold transition-colors hover:text-violet ${ak.anggota?.live ? "text-violet" : "text-ink/80"}`}
        >
          {ak.authenticated && <span className={`inline-block h-2 w-2 rounded-full ${ak.anggota?.live ? "bg-violet" : "bg-ink/30"}`} aria-hidden />}
          {ak.authenticated ? (ak.anggota?.live ? t.nav.member : t.nav.signedIn) : ak.memproses ? "…" : t.nav.signIn}
        </button>
        <Link href="/#proof" className="hidden rounded-full bg-ink px-5 py-2.5 text-sm font-semibold text-white transition hover:bg-violet lg:inline-block">
          {t.nav.cta}
        </Link>
      </div>
      <LoginModal />
    </header>
  );
}
