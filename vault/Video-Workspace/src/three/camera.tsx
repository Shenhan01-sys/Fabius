// Camera as data. A scene never owns its camera: it receives a CameraDesc every frame and <CameraRig> copies it onto R3F's default camera in
// a layout effect (layout effects run before @remotion/three's ManualFrameRenderer calls advance(), so the frame is drawn with this camera).
// Helpers build descriptions (orbitCam, telephoto) and fly between them (camPath: C1 Hermite spline in orbit space).

import { useThree } from '@react-three/fiber';
import React, { createContext, useContext, useLayoutEffect } from 'react';
import * as THREE from 'three';
import { clamp, DEG, type Vec3 } from './util';

/** Perspective camera. fov = vertical field of view in degrees; roll in degrees (positive = camera rolls counter-clockwise). */
export type CameraDesc = { position: Vec3; target: Vec3; fov: number; roll?: number; near?: number; far?: number };
/** Orbit parameters around `target`: azimuth 0 = camera on +z looking toward -z, positive azimuth swings the camera toward +x. */
export type Orbit = { az: number; el: number; dist: number; target: Vec3; fov: number; roll?: number };

export function orbitCam(azimuthDeg: number, elevationDeg: number, distance: number, target: Vec3 = [0, 0, 0], fov = 30, roll = 0): CameraDesc {
  const el = clamp(elevationDeg, -89.9, 89.9) * DEG;
  const az = azimuthDeg * DEG;
  return {
    position: [target[0] + distance * Math.cos(el) * Math.sin(az), target[1] + distance * Math.sin(el), target[2] + distance * Math.cos(el) * Math.cos(az)],
    target: [target[0], target[1], target[2]],
    fov,
    roll,
  };
}

export const fromOrbit = (o: Orbit): CameraDesc => orbitCam(o.az, o.el, o.dist, o.target, o.fov, o.roll ?? 0);

export function toOrbit(c: CameraDesc): Orbit {
  const dx = c.position[0] - c.target[0];
  const dy = c.position[1] - c.target[1];
  const dz = c.position[2] - c.target[2];
  const dist = Math.max(1e-6, Math.hypot(dx, dy, dz));
  return { az: Math.atan2(dx, dz) / DEG, el: Math.asin(clamp(dy / dist, -1, 1)) / DEG, dist, target: [...c.target] as Vec3, fov: c.fov, roll: c.roll ?? 0 };
}

export const camDistance = (c: CameraDesc) => Math.hypot(c.position[0] - c.target[0], c.position[1] - c.target[1], c.position[2] - c.target[2]);
/** World-space height of the picture at the target's distance. */
export const viewHeight = (c: CameraDesc) => 2 * camDistance(c) * Math.tan((c.fov * DEG) / 2);

/**
 * Same direction and framing (vertical view height at the target), long lens. With fov ~4 deg this is visually the website's orthographic
 * camera, and flying from it to a normal lens (camPath interpolates distance and tan(fov/2) in log space) is a clean dolly-zoom.
 */
export function telephoto(cam: CameraDesc, height: number, fov = 4): CameraDesc {
  const o = toOrbit(cam);
  return fromOrbit({ ...o, fov, dist: height / (2 * Math.tan((fov * DEG) / 2)) });
}

/** Depth range scaled to the shot so long lenses keep depth precision (no z-fighting) and close-ups do not clip. */
export function nearFar(c: CameraDesc): { near: number; far: number } {
  const d = camDistance(c);
  return { near: c.near ?? clamp(d * 0.04, 0.02, 40), far: c.far ?? Math.max(80, d * 3 + 60) };
}

type PerspectiveWithManual = THREE.PerspectiveCamera & { manual?: boolean };

export function applyCam(camera: THREE.PerspectiveCamera, c: CameraDesc, aspect: number) {
  const { near, far } = nearFar(c);
  (camera as PerspectiveWithManual).manual = true; // R3F must not reset aspect/projection on resize; we own it
  camera.fov = c.fov;
  camera.aspect = aspect;
  camera.near = near;
  camera.far = far;
  camera.position.set(c.position[0], c.position[1], c.position[2]);
  camera.up.set(0, 1, 0);
  camera.lookAt(c.target[0], c.target[1], c.target[2]);
  if (c.roll) camera.rotateZ(c.roll * DEG);
  camera.updateProjectionMatrix();
  camera.updateMatrixWorld(true);
}

/** Current camera + output size, readable by anything inside a <Stage> (labels use it to face the camera at a constant pixel size). */
export type View = { cam: CameraDesc; width: number; height: number };
export const ViewContext = createContext<View | null>(null);
export const useView = () => useContext(ViewContext);

/** Copies `cam` onto R3F's default perspective camera on every commit. */
export const CameraRig: React.FC<{ cam: CameraDesc }> = ({ cam }) => {
  const camera = useThree((s) => s.camera);
  const width = useThree((s) => s.size.width);
  const height = useThree((s) => s.size.height);
  useLayoutEffect(() => {
    if (camera instanceof THREE.PerspectiveCamera) applyCam(camera, cam, width / Math.max(1, height));
  });
  return null;
};

// ---------------------------------------------------------------- projection for 2D callouts (pure, outside the canvas)

const _pc = new THREE.PerspectiveCamera();
const _v = new THREE.Vector3();

/** Pixel position of world point `p` for camera `cam` on a width x height frame (for 2D callouts that track 3D anchors). */
export function projectPoint(cam: CameraDesc, p: Vec3, width: number, height: number) {
  applyCam(_pc, cam, width / height);
  _v.set(p[0], p[1], p[2]).project(_pc);
  const x = ((_v.x + 1) / 2) * width;
  const y = ((1 - _v.y) / 2) * height;
  return { x, y, ndcZ: _v.z, inFront: _v.z > -1 && _v.z < 1, onScreen: _v.z > -1 && _v.z < 1 && x >= 0 && x <= width && y >= 0 && y <= height };
}

/** Distance from the camera plane to `p` along the view axis (world units). */
export function viewDepth(cam: CameraDesc, p: Vec3) {
  const f = new THREE.Vector3(cam.target[0] - cam.position[0], cam.target[1] - cam.position[1], cam.target[2] - cam.position[2]).normalize();
  return f.dot(new THREE.Vector3(p[0] - cam.position[0], p[1] - cam.position[1], p[2] - cam.position[2]));
}

// ---------------------------------------------------------------- flying the camera

export type CamKey = {
  /** time (seconds, same clock as the `t` you pass to camPath) */
  at: number;
  cam: CameraDesc | Orbit;
  /** stop at this key (zero velocity) instead of flowing through it */
  hold?: boolean;
};

const isOrbit = (c: CameraDesc | Orbit): c is Orbit => (c as Orbit).az !== undefined;

// interpolation vector: az, el, ln(dist), tx, ty, tz, ln(tan(fov/2)), roll
type K = [number, number, number, number, number, number, number, number];

function keyVec(c: CameraDesc | Orbit, prevAz: number | null): K {
  const o = isOrbit(c) ? c : toOrbit(c);
  let az = o.az;
  if (!isOrbit(c) && prevAz !== null) {
    // a CameraDesc carries no turn count: take the azimuth nearest to the previous key so the camera never spins the long way round
    while (az - prevAz > 180) az -= 360;
    while (az - prevAz < -180) az += 360;
  }
  return [az, o.el, Math.log(Math.max(1e-6, o.dist)), o.target[0], o.target[1], o.target[2], Math.log(Math.tan(((o.fov * DEG) / 2))), o.roll ?? 0];
}

/**
 * Camera at time t along keyframes: C1 Hermite (Catmull-Rom tangents over the key times) in orbit space, so orbits stay round, push-ins
 * feel even (log distance) and fov changes keep the target's framing when distance and fov move together. Holds before the first key and
 * after the last; ends and `hold` keys ease to a stop.
 */
export function camPath(keys: CamKey[], t: number): CameraDesc {
  if (!keys.length) throw new Error('camPath needs at least one key');
  const ks = [...keys].sort((a, b) => a.at - b.at);
  const vs: K[] = [];
  ks.forEach((k, i) => vs.push(keyVec(k.cam, i ? vs[i - 1][0] : null)));
  const out = (v: K): CameraDesc =>
    fromOrbit({ az: v[0], el: v[1], dist: Math.exp(v[2]), target: [v[3], v[4], v[5]], fov: (2 * Math.atan(Math.exp(v[6]))) / DEG, roll: v[7] });
  if (t <= ks[0].at || ks.length === 1) return out(vs[0]);
  const n = ks.length;
  if (t >= ks[n - 1].at) return out(vs[n - 1]);
  let i = 0;
  while (i < n - 2 && t > ks[i + 1].at) i++;
  const tan = (j: number): K => {
    if (j === 0 || j === n - 1 || ks[j].hold) return [0, 0, 0, 0, 0, 0, 0, 0];
    const dt = ks[j + 1].at - ks[j - 1].at;
    return vs[j].map((_, c) => (vs[j + 1][c] - vs[j - 1][c]) / dt) as K;
  };
  const h = ks[i + 1].at - ks[i].at;
  const s = (t - ks[i].at) / h;
  const s2 = s * s;
  const s3 = s2 * s;
  const h00 = 2 * s3 - 3 * s2 + 1;
  const h10 = s3 - 2 * s2 + s;
  const h01 = -2 * s3 + 3 * s2;
  const h11 = s3 - s2;
  const m0 = tan(i);
  const m1 = tan(i + 1);
  const v = vs[i].map((p0, c) => h00 * p0 + h10 * h * m0[c] + h01 * vs[i + 1][c] + h11 * h * m1[c]) as K;
  return out(v);
}

/** Linear blend of two cameras in orbit space (k = 0..1, unclamped; apply your own easing). */
export function lerpCam(a: CameraDesc | Orbit, b: CameraDesc | Orbit, k: number): CameraDesc {
  const va = keyVec(a, null);
  const vb = keyVec(b, va[0]);
  const v = va.map((x, c) => x + (vb[c] - x) * k) as K;
  return fromOrbit({ az: v[0], el: v[1], dist: Math.exp(v[2]), target: [v[3], v[4], v[5]], fov: (2 * Math.atan(Math.exp(v[6]))) / DEG, roll: v[7] });
}
