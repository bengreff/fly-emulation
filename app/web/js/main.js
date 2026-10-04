// Fly Workbench: load a recording and the scan's atlas, then drive the body,
// brain map, traces and inspector from one clock.
import { fetchJSON } from "./io.js";
import { Recording } from "./recording.js";
import { Atlas } from "./atlas.js";
import { BodyView } from "./body.js";
import { BrainView } from "./brain.js";
import { Traces } from "./traces.js";
import { Inspector, esc, chip } from "./inspector.js";

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
    o.textContent = `${r.title}${r.flags && r.flags.length ? " [" + r.flags.join(", ") + "]" : ""}`;
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
  runPanel(rec, atlas, entry);
  brainCount(rec, atlas);
  window.addEventListener("resize", resize);
  resize();
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
  const gl = app.brain.groupLabels();
  const key = gl.map(l => `${l.x | 0},${l.y | 0}`).join();
  if (key !== tick.glKey) {
    tick.glKey = key;
    $("#glabels").innerHTML = gl.map(l => `<span style="left:${l.x}px;top:${l.y - 14}px">${esc(l.text)}</span>`).join("");
  }
  $("#time").textContent = `${state.t.toFixed(1)} / ${rec.duration.toFixed(0)} ms`;
  $("#scrub").value = String(state.t / rec.duration * 1000);
  $("#bodyinfo").textContent = app.body.thoraxHeight !== undefined ? `thorax ${app.body.thoraxHeight.toFixed(2)} mm` : "";
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
    + `<div class="dim">${b.shown.toLocaleString()} of ${app.atlas.n.toLocaleString()} drawn</div>`;
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
  $("#tab-run").innerHTML = `
    <h2>${esc(entry.title)}</h2>
    <div class="sub">${esc(m.run_id)} · ${esc(m.created || "")}</div>
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
    <table>${["commit", "branch", "dirty_files", "command", "python", "host", "dataset", "mujoco"].filter(k => p[k] !== undefined).map(k => `<tr><td>${k}</td><td class="mono">${esc(Array.isArray(p[k]) ? p[k].join(" ") : p[k])}</td></tr>`).join("")}</table>
    ${m.edits ? `<h3>Edits after recording</h3><div>${esc(JSON.stringify(m.edits))}</div>` : ""}
    <h3>Atlas</h3>
    <table>${Object.entries(atlas.info.coverage.pos_basis_counts).map(([k, v]) => `<tr><td>${esc(k)}</td><td>${v.toLocaleString()}</td></tr>`).join("")}
    <tr><td>coordinate frame</td><td>${esc(atlas.info.frame.axes)}; voxel ${atlas.info.frame.voxel_um} um (${esc(atlas.info.frame.voxel_basis)})</td></tr>
    <tr><td>flow layer</td><td>${esc(atlas.info.layers["flow layer"])}</td></tr></table>`;
}

main().catch(e => { console.error(e); status("error: " + e.message); });
