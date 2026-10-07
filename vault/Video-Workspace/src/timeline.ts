// The edit: which plate plays when. Every cut sits in the pause before a line (the kit's rule), anchored to
// the aligned script by content, so a new voiceover re-times the whole video.
import type React from 'react';
import type { Tr } from './components/transition';
import { cut, LY } from './lib/lyrics';
import Hook from './plates/Hook';
import Problem from './plates/Problem';
import Idea from './plates/Idea';
import Lock from './plates/Lock';
import Commit from './plates/Commit';
import Desk from './plates/Desk';
import Split from './plates/Split';
import Open from './plates/Open';
import Bnb from './plates/Bnb';
import Honest from './plates/Honest';
import End from './plates/End';

export interface PlateProps { t: number; start: number; end: number; frame: number; fps: number }
export interface Src { at: number; text: string }
export interface Entry {
  id: string;
  title: string;
  start: number;
  end: number;
  /** the transition INTO this plate, centred on its start */
  tr?: Tr;
  /** light plate: HUD in ink */
  ink?: (t: number) => boolean;
  /** source labels for the claims on screen, bottom-right */
  src?: Src[];
  Comp: React.FC<PlateProps>;
}

const at = (q: string) => LY.get(q).start;

export function makeTimeline(): Entry[] {
  const b = {
    problem: cut('Most trading bots'),
    idea: cut('Fabius is a paper-trading'),
    lock: cut('It starts with the rules'),
    commit: cut('Every bar, a bot'),
    desk: cut('On top runs the AI desk'),
    split: cut('The AI picks the rulebook'),
    open: cut('And the desk is open'),
    bnb: cut('Signals sell over'),
    honest: cut('Because here'),
    end: cut('So Fabius does what'),
    stop: LY.duration,
  };
  return [
    { id: 'hook', title: 'Cunctator', start: 0, end: b.problem, Comp: Hook,
      src: [{ at: at('His name was'), text: 'README.md · the name' }] },
    { id: 'problem', title: 'The screenshot', start: b.problem, end: b.idea, Comp: Problem, tr: { type: 'zoom', d: 0.7, x: 960, y: 640 } },
    { id: 'idea', title: 'The idea', start: b.idea, end: b.lock, Comp: Idea, ink: () => true, tr: { type: 'iris', d: 0.8 },
      src: [{ at: at('Fabius is a paper'), text: 'contracts/SignalAnchor.sol · contracts/DeskAnchor.sol' }] },
    { id: 'lock', title: 'Rules first', start: b.lock, end: b.commit, Comp: Lock, ink: () => true, tr: { type: 'push', d: 0.7 },
      src: [{ at: at('Each of our six'), text: 'deployments/97.json · m3.locks' }, { at: at('A strategy that'), text: 'contracts/SignalAnchor.sol · LockedAfterBar · snapshot: SEBELUM KUNCI' }] },
    { id: 'commit', title: 'Commit, reveal', start: b.commit, end: b.desk, Comp: Commit, tr: { type: 'whip', d: 0.6 },
      src: [{ at: at('Every bar, a bot'), text: 'ledger/paper/B2-RS.jsonl · bar 2026-10-05 · lag 31,458 s' }, { at: at('Late commits'), text: 'deployments/97.json · maxLag_s 43200' }, { at: at('Anyone can rerun'), text: 'python -X utf8 -m engine.cli ledger verify' }] },
    { id: 'desk', title: 'The AI desk', start: b.desk, end: b.split, Comp: Desk, tr: { type: 'zoom', d: 0.8, x: 1660, y: 420 },
      src: [{ at: at('Every five minutes'), text: 'deployments/97.json · analis.agents' }, { at: at('A locked formula'), text: 'tools/meja_slot.py · PARAMS2 r4' }, { at: at('And its root must'), text: 'contracts/DeskAnchor.sol · CYCLE = 300' }] },
    { id: 'split', title: 'Who decides', start: b.split, end: b.open, Comp: Split, tr: { type: 'flash', d: 0.3 },
      src: [{ at: at('The AI picks'), text: 'vault · F-D112 (direction computed by code)' }] },
    { id: 'open', title: 'Open desk', start: b.open, end: b.bnb, Comp: Open, tr: { type: 'whip', d: 0.6 },
      src: [{ at: at('Bring your own'), text: 'engine/rule.py · tools/agen_luar.py' }, { at: at('Every bot runs'), text: 'engine/gates.py · G1–G11' }] },
    { id: 'bnb', title: 'On BNB Chain', start: b.bnb, end: b.honest, Comp: Bnb, tr: { type: 'zoom', d: 0.7 },
      src: [{ at: at('Signals sell over'), text: 'tools/x402_sinyal.py · FabiusCredit (FAB)' }, { at: at('All on testnet'), text: 'config/uang_nyata.json · "aktif": false' }] },
    { id: 'honest', title: 'What we don’t claim', start: b.honest, end: b.end, Comp: Honest, ink: () => true, tr: { type: 'iris', d: 0.8 },
      src: [{ at: at('To pass, a bot'), text: 'engine/fd16.py · F-D16' }, { at: at('Today, zero of six'), text: 'python -X utf8 -m engine.cli ledger fd16 · 06 Oct 2026' }] },
    { id: 'end', title: 'Fabius', start: b.end, end: b.stop, Comp: End, tr: { type: 'push', d: 0.7 }, ink: (t) => t >= LY.get('Fabius. Refuse').start - 0.25 },
  ];
}
