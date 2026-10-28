// In-3D replacement for the website's DOM labels (Bridge + LabelSync). Each tag is drawn once into a CanvasTexture in the site's styles
// (white/90 pill, violet/20 border, JetBrains Mono 10 px; dark variant for the formula/hub) and placed as a camera-facing plane on its 3D
// anchor. Its world size is recomputed from the camera every frame so it keeps a constant pixel size, like the DOM label did, and it is
// drawn on top of everything (depthTest off), like the DOM label was. Needs <Stage fonts>.

import React, { useEffect, useMemo } from 'react';
import * as THREE from 'three';
import { applyCam, useView, viewDepth } from './camera';
import { MONO, SANS } from './fonts';
import { C } from './palette';
import { DEG, type Vec3 } from './util';

export type TagLine = { text: string; color?: string; size?: number; weight?: number; font?: 'mono' | 'sans' };
export type TagSpec = { lines: TagLine[]; dark?: boolean; padX?: number; padY?: number; radius?: number };

const SS = 3; // supersampling of the label bitmap relative to its on-screen pixel size

function drawTag(spec: TagSpec, px: number) {
  const k = px * SS;
  const padX = (spec.padX ?? 8) * k;
  const padY = (spec.padY ?? 2) * k;
  const radius = (spec.radius ?? 8) * k;
  const probe = document.createElement('canvas').getContext('2d')!;
  const fontOf = (l: TagLine) => `${l.weight ?? (l.font === 'sans' ? 500 : 400)} ${(l.size ?? 10) * k}px "${l.font === 'sans' ? SANS : MONO}"`;
  const metrics = spec.lines.map((l) => {
    probe.font = fontOf(l);
    return { w: probe.measureText(l.text).width, h: (l.size ?? 10) * 1.25 * k };
  });
  const shadow = 2 * k;
  const w = Math.ceil(Math.max(...metrics.map((m) => m.w)) + padX * 2 + shadow * 2);
  const h = Math.ceil(metrics.reduce((s, m) => s + m.h, 0) + padY * 2 + shadow * 2);
  const cv = document.createElement('canvas');
  cv.width = w;
  cv.height = h;
  const g = cv.getContext('2d')!;
  const x0 = shadow, y0 = shadow, bw = w - shadow * 2, bh = h - shadow * 2;
  const path = () => {
    g.beginPath();
    g.roundRect(x0 + k * 0.5, y0 + k * 0.5, bw - k, bh - k, radius);
  };
  // shadow-sm
  g.save();
  g.shadowColor = 'rgba(21,18,43,0.10)';
  g.shadowBlur = 2 * k;
  g.shadowOffsetY = 1 * k;
  path();
  g.fillStyle = spec.dark ? 'rgba(21,18,43,0.9)' : 'rgba(255,255,255,0.9)';
  g.fill();
  g.restore();
  path();
  g.lineWidth = k;
  g.strokeStyle = spec.dark ? 'rgba(110,75,255,0.4)' : 'rgba(110,75,255,0.2)';
  g.stroke();
  let y = y0 + padY;
  spec.lines.forEach((l, i) => {
    g.font = fontOf(l);
    g.fillStyle = l.color ?? (spec.dark ? C.white : 'rgba(21,18,43,0.7)');
    g.textBaseline = 'middle';
    g.fillText(l.text, x0 + padX, y + metrics[i].h / 2 + 0.5 * k);
    y += metrics[i].h;
  });
  const tex = new THREE.CanvasTexture(cv);
  tex.colorSpace = THREE.SRGBColorSpace;
  tex.premultiplyAlpha = true;
  tex.generateMipmaps = true;
  tex.minFilter = THREE.LinearMipmapLinearFilter;
  tex.anisotropy = 4;
  return { tex, w: w / SS, h: h / SS };
}

const _q = new THREE.PerspectiveCamera();

/**
 * A label at `position`, facing the camera, `scale` x the website's CSS pixel size (2 reads well at 1080p). `offsetPx` shifts it on screen
 * (the site centres the label on its anchor). Hidden when the anchor is behind the camera.
 */
export const Tag3D: React.FC<{ spec: TagSpec; position: Vec3; scale?: number; offsetPx?: [number, number]; opacity?: number }> = ({
  spec,
  position,
  scale = 2,
  offsetPx = [0, 0],
  opacity = 1,
}) => {
  const view = useView();
  const key = JSON.stringify(spec);
  const drawn = useMemo(() => drawTag(spec, scale), [key, scale]); // eslint-disable-line react-hooks/exhaustive-deps
  useEffect(() => () => drawn.tex.dispose(), [drawn]);
  const mat = useMemo(
    () =>
      // premultiplied bitmap (no dark fringe at the rounded edges) blended as premultiplied; colour = opacity scales rgb with alpha
      new THREE.MeshBasicMaterial({
        map: drawn.tex,
        transparent: true,
        depthTest: false,
        depthWrite: false,
        toneMapped: false,
        fog: false,
        blending: THREE.CustomBlending,
        blendSrc: THREE.OneFactor,
        blendDst: THREE.OneMinusSrcAlphaFactor,
        blendSrcAlpha: THREE.OneFactor,
        blendDstAlpha: THREE.OneMinusSrcAlphaFactor,
      }),
    [drawn],
  );
  useEffect(() => () => mat.dispose(), [mat]);
  if (!view) return null;
  const depth = viewDepth(view.cam, position);
  if (depth <= 0.05 || opacity <= 0) return null;
  mat.opacity = opacity;
  mat.color.setScalar(opacity);
  applyCam(_q, view.cam, view.width / view.height);
  const worldPerPx = (2 * depth * Math.tan((view.cam.fov * DEG) / 2)) / view.height;
  const right = new THREE.Vector3(1, 0, 0).applyQuaternion(_q.quaternion);
  const up = new THREE.Vector3(0, 1, 0).applyQuaternion(_q.quaternion);
  const p = new THREE.Vector3(...position).addScaledVector(right, offsetPx[0] * worldPerPx).addScaledVector(up, -offsetPx[1] * worldPerPx);
  return (
    <mesh position={p} quaternion={_q.quaternion.clone()} scale={[drawn.w * worldPerPx, drawn.h * worldPerPx, 1]} material={mat} renderOrder={1000}>
      <planeGeometry args={[1, 1]} />
    </mesh>
  );
};
