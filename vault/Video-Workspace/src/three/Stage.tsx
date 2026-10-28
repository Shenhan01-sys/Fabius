// <Stage>: the one canvas wrapper every scene uses. @remotion/three's <ThreeCanvas> (frameloop "never" while rendering, one advance() per
// Remotion frame), the camera from props (<CameraRig>), background colour or transparent, optional fog, tone mapping, shadows, and a
// deterministic bloom.
//
// Why not <EffectComposer> from @react-three/postprocessing: it builds the composer in a useEffect and its passes one more render later, and
// forces NoToneMapping in another useEffect. Under Remotion the first frame of every render tab is drawn (advance) before those effects run,
// so that frame came out without bloom and with the wrong tone mapping: a visible flicker at every chunk boundary of a parallel render.
// <DetBloom> builds the same postprocessing composer (RenderPass + EffectPass(BloomEffect), HalfFloat, MSAA 8) synchronously on mount and
// renders it from a priority-1 useFrame, so the very first advance() already draws the final picture.

import { useFrame, useThree } from '@react-three/fiber';
import { ThreeCanvas } from '@remotion/three';
import { BloomEffect, EffectComposer, EffectPass, RenderPass } from 'postprocessing';
import React, { useEffect, useLayoutEffect, useState } from 'react';
import { useVideoConfig } from 'remotion';
import * as THREE from 'three';
import { CameraRig, nearFar, ViewContext, type CameraDesc } from './camera';
import { useThreeFonts } from './fonts';

export type Background = 'transparent' | string;
export type FogDesc = { color: string; near: number; far: number };
export type BloomDesc = { intensity: number; threshold: number; smoothing: number; mipmapBlur?: boolean; radius?: number };
export type ToneMap = 'none' | 'neutral' | 'aces';

export type StageProps = {
  cam: CameraDesc;
  /** 'transparent' = alpha canvas, the composition's own world shows through. Otherwise a CSS colour cleared into the canvas. */
  background?: Background;
  fog?: FogDesc | false | null;
  toneMapping?: ToneMap;
  exposure?: number;
  shadows?: boolean;
  bloom?: BloomDesc | false | null;
  /** wait for the label/monitor fonts before mounting the canvas */
  fonts?: boolean;
  width?: number;
  height?: number;
  style?: React.CSSProperties;
  children: React.ReactNode;
};

const TONE: Record<ToneMap, THREE.ToneMapping> = { none: THREE.NoToneMapping, neutral: THREE.NeutralToneMapping, aces: THREE.ACESFilmicToneMapping };

function DetBloom({ bloom }: { bloom: BloomDesc }) {
  const gl = useThree((s) => s.gl);
  const scene = useThree((s) => s.scene);
  const camera = useThree((s) => s.camera);
  const [fx] = useState(() => {
    const composer = new EffectComposer(gl, { frameBufferType: THREE.HalfFloatType, multisampling: 8 });
    composer.addPass(new RenderPass(scene, camera));
    const effect = new BloomEffect({
      intensity: bloom.intensity,
      luminanceThreshold: bloom.threshold,
      luminanceSmoothing: bloom.smoothing,
      mipmapBlur: bloom.mipmapBlur ?? true,
      radius: bloom.radius ?? 0.85,
    });
    composer.addPass(new EffectPass(camera, effect));
    return { composer, effect, size: new THREE.Vector2(-1, -1) };
  });
  useLayoutEffect(() => {
    fx.effect.intensity = bloom.intensity;
    fx.effect.luminanceMaterial.threshold = bloom.threshold;
    fx.effect.luminanceMaterial.smoothing = bloom.smoothing;
  }, [fx, bloom.intensity, bloom.threshold, bloom.smoothing]);
  useEffect(() => () => fx.composer.dispose(), [fx]);
  useFrame(() => {
    const s = gl.getSize(new THREE.Vector2());
    if (s.x !== fx.size.x || s.y !== fx.size.y) {
      fx.composer.setSize(s.x, s.y);
      fx.size.copy(s);
    }
    fx.composer.render(0);
  }, 1);
  return null;
}

/** Keeps renderer flags in sync with props (R3F only reads `gl` options at creation). */
function GlSync({ toneMapping, exposure }: { toneMapping: ToneMap; exposure: number }) {
  const gl = useThree((s) => s.gl);
  useLayoutEffect(() => {
    gl.toneMapping = TONE[toneMapping];
    gl.toneMappingExposure = exposure;
  }, [gl, toneMapping, exposure]);
  return null;
}

export const Stage: React.FC<StageProps> = ({
  cam,
  background = 'transparent',
  fog = null,
  toneMapping = 'none',
  exposure = 1,
  shadows = false,
  bloom = null,
  fonts = false,
  width,
  height,
  style,
  children,
}) => {
  const vc = useVideoConfig();
  const w = width ?? vc.width;
  const h = height ?? vc.height;
  const fontsOk = useThreeFonts(fonts);
  if (!fontsOk) return null;
  const { near, far } = nearFar(cam);
  return (
    <ThreeCanvas
      width={w}
      height={h}
      style={style}
      // devicePixelRatio = Remotion's --scale: draw at the output resolution, never a fixed 1x
      dpr={[0.1, 8]}
      shadows={shadows}
      flat={toneMapping === 'none'}
      camera={{ position: cam.position, fov: cam.fov, near, far }}
      gl={{ antialias: true, alpha: true, preserveDrawingBuffer: true, powerPreference: 'high-performance', toneMapping: TONE[toneMapping], toneMappingExposure: exposure }}
    >
      <ViewContext.Provider value={{ cam, width: w, height: h }}>
        <GlSync toneMapping={toneMapping} exposure={exposure} />
        <CameraRig cam={cam} />
        {background !== 'transparent' && <color attach="background" args={[background]} />}
        {fog ? <fog attach="fog" args={[fog.color, fog.near, fog.far]} /> : null}
        {children}
        {bloom ? <DetBloom bloom={bloom} /> : null}
      </ViewContext.Provider>
    </ThreeCanvas>
  );
};
