// Fonts for text drawn into CanvasTextures (labels, monitor screens, the robot's chest). Loaded once from public/fonts with the FontFace API;
// <Stage fonts> holds the frame (delayRender) until they are ready, so no texture is ever drawn with a fallback font.

import { useEffect, useState } from 'react';
import { staticFile, useDelayRender } from 'remotion';

export const MONO = 'Fabius3D Mono'; // JetBrains Mono (the site's font-mono)
export const SANS = 'Fabius3D Sans'; // Inter (the site's monitor text)

const FILES: { family: string; file: string }[] = [
  { family: MONO, file: 'fonts/JetBrainsMono-VF.ttf' },
  { family: SANS, file: 'fonts/Inter-VF.ttf' },
];

let ready = false;
let pending: Promise<void> | null = null;

export function loadThreeFonts(): Promise<void> {
  if (ready) return Promise.resolve();
  if (!pending) {
    pending = Promise.all(
      FILES.map(async ({ family, file }) => {
        const face = new FontFace(family, `url(${staticFile(file)})`, { weight: '100 900', style: 'normal' });
        await face.load();
        document.fonts.add(face);
      }),
    ).then(() => {
      ready = true;
    });
  }
  return pending;
}

export const threeFontsReady = () => ready;

/** true once the fonts are usable; until then the current frame is held with delayRender. */
export function useThreeFonts(enabled = true): boolean {
  const [ok, setOk] = useState(() => !enabled || ready);
  const { delayRender, continueRender, cancelRender } = useDelayRender();
  const [handle] = useState(() => (!enabled || ready ? null : delayRender('Loading fonts for 3D text textures')));
  useEffect(() => {
    if (ok) return;
    let live = true;
    loadThreeFonts().then(
      () => live && setOk(true),
      (e: unknown) => cancelRender(e instanceof Error ? e : new Error(String(e))),
    );
    return () => {
      live = false;
    };
  }, [ok, cancelRender]);
  useEffect(() => {
    // released one commit after `ok`: by then the canvas that needed the fonts has mounted and holds its own delayRender
    if (ok && handle !== null) continueRender(handle);
  }, [ok, handle, continueRender]);
  return ok;
}
