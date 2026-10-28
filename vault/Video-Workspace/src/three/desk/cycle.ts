// One Live Book cycle as the pipeline scene needs it, built from the public snapshot.
//
// The public gateway hides the live cycle's contents for 24 h (P165): bot, score, target and positions are members-only (pipa.terkunci,
// only the count slot_n is public). So there are three ready-made cycles:
//   LIVE_CYCLE      exactly the public live cycle: 6/6 agents valid, formula r4, bot hidden, 5 positions hidden, sealed on chain 97.
//   REVEALED_CYCLE  the newest decision the public tape has revealed (24 h old): its bot and score parsed from the tape's `dasar` text.
//   DEFAULT_CYCLE   LIVE_CYCLE with the bot/score from REVEALED_CYCLE so the robot has an id and the orbit a winner (provenance in `note`).

import { DESK, LIVE_BOOK } from '../snapshot';
import type { Desk, LiveBookData } from './types';

export const BOTS = ['B1-TREND', 'B2-RS', 'B3-CARRY', 'B4-LISTING-FADE', 'B5-CORE-RWA', 'B6-BOUNCE'];

export type CycleAgent = { slug: string; ok: boolean; trial: boolean };
export type PipelineCycle = {
  /** cycle start, unix seconds */
  siklus: number;
  rumus: string;
  agents: CycleAgent[];
  /** winning bot = the rule the robot applies; null = hidden (public view) */
  bot: string | null;
  score: number | null;
  /** bot -> formula value (orbit cube size); empty = unknown, all cubes minimum size */
  nilai: Record<string, number>;
  /** asset -> signed weight (book bars, site style); empty when hidden or flat */
  target: Record<string, number>;
  /** open positions; with an empty target these are drawn as equal "locked" bars (contents members-only) */
  positions: number;
  sealed: boolean;
  tx: string | null;
  note: string;
};

const hhmm = (s: number) => new Date(s * 1000).toISOString().slice(11, 16) + 'Z';

export function liveCycle(lb: LiveBookData = LIVE_BOOK): PipelineCycle {
  const p = lb.pipa;
  return {
    siklus: p.siklus,
    rumus: p.rumus,
    agents: p.agen.map((a) => ({ slug: a.slug, ok: a.status === 'ok', trial: a.kursi === 'uji' })),
    bot: p.bot,
    score: p.skor_bot,
    nilai: {},
    target: p.target ?? {},
    positions: Object.keys(p.target ?? {}).length || (p.terkunci ? (p.slot_n ?? 0) : 0),
    sealed: p.status === 'dikomit',
    tx: p.tx,
    note: `live public cycle ${hhmm(p.siklus)} (bot, scores and positions members-only)`,
  };
}

/** Bot and score of the newest revealed tape row ("dominant bot B2-RS (+19.6); ..."). */
export function revealedDecision(lb: LiveBookData = LIVE_BOOK): { siklus: number; bot: string | null; score: number | null; instruments: number; agentsIn: number; dasar: string } | null {
  const row = lb.pita_keputusan[0];
  if (!row) return null;
  const m = /(?:dominant bot|hold)\s+([A-Z0-9-]+)\s+\(([+-]?\d+(?:\.\d+)?)(?:\)| points)?/.exec(row.dasar ?? '');
  const dominant = /dominant bot/.test(row.dasar ?? '');
  return {
    siklus: row.siklus,
    bot: row.bot ?? m?.[1] ?? null,
    // only "dominant bot X (+s)" carries the formula score; "hold X (hysteresis: +p points)" is a margin, not a score
    score: dominant && m ? Number(m[2]) : null,
    instruments: row.instrumen.length,
    agentsIn: row.masuk,
    dasar: row.dasar ?? '',
  };
}

export function revealedCycle(lb: LiveBookData = LIVE_BOOK, desk: Desk = DESK): PipelineCycle {
  const live = liveCycle(lb);
  const r = revealedDecision(lb);
  if (!r) return live;
  const brake = /daily loss brake/.test(r.dasar);
  return {
    ...live,
    siklus: r.siklus,
    bot: r.bot,
    score: r.score,
    nilai: r.bot && r.score !== null ? { [r.bot]: r.score } : {},
    target: {},
    positions: 0, // the revealed row is flat (daily loss brake); weights are not in the public tape
    sealed: desk.komit_24j > 0 && desk.komit_24j === desk.siklus_24j,
    tx: null,
    note: `revealed decision ${hhmm(r.siklus)} (24 h public delay): ${r.bot ?? '-'} ${r.score !== null ? `(+${r.score})` : ''}${brake ? ', book flat by the daily loss brake' : ''}`,
  };
}

export const LIVE_CYCLE: PipelineCycle = liveCycle();
export const REVEALED_CYCLE: PipelineCycle = revealedCycle();
export const DEFAULT_CYCLE: PipelineCycle = {
  ...LIVE_CYCLE,
  bot: REVEALED_CYCLE.bot,
  score: REVEALED_CYCLE.score,
  nilai: REVEALED_CYCLE.nilai,
  note: `${LIVE_CYCLE.note}; robot/orbit show the newest revealed winner: ${REVEALED_CYCLE.note}`,
};
