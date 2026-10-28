# src/three: the website's 3D scenes, filmable

Ports of the three real-time scenes on fabius-one.vercel.app to `@remotion/three`, so the pitch video can fly a camera through them.
Every frame is a pure function of `t` (seconds) and props: no `useFrame` animation, no clock, no unseeded randomness.

| Scene | Website source | Component |
|---|---|---|
| Hero crystal (3x3x3 glass blocks) | `web/src/components/hero/Crystal.tsx` | `CrystalScene` (canvas) / `Crystal` (group) |
| Fabius Live Book pipeline | `web/.../desk/floor/PipelineScene.tsx` | `LiveBookScene` / `LiveBookWorld` |
| AI desk trading floor | `web/.../desk/floor/Scene.tsx` | `FloorScene` / `FloorWorld` |

Shared: `Stage` (canvas wrapper), `camera.tsx` (camera as data), `labels.tsx` (site labels as 3D tags), `desk/parts.tsx` (voxel NPC),
`desk/looks.ts` + `desk/model.ts` (same look/seat maths as the site), `data/desk-snapshot.json` + `snapshot.ts` (one real snapshot, typed).
Everything is re-exported from `index.ts`.

## Use in a scene

```tsx
import { useCurrentFrame, useVideoConfig, AbsoluteFill } from 'remotion';
import { LiveBookScene, camPath, orbitCam, liveBookSiteCam, LIVEBOOK_POINTS, DESK_BACKDROP_CSS, ramp } from '../three';

export const DeskShot: React.FC = () => {
  const t = useCurrentFrame() / useVideoConfig().fps;
  const cam = camPath([
    { at: 0, cam: liveBookSiteCam() },                                    // exactly the website's framing
    { at: 2, cam: orbitCam(-30, 4, 3.6, LIVEBOOK_POINTS.agents, 40) },   // agents' eye level
    { at: 6, cam: orbitCam(15, 12, 2.6, LIVEBOOK_POINTS.chain, 30), hold: true },
  ], t);
  return (
    <AbsoluteFill style={{ background: DESK_BACKDROP_CSS }}>
      <LiveBookScene t={t} cam={cam} cycleT={ramp(0.5, 6.5, t)} />
    </AbsoluteFill>
  );
};
```

## Props

Common to the three `*Scene` components: `t`, `cam` (default = the site preset), `background` (`'transparent'` or a CSS colour; crystal
default `#ece8fa`, desk scenes default transparent like the site), `fog` (`{color, near, far}` or null). `Stage` also takes `toneMapping`,
`exposure`, `shadows`, `bloom`, `fonts` if you assemble your own canvas from `Crystal` / `LiveBookWorld` / `FloorWorld`.

**CrystalScene** `counts` (default = live site: 22 verified, 4 sealed, 0 empty), `assemble` 0..1 (fly-in; default driven by `t` as on the
site, landed by ~2.4 s), `spread` 0..1 (exploded view along cell directions), `beatAt` (`[{t, block?, len?}]`, block = index into
`beatables()` or `'sealed'`/`'verified'`; default = site schedule: from 3.2 s every 3.4 s; `[]` = no beats), `sealWave` 0..1 (clear -> indigo
in commit order: locks first, in lock order), `verifyWave` 0..1 (indigo -> white for verified blocks), `lean {x,y}` (the site's pointer
tilt), `position` / `scale` (site: `crystalSiteLayout(aspect)`), `idle`, `yaw`, `sparkles`, `groundShadow`, `bloom` (`false` = no
postprocessing). Helpers: `crystalBeatInfo(props)` (which block is out, how far, its world position and the on-chain lock it stands for =
the site's beat label), `facingBlock(props, camPos, kind)` (pop the block that faces the camera), `crystalBlockWorld(props, i)`.

**LiveBookScene** `cycleT` 0..1 plays one cycle (windows in `CYCLE`: vote 0.02-0.2, motes to formula, formula spin 0.2-0.42, winner lights at
0.36, robot chest + arm 0.46-0.6, bars grow 0.61-0.78, block drops and lights 0.8-0.92); undefined = site steady state. `cycle`
(`DEFAULT_CYCLE` | `LIVE_CYCLE` | `REVEALED_CYCLE` or your own `PipelineCycle`), `labels`, `labelScale`, `labelOpacity`, `desync`, `reduced`.

**FloorScene** `beats` (times a new cycle lands: wire pulses + tower drop), `thinkUntilBeat`, `seats` / `hub` / `cycles` (default from the
snapshot), `lean`, `labels`, `labelScale`, `labelOpacity`, `desync`.

## Camera

`CameraDesc = {position, target, fov, roll?, near?, far?}` (perspective; near/far auto-scale with distance so long lenses keep depth
precision). `orbitCam(azDeg, elDeg, dist, target, fov, roll)`, `toOrbit` / `fromOrbit`, `telephoto(cam, viewHeight, fov)`, `camPath(keys, t)`
(C1 spline in orbit space: orbits stay round, distance and tan(fov/2) interpolate in log space so telephoto -> wide is a clean dolly-zoom;
`hold: true` stops at a key), `lerpCam(a, b, k)`. Presets: `CRYSTAL_SITE_CAM` (+ `crystalSiteLayout`), `liveBookSiteCam(aspect)`,
`floorSiteCam(aspect)` (the site's orthographic cameras as 4 deg telephotos with identical framing). `projectPoint(cam, p, w, h)` gives
pixel positions for 2D callouts that track 3D anchors.

## Anchors (world coordinates)

`LIVEBOOK_ANCHORS[agents|formula|bot|book|chain] = {label, focus}`, `LIVEBOOK_POINTS` (same focus points, `robot` named),
`liveBookAgentPositions(n)` (feet, head, vote cube). `floorAnchors()` -> per seat `{label, screen, head, desk}`, `hub {label, core}`,
`tower {label, top, base}`; `seatToWorld(seat, localPoint)` for anything on a desk. Crystal: `crystalBeatInfo().world`.

## Labels

The site pins DOM labels to 3D anchors (Bridge). Here they are optional in-3D tags (`labels`), drawn once into CanvasTextures in the site's
pill styles after the fonts load (`Stage fonts` holds the frame with delayRender), camera-facing, constant pixel size, always on top.
For your own typography use the anchors + `projectPoint` and draw 2D callouts.

## Changed from the website, and why

- Time: all `useFrame`/clock/`lerp` state replaced by functions of `t`; the site's per-frame lerp smoothing is reproduced analytically
  (`smoothedSin`, same amplitude and lag at 60 Hz). Pointer -> `lean` prop. Data-refresh "beats" -> `beats` / `cycleT`.
- Cameras: props instead of fixed orthographic cameras; the site framings are exact telephoto equivalents.
- Bloom: `@react-three/postprocessing`'s `<EffectComposer>` builds its composer in effects, so under Remotion the first frame of every
  render tab came out empty (verified: canvas not drawn at all) and the next ones without bloom. `Stage` builds the same postprocessing
  composer (RenderPass + Bloom 0.22 / 0.92 / 0.15 mipmap, HalfFloat, MSAA 8) synchronously. `bloom={false}` is the fallback: same colours
  (no tone mapping either way, as on the site), no glow.
- Live Book data: the public gateway hides the live cycle's bot, scores and positions for 24 h. `DEFAULT_CYCLE` = live cycle (6/6 valid,
  formula r4, 5 positions, sealed) + the newest revealed winner (B2-RS +19.6, 6 Oct 15:55Z) so the robot has an id; the 5 hidden positions
  are drawn as equal "locked" bars (lav with violet caps). Use `LIVE_CYCLE` for strictly live (robot shows "-"). Other bots' formula
  scores are not public, so their orbit cubes stay at minimum size.
- Floor poses are taken one minute into the last cycle (`FLOOR_NOW`); at fetch time the site showed every agent "thinking".
- Additions: crystal `spread`, `sealWave`/`verifyWave`, `sparkles`, a 3D contact shadow (the site's CSS ellipse), per-agent idle phase
  offsets (`desync`; the site moves everyone in lockstep), 2048 shadow maps and 3x monitor textures for close-ups, `cycleT` story beats
  (vote motes, orbit spin-up, arm swing, block drop) layered on the site's geometry.

## Data

`data/desk-snapshot.json`: public GETs at 2026-10-07T15:56:44Z of `GET /desk` and `GET /desk/fabius` on
`https://fabius-x402-production.up.railway.app` (the site's gateway) plus the hero's fields of `https://fabius-one.vercel.app/data/snapshot.json`
(chain block #135,379,370, 11 locks, 22 SAH -> crystal 22/4/0). Fonts come from `public/fonts` (JetBrains Mono, Inter).
**Git:** the repo-root `.gitignore` rule `data/` (line 40) ignores `src/three/data/`; commit the JSON with `git add -f` or add
`!vault/Video-Workspace/src/three/data/` to the root `.gitignore`, otherwise a clone has no snapshot and `snapshot.ts` fails to import.

## Test harness

`npx remotion studio src/three/preview/index.ts` - compositions `CrystalTest` (8 s), `DeskTest` (10 s), `FloorTest` (8 s),
`CrystalWaveTest` (6 s), 1920x1080 @ 60. Input props: `{"bloom":false}`, `{"transparent":true,"backdrop":"<css>"}`, `{"labels":false}`.
`node src/three/preview/stills.mjs CrystalTest:0,120 DeskTest:300` renders many stills from one bundle; `node src/three/preview/clips.mjs
DeskTest:180-299 --scale=0.5` renders timed mp4 clips. Always `--gl=angle` (the workspace config defaults to swangle).
