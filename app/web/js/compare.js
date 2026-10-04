// A stimulated run against its matched control: same model, seed and start, no
// stimulus. Everything here is computed in the page from the two recordings
// (derived from this recording), never read from the model.
const same = (a, b) => JSON.stringify(a) === JSON.stringify(b);
// configurations that give the same run without kicks (kick_rng only changes kicks)
export const sameModel = (a, b) => same({ ...a, kick_rng: undefined }, { ...b, kick_rng: undefined });

// controls in the catalogue that can stand beside this run, best first
export function controlsFor(cat, entry) {
  if (!entry || entry.control) return [];
  return cat.recordings
    .filter(r => r.control && r.status === "complete" && r.id !== entry.id
      && sameModel(r.config, entry.config) && (r.duration_ms || 0) >= (entry.duration_ms || 0))
    .sort((x, y) => (y.commit === entry.commit) - (x.commit === entry.commit)
      || (y.id.split("/")[0] === entry.id.split("/")[0]) - (x.id.split("/")[0] === entry.id.split("/")[0])
      || String(y.created).localeCompare(String(x.created)));
}

// stimulus window (ms): first event on to last event off; a genotype alone is the whole run
export function stimWindow(rec) {
  const res = rec.manifest.protocol && rec.manifest.protocol.resolved;
  if (!res) return null;
  if (res.events.length) {
    const on = Math.min(...res.events.map(e => e.on_step)), off = Math.max(...res.events.map(e => e.off_step));
    return { t0: on * rec.ts, t1: Math.min(rec.duration, off * rec.ts), onStep: on, genotypeOnly: false };
  }
  return res.genotype.length ? { t0: 0, t1: rec.duration, onStep: 0, genotypeOnly: true } : null;
}

// first step at which the two spike trains differ (null if identical up to the shorter end)
export function firstDivergence(a, b) {
  const ka = a.spikeKeys(), kb = b.spikeKeys(), n = a.manifest.n_rows;
  const end = Math.min(a.duration, b.duration) / a.ts;
  const m = Math.min(ka.length, kb.length);
  for (let i = 0; i < m; i++) {
    if (ka[i] !== kb[i]) return Math.floor(Math.min(ka[i], kb[i]) / n);
  }
  const rest = ka.length > m ? ka[m] : kb.length > m ? kb[m] : null;
  if (rest === null) return null;
  const s = Math.floor(rest / n);
  return s < end ? s : null;
}

// thorax pose at time t: position (mm) and yaw (rad); forward is the thorax +x axis
// (the head sits 0.57 mm along it in the flybody model)
function pose(rec, t) {
  const NB = rec.nBodies, f = Math.max(0, rec.frameAt(t)), o = (f * NB + 1) * 3, q = (f * NB + 1) * 4;
  const [w, x, y, z] = rec.xquat.subarray(q, q + 4);
  return { p: rec.xpos.subarray(o, o + 3), yaw: Math.atan2(2 * (w * z + x * y), 1 - 2 * (y * y + z * z)) };
}

export function movement(rec, t0, t1) {
  const a = pose(rec, t0), b = pose(rec, t1);
  const dx = b.p[0] - a.p[0], dy = b.p[1] - a.p[1], c = Math.cos(a.yaw), s = Math.sin(a.yaw);
  let turn = (b.yaw - a.yaw) * 180 / Math.PI;
  turn = ((turn + 540) % 360) - 180;
  return { forward: c * dx + s * dy, left: -s * dx + c * dy, turn, height0: a.p[2], height1: b.p[2] };
}

export const readoutTypes = rec => (((rec.manifest.protocol || {}).expect || {}).readout || {}).type || [];

// Readout cells the reconstructors flag as incompletely traced (statusLabel "Hard
// to trace" or "Partially traced"): atlas index -> instance. scripts/assay_pathways.py
// drops these from its readouts (F-DATA-3), and so does app/tools/score_library.py.
export async function incompleteReadout(atlas, types) {
  const out = new Map();
  for (const ty of types) {
    const code = atlas.vocab.type.indexOf(ty);
    if (code < 0) continue;
    for (const i of atlas.ofType(code)) {
      const m = (await atlas.meta(i)) || {};
      if (/Hard to trace|Partially/.test(m.statusLabel || "")) out.set(i, m.instance || String(atlas.bodyId[i]));
    }
  }
  return out;
}

// `opts.win` and `opts.criterion` let a sham run be read over another run's
// window and against another run's rule (the noise floor)
export function compare(run, ctrl, atlas, rowToAtlas, opts = {}) {
  const win = opts.win || stimWindow(run);
  if (!win) return null;
  const n = run.manifest.n_rows, D = run.duration;
  const periods = { before: [0, win.t0], during: [win.t0, win.t1], after: [win.t1, D] };
  const rate = {};
  for (const [k, [t0, t1]] of Object.entries(periods)) {
    const s = (t1 - t0) / 1000;
    rate[k] = s > 0 ? { run: run.countsIn(t0, t1), ctrl: ctrl.countsIn(t0, t1), s } : null;
  }
  const d = rate.during, delta = new Float32Array(n);
  for (let r = 0; r < n; r++) delta[r] = (d.run[r] - d.ctrl[r]) / d.s;
  // per atlas cell, for the map: NaN where the scan cell is not simulated
  const atlasDelta = new Float32Array(atlas.n).fill(NaN);
  for (let r = 0; r < n; r++) if (rowToAtlas[r] >= 0) atlasDelta[rowToAtlas[r]] = delta[r];
  const div = firstDivergence(run, ctrl);
  // targeted rows
  const res = run.manifest.protocol.resolved, targeted = new Set();
  for (const e of [...res.genotype, ...res.events]) for (const r of e.rows || []) targeted.add(r);
  // responders: largest absolute change in rate during the stimulus
  const order = Array.from({ length: n }, (_, r) => r).filter(r => d.run[r] !== d.ctrl[r]);
  order.sort((x, y) => Math.abs(delta[y]) - Math.abs(delta[x]));
  const top = order.slice(0, 15).map(r => ({ r, i: rowToAtlas[r], run: d.run[r] / d.s, ctrl: d.ctrl[r] / d.s, delta: delta[r], targeted: targeted.has(r) }));
  let up = 0, down = 0;
  for (const r of order) { if (delta[r] >= 1) up++; else if (delta[r] <= -1) down++; }
  // readout types named by the protocol's expectation; `opts.exclude` (atlas index ->
  // name) drops cells flagged as incompletely traced, as the model's assays do
  const want = new Set(opts.readout || readoutTypes(run));
  const byType = new Map(), dropped = new Map();
  for (let r = 0; r < n; r++) {
    const i = rowToAtlas[r]; if (i < 0) continue;
    const ty = atlas.typeName(i);
    if (!want.has(ty)) continue;
    const m = opts.exclude && opts.exclude.has(i) ? dropped : byType;
    if (!m.has(ty)) m.set(ty, []);
    m.get(ty).push(m === dropped ? opts.exclude.get(i) : r);
  }
  const mean = (p, which, rows) => !rate[p] ? null : rows.reduce((s, r) => s + rate[p][which][r], 0) / rows.length / rate[p].s;
  const readout = [...want].map(ty => {
    const rows = byType.get(ty) || [], excluded = dropped.get(ty) || [];
    if (!rows.length) return { type: ty, n: 0, excluded };
    const o = { type: ty, n: rows.length, excluded, targeted: rows.filter(r => targeted.has(r)).length };
    for (const p of ["before", "during", "after"]) o[p] = { run: mean(p, "run", rows), ctrl: mean(p, "ctrl", rows) };
    return o;
  });
  const spikes = p => rate[p] ? [rate[p].run.reduce((s, x) => s + x, 0), rate[p].ctrl.reduce((s, x) => s + x, 0)] : null;
  const move = { run: movement(run, win.t0, win.t1), ctrl: movement(ctrl, win.t0, win.t1) };
  return {
    criterion: score("criterion" in opts ? opts.criterion : (run.manifest.protocol.expect || {}).criterion, { move, readout }),
    move,
    win, during: d, delta, atlasDelta, div, divOk: div === null || div >= win.onStep, targeted, top, up, down,
    changed: order.length, readout, spikes: { before: spikes("before"), during: spikes("during"), after: spikes("after") },
  };
}

// the protocol's pass/fail rule, declared in the protocol before the run was viewed
const METRICS = {
  readout_delta_hz: x => {
    const r = x.readout.filter(o => o.n);
    if (!r.length) return null;
    const n = r.reduce((s, o) => s + o.n, 0);
    return r.reduce((s, o) => s + o.n * (o.during.run - o.during.ctrl), 0) / n;
  },
  forward_mm_vs_control: x => x.move.run.forward - x.move.ctrl.forward,
  turn_left_deg_vs_control: x => x.move.run.turn - x.move.ctrl.turn,
};

function score(c, x) {
  if (!c) return null;
  const f = METRICS[c.metric];
  if (!f) return { ...c, value_measured: null, pass: null, note: `metric ${c.metric} unknown to this page` };
  const v = f(x);
  const pass = v === null ? null : c.op === ">=" ? v >= c.value : c.op === "<=" ? v <= c.value : null;
  return { ...c, value_measured: v, pass };
}
