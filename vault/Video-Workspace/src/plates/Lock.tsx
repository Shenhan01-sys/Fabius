// 04 LOCK — "It starts with the rules. / Each of our six bots has its strategy hashed and locked on-chain. /
// A strategy that wasn't locked first can't commit a signal."
// Six thick glass rule tablets, one per bot with its one rule, land in 3D. A scan beam hashes each into its spec
// sha; solid padlocks drop and snap shut with the real lock times (deployments/97.json m3.locks); the tablets sit
// on the LockRegistry, and the B1 tablet opens into its page. Then the real refusal: a signal of bar 01 Oct
// (B1/B3 were locked 02 Oct) hits SignalAnchor's LockedAfterBar wall and bounces.
import React from 'react';
import { AbsoluteFill } from 'remotion';
import type { PlateProps } from '../timeline';
import { C, rgba } from '../lib/palette';
import { F } from '../lib/fonts';
import { lineOf, wordOf } from '../lib/lyrics';
import { clamp, ease, env, lerp, prog, pulse, shake } from '../lib/util';
import { GraphPaper, Karaoke, LavBg, Mono, stampStyle, Typer } from '../components/kit';
import { BrowserFrame } from '../components/devices';
import { Ambient } from '../components/camera';
import { At, Block, Box, Padlock3D, Plane, Stage, stageAt, type StageKey } from '../components/solid';

const L8 = lineOf('It starts with the rules');
const L9 = lineOf('Each of our six');
const L10 = lineOf('A strategy that');
const w9 = (q: string) => wordOf(L9, q), w10 = (q: string) => wordOf(L10, q);

const BOTS = [
  { id: 'B1-TREND', rule: 'long if close > close 60 days ago', sha: '0x23cb026b', at: '02 OCT 15:49Z' },
  { id: 'B2-RS', rule: 'long top 3 / short bottom 3 by 28-day return', sha: '0x2dd6ccf2', at: '04 OCT 16:37Z' },
  { id: 'B3-CARRY', rule: 'spot long + perp short while funding > 10%/yr', sha: '0xc528abf5', at: '02 OCT 15:49Z' },
  { id: 'B4-LISTING-FADE', rule: 'short a new listing, close after 14 days', sha: '0x78bb0e32', at: '04 OCT 16:37Z' },
  { id: 'B5-CORE-RWA', rule: 'BTC and gold weighted by 1/σ over 90 days', sha: '0x2dfb0fa4', at: '04 OCT 16:37Z' },
  { id: 'B6-BOUNCE', rule: 'buy when 10-day z < −2, exit at z ≥ 0', sha: '0x4a6d180d', at: '04 OCT 16:37Z' },
];
const SW = 470, SH = 250, SD = 36;
const slot = (i: number) => ({ x: ((i % 3) - 1) * 520, y: (Math.floor(i / 3) - 0.5) * 300 });
const RAIL_Y = 330;

const typed = (t: number, t0: number, text: string, cps: number) => text.slice(0, clamp(Math.floor((t - t0) * cps), 0, text.length));

const SLAB_FACES = {
  front: 'linear-gradient(160deg, rgba(255,255,255,0.97) 0%, rgba(246,243,255,0.93) 55%, rgba(233,227,253,0.92) 100%)',
  left: 'linear-gradient(180deg, #d9d0fb, #b9aaf3)',
  right: 'linear-gradient(180deg, #e3dcfd, #c4b6f6)',
  top: 'linear-gradient(90deg, #ffffff, #f1edff)',
  bottom: '#a593ec',
  back: '#d8cff9',
};

export default function Lock({ t, start, end }: PlateProps) {
  const tSix = w9('six').start;
  const tHash = w9('hashed').start;
  const tLock = w9('locked').start;
  const tChain = w9('on-chain').start;
  const tOut = L10.start - 0.35; // the tablets step back for the refusal
  const tGo = w10('locked').start, tHit = w10('can’t').start + 0.05;
  const leave = prog(t, end - 0.2, end, ease.inCubic);
  const sh = shake(t, 7 * pulse(t, tHit, 0.06));

  const cam: StageKey[] = [
    { t: start - 0.3, rx: 16, ry: -24, z: -260 },
    { t: L8.end + 0.1, rx: 9, ry: -9, z: 0, ez: ease.outCubic },
    { t: tHash, rx: 7, ry: -3, z: 30 },
    { t: tChain + 0.2, rx: 10, ry: 4, z: -40, y: 20 },
    { t: L10.start + 0.2, rx: 9, ry: -12, z: -60, y: 0 },
    { t: end + 0.3, rx: 8, ry: -16, z: -30, y: 0 },
  ];
  const c = stageAt(cam, t);
  const back = prog(t, tOut, tOut + 0.6, ease.inOutCubic);

  const slab = (i: number) => {
    const b = BOTS[i]!, p = slot(i);
    const tLand = L8.start + 0.12 + 0.1 * i;
    const k = prog(t, tLand - 0.75, tLand, ease.outCubic);
    if (k <= 0) return null;
    const tScan = tHash - 0.12 + 0.07 * i;
    const scan = prog(t, tScan, tScan + 0.42, ease.inOutCubic);
    const tDrop = tLock - 0.28 + 0.07 * i, tShut = tDrop + 0.24;
    const drop = prog(t, tDrop, tShut, ease.inQuad);
    const shut = prog(t, tShut + 0.02, tShut + 0.12, ease.outQuart);
    const dip = 16 * pulse(t, tShut, 0.09);
    const glow = pulse(t, tSix + 0.07 * i, 0.16) + 0.6 * pulse(t, tShut, 0.12);
    const alpha = clamp(k * 2.2) * (1 - 0.9 * back);
    const locked = t >= tShut;
    return (
      <At key={b.id} x={p.x} y={p.y + 90 * (1 - k) + 5 * Math.sin(t * 1.4 + i * 1.9)} z={lerp(-1500, 0, k) - dip - 380 * back} rx={22 * (1 - k)} ry={-38 * (1 - k)}>
        <Box w={SW} h={SH} d={SD} faces={SLAB_FACES} radius={18} edge={rgba('violet', 0.22 + 0.5 * clamp(glow))} edgeW={1.5} alpha={alpha}
          glow={`0 40px 70px -30px rgba(62,37,160,0.45), 0 0 ${26 * glow}px ${rgba('violet', 0.55 * clamp(glow))}`}>
          <div style={{ position: 'absolute', left: 28, top: 22, ...F.archivo(36, 850, 100), color: C.ink, letterSpacing: -0.4 }}>{b.id}</div>
          <div style={{ position: 'absolute', left: 28, top: 74, width: 380, ...F.mono(18.5, 400), lineHeight: 1.38, color: rgba('ink', 0.86) }}>
            {typed(t, tLand - 0.1, b.rule, 80)}
          </div>
          {/* the spec strip */}
          <div style={{ position: 'absolute', left: 0, right: 0, bottom: 0, height: 72, borderRadius: '0 0 16px 16px', background: locked ? 'linear-gradient(90deg, rgba(110,75,255,0.16), rgba(110,75,255,0.08))' : 'rgba(201,189,242,0.28)', borderTop: `1px solid ${rgba('violet', 0.18)}` }}>
            <div style={{ position: 'absolute', left: 28, top: 12, opacity: prog(t, tScan + 0.1, tScan + 0.3) }}>
              <Mono size={11} col={rgba('ink', 0.5)} spacing={2.2}>spec sha-256</Mono>
              <div style={{ ...F.mono(20, 600), color: C.violet, marginTop: 3 }}>{scan > 0.35 ? typed(t, tScan + 0.15, `${b.sha}…`, 60) : ''}</div>
            </div>
            <div style={{ position: 'absolute', right: 26, top: 12, textAlign: 'right', opacity: prog(t, tShut, tShut + 0.15) }}>
              <Mono size={11} col={rgba('ink', 0.5)} spacing={2.2}>locked · chain 97</Mono>
              <div style={{ ...F.mono(16, 600), color: C.ink, marginTop: 5 }}>{typed(t, tShut + 0.05, b.at, 70)}</div>
            </div>
          </div>
          {/* the hash scan */}
          {scan > 0 && scan < 1 && (
            <div style={{ position: 'absolute', left: 0, right: 0, top: lerp(-34, SH - 34, scan), height: 34, background: `linear-gradient(180deg, ${rgba('violet', 0)} 0%, ${rgba('violet', 0.22)} 70%, ${rgba('violet2', 0.95)} 100%)`, boxShadow: `0 6px 18px ${rgba('violet', 0.5)}` }} />
          )}
        </Box>
        {/* the padlock drops onto the tablet's corner and snaps shut */}
        {t >= tDrop && (
          <At x={SW / 2 - 58} y={-SH / 2 + 44 - 300 * (1 - drop)} z={SD / 2 + 18}>
            <Padlock3D s={1.2} shut={shut} alpha={clamp(prog(t, tDrop, tDrop + 0.08) * (1 - 0.9 * back))} />
          </At>
        )}
      </At>
    );
  };

  // the LockRegistry rail the six tablets stand on
  const rail = prog(t, tChain - 0.15, tChain + 0.35, ease.outCubic);

  // the refusal (L10): a signal of bar 01 Oct slides at SignalAnchor and bounces off the LockedAfterBar wall
  const sc = prog(t, L10.start - 0.2, L10.start + 0.45, ease.outCubic);
  const go = prog(t, tGo, tHit, ease.inQuad);
  const bounce = prog(t, tHit, tHit + 0.55, ease.outCubic);
  const cubeX = lerp(-600, 128, go) - 300 * bounce;
  const cubeY = -Math.sin(Math.PI * clamp(bounce * 1.4)) * 70 * (1 - bounce * 0.5);
  const hit = pulse(t, tHit, 0.14);
  const red = t >= tHit;

  return (
    <AbsoluteFill style={{ opacity: 1 - leave }}>
      <LavBg glow={0.8} />
      <div style={{ position: 'absolute', inset: 0, opacity: 0.5 }}><Ambient t={t} light seed={8} n={5} dust={18} cubes={6} /></div>
      <GraphPaper paper opacity={0.5} />

      <AbsoluteFill style={{ transform: `translate(${sh[0]}px, ${sh[1]}px)` }}>
        <Stage cam={c} t={t} drift={0.7} perspective={1800} cy={570}>
          {BOTS.map((_, i) => slab(i))}
          {rail > 0 && (
            <At x={0} y={RAIL_Y} z={-30 - 380 * back}>
              <Box w={1560 * rail} h={50} d={90} radius={10} alpha={1 - 0.85 * back} edge={rgba('violet2', 0.6)} edgeW={1}
                faces={{ front: `linear-gradient(90deg, ${C.night3}, #3a2d95 50%, ${C.night3})`, top: 'linear-gradient(90deg, #5a47c9, #7a63f0, #5a47c9)', left: C.night2, right: C.night2, bottom: C.indigo, back: C.night2 }}
                glow={`0 0 40px ${rgba('violet', 0.45)}`}>
                <div style={{ position: 'absolute', inset: 0, display: 'flex', alignItems: 'center', justifyContent: 'center', opacity: prog(t, tChain + 0.15, tChain + 0.4), whiteSpace: 'nowrap' }}>
                  <Mono size={14} col={C.lav} spacing={3}>LockRegistry 0xcF6f…Bb0C · BNB Smart Chain testnet (97) · write-once · a re-lock reverts</Mono>
                </div>
              </Box>
            </At>
          )}

          {/* the refusal scene, in front of the tablets */}
          {sc > 0 && (
            <At x={0} y={150} z={170}>
              {/* the glass track */}
              <At y={64}>
                <Box w={1300 * sc} h={12} d={170} radius={6} alpha={sc} edge="rgba(255,255,255,0.8)" edgeW={1}
                  faces={{ front: 'rgba(255,255,255,0.75)', top: 'linear-gradient(90deg, rgba(255,255,255,0.55), rgba(236,232,250,0.85))', left: C.lav2, right: C.lav2, bottom: C.lav3, back: C.lav2 }} />
              </At>
              {/* SignalAnchor */}
              <At x={440} y={-82} z={0}>
                <Box w={290} h={280} d={230} radius={14} alpha={sc} edge={rgba('violet2', 0.9)} edgeW={1.5}
                  faces={{ front: `linear-gradient(150deg, #33287a, ${C.night2} 60%, ${C.indigo})`, top: 'linear-gradient(90deg, #4b3cae, #3a2d95)', left: `linear-gradient(180deg, #2a2168, ${C.indigo})`, right: `linear-gradient(180deg, #2a2168, ${C.indigo})`, bottom: C.indigo, back: C.night2 }}
                  glow={`inset 0 0 50px ${rgba('violet', 0.45)}`}>
                  <div style={{ position: 'absolute', left: 0, right: 0, top: 30, textAlign: 'center', ...F.mono(24, 600), color: C.lav }}>SignalAnchor</div>
                  <div style={{ position: 'absolute', left: 0, right: 0, top: 66, textAlign: 'center', ...F.mono(14, 400), color: rgba('lav', 0.7) }}>.commit(bot, specSha, bar)</div>
                  <div style={{ position: 'absolute', left: 85, top: 110, width: 120, height: 120, borderRadius: 14, border: `2px solid ${red ? C.gap : C.violet2}`, background: red ? rgba('gap', 0.18 + 0.4 * hit) : rgba('violet', 0.25), boxShadow: `0 0 ${30 + 40 * hit}px ${red ? rgba('gap', 0.6) : rgba('violet', 0.6)}` }} />
                </Box>
              </At>
              {/* the LockedAfterBar wall */}
              <At x={200} y={-82} z={0}>
                <Box w={22} h={280} d={240} radius={6} alpha={sc * (0.55 + 0.45 * clamp(hit * 2))} edge={rgba('gap', 0.9)} edgeW={1.5}
                  faces={{ front: rgba('gap', 0.55), left: `linear-gradient(180deg, ${rgba('gap', 0.35 + 0.5 * hit)}, ${rgba('gap', 0.15 + 0.4 * hit)})`, right: rgba('gap', 0.3), top: rgba('gap', 0.7), bottom: rgba('gap', 0.3), back: rgba('gap', 0.3) }}
                  glow={`0 0 ${20 + 60 * hit}px ${rgba('gap', 0.5 + 0.4 * hit)}`} />
              </At>
              {/* the signal of bar 01 Oct */}
              <At x={cubeX} y={-1 + cubeY} z={0}>
                <At rz={-25 * bounce}>
                  <Block s={118} state="sealed" alpha={sc} label="bar 01 Oct" />
                </At>
                <At y={-112}>
                  <Plane w={330} h={30} style={{ textAlign: 'center', opacity: sc }}>
                    <span style={{ ...F.mono(17, 600), color: C.ink }}>B1-TREND · bar 01 Oct</span>
                  </Plane>
                </At>
              </At>
            </At>
          )}
        </Stage>
      </AbsoluteFill>

      {/* words: the title, then each line in the same place */}
      <div style={{ position: 'absolute', left: 150, top: 104, opacity: 1 - prog(t, L9.start - 0.3, L9.start - 0.05) }}>
        <Karaoke t={t} words={L8.words} st={{ font: F.serif(84, 500), light: true }} />
      </div>
      <div style={{ position: 'absolute', left: 150, right: 150, top: 120, opacity: env(t, L9.start - 0.3, L10.start - 0.15, 0.25, 0.25) }}>
        <Karaoke t={t} words={L9.words} st={{ font: F.archivo(46, 800, 100), light: true }} wrap />
      </div>
      <div style={{ position: 'absolute', right: 150, top: 196, textAlign: 'right', opacity: env(t, tSix, L10.start - 0.15, 0.3, 0.25) }}>
        <Mono size={14} col={rgba('ink', 0.55)}>six bots · one rule each · one parameter</Mono>
      </div>
      <div style={{ position: 'absolute', left: 150, right: 150, top: 120, opacity: env(t, L10.start - 0.2, end + 1, 0.25, 0.3) }}>
        <Karaoke t={t} words={L10.words} st={{ font: F.archivo(50, 800, 100), light: true }} wrap />
      </div>
      <div style={{ position: 'absolute', left: 150, top: 194, opacity: prog(t, L10.start + 0.3, L10.start + 0.6) }}>
        <Typer t={t} t0={L10.start + 0.3} text="B1-TREND, B3-CARRY · bar 01 Oct · locked 02 Oct → the bar came first" size={18} weight={500} col={rgba('ink', 0.72)} cps={80} caret={false} />
      </div>
      <div style={{ position: 'absolute', left: 1010, top: 268, ...stampStyle(t, tHit + 0.3, -5) }}>
        <div style={{ ...F.mono(30, 600), color: C.gap, border: `3px solid ${C.gap}`, padding: '8px 18px', background: rgba('lav', 0.82), borderRadius: 6 }}>revert LockedAfterBar()</div>
      </div>

      {/* the B1 tablet opens into its page: the rule as locked, and the on-chain lock */}
      {(() => {
        const tA = tChain + 0.1, tB = L10.start - 0.12;
        const k = prog(t, tA, tA + 0.42, ease.outQuart) * (1 - prog(t, tB, tB + 0.3, ease.inCubic));
        if (k <= 0.001) return null;
        return (
          <div style={{ position: 'absolute', left: lerp(250, 380, k), top: lerp(300, 236, k), transform: `perspective(1600px) rotateY(${lerp(-24, -4, k)}deg) scale(${lerp(0.4, 1, k)})`, transformOrigin: '0 0', opacity: clamp(k * 2) }}>
            <BrowserFrame src="ui/bot-d-top.jpg" url="fabius-one.vercel.app/bot/B1-TREND" w={1160} h={620} imgW={2160} scroll={lerp(0, 120, prog(t, tA, tB))} glint={prog(t, tA + 0.3, tA + 1.0)} />
          </div>
        );
      })()}
    </AbsoluteFill>
  );
}
