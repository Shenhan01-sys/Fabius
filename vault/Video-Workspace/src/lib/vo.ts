// Word timings of the voiceover (public/data/vo.json, written by analysis/vo_v2.py from the TTS word boundaries).
// Scenes find their moments by content - a line id plus a word - so a new read re-times the whole video.
import data from '../../public/data/vo.json';

export interface Word { w: string; start: number; end: number }
export interface Line { id: string; scene: string; text: string; start: number; end: number; words: Word[] }
export interface Vo { voice: string; duration: number; lines: Line[] }

export const VO = data as unknown as Vo;
export const DURATION = VO.duration;

const byId = new Map(VO.lines.map((l) => [l.id, l]));
const norm = (s: string) => s.toLowerCase().replace(/[^a-z0-9']/g, '');

export function line(id: string): Line {
  const l = byId.get(id);
  if (!l) throw new Error(`no voiceover line ${id}`);
  return l;
}
/** the n-th (0-based) occurrence of word `w` in line `id`; a negative index counts from the end of the line */
export function word(id: string, w: string | number, n = 0): Word {
  const l = line(id);
  if (typeof w === 'number') {
    const x = l.words[w < 0 ? l.words.length + w : w];
    if (!x) throw new Error(`no word #${w} in ${id}`);
    return x;
  }
  const hits = l.words.filter((x) => norm(x.w) === norm(w));
  const x = hits[n];
  if (!x) throw new Error(`no word "${w}" (#${n}) in ${id}: ${l.text}`);
  return x;
}
/** start time of word `w` in line `id` */
export const at = (id: string, w: string | number, n = 0) => word(id, w, n).start;
/** first line of a scene */
export const sceneLines = (scene: string) => VO.lines.filter((l) => l.scene === scene);
/** the cut into a scene sits in the pause before its first line */
export function cut(scene: string, lead = 0.28): number {
  const ls = sceneLines(scene);
  if (!ls.length) throw new Error(`no scene ${scene}`);
  const i = VO.lines.indexOf(ls[0]!);
  const prevEnd = i > 0 ? VO.lines[i - 1]!.end : 0;
  return Math.max(prevEnd + 0.05, ls[0]!.start - lead);
}
/** all words with their line, in order (for captions) */
export const allWords = () => VO.lines.flatMap((l) => l.words.map((w) => ({ ...w, line: l.id })));
