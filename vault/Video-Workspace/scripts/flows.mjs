// Capture flows for scripts/capture-flow.mjs (live site, read-only). Targets were picked from the live DOM (7 Oct 2026).
// Step vocabulary (seconds are virtual-time seconds = video seconds at 60 fps):
//   { wait: s }                                    hold
//   { move: target | [target, target, ...], dur, ease, arc }   eased real page.mouse moves, one per frame (several
//                                                  targets = one smooth Catmull-Rom path through them)
//   { hover: target, dur }                         same as move (named for intent)
//   { scroll: y | { to: target, block: 'start'|'center'|'end', offset } | { by: dy } | { js }, dur, ease }
//   { move: ..., scroll: ..., dur }                both at once
//   { click: target | true, hold, wait }           mouse down / up on captured frames (moves there first if needed)
//   { waitFor: predicate, timeout, after, markAs }  keep stepping + capturing until the predicate is true
//   { mark: 'name' }  { shot: 'name' }  { cursor: target }
// Any step may also carry `mark: 'name'` (frame index where the step starts).
// target: [x, y] (viewport CSS px) | 'css selector' | { selector, text, closest, up, index, within, at: [fx, fy], dx, dy }
// predicate: 'js expression' | { js } | { selector | text ... } (exists and visible)
// flow.watch: { markName: predicate | { js, after: 'mark' } }  -> first frame where it holds becomes a mark
export const DEFAULT_BASE = 'https://fabius-one.vercel.app';

// scroll position for progress p (0..1) through the pinned 360vh "From candle close to proof" section
const journey = (p) => ({
  js: `(() => { const s = document.querySelector('section#journey'); return s.getBoundingClientRect().top + scrollY + ${p} * (s.offsetHeight - innerHeight); })()`,
});
// a /verify station card has settled (motion spring done: opacity 1, no transform on the card and its cube icon)
const settledJs = (heading) => `(() => { const c = window.__vt.find({ text: ${JSON.stringify(heading)}, within: 'section#top', closest: '.glass' })[0]; if (!c) return false;
    const ok = (e) => { const s = getComputedStyle(e); return s.opacity === '1' && (s.transform === 'none' || s.transform === 'matrix(1, 0, 0, 1, 0, 0)'); };
    const icon = c.querySelector('div.flex.items-center.justify-between > div'); return ok(c) && (!icon || ok(icon)); })()`;
const STATIONS = ['Ledger tick', 'Committed on-chain', 'Opened', 'Recomputed'];
const stationDone = (heading) => ({ after: 'verify-release', js: settledJs(heading) });
const VERDICT = 'section#top div[class*="bg-night"][class*="rounded-[28px]"]';

export const FLOWS = [
  {
    name: 'home-hero',
    device: 'desktop',
    path: '/',
    start: 'frozen', // page loads with virtual time stopped: the cube's first WebGL frame is frame 0's next step
    ready: { selector: 'section#top canvas', timeout: 40 },
    cursorStart: [1290, 236],
    boxes: {
      headline: 'section#top h1',
      caret: 'section#top h1 span[class*="animate-blink"]',
      liveTag: { text: 'Live from chain', selector: 'section#top span' },
      chips: { selector: 'section#top .glass.rounded-2xl', all: true },
      chipRules: { text: 'rules locked on-chain', within: 'section#top', closest: '.glass' },
      chipVerified: { text: 'signals verified', within: 'section#top', closest: '.glass' },
      chipEmpty: { text: 'empty: the record started', within: 'section#top', closest: '.glass' },
      ctaProof: { text: 'See the proof feed', selector: 'section#top a' },
      ctaAgent: { text: 'Connect an agent', selector: 'section#top a' },
      verifyBadge: 'section#top button[aria-label="verify"]',
      canvas: 'section#top canvas',
      nav: 'header, nav',
    },
    steps: [
      { wait: 0.9 },
      { move: [[1150, 300], [930, 250], [760, 330], [880, 520], [1010, 610]], dur: 3.6, ease: 'inOutSine', mark: 'drift' },
      { move: { text: 'See the proof feed', selector: 'section#top a' }, dur: 1.2, ease: 'inOutCubic', mark: 'cta-approach' },
      { mark: 'cta-hover' },
      { wait: 1.3 },
      { shot: 'cta-hover' },
    ],
  },
  {
    name: 'home-journey',
    device: 'desktop',
    path: '/',
    start: 'free',
    ready: { selector: 'section#journey h2', timeout: 40 },
    scrollStart: journey(0),
    preroll: 0.8,
    boxes: {
      sticky: 'section#journey > div.sticky',
      heading: 'section#journey h2',
      tag: { text: '01 — One signal', within: 'section#journey' },
      stations: { selector: 'section#journey div[class*="w-[19%]"]', all: true },
      mover: 'section#journey div[class*="-translate-y-[86%]"]',
      progressLine: 'section#journey div[class*="origin-left"]',
      command: { text: 'verify_signals.py', within: 'section#journey', closest: '.glass-dark' },
    },
    steps: [
      { wait: 1.0, mark: 'station-1' },
      { scroll: journey(0.25), dur: 1.25, ease: 'inOutCubic' },
      { wait: 0.8, mark: 'station-2' },
      { scroll: journey(0.5), dur: 1.25, ease: 'inOutCubic' },
      { wait: 0.8, mark: 'station-3' },
      { shot: 'station-3' },
      { scroll: journey(0.75), dur: 1.25, ease: 'inOutCubic' },
      { wait: 0.8, mark: 'station-4' },
      { scroll: journey(1), dur: 1.25, ease: 'inOutCubic' },
      { wait: 1.2, mark: 'station-5' },
    ],
  },
  {
    name: 'home-mobile',
    device: 'mobile',
    path: '/',
    start: 'frozen',
    ready: { selector: 'section#top canvas', timeout: 40 },
    boxes: {
      headline: 'section#top h1',
      ctaProof: { text: 'See the proof feed', selector: 'section#top a' },
      canvas: 'section#top canvas',
      journey: 'section#journey',
      journeyHeading: 'section#journey h2',
      stations: { selector: 'section#journey div[class*="w-[19%]"]', all: true },
      proof: 'section#proof',
      proofHeading: 'section#proof h2',
    },
    steps: [
      { wait: 2.4 },
      { shot: 'hero' },
      { scroll: { to: 'section#journey', block: 'start' }, dur: 1.4, ease: 'inOutCubic', mark: 'to-journey' },
      { wait: 0.4 },
      { scroll: journey(0.5), dur: 1.3, ease: 'inOutSine' },
      { wait: 0.3 },
      { scroll: journey(1), dur: 1.3, ease: 'inOutSine' },
      { scroll: { to: 'section#proof', block: 'start' }, dur: 1.2, ease: 'inOutCubic', mark: 'to-proof' },
      { wait: 0.7 },
    ],
  },
  {
    name: 'bot-b1',
    device: 'desktop',
    path: '/bot/B1-TREND',
    start: 'frozen',
    ready: { selector: 'section#top h1', timeout: 40 },
    cursorStart: [1180, 330],
    boxes: {
      title: 'section#top h1',
      tag: { text: 'Bot — one locked machine', within: 'section#top' },
      slotBadge: { text: 'In the book', within: 'section#top', selector: 'div,span' },
      quoteCard: { text: 'The rule, as locked', within: 'section#top', closest: '.glass' },
      quote: { selector: 'section#top .glass p', index: 0 },
      lockPill: { text: 'spec locked on-chain', selector: 'a' },
      bookSection: 'section#book',
      bookTitle: 'section#book h2',
    },
    steps: [
      { wait: 1.3 },
      { move: { text: 'spec locked on-chain', selector: 'a', at: [0.32, 0.5] }, dur: 1.3, ease: 'inOutCubic', mark: 'pill-approach' },
      { wait: 1.2, mark: 'pill-hover' },
      { shot: 'pill-hover' },
      { scroll: { to: { text: 'The rule, as locked', within: 'section#top', closest: '.glass' }, block: 'center' }, move: [1252, 470], dur: 1.2, ease: 'inOutCubic', mark: 'to-quote' },
      { wait: 0.7 },
      { scroll: { to: 'section#book', block: 'start', offset: -70 }, dur: 1.5, ease: 'inOutCubic', mark: 'to-book' },
      { wait: 1.2 },
    ],
  },
  {
    name: 'desk',
    device: 'desktop',
    path: '/desk',
    start: 'free', // the Live Book scene only mounts after its data arrives; both 3D scenes loop, so load in real time then freeze
    ready: { selector: 'canvas', timeout: 40 },
    cursorStart: [1250, 430],
    boxes: {
      title: 'h1',
      liveBook: { text: 'Fabius Live Book', selector: 'p', closest: 'div.rounded-2xl' },
      liveBook3d: { selector: 'canvas', index: 0 },
      labelAgents: { text: 'Agents ·', selector: '.absolute.z-20' },
      labelFormula: { text: 'Formula', selector: '.absolute.z-20' },
      labelBotRule: { text: 'Bot rule', selector: '.absolute.z-20' },
      labelBook: { text: 'Book ·', selector: '.absolute.z-20' },
      labelChain: { text: 'BNB Chain · sealed', selector: '.absolute.z-20' },
      labels: { selector: '[class*="from-lav/70"] > .absolute.z-20', all: true },
      floor: { text: 'The trading floor', selector: 'p', closest: 'div.rounded-2xl' },
      floor3d: { selector: 'canvas', index: 1 },
    },
    steps: [
      { wait: 1.0 },
      { scroll: { to: { selector: 'canvas', index: 0 }, block: 'center', offset: -40 }, dur: 1.3, ease: 'inOutCubic' },
      { wait: 3.5, mark: 'livebook-centred' },
      { shot: 'livebook' },
      { wait: 3.5 },
      { scroll: { to: { text: 'The trading floor', selector: 'p', closest: 'div.rounded-2xl' }, block: 'center' }, dur: 2.2, ease: 'inOutCubic', mark: 'to-floor' },
      { wait: 2.6, mark: 'floor-centred' },
      { shot: 'floor' },
    ],
  },
  {
    name: 'analysts',
    device: 'desktop',
    path: '/analysts',
    start: 'frozen',
    ready: { selector: 'article', timeout: 40 },
    cursorStart: [1200, 320],
    boxes: {
      title: 'h1',
      tradesNow: { text: 'Bot Fabius trades now', selector: 'p', closest: 'div.rounded-2xl' },
      picksLabel: { text: 'Picks for the bar closing', selector: 'p' },
      picks: { selector: 'article', all: true },
    },
    steps: [
      { wait: 1.4 },
      { scroll: { to: { text: 'Bot Fabius trades now', selector: 'p', closest: 'div.rounded-2xl' }, block: 'start', offset: -100 }, dur: 1.4, ease: 'inOutCubic', mark: 'to-picks' },
      { wait: 0.4 },
      { move: { selector: 'article', index: 0, at: [0.62, 0.42] }, dur: 1.1, ease: 'inOutCubic', mark: 'pick-approach' },
      { wait: 1.6, mark: 'pick-hover' },
      { shot: 'picks' },
      { move: { selector: 'article', index: 1, at: [0.38, 0.42] }, dur: 1.0, ease: 'inOutCubic' },
      { wait: 1.1 },
    ],
  },
  {
    name: 'buy',
    device: 'desktop',
    path: '/buy',
    start: 'frozen',
    ready: { text: '0.01 FAB', timeout: 40 },
    cursorStart: [1180, 760],
    boxes: {
      title: 'h1',
      offerCard: { text: 'The offer', selector: 'p', closest: 'div.rounded-2xl' },
      price: { text: '0.01 FAB', selector: 'p' },
      walletCard: { text: 'Your wallet', selector: 'p', closest: 'div.rounded-2xl' },
      signIn: { text: 'Sign in (Google', selector: 'button' },
      payCard: { text: 'Pay and reveal', selector: 'p', closest: 'div.rounded-2xl' },
      pay: { text: 'and reveal', selector: 'button' },
      modal: '#privy-modal-content',
    },
    watch: { 'modal-visible': { after: 'signin-release', selector: '#privy-modal-content' } },
    steps: [
      { wait: 1.5 },
      { move: { text: '0.01 FAB', selector: 'p', at: [0.18, 0.5] }, dur: 1.3, ease: 'inOutCubic', mark: 'price-approach' },
      { wait: 0.9, mark: 'price-hold' },
      { move: { text: 'Sign in (Google', selector: 'button', at: [0.55, 0.5] }, dur: 1.2, ease: 'inOutCubic', mark: 'signin-approach' },
      { wait: 0.8, mark: 'signin-hover' },
      // opens Privy's in-page sign-in modal only (checked in a throwaway page: no navigation, no request); nothing inside it is touched
      { click: { text: 'Sign in (Google', selector: 'button', at: [0.55, 0.5] }, mark: 'signin-click', markUp: 'signin-release' },
      { waitFor: { selector: '#privy-modal-content' }, timeout: 3, markAs: 'modal-open' },
      { wait: 1.2 },
      { shot: 'modal' },
      { wait: 1.3 },
    ],
  },
  {
    name: 'verify',
    device: 'desktop',
    // start on B1-TREND so picking B2-RS is a visible choice; 2026-10-06 = latest closed bar, B2-RS committed + revealed 5 signals (SAH)
    path: '/verify?bot=B1-TREND&bar=2026-10-06',
    start: 'frozen',
    ready: { text: 'Ledger tick', timeout: 40 },
    cursorStart: [1180, 470],
    boxes: {
      title: 'section#top h1',
      form: 'section#top form',
      chips: { selector: 'section#top form div.flex.flex-wrap.gap-2 > button', all: true },
      chipB2: { text: 'B2-RS', selector: 'form button' },
      date: 'form input[type="date"]',
      latest: { text: 'latest', selector: 'form button' },
      verify: 'form button[type="submit"]',
      loading: { text: 'Checking', within: 'section#top', closest: '.glass' },
      stations: { selector: 'section#top div[class*="lg:grid-cols-4"] > div.glass', all: true },
      stationTick: { text: 'Ledger tick', within: 'section#top', closest: '.glass' },
      stationCommitted: { text: 'Committed on-chain', within: 'section#top', closest: '.glass' },
      stationOpened: { text: 'Opened', within: 'section#top', selector: 'div.font-display', closest: '.glass' },
      stationRecomputed: { text: 'Recomputed', within: 'section#top', closest: '.glass' },
      signalsTable: { selector: 'section#top table', closest: '.glass' },
      verdict: VERDICT,
      verdictWord: { selector: `${VERDICT} div.font-display` },
    },
    watch: {
      'result-in': { after: 'verify-release', js: `!!window.__vt.find({ text: 'Ledger tick', within: 'section#top', closest: '.glass' }).length` },
      'station-1-done': stationDone('Ledger tick'),
      'station-2-done': stationDone('Committed on-chain'),
      'station-3-done': stationDone('Opened'),
      'station-4-done': stationDone('Recomputed'),
      'verdict-done': { after: 'verify-release', js: `(() => { const v = document.querySelector('${VERDICT}'); if (!v) return false; const s = getComputedStyle(v); return s.opacity === '1' && (s.transform === 'none' || s.transform === 'matrix(1, 0, 0, 1, 0, 0)'); })()` },
    },
    steps: [
      { wait: 1.0 },
      { move: { text: 'B2-RS', selector: 'form button' }, dur: 1.0, ease: 'inOutCubic', mark: 'chip-approach' },
      { click: { text: 'B2-RS', selector: 'form button' }, wait: 0.4, mark: 'chip-click' },
      { move: 'form button[type="submit"]', dur: 0.9, ease: 'inOutCubic', mark: 'verify-approach' },
      { wait: 0.25 },
      { click: 'form button[type="submit"]', wait: 0.15, mark: 'verify-click', markUp: 'verify-release' },
      { scroll: { to: 'section#top form', block: 'start', offset: -40 }, move: [1300, 470], dur: 1.3, ease: 'inOutCubic', mark: 'to-stations' },
      // keep stepping until all four stations (card + cube icon) have settled, then hold
      { waitFor: { js: `[${STATIONS.map((h) => settledJs(h)).join(', ')}].every(Boolean)` }, timeout: 12, markAs: 'stations-final', after: 1.2 },
      { scroll: { to: VERDICT, block: 'end', offset: 50 }, dur: 1.3, ease: 'inOutCubic', mark: 'to-verdict' },
      { wait: 2.4, mark: 'verdict-hold' },
      { shot: 'result' },
    ],
  },
  {
    name: 'submit',
    device: 'desktop',
    path: '/submit',
    start: 'frozen',
    ready: { selector: 'button[role="radio"]', timeout: 40 },
    cursorStart: [1250, 420],
    boxes: {
      title: 'h1',
      pipeline: { text: 'Pipeline', selector: 'p', closest: 'div.rounded-2xl' },
      methodLegend: { text: 'Method', selector: 'legend' },
      methodCards: { selector: 'div[role="radiogroup"][class*="grid-cols-3"] > button', all: true },
      cardRule: { selector: 'div[role="radiogroup"][class*="grid-cols-3"] > button', index: 0 },
      cardCode: { selector: 'div[role="radiogroup"][class*="grid-cols-3"] > button', index: 1 },
      cardFeed: { selector: 'div[role="radiogroup"][class*="grid-cols-3"] > button', index: 2 },
    },
    steps: [
      { wait: 1.3 },
      { scroll: { to: { text: 'Pipeline', selector: 'p', closest: 'div.rounded-2xl' }, block: 'start', offset: -90 }, dur: 1.4, ease: 'inOutCubic', mark: 'to-method' },
      { wait: 0.3 },
      { move: { selector: 'div[role="radiogroup"][class*="grid-cols-3"] > button', index: 0, at: [0.55, 0.55] }, dur: 1.0, ease: 'inOutCubic', mark: 'hover-rule' },
      { wait: 0.8 },
      { shot: 'method' },
      { move: { selector: 'div[role="radiogroup"][class*="grid-cols-3"] > button', index: 1, at: [0.5, 0.55] }, dur: 0.7, ease: 'inOutCubic', mark: 'hover-code' },
      { wait: 0.8 },
      { move: { selector: 'div[role="radiogroup"][class*="grid-cols-3"] > button', index: 2, at: [0.45, 0.55] }, dur: 0.7, ease: 'inOutCubic', mark: 'hover-feed' },
      { wait: 1.0 },
    ],
  },
  {
    name: 'submit-agent',
    device: 'desktop',
    path: '/submit-agent',
    start: 'frozen',
    ready: { selector: 'ol li', timeout: 40 },
    cursorStart: [1250, 420],
    boxes: {
      title: 'h1',
      agents: { text: 'Fabius external test', selector: 'p', closest: 'div.rounded-2xl' },
      stepsCard: { selector: 'ol', closest: 'div.rounded-2xl' },
      steps: { selector: 'ol > li', all: true },
    },
    steps: [
      { wait: 1.3 },
      { scroll: { to: 'ol', block: 'center', offset: -30 }, dur: 1.3, ease: 'inOutCubic', mark: 'to-steps' },
      { move: [{ selector: 'ol > li', index: 0, at: [0.3, 0.5] }, { selector: 'ol > li', index: 1, at: [0.3, 0.5] }, { selector: 'ol > li', index: 3, at: [0.3, 0.5] }], dur: 2.4, ease: 'inOutSine', mark: 'steps-tour' },
      { wait: 1.0 },
      { shot: 'steps' },
    ],
  },
  {
    name: 'status',
    device: 'desktop',
    path: '/status',
    start: 'frozen',
    ready: { selector: 'section#top svg[role="img"]', timeout: 40 },
    cursorStart: [860, 700],
    boxes: {
      title: 'section#top h1',
      clock: { selector: 'section#top svg[role="img"]', closest: 'div.glass' },
      clockSvg: 'section#top svg[role="img"]',
      statePill: 'section#top div.inline-flex.rounded-full',
      stations: 'section#stations',
      stationsTitle: 'section#stations h2',
      botRows: { selector: 'section#stations div.mt-12.space-y-8 > *', all: true },
    },
    steps: [
      { wait: 1.0 },
      { move: { selector: 'section#top svg[role="img"]', at: [0.2, 0.75] }, dur: 1.3, ease: 'inOutCubic', mark: 'to-clock' },
      { wait: 0.6 },
      { shot: 'clock' },
      { scroll: { to: 'section#stations', block: 'start', offset: -24 }, dur: 1.6, ease: 'inOutCubic', mark: 'to-stations' },
      { wait: 1.6 },
      { shot: 'stations' },
    ],
  },
];

// Full-page stills (desktop, DPR 2): public/web/stills/<name>-full.jpg + .json with document-coordinate boxes
const COMMON = { sections: { selector: 'section', all: true }, h1: 'h1', h2: { selector: 'h2', all: true }, canvases: { selector: 'canvas', all: true }, nav: 'header, nav', footer: 'footer' };
export const STILLS = [
  { name: 'home', path: '/', boxes: { ...COMMON, hero: 'section#top', journey: 'section#journey', stations: { selector: 'section#journey div[class*="w-[19%]"]', all: true }, proof: 'section#proof', book: 'section#book', access: 'section#access', chips: { selector: 'section#top .glass.rounded-2xl', all: true }, ctaProof: { text: 'See the proof feed', selector: 'section#top a' } } },
  { name: 'desk', path: '/desk', boxes: { ...COMMON, liveBook: { text: 'Fabius Live Book', selector: 'p', closest: 'div.rounded-2xl' }, floor: { text: 'The trading floor', selector: 'p', closest: 'div.rounded-2xl' }, labels: { selector: '[class*="from-lav/70"] > .absolute.z-20', all: true } } },
  { name: 'analysts', path: '/analysts', boxes: { ...COMMON, tradesNow: { text: 'Bot Fabius trades now', selector: 'p', closest: 'div.rounded-2xl' }, picks: { selector: 'article', all: true } } },
  { name: 'bot-b1', path: '/bot/B1-TREND', boxes: { ...COMMON, quoteCard: { text: 'The rule, as locked', within: 'section#top', closest: '.glass' }, lockPill: { text: 'spec locked on-chain', selector: 'a' } } },
  { name: 'buy', path: '/buy', boxes: { ...COMMON, offerCard: { text: 'The offer', selector: 'p', closest: 'div.rounded-2xl' }, price: { text: '0.01 FAB', selector: 'p' }, signIn: { text: 'Sign in (Google', selector: 'button' }, pay: { text: 'and reveal', selector: 'button' } } },
  {
    name: 'verify', path: '/verify?bot=B2-RS&bar=2026-10-06', waitFor: { selector: VERDICT }, settle: 3000,
    boxes: { ...COMMON, form: 'section#top form', chips: { selector: 'section#top form div.flex.flex-wrap.gap-2 > button', all: true }, date: 'form input[type="date"]', verify: 'form button[type="submit"]', stations: { selector: 'section#top div[class*="lg:grid-cols-4"] > div.glass', all: true }, signalsTable: { selector: 'section#top table', closest: '.glass' }, verdict: VERDICT },
  },
  { name: 'submit', path: '/submit', boxes: { ...COMMON, pipeline: { text: 'Pipeline', selector: 'p', closest: 'div.rounded-2xl' }, methodCards: { selector: 'div[role="radiogroup"][class*="grid-cols-3"] > button', all: true } } },
  { name: 'submit-agent', path: '/submit-agent', boxes: { ...COMMON, steps: { selector: 'ol > li', all: true }, agents: { text: 'Fabius external test', selector: 'p', closest: 'div.rounded-2xl' } } },
  { name: 'status', path: '/status', boxes: { ...COMMON, clock: { selector: 'section#top svg[role="img"]', closest: 'div.glass' }, stations: 'section#stations', botRows: { selector: 'section#stations div.mt-12.space-y-8 > *', all: true } } },
];
