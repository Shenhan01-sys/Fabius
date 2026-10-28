// The site's three families (web/src/app/layout.tsx), loaded from public/fonts (variable files, OFL):
// Archivo with its width axis (light + expanded for calm headings, heavy italic + condensed for the violet accent word),
// Inter for body and captions, JetBrains Mono for the small uppercase labels.
import type React from 'react';
import { staticFile } from 'remotion';
import { loadFont } from '@remotion/fonts';

let started = false;
export function loadFonts() {
  if (started) return;
  started = true;
  const vf = { weight: '100 900' } as const;
  void loadFont({ family: 'Archivo', url: staticFile('fonts/Archivo-VF.ttf'), ...vf, style: 'normal' });
  void loadFont({ family: 'Archivo', url: staticFile('fonts/Archivo-Italic-VF.ttf'), ...vf, style: 'italic' });
  void loadFont({ family: 'Inter', url: staticFile('fonts/Inter-VF.ttf'), ...vf, style: 'normal' });
  void loadFont({ family: 'JetBrains Mono', url: staticFile('fonts/JetBrainsMono-VF.ttf'), weight: '100 800', style: 'normal' });
}

type CSS = React.CSSProperties;
/** Archivo at a weight and width (%, 62-125). */
export const archivo = (size: number, weight = 400, width = 100, italic = false): CSS => ({
  fontFamily: 'Archivo, sans-serif',
  fontSize: size,
  fontWeight: weight,
  fontStyle: italic ? 'italic' : 'normal',
  fontVariationSettings: `'wght' ${weight}, 'wdth' ${width}`,
  fontStretch: `${width}%`,
  lineHeight: 0.95,
});
/** The site's two display voices. */
export const calm = (size: number): CSS => ({ ...archivo(size, 300, 112), letterSpacing: -0.02 * size });
export const accent = (size: number): CSS => ({ ...archivo(size, 800, 79, true), letterSpacing: -0.01 * size });
export const heavy = (size: number, width = 100): CSS => ({ ...archivo(size, 800, width), letterSpacing: -0.015 * size });
export const inter = (size: number, weight = 400): CSS => ({ fontFamily: 'Inter, sans-serif', fontSize: size, fontWeight: weight, lineHeight: 1.35 });
export const mono = (size: number, weight = 500): CSS => ({ fontFamily: '"JetBrains Mono", monospace', fontSize: size, fontWeight: weight, lineHeight: 1.3 });
/** uppercase micro label with wide tracking (site: "VERIFY - NO KEY, NO GAS") */
export const label = (size: number, weight = 500): CSS => ({ ...mono(size, weight), textTransform: 'uppercase', letterSpacing: 0.16 * size });
