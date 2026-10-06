"use client";

// P165: satu baris status akses di halaman alpha (/desk, /analysts) - pengganti kartu login per halaman. Login + akun = popup (LoginModal).

import Link from "next/link";
import { useAkses } from "./akses";
import { useLang } from "./lang";

const tgl = (s?: number) => (s ? new Date(s * 1000).toISOString().slice(0, 16).replace("T", " ") + "Z" : "-");

export default function AccessLine({ publik }: { publik: "publicDesk" | "publicAnalysts" }) {
  const { t } = useLang();
  const v = t.login.line;
  const ak = useAkses();
  const a = ak.anggota;
  if (ak.authenticated && a?.live)
    return (
      <p className="flex items-center gap-2 text-sm text-violet">
        <span className="inline-block h-2 w-2 rounded-full bg-violet" aria-hidden />
        {v.member.replace("{d}", tgl(a.berlaku_sampai))}
      </p>
    );
  const masuk = ak.authenticated;
  return (
    <p className="text-sm leading-snug text-ink/60">
      🔒 {masuk ? v.signedNoBuy : v[publik]}{" "}
      {masuk ? (
        <Link href="/buy" className="whitespace-nowrap font-medium text-violet underline-offset-2 hover:underline">
          {v.buy} →
        </Link>
      ) : (
        <button onClick={ak.bukaLogin} className="whitespace-nowrap font-medium text-violet underline-offset-2 hover:underline">
          {v.signIn} →
        </button>
      )}
    </p>
  );
}
