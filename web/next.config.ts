import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  // package-lock.json lain ada di folder induk (C:\Users\hansg); akar proyek web adalah folder ini.
  turbopack: { root: process.cwd() },
  // Rute English (P146). Rute lama tetap mengarah ke yang baru: tautan di pesan Telegram yang sudah terkirim memakai /beli dan /analis.
  async redirects() {
    return [
      { source: "/beli", destination: "/buy", permanent: true },
      { source: "/beli/:bot", destination: "/buy/:bot", permanent: true },
      { source: "/analis", destination: "/analysts", permanent: true },
    ];
  },
};

export default nextConfig;
