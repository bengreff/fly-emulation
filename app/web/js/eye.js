// Fly's-eye view (M3): each eye's 721 ommatidia as the hex mosaic, shaded by the
// readout the photoreceptors were driven by at the current time (recorded eye frames,
// 2 eyes x 721 x yellow/pale, one channel filled); the columnar cells of the motion
// pathway placed on it (app/build/columns.py, flyemu-columns/1); what each type did in
// this run; and traces of the motion-sensing cells. Geometry and photoreceptor
// assignments come from app/build/eye.py (flyemu-eye/1).
import { fetchJSON } from "./io.js";
import { esc } from "./inspector.js";

const N_EYE = 2;
// lobula plate tangential cells: the motion-sensing outputs of T4/T5 (male-cns type names)
const LPTC = ["HSE", "HSN", "HSS", "H1", "H2", "VS", "VSm", "HST", "VST1", "VST2"];
const STAGES = [
  ["lamina", ["L1", "L2", "L3", "L4", "L5"]],
  ["medulla, ON inputs to T4", ["Mi1", "Tm3", "Mi4", "Mi9", "C3"]],
  ["medulla, OFF inputs to T5", ["Tm1", "Tm2", "Tm4", "Tm9"]],
  ["T4, ON motion", ["T4a", "T4b", "T4c", "T4d"]],
  ["T5, OFF motion", ["T5a", "T5b", "T5c", "T5d"]],
];
const RATE_BIN = 10;          // ms, for spike-rate traces
const MIN_SPAN = 1;           // mV, the least vertical range of a voltage row
const fmt = (v, d = 1) => v === null || v === undefined || Number.isNaN(v) ? "–" : Number(v).toFixed(d);
const chipFor = s => `<span class="chip ${s === "measured" ? "measured" : s === "inferred" || s === "derived" ? "inferred" : "guessed"}">${esc(s)}</span>`;

export class EyePanel {
  constructor(el, { onSelect, onHighlight, onTime }) {
    this.el = el; this.onSelect = onSelect; this.onHighlight = onHighlight; this.onTime = onTime || (() => {});
    this.frame = -2; this.pick = null; this.selType = null; this.drawKey = ""; this.traceKey = "";
  }

  async load(url, rec, atlas) {
    this.rec = rec; this.atlas = atlas;
    try { this.g = await fetchJSON(url); } catch { this.g = null; }
    if (!this.g) { this.el.innerHTML = `<div class="empty">No eye geometry for this body (run app/build/eye.py).</div>`; return; }
    try { this.cols = await fetchJSON(url.replace(/eye\.json$/, "columns.json")); } catch { this.cols = null; }
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
    this.ommOf = new Map();        // bodyId -> {e, o}
    const prTypes = new Set();
    ["L", "R"].forEach((k, e) => {
      const p = this.g.photoreceptors[k], m = new Map();
      if (p) p.ommatidium.forEach((o, j) => {
        if (!m.has(o)) m.set(o, []);
        m.get(o).push({ bodyId: p.bodyId[j], type: p.type[j] });
        this.ommOf.set(p.bodyId[j], { e, o });
        prTypes.add(p.type[j]);
      });
      this.cells[e] = m;
    });
    this.prTypes = [...prTypes].sort();
    // R1-R6 per ommatidium in the assignment, against the 6 per cartridge of the real eye
    const k = [];
    for (const m of Object.values(this.cells))
      for (const cs of m.values()) { const r = cs.filter(c => c.type === "R1-R6").length; if (r) k.push(r); }
    this.r16 = k.length ? { n: k.length, min: Math.min(...k), max: Math.max(...k),
      mean: k.reduce((a, b) => a + b, 0) / k.length, six: k.filter(v => v === 6).length } : null;
    this.buildTypes();
    const nf = rec.eyeStep ? rec.eyeStep.length : 0;
    const note = (rec.manifest.protocol || {}).watch_note;
    this.patch = note && note.patch_ommatidia ? { e: note.patch_eye === "right" ? 1 : 0, o: new Set(note.patch_ommatidia) } : null;
    this.el.innerHTML = `<h2>Fly's-eye view</h2>
      <div class="sub">${nf ? `${nf} eye frames in this run` : "no eye frames in this run"}; 721 ommatidia per eye</div>
      ${nf ? "" : `<div class="warnline">${rec.manifest.preparation && rec.manifest.preparation.coupling === "brain_only"
        ? "Brain only: the eyes were not rendered, so the photoreceptors received no light input." : "This recording holds no eye readouts."}</div>`}
      ${this.activityHTML()}
      <label><input type="checkbox" id="eye-pale"> ring pale ommatidia</label>
      <canvas id="eye-canvas"></canvas>
      <div id="eye-key" class="dim"></div>
      <div class="dim">Shade: the luminance each ommatidium's photoreceptors were driven by at this time (0 to 1, the renderer's units; the white sky reaches 1, the renderer's ceiling). Positions: centroid of each ommatidium's pixels in flygym's eye map <span class="chip inferred">derived</span>. Pale/yellow: majority of the connectome's R7/R8 subtypes per ommatidium, else flygym's mask <span class="chip inferred">derived</span>. Eyes as rendered (flygym's image frame).</div>
      ${this.r16 ? `<div class="dim">Assignment check: a real lamina cartridge receives 6 R1-R6 terminals (neural superposition) <span class="chip measured">measured anatomy</span>; this assignment gives ${this.r16.min} to ${this.r16.max} per ommatidium (mean ${this.r16.mean.toFixed(1)}; exactly 6 in ${this.r16.six} of the ${this.r16.n} with any), so one ommatidium's list is uncertain.</div>` : ""}
      <div id="eye-pick"></div>
      <h3 id="eye-columns">Columns: photoreceptor to motion-sensing cell</h3>
      ${this.tableHTML()}
      <div id="eye-type"></div>
      ${this.placementNotesHTML()}
      <h3 id="eye-motion">Motion-sensing traces</h3>
      <div class="dim">${this.traceIntroHTML()}</div>
      <canvas id="eye-traces"></canvas>
      <div class="dim">Blue: mean membrane potential of the watched cells of the row (mV), each row scaled to its own range (at least ${MIN_SPAN} mV), printed at right with the value now. Orange: spikes per cell per second in ${RATE_BIN} ms bins, for rows with no watched cell. Click to set the time.</div>
      ${this.lptcNotesHTML()}`;
    this.canvas = this.el.querySelector("#eye-canvas");
    this.tcanvas = this.el.querySelector("#eye-traces");
    this.el.querySelector("#eye-pale").onchange = () => { this.drawKey = ""; };
    this.canvas.onclick = e => this.click(e);
    this.tcanvas.onclick = e => this.traceClick(e);
    this.el.querySelector("#eye-pick").onclick = e => {
      const a = e.target.closest("[data-i]"); if (a) this.onSelect(Number(a.dataset.i));
      const h = e.target.closest("[data-all]"); if (h) this.onHighlight(this.pickIds());
    };
    this.el.querySelector("#eye-coltable").onclick = e => {
      const r = e.target.closest("[data-type]"); if (r) this.selectType(r.dataset.type);
    };
  }

  // ---- per-type bookkeeping for this run --------------------------------------------

  buildTypes() {
    const rec = this.rec, a = this.atlas, inv = rec.inventory || [];
    const code = new Map(a.vocab.type.map((t, c) => [t, c]));
    this.rowOf = new Map();
    for (let r = 0; r < rec.rowBodyId.length; r++) this.rowOf.set(rec.rowBodyId[r], r);
    // the model's transmission mode per type, read from the run's inventory
    const graded = inv.filter(r => r.property === "graded" && r.entity.startsWith("cell_type:") && r.entity !== "cell_type:all"
      && Number(r.value) === 1).map(r => ({ re: new RegExp(r.entity.slice(10)), status: r.status || r.basis, evidence: r.evidence }));
    const colMode = inv.find(r => r.entity === "mode:n1_p_graded_optic_columnar" && r.property === "graded");
    this.colMode = colMode ? { value: Number(colMode.value), status: colMode.status, n: colMode.instances } : null;
    const dflt = inv.find(r => r.entity === "cell_type:all" && r.property === "graded");
    this.defaultStatus = dflt ? dflt.status : null;
    const counts = rec.countsPerRow(), dur = rec.duration / 1000;
    const per = this.cols ? new Map(this.cols.per_type.map(p => [p.type, p])) : new Map();
    const mk = (name, stage) => {
      const c = code.get(name);
      const idx = c === undefined ? [] : Array.from(a.ofType(c));
      const rows = [], watched = [];
      let spikes = 0, firing = 0;
      for (const i of idx) {
        const r = this.rowOf.get(a.bodyId[i]);
        if (r === undefined) continue;
        rows.push(r); spikes += counts[r]; if (counts[r]) firing++;
        const w = rec.watchIndex(r); if (w >= 0) watched.push(w);
      }
      const g = graded.find(m => m.re.test(name));
      return { name, stage, idx, rows, watched, spikes, firing, hz: rows.length ? spikes / rows.length / dur : null,
               mode: g ? { graded: true, status: g.status, evidence: g.evidence } : rec.inventory ? { graded: false, status: this.defaultStatus } : null,
               place: per.get(name) || null };
    };
    this.types = [];
    for (const t of this.prTypes) this.types.push(mk(t, "photoreceptors"));
    for (const [stage, ts] of STAGES) for (const t of ts) this.types.push(mk(t, stage));
    for (const t of LPTC) this.types.push(mk(t, "lobula plate tangential"));
    this.byName = new Map(this.types.map(t => [t.name, t]));
    this.buildTraces();
  }

  activityHTML() {
    const ty = this.types, all = ty.reduce((s, t) => s + t.rows.length, 0), fired = ty.reduce((s, t) => s + t.firing, 0);
    const spikes = ty.reduce((s, t) => s + t.spikes, 0), watched = ty.reduce((s, t) => s + t.watched.length, 0);
    const gr = ty.filter(t => t.mode && t.mode.graded).reduce((s, t) => s + t.rows.length, 0);
    return `<div class="${fired ? "dim" : "warnline"}">This run: ${fired.toLocaleString()} of the ${all.toLocaleString()} cells in the table fired
      (${spikes.toLocaleString()} spikes) <span class="chip measured">this run</span>; ${gr.toLocaleString()} of them are graded in the model and cannot spike;
      ${watched ? `${watched} have their membrane potential recorded` : "none has its membrane potential recorded, so the graded ones show nothing here"}.
      The scene holds no moving stimulus (visual stimulus objects are on hold), so the only image motion is the fly's own.</div>`;
  }

  tableHTML() {
    const t0 = this.types, cell = (v, cls = "num") => `<td class="${cls}">${v}</td>`;
    let stage = null, h = "";
    for (const t of t0) {
      if (t.stage !== stage) { stage = t.stage; h += `<tr class="grp"><td colspan="9">${esc(stage)}</td></tr>`; }
      const p = t.place, mode = t.mode ? (t.mode.graded ? "graded" : "spiking") : "?";
      const placed = p ? `${p.n_placed}/${p.n_scan}` : t.stage === "photoreceptors"
        ? `${this.assigned(t.name)}/${t.idx.length}` : "–";
      const ncol = p ? `${p.n_columns[0]}·${p.n_columns[1]}` : "–";
      const per = p ? `${fmt(p.per_column_median, 0)}/${p.per_column_max}` : "–";
      const soma = p && p.soma_neighbours_near !== null ? `${fmt(p.soma_neighbours_near, 2)}/${fmt(p.soma_neighbours_near_shuffled, 2)}` : "–";
      h += `<tr class="link${this.selType === t.name ? " on" : ""}" data-type="${esc(t.name)}">
        <td>${esc(t.name)}</td><td class="mode ${mode}">${mode}</td>${cell(placed)}${cell(ncol)}${cell(per)}${cell(soma)}
        ${cell(t.rows.length ? `${t.firing}/${t.rows.length}` : "–")}${cell(t.hz === null ? "–" : fmt(t.hz, t.hz && t.hz < 1 ? 2 : 1))}
        <td class="num" data-v="${esc(t.name)}">${t.watched.length ? "" : "–"}</td></tr>`;
    }
    return `<table id="eye-coltable" class="coltable">
      <tr class="hd"><td>type</td><td>model</td><td class="num" title="placed in the mosaic / cells in the scan (photoreceptors: assigned to an ommatidium)">placed</td>
      <td class="num" title="ommatidia holding at least one cell, left·right eye (721 each)">columns</td>
      <td class="num" title="cells per occupied column, median/max (the real eye has 1 of each type per column, more for T4/T5 subtypes only by count)">per col</td>
      <td class="num" title="share of cells whose 6 nearest by soma lie within 2 spacings in the mosaic, against the placements shuffled within the type">soma</td>
      <td class="num" title="cells that fired at least once in this run / cells simulated">fired</td>
      <td class="num" title="mean spikes per cell per second over the run">Hz</td>
      <td class="num" title="mean membrane potential of the watched cells at the current time (n watched)">mV now</td></tr>${h}</table>
      <div class="dim">Placement columns <span class="chip inferred">derived</span> (app/build/columns.py); fired, Hz and mV <span class="chip measured">this run</span>; model mode from this run's inventory. Click a type to place its cells on the mosaic and light them on the brain map.</div>`;
  }

  assigned(type) {
    let n = 0;
    for (const k of ["L", "R"]) { const p = this.g.photoreceptors[k]; if (p) for (const t of p.type) if (t === type) n++; }
    return n;
  }

  placementNotesHTML() {
    const c = this.cols, m = this.colMode;
    const mode = this.types.filter(t => t.mode && t.mode.graded);
    const modeLine = `Model mode: ${[...new Set(mode.map(t => `${t.name}`))].join(", ") || "no type"} graded (${[...new Set(mode.map(t => t.mode.status))].join(", ")}; R types from intracellular recordings, L1-L3 from blowfly and Drosophila lamina recordings); every other type here spikes by the model's default ${chipFor(this.defaultStatus || "guessed")}${m ? `, and the optic-columnar group's graded switch is ${m.value} in this profile ${chipFor(m.status)}` : ""}. Graded cells pass a rate-equivalent to their targets, not spikes.`;
    if (!c) return `<div class="dim">${modeLine}</div><div class="warnline">No column placement for this body (run app/build/columns.py).</div>`;
    return `<ul class="caveats">
      <li>${modeLine}</li>
      <li>Placement ${chipFor("derived")}: the scan has no column labels for these cells. Each photoreceptor sits at its ommatidium (itself derived topology with an inferred global alignment); every other cell takes the synapse-weighted mean position of its placed inputs (edges of ${c.min_synapses} or more synapses), iterated to convergence (${c.iterations} iterations). Built ${esc(c.created)}.</li>
      <li>Checks, not used for placing: every placed cell lands in the eye of its annotated soma side; somata that are neighbours land near each other far more often than when the placements are shuffled (the soma column, e.g. L1 ${this.somaPair("L1")}, T4a ${this.somaPair("T4a")}).</li>
      <li>Limit: a weighted mean cannot place a cell beyond the photoreceptors it reads, so cells past the edge of the photoreceptor map stack on edge ommatidia (the per-column maxima, up to ${Math.max(...c.per_type.map(p => p.per_column_max || 0))} cells of one type on one ommatidium), and columns without assigned photoreceptors stay empty. The real eye has one of each columnar type per column (T4/T5: one of each subtype).</li></ul>`;
  }

  somaPair(t) {
    const p = this.byName.get(t) && this.byName.get(t).place;
    return p && p.soma_neighbours_near !== null ? `${fmt(p.soma_neighbours_near, 2)} against ${fmt(p.soma_neighbours_near_shuffled, 2)}` : "–";
  }

  traceIntroHTML() {
    const nW = this.traces.filter(r => r.kind === "v").length;
    const note = (this.rec.manifest.protocol || {}).watch_note;
    return nW
      ? `${nW} rows from watched cells${note ? `: a patch of ${note.patch_ommatidia.length} ${note.patch_eye}-eye ommatidia around ommatidium ${note.patch_centre_ommatidium} (one cell per type per ommatidium, ${note.patch_cells} columnar cells, plus the photoreceptors assigned there), outlined on the mosaic, and every tangential cell` : ""}. Cells without a recorded voltage show their spike rate.`
      : `No visual cell's membrane potential was recorded in this run (the library control watches only its readout types), so each spiking type shows its spike rate over all its cells and the graded types show nothing.`;
  }

  lptcNotesHTML() {
    return `<ul class="caveats"><li>In real flies the lobula plate tangential cells (HS, VS, H1, H2) report wide-field motion mainly as graded depolarisation and hyperpolarisation, with spikes riding on it in some cells ${chipFor("measured")} (literature: blowfly recordings from Hausen and Hengstenberg; Drosophila HS and VS whole-cell recordings, Joesch et al. 2008, Schnell et al. 2010), so a model spike rate of zero does not by itself mean the cell is unmoved; its voltage says that.</li>
      <li>Direction selectivity is not checked here: that needs moving gratings in the scene, which waits on the visual-stimulus request (on hold).</li></ul>`;
  }

  // trace rows: patch types (watched voltage if any, else rate over all cells), then
  // every tangential type per side
  buildTraces() {
    const rec = this.rec, a = this.atlas, rows = [];
    const pr = this.types.filter(t => t.stage === "photoreceptors"), graded = t => !!(t.mode && t.mode.graded);
    const r16 = pr.filter(t => t.name === "R1-R6"), r78 = pr.filter(t => t.name !== "R1-R6");
    if (r16.length) rows.push(this.traceRow("R1-R6", r16.flatMap(t => t.idx), false, r16.every(graded)));
    if (r78.length) rows.push(this.traceRow("R7, R8", r78.flatMap(t => t.idx), false, r78.every(graded)));
    for (const t of this.types) {
      if (t.stage === "lobula plate tangential" || t.stage === "photoreceptors") continue;
      rows.push(this.traceRow(t.name, t.idx, false, graded(t)));
    }
    for (const name of LPTC) {
      const t = this.byName.get(name);
      for (const s of ["L", "R"]) {
        const idx = t.idx.filter(i => a.side(i) === s);
        if (idx.length) rows.push(this.traceRow(`${name} ${s}`, idx, true, !!(t.mode && t.mode.graded)));
      }
    }
    // spike rates for the rows that need them: one pass over the spikes
    const nb = Math.ceil(rec.duration / RATE_BIN), grp = new Int32Array(rec.manifest.n_rows).fill(-1);
    rows.forEach((r, g) => { if (r.kind === "rate") { r.data = new Float32Array(nb); for (const q of r.rows) grp[q] = g; } });
    const P = rec.spikePtr, R = rec.spikeRow, S = rec.spikeSub;
    for (let b = 0; b < rec.nBins; b++)
      for (let k = P[b]; k < P[b + 1]; k++) {
        const g = grp[R[k]]; if (g < 0) continue;
        const bin = Math.min(nb - 1, Math.floor((b * rec.binMs + S[k] * rec.ts) / RATE_BIN));
        rows[g].data[bin]++;
      }
    for (const r of rows) if (r.kind === "rate") {
      const k = 1000 / RATE_BIN / Math.max(1, r.rows.length);
      for (let i = 0; i < r.data.length; i++) r.data[i] *= k;
      r.total = r.rows.reduce((s, q) => s + rec.countsPerRow()[q], 0);
    }
    for (const r of rows) { let lo = Infinity, hi = -Infinity; for (const v of r.data) { lo = Math.min(lo, v); hi = Math.max(hi, v); } r.lo = lo; r.hi = hi; }
    this.traces = rows;
  }

  traceRow(label, idx, lptc, graded) {
    const rec = this.rec, rows = [], watched = [];
    for (const i of idx) {
      const r = this.rowOf.get(this.atlas.bodyId[i]); if (r === undefined) continue;
      rows.push(r); const w = rec.watchIndex(r); if (w >= 0) watched.push(w);
    }
    if (watched.length) {
      const nV = rec.vStep.length, nW = rec.nWatch, data = new Float32Array(nV);
      for (let s = 0; s < nV; s++) { let m = 0; for (const w of watched) m += rec.v[s * nW + w]; data[s] = m / watched.length; }
      return { label, kind: "v", rows, watched, data, lptc };
    }
    // a graded cell has no spikes to count: without a recorded voltage there is nothing to draw
    if (graded) return { label, kind: "none", rows, watched, data: new Float32Array(0), lptc };
    return { label, kind: "rate", rows, watched, lptc };
  }

  // ---- selection --------------------------------------------------------------------

  selectType(name) {
    this.selType = this.selType === name ? null : name;
    this.el.querySelectorAll("#eye-coltable tr[data-type]").forEach(r => r.classList.toggle("on", r.dataset.type === this.selType));
    this.drawKey = "";
    const t = this.selType && this.byName.get(this.selType);
    this.onHighlight(t ? t.idx : []);
    this.selCells = t ? this.cellsOf(t) : null;
    const box = this.el.querySelector("#eye-type");
    if (!t) { box.innerHTML = ""; return; }
    const p = t.place, sc = this.selCells;
    box.innerHTML = `<h3>${esc(t.name)}</h3><table>
      <tr><td>in the scan</td><td>${t.idx.length} cells; ${t.rows.length} simulated in this run</td></tr>
      <tr><td>model mode</td><td>${t.mode ? (t.mode.graded ? `graded ${chipFor(t.mode.status)}<div class="dim">${esc(t.mode.evidence || "")}</div>` : `spiking ${chipFor(t.mode.status || "guessed")}`) : "no inventory in this run"}</td></tr>
      ${p ? `<tr><td>placed</td><td>${p.n_placed} of ${p.n_scan}; ${p.n_columns[0]} left and ${p.n_columns[1]} right columns; ${fmt(p.per_column_median, 0)} per column (max ${p.per_column_max}) ${chipFor("derived")}</td></tr>
      <tr><td>hops</td><td>median ${fmt(p.hops_median, 0)} synaptic steps from a photoreceptor (connectome path)</td></tr>
      <tr><td>input read</td><td>median ${fmt(p.share_median * 100, 0)}% of its input synapses come from the cells the placement reads; their spread ${fmt(p.spread_median, 2)} spacings (RMS)</td></tr>
      <tr><td>checks</td><td>eye matches soma side in ${fmt(p.eye_matches_soma_side * 100, 0)}%; soma neighbours near ${this.somaPair(t.name)} shuffled</td></tr>` : ""}
      <tr><td>this run</td><td>${t.firing} fired, ${t.spikes} spikes, ${t.hz === null ? "–" : fmt(t.hz, 2)} Hz per cell; ${t.watched.length} watched</td></tr>
      <tr><td>on the mosaic</td><td>${sc && sc.n ? `${sc.n} cells drawn${t.watched.length ? "; watched cells coloured by membrane potential" : ""}` : "not columnar: no position in the mosaic"}</td></tr></table>`;
  }

  // positions of a type's cells in the mosaic: placements for columnar types, the
  // assigned ommatidium for photoreceptors
  cellsOf(t) {
    const out = { e: [], x: [], y: [], w: [], n: 0 }, rec = this.rec;
    const push = (bid, e, x, y) => {
      const r = this.rowOf.get(bid), w = r === undefined ? -1 : rec.watchIndex(r);
      out.e.push(e); out.x.push(x); out.y.push(y); out.w.push(w); out.n++;
    };
    if (t.stage === "photoreceptors") {
      ["L", "R"].forEach((k, e) => {
        const p = this.g.photoreceptors[k]; if (!p) return;
        p.type.forEach((ty, j) => { if (ty === t.name) push(p.bodyId[j], e, this.g.centroid.x[p.ommatidium[j]], this.g.centroid.y[p.ommatidium[j]]); });
      });
    } else if (this.cols) {
      const c = this.cols.cells, ti = this.cols.types.indexOf(t.name);
      if (ti >= 0) for (let j = 0; j < c.type.length; j++) if (c.type[j] === ti) push(c.bodyId[j], c.eye[j], c.x[j], c.y[j]);
    }
    return out;
  }

  // ---- drawing ----------------------------------------------------------------------

  layout() {
    const w = Math.max(200, this.el.clientWidth - 8), img = this.g.image;
    const s = (w / 2 - 12) / img.cols;           // pixels of canvas per image pixel
    return { w, h: Math.ceil(img.rows * s) + 18, s, ox: [0, w / 2 + 6] };
  }

  draw(t) {
    if (!this.g || !this.canvas || this.el.hidden) return;
    this.drawMosaic(t);
    this.drawTraces(t);
    this.updateNow(t);
  }

  drawMosaic(t) {
    const rec = this.rec, nf = rec.eyeStep ? rec.eyeStep.length : 0;
    const f = nf ? rec.eyeAt(t) : -1;
    const L = this.layout();
    const sc = this.selCells, vi = sc && sc.w.some(w => w >= 0) ? rec.vAt(t) : -1;
    const key = `${f},${L.w},${this.selType},${vi},${this.pick ? this.pick.e + ":" + this.pick.o : ""}`;
    if (key === this.drawKey) return;
    this.drawKey = key;
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
        if (this.patch && this.patch.e === e && this.patch.o.has(o)) { g.strokeStyle = "#20a0ff"; g.lineWidth = 1.5; g.stroke(); }
      }
      if (this.pick && this.pick.e === e) {          // the picked ommatidium, drawn last so it sits on top
        const o = this.pick.o, cx = L.ox[e] + x[o] * L.s, cy = 16 + y[o] * L.s;
        g.beginPath(); g.arc(cx, cy, r * 1.8, 0, 2 * Math.PI);
        g.strokeStyle = "#ff2020"; g.lineWidth = 2.5; g.stroke();
      }
    }
    const key2 = this.el.querySelector("#eye-key");
    if (!sc) { key2.textContent = this.patch ? "Blue outline: the watched patch." : ""; return; }
    // the selected type's cells: unwatched as small dots, watched coloured by voltage
    let lo = Infinity, hi = -Infinity;
    if (vi >= 0) for (const w of sc.w) if (w >= 0) { const v = rec.v[vi * rec.nWatch + w]; lo = Math.min(lo, v); hi = Math.max(hi, v); }
    for (let j = 0; j < sc.n; j++) {
      const cx = L.ox[sc.e[j]] + sc.x[j] * L.s, cy = 16 + sc.y[j] * L.s;
      g.beginPath();
      if (sc.w[j] >= 0 && vi >= 0) {
        const v = rec.v[vi * rec.nWatch + sc.w[j]], u = hi > lo ? (v - lo) / (hi - lo) : 0.5;
        g.arc(cx, cy, r * 0.6, 0, 2 * Math.PI);
        g.fillStyle = `rgb(${Math.round(40 + 215 * u)},${Math.round(80 + 60 * (1 - Math.abs(u - 0.5) * 2))},${Math.round(255 - 215 * u)})`;
        g.fill(); g.strokeStyle = "#000"; g.lineWidth = 0.8; g.stroke();
      } else {
        g.arc(cx, cy, Math.max(1.2, r * 0.28), 0, 2 * Math.PI);
        g.fillStyle = "#e0501a"; g.fill();
      }
    }
    const nw = sc.w.filter(w => w >= 0).length;
    key2.innerHTML = `${esc(this.selType)}: ${sc.n} cells (orange dots, positions ${this.byName.get(this.selType).stage === "photoreceptors" ? "the assigned ommatidium" : "derived placement"})`
      + (nw && vi >= 0 ? `; ${nw} watched, coloured blue to red over ${fmt(lo, 2)} to ${fmt(hi, 2)} mV at this time` : "")
      + (this.patch ? "; blue outline: the watched patch" : "") + ".";
  }

  traceLayout() {
    const w = Math.max(200, this.el.clientWidth - 8), rh = 22, top = 4;
    let y = top, last = null;
    const pos = this.traces.map(r => {
      const sect = r.lptc ? "lptc" : "col";
      if (sect !== last) { y += 14; last = sect; }
      const p = { y }; y += rh; return p;
    });
    return { w, h: y + 6, rh, pos, x0: 82, x1: w - 96 };
  }

  drawTraces(t) {
    const L = this.traceLayout(), key = `${Math.round(t)},${L.w}`;
    if (key === this.traceKey) return;
    this.traceKey = key;
    const c = this.tcanvas, dpr = devicePixelRatio || 1, rec = this.rec;
    c.style.width = `${L.w}px`; c.style.height = `${L.h}px`;
    c.width = L.w * dpr; c.height = L.h * dpr;
    const g = c.getContext("2d"); g.scale(dpr, dpr);
    const dark = document.documentElement.dataset.theme === "dark";
    const fg = dark ? "#e4e2dc" : "#1d1f22", dim = dark ? "#8a8d92" : "#7d7a73", line = dark ? "#2a2d31" : "#dedad2";
    const tx = s => L.x0 + (L.x1 - L.x0) * s / rec.duration;
    let last = null;
    this.traces.forEach((r, k) => {
      const y = L.pos[k].y, h = L.rh - 4;
      const sect = r.lptc ? "lptc" : "col";
      if (sect !== last) {
        last = sect;
        g.fillStyle = dim; g.font = "600 10px sans-serif";
        g.fillText(sect === "lptc" ? "LOBULA PLATE TANGENTIAL CELLS, BY SIDE" : "COLUMNS, PHOTORECEPTOR TO T4/T5", 0, y - 4);
      }
      g.strokeStyle = line; g.lineWidth = 1; g.beginPath(); g.moveTo(L.x0, y + h + 1.5); g.lineTo(L.x1, y + h + 1.5); g.stroke();
      g.fillStyle = fg; g.font = "11px sans-serif"; g.fillText(r.label, 0, y + 9);
      g.fillStyle = dim; g.font = "9px sans-serif";
      g.fillText(r.kind === "v" ? `${r.watched.length} watched` : `${r.rows.length} cells`, 0, y + h);
      if (r.kind === "none") {
        g.fillStyle = dim; g.font = "10px sans-serif";
        g.fillText("graded in the model and no voltage recorded: nothing to show", L.x0 + 8, y + h - 5);
        return;
      }
      const flat = !(r.hi - r.lo > (r.kind === "v" ? 0.01 : 0));
      // voltage rows span at least MIN_SPAN mV, so a 0.1 mV ripple does not look like a response
      const mid = (r.hi + r.lo) / 2, span = r.kind === "v" ? Math.max(MIN_SPAN, r.hi - r.lo) : r.hi - r.lo;
      const lo = r.kind === "v" ? mid - span / 2 : r.lo;
      g.strokeStyle = r.kind === "v" ? "#2f6fd0" : "#e0501a"; g.lineWidth = 1.2; g.beginPath();
      const n = r.data.length;
      for (let i = 0; i < n; i++) {
        const s = r.kind === "v" ? rec.vStep[i] * rec.ts : (i + 0.5) * RATE_BIN;
        const u = flat ? 0.5 : (r.data[i] - lo) / span;
        const X = tx(s), Y = y + h - u * h;
        g[i ? "lineTo" : "moveTo"](X, Y);
      }
      g.stroke();
      // value now and range
      let now;
      if (r.kind === "v") now = r.data[Math.max(0, rec.vAt(t))];
      else now = r.data[Math.min(n - 1, Math.floor(t / RATE_BIN))];
      g.fillStyle = fg; g.font = "11px ui-monospace, Menlo, monospace";
      g.fillText(r.kind === "v" ? `${fmt(now, 2)} mV` : r.total ? `${fmt(now, 1)} Hz` : "no spike", L.x1 + 6, y + 9);
      g.fillStyle = dim; g.font = "9px ui-monospace, Menlo, monospace";
      if (r.kind === "v" || r.total)
        g.fillText(flat ? "flat" : r.kind === "v" ? `${fmt(r.lo, 2)}…${fmt(r.hi, 2)}` : `0…${fmt(r.hi, 0)} Hz`, L.x1 + 6, y + h);
    });
    const X = tx(t);
    g.strokeStyle = "#e0501a"; g.lineWidth = 1; g.beginPath(); g.moveTo(X, 14); g.lineTo(X, L.h); g.stroke();
  }

  updateNow(t) {
    const rec = this.rec, vi = rec.nWatch ? rec.vAt(t) : -1;
    if (vi === this.nowV) return;
    this.nowV = vi;
    if (vi < 0) return;
    for (const td of this.el.querySelectorAll("#eye-coltable td[data-v]")) {
      const ty = this.byName.get(td.dataset.v);
      if (!ty || !ty.watched.length) continue;
      let m = 0; for (const w of ty.watched) m += rec.v[vi * rec.nWatch + w];
      td.textContent = `${fmt(m / ty.watched.length, 1)} (${ty.watched.length})`;
    }
  }

  traceClick(ev) {
    const L = this.traceLayout(), b = this.tcanvas.getBoundingClientRect(), px = ev.clientX - b.left;
    if (px < L.x0 || px > L.x1) return;
    this.onTime((px - L.x0) / (L.x1 - L.x0) * this.rec.duration);
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
    this.pickOmm(e, best);
  }

  // the ommatidium a photoreceptor cell is assigned to, or null
  ommatidiumOf(bodyId) { return this.g ? this.ommOf.get(bodyId) || null : null; }

  pickOmm(e, best) {
    this.pick = { e, o: best };
    this.drawKey = "";
    const cells = this.cells[e].get(best) || [];
    // columnar cells placed on this ommatidium
    const placed = [];
    if (this.cols) {
      const c = this.cols.cells;
      for (let j = 0; j < c.column.length; j++)
        if (c.column[j] === best && c.eye[j] === e) placed.push({ bodyId: c.bodyId[j], type: this.cols.types[c.type[j]] });
    }
    const row = c => { const i = this.atlas.index.get(c.bodyId), r = this.rowOf.get(c.bodyId);
      const w = r === undefined ? -1 : this.rec.watchIndex(r);
      return `<tr${i === undefined ? "" : ` class="link" data-i="${i}"`}><td>${c.bodyId}</td><td>${esc(c.type)}</td><td class="dim">${w >= 0 ? "watched" : ""}</td></tr>`; };
    this.pickList = [...cells, ...placed];
    this.el.querySelector("#eye-pick").innerHTML = `<h3>${e ? "Right" : "Left"} eye, ommatidium ${best}</h3>
      <div>${this.g.pale[e ? "right" : "left"][best] ? "pale" : "yellow"}; ${this.g.pixels[best]} render pixels</div>
      ${cells.length ? `<div>${cells.length} photoreceptor cells assigned to it <span class="chip inferred">derived topology, inferred alignment</span> <a href="#" data-all>highlight all</a></div>
        <table>${cells.map(row).join("")}</table>`
        : `<div class="dim">No photoreceptor cell is assigned to this ommatidium (the derived assignment does not cover every ommatidium).</div>`}
      ${placed.length ? `<div>${placed.length} columnar cells placed nearest to it <span class="chip inferred">derived</span></div><table>${placed.map(row).join("")}</table>` : ""}`;
    this.onHighlight(this.pickIds());
  }

  pickIds() {
    if (!this.pick) return [];
    return (this.pickList || []).map(c => this.atlas.index.get(c.bodyId)).filter(i => i !== undefined);
  }
}
