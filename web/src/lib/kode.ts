// P167b: editor `kind=code` di web. Kode PRIVAT: formulir yang ditandatangani hanya memuat `spec.kode` = {sha, ukuran, params}; teks kode dikirim
// terpisah (`body.code`) dan gerbang memeriksa ulang semuanya (`engine/kode.py::cocok_meta`: sha, ukuran, PARAMS, daftar-izin AST). Jenis ini
// TERTUTUP sampai builder menyetujui jalur privat (`info.code.open`). Kontrak lintas bahasa: `engine/tests/test_kode.py::WebContractTests`.

export type CodeInfo = {
  open: boolean;
  label: string;
  reviewer_note: string;
  max_bytes: number;
  max_params: number;
  imports: string[];
  builtins: string[];
  template: string;
  limits: Record<string, number>;
  public_copy: string;
};

export type KodeMeta = { sha: string; ukuran: number; params: Record<string, number> };

export const ukuran = (src: string): number => new TextEncoder().encode(src).length;

export async function shaKode(src: string): Promise<string> {
  const buf = await crypto.subtle.digest("SHA-256", new TextEncoder().encode(src));
  return "0x" + Array.from(new Uint8Array(buf), (b) => b.toString(16).padStart(2, "0")).join("");
}

/** PARAMS dari literal sederhana `PARAMS = {"N": 60, "k": 0.5}` (petunjuk di web; gerbang membaca AST yang sebenarnya). null = tidak terbaca. */
export function paramsDari(src: string): Record<string, number> | null {
  const m = /^PARAMS\s*=\s*\{([^}]*)\}\s*$/m.exec(src);
  if (!m) return null;
  const out: Record<string, number> = {};
  const body = m[1].trim();
  if (!body) return out;
  for (const part of body.split(",")) {
    const kv = /^\s*["']([A-Za-z][A-Za-z0-9_]{0,15})["']\s*:\s*(-?\d+(?:\.\d+)?(?:[eE][-+]?\d+)?)\s*$/.exec(part);
    if (!kv) return null;
    out[kv[1]] = Number(kv[2]);
  }
  return out;
}

/** {sha, ukuran, params} untuk `spec.kode`; null bila PARAMS tidak terbaca. */
export async function meta(src: string): Promise<KodeMeta | null> {
  const params = paramsDari(src);
  if (params === null) return null;
  return { sha: await shaKode(src), ukuran: ukuran(src), params };
}
