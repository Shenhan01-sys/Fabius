// Deterministic 60 fps capture of the LIVE Fabius site (read-only) for the pitch video's browser frames.
//
// How it works: a virtual clock is installed before any page script runs (performance.now, Date.now / new Date(),
// requestAnimationFrame, setTimeout / setInterval, Web Animations + CSS animations / transitions, document.timeline).
//   FREE    virtual time follows real time: hydration, fetches and fonts load normally.
//   STEPPED virtual time is frozen; every captured frame advances it by exactly 1000/60 ms, fires the due timers in
//           order, runs one rAF batch with the new timestamp and moves every CSS / WAAPI animation by the same amount.
// Each frame is then grabbed over CDP (Page.captureScreenshot, JPEG) and piped into ffmpeg, so capture speed never
// shows in the clip. Network stays real: a slow request simply spans more captured frames.
// Flows (scripts/flows.mjs) script the cursor (real page.mouse moves, eased per frame), clicks, eased scrolls, marks,
// stills and waits. Per clip a JSON holds fps, size, per-frame scrollY + cursor, marks and element boxes.
//
// Usage (from vault/Video-Workspace):
//   node scripts/capture-flow.mjs                           every clip + every full-page still
//   node scripts/capture-flow.mjs --clips-only --only home-hero,verify   only these clips
//   node scripts/capture-flow.mjs --stills-only --only home              only these full-page stills
//   (--only matches clip AND still names - desk, buy, verify ... are both - so pair it with --clips-only / --stills-only;
//    clips are overwritten in place, never re-capture while a render is reading public/web/clips)
//   options: --base https://fabius-one.vercel.app  --out public/web  --check out/capture-check
//            --gpu auto|d3d11|swiftshader  --quality 92  --headed
// Read-only by construction: flows never log in, submit a form that changes state, sign or pay; non-GET requests to
// the Fabius app / gate are aborted, popups are closed and dialogs dismissed.
import { chromium } from 'playwright-core';
import { spawn, execFileSync } from 'node:child_process';
import { mkdirSync, writeFileSync, rmSync, statSync, existsSync } from 'node:fs';
import { once } from 'node:events';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { FLOWS, STILLS, DEFAULT_BASE } from './flows.mjs';

const ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
const argv = process.argv.slice(2);
const flag = (k) => argv.includes(`--${k}`);
const opt = (k, d) => {
  const i = argv.indexOf(`--${k}`);
  return i >= 0 && argv[i + 1] !== undefined && !argv[i + 1].startsWith('--') ? argv[i + 1] : d;
};
const BASE = opt('base', DEFAULT_BASE).replace(/\/$/, '');
const OUT = path.resolve(ROOT, opt('out', 'public/web'));
const CHECK = path.resolve(ROOT, opt('check', 'out/capture-check'));
const ONLY = opt('only', '').split(',').map((s) => s.trim()).filter(Boolean);
const QUALITY = Number(opt('quality', '92'));
const STILL_QUALITY = 88;
const CHROME = process.env.CHROME_PATH || 'C:/Program Files/Google/Chrome/Application/chrome.exe';
const FPS = 60;
const DT = 1000 / FPS;
const sleep = (ms) => new Promise((r) => setTimeout(r, ms));
const r1 = (v) => Math.round(v * 10) / 10;
const log = (...a) => console.log(new Date().toISOString().slice(11, 19), ...a);

const UA_IPHONE =
  'Mozilla/5.0 (iPhone; CPU iPhone OS 18_5 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/18.5 Mobile/15E148 Safari/604.1';
const DEVICES = {
  desktop: { viewport: { width: 1440, height: 900 }, deviceScaleFactor: 2, isMobile: false, hasTouch: false },
  mobile: { viewport: { width: 390, height: 844 }, deviceScaleFactor: 3, isMobile: true, hasTouch: true, userAgent: UA_IPHONE },
};
const GPU_ARGS = {
  d3d11: ['--use-angle=d3d11', '--enable-gpu', '--ignore-gpu-blocklist'],
  swiftshader: ['--use-angle=swiftshader', '--enable-unsafe-swiftshader', '--ignore-gpu-blocklist'],
};
const COMMON_ARGS = ['--hide-scrollbars', '--force-color-profile=srgb', '--disable-features=CalculateNativeWinOcclusion'];

// ---------------------------------------------------------------------------------------------------------------
// In-page virtual clock + helpers. Serialized by Playwright into an init script; runs before any page script.
// ---------------------------------------------------------------------------------------------------------------
function installVirtualTime(cfg) {
  if (window.top !== window || window.__vt) return;
  const W = window;
  const realNow = performance.now.bind(performance);
  const RealDate = Date;
  const realDateNow = Date.now.bind(Date);
  const realST = W.setTimeout.bind(W);
  const realCT = W.clearTimeout.bind(W);
  const realRAF = W.requestAnimationFrame.bind(W);
  const realCAF = W.cancelAnimationFrame.bind(W);
  const epochAtZero = realDateNow() - realNow();
  const report = (e) => { try { (W.reportError || console.error)(e); } catch { /* ignore */ } };

  let stepped = !!cfg.startFrozen;
  let offset = 0; // FREE: virtual = real - offset (offset only grows after an unfreeze)
  let vt = realNow(); // STEPPED: the frozen virtual time
  const now = () => (stepped ? vt : realNow() - offset);

  // ---- timers -------------------------------------------------------------------------------------------------
  let cseq = 0; // creation order
  let oseq = 0; // ordering among equal due times
  let nextId = 1;
  const timers = new Map();
  let armed = null;
  let armedFor = Infinity;
  const earliest = () => { let m = Infinity; for (const t of timers.values()) if (t.due < m) m = t.due; return m; };
  function arm() {
    if (armed !== null) { realCT(armed); armed = null; armedFor = Infinity; }
    const m = earliest();
    if (m === Infinity) return;
    if (!stepped) { armed = realST(pump, Math.max(0, m - now())); armedFor = m; }
    else if (m <= vt) { armed = realST(pump, 0); armedFor = m; }
  }
  function pump() { armed = null; armedFor = Infinity; fire(now(), cseq, false); arm(); }
  function nextDue(limit, maxC) {
    let best = null;
    for (const t of timers.values()) {
      if (t.due > limit || t.c > maxC) continue;
      if (!best || t.due < best.due || (t.due === best.due && t.o < best.o)) best = t;
    }
    return best;
  }
  function fire(limit, maxC, moveClock) {
    for (let guard = 0; guard < 20000; guard++) {
      const t = nextDue(limit, maxC);
      if (!t) return;
      if (moveClock && t.due > vt) vt = t.due;
      if (t.interval != null) { t.due = stepped ? t.due + t.interval : Math.max(t.due + t.interval, now()); t.o = ++oseq; }
      else timers.delete(t.id);
      try { if (typeof t.fn === 'function') t.fn.apply(W, t.args); else (0, eval)(String(t.fn)); } catch (e) { report(e); }
    }
  }
  function addTimer(fn, delay, args, repeat) {
    const id = nextId++;
    let d = Number(delay) || 0;
    d = repeat ? Math.max(4, d) : Math.max(0, d);
    const t = { id, fn, args, due: now() + d, interval: repeat ? d : null, c: ++cseq, o: ++oseq };
    timers.set(id, t);
    if (t.due < armedFor) arm();
    return id;
  }
  W.setTimeout = function setTimeout(fn, delay, ...args) { return addTimer(fn, delay, args, false); };
  W.setInterval = function setInterval(fn, delay, ...args) { return addTimer(fn, delay, args, true); };
  W.clearTimeout = function clearTimeout(id) { timers.delete(id); };
  W.clearInterval = function clearInterval(id) { timers.delete(id); };

  // ---- requestAnimationFrame ----------------------------------------------------------------------------------
  let rafSeq = 0;
  let rafQ = new Map();
  let curBatch = null;
  let realLoop = null; // the single real rAF registration that drives FREE mode
  function runRaf(ts) {
    const batch = rafQ;
    rafQ = new Map();
    curBatch = batch;
    for (const [, cb] of batch) { try { cb(ts); } catch (e) { report(e); } }
    curBatch = null;
  }
  function loop(ts) {
    realLoop = null;
    if (stepped) return;
    runRaf(ts - offset);
    // callbacks queued during the batch belong to the next frame: exactly one real registration
    if (rafQ.size && realLoop === null && !stepped) realLoop = realRAF(loop);
  }
  W.requestAnimationFrame = function requestAnimationFrame(cb) {
    const id = ++rafSeq;
    rafQ.set(id, cb);
    if (!stepped && realLoop === null && curBatch === null) realLoop = realRAF(loop);
    return id;
  };
  W.cancelAnimationFrame = function cancelAnimationFrame(id) { rafQ.delete(id); if (curBatch) curBatch.delete(id); };

  // ---- performance.now / Date ---------------------------------------------------------------------------------
  try { Object.defineProperty(performance, 'now', { value: function now_() { return now(); }, configurable: true, writable: true }); } catch { /* ignore */ }
  const vDateNow = () => Math.floor(epochAtZero + now());
  function VDate(...a) {
    if (!new.target) return new RealDate(vDateNow()).toString();
    return Reflect.construct(RealDate, a.length ? a : [vDateNow()], new.target);
  }
  VDate.prototype = RealDate.prototype;
  VDate.now = vDateNow;
  VDate.parse = RealDate.parse;
  VDate.UTC = RealDate.UTC;
  Object.defineProperty(VDate, 'name', { value: 'Date' });
  Object.defineProperty(VDate, 'length', { value: 7 });
  try { Object.defineProperty(RealDate.prototype, 'constructor', { value: VDate, writable: true, configurable: true }); } catch { /* ignore */ }
  W.Date = VDate;

  // ---- Web Animations / CSS animations & transitions ----------------------------------------------------------
  const AP = Animation.prototype;
  const origPause = AP.pause;
  const origPlay = AP.play;
  const origFinish = AP.finish;
  const ctD = Object.getOwnPropertyDescriptor(AP, 'currentTime');
  const stD = Object.getOwnPropertyDescriptor(AP, 'startTime');
  const ctGet = (a) => ctD.get.call(a);
  const ctSet = (a, v) => ctD.set.call(a, v);
  const seen = new WeakSet();
  const ours = new WeakSet();
  const t0 = new WeakMap();
  const isDoc = (a) => { const tl = a.timeline; return !!tl && (tl === document.timeline || (typeof DocumentTimeline !== 'undefined' && tl instanceof DocumentTimeline)); };
  function adopt(a, ct) {
    try { origPause.call(a); if (ct != null && Number.isFinite(ct)) ctSet(a, ct); } catch { /* ignore */ }
    ours.add(a); seen.add(a); t0.set(a, vt);
  }
  function advance(a, dt) {
    const rate = a.playbackRate;
    if (!rate) return;
    const cur = ctGet(a) ?? 0;
    const next = cur + dt * rate;
    let end = Infinity;
    try { end = a.effect ? a.effect.getComputedTiming().endTime : 0; } catch { /* ignore */ }
    if ((rate > 0 && next >= end) || (rate < 0 && next <= 0)) {
      ours.delete(a);
      try { origFinish.call(a); } catch { try { ctSet(a, rate > 0 ? end : 0); } catch { /* ignore */ } }
      return;
    }
    try { ctSet(a, next); } catch { /* ignore */ }
  }
  function sweep(freezing) {
    if (!stepped) return 0;
    let list;
    try { list = document.getAnimations(); } catch { return 0; }
    for (const a of list) {
      if (!isDoc(a)) continue;
      const ps = a.playState;
      if (ps === 'running') {
        // running on the real clock: created / restarted since the last sweep (or before the freeze)
        const ct = !seen.has(a) && !freezing ? 0 : ctGet(a);
        adopt(a, ct);
      } else if (ps === 'paused') {
        seen.add(a);
        if (!ours.has(a)) continue; // paused by the page itself (or animation-play-state: paused)
        const dt = vt - (t0.get(a) ?? vt);
        t0.set(a, vt);
        if (dt > 0) advance(a, dt);
      } else seen.add(a);
    }
    return list.length;
  }
  AP.pause = function pause() { ours.delete(this); return origPause.call(this); };
  AP.play = function play() {
    const r = origPlay.call(this);
    if (stepped && isDoc(this)) adopt(this, ctGet(this) ?? 0);
    return r;
  };
  Object.defineProperty(AP, 'currentTime', {
    configurable: true,
    get() { return ctGet(this); },
    set(v) { ctSet(this, v); if (ours.has(this)) t0.set(this, vt); },
  });
  Object.defineProperty(AP, 'startTime', {
    configurable: true,
    get() {
      if (stepped && ours.has(this)) { const c = ctGet(this); return c == null ? null : vt - c / (this.playbackRate || 1); }
      const s = stD.get.call(this);
      return s == null ? s : s - offset;
    },
    set(v) {
      if (v == null || !isDoc(this)) return stD.set.call(this, v);
      if (stepped) { seen.add(this); adopt(this, (vt - v) * (this.playbackRate || 1)); return; }
      stD.set.call(this, v + offset);
    },
  });
  const origAnimate = Element.prototype.animate;
  Element.prototype.animate = function animate(k, o) {
    const a = origAnimate.call(this, k, o);
    seen.add(a);
    if (stepped && isDoc(a)) adopt(a, 0);
    return a;
  };
  try {
    const tlD = Object.getOwnPropertyDescriptor(AnimationTimeline.prototype, 'currentTime');
    Object.defineProperty(AnimationTimeline.prototype, 'currentTime', {
      configurable: true,
      get() { return typeof DocumentTimeline !== 'undefined' && this instanceof DocumentTimeline ? now() : tlD.get.call(this); },
    });
  } catch { /* ignore */ }

  // ---- mode switches + stepping -------------------------------------------------------------------------------
  function freeze() {
    if (stepped) return vt;
    vt = now();
    stepped = true;
    if (realLoop !== null) { realCAF(realLoop); realLoop = null; }
    arm();
    sweep(true);
    return vt;
  }
  function unfreeze() {
    if (!stepped) return;
    try { for (const a of document.getAnimations()) if (ours.has(a)) { ours.delete(a); origPlay.call(a); } } catch { /* ignore */ }
    offset = realNow() - vt;
    stepped = false;
    arm();
    if (rafQ.size && realLoop === null) realLoop = realRAF(loop);
  }
  function step(dt) {
    if (!stepped) freeze();
    sweep(false); // adopt what was created since the last frame, at the old time
    const target = vt + dt;
    fire(target, cseq, true); // timers that existed before this step, in due order, clock moved to each due time
    vt = target;
    runRaf(vt);
    sweep(false);
    arm();
    return vt;
  }

  // ---- element lookup + measurement ---------------------------------------------------------------------------
  const norm = (s) => (s || '').replace(/\s+/g, ' ').trim();
  const visible = (el) => { if (!el.isConnected) return false; const r = el.getBoundingClientRect(); return r.width > 0 && r.height > 0; };
  function find(spec) {
    if (spec == null) return [];
    if (typeof spec === 'string') spec = { selector: spec };
    const root = spec.within ? document.querySelector(spec.within) : document;
    if (!root) return [];
    let els;
    if (spec.text != null) {
      const want = norm(spec.text).toLowerCase();
      const cands = [...root.querySelectorAll(spec.selector || 'body *')].filter((e) => norm(e.textContent).toLowerCase().includes(want));
      const set = new Set(cands);
      els = cands.filter((e) => ![...e.querySelectorAll('*')].some((c) => set.has(c)));
    } else els = [...root.querySelectorAll(spec.selector)];
    if (spec.closest) els = els.map((e) => e.closest(spec.closest)).filter(Boolean);
    if (spec.up) els = els.map((e) => { let x = e; for (let i = 0; i < spec.up && x.parentElement; i++) x = x.parentElement; return x; });
    els = [...new Set(els)];
    if (spec.visible !== false) els = els.filter(visible);
    if (spec.index != null) els = els.slice(spec.index, spec.index + 1);
    return els;
  }
  const rectOf = (el) => { const r = el.getBoundingClientRect(); return [Math.round(r.left * 10) / 10, Math.round(r.top * 10) / 10, Math.round(r.width * 10) / 10, Math.round(r.height * 10) / 10]; };
  const cache = new Map();
  function measure(boxes) {
    const out = {};
    if (!boxes) return out;
    for (const [name, spec] of Object.entries(boxes)) {
      const all = typeof spec === 'object' && spec.all;
      let els = cache.get(name);
      if (!els || !els.length || els.some((e) => !e.isConnected)) { els = find(spec); cache.set(name, els); }
      const vis = els.filter(visible);
      out[name] = all ? vis.map(rectOf) : vis.length ? rectOf(vis[0]) : null;
    }
    return out;
  }
  function test(pred) {
    if (!pred) return false;
    try {
      if (typeof pred === 'string') return !!(0, eval)(pred);
      if (pred.js) return !!(0, eval)(pred.js);
      return find(pred).length > 0;
    } catch { return false; }
  }

  W.__vt = { cfg, now, step, freeze, unfreeze, find, measure, test, get stepped() { return stepped; }, timers: () => timers.size, rafs: () => rafQ.size };
  W.__vtStep = step;
  W.__vtFreeze = freeze;
  W.__vtUnfreeze = unfreeze;
  W.__vtRect = (spec) => { const e = find(spec)[0]; return e ? rectOf(e) : null; };
  W.__vtFrame = (o) => {
    if (o.scrollY != null && Math.abs(W.scrollY - o.scrollY) > 0.01) {
      W.scrollTo({ top: o.scrollY, left: 0, behavior: 'instant' });
      try { document.dispatchEvent(new Event('scroll', { bubbles: true })); } catch { /* ignore */ }
    }
    if (o.dt) step(o.dt);
    const watch = {};
    for (const [k, p] of Object.entries(o.watch || {})) watch[k] = test(p);
    return { t: vt, scrollX: W.scrollX, scrollY: W.scrollY, boxes: measure(o.boxes), watch, until: o.until ? test(o.until) : false };
  };
}

// ---------------------------------------------------------------------------------------------------------------
// Easing + paths
// ---------------------------------------------------------------------------------------------------------------
const EASE = {
  linear: (t) => t,
  inOutSine: (t) => -(Math.cos(Math.PI * t) - 1) / 2,
  inOutQuad: (t) => (t < 0.5 ? 2 * t * t : 1 - (-2 * t + 2) ** 2 / 2),
  inOutCubic: (t) => (t < 0.5 ? 4 * t ** 3 : 1 - (-2 * t + 2) ** 3 / 2),
  inOutQuart: (t) => (t < 0.5 ? 8 * t ** 4 : 1 - (-2 * t + 2) ** 4 / 2),
  inOutQuint: (t) => (t < 0.5 ? 16 * t ** 5 : 1 - (-2 * t + 2) ** 5 / 2),
  outCubic: (t) => 1 - (1 - t) ** 3,
  outQuart: (t) => 1 - (1 - t) ** 4,
  outQuint: (t) => 1 - (1 - t) ** 5,
  inOutExpo: (t) => (t === 0 ? 0 : t === 1 ? 1 : t < 0.5 ? 2 ** (20 * t - 10) / 2 : (2 - 2 ** (-20 * t + 10)) / 2),
};
const ease = (name) => EASE[name ?? 'inOutCubic'] ?? EASE.inOutCubic;

// Smooth cursor path through points (Catmull-Rom), sampled by arc length so eased time maps to even travel.
function makePath(points, arc = 0) {
  let pts = points;
  if (pts.length === 2 && arc) {
    const [a, b] = pts;
    const dx = b[0] - a[0], dy = b[1] - a[1];
    const m = [(a[0] + b[0]) / 2 - dy * arc, (a[1] + b[1]) / 2 + dx * arc];
    pts = [a, m, b];
  }
  const P = [pts[0], ...pts, pts[pts.length - 1]];
  const samples = [];
  for (let i = 1; i < P.length - 2; i++) {
    const [p0, p1, p2, p3] = [P[i - 1], P[i], P[i + 1], P[i + 2]];
    for (let s = 0; s < 64; s++) {
      const t = s / 64, t2 = t * t, t3 = t2 * t;
      const f = (k) => 0.5 * (2 * p1[k] + (-p0[k] + p2[k]) * t + (2 * p0[k] - 5 * p1[k] + 4 * p2[k] - p3[k]) * t2 + (-p0[k] + 3 * p1[k] - 3 * p2[k] + p3[k]) * t3);
      samples.push([f(0), f(1)]);
    }
  }
  samples.push(pts[pts.length - 1]);
  const acc = [0];
  for (let i = 1; i < samples.length; i++) acc.push(acc[i - 1] + Math.hypot(samples[i][0] - samples[i - 1][0], samples[i][1] - samples[i - 1][1]));
  const total = acc[acc.length - 1] || 1;
  return (u) => {
    const L = Math.min(1, Math.max(0, u)) * total;
    let i = 1;
    while (i < acc.length - 1 && acc[i] < L) i++;
    const seg = acc[i] - acc[i - 1] || 1;
    const k = (L - acc[i - 1]) / seg;
    return [samples[i - 1][0] + (samples[i][0] - samples[i - 1][0]) * k, samples[i - 1][1] + (samples[i][1] - samples[i - 1][1]) * k];
  };
}

// ---------------------------------------------------------------------------------------------------------------
// Browser
// ---------------------------------------------------------------------------------------------------------------
async function launch() {
  const want = opt('gpu', 'auto');
  for (const kind of want === 'auto' ? ['d3d11', 'swiftshader'] : [want]) {
    const browser = await chromium.launch({ executablePath: CHROME, headless: !flag('headed'), args: [...COMMON_ARGS, ...GPU_ARGS[kind]] });
    const page = await browser.newPage();
    const gl = await page.evaluate(() => {
      const c = document.createElement('canvas');
      const g = c.getContext('webgl2') || c.getContext('webgl');
      if (!g) return null;
      const e = g.getExtension('WEBGL_debug_renderer_info');
      return String(e ? g.getParameter(e.UNMASKED_RENDERER_WEBGL) : g.getParameter(g.RENDERER));
    });
    await page.close();
    const ok = gl && (kind !== 'd3d11' || !/swiftshader/i.test(gl));
    if (ok) { log(`[gpu] ${kind}: ${gl}`); return { browser, gpu: kind, gl }; }
    log(`[gpu] ${kind} unavailable (${gl}); trying the next option`);
    await browser.close();
  }
  throw new Error('No WebGL in headless Chrome');
}

async function newContext(browser, deviceName, startFrozen) {
  const dev = DEVICES[deviceName];
  const major = browser.version().split('.')[0];
  const ua = dev.userAgent ?? `Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/${major}.0.0.0 Safari/537.36`;
  const ctx = await browser.newContext({
    ...dev, userAgent: ua, reducedMotion: 'no-preference', colorScheme: 'light', forcedColors: 'none',
    locale: 'en-US', timezoneId: 'UTC', serviceWorkers: 'block', acceptDownloads: false,
  });
  await ctx.addInitScript(installVirtualTime, { startFrozen: !!startFrozen });
  // read-only guard: state-changing requests to Fabius' own app / gate never leave the browser
  await ctx.route(/fabius-one\.vercel\.app|fabius-x402|railway\.app/, (route) => {
    const m = route.request().method();
    if (m === 'GET' || m === 'HEAD' || m === 'OPTIONS') return route.continue();
    log(`[guard] blocked ${m} ${route.request().url()}`);
    return route.abort();
  });
  ctx.on('page', (p) => { setTimeout(() => { if (ctx.pages()[0] !== p) p.close().catch(() => {}); }, 0); });
  return ctx;
}

function wirePage(page, name) {
  const errors = [];
  page.on('pageerror', (e) => errors.push(String(e).slice(0, 300)));
  page.on('dialog', (d) => d.dismiss().catch(() => {}));
  page.on('console', (m) => { if (m.type() === 'error') errors.push(`console: ${m.text().slice(0, 300)}`); });
  return errors;
}

async function waitReady(page, ready = {}, frozen) {
  await page.waitForLoadState('load', { timeout: 60000 }).catch(() => {});
  await page.waitForLoadState('networkidle', { timeout: (ready.idle ?? 10) * 1000 }).catch(() => {});
  await page.evaluate(() => document.fonts.ready.then(() => document.fonts.status)).catch(() => {});
  const cond = ready.selector ? { selector: ready.selector } : ready.text ? { text: ready.text } : ready.js ? { js: ready.js } : null;
  const deadline = Date.now() + (ready.timeout ?? 30) * 1000;
  let nudged = 0;
  while (cond && !(await page.evaluate((c) => window.__vt.test(c), cond))) {
    if (Date.now() > deadline) throw new Error(`ready condition not met: ${JSON.stringify(cond)}`);
    if (frozen && (ready.nudge ?? 1) > 0 && nudged < (ready.maxNudge ?? 600)) {
      const ms = ready.nudge ?? 1;
      await page.evaluate((v) => window.__vtStep(v), ms);
      nudged += ms;
    }
    await sleep(100);
  }
  // in-viewport images decoded
  await page.evaluate(async () => {
    const imgs = [...document.images].filter((i) => { const r = i.getBoundingClientRect(); return r.bottom > 0 && r.top < innerHeight; });
    await Promise.all(imgs.map((i) => (i.complete ? null : i.decode().catch(() => {}))));
  }).catch(() => {});
  await sleep(ready.settle ?? 300);
  return nudged;
}

// ---------------------------------------------------------------------------------------------------------------
// Clip recorder
// ---------------------------------------------------------------------------------------------------------------
class Clip {
  constructor(page, cdp, flow, dev, file) {
    Object.assign(this, { page, cdp, flow, dev, file });
    this.frames = [];
    this.boxes = {};
    this.marks = {};
    this.shots = {};
    this.watched = {};
    this.cursor = { x: dev.viewport.width * 0.82, y: dev.viewport.height * 0.3, down: false, visible: false };
    this.sentCursor = null;
    this.scroll = null; // desired scrollY for the next frame (null = leave as is)
    this.scrollY = 0;
  }

  start() {
    mkdirSync(path.dirname(this.file), { recursive: true });
    this.ff = spawn('ffmpeg', [
      '-hide_banner', '-loglevel', 'error', '-y',
      '-f', 'image2pipe', '-framerate', String(FPS), '-c:v', 'mjpeg', '-i', '-',
      // Chrome JPEGs are JFIF (BT.601, full range) -> BT.709 limited range, tagged so browsers / Remotion decode the site's exact colours
      '-vf', 'scale=in_range=full:out_range=tv:in_color_matrix=bt601:out_color_matrix=bt709:flags=accurate_rnd+full_chroma_int,format=yuv420p,setparams=range=tv:color_primaries=bt709:color_trc=bt709:colorspace=bt709',
      '-c:v', 'libx264', '-preset', 'slow', '-crf', '18', '-pix_fmt', 'yuv420p', '-g', '60',
      '-color_primaries', 'bt709', '-color_trc', 'bt709', '-colorspace', 'bt709', '-color_range', 'tv',
      '-movflags', '+faststart', this.file,
    ], { stdio: ['pipe', 'inherit', 'inherit'] });
    this.ffDone = once(this.ff, 'exit');
  }

  async frame() {
    const { page, cdp, flow } = this;
    const c = this.cursor;
    if (!Number.isFinite(c.x) || !Number.isFinite(c.y)) throw new Error(`${flow.name}: cursor position is not a number (${c.x}, ${c.y})`);
    if (c.visible && (!this.sentCursor || this.sentCursor[0] !== c.x || this.sentCursor[1] !== c.y)) {
      await page.mouse.move(c.x, c.y);
      this.sentCursor = [c.x, c.y];
    }
    const res = await page.evaluate((o) => window.__vtFrame(o), {
      dt: DT, scrollY: this.scroll, boxes: flow.boxes, watch: this.pendingWatch(), until: this.until ?? null,
    });
    this.scrollY = res.scrollY;
    // clip is in document coordinates; scale = DPR gives native device pixels (no clip = CSS-size output)
    const { width: vw, height: vh } = this.dev.viewport;
    const clipRect = { x: res.scrollX, y: res.scrollY, width: vw, height: vh, scale: this.dev.deviceScaleFactor };
    this.lastClip = clipRect;
    const shot = await cdp.send('Page.captureScreenshot', { format: 'jpeg', quality: QUALITY, optimizeForSpeed: true, captureBeyondViewport: false, clip: clipRect });
    const buf = Buffer.from(shot.data, 'base64');
    if (!this.ff.stdin.write(buf)) await once(this.ff.stdin, 'drain');
    const i = this.frames.length;
    this.frames.push({ t: r1(i * DT), scrollY: r1(res.scrollY), cursor: { x: r1(c.x), y: r1(c.y), down: c.down, visible: c.visible } });
    for (const [k, v] of Object.entries(res.boxes)) (this.boxes[k] ??= []).push(v);
    for (const [k, v] of Object.entries(res.watch)) if (v && this.marks[k] == null) { this.marks[k] = i; log(`  mark ${k} @ frame ${i}`); }
    this.lastUntil = res.until;
    if (i % 60 === 0) process.stdout.write(`  ${flow.name} frame ${i}\r`);
    return i;
  }

  pendingWatch() {
    const w = {};
    const i = this.frames.length;
    for (const [k, v] of Object.entries(this.flow.watch || {})) {
      if (this.marks[k] != null) continue;
      if (v && typeof v === 'object' && v.after) {
        const m = this.marks[v.after];
        if (m == null || i < m + 3) continue; // armed a few frames after the triggering mark
      }
      w[k] = v;
    }
    return w;
  }

  async point(target) {
    if (Array.isArray(target)) return target;
    const spec = typeof target === 'string' ? { selector: target } : target;
    const r = await this.page.evaluate((s) => window.__vtRect(s), spec);
    if (!r) throw new Error(`${this.flow.name}: target not found ${JSON.stringify(spec)}`);
    const [fx, fy] = spec.at ?? [0.5, 0.5];
    return [r[0] + r[2] * fx + (spec.dx ?? 0), r[1] + r[3] * fy + (spec.dy ?? 0)];
  }

  async scrollTarget(s) {
    const vh = this.dev.viewport.height;
    const info = await this.page.evaluate(() => ({ y: scrollY, max: document.documentElement.scrollHeight - innerHeight }));
    let y;
    if (typeof s === 'number') y = s;
    else if (s.by != null) y = info.y + s.by;
    else if (s.y != null) y = s.y;
    else if (s.js) y = await this.page.evaluate((js) => (0, eval)(js), s.js);
    else {
      const spec = s.to ?? s;
      const r = await this.page.evaluate((sp) => window.__vtRect(sp), typeof spec === 'string' ? { selector: spec } : spec);
      if (!r) throw new Error(`${this.flow.name}: scroll target not found ${JSON.stringify(spec)}`);
      const top = r[1] + info.y;
      const block = s.block ?? 'start';
      y = block === 'center' ? top + r[3] / 2 - vh / 2 : block === 'end' ? top + r[3] - vh : top;
      y += s.offset ?? 0;
    }
    return Math.max(0, Math.min(info.max, y));
  }

  async run(steps) {
    for (const st of steps) await this.runStep(st);
  }

  async runStep(st) {
    const f0 = this.frames.length;
    if (st.mark) this.marks[st.mark] = f0;
    if (st.cursor) { this.cursor.visible = st.cursor.visible ?? true; [this.cursor.x, this.cursor.y] = await this.point(st.cursor.at ?? st.cursor); }
    if (st.wait != null && st.move == null && st.scroll == null && st.click == null) {
      const n = Math.round(st.wait * FPS);
      for (let i = 0; i < n; i++) await this.frame();
      return;
    }
    if (st.move != null || st.hover != null || st.scroll != null) {
      const dur = st.dur ?? 1;
      const n = Math.max(1, Math.round(dur * FPS));
      let path = null;
      if (st.move != null || st.hover != null) {
        const tgt = st.move ?? st.hover;
        const isXY = (v) => Array.isArray(v) && v.length === 2 && typeof v[0] === 'number' && typeof v[1] === 'number';
        const pts = Array.isArray(tgt) && !isXY(tgt) ? tgt : [tgt]; // several targets = one path through them
        const abs = [[this.cursor.x, this.cursor.y]];
        for (const p of pts) abs.push(await this.point(p));
        path = makePath(abs, pts.length === 1 ? st.arc ?? 0.06 : 0);
        this.cursor.visible = true;
      }
      let y0 = null, y1 = null;
      if (st.scroll != null) { y0 = this.scrollY; y1 = await this.scrollTarget(st.scroll); }
      const em = ease(st.ease ?? (st.scroll != null ? 'inOutCubic' : 'inOutSine'));
      const es = ease(st.scrollEase ?? st.ease ?? 'inOutCubic');
      for (let i = 1; i <= n; i++) {
        const t = i / n;
        if (path) [this.cursor.x, this.cursor.y] = path(em(t));
        if (y0 != null) this.scroll = Math.round(y0 + (y1 - y0) * es(t)); // Chrome snaps scroll offsets to whole CSS px
        await this.frame();
      }
      this.scroll = null;
      if (st.wait) for (let i = 0, m = Math.round(st.wait * FPS); i < m; i++) await this.frame();
      return;
    }
    if (st.click != null) {
      const p = st.click === true ? [this.cursor.x, this.cursor.y] : await this.point(st.click);
      if (Math.hypot(p[0] - this.cursor.x, p[1] - this.cursor.y) > 3 || !this.cursor.visible) {
        await this.runStep({ move: p, dur: st.moveDur ?? 0.6 });
      }
      if (st.mark) this.marks[st.mark] = this.frames.length; // click marks sit on the mouse-down frame
      await this.page.mouse.down();
      this.cursor.down = true;
      for (let i = 0, n = Math.round((st.hold ?? 0.11) * FPS); i < n; i++) await this.frame();
      await this.page.mouse.up();
      this.cursor.down = false;
      if (st.markUp) this.marks[st.markUp] = this.frames.length; // the click handler has run before this frame
      for (let i = 0, n = Math.round((st.wait ?? 0) * FPS); i < n; i++) await this.frame();
      return;
    }
    if (st.waitFor) {
      this.until = st.waitFor;
      const max = Math.round((st.timeout ?? 10) * FPS);
      let i = 0;
      for (; i < max; i++) { await this.frame(); if (this.lastUntil) break; }
      this.until = null;
      if (i >= max) log(`  [warn] ${this.flow.name}: waitFor timed out ${JSON.stringify(st.waitFor)}`);
      else if (st.markAs) this.marks[st.markAs] = this.frames.length - 1;
      for (let k = 0, n = Math.round((st.after ?? 0) * FPS); k < n; k++) await this.frame();
      return;
    }
    if (st.shot) {
      const name = st.shot;
      const file = path.join(OUT, 'stills', `${this.flow.name}-${name}.jpg`);
      mkdirSync(path.dirname(file), { recursive: true });
      const s = await this.cdp.send('Page.captureScreenshot', { format: 'jpeg', quality: 95, captureBeyondViewport: false, clip: this.lastClip });
      writeFileSync(file, Buffer.from(s.data, 'base64'));
      const fi = Math.max(0, this.frames.length - 1);
      const boxes = Object.fromEntries(Object.entries(this.boxes).map(([k, v]) => [k, v[fi]]));
      writeFileSync(file.replace(/\.jpg$/, '.json'), JSON.stringify({ clip: this.flow.name, frame: fi, viewport: this.dev.viewport, deviceScaleFactor: this.dev.deviceScaleFactor, scrollY: this.scrollY, boxes }, null, 1));
      this.shots[name] = { frame: fi, file: path.relative(OUT, file).replace(/\\/g, '/') };
      return;
    }
    if (st.js) { await this.page.evaluate((js) => (0, eval)(js), st.js); return; }
    if (st.mark) return;
    throw new Error(`unknown step ${JSON.stringify(st)}`);
  }

  async finish(meta) {
    this.ff.stdin.end();
    await this.ffDone;
    const json = {
      name: this.flow.name, ...meta,
      fps: FPS, frameCount: this.frames.length, duration: r1(this.frames.length / FPS),
      viewport: this.dev.viewport, deviceScaleFactor: this.dev.deviceScaleFactor,
      video: { width: this.dev.viewport.width * this.dev.deviceScaleFactor, height: this.dev.viewport.height * this.dev.deviceScaleFactor, file: path.basename(this.file) },
      units: 'CSS px; cursor and boxes in viewport coordinates at that frame; box = [x, y, width, height]; video px = CSS px x deviceScaleFactor',
      marks: this.marks, shots: this.shots,
      boxSpecs: this.flow.boxes ?? {},
      frames: this.frames, boxes: this.boxes,
    };
    writeFileSync(this.file.replace(/\.mp4$/, '.json'), JSON.stringify(json));
    return json;
  }
}

async function runClip(browser, flow, env) {
  const frozen = (flow.start ?? 'frozen') === 'frozen';
  const dev = DEVICES[flow.device ?? 'desktop'];
  const ctx = await newContext(browser, flow.device ?? 'desktop', frozen);
  const page = await ctx.newPage();
  const errors = wirePage(page, flow.name);
  const cdp = await ctx.newCDPSession(page);
  const url = BASE + flow.path;
  log(`[clip] ${flow.name} ${url} (${flow.device ?? 'desktop'}, start ${frozen ? 'frozen' : 'free'})`);
  const t0 = Date.now();
  await page.goto(url, { waitUntil: 'commit', timeout: 60000 });
  let nudged;
  try { nudged = await waitReady(page, flow.ready, frozen); }
  catch (e) { await ctx.close().catch(() => {}); throw e; }
  if (!frozen) await page.evaluate(() => window.__vtFreeze());
  const file = path.join(OUT, 'clips', `${flow.name}.mp4`);
  const clip = new Clip(page, cdp, flow, dev, file);
  if (flow.scrollStart != null) {
    const y = await clip.scrollTarget(flow.scrollStart);
    await page.evaluate((yy) => { window.scrollTo({ top: yy, left: 0, behavior: 'instant' }); }, y);
    clip.scrollY = y;
    await sleep(400);
  }
  if (flow.cursorStart) {
    [clip.cursor.x, clip.cursor.y] = await clip.point(flow.cursorStart);
    clip.cursor.visible = true;
    await page.mouse.move(clip.cursor.x, clip.cursor.y);
    clip.sentCursor = [clip.cursor.x, clip.cursor.y];
  }
  for (let i = 0, n = Math.round((flow.preroll ?? 0) * FPS); i < n; i++) await page.evaluate((dt) => window.__vtFrame({ dt }), DT);
  const envInfo = await page.evaluate(() => ({
    reducedMotion: matchMedia('(prefers-reduced-motion: reduce)').matches,
    dpr: devicePixelRatio, ua: navigator.userAgent, title: document.title,
    canvases: [...document.querySelectorAll('canvas')].map((c) => [c.width, c.height]),
  }));
  if (envInfo.reducedMotion) throw new Error('prefers-reduced-motion is reduce');
  clip.start();
  const captureStartedUtc = new Date().toISOString();
  try {
    await clip.run(flow.steps);
  } catch (e) {
    try { clip.ff.stdin.destroy(); clip.ff.kill('SIGKILL'); } catch { /* ignore */ }
    await Promise.race([clip.ffDone, sleep(3000)]);
    rmSync(file, { force: true });
    await ctx.close().catch(() => {});
    throw e;
  }
  const json = await clip.finish({
    url, capturedUtc: captureStartedUtc, readOnly: true, gpu: env.gl, chrome: browser.version(),
    startMode: frozen ? 'frozen at first script (page loaded with virtual time stopped)' : 'free until ready, then frozen',
    readyNudgeMs: nudged, page: envInfo, pageErrors: errors.slice(0, 20),
  });
  await ctx.close();
  const mb = statSync(file).size / 1048576;
  log(`[clip] ${flow.name}: ${json.frameCount} frames (${json.duration}s) ${json.video.width}x${json.video.height} ${mb.toFixed(1)} MB in ${((Date.now() - t0) / 1000).toFixed(0)}s; marks ${JSON.stringify(json.marks)}`);
  if (errors.length) log(`  page errors: ${errors.length} (first: ${errors[0]})`);
  contactSheet(file, flow.name);
  return { name: flow.name, file, mb, frames: json.frameCount, duration: json.duration, size: `${json.video.width}x${json.video.height}`, marks: json.marks };
}

function contactSheet(file, name) {
  mkdirSync(CHECK, { recursive: true });
  try {
    execFileSync('ffmpeg', ['-hide_banner', '-loglevel', 'error', '-y', '-i', file, '-vf', 'fps=2,scale=480:-2,tile=6x4', '-q:v', '3', path.join(CHECK, `${name}-%02d.jpg`)]);
  } catch (e) { log(`  contact sheet failed: ${e.message}`); }
}

// ---------------------------------------------------------------------------------------------------------------
// Full-page stills (real time, no stepping): JPEG + document-coordinate boxes
// ---------------------------------------------------------------------------------------------------------------
async function runStill(browser, still) {
  const dev = DEVICES[still.device ?? 'desktop'];
  const ctx = await newContext(browser, still.device ?? 'desktop', false);
  const page = await ctx.newPage();
  const errors = wirePage(page, still.name);
  const cdp = await ctx.newCDPSession(page);
  const url = BASE + still.path;
  log(`[still] ${still.name} ${url}`);
  await page.goto(url, { waitUntil: 'commit', timeout: 60000 });
  await waitReady(page, still.ready, false);
  // walk the page so in-view reveals and lazy scenes run, then return to the top
  const h0 = await page.evaluate(() => document.documentElement.scrollHeight);
  for (let y = 0; y < h0; y += 450) { await page.evaluate((yy) => window.scrollTo({ top: yy, behavior: 'instant' }), y); await sleep(220); }
  await page.evaluate(() => window.scrollTo({ top: document.documentElement.scrollHeight, behavior: 'instant' }));
  await sleep(900);
  await page.evaluate(() => window.scrollTo({ top: 0, behavior: 'instant' }));
  await sleep(still.settle ?? 1800);
  if (still.waitFor) await page.waitForFunction((c) => window.__vt.test(c), still.waitFor, { timeout: 30000 }).catch(() => log(`  [warn] ${still.name}: waitFor timed out`));
  await sleep(500);
  const doc = await page.evaluate((boxes) => {
    const out = {};
    for (const [k, spec] of Object.entries(boxes || {})) {
      const els = window.__vt.find(spec);
      const rs = els.map((e) => { const r = e.getBoundingClientRect(); return [Math.round(r.left), Math.round(r.top + scrollY), Math.round(r.width), Math.round(r.height)]; });
      out[k] = typeof spec === 'object' && spec.all ? rs : rs[0] ?? null;
    }
    return { width: document.documentElement.scrollWidth, height: document.documentElement.scrollHeight, boxes: out };
  }, still.boxes);
  const dpr = dev.deviceScaleFactor;
  const file = path.join(OUT, 'stills', `${still.name}-full.jpg`);
  mkdirSync(path.dirname(file), { recursive: true });
  const W = dev.viewport.width;
  const H = doc.height;
  const maxTile = Math.floor(16000 / dpr); // GPU surfaces wrap beyond 16384 device px
  if (H <= maxTile) {
    const s = await cdp.send('Page.captureScreenshot', { format: 'jpeg', quality: STILL_QUALITY, captureBeyondViewport: true, clip: { x: 0, y: 0, width: W, height: H, scale: dpr } });
    writeFileSync(file, Buffer.from(s.data, 'base64'));
  } else {
    const tiles = [];
    const tileH = Math.ceil(H / Math.ceil(H / maxTile));
    for (let y = 0, k = 0; y < H; y += tileH, k++) {
      const h = Math.min(tileH, H - y);
      const s = await cdp.send('Page.captureScreenshot', { format: 'png', captureBeyondViewport: true, clip: { x: 0, y, width: W, height: h, scale: dpr } });
      const tf = path.join(ROOT, 'out', 'capture-check', `.tile-${still.name}-${k}.png`);
      mkdirSync(path.dirname(tf), { recursive: true });
      writeFileSync(tf, Buffer.from(s.data, 'base64'));
      tiles.push(tf);
    }
    execFileSync('ffmpeg', ['-hide_banner', '-loglevel', 'error', '-y', ...tiles.flatMap((t) => ['-i', t]),
      '-filter_complex', `${tiles.map((_, i) => `[${i}:v]`).join('')}vstack=inputs=${tiles.length},format=yuvj420p`, '-frames:v', '1', '-q:v', '3', file]);
    for (const t of tiles) rmSync(t, { force: true });
  }
  const json = {
    name: still.name, url, capturedUtc: new Date().toISOString(), readOnly: true,
    viewport: dev.viewport, deviceScaleFactor: dpr, document: { width: doc.width, height: doc.height },
    image: { file: path.basename(file), width: W * dpr, height: H * dpr },
    units: 'CSS px in document coordinates (top of page = 0); box = [x, y, width, height]; image px = CSS px x deviceScaleFactor',
    boxSpecs: still.boxes ?? {}, boxes: doc.boxes, pageErrors: errors.slice(0, 20),
  };
  writeFileSync(file.replace(/\.jpg$/, '.json'), JSON.stringify(json, null, 1));
  await ctx.close();
  const mb = statSync(file).size / 1048576;
  log(`[still] ${still.name}: ${json.image.width}x${json.image.height} ${mb.toFixed(1)} MB`);
  return { name: still.name, file, mb, size: `${json.image.width}x${json.image.height}` };
}

// ---------------------------------------------------------------------------------------------------------------
async function main() {
  const env = await launch();
  const results = [];
  const pick = (list) => list.filter((x) => !ONLY.length || ONLY.includes(x.name));
  try {
    if (!flag('stills-only')) for (const f of pick(FLOWS)) {
      try { results.push(await runClip(env.browser, f, env)); }
      catch (e) { log(`[clip] ${f.name} FAILED: ${e.stack || e}`); results.push({ name: f.name, failed: String(e.message || e) }); }
    }
    if (!flag('clips-only')) for (const s of pick(STILLS)) {
      try { results.push(await runStill(env.browser, s)); }
      catch (e) { log(`[still] ${s.name} FAILED: ${e.stack || e}`); results.push({ name: s.name, failed: String(e.message || e) }); }
    }
  } finally {
    await env.browser.close();
  }
  console.log('\nresult');
  let total = 0;
  for (const r of results) {
    if (r.failed) { console.log(`  FAILED ${r.name}: ${r.failed}`); continue; }
    total += r.mb;
    console.log(`  ${r.name.padEnd(16)} ${(r.duration != null ? `${r.duration}s ` : '').padEnd(8)}${r.size.padEnd(11)} ${r.mb.toFixed(1)} MB  ${path.relative(ROOT, r.file)}`);
  }
  console.log(`  total ${total.toFixed(1)} MB`);
  if (results.some((r) => r.failed)) process.exitCode = 1;
}

if (process.argv[1] && path.resolve(process.argv[1]) === fileURLToPath(import.meta.url)) await main();
export { installVirtualTime, makePath, EASE };
