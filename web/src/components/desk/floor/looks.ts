// Template pekerja 3D (P159). Agent baru TIDAK perlu desain manual: penampilannya dibuat deterministik dari slug (warna kaus keluarga violet/ink
// Fabius, kulit + rambut beragam, aksesori + benda meja), lalu ditimpa oleh `npc` dari config/agents.json bila ada (dikirim gerbang di /desk).
// Jalan pintas mengubah penampilan satu agent: isi `npc` di entri agent itu (`tools/analis.py tambah --extra glasses --short Kimi ...`).

export type Extra = "headset" | "cap" | "glasses" | "beanie" | "hood" | "none";
export type Prop = "mug" | "paper" | "plant" | "books";
export type Look = { shirt: string; hair: string; skin: string; extra: Extra; prop: Prop; short: string };
export type NpcHint = Partial<Look> | null | undefined;

const SHIRTS = ["#6e4bff", "#9d86ff", "#15122b", "#1a1442", "#c9bdf2", "#8b86a6", "#4b33c7", "#ddd5f6"];
const SKINS = ["#f1c9a5", "#e0ac80", "#c68e63", "#a8714a", "#8d5a3b", "#5c3a24"];
const HAIRS = ["#15122b", "#2a2140", "#3b2a1e", "#6b4a2b", "#d8c3a5", "#8b86a6", "#9d86ff"];
const EXTRAS: Extra[] = ["headset", "cap", "glasses", "beanie", "hood", "none"];
const PROPS: Prop[] = ["mug", "paper", "plant", "books"];

// FNV-1a 32 bit: slug yang sama selalu menghasilkan pekerja yang sama di semua browser
function hash(s: string): number {
  let h = 0x811c9dc5;
  for (let i = 0; i < s.length; i++) {
    h ^= s.charCodeAt(i);
    h = Math.imul(h, 0x01000193) >>> 0;
  }
  return h;
}

export function shortName(nama: string): string {
  const n = nama.replace(/^v2 · /, "").replace(/^Fabius Analyst · /, "").trim();
  return n.split(/\s+/)[0]?.slice(0, 14) || n.slice(0, 14);
}

export function lookFor(slug: string, nama: string, hint: NpcHint): Look {
  const h = hash(slug);
  const pick = <T,>(xs: T[], shift: number) => xs[(h >>> shift) % xs.length];
  const base: Look = {
    shirt: pick(SHIRTS, 0),
    skin: pick(SKINS, 5),
    hair: pick(HAIRS, 10),
    extra: pick(EXTRAS, 15),
    prop: pick(PROPS, 20),
    short: shortName(nama),
  };
  const ok = Object.fromEntries(Object.entries(hint ?? {}).filter(([, v]) => v !== undefined && v !== null && v !== "")) as Partial<Look>;
  return { ...base, ...ok };
}

// nama pendek ganda (mis. dua model "Qwen ...") diberi kata kedua supaya label tetap bisa dibedakan
export function dedupeShort<T extends { look: Look; nama: string }>(seats: T[]): T[] {
  const count = new Map<string, number>();
  seats.forEach((s) => count.set(s.look.short, (count.get(s.look.short) ?? 0) + 1));
  return seats.map((s) => {
    if ((count.get(s.look.short) ?? 0) < 2) return s;
    const w = s.nama.replace(/^v2 · /, "").replace(/^Fabius Analyst · /, "").split(/\s+/);
    const extra = w.find((x, i) => i > 0 && /^[A-Za-z]/.test(x)) ?? w[1] ?? "";
    return { ...s, look: { ...s.look, short: `${s.look.short} ${extra}`.slice(0, 16) } };
  });
}
