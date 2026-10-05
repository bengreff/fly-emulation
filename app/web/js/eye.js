// Fly's-eye view (M3, first cut): each eye's 721 ommatidia as the hex mosaic, shaded by
// the readout the photoreceptors were driven by at the current time (recorded eye
// frames, 2 eyes x 721 x yellow/pale, one channel filled). Geometry and assignments
// come from app/build/eye.py (flyemu-eye/1).
import { fetchJSON } from "./io.js";
import { esc } from "./inspector.js";

const N_EYE = 2;

export class EyePanel {
  constructor(el, { onSelect, onHighlight }) {
    this.el = el; this.onSelect = onSelect; this.onHighlight = onHighlight;
    this.frame = -2; this.pick = null;
  }

  async load(url, rec, atlas) {
    this.rec = rec; this.atlas = atlas;
    try { this.g = await fetchJSON(url); } catch { this.g = null; }
    if (!this.g) { this.el.innerHTML = `<div class="empty">No eye geometry for this body (run app/build/eye.py).</div>`; return; }
    const n = this.g.n_ommatidia, x = this.g.centroid.x, y = this.g.centroid.y;
    this.n = n;
    // hex spacing: the median nearest-neighbour distance between centroids
    const d = [];
    for (let i = 0; i < n; i += 7) {
      let best = Infinity;
      for (let j = 0; j < n; j++) if (j !== i) best = Math.min(best, Math.hypot(x[i] - x[j], y[i] - y[j]));
      d.push(best);
    }
    d.sort((a, b) => a - b);
    this.spacing = d[d.length >> 1];
    this.cells = {};               // eye index -> ommatidium -> [{bodyId, type}]
    ["L", "R"].forEach((k, e) => {
      const p = this.g.photoreceptors[k], m = new Map();
      if (p) p.ommatidium.forEach((o, j) => { if (!m.has(o)) m.set(o, []); m.get(o).push({ bodyId: p.bodyId[j], type: p.type[j] }); });
      this.cells[e] = m;
    });
    const nf = rec.eyeStep ? rec.eyeStep.length : 0;
    this.el.innerHTML = `<h2>Fly's-eye view</h2>
      <div class="sub">${nf ? `${nf} eye frames in this run` : "no eye frames in this run"}; 721 ommatidia per eye</div>
      ${nf ? "" : `<div class="warnline">${rec.manifest.preparation && rec.manifest.preparation.coupling === "brain_only"
        ? "Brain only: the eyes were not rendered, so the photoreceptors received no light input." : "This recording holds no eye readouts."}</div>`}
      <label><input type="checkbox" id="eye-pale"> ring pale ommatidia</label>
      <canvas id="eye-canvas"></canvas>
      <div class="dim">Shade: the luminance each ommatidium's photoreceptors were driven by at this time (0 to 1, the renderer's units; the white sky reaches 1, the renderer's ceiling). Positions: centroid of each ommatidium's pixels in flygym's eye map <span class="chip inferred">derived</span>. Pale/yellow: majority of the connectome's R7/R8 subtypes per ommatidium, else flygym's mask <span class="chip inferred">derived</span>. Eyes as rendered (flygym's image frame).</div>
      <div id="eye-pick"></div>`;
    this.canvas = this.el.querySelector("#eye-canvas");
    this.el.querySelector("#eye-pale").onchange = () => { this.frame = -2; };
    this.canvas.onclick = e => this.click(e);
    this.el.querySelector("#eye-pick").onclick = e => {
      const a = e.target.closest("[data-i]"); if (a) this.onSelect(Number(a.dataset.i));
      const h = e.target.closest("[data-all]"); if (h) this.onHighlight(this.pickIds());
    };
  }

  layout() {
    const w = Math.max(200, this.el.clientWidth - 8), img = this.g.image;
    const s = (w / 2 - 12) / img.cols;           // pixels of canvas per image pixel
    return { w, h: Math.ceil(img.rows * s) + 18, s, ox: [0, w / 2 + 6] };
  }

  draw(t) {
    if (!this.g || !this.canvas || this.el.hidden) return;
    const rec = this.rec, nf = rec.eyeStep ? rec.eyeStep.length : 0;
    const f = nf ? rec.eyeAt(t) : -1;
    const L = this.layout();
    if (f === this.frame && this.w === L.w) return;
    this.frame = f; this.w = L.w;
    const c = this.canvas, dpr = devicePixelRatio || 1;
    c.style.width = `${L.w}px`; c.style.height = `${L.h}px`;
    c.width = L.w * dpr; c.height = L.h * dpr;
    const g = c.getContext("2d"); g.scale(dpr, dpr);
    const x = this.g.centroid.x, y = this.g.centroid.y, r = this.spacing * L.s * 0.55, n = this.n;
    const ring = this.el.querySelector("#eye-pale").checked;
    const dark = document.documentElement.dataset.theme === "dark";
    g.font = "11px sans-serif";
    for (let e = 0; e < N_EYE; e++) {
      g.fillStyle = dark ? "#ccc" : "#333";
      g.fillText(e ? "right eye" : "left eye", L.ox[e] + 2, 11);
      g.fillStyle = "#7f7f7f";                 // mid grey, so both the white sky and dark ground read
      g.fillRect(L.ox[e], 14, L.w / 2 - 6, L.h - 14);
      const pale = this.g.pale[e ? "right" : "left"];
      for (let o = 0; o < n; o++) {
        let v = null;
        if (f >= 0) {
          const k = ((f * N_EYE + e) * n + o) * 2;
          v = Math.max(rec.eye[k], rec.eye[k + 1]);
        }
        const cx = L.ox[e] + x[o] * L.s, cy = 16 + y[o] * L.s;
        g.beginPath();
        for (let a = 0; a < 6; a++) {
          const th = Math.PI / 6 + a * Math.PI / 3;
          g[a ? "lineTo" : "moveTo"](cx + r * Math.cos(th), cy + r * Math.sin(th));
        }
        g.closePath();
        g.fillStyle = v === null ? (dark ? "#333" : "#ddd") : `rgb(${v},${v},${v})`;
        g.fill();
        if (ring && pale[o]) { g.strokeStyle = "#a050e0"; g.lineWidth = 1; g.stroke(); }
      }
      if (this.pick && this.pick.e === e) {          // the picked ommatidium, drawn last so it sits on top
        const o = this.pick.o, cx = L.ox[e] + x[o] * L.s, cy = 16 + y[o] * L.s;
        g.beginPath(); g.arc(cx, cy, r * 1.8, 0, 2 * Math.PI);
        g.strokeStyle = "#ff2020"; g.lineWidth = 2.5; g.stroke();
      }
    }
  }

  click(ev) {
    const L = this.layout(), b = this.canvas.getBoundingClientRect();
    const px = ev.clientX - b.left, py = ev.clientY - b.top;
    const e = px < L.w / 2 ? 0 : 1;
    const ix = (px - L.ox[e]) / L.s, iy = (py - 16) / L.s;
    const x = this.g.centroid.x, y = this.g.centroid.y;
    let best = -1, bd = Infinity;
    for (let o = 0; o < this.n; o++) { const d = Math.hypot(x[o] - ix, y[o] - iy); if (d < bd) { bd = d; best = o; } }
    if (bd > this.spacing) return;
    this.pick = { e, o: best };
    this.frame = -2;
    const cells = this.cells[e].get(best) || [];
    this.el.querySelector("#eye-pick").innerHTML = `<h3>${e ? "Right" : "Left"} eye, ommatidium ${best}</h3>
      <div>${this.g.pale[e ? "right" : "left"][best] ? "pale" : "yellow"}; ${this.g.pixels[best]} render pixels</div>
      ${cells.length ? `<div>${cells.length} photoreceptor cells assigned to it <span class="chip inferred">derived topology, inferred alignment</span> <a href="#" data-all>highlight all</a></div>
        <table>${cells.map(c => { const i = this.atlas.index.get(c.bodyId);
          return `<tr${i === undefined ? "" : ` class="link" data-i="${i}"`}><td>${c.bodyId}</td><td>${esc(c.type)}</td></tr>`; }).join("")}</table>`
        : `<div class="dim">No photoreceptor cell is assigned to this ommatidium (the derived assignment does not cover every ommatidium).</div>`}`;
    this.onHighlight(this.pickIds());
  }

  pickIds() {
    if (!this.pick) return [];
    return (this.cells[this.pick.e].get(this.pick.o) || []).map(c => this.atlas.index.get(c.bodyId)).filter(i => i !== undefined);
  }
}
