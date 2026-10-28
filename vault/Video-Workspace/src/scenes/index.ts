// Scene registry. Scenes not built yet render a placeholder so the whole edit always plays end to end.
import type { SceneMap } from '../timeline';
import { Placeholder } from './Placeholder';
import { S1Hook } from './S1Hook';
import { S9Honest } from './S9Honest';
import { S4Seal } from './S4Seal';
import { S10End } from './S10End';
import { S2Reveal } from './S2Reveal';
import { S6Use } from './S6Use';
import { S3Rules } from './S3Rules';
import { S5Desk } from './S5Desk';
import { S7Verify } from './S7Verify';
import { S8Open } from './S8Open';

const ph = (name: string, dark = false) => Placeholder(name, dark);

export const SCENES: SceneMap = {
  hook: S1Hook,
  reveal: S2Reveal,
  rules: S3Rules,
  seal: S4Seal,
  desk: S5Desk,
  use: S6Use,
  verify: S7Verify,
  open: S8Open,
  honest: S9Honest,
  end: S10End,
};
