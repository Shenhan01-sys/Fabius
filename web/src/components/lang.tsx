"use client";

import { createContext, useContext, useSyncExternalStore, type ReactNode } from "react";
import { copy, type Copy, type Lang } from "@/lib/copy";

// Pilihan bahasa = keadaan luar (localStorage + bahasa peramban). Server selalu "en"; klien membaca sesudah hidrasi tanpa setState di effect.
const listeners = new Set<() => void>();
let chosen: Lang | null = null;

function read(): Lang {
  if (chosen) return chosen;
  try {
    const saved = window.localStorage.getItem("fabius-lang");
    if (saved === "en" || saved === "id") return saved;
    return navigator.language?.toLowerCase().startsWith("id") ? "id" : "en";
  } catch {
    return "en"; // penyimpanan bisa diblokir: bahasa bawaan saja
  }
}

function subscribe(cb: () => void) {
  listeners.add(cb);
  return () => {
    listeners.delete(cb);
  };
}

function choose(l: Lang) {
  chosen = l;
  try {
    window.localStorage.setItem("fabius-lang", l);
  } catch {
    /* abaikan */
  }
  listeners.forEach((f) => f());
}

const Ctx = createContext<{ lang: Lang; t: Copy; setLang: (l: Lang) => void }>({ lang: "en", t: copy.en as Copy, setLang: choose });

export function LangProvider({ children }: { children: ReactNode }) {
  const lang = useSyncExternalStore(subscribe, read, () => "en" as Lang);
  return <Ctx.Provider value={{ lang, t: copy[lang] as Copy, setLang: choose }}>{children}</Ctx.Provider>;
}

export const useLang = () => useContext(Ctx);
