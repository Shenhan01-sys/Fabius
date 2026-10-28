// Data shapes the desk scenes read, copied from web/src/lib/desk.ts (gateway GET /desk and GET /desk/fabius). Only what the scenes use.

export type Target = { w: number; k: number; alasan?: string };
export type Keputusan = {
  ringkasan: string;
  target: Record<string, Target>;
  bot?: string;
  skor_bot?: Record<string, number>;
  nilai_bot?: Record<string, number>;
  instrumen?: (string | { aset: string; k: number })[];
};
export type Npc = {
  shirt?: string;
  hair?: string;
  skin?: string;
  extra?: 'headset' | 'cap' | 'glasses' | 'beanie' | 'hood' | 'none';
  prop?: 'mug' | 'paper' | 'plant' | 'books';
  short?: string;
};
export type Buku = {
  agent: string;
  nama: string;
  versi?: number;
  ekuitas: number;
  hasil_pct: number;
  biaya: number;
  n_trade: number;
  posisi: Record<string, number>;
  deret: [number, number][];
  status_terakhir: string | null;
  keputusan_terakhir: Keputusan | null;
  siklus_terakhir?: number | null;
  isi_terakhir?: number;
  n_posisi?: number;
  terkunci?: boolean;
  kursi?: 'aktif' | 'uji' | 'antre' | 'keluar' | null;
  luar?: boolean;
  npc?: Npc | null;
};
export type Siklus = { siklus: number; root: string; tx: string | null; status: string; n: number };
export type Desk = {
  t: number;
  buku: Buku[];
  siklus_terakhir: Siklus | null;
  siklus_12?: Siklus[];
  siklus_24j: number;
  komit_24j: number;
  kursi?: Record<string, 'aktif' | 'uji' | 'antre' | 'keluar'>;
  anchor?: string;
};
export type LiveAgent = { slug: string; status: string; kursi: string | null; bot?: string | null };
export type Pipa = {
  siklus: number;
  rumus: string;
  bot: string | null;
  skor_bot: number | null;
  dasar: string | null;
  instrumen: string[];
  target: Record<string, number>;
  isi: number;
  masuk: string[];
  aktif: string[];
  agen: LiveAgent[];
  root: string | null;
  tx: string | null;
  status: string | null;
  maks_slot?: number;
  slot_n?: number;
  terkunci?: boolean;
};
export type TapeRow = { siklus: number; bot: string | null; dasar: string | null; instrumen: string[]; masuk: number; isi: unknown[]; ekuitas: number; hash: string };
export type LiveBookData = {
  mulai: number;
  siklus_terakhir: number;
  modal_awal: number;
  ekuitas: number;
  hasil_pct: number;
  siklus: number;
  pipa: Pipa;
  pita_keputusan: TapeRow[];
};
export type Lock = { label: string; what: string; at_utc: string | null; tx: string | null; where: string };
