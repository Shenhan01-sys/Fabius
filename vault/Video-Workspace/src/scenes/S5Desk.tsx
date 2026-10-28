// AI DESK - "Who picks the bot? A desk of AI agents. Every five minutes, analysts with their own on-chain identities
// make their picks, and a locked formula turns them into one paper portfolio, sealed before the cycle ends."
// The site's own 3D, re-rendered (src/three, data = public GET /desk 7 Oct 15:56Z): the desk floor from above, a crane
// down to the agents at their screens, their ERC-8004 identities (deployments/97.json analis.agents), a cycle landing;
// then the Live Book pipeline: votes -> the locked formula -> the bot's rule -> one paper book -> the root sealed on
// BNB Chain (DeskAnchor, one root per 300 s cycle; 281 cycles sealed in the 24 h before the snapshot).
import React from 'react';
import { AbsoluteFill, useVideoConfig } from 'remotion';
import { NightWorld } from '../fx/world';
import { Flash, GlowBlob } from '../fx/fx';
import { Headline } from '../ui/text';
import { Tag } from '../ui/bits';
import { BrowserWindow, Clip } from '../ui/browser';
import { At, camAt, Space } from '../cam/space';
import { C, rgba } from '../lib/palette';
import { inter, label, mono } from '../lib/fonts';
import { ease, prog } from '../lib/util';
import { at, line } from '../lib/vo';
import type { SceneProps } from '../timeline';
import { camPath, floorAnchors, FloorScene, LiveBookScene, LIVEBOOK_POINTS, orbitCam, projectPoint, type CameraDesc } from '../three';

// ERC-8004 identities of the desk's seats (deployments/97.json analis.agents + agen_luar_uji); seat state from GET /desk
const IDS: Record<string, { id: string; name: string; seat: string }> = {
  glm: { id: '2558', name: 'DeepSeek V4.1 Flash', seat: 'active' },
  berita: { id: '2561', name: 'Qwen 3.8 Omni Flash · news', seat: 'active' },
  muse: { id: '2566', name: 'Muse Spark 1.3', seat: 'active' },
  qwenplus: { id: '2567', name: 'Qwen 3.7 Plus', seat: 'active' },
  qwen: { id: '2559', name: 'Qwen 3.8 Flash', seat: 'trial' },
  x2573: { id: '2573', name: 'external agent', seat: 'trial' },
};

const Ring: React.FC<{ k: number; size?: number }> = ({ k, size = 120 }) => {
  const r = size / 2 - 7, c = 2 * Math.PI * r;
  return (
    <div style={{ position: 'relative', width: size, height: size }}>
      <svg width={size} height={size} style={{ position: 'absolute', inset: 0, transform: 'rotate(-90deg)' }}>
        <circle cx={size / 2} cy={size / 2} r={r} fill="rgba(26,20,66,0.6)" stroke="rgba(157,134,255,0.25)" strokeWidth={6} />
        <circle cx={size / 2} cy={size / 2} r={r} fill="none" stroke={C.violet2} strokeWidth={6} strokeLinecap="round" strokeDasharray={`${c * k} ${c}`} />
      </svg>
      <div style={{ position: 'absolute', inset: 0, display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', ...mono(size * 0.26, 700), color: '#f2efff', lineHeight: 1 }}>5<span style={{ ...mono(size * 0.11, 600), color: C.violet2, letterSpacing: 1 }}>MIN</span></div>
    </div>
  );
};

export const S5Desk: React.FC<SceneProps> = ({ t, t0, t1 }) => {
  const { width, height } = useVideoConfig();
  const d1 = line('desk1'), d2 = line('desk2'), d3 = line('desk3');
  const tFive = at('desk2', 'five'), tIds = at('desk2', 'identities'), tPicks = at('desk2', 'picks');
  const tFormula = at('desk3', 'formula'), tPortfolio = at('desk3', 'portfolio'), tSealed = at('desk3', 'sealed');
  const tCut = d3.start - 0.05; // floor -> Live Book
  const anchors = floorAnchors();
  const seat = anchors.seats.berita ?? Object.values(anchors.seats)[0]!;
  // --- shot A: the floor
  const floorCam: CameraDesc = camPath([
    { at: t0, cam: orbitCam(-20, 78, 26, [0, 0, 0], 28) },
    { at: d1.end, cam: orbitCam(10, 34, 15, [0, 0.6, 0], 30) },
    { at: tFive + 0.9, cam: orbitCam(38, 10, 3.4, seat.head, 36) },
    { at: tIds + 0.1, cam: orbitCam(-25, 22, 10.5, [0, 0.8, 0], 32) },
    { at: tCut, cam: orbitCam(-70, 16, 8.2, [0, 0.8, 0], 32), hold: true },
  ], t);
  // --- shot B: the Live Book
  const bookCam: CameraDesc = camPath([
    { at: tCut, cam: orbitCam(-28, 6, 4.2, LIVEBOOK_POINTS.agents, 34) },
    { at: tFormula + 0.6, cam: orbitCam(18, 14, 3.6, LIVEBOOK_POINTS.formula, 32) },
    { at: tPortfolio + 0.3, cam: orbitCam(-12, 10, 4.4, [(LIVEBOOK_POINTS.robot[0] + LIVEBOOK_POINTS.book[0]) / 2, LIVEBOOK_POINTS.book[1], LIVEBOOK_POINTS.book[2]], 32) },
    { at: tSealed + 0.2, cam: orbitCam(22, 16, 3.0, LIVEBOOK_POINTS.chain, 30) },
    { at: t1 + 0.3, cam: orbitCam(34, 22, 3.6, LIVEBOOK_POINTS.chain, 30), hold: true },
  ], t);
  const cycleT = 0.02 + 0.92 * prog(t, tCut - 0.1, d3.end + 0.1, ease.linear);
  const inFloor = t < tCut + 0.05;
  const ring = prog(t, t0 + 0.4, d3.end, ease.linear);
  const sealNow = prog(t, tSealed - 0.1, tSealed + 0.4, ease.cine);
  const ids = Object.entries(IDS).map(([slug, v], i) => {
    const a = anchors.seats[slug];
    if (!a) return null;
    const p = projectPoint(floorCam, a.label, width, height);
    const k = prog(t, tIds - 0.25 + i * 0.08, tIds + 0.25 + i * 0.08, ease.cine) * (1 - prog(t, tCut - 0.3, tCut));
    if (!p.inFront || k <= 0) return null;
    return (
      <div key={slug} style={{ position: 'absolute', left: p.x, top: p.y, transform: `translate(-50%, -100%) translateY(${(1 - k) * 16}px)`, opacity: k }}>
        <div style={{ padding: '10px 14px', borderRadius: 14, background: 'rgba(15,11,38,0.82)', border: `1px solid ${rgba('violet2', 0.45)}`, boxShadow: `0 12px 30px -10px ${rgba('violet', 0.6)}`, whiteSpace: 'nowrap' }}>
          <div style={{ ...label(11, 700), color: v.seat === 'trial' ? '#ffb86b' : C.violet2 }}>ERC-8004 · #{v.id} · {v.seat}</div>
          <div style={{ ...inter(17, 600), color: '#f2efff', marginTop: 3 }}>{v.name}</div>
        </div>
      </div>
    );
  });
  const chainP = projectPoint(bookCam, LIVEBOOK_POINTS.chain, width, height);
  const formulaP = projectPoint(bookCam, LIVEBOOK_POINTS.formula, width, height);
  const bookP = projectPoint(bookCam, LIVEBOOK_POINTS.book, width, height);
  return (
    <AbsoluteFill>
      <NightWorld t={t} glow={1.1} grid={0.45} />
      <GlowBlob x={960} y={620} r={720} col="violet" a={0.22} />
      {inFloor ? (
        <AbsoluteFill>
          <FloorScene t={t - t0} cam={floorCam} beats={[tPicks - t0]} thinkUntilBeat labels={false} />
          <AbsoluteFill style={{ zIndex: 5 }}>{ids}</AbsoluteFill>
        </AbsoluteFill>
      ) : (
        <AbsoluteFill>
          <LiveBookScene t={t - t0} cam={bookCam} cycleT={cycleT} labels={false} />
          {/* callouts that ride on the 3D anchors */}
          {formulaP.inFront ? (
            <div style={{ position: 'absolute', left: formulaP.x, top: formulaP.y - 210, transform: 'translateX(-50%)', opacity: prog(t, tFormula, tFormula + 0.4) * (1 - prog(t, tPortfolio - 0.3, tPortfolio)) }}>
              <Tag dark size={18}>locked formula · r4 · sha 0x6f613e50…</Tag>
            </div>
          ) : null}
          {bookP.inFront ? (
            <div style={{ position: 'absolute', left: bookP.x, top: bookP.y - 200, transform: 'translateX(-50%)', opacity: prog(t, tPortfolio, tPortfolio + 0.4) * (1 - prog(t, tSealed - 0.4, tSealed)) }}>
              <Tag dark size={18}>one paper book · max 5 positions</Tag>
            </div>
          ) : null}
          {chainP.inFront ? <GlowBlob x={chainP.x} y={chainP.y - 40} r={260} col="violet2" a={0.55 * sealNow} /> : null}
          {chainP.inFront ? (
            <div style={{ position: 'absolute', left: chainP.x + 120, top: chainP.y - 150, opacity: sealNow }}>
              <div style={{ padding: '16px 22px', borderRadius: 18, background: 'rgba(15,11,38,0.86)', border: `1px solid ${rgba('violet2', 0.5)}`, boxShadow: `0 20px 50px -14px ${rgba('violet', 0.7)}`, whiteSpace: 'nowrap' }}>
                <div style={{ ...label(13, 700), color: C.violet2 }}>DeskAnchor · BNB Chain · sealed</div>
                <div style={{ ...inter(22, 600), color: '#f2efff', marginTop: 6 }}>one root per 5-minute cycle</div>
                <div style={{ ...mono(15, 500), color: rgba('lav', 0.7), marginTop: 6 }}>281 cycles sealed in the last 24 h</div>
              </div>
            </div>
          ) : null}
        </AbsoluteFill>
      )}
      {/* the real /desk page first (capture desk), then the camera dives into its 3D */}
      {t < d1.end + 0.6 ? (
        <AbsoluteFill style={{ zIndex: 4, opacity: 1 - prog(t, d1.end - 0.15, d1.end + 0.5, ease.inCubic), transform: `scale(${1 + 0.7 * prog(t, d1.end - 0.3, d1.end + 0.5, ease.inCubic)})`, transformOrigin: '62% 58%' }}>
          <NightWorld t={t} glow={1.1} grid={0.45} />
          <Space cam={camAt([{ t: t0, z: -300, x: -430, rx: 5, ry: -16 }, { t: d1.end, z: -40, x: -380, rx: 3, ry: -8, ez: ease.inOutCubic }], t)} perspective={1600}>
            <At x={0} y={0} z={0}>
              <BrowserWindow w={1280} h={846} url="fabius-one.vercel.app/desk">
                <Clip name="desk" f={40 + Math.max(0, (t - t0) * 60)} />
              </BrowserWindow>
            </At>
          </Space>
          <AbsoluteFill style={{ background: 'linear-gradient(90deg, rgba(15,11,38,0.92) 0%, rgba(15,11,38,0.7) 32%, rgba(15,11,38,0) 55%)' }} />
        </AbsoluteFill>
      ) : null}
      <Flash t={t} at={tCut} col="violet2" strength={0.35} len={0.14} />
      {/* the 5-minute clock */}
      <div style={{ position: 'absolute', right: 80, top: 70, display: 'flex', alignItems: 'center', gap: 16, opacity: prog(t, tFive - 0.2, tFive + 0.3) }}>
        <div style={{ textAlign: 'right' }}>
          <div style={{ ...label(13, 700), color: C.violet2 }}>every 5 minutes</div>
          <div style={{ ...inter(18, 500), color: rgba('lav', 0.8), marginTop: 4 }}>paper · real fees · sealed on-chain</div>
        </div>
        <Ring k={ring} size={112} />
      </div>
      <AbsoluteFill style={{ padding: '0 0 0 120px', justifyContent: 'center', pointerEvents: 'none', zIndex: 10 }}>
        <Headline t={t} size={112} col="#f2efff" out={d1.end + 0.2}
          segs={[{ text: 'Who picks the bot?', at: d1.words[0]!.start, voice: 'calm', size: 72 }, { text: 'A desk of AI agents.', at: at('desk1', 'desk'), voice: 'accent', col: C.violet2, br: true }]} />
      </AbsoluteFill>
      <AbsoluteFill style={{ background: `radial-gradient(ellipse 80% 70% at 50% 50%, rgba(15,11,38,0) 55%, rgba(15,11,38,0.35) 100%)`, pointerEvents: 'none' }} />
    </AbsoluteFill>
  );
};
