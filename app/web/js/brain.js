// The brain map: every neuron of the scan as a point, in one of three
// switchable layouts (anatomy, flow, groups), coloured by a chosen attribute,
// with the run's spikes drawn as a decaying trace on the cells that fired.
import * as THREE from "three";
import { OrbitControls } from "three/addons/controls/OrbitControls.js";

const TAU_MS = 30;           // display decay of a spike's glow (not a model constant)
const WINDOW_MS = 150;
const FLOW_DY = 70;          // flow layout: height of one traversal layer (display units)
const FLOW_CAP = 9;          // deeper layers are drawn at this one

// colour of each superclass family; members of a family vary in lightness
const FAMILY = [
  [/^ol_|^visual/, 0x4c78c8], [/^cb_sensory|^sensory|^vnc_sensory|^ol_sensory/, 0xd9a400],
  [/^cb_/, 0x3f9f5f], [/^descending/, 0x9b59b6], [/^ascending/, 0xc0392b],
  [/^vnc_motor|^cb_motor/, 0xe8590c], [/^vnc_|^efferent/, 0xd98a3a], [/./, 0x8c8c8c],
];
const NT = {
  acetylcholine: 0xe0a000, gaba: 0x2f6fd0, glutamate: 0x30a050, dopamine: 0xc03030,
  serotonin: 0x9040c0, octopamine: 0xd06090, histamine: 0x20a0a0, unclear: 0x909090, "": 0xb0b0b0,
};
const BASIS = [0x2a7f62, 0x52b8a0, 0xe0a030, 0xd05030, 0xd000d0];
const SIDE = { L: 0x3070d0, R: 0xd04030, M: 0x40a040, "": 0xa0a0a0 };

function superclassColour(name) {
  for (const [re, c] of FAMILY) if (re.test(name)) return c;
  return 0x8c8c8c;
}

const VERT = `
attribute vec3 color; attribute float act; attribute float vis;
uniform float uSize, uScale, uDim, uActOn; uniform vec3 uHot;
varying vec3 vColor; varying float vAlpha;
void main() {
  vec4 mv = modelViewMatrix * vec4(position, 1.0);
  gl_Position = projectionMatrix * mv;
  float a = clamp(act, 0.0, 1.0) * uActOn;
  gl_PointSize = vis * uSize * (1.0 + 2.0 * a) * uScale / max(-mv.z, 1e-3);
  vColor = mix(color, uHot, a);
  vAlpha = vis * mix(mix(1.0, uDim, uActOn), 1.0, a);
}`;
const FRAG = `
varying vec3 vColor; varying float vAlpha;
void main() {
  vec2 d = gl_PointCoord - 0.5;
  if (dot(d, d) > 0.25 || vAlpha <= 0.0) discard;
  gl_FragColor = vec4(vColor, vAlpha);
}`;

export class BrainView {
  constructor(canvas, atlas) {
    this.canvas = canvas;
    this.atlas = atlas;
    const n = atlas.n;
    this.renderer = new THREE.WebGLRenderer({ canvas, antialias: true, preserveDrawingBuffer: true });
    this.renderer.setPixelRatio(Math.min(devicePixelRatio, 2));
    this.scene = new THREE.Scene();
    this.camera = new THREE.PerspectiveCamera(30, 1, 1, 20000);
    this.controls = new OrbitControls(this.camera, canvas);
    this.controls.enableDamping = false;
    this.layouts = { anatomy: this._anatomy(), flow: this._flow(), groups: this._groups() };
    this.layoutName = "anatomy";
    this.pos = this.layouts.anatomy.slice();
    const g = new THREE.BufferGeometry();
    this.posAttr = new THREE.BufferAttribute(this.pos, 3);
    this.colAttr = new THREE.BufferAttribute(new Float32Array(n * 3), 3);
    this.actAttr = new THREE.BufferAttribute(new Float32Array(n), 1);
    this.visAttr = new THREE.BufferAttribute(new Float32Array(n).fill(1), 1);
    g.setAttribute("position", this.posAttr);
    g.setAttribute("color", this.colAttr);
    g.setAttribute("act", this.actAttr);
    g.setAttribute("vis", this.visAttr);
    this.uniforms = {
      uSize: { value: 2.2 }, uScale: { value: 400 }, uDim: { value: 0.2 },
      uActOn: { value: 1 }, uHot: { value: new THREE.Color(0xff5a1f) },
    };
    this.points = new THREE.Points(g, new THREE.ShaderMaterial({
      vertexShader: VERT, fragmentShader: FRAG, uniforms: this.uniforms,
      transparent: true, depthWrite: false,
    }));
    this.points.frustumCulled = false;
    this.scene.add(this.points);
    this.order = new Uint32Array(n);
    g.setIndex(new THREE.BufferAttribute(this.order, 1));
    this.controls.addEventListener("end", () => this.sortByDepth());
    // highlighted set (selected neuron, its type, stimulated cells) drawn on top
    this.hiGeo = new THREE.BufferGeometry();
    this.hi = new THREE.Points(this.hiGeo, new THREE.PointsMaterial({
      size: 9, sizeAttenuation: false, color: 0x111111, transparent: true, opacity: 0.95, depthTest: false,
    }));
    this.hi.renderOrder = 2;
    this.scene.add(this.hi);
    this.lines = new THREE.LineSegments(new THREE.BufferGeometry(), new THREE.LineBasicMaterial({
      vertexColors: true, transparent: true, opacity: 0.7, depthTest: false,
    }));
    this.lines.renderOrder = 1;
    this.scene.add(this.lines);
    this.hidden = new Set();          // legend categories switched off
    this.filters = { inModel: false, measuredOnly: false };
    this.colourBy = "superclass";
    this.highlight = [];
    this.partners = null;
    this.rowToAtlas = null;
    this.act = this.actAttr.array;
    this.setColour("superclass");
    this.frame(true);
  }

  setTheme(dark) {
    this.dark = dark;
    this.scene.background = new THREE.Color(dark ? 0x15171a : 0xf7f6f2);
    this.hi.material.color.set(dark ? 0xffffff : 0x111111);
    this.uniforms.uHot.value.set(dark ? 0xffb020 : 0xff4a10);
    this.uniforms.uDim.value = dark ? 0.3 : 0.2;
  }

  bindRecording(rec) {
    this.rec = rec;
    const rows = rec.rowBodyId, map = new Int32Array(rows.length).fill(-1);
    let miss = 0;
    for (let r = 0; r < rows.length; r++) {
      const i = this.atlas.index.get(rows[r]);
      if (i === undefined) miss++; else map[r] = i;
    }
    this.rowToAtlas = map;
    this.unjoined = miss;
    const inRun = new Uint8Array(this.atlas.n);
    for (const i of map) if (i >= 0) inRun[i] = 1;
    this.inRun = inRun;
    this.applyFilters();
  }

  // ---- layouts --------------------------------------------------------------
  // anatomy: dataset frame (um), centred; screen up = dorsal (-y), camera in front (-z)
  _anatomy() {
    const p = this.atlas.arr.pos, n = this.atlas.n, out = new Float32Array(n * 3);
    const c = [0, 0, 0];
    for (let i = 0; i < n; i++) for (let k = 0; k < 3; k++) c[k] += p[i * 3 + k] / n;
    this.centre = c;
    for (let i = 0; i < n; i++) {
      out[i * 3] = p[i * 3] - c[0];
      out[i * 3 + 1] = -(p[i * 3 + 1] - c[1]);
      out[i * 3 + 2] = -(p[i * 3 + 2] - c[2]);
    }
    return out;
  }

  // flow: lateral position kept, height = traversal layer from the sensory periphery
  _flow() {
    const p = this.atlas.arr.pos, L = this.atlas.arr.layer, n = this.atlas.n, out = new Float32Array(n * 3);
    const c = this.centre;
    let maxL = 0;
    for (let i = 0; i < n; i++) if (L[i] > maxL) maxL = L[i];
    this.flowMax = maxL;
    const top = 5 * FLOW_DY;
    for (let i = 0; i < n; i++) {
      const reached = L[i] >= 0;
      out[i * 3] = p[i * 3] - c[0];
      out[i * 3 + 1] = reached ? top - Math.min(L[i], FLOW_CAP) * FLOW_DY : top - (FLOW_CAP + 1.5) * FLOW_DY;
      out[i * 3 + 2] = -(p[i * 3 + 2] - c[2]) * 0.3;
    }
    return out;
  }

  // groups: one block per superclass, cells sorted by type within a block
  _groups() {
    const a = this.atlas, n = a.n, sc = a.arr.superclass, ty = a.arr.type, out = new Float32Array(n * 3);
    const order = Array.from({ length: n }, (_, i) => i);
    order.sort((x, y) => sc[x] - sc[y] || ty[x] - ty[y] || x - y);
    const counts = new Map();
    for (let i = 0; i < n; i++) counts.set(sc[i], (counts.get(sc[i]) || 0) + 1);
    const step = 2.2, rowW = 1400, gap = 30;
    let bx = -rowW / 2, by = 400, rowH = 0, k = 0;
    this.groupBoxes = [];
    for (const code of [...counts.keys()].sort((x, y) => counts.get(y) - counts.get(x))) {
      const m = counts.get(code), cols = Math.max(4, Math.ceil(Math.sqrt(m * 1.6)));
      const w = cols * step, h = Math.ceil(m / cols) * step;
      if (bx + w > rowW / 2) { bx = -rowW / 2; by -= rowH + gap; rowH = 0; }
      this.groupBoxes.push({ code, x: bx, y: by, w, h });
      let j = 0;
      for (const i of order) {
        if (sc[i] !== code) continue;
        out[i * 3] = bx + (j % cols) * step;
        out[i * 3 + 1] = by - Math.floor(j / cols) * step;
        out[i * 3 + 2] = 0;
        j++;
      }
      bx += w + gap; rowH = Math.max(rowH, h); k++;
    }
    return out;
  }

  setLayout(name) {
    if (!this.layouts[name] || name === this.layoutName) return;
    this.layoutName = name;
    this._tween = { from: this.pos.slice(), to: this.layouts[name], t0: performance.now() };
    this.frame(false, this.layouts[name]);
  }

  // ---- colour and visibility -------------------------------------------------
  category(i) {
    const a = this.atlas;
    switch (this.colourBy) {
      case "superclass": return a.superclass(i) || "(none)";
      case "nt": return a.vocab.nt[a.arr.nt[i]] || "(none)";
      case "basis": return a.vocab.pos_basis[a.arr.pos_basis[i]];
      case "side": return a.side(i) || "(none)";
      case "model": return a.arr.in_model[i] ? "in the model (status policy)" : "not in the model";
      case "layer": { const L = a.arr.layer[i]; return L < 0 ? "not reached" : `layer ${Math.min(8, Math.floor(L))}${L >= 8 ? "+" : ""}`; }
    }
    return "";
  }

  colourOf(i) {
    const a = this.atlas;
    switch (this.colourBy) {
      case "superclass": return superclassColour(a.superclass(i));
      case "nt": return NT[a.vocab.nt[a.arr.nt[i]]] ?? 0xb0b0b0;
      case "basis": return BASIS[a.arr.pos_basis[i]];
      case "side": return SIDE[a.side(i)] ?? 0xa0a0a0;
      case "model": return a.arr.in_model[i] ? 0x2a7f62 : 0xd05030;
      case "layer": {
        const L = a.arr.layer[i];
        if (L < 0) return 0xb0b0b0;
        return new THREE.Color().setHSL(0.62 - 0.62 * Math.min(1, L / 8), 0.7, 0.45).getHex();
      }
    }
    return 0x888888;
  }

  setColour(mode) {
    this.colourBy = mode;
    this.hidden.clear();
    const n = this.atlas.n, col = this.colAttr.array, c = new THREE.Color();
    const legend = new Map();
    for (let i = 0; i < n; i++) {
      const hex = this.colourOf(i);
      c.setHex(hex);
      col[i * 3] = c.r; col[i * 3 + 1] = c.g; col[i * 3 + 2] = c.b;
      const k = this.category(i);
      const e = legend.get(k) || { name: k, colour: hex, n: 0 };
      e.n++;
      legend.set(k, e);
    }
    this.legend = [...legend.values()].sort((x, y) => mode === "layer" ? x.name.localeCompare(y.name, undefined, { numeric: true }) : y.n - x.n);
    this.colAttr.needsUpdate = true;
    this.applyFilters();
  }

  toggleCategory(name) {
    if (this.hidden.has(name)) this.hidden.delete(name); else this.hidden.add(name);
    this.applyFilters();
  }

  applyFilters() {
    const a = this.atlas, vis = this.visAttr.array, n = a.n;
    let shown = 0;
    for (let i = 0; i < n; i++) {
      let v = 1;
      if (this.filters.inModel && !a.arr.in_model[i]) v = 0;
      if (this.filters.measuredOnly && a.arr.pos_basis[i] > 1) v = 0;
      if (v && this.hidden.size && this.hidden.has(this.category(i))) v = 0;
      vis[i] = v;
      shown += v;
    }
    this.shown = shown;
    this.visAttr.needsUpdate = true;
  }

  // ---- activity ----------------------------------------------------------------
  setTime(t) {
    const act = this.act, rec = this.rec;
    act.fill(0);
    if (rec && this.rowToAtlas) {
      const b0 = Math.max(0, Math.floor((t - WINDOW_MS) / rec.binMs));
      const b1 = Math.min(rec.nBins - 1, Math.floor(t / rec.binMs));
      const P = rec.spikePtr, R = rec.spikeRow, S = rec.spikeSub, map = this.rowToAtlas;
      for (let b = b0; b <= b1; b++) {
        for (let k = P[b]; k < P[b + 1]; k++) {
          const ts = b * rec.binMs + S[k] * rec.ts;
          if (ts > t) continue;
          const i = map[R[k]];
          if (i >= 0) act[i] += Math.exp(-(t - ts) / TAU_MS);
        }
      }
    }
    this.actAttr.needsUpdate = true;
  }

  setActivityShown(on) { this.uniforms.uActOn.value = on ? 1 : 0; }

  // ---- highlight and partners ------------------------------------------------
  setHighlight(list) {
    this.highlight = Array.from(list);
    this._updateHighlight();
  }

  _updateHighlight() {
    const arr = new Float32Array(this.highlight.length * 3);
    this.highlight.forEach((i, k) => arr.set(this.pos.subarray(i * 3, i * 3 + 3), k * 3));
    this.hiGeo.setAttribute("position", new THREE.BufferAttribute(arr, 3));
    this.hiGeo.computeBoundingSphere();
    this.hi.material.size = this.highlight.length > 1 ? 5 : 10;
  }

  setPartners(i, edges, top = 40) {
    this.partners = i === null ? null : { i, out: edges.out.slice(0, top), in: edges.in.slice(0, top) };
    this._updateLines();
  }

  _updateLines() {
    const P = this.partners;
    if (!P) { this.lines.geometry = new THREE.BufferGeometry(); return; }
    const segs = [...P.out.map(e => [e, 0]), ...P.in.map(e => [e, 1])];
    const pos = new Float32Array(segs.length * 6), col = new Float32Array(segs.length * 6);
    const wmax = Math.max(1, ...segs.map(s => s[0][1]));
    const cOut = new THREE.Color(0xe0501a), cIn = new THREE.Color(0x2070d0);
    segs.forEach(([[j, w], dir], k) => {
      pos.set(this.pos.subarray(P.i * 3, P.i * 3 + 3), k * 6);
      pos.set(this.pos.subarray(j * 3, j * 3 + 3), k * 6 + 3);
      const c = dir ? cIn : cOut, s = 0.35 + 0.65 * Math.sqrt(w / wmax);
      for (const o of [0, 3]) { col[k * 6 + o] = c.r * s + (1 - s) * (this.dark ? 0.1 : 0.95); col[k * 6 + o + 1] = c.g * s + (1 - s) * (this.dark ? 0.1 : 0.95); col[k * 6 + o + 2] = c.b * s + (1 - s) * (this.dark ? 0.1 : 0.95); }
    });
    const g = new THREE.BufferGeometry();
    g.setAttribute("position", new THREE.BufferAttribute(pos, 3));
    g.setAttribute("color", new THREE.BufferAttribute(col, 3));
    this.lines.geometry.dispose();
    this.lines.geometry = g;
  }

  // painter's order for the translucent points: far first, along the view direction
  sortByDepth() {
    const n = this.atlas.n, P = this.pos, d = new THREE.Vector3();
    this.camera.getWorldDirection(d);
    const key = new Float32Array(n);
    for (let i = 0; i < n; i++) key[i] = -(P[i * 3] * d.x + P[i * 3 + 1] * d.y + P[i * 3 + 2] * d.z);
    const idx = Array.from({ length: n }, (_, i) => i).sort((a, b) => key[a] - key[b]);
    this.order.set(idx);
    this.points.geometry.index.needsUpdate = true;
  }

  // ---- camera and picking -------------------------------------------------------
  frame(reset, P = this.pos) {
    const n = this.atlas.n;
    const lo = [Infinity, Infinity, Infinity], hi = [-Infinity, -Infinity, -Infinity];
    for (let i = 0; i < n; i++) for (let k = 0; k < 3; k++) {
      const v = P[i * 3 + k]; if (v < lo[k]) lo[k] = v; if (v > hi[k]) hi[k] = v;
    }
    const c = lo.map((v, k) => (v + hi[k]) / 2);
    const aspect = this.camera.aspect || 1.5;
    const span = Math.max((hi[0] - lo[0]) / aspect, hi[1] - lo[1]);
    const dist = span / (2 * Math.tan((this.camera.fov * Math.PI) / 360)) * 1.3;
    c[0] += 0.12 * (hi[0] - lo[0]);      // shift content left of the legend
    c[1] += 0.08 * (hi[1] - lo[1]);      // and below the toolbar
    this.controls.target.set(c[0], c[1], c[2]);
    this.camera.position.set(c[0], c[1], c[2] + dist + (hi[2] - lo[2]) / 2);
    this.camera.up.set(0, 1, 0);
    this.camera.near = dist / 50; this.camera.far = dist * 20;
    this.camera.updateProjectionMatrix();
    this.uniforms.uScale.value = dist * 0.9;
    this.sortByDepth();
  }

  pick(px, py, radius = 8) {
    const w = this.canvas.clientWidth, h = this.canvas.clientHeight;
    this.camera.updateMatrixWorld();
    const M = new THREE.Matrix4().multiplyMatrices(this.camera.projectionMatrix, this.camera.matrixWorldInverse).elements;
    const P = this.pos, vis = this.visAttr.array, n = this.atlas.n;
    let best = -1, bd = radius * radius, bz = Infinity;
    for (let i = 0; i < n; i++) {
      if (!vis[i]) continue;
      const x = P[i * 3], y = P[i * 3 + 1], z = P[i * 3 + 2];
      const cw = M[3] * x + M[7] * y + M[11] * z + M[15];
      if (cw <= 0) continue;
      const sx = ((M[0] * x + M[4] * y + M[8] * z + M[12]) / cw * 0.5 + 0.5) * w;
      const sy = (0.5 - (M[1] * x + M[5] * y + M[9] * z + M[13]) / cw * 0.5) * h;
      const d = (sx - px) ** 2 + (sy - py) ** 2;
      if (d < bd || (d === bd && cw < bz)) { best = i; bd = d; bz = cw; }
    }
    return best;
  }

  // screen positions of the group block labels (groups layout only)
  groupLabels() {
    if (this.layoutName !== "groups" || this._tween) return [];
    const w = this.canvas.clientWidth, h = this.canvas.clientHeight, v = new THREE.Vector3();
    return this.groupBoxes.filter(b => b.w > 40).map(b => {
      v.set(b.x, b.y + 4, 0).project(this.camera);
      return { text: this.atlas.vocab.superclass[b.code] || "(none)", x: (v.x * 0.5 + 0.5) * w, y: (0.5 - v.y * 0.5) * h };
    });
  }

  resize() {
    const w = this.canvas.clientWidth, h = this.canvas.clientHeight;
    if (!w || !h) return;
    this.renderer.setSize(w, h, false);
    this.camera.aspect = w / h;
    this.camera.updateProjectionMatrix();
  }

  render() {
    if (this._tween) {
      const u = Math.min(1, (performance.now() - this._tween.t0) / 600), s = u * u * (3 - 2 * u);
      const { from, to } = this._tween;
      for (let k = 0; k < this.pos.length; k++) this.pos[k] = from[k] + (to[k] - from[k]) * s;
      this.posAttr.needsUpdate = true;
      this._updateHighlight();
      this._updateLines();
      if (u >= 1) { this._tween = null; this.sortByDepth(); }
    }
    this.controls.update();
    this.renderer.render(this.scene, this.camera);
  }
}
