// Fabius palette as used by the website's 3D scenes (web/src/components/desk/floor/parts.tsx `C` + the hero crystal's materials).

export const C = {
  clay: '#fbfaff',
  lav: '#ece8fa',
  lav2: '#ddd5f6',
  lav3: '#c9bdf2',
  ink: '#15122b',
  night: '#1a1442',
  violet: '#6e4bff',
  violet2: '#9d86ff',
  mist: '#8b86a6',
  gap: '#ff5a6e',
  indigo: '#2a1a94',
  white: '#ffffff',
} as const;

/**
 * The /desk panel behind both desk canvases on the site: `bg-gradient-to-b from-lav/70 to-white` on a white card, flattened to opaque colours
 * (lav at 70 % over white = #f2effc). Keep backdrops opaque: video frames are opaque, so any alpha in the page background renders darker.
 */
export const DESK_BACKDROP_CSS = 'linear-gradient(to bottom, #f2effc, #ffffff)';
/** The hero section behind the crystal (opaque canvas cleared to lav). */
export const HERO_BACKDROP_CSS = C.lav;
