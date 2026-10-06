import type { Metadata } from "next";
import { Archivo, Inter, JetBrains_Mono } from "next/font/google";
import Script from "next/script";
import { Providers } from "@/components/akses";
import "./globals.css";

const archivo = Archivo({ subsets: ["latin"], axes: ["wdth"], style: ["normal", "italic"], variable: "--font-archivo", display: "swap" });
const inter = Inter({ subsets: ["latin"], variable: "--font-inter", display: "swap" });
const jetbrains = JetBrains_Mono({ subsets: ["latin"], variable: "--font-jetbrains", display: "swap" });

export const metadata: Metadata = {
  title: "Fabius — signals sealed before the outcome",
  description:
    "Locked trading bots. Every signal committed on BNB Chain before the market answers, verifiable by anyone. Paper only; no profit claims.",
};

export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return (
    // suppressHydrationWarning: skrip Telegram (beforeInteractive) menulis --tg-viewport-* di <html> sebelum hidrasi; atribut itu milik Telegram
    <html lang="en" className={`${archivo.variable} ${inter.variable} ${jetbrains.variable}`} suppressHydrationWarning>
      <body>
        {/* P165: satu login Privy untuk semua halaman; skrip Telegram sebelum Privy supaya login di Mini App jalan */}
        <Script src="https://telegram.org/js/telegram-web-app.js" strategy="beforeInteractive" />
        <Providers>{children}</Providers>
      </body>
    </html>
  );
}
