// Test harness for the 3D ports, separate from the pitch video (src/index.ts). Run from vault/Video-Workspace:
//   npx remotion studio src/three/preview/index.ts
//   npx remotion still src/three/preview/index.ts CrystalTest out/three/crystal-f120.png --frame=120 --gl=angle
import { registerRoot } from 'remotion';
import { Root3D } from './Root3D';

registerRoot(Root3D);
