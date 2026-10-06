// /login (P165, builder 6 Okt: satu login lewat navbar + halaman sendiri, bukan kartu login di /desk dan /analysts): login Privy, akun + dompet,
// status anggota (gerbang GET /access), lalu kembali ke halaman asal (?next=/desk).
import type { Metadata } from "next";
import LoginView from "@/components/login/LoginView";

export const metadata: Metadata = {
  title: "Sign in — Fabius",
  description: "One sign-in for Fabius. Members (one signal bought in the last 7 days) see the AI desk live and every analyst's reasoning before the bar closes.",
};

export default async function Page({ searchParams }: { searchParams: Promise<{ next?: string }> }) {
  const { next } = await searchParams;
  // hanya path internal (bukan "//host" atau URL luar) supaya tautan login tidak bisa dipakai untuk mengalihkan ke situs lain
  const aman = next && next.startsWith("/") && !next.startsWith("//") ? next : undefined;
  return <LoginView next={aman} />;
}
