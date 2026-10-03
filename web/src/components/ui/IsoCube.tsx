// Kubus isometrik SVG: penanda satu blok/sinyal di luar kanvas 3D. Warna = keadaan (docs/design/landing.md), satu bahasa dengan kristal.
import type { CellState } from "@/lib/snapshot";

type Kind = CellState | "empty" | "core";

const FACES: Record<Kind, { top: string; left: string; right: string; stroke: string; dash?: string; op?: number }> = {
  future: { top: "rgba(255,255,255,.55)", left: "rgba(255,255,255,.3)", right: "rgba(255,255,255,.18)", stroke: "rgba(160,140,230,.45)", dash: "3 4", op: 0.75 },
  empty: { top: "rgba(255,255,255,.75)", left: "rgba(236,232,250,.7)", right: "rgba(221,213,246,.7)", stroke: "rgba(160,140,230,.6)" },
  prelock: { top: "#e9e4fb", left: "#d9d1f5", right: "#c9bdf2", stroke: "#a99bdc", dash: "2 3" },
  pending: { top: "rgba(157,134,255,.25)", left: "rgba(157,134,255,.15)", right: "rgba(157,134,255,.1)", stroke: "#6e4bff", dash: "4 3" },
  sealed: { top: "#5a45d6", left: "#3a29b8", right: "#24157e", stroke: "#24157e" },
  verified: { top: "#ffffff", left: "#efe9ff", right: "#d8ccff", stroke: "#b9a6ff" },
  core: { top: "#ffffff", left: "#f3efff", right: "#e4dcff", stroke: "#ffffff" },
  gap: { top: "rgba(255,90,110,.18)", left: "rgba(255,90,110,.1)", right: "rgba(255,90,110,.06)", stroke: "#ff5a6e", dash: "2 2" },
  missed: { top: "rgba(255,90,110,.35)", left: "rgba(255,90,110,.25)", right: "rgba(255,90,110,.18)", stroke: "#ff5a6e" },
};

export default function IsoCube({ kind, size = 40, className = "", glow = false }: { kind: Kind; size?: number; className?: string; glow?: boolean }) {
  const f = FACES[kind];
  return (
    <svg viewBox="0 0 100 100" width={size} height={size} className={className} style={{ opacity: f.op ?? 1, overflow: "visible" }} aria-hidden>
      {glow && (
        <defs>
          <radialGradient id="g" cx="50%" cy="50%" r="50%">
            <stop offset="0%" stopColor="#c8b8ff" stopOpacity="0.9" />
            <stop offset="100%" stopColor="#c8b8ff" stopOpacity="0" />
          </radialGradient>
        </defs>
      )}
      {glow && <circle cx="50" cy="52" r="58" fill="url(#g)" />}
      <g stroke={f.stroke} strokeWidth="1.6" strokeDasharray={f.dash} strokeLinejoin="round">
        <path d="M50 8 L88 30 L50 52 L12 30 Z" fill={f.top} />
        <path d="M12 30 L50 52 L50 94 L12 72 Z" fill={f.left} />
        <path d="M50 52 L88 30 L88 72 L50 94 Z" fill={f.right} />
      </g>
      {kind === "gap" && <path d="M30 40 L44 56 L38 64 L54 82" stroke="#ff5a6e" strokeWidth="2.2" fill="none" />}
      {kind === "prelock" && (
        <g transform="translate(50 60)" stroke="#8b7fd0" strokeWidth="3" fill="none">
          <rect x="-9" y="-2" width="18" height="14" rx="2" fill="#f4f1ff" />
          <path d="M-5 -2 V-7 a5 5 0 0 1 10 0 V-2" />
        </g>
      )}
    </svg>
  );
}
