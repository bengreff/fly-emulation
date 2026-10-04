// Time traces under the views: stimulus, population rate by superclass, the
// motor-neuron raster, actuator torque, modulator levels, body height and the
// selected cell. One shared time axis; click or drag to seek, wheel to zoom.
const GUTTER = 168;
const RATE_BIN_MS = 5;

export class Traces {
  constructor(canvas, onSeek) {
    this.canvas = canvas;
    this.ctx = canvas.getContext("2d");
    this.onSeek = onSeek;
    this.view = null;
    this.sel = null;
    this.t = 0;
    let drag = false;
    const seek = e => {
      const r = canvas.getBoundingClientRect(), x = e.clientX - r.left;
      if (x < GUTTER) return;
      this.onSeek(this.xToT(x));
    };
    canvas.addEventListener("pointerdown", e => { drag = true; canvas.setPointerCapture(e.pointerId); seek(e); });
    canvas.addEventListener("pointermove", e => { if (drag) seek(e); });
    canvas.addEventListener("pointerup", () => { drag = false; });
    canvas.addEventListener("wheel", e => {
      e.preventDefault();
      const r = canvas.getBoundingClientRect(), x = e.clientX - r.left;
      const [a, b] = this.view, tc = x > GUTTER ? this.xToT(x) : (a + b) / 2;
      const k = Math.exp(e.deltaY * 0.0015), D = this.rec.duration;
      let na = tc - (tc - a) * k, nb = tc + (b - tc) * k;
      if (nb - na < 20) return;
      if (na < 0) { nb -= na; na = 0; }
      if (nb > D) { na -= nb - D; nb = D; }
      this.view = [Math.max(0, na), Math.min(D, nb)];
      this.redraw();
    }, { passive: false });
    canvas.addEventListener("dblclick", () => { this.view = [0, this.rec.duration]; this.redraw(); });
  }

  bind(rec, atlas, rowToAtlas, theme) {
    this.rec = rec; this.atlas = atlas; this.rowToAtlas = rowToAtlas;
    this.view = [0, rec.duration];
    this._prepare();
    this.setTheme(theme);
  }

  setTheme(dark) {
    this.dark = dark;
    this.col = dark
      ? { bg: "#15171a", fg: "#d8d6d0", dim: "#6b6e73", grid: "#2a2d31", hot: "#ffb020", cool: "#4aa3ff", clip: "#ff40ff", stim: "#ff6a3d" }
      : { bg: "#fbfaf7", fg: "#1d1f22", dim: "#8a8780", grid: "#e6e3dc", hot: "#e0501a", cool: "#2070d0", clip: "#c000c0", stim: "#e0501a" };
    if (this.rec) this.redraw();
  }

  _prepare() {
    const rec = this.rec, st = rec.static, a = this.atlas, map = this.rowToAtlas;
    // population rate by superclass, 5 ms bins
    const nB = Math.ceil(rec.duration / RATE_BIN_MS);
    const cells = new Map();
    for (let r = 0; r < map.length; r++) {
      const i = map[r]; if (i < 0) continue;
      const s = a.arr.superclass[i]; cells.set(s, (cells.get(s) || 0) + 1);
    }
    const supers = [...cells.entries()].filter(([, n]) => n >= 100).sort((x, y) => y[1] - x[1]).map(([s]) => s);
    const slot = new Map(supers.map((s, k) => [s, k]));
    const rate = supers.map(() => new Float32Array(nB));
    // motor raster
    const mn = st.mn_rows, mapped = st.mn_mapped, mnRank = new Map();
    const ordered = [...mn].map((r, k) => ({ r, m: mapped[k], k }))
      .sort((x, y) => (y.m - x.m) || x.k - y.k);
    ordered.forEach((o, k) => mnRank.set(o.r, k));
    this.mnMappedCount = ordered.filter(o => o.m).length;
    const mnT = [], mnY = [];
    const P = rec.spikePtr, R = rec.spikeRow, S = rec.spikeSub;
    for (let b = 0; b < rec.nBins; b++) {
      for (let k = P[b]; k < P[b + 1]; k++) {
        const row = R[k], t = b * rec.binMs + S[k] * rec.ts;
        const i = map[row];
        if (i >= 0) {
          const q = slot.get(a.arr.superclass[i]);
          if (q !== undefined) rate[q][Math.min(nB - 1, Math.floor(t / RATE_BIN_MS))]++;
        }
        const y = mnRank.get(row);
        if (y !== undefined) { mnT.push(t); mnY.push(y); }
      }
    }
    supers.forEach((s, q) => {
      const f = 1000 / (RATE_BIN_MS * cells.get(s));
      for (let k = 0; k < nB; k++) rate[q][k] *= f;     // Hz per cell
    });
    this.rates = { supers, rate, nB, cells };
    this.mn = { t: Float32Array.from(mnT), y: Uint16Array.from(mnY), n: ordered.length };
    // stimulus: build-time genotype (whole run) and timed events from the resolved protocol
    const res = (rec.manifest.protocol && rec.manifest.protocol.resolved) || { events: [], genotype: [] };
    this.events = [
      ...res.genotype.map(g => ({ label: g.label, t0: 0, t1: rec.duration, effector: g.effector, mv: g.mv, approx: g.approximation })),
      ...res.events.map(e => ({
        label: e.label || e.effector, t0: e.on_step * rec.ts, t1: e.off_step * rec.ts, effector: e.effector, mv: e.mv,
        pulse: e.pulse_steps ? [e.pulse_steps[0] * rec.ts, e.pulse_steps[1] * rec.ts] : null,
        approx: e.approximation, rows: e.effector === "kick" ? new Set(e.rows) : null, on: e.on_step, off: e.off_step,
      })),
    ];
    for (const e of this.events) if (e.rows) e.kicks = [];
    const kev = this.events.filter(e => e.rows);
    for (let k = 0; k < rec.kickStep.length; k++) {
      const s = rec.kickStep[k], r = rec.kickRow[k];
      const e = kev.find(e => s >= e.on && s < e.off && e.rows.has(r));
      if (e) e.kicks.push(s * rec.ts);
    }
    this._layout();
  }

  _layout() {
    const tracks = [];
    if (this.events.length) tracks.push({ id: "stim", h: 4 + 22 * this.events.length, label: "stimulus" });
    if (this.sel !== null) tracks.push({ id: "sel", h: 56, label: "selected cell" });
    tracks.push({ id: "rate", h: Math.max(48, 9 * this.rates.supers.length), label: "rate by superclass" });
    tracks.push({ id: "mn", h: 90, label: "motor neurons" });
    if (this.rec.nAct) tracks.push({ id: "torque", h: 70, label: "actuator torque" });
    if (this.rec.mod_level.length) tracks.push({ id: "mod", h: 30, label: "modulators" });
    tracks.push({ id: "height", h: 30, label: "thorax height" });
    let y = 18;
    for (const tr of tracks) { tr.y = y; y += tr.h + 8; }
    this.tracks = tracks;
    this.height = y + 4;
    this.canvas.style.height = this.height + "px";
  }

  // a matched control recording (same rows); its spikes show under the selected cell
  setControl(ctrl) {
    this.ctrl = ctrl;
    if (this.sel !== null) this.select(this.sel, this.selLabel);
  }

  select(row, label) {
    this.sel = row;
    this.selLabel = label;
    this.selSpikes = row === null ? [] : this.rec.spikeTimes(row);
    this.ctrlSpikes = row === null || !this.ctrl ? null : this.ctrl.spikeTimes(row);
    const w = row === null ? -1 : this.rec.watchIndex(row);
    this.selWatch = w;
    this._layout();
    this.redraw();
  }

  tToX(t) { const [a, b] = this.view; return GUTTER + (t - a) / (b - a) * (this.W - GUTTER - 8); }
  xToT(x) { const [a, b] = this.view; return Math.max(0, Math.min(this.rec.duration, a + (x - GUTTER) / (this.W - GUTTER - 8) * (b - a))); }

  redraw() {
    if (!this.rec) return;
    const dpr = Math.min(devicePixelRatio, 2), W = this.canvas.clientWidth;
    this.W = W;
    if (!this.off) this.off = document.createElement("canvas");
    this.off.width = W * dpr; this.off.height = this.height * dpr;
    this.canvas.width = W * dpr; this.canvas.height = this.height * dpr;
    const g = this.off.getContext("2d");
    g.setTransform(dpr, 0, 0, dpr, 0, 0);
    g.fillStyle = this.col.bg; g.fillRect(0, 0, W, this.height);
    g.font = "11px 'IBM Plex Mono', ui-monospace, monospace";
    this._axis(g);
    for (const tr of this.tracks) this["_" + tr.id](g, tr);
    this.draw(this.t);
  }

  _axis(g) {
    const [a, b] = this.view, span = b - a;
    const step = [1, 2, 5, 10, 20, 50, 100, 200, 500, 1000, 2000, 5000, 10000, 30000, 60000]
      .find(s => span / s <= 10) || 60000;
    g.fillStyle = this.col.dim; g.strokeStyle = this.col.grid; g.lineWidth = 1;
    for (let t = Math.ceil(a / step) * step; t <= b; t += step) {
      const x = Math.round(this.tToX(t)) + 0.5;
      g.beginPath(); g.moveTo(x, 14); g.lineTo(x, this.height); g.stroke();
      g.fillText(t >= 1000 ? `${(t / 1000).toFixed(step < 1000 ? 1 : 0)} s` : `${t} ms`, x + 3, 11);
    }
  }

  _label(g, tr, text, sub) {
    g.fillStyle = this.col.fg; g.fillText(text, 8, tr.y + 11);
    if (sub) { g.fillStyle = this.col.dim; g.fillText(sub, 8, tr.y + 24); }
  }

  // one row per genotype or event: its label (with "approx." when the effector is an
  // approximation), then a bar; pulses drawn one by one, kicks as ticks
  _stim(g, tr) {
    this._label(g, tr, "stimulus", "* = approximated");
    const [a, b] = this.view, xEnd = this.W - 8;
    this.events.forEach((e, k) => {
      const y = tr.y + 2 + k * 22, by = y + 13;
      const x0 = Math.max(GUTTER, this.tToX(e.t0)), x1 = Math.min(xEnd, this.tToX(e.t1));
      g.fillStyle = this.col.fg;
      g.fillText(`${e.label}${e.approx ? " *" : ""}`, Math.max(GUTTER, Math.min(x0, xEnd - 200)) + 2, y + 9);
      if (x1 <= x0) return;
      const colour = e.mv < 0 ? this.col.cool : e.effector === "world" ? "#30a050" : this.col.stim;
      g.fillStyle = colour;
      if (e.kicks) {
        g.globalAlpha = 0.18; g.fillRect(x0, by, x1 - x0, 7); g.globalAlpha = 1;
        for (const t of e.kicks) if (t >= a && t <= b) g.fillRect(this.tToX(t), by, 1, 7);
      } else if (e.pulse && (x1 - x0) / ((e.t1 - e.t0) / e.pulse[0]) >= 3) {
        for (let t = e.t0; t < e.t1; t += e.pulse[0]) {
          const p0 = this.tToX(t), p1 = this.tToX(Math.min(e.t1, t + e.pulse[1]));
          if (p1 >= GUTTER && p0 <= xEnd) g.fillRect(Math.max(GUTTER, p0), by, Math.max(1, p1 - Math.max(GUTTER, p0)), 7);
        }
      } else {
        g.globalAlpha = e.pulse ? 0.5 : e.effector === "TNT" || e.effector === "Kir2.1" ? 0.45 : 1;
        g.fillRect(x0, by, x1 - x0, 7); g.globalAlpha = 1;
      }
    });
  }

  _rate(g, tr) {
    const { supers, rate, nB } = this.rates, h = tr.h / supers.length;
    this._label(g, tr, "rate", "Hz/cell");
    g.fillStyle = this.col.dim; g.fillText("log", 8, tr.y + 37);
    const [a, b] = this.view, k0 = Math.floor(a / RATE_BIN_MS), k1 = Math.min(nB, Math.ceil(b / RATE_BIN_MS));
    g.font = "9px 'IBM Plex Mono', ui-monospace, monospace"; g.textAlign = "right";
    supers.forEach(s => {
      const q = supers.indexOf(s), y = tr.y + q * h;
      g.fillStyle = this.col.dim;
      g.fillText(this.atlas.vocab.superclass[s] || "(none)", GUTTER - 6, y + h - 1);
    });
    g.font = "11px 'IBM Plex Mono', ui-monospace, monospace"; g.textAlign = "left";
    supers.forEach((s, q) => {
      const y = tr.y + q * h;
      for (let k = k0; k < k1; k++) {
        const v = rate[q][k]; if (!v) continue;
        const u = Math.min(1, Math.log10(1 + v) / 2);     // 0..99 Hz
        g.globalAlpha = 0.15 + 0.85 * u;
        g.fillStyle = this.col.hot;
        const x0 = this.tToX(k * RATE_BIN_MS), x1 = this.tToX((k + 1) * RATE_BIN_MS);
        g.fillRect(x0, y, Math.max(1, x1 - x0), h - 1);
      }
      g.globalAlpha = 1;
    });
  }

  _mn(g, tr) {
    const { t, y, n } = this.mn, m = this.mnMappedCount;
    this._label(g, tr, "motor neurons", `${m} of ${n} drive`);
    g.fillStyle = this.col.dim; g.fillText("a muscle (top)", 8, tr.y + 37);
    const sy = tr.h / n;
    g.fillStyle = this.col.dim; g.globalAlpha = 0.25;
    g.fillRect(GUTTER, tr.y + m * sy, this.W - GUTTER - 8, 1);
    g.globalAlpha = 1; g.fillStyle = this.col.fg;
    const [a, b] = this.view;
    for (let k = 0; k < t.length; k++) {
      if (t[k] < a || t[k] > b) continue;
      g.fillRect(this.tToX(t[k]), tr.y + y[k] * sy, 1.2, Math.max(1, sy));
    }
  }

  _torque(g, tr) {
    const rec = this.rec, nA = rec.nAct, lim = rec.manifest.limits;
    this._label(g, tr, "actuator torque", `${nA} actuators; / limit`);
    g.fillStyle = this.col.dim; g.fillText("clipped", 8, tr.y + 37);
    g.fillStyle = this.col.clip; g.fillRect(64, tr.y + 29, 9, 9);
    const sy = tr.h / nA, [a, b] = this.view, fs = rec.frameStep, ts = rec.ts;
    const f0 = Math.max(0, rec.frameAt(a)), f1 = Math.min(rec.nFrames - 1, rec.frameAt(b) + 1);
    for (let f = f0; f <= f1; f++) {
      const x0 = this.tToX(fs[f] * ts), x1 = f + 1 < rec.nFrames ? this.tToX(fs[f + 1] * ts) : x0 + 2;
      for (let j = 0; j < nA; j++) {
        const v = rec.torque[f * nA + j];
        const L = v >= 0 ? (lim ? lim.hi[j] : 1) : (lim ? -lim.lo[j] : 1);
        const u = L > 0 ? Math.abs(v) / L : 0;
        if (u < 0.02) continue;
        if (lim && lim.limited && lim.limited[j] && u >= 0.999) g.fillStyle = this.col.clip;
        else { g.fillStyle = v >= 0 ? this.col.hot : this.col.cool; g.globalAlpha = Math.min(1, 0.15 + u); }
        g.fillRect(x0, tr.y + j * sy, Math.max(1, x1 - x0), Math.max(1, sy));
        g.globalAlpha = 1;
      }
    }
  }

  _mod(g, tr) {
    const rec = this.rec, names = rec.manifest.names.modulators || [], k = names.length || 3;
    const colours = [this.col.hot, this.col.cool, "#30a050"];
    let max = 0;
    for (const v of rec.mod_level) max = Math.max(max, v);
    this._label(g, tr, "modulators", max > 0 ? `max ${max.toPrecision(2)}` : "all zero");
    g.textAlign = "right";
    names.forEach((nm, j) => { g.fillStyle = colours[j % 3]; g.fillText(nm.slice(0, 4), GUTTER - 6 - (k - 1 - j) * 34, tr.y + 11); });
    g.textAlign = "left";
    max = Math.max(max, 1e-9);
    for (let j = 0; j < k; j++) {
      g.strokeStyle = colours[j % 3]; g.beginPath();
      for (let f = 0; f < rec.nFrames; f++) {
        const x = this.tToX(rec.frameStep[f] * rec.ts), y = tr.y + tr.h - rec.mod_level[f * k + j] / max * tr.h;
        f ? g.lineTo(x, y) : g.moveTo(x, y);
      }
      g.stroke();
    }
  }

  _height(g, tr) {
    const rec = this.rec, NB = rec.nBodies;
    let lo = Infinity, hi = -Infinity;
    const z = new Float32Array(rec.nFrames);
    for (let f = 0; f < rec.nFrames; f++) { z[f] = rec.xpos[(f * NB + 1) * 3 + 2]; lo = Math.min(lo, z[f]); hi = Math.max(hi, z[f]); }
    this._label(g, tr, "thorax height", `${lo.toFixed(2)} to ${hi.toFixed(2)} mm`);
    g.strokeStyle = this.col.fg; g.beginPath();
    for (let f = 0; f < rec.nFrames; f++) {
      const x = this.tToX(rec.frameStep[f] * rec.ts), y = tr.y + tr.h - (z[f] - lo) / Math.max(1e-6, hi - lo) * tr.h;
      f ? g.lineTo(x, y) : g.moveTo(x, y);
    }
    g.stroke();
  }

  _sel(g, tr) {
    const rec = this.rec;
    this._label(g, tr, (this.selLabel || "").slice(0, 22), `${this.selSpikes.length} spikes` + (this.selWatch < 0 ? "; v not recorded" : ""));
    g.fillStyle = this.col.hot;
    for (const t of this.selSpikes) g.fillRect(this.tToX(t), tr.y, 1.5, 10);
    if (this.ctrlSpikes) {
      g.fillStyle = this.col.dim;
      for (const t of this.ctrlSpikes) g.fillRect(this.tToX(t), tr.y + 11, 1.5, 6);
      g.fillText(`control ${this.ctrlSpikes.length} (grey)`, 8, tr.y + 50);
    }
    if (this.selWatch >= 0) {
      const w = this.selWatch, nW = rec.nWatch, nV = rec.vStep.length;
      let lo = Infinity, hi = -Infinity;
      for (let s = 0; s < nV; s++) { const v = rec.v[s * nW + w]; lo = Math.min(lo, v); hi = Math.max(hi, v); }
      g.strokeStyle = this.col.fg; g.beginPath();
      const [a, b] = this.view;
      let started = false;
      for (let s = 0; s < nV; s++) {
        const t = rec.vStep[s] * rec.ts; if (t < a || t > b) continue;
        const x = this.tToX(t), y = tr.y + tr.h - (rec.v[s * nW + w] - lo) / Math.max(1e-6, hi - lo) * (tr.h - 14);
        started ? g.lineTo(x, y) : g.moveTo(x, y); started = true;
      }
      g.stroke();
      g.fillStyle = this.col.dim; g.fillText(`${lo.toFixed(0)} to ${hi.toFixed(0)} mV`, 8, tr.y + 37);
    }
  }

  draw(t) {
    this.t = t;
    if (!this.off) return;
    const g = this.ctx, dpr = Math.min(devicePixelRatio, 2);
    g.setTransform(1, 0, 0, 1, 0, 0);
    g.drawImage(this.off, 0, 0);
    g.setTransform(dpr, 0, 0, dpr, 0, 0);
    const x = this.tToX(t);
    if (x >= GUTTER) {
      g.strokeStyle = this.col.hot; g.lineWidth = 1.5;
      g.beginPath(); g.moveTo(x, 14); g.lineTo(x, this.height); g.stroke();
    }
  }
}
