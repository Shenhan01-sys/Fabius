// Jembatan adegan 3D <-> label DOM (P158). Label = tombol DOM biasa di Floor (satu root React, terbaca pembaca layar); adegan mendaftarkan titik
// jangkar 3D + fungsi pembuka modal (rect monitor dihitung di dalam kanvas); `sync` menggeser label ke posisi jangkar tiap frame tanpa render ulang.

import * as THREE from "three";

export class Bridge {
  private anchors = new Map<string, THREE.Object3D>();
  private els = new Map<string, HTMLElement>();
  private openers = new Map<string, () => void>();
  private elRefs = new Map<string, (el: HTMLElement | null) => void>();
  private anchorRefs = new Map<string, (o: THREE.Object3D | null) => void>();
  private v = new THREE.Vector3();

  /** callback ref stabil untuk elemen label DOM `key` */
  el(key: string) {
    let f = this.elRefs.get(key);
    if (!f) {
      f = (el) => (el ? this.els.set(key, el) : this.els.delete(key));
      this.elRefs.set(key, f);
    }
    return f;
  }

  /** callback ref stabil untuk titik jangkar 3D `key` */
  anchor(key: string) {
    let f = this.anchorRefs.get(key);
    if (!f) {
      f = (o) => (o ? this.anchors.set(key, o) : this.anchors.delete(key));
      this.anchorRefs.set(key, f);
    }
    return f;
  }

  setOpen(key: string, fn: (() => void) | null) {
    if (fn) this.openers.set(key, fn);
    else this.openers.delete(key);
  }

  open(key: string) {
    this.openers.get(key)?.();
  }

  sync(camera: THREE.Camera, width: number, height: number) {
    for (const [k, o] of this.anchors) {
      const el = this.els.get(k);
      if (!el) continue;
      o.getWorldPosition(this.v).project(camera);
      el.style.transform = `translate3d(${((this.v.x + 1) / 2) * width}px, ${((1 - this.v.y) / 2) * height}px, 0) translate(-50%, -50%)`;
      el.style.visibility = "visible";
    }
  }
}
