// /account (P157, F5, F-D111): akun MCP berbayar - deposit FAB lewat x402, kunci API dari tanda tangan dompet, saldo + riwayat potongan.
// Selama sakelar gerbang FABIUS_F5 mati, halaman ini hanya menjelaskan statusnya (tidak ada tautan navbar sampai builder membukanya).
import type { Metadata } from "next";
import AkunView from "@/components/akun/AkunView";

export const metadata: Metadata = {
  title: "MCP account — Fabius",
  description: "Deposit FAB with x402, get an API key by signing with your wallet, and pay per call for Fabius MCP signal tools (BNB testnet, no value).",
};

export default function Page() {
  return <AkunView />;
}
