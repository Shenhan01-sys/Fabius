import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  // package-lock.json lain ada di folder induk (C:\Users\hansg); akar proyek web adalah folder ini.
  turbopack: { root: process.cwd() },
};

export default nextConfig;
