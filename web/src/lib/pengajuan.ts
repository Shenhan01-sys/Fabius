// P161 B1e: jalur pengajuan bot penerbit di web. Skema + pesan EIP-712 + antrean semuanya dari gerbang (`tools/pengajuan.py`); web hanya
// menyusun formulir dari skema, meminta dompet Privy menandatangani pesan yang dihitung gerbang, lalu mengirim.
import { GATE } from "./x402-buy";
import type { RuleVocab } from "./rule";

export type Field = {
  t: "int" | "str" | "text" | "number" | "enum" | "list" | "address" | "url" | "date" | "bool" | "object" | "rule";
  label: string;
  help?: string;
  optional?: boolean;
  min?: number;
  max?: number;
  pattern?: string;
  values?: string[];
  const?: unknown;
  item?: Field | Record<string, Field>;
};
export type Node = Field | { [k: string]: Node };
export const isField = (n: unknown): n is Field => !!n && typeof n === "object" && "t" in (n as object) && "label" in (n as object);

export type SchemaInfo = {
  eip712_name: string;
  version: string;
  chain_id: number;
  max_ttl_s: number;
  templates: Record<string, { param_nama: string; param: number; metode: string }>;
  symbols: string[];
  kill_bounds: Record<string, [number, number]>;
  shadow_days: number;
  kinds_open: string[];
  rule: RuleVocab;
  schema: Record<string, Node>;
};

export type Kiriman = {
  t: number;
  submission_sha: string;
  bot_id: string;
  issuer: string;
  status: "waiting for review" | "queued" | "reviewed" | "rejected" | "shadow" | "in slot";
  review: { vonis: string; report_sha: string; k: number; alpha: number; t_utc: string } | null;
  note: string | null;
  shadow: { days: number; of: number; slot: boolean; started: boolean } | null;
  owner_review?: OwnerReview; // P168: hanya untuk kiriman yang lolos tahap 1 (teks = teks biasa)
};

// P168 (epik 12 §5): kartu peninjau LLM dari gerbang (`engine/peninjau.py::kartu`)
export type OwnerReview = {
  state: "not calibrated" | "pending" | "done" | "failed";
  verdict?: "LANJUT" | "TAHAN" | "TOLAK";
  model_verdict?: string | null;
  coerced?: string[];
  tags?: string[];
  one_line?: string;
  report_sha?: string;
  note?: string;
};

export async function schemaInfo(): Promise<SchemaInfo> {
  const r = await fetch(`${GATE}/bots/schema`, { cache: "no-store" });
  if (!r.ok) throw new Error(`/bots/schema HTTP ${r.status}`);
  return r.json();
}

export async function kiriman(): Promise<Kiriman[]> {
  const r = await fetch(`${GATE}/bots/submissions`, { cache: "no-store" });
  if (!r.ok) throw new Error(`/bots/submissions HTTP ${r.status}`);
  return (await r.json()).submissions;
}

type Jawab = { ok: boolean; status: number; body: Record<string, unknown> };
async function post(path: string, body: unknown): Promise<Jawab> {
  const r = await fetch(`${GATE}${path}`, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(body) });
  return { ok: r.ok, status: r.status, body: await r.json().catch(() => ({})) };
}

export const typedData = (submission: unknown, nonce: number, deadline: number) => post("/bots/typed-data", { submission, nonce, deadline });
export const submit = (submission: unknown, signature: string, nonce: number, deadline: number) =>
  post("/bots/submit", { submission, signature, nonce, deadline });
