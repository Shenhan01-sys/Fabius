"use client";

import { useLang } from "./lang";
import IsoCube from "./ui/IsoCube";

export default function Nav() {
  const { t, lang, setLang } = useLang();
  const links: [string, string][] = [
    ["#journey", t.nav.journey],
    ["#proof", t.nav.proof],
    ["#book", t.nav.book],
    ["#access", t.nav.access],
  ];
  return (
    <header className="fixed inset-x-0 top-0 z-50 flex items-center justify-between px-5 pt-5 sm:px-9 sm:pt-7">
      <a href="#top" className="glass flex items-center gap-2.5 rounded-full py-1.5 pl-2 pr-4 font-display text-[1.1rem] font-semibold tracking-tight text-ink">
        <IsoCube kind="sealed" size={26} />
        Fabius
      </a>
      <nav className="glass hidden items-center gap-1 rounded-full px-2 py-1.5 md:flex">
        {links.map(([href, label]) => (
          <a key={href} href={href} className="rounded-full px-4 py-2 text-[0.92rem] font-medium text-ink/80 transition hover:bg-white/70 hover:text-ink">
            {label}
          </a>
        ))}
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
        <a href="#proof" className="hidden rounded-full bg-ink px-5 py-2.5 text-sm font-semibold text-white transition hover:bg-violet sm:inline-block">
          {t.nav.cta}
        </a>
      </div>
    </header>
  );
}
