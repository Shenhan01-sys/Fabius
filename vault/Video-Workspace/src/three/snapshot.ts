// Typed access to data/desk-snapshot.json (NOTE: the repo-root .gitignore rule `data/` ignores src/three/data/; force-add it or add a negation): one real snapshot of what the website's 3D scenes render, fetched with public read-only GETs
// (no keys) on 2026-10-07 15:56:44Z. Sources and the public-view caveats are in the JSON's `note`.

import raw from './data/desk-snapshot.json';
import type { Counts } from './crystal/Crystal';
import { hubBook, seats as toSeats, type Seat } from './desk/model';
import type { Look } from './desk/looks';
import type { Desk, LiveBookData, Lock, Siklus } from './desk/types';

type Raw = {
  fetched_utc: string;
  note: string;
  sources: Record<string, string>;
  desk: Desk;
  liveBook: LiveBookData;
  site: { generated_utc: string; repo_head: string; locks: Lock[]; chain: { id: number; block: number; block_utc: string; totals: Record<string, number> } | null; crystal_counts: Counts };
};

const S = raw as unknown as Raw;

export const SNAPSHOT_FETCHED_UTC = S.fetched_utc;
export const SNAPSHOT_NOTE = S.note;
export const SNAPSHOT_SOURCES = S.sources;
export const DESK: Desk = S.desk;
export const LIVE_BOOK: LiveBookData = S.liveBook;
/** On-chain locks in lock order (the hero's beat label for sealed block `order` k is LOCKS[k]). */
export const LOCKS: Lock[] = S.site.locks;
/** What the live hero shows: crystalCounts(snapshot, 26) = { verified 22, sealed 4, empty 0 } at fetch time. */
export const CRYSTAL_COUNTS: Counts = S.site.crystal_counts;
export const CHAIN = S.site.chain;

/**
 * The floor is shown one minute into the last recorded cycle: each agent's pose comes from its book's last record (trade / hold / fail).
 * (The site computes poses at the data's own time; at fetch time that was 404 s into the cycle, when every agent shows "thinking".)
 */
export const FLOOR_NOW = (DESK.siklus_terakhir?.siklus ?? DESK.t) + 60;
export const deskSeats = (now = FLOOR_NOW): Seat[] => toSeats(DESK, now);
export const deskHub = () => hubBook(DESK);
export const deskCycles = (): Siklus[] => (DESK.siklus_12 ?? []).slice(-12);
/** Same workers on the Live Book platform as on the floor (the site builds `looks` from the floor seats). */
export const deskLooks = (): Record<string, Look> => Object.fromEntries(deskSeats().map((s) => [s.slug, s.look]));
