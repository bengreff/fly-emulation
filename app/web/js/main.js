// Fly Workbench: load a recording and the scan's atlas, then drive the body,
// brain map, traces and inspector from one clock.
import { fetchJSON } from "./io.js";
import { Recording } from "./recording.js";
import { Atlas } from "./atlas.js";
import { BodyView } from "./body.js";
import { BrainView } from "./brain.js";
import { Traces } from "./traces.js";
import { Inspector, esc, chip, approxChip } from "./inspector.js";
import { controlsFor, compare, stimWindow, sameModel, incompleteReadout, readoutTypes } from "./compare.js";
import { SessionPanel } from "./session.js";
import { EyePanel } from "./eye.js";

const $ = s => document.querySelector(s);
const params = new URLSearchParams(location.search);
const state = { t: Number(params.get("t") || 0), playing: false, speed: 0.25, sel: null };

function status(msg) { $("#status").textContent = msg; }

function setTheme(dark) {
  document.documentElement.dataset.theme = dark ? "dark" : "light";
  state.dark = dark;
  app.body && app.body.setTheme(dark);
  app.brain && app.brain.setTheme(dark);
  app.traces && app.traces.setTheme(dark);
}

const app = {};

async function main() {
  setTheme(params.get("theme") ? params.get("theme") === "dark" : matchMedia("(prefers-color-scheme: dark)").matches);
  status("loading catalogue…");
  const cat = await fetchJSON("catalog.json");
  const sel = $("#run");
  for (const r of cat.recordings) {
    const o = document.createElement("option");
    o.value = r.id;
    o.textContent = `${r.verdict ? r.verdict + ": " : ""}${r.title}${r.flags && r.flags.length ? " [" + r.flags.join(", ") + "]" : ""}`;
    sel.appendChild(o);
  }
  const recId = params.get("rec") || (cat.recordings[0] && cat.recordings[0].id);
  if (!recId) { status("no recordings in the catalogue"); return; }
  sel.value = recId;
  sel.onchange = () => { params.set("rec", sel.value); params.delete("t"); params.delete("sel"); location.search = params.toString(); };
  const entry = cat.recordings.find(r => r.id === recId);
  if (!entry) { status(`recording ${recId} not in the catalogue`); return; }

  status("loading recording…");
  const rec = await Recording.load(entry.path, (k, n) => status(`loading recording: chunk ${k} of ${n}`));
  app.rec = rec;
  const scan = rec.manifest.config.scan || "male-cns:v1.0";
  const at = cat.atlases.find(a => `${a.scan}:${a.version}` === scan);
  if (!at) { status(`no atlas for ${scan}`); return; }
  status(`loading ${scan} atlas…`);
  const atlas = await Atlas.load(at.path);
  app.atlas = atlas;
  $("#scan").textContent = `${atlas.info.scan} ${atlas.info.version}`;

  // body
  const bodyEntry = cat.bodies.find(b => b.id === rec.manifest.config.body);
  app.body = new BodyView($("#body"));
  app.body.setTheme(state.dark);
  if (bodyEntry) await app.body.load(bodyEntry.path, rec);
  $("#follow").onchange = e => { app.body.follow = e.target.checked; };

  // brain
  status("building brain map…");
  app.brain = new BrainView($("#brain"), atlas);
  app.brain.setTheme(state.dark);
  app.brain.bindRecording(rec);
  const rowOfAtlas = new Map();
  for (let r = 0; r < rec.rowBodyId.length; r++) rowOfAtlas.set(rec.rowBodyId[r], r);
  app.rowOfAtlas = rowOfAtlas;

  // traces
  app.traces = new Traces($("#traces"), t => { state.t = t; });
  app.traces.bind(rec, atlas, app.brain.rowToAtlas, state.dark);

  // inspector
  app.inspector = new Inspector($("#inspector"), i => select(i), code => showType(code));
  app.inspector.bind(atlas, rec, rowOfAtlas);
  app.inspector.clear();

  wireControls(cat);
  protocolTargets(rec);
  runPanel(rec, atlas, entry);
  brainCount(rec, atlas);
  window.addEventListener("resize", resize);
  resize();
  await setupCompare(cat, entry);
  app.session = new SessionPanel($("#tab-session"), { rec });
  app.eye = new EyePanel($("#tab-eye"), { onSelect: i => select(i), onHighlight: ids => app.brain.setHighlight(ids) });
  if (bodyEntry) await app.eye.load(`${bodyEntry.path}/eye.json`, rec, atlas);
  app.inspector.eyeOf = bid => app.eye.ommatidiumOf(bid);
  app.inspector.onOmm = (e, o) => { showTab("eye"); app.eye.pickOmm(e, o); };
  if (rec.manifest.status === "recording") followGrowth(atlas, entry);
  if (params.get("tab")) showTab(params.get("tab"));
  const layout = params.get("view");
  if (layout) { app.brain.setLayout(layout); $(`#layout [data-v="${layout}"]`)?.classList.add("on"); }
  const colour = params.get("colour");
  if (colour) { $("#colour").value = colour; app.brain.setColour(colour); }
  legend();
  if (params.get("sel")) {
    const i = atlas.index.get(Number(params.get("sel")));
    if (i !== undefined) await select(i);
  }
  status("");
  document.body.classList.add("ready");
  requestAnimationFrame(tick);
}

// a run still recording (a live session, or a run started elsewhere): load new
// chunks as the recorder writes them
function followGrowth(atlas, entry) {
  const step = async () => {
    let n = 0;
    try { n = await app.rec.refresh(); } catch { /* manifest mid-write; next time */ }
    if (n) { protocolTargets(app.rec); legend(); app.traces.redraw(); }
    if (app.rec.manifest.status === "recording") setTimeout(step, 3000);
    else runPanel(app.rec, atlas, entry);
  };
  setTimeout(step, 3000);
}

function resize() {
  app.body.resize(); app.brain.resize(); app.traces.redraw();
  $("#legend").style.top = `${$("#brain").parentElement.querySelector(".head").offsetHeight + 14}px`;
}

// What the map counts, split the way the model's builder splits the scan
// (atlas.json counts, written by app/build/atlas.py), and how this run joins it.
function brainCount(rec, atlas) {
  const c = atlas.info.counts, f = n => n.toLocaleString(), m = rec.manifest;
  $("#brain-scan").textContent = `${atlas.info.scan} ${atlas.info.version}`;
  if (!c) { $("#brain-count").textContent = `${f(atlas.n)} neurons in the scan; counts not recorded in this atlas (rebuild it)`; return; }
  const list = o => Object.entries(o).map(([k, v]) => `${k} ${f(v)}`).join("; ");
  const ran = m.n_model_neurons || m.n_rows;
  const joined = app.brain.unjoined ? `${f(app.brain.unjoined)} rows not in the atlas`
    : m.join ? "every row found in the atlas; bodyIds assigned by table order, type sequence checked" : "every row joined by bodyId";
  const run = m.n_rows === c.in_model && ran === c.in_model
    ? `this run simulated all ${f(ran)}; ${joined}`
    : m.n_rows < ran
      ? `this run simulated ${f(ran)} and recorded ${f(m.n_rows)}; ${joined}`
      : `<span class="warn">this run simulated ${f(ran)}, not ${f(c.in_model)}</span>; ${joined}`;
  $("#brain-count").innerHTML =
    `<b>${f(c.in_model)} in the model</b> = ${f(c.in_model_traced)} traced + `
    + `<abbr title="${esc(`kept because they carry a cell type. Status: ${list(c.in_model_untraced_by_status)}. Types: ${list(c.in_model_untraced_top_types || {})}`)}">${f(c.in_model_untraced_typed)} untraced but typed</abbr>`
    + ` · <abbr title="${esc(`${c.scan_only_what}. Status: ${list(c.scan_only_by_status)}`)}">${f(c.scan_only)} scan only</abbr> (untyped fragments, drawn, never simulated)`
    + ` · <abbr title="${esc(`${c.cache_what}. Policy: ${c.policy}`)}">${f(c.cache)} in the scan</abbr><br>${run}`;
}

let last = performance.now();
function tick(now) {
  const dt = Math.min(100, now - last); last = now;
  const rec = app.rec;
  if (state.playing) {
    state.t += dt * state.speed;
    if (state.t > rec.duration) state.t = 0;
  }
  state.t = Math.max(0, Math.min(rec.duration, state.t));
  app.body.pose(state.t);
  app.brain.setTime(state.t);
  app.body.render();
  app.brain.render();
  app.traces.draw(state.t);
  if (app.eye) app.eye.draw(state.t);
  const gl = app.brain.groupLabels();
  const key = gl.map(l => `${l.x | 0},${l.y | 0}`).join();
  if (key !== tick.glKey) {
    tick.glKey = key;
    $("#glabels").innerHTML = gl.map(l => `<span style="left:${l.x}px;top:${l.y - 14}px">${esc(l.text)}</span>`).join("");
  }
  $("#time").textContent = `${state.t.toFixed(1)} / ${rec.duration.toFixed(0)} ms`;
  $("#scrub").value = String(rec.duration ? state.t / rec.duration * 1000 : 0);
  $("#bodyinfo").textContent = (rec.manifest.preparation || {}).coupling === "brain_only"
    ? "brain only: body not stepped, pose is the start pose"
    : app.body.thoraxHeight !== undefined ? `thorax ${app.body.thoraxHeight.toFixed(2)} mm` : "";
  requestAnimationFrame(tick);
}

function updateURL() {
  params.set("t", state.t.toFixed(1));
  if (state.sel !== null) params.set("sel", String(app.atlas.bodyId[state.sel])); else params.delete("sel");
  params.set("view", app.brain.layoutName);
  params.set("colour", app.brain.colourBy);
  history.replaceState(null, "", "?" + params.toString());
}

async function select(i) {
  state.sel = i;
  showTab("neuron");
  app.brain.setHighlight([i]);
  const row = app.rowOfAtlas.get(app.atlas.bodyId[i]);
  app.traces.select(row === undefined ? null : row, app.atlas.typeName(i) || String(app.atlas.bodyId[i]));
  const edges = await app.inspector.show(i);
  if (edges && state.sel === i) app.brain.setPartners(i, edges);
  updateURL();
}

function showType(code) {
  const ids = app.atlas.ofType(code);
  app.brain.setHighlight(ids);
  status(`${ids.length} neurons of type ${app.atlas.vocab.type[code]} highlighted`);
}

function legend() {
  const b = app.brain, el = $("#legend");
  el.innerHTML = b.legend.slice(0, 24).map(e =>
    `<div class="lg ${b.hidden.has(e.name) ? "off" : ""}" data-name="${esc(e.name)}"><i style="background:#${e.colour.toString(16).padStart(6, "0")}"></i>${esc(e.name)} <span>${e.n.toLocaleString()}</span></div>`).join("")
    + (b.legend.length > 24 ? `<div class="dim">+${b.legend.length - 24} more</div>` : "")
    + (app.stimCount ? `<div class="lg" title="cells the protocol stimulates, silences or kicks"><i class="stimkey"></i>targeted <span>${app.stimCount.toLocaleString()}</span></div>` : "")
    + `<div class="dim">${b.shown.toLocaleString()} of ${app.atlas.n.toLocaleString()} drawn</div>`;
}

// cells the protocol acts on: ringed on the map, listed in the inspector
function protocolTargets(rec) {
  const res = rec.manifest.protocol && rec.manifest.protocol.resolved, targets = new Map(), stim = new Set();
  if (res) for (const e of [...res.genotype, ...res.events]) for (const r of e.rows || []) {
    if (!targets.has(r)) targets.set(r, []);
    targets.get(r).push(e);
    const i = app.brain.rowToAtlas[r];
    if (i >= 0) stim.add(i);
  }
  app.inspector.targets = targets;
  app.brain.setStimulated([...stim]);
  app.stimCount = stim.size;
}

// the matched control: a complete run with the same configuration and no stimulus
async function setupCompare(cat, entry) {
  const el = $("#tab-compare"), rec = app.rec;
  const go = id => { params.set("rec", id); params.delete("sel"); params.delete("ctrl"); location.search = params.toString(); };
  if (entry.control) {
    const users = cat.recordings.filter(r => !r.control && r.n_events + r.n_genotype > 0 && sameModel(r.config, entry.config));
    el.innerHTML = `<h2>A control run</h2><div class="sub">No stimulus. These runs share its model, seed and start, and compare themselves against it:</div>
      <table>${users.map(r => `<tr class="link" data-rec="${esc(r.id)}"><td>${esc(r.id)}</td><td>${esc(r.title)}</td></tr>`).join("")}</table>`;
    el.onclick = e => { const d = e.target.closest("[data-rec]"); if (d) go(d.dataset.rec); };
    return;
  }
  if (!stimWindow(rec)) { el.innerHTML = `<div class="empty">This recording has no protocol, so there is nothing to compare.</div>`; return; }
  const cands = controlsFor(cat, entry);
  if (!cands.length) {
    el.innerHTML = `<div class="empty">No matched control in the catalogue (a complete run with the same configuration and no stimulus). Record app/protocols/control.json with this run's configuration.</div>${trialsHTML(entry)}`;
    return;
  }
  const pick = cands.find(c => c.id === params.get("ctrl")) || cands[0];
  status("loading the control…");
  const ctrl = await Recording.load(pick.path, (k, n) => status(`loading the control: chunk ${k} of ${n}`));
  const exclude = await incompleteReadout(app.atlas, readoutTypes(rec));
  const c = compare(rec, ctrl, app.atlas, app.brain.rowToAtlas, { exclude });
  app.ctrl = ctrl;
  app.brain.setDelta(c.atlasDelta);
  $('#colour option[value="delta"]').disabled = false;
  app.traces.setControl(ctrl);
  app.inspector.cmp = c;
  // the noise floor: a sham run (a few forced spikes in one unrelated cell) read
  // over this run's window, against this run's rule
  const sham = entry.role === "sham" ? null : cat.recordings.find(r => r.role === "sham" && r.status === "complete"
    && sameModel(r.config, entry.config));
  let floor = null;
  if (sham) {
    status("loading the sham run…");
    const sr = await Recording.load(sham.path);
    floor = compare(sr, ctrl, app.atlas, app.brain.rowToAtlas, { win: c.win, criterion: c.criterion, readout: c.readout.map(o => o.type), exclude });
    floor.entry = sham;
    floor.onset = stimWindow(sr).t0;
  }
  el.innerHTML = compareHTML(c, rec, pick, cands, entry, floor);
  $("#ctrl-pick").onchange = e => { params.set("ctrl", e.target.value); location.search = params.toString(); };
  el.onclick = e => { const d = e.target.closest("[data-i]"); if (d && Number(d.dataset.i) >= 0) select(Number(d.dataset.i)); };
}

function verdictHTML(cr) {
  if (!cr) return `<span class="verdict none">no criterion declared</span>`;
  if (cr.pass === null) return `<span class="verdict none">not scored</span>`;
  return cr.pass ? `<span class="verdict pass">PASS</span>` : `<span class="verdict fail">FAIL</span>`;
}

// the same protocol recorded at several seeds (score_library.py "trials"): one trial of a
// threshold pathway can sit far from the mean, so show where this one falls
function trialsHTML(entry) {
  const g = entry.trials;
  if (!g) return "";
  const seed = entry.config && entry.config.seed;
  const vals = g.seeds.map((s, i) => s === seed ? `<b>${g.readout_hz[i].toFixed(1)}</b>` : g.readout_hz[i].toFixed(1)).join(", ");
  const cm = g.criterion_on_mean;
  return `<h3>This protocol at ${g.seeds.length} seeds <span class="chip measured">score_library.py</span></h3>
    <div>readout, Hz (this run in bold; seeds ${esc(g.seeds.join(", "))}): ${vals}; mean ${g.readout_hz_mean.toFixed(2)}, SD ${g.readout_hz_sd.toFixed(2)}${g.excluded_incomplete.length ? ` (without ${esc(g.excluded_incomplete.join(", "))}, incompletely traced)` : ""}</div>
    ${cm ? `<div>${cm.pass ? `<span class="verdict pass">PASS</span>` : `<span class="verdict fail">FAIL</span>`} on the mean: ${esc(cm.what || cm.metric || "")} ${cm.value_measured.toFixed(2)} ${esc(cm.units || "Hz")} vs control (SD ${(cm.sd ?? 0).toFixed(2)}); needs ${esc(cm.op)} ${cm.value}${cm.threshold_met === undefined ? "" : cm.threshold_met ? ", met" : ", not met"} <span class="chip guessed" title="${esc(cm.rule)}">post hoc rule</span></div>
    ${!cm.values ? "" : `<div class="dim">per seed: ${cm.values.map((v, i) => g.seeds[i] === seed ? `<b>${v.toFixed(2)}</b>` : v.toFixed(2)).join(", ")}${cm.sham_values ? `; the same seed's sham: ${cm.sham_values.map(v => v === null ? "–" : v.toFixed(2)).join(", ")}` : ""}</div>`}
    ${cm.p_sham === undefined ? "" : cm.p_sham === null ? `<div class="warnline">no sham at these seeds, so the mean is judged on its threshold alone</div>`
      : `<div class="${cm.within_noise ? "warnline" : "dim"}">against the same seeds' shams (exact sign-flip test, ${cm.n_pairs} pairs): p = ${cm.p_sham.toFixed(3)}${cm.within_noise ? ", so the mean cannot be told from noise" : ", beyond noise"}</div>`}` : ""}`;
}

function compareHTML(c, rec, pick, cands, entry, floor) {
  const f1 = v => v === null || v === undefined ? "–" : v.toFixed(1), f2 = v => v.toFixed(2);
  const ex = rec.manifest.protocol.expect || {}, cr = c.criterion, w = c.win;
  const sign = v => (v > 0 ? "+" : "") + f1(v);
  const fc = floor && floor.criterion, fv = fc ? fc.value_measured : null;
  // the scorer's floor (score_library.py: every sham with this configuration) when there is one
  const sv = entry.sham_values && entry.sham_values.length > 1 ? entry.sham_values : null;
  const svMax = sv ? Math.max(...sv.map(Math.abs)) : null;
  const inNoise = cr && cr.value_measured !== null && (sv ? Math.abs(cr.value_measured) <= svMax
    : fv !== null && Math.abs(cr.value_measured) <= Math.abs(fv));
  const mv = k => floor ? `<td class="num">${f2(floor.move.run[k] - floor.move.ctrl[k])}</td>` : "";
  const prep = rec.manifest.preparation;
  return `<h2>Against its control</h2>
    ${prep && prep.coupling === "brain_only" ? `<div class="warnline">${esc(prep.desc)}</div>` : ""}
    <div class="sub">control <select id="ctrl-pick">${cands.map(x => `<option value="${esc(x.id)}" ${x.id === pick.id ? "selected" : ""}>${esc(x.id)}</option>`).join("")}</select></div>
    ${pick.commit === entry.commit ? "" : `<div class="warnline">control recorded at commit ${esc((pick.commit || "?").slice(0, 7))}, this run at ${esc((entry.commit || "?").slice(0, 7))}; the identity check below is what makes them comparable</div>`}
    <h3>Matched?</h3>
    <div>${c.div === null ? "spike trains identical throughout" : `first difference at ${(c.div * rec.ts).toFixed(1)} ms (step ${c.div}); stimulus starts at step ${w.onStep}`}
      ${c.divOk ? `<span class="chip measured">identical before the stimulus</span>` : `<span class="verdict fail">differs before the stimulus: not a matched control</span>`}</div>
    ${c.div === null ? `<div class="warnline">No spike anywhere differs from the control: the stimulus never changed when any cell crossed threshold (voltages below threshold may still differ), so nothing downstream could respond.</div>` : ""}
    <h3>Expectation</h3>
    <div>${esc(ex.text || "not stated")}</div>
    <div class="dim">${esc(ex.source || "no source")}</div>
    <div style="margin:6px 0">${verdictHTML(cr)} ${cr ? `${esc(cr.what)}: <b>${cr.value_measured === null ? "n/a" : f2(cr.value_measured)} ${esc(cr.units)}</b>; pass needs ${esc(cr.op)} ${cr.value} <span class="chip guessed" title="${esc(cr.basis)}">guessed threshold</span>` : ""}</div>
    ${sv && cr && c.div !== null ? `<div class="${inNoise ? "warnline" : "dim"}">${sv.length} sham runs give ${sv.map(f2).join(", ")} ${esc(cr.units)} on the same measure (largest size ${f2(svMax)}; ${!entry.shams_distinct ? "" : entry.shams_distinct < sv.length ? `only ${entry.shams_distinct} distinct: the others repeat another sham's spike trains exactly, outside the forced cells; ` : "all distinct; "}scored by score_library.py)${inNoise ? ": this result is no larger, so it cannot be told from noise" : ": this result is larger than every sham"}.</div>`
    : fc && c.div !== null ? `<div class="${inNoise ? "warnline" : "dim"}">The sham run gives ${fv === null ? "n/a" : f2(fv)} ${esc(cr.units)} on the same measure${inNoise ? ": this result is no larger than the sham's, so it cannot be told from noise (one sham sample)" : " (one sham sample)"}.</div>` : ""}
    <div class="dim">${esc(ex.status || "")}</div>
    ${trialsHTML(entry)}
    <h3>Readout cells <span class="chip measured">this run</span></h3>
    <table><tr><td></td><td class="num">n</td><td class="num">before</td><td class="num">during</td><td class="num">after</td></tr>
    ${c.readout.map(o => o.n ? `<tr><td>${esc(o.type)}${o.targeted ? ` <span class="dim">(${o.targeted} targeted)</span>` : ""}</td><td class="num">${o.n}</td>${["before", "during", "after"].map(p => `<td class="num">${o[p] ? `${f1(o[p].run)} <span class="dim">/ ${f1(o[p].ctrl)}</span>` : "–"}</td>`).join("")}</tr>`
      : `<tr><td>${esc(o.type)}</td><td colspan="4">${o.excluded.length ? "only incompletely traced cells" : "not in this model"}</td></tr>`).join("")}</table>
    <div class="dim">Mean Hz per cell, this run / control. Stimulus window ${w.t0.toFixed(0)} to ${w.t1.toFixed(0)} ms.${c.readout.some(o => o.excluded.length) ? ` Excluded as incompletely traced (the model's assay rule, F-DATA-3): ${esc(c.readout.flatMap(o => o.excluded).join(", "))}.` : ""}</div>
    <h3>Body during the stimulus <span class="chip measured">this run</span></h3>
    <table><tr><td></td><td class="num">run</td><td class="num">control</td><td class="num">diff.</td>${floor ? `<td class="num" title="the sham run minus the control, same window">sham</td>` : ""}</tr>
    ${[["forward, mm", "forward"], ["left, mm", "left"], ["turn left, deg", "turn"]].map(([l, k]) =>
      `<tr><td>${l}</td><td class="num">${f2(c.move.run[k])}</td><td class="num">${f2(c.move.ctrl[k])}</td><td class="num">${f2(c.move.run[k] - c.move.ctrl[k])}</td>${mv(k)}</tr>`).join("")}
    <tr><td title="thorax height at stimulus on and off">height, mm</td><td class="num">${f2(c.move.run.height0)} to ${f2(c.move.run.height1)}</td><td class="num">${f2(c.move.ctrl.height0)} to ${f2(c.move.ctrl.height1)}</td><td></td></tr></table>
    <div class="dim">Thorax displacement from stimulus on to off, in the body frame at onset; forward is the thorax +x axis (the head's direction in the flybody model).</div>
    <h3>Network <span class="chip measured">this run</span></h3>
    <table><tr><td>spikes during</td><td>${c.spikes.during[0].toLocaleString()} here, ${c.spikes.during[1].toLocaleString()} in the control</td></tr>
    <tr><td>cells changed</td><td>${c.changed.toLocaleString()} with any change in spike count during the stimulus; ${c.up.toLocaleString()} up and ${c.down.toLocaleString()} down by 1 Hz or more</td></tr>
    ${floor ? `<tr><td>sham, same window</td><td>${floor.changed.toLocaleString()} changed; ${floor.up.toLocaleString()} up and ${floor.down.toLocaleString()} down by 1 Hz or more${floor.onset > w.t0 ? ` <span class="warnline">(the sham starts at ${floor.onset.toFixed(0)} ms, after this window opens, so this floor is low)</span>` : ""}</td></tr>` : ""}
    <tr><td>resolution</td><td>one spike in this ${(w.t1 - w.t0).toFixed(0)} ms window is ${(1000 / (w.t1 - w.t0)).toFixed(1)} Hz</td></tr>
    <tr><td>targeted</td><td>${c.targeted.size.toLocaleString()} model rows <span class="stimkey"></span></td></tr></table>
    <h3>Largest changes</h3>
    <table><tr><td>type</td><td class="num">here</td><td class="num">control</td><td class="num">change</td></tr>
    ${c.top.map(o => `<tr class="link" data-i="${o.i}"><td>${esc(o.i >= 0 ? app.atlas.typeName(o.i) || app.atlas.bodyId[o.i] : "row " + o.r)}${o.targeted ? ` <span class="stimkey" title="targeted by the protocol"></span>` : ""}</td><td class="num">${f1(o.run)}</td><td class="num">${f1(o.ctrl)}</td><td class="num">${sign(o.delta)}</td></tr>`).join("")}</table>
    <div class="dim">Hz during the stimulus. Colour the map by "rate vs control" to see every cell.</div>`;
}

function showTab(name) {
  document.querySelectorAll("#tabs button").forEach(b => b.classList.toggle("on", b.dataset.tab === name));
  document.querySelectorAll(".tab").forEach(t => t.hidden = t.id !== `tab-${name}`);
}

function wireControls() {
  $("#play").onclick = () => { state.playing = !state.playing; $("#play").textContent = state.playing ? "pause" : "play"; if (!state.playing) updateURL(); };
  $("#speed").onchange = e => { state.speed = Number(e.target.value); };
  $("#scrub").oninput = e => { state.t = Number(e.target.value) / 1000 * app.rec.duration; };
  $("#scrub").onchange = updateURL;
  document.addEventListener("keydown", e => {
    if (e.target.tagName === "INPUT" || e.target.tagName === "SELECT") return;
    if (e.code === "Space") { e.preventDefault(); $("#play").click(); }
    if (e.code === "ArrowRight") state.t += e.shiftKey ? 50 : 5;
    if (e.code === "ArrowLeft") state.t -= e.shiftKey ? 50 : 5;
    if (e.code === "Escape") { state.sel = null; app.brain.setHighlight([]); app.brain.setPartners(null); app.traces.select(null); app.inspector.clear(); updateURL(); }
  });
  $("#theme").onclick = () => setTheme(!state.dark);
  document.querySelectorAll("#layout button").forEach(b => b.onclick = () => {
    document.querySelectorAll("#layout button").forEach(x => x.classList.toggle("on", x === b));
    app.brain.setLayout(b.dataset.v); updateURL();
  });
  $("#colour").onchange = e => { app.brain.setColour(e.target.value); legend(); updateURL(); };
  $("#activity").onchange = e => app.brain.setActivityShown(e.target.checked);
  $("#inmodel").onchange = e => { app.brain.filters.inModel = e.target.checked; app.brain.applyFilters(); legend(); };
  $("#measured").onchange = e => { app.brain.filters.measuredOnly = e.target.checked; app.brain.applyFilters(); legend(); };
  $("#legend").onclick = e => { const d = e.target.closest("[data-name]"); if (d) { app.brain.toggleCategory(d.dataset.name); legend(); } };
  $("#reframe").onclick = () => app.brain.frame(true, app.brain.layouts[app.brain.layoutName]);
  document.querySelectorAll("#tabs button").forEach(b => b.onclick = () => showTab(b.dataset.tab));

  // brain picking: hover tooltip and click to select
  const cv = $("#brain"), tip = $("#tip");
  let pending = null, scheduled = false, down = null;
  cv.addEventListener("pointermove", e => {
    pending = e;
    if (scheduled) return;
    scheduled = true;
    requestAnimationFrame(() => {
      scheduled = false;
      if (!pending) return;
      const r = cv.getBoundingClientRect(), x = pending.clientX - r.left, y = pending.clientY - r.top;
      const i = app.brain.pick(x, y);
      if (i >= 0) {
        tip.hidden = false;
        tip.style.left = `${x + 12}px`; tip.style.top = `${y + 12}px`;
        tip.textContent = `${app.atlas.label(i)} · ${app.atlas.superclass(i)}`;
      } else tip.hidden = true;
      pending = null;
    });
  });
  cv.addEventListener("pointerleave", () => { tip.hidden = true; });
  cv.addEventListener("pointerdown", e => { down = [e.clientX, e.clientY]; });
  cv.addEventListener("pointerup", e => {
    if (!down || Math.hypot(e.clientX - down[0], e.clientY - down[1]) > 4) return;
    const r = cv.getBoundingClientRect();
    const i = app.brain.pick(e.clientX - r.left, e.clientY - r.top);
    if (i >= 0) select(i);
  });

  // search
  const q = $("#search"), res = $("#results");
  q.oninput = () => {
    const hits = app.atlas.search(q.value);
    res.innerHTML = hits.map(h => h.kind === "neuron"
      ? `<div class="hit" data-i="${h.i}">${esc(h.label)}</div>`
      : `<div class="hit" data-code="${h.code}">${esc(h.label)} <span>${h.n}</span></div>`).join("");
  };
  res.onclick = e => {
    const d = e.target.closest(".hit"); if (!d) return;
    if (d.dataset.i) select(Number(d.dataset.i));
    else { const code = Number(d.dataset.code); showType(code); select(app.atlas.ofType(code)[0]); app.brain.setHighlight(app.atlas.ofType(code)); }
    res.innerHTML = ""; q.value = "";
  };
}

// the run panel: configuration, status, measured summary, caveats, provenance
function runPanel(rec, atlas, entry) {
  const m = rec.manifest, s = m.summary || {}, p = m.provenance || {};
  const warn = /not validated|custom/.test(m.profile_status || "");
  $("#badge").textContent = m.profile_status || "";
  $("#badge").className = warn ? "badge warn" : "badge";
  const basisCounts = {};
  for (const r of rec.inventory || []) basisCounts[r.basis || "unknown"] = (basisCounts[r.basis || "unknown"] || 0) + 1;
  const clip = (s.torque_clip_fraction || []).filter(x => x > 0.01).length;
  const pv = { ...(p.git || {}), ...p };
  $("#tab-run").innerHTML = `
    <h2>${esc(entry.title)}</h2>
    <div class="sub">${esc(m.run_id)} · ${esc(m.created || "")}</div>
    ${m.protocol ? protocolHTML(m.protocol, rec) : ""}
    <h3>Configuration <span class="chip completed">${esc(m.profile_status || "")}</span></h3>
    <table>${Object.entries(m.config).map(([k, v]) => `<tr><td>${esc(k)}</td><td>${esc(typeof v === "object" ? JSON.stringify(v) : v)}</td></tr>`).join("")}</table>
    <h3>Measured in this run <span class="chip measured">this run</span></h3>
    <table>
      <tr><td>duration</td><td>${rec.duration} ms simulated</td></tr>
      <tr><td>neurons, connections</td><td>${(m.n_model_neurons || m.n_rows).toLocaleString()}, ${m.n_edges.toLocaleString()}${m.n_model_neurons && m.n_model_neurons !== m.n_rows ? `; ${m.n_rows.toLocaleString()} recorded` : ""} (${atlas.bodyId.length.toLocaleString()} in the scan; ${app.brain.unjoined} rows not in the atlas)</td></tr>
      <tr><td>spikes</td><td>${(s.spikes_total || 0).toLocaleString()}; mean ${(s.mean_rate_hz || 0).toFixed(2)} Hz per neuron</td></tr>
      <tr><td>compute</td><td>${s.wall_s ? `${s.wall_s.toFixed(0)} s wall, ${s.wall_s_per_sim_s.toFixed(0)} s per simulated s` : "not recorded"}</td></tr>
      <tr><td>actuators clipped &gt;1% of time</td><td>${clip} of ${rec.nAct}</td></tr>
      <tr><td>eye frames</td><td>${s.n_eye_frames ?? "none"}</td></tr>
    </table>
    <h3>Caveats</h3>
    <ul class="caveats">${(m.caveats || []).map(c => `<li><b>${esc(c.id)}</b> ${esc(c.text)} <span class="chip ${c.basis === "measured" ? "measured" : "inferred"}">${esc(c.basis)}</span></li>`).join("")}</ul>
    <h3>Parameter inventory</h3>
    <div>${Object.entries(basisCounts).sort((a, b) => b[1] - a[1]).map(([b, n]) => `${chip(b)} ${n}`).join(" &nbsp; ")}</div>
    <div class="dim">${(rec.inventory || []).length} rows; written by the model at record time.</div>
    <h3>Provenance</h3>
    <table>${["commit", "branch", "dirty_files", "command", "python", "host", "dataset", "mujoco"].filter(k => pv[k] !== undefined).map(k => `<tr><td>${k}</td><td class="mono">${esc(Array.isArray(pv[k]) ? pv[k].join(" ") : pv[k])}</td></tr>`).join("")}</table>
    ${m.edits ? `<h3>Edits after recording</h3><div>${esc(JSON.stringify(m.edits))}</div>` : ""}
    <h3>Atlas</h3>
    <table>${Object.entries(atlas.info.coverage.pos_basis_counts).map(([k, v]) => `<tr><td>${esc(k)}</td><td>${v.toLocaleString()}</td></tr>`).join("")}
    <tr><td>coordinate frame</td><td>${esc(atlas.info.frame.axes)}; voxel ${atlas.info.frame.voxel_um} um (${esc(atlas.info.frame.voxel_basis)})</td></tr>
    <tr><td>flow layer</td><td>${esc(atlas.info.layers["flow layer"])}</td></tr></table>`;
}

// the protocol as the recorder resolved it: what was done to which cells, when,
// with which approximation; what a real fly does; the held-out guard's result
function protocolHTML(pr, rec) {
  const res = pr.resolved || { events: [], genotype: [] }, ex = pr.expect || {}, g = pr.heldout, s = rec.manifest.summary || {};
  const rows = [...res.genotype.map(x => ({ ...x, when: "whole run (genotype)" })),
    ...res.events.map(e => ({ ...e, when: `${(e.on_step * rec.ts).toFixed(0)} to ${(e.off_step * rec.ts).toFixed(0)} ms` }))];
  const detail = e => e.effector === "kick" ? `${e.rate_hz} Hz per cell; ${s.kicks_total ?? "?"} kicks delivered in the run`
    : e.mv !== undefined ? `${e.mv > 0 ? "+" : ""}${e.mv} mV${e.pulse_hz ? `, ${e.pulse_hz} Hz pulses of ${e.pulse_ms} ms` : ""}`
    : e.effector === "world" ? `sets ${Object.keys(e.set).join(", ")}` : "";
  const applied = (res.world_applied || []).filter(Boolean);
  const cr = ex.criterion;
  return `<h3>Protocol</h3>
    <table>${rows.map(e => `<tr><td>${esc(e.when)}</td><td>${esc(e.label)} ${approxChip(e.approximation)}<br><span class="dim">${esc(e.effector)}${e.n ? ` on ${e.n} cells` : ""} · ${esc(detail(e))}</span></td></tr>`).join("")
      || `<tr><td>none</td><td>no stimulus: a control run</td></tr>`}</table>
    ${applied.map(a => `<div class="dim">world change at step ${a.step}, thorax at ${a.fly_xyz.map(v => v.toFixed(2)).join(", ")} mm: ${esc(JSON.stringify(a.set))}</div>`).join("")}
    <h3>What a real fly does</h3>
    <div>${esc(ex.text || "not stated")}</div>
    <div class="dim">${esc(ex.source || "no source")}${ex.status ? " · " + esc(ex.status) : ""}</div>
    ${cr ? `<div class="dim">Pass if ${esc(cr.what)} ${esc(cr.op)} ${cr.value} ${esc(cr.units)} (${esc(cr.basis)}). Scored in the Compare tab.</div>` : ""}
    <h3>Held-out guard</h3>
    <div>${g ? `${g.items.length ? `touches ${g.items.map(h => esc(h.id)).join(", ")}; spent here: ${esc((g.spent_here || []).join(", ") || "none")}` : "touches no held-out item"}; seed ${g.seed} ${g.seed_spent ? "is already spent (a development seed)" : "is fresh"}` : "not checked (recorded before the guard existed)"}</div>
    ${g ? `<div class="dim">${esc(g.register)}</div>` : ""}`;
}

main().catch(e => { console.error(e); status("error: " + e.message); });
