// The same protocol recorded as another model: another library folder scored by
// app/tools/score_library.py, set beside this run's library seed by seed and on the
// mean. Everything is read from the libraries' scores.json files and manifests through
// the catalogue (derived from the recordings). The test between the two models is
// post hoc: the declared rule only compares a test with its own shams.
import { esc } from "./inspector.js";

const groupOf = (lib, protocol) => lib && (lib.trials || []).find(g => g.protocol === protocol && g.criterion_on_mean);
const model = lib => lib.profiles.join(" + ");
const mean = a => a.reduce((s, x) => s + x, 0) / a.length;

export const libraryOf = (cat, entry) => (cat.libraries || []).find(l => l.id === entry.library);

// libraries holding this protocol, another model first, then more seeds
export function modelChoices(cat, entry) {
  const own = libraryOf(cat, entry), g = own && entry.trials && groupOf(own, entry.trials.protocol);
  if (!g) return [];
  return (cat.libraries || []).filter(l => l.id !== own.id && groupOf(l, g.protocol))
    .sort((x, y) => (model(x) === model(own)) - (model(y) === model(own))
      || groupOf(y, g.protocol).seeds.length - groupOf(x, g.protocol).seeds.length || x.id.localeCompare(y.id));
}

// Exact two-sided permutation test on the difference of two means: the share of all
// splits of the pooled values into groups of these sizes whose means differ at least as
// much. The two libraries share seeds and kick draws but not the model, so their runs
// are two samples, not pairs. Null when there are more than `limit` splits.
export function permutationP(a, b, limit = 2e6) {
  const pool = [...a, ...b], n = pool.length, k = a.length, tot = pool.reduce((s, x) => s + x, 0);
  let all = 1;
  for (let i = 0; i < k; i++) all = all * (n - i) / (i + 1);
  if (!k || k === n || all > limit) return null;
  const obs = Math.abs(mean(a) - mean(b)), tol = 1e-9 * Math.max(1, obs);
  let hit = 0;
  const walk = (start, left, sum) => {
    if (!left) { if (Math.abs(sum / k - (tot - sum) / (n - k)) >= obs - tol) hit++; return; }
    for (let i = start; i <= n - left; i++) walk(i + 1, left - 1, sum + pool[i]);
  };
  walk(0, k, 0);
  return { p: hit / Math.round(all), hit, all: Math.round(all) };
}

// seeds as ranges: 0, 1, 2, 5 -> "0 to 2, 5"
const ranges = s => s.reduce((o, x) => { const l = o[o.length - 1]; l && x === l[1] + 1 ? l[1] = x : o.push([x, x]); return o; }, [])
  .map(([a, b]) => a === b ? `${a}` : `${a} to ${b}`).join(", ");

// hosts as recorded in the manifests, with the seeds each ran
function machines(lib, g) {
  const by = new Map();
  for (const s of g.seeds) {
    const h = (lib.hosts[`${g.protocol}-s${s}`] || "unrecorded").split(".")[0];
    if (!by.has(h)) by.set(h, []);
    by.get(h).push(s);
  }
  return [...by].map(([h, s]) => `${esc(h)}${by.size > 1 ? ` <span class="dim">${ranges(s)}</span>` : ""}`).join("<br>");
}

// The other library's run to read the model from: the same protocol at the same seed
// when it was recorded, else its first seed.
export function otherRun(other, protocol, seed) {
  const g = groupOf(other, protocol), s = g.seeds.includes(seed) ? seed : g.seeds[0];
  return { id: `${other.id}/${protocol}-s${s}`, url: `${other.path}/${protocol}-s${s}/inventory.csv` };
}

// What differs between the two models, from the registry inventory each run wrote
// (record.py: every value its build asked for, with units and status). Recorded with
// the runs, so it holds for runs made before the profile's values went into manifests.
export function inventoryDiffHTML(a, b, invA, invB, runA, runB) {
  const key = r => `${r.entity}|${r.property}`;
  const A = new Map(invA.map(r => [key(r), r])), B = new Map(invB.map(r => [key(r), r]));
  const differ = [...A.keys()].filter(k => B.has(k) && A.get(k).value !== B.get(k).value).sort();
  const onlyA = [...A.keys()].filter(k => !B.has(k)).sort(), onlyB = [...B.keys()].filter(k => !A.has(k)).sort();
  const short = s => s.length > 48 ? `<span title="${esc(s)}">${esc(s.slice(0, 46))}…</span>` : esc(s);
  const v = r => `${short(r.value)}${r.units && !["dimensionless", "enum", "bool", "count"].includes(r.units) ? ` ${esc(r.units)}` : ""}`
    + ` <span class="chip ${esc(r.status)}">${esc(r.status)}</span>`;
  // an entity can hold "|" (motor_map keys are patterns), so name it from the row
  const name = r => `<td title="${esc(key(r))}">${short(r.entity)}<br><span class="dim">${esc(r.property)}</span></td>`;
  const only = (keys, M, lib) => !keys.length ? "" : `<details><summary class="dim">${keys.length} asked for only by ${esc(model(lib))}'s build</summary>
    <table class="diff">${keys.map(k => `<tr>${name(M.get(k))}<td>${v(M.get(k))}</td></tr>`).join("")}</table></details>`;
  return `<table class="diff"><tr><td>${differ.length} value${differ.length === 1 ? "" : "s"} differ</td><td>${esc(model(a))}</td><td>${esc(model(b))}</td></tr>
    ${differ.map(k => `<tr>${name(A.get(k))}<td>${v(A.get(k))}</td><td>${v(B.get(k))}</td></tr>`).join("")}</table>
    ${only(onlyA, A, a)}${only(onlyB, B, b)}
    <div class="dim">From the registry inventories written with ${esc(runA)} (${A.size} values) and ${esc(runB)} (${B.size}).</div>`;
}

// `own` is this run's library, `other` the one picked; `seed` is this run's seed
export function modelsHTML(cat, entry, pickId) {
  const own = libraryOf(cat, entry), cands = modelChoices(cat, entry);
  if (!own || !entry.trials) return "";
  if (!cands.length) return `<h3>Across models</h3><div class="dim">No other library holds ${esc(entry.trials.protocol)}.</div>`;
  const other = cands.find(l => l.id === pickId) || cands[0];
  const ga = groupOf(own, entry.trials.protocol), gb = groupOf(other, entry.trials.protocol);
  const ca = ga.criterion_on_mean, cb = gb.criterion_on_mean, u = ca.units || "Hz";
  const dp = u === "mm" ? 3 : u === "Hz" ? 1 : 2, f = v => v === null || v === undefined ? "–" : (v > 0 ? "+" : "") + v.toFixed(dp);
  const seed = entry.config && entry.config.seed;
  const val = (g, s) => {
    const i = g.seeds.indexOf(s), c = g.criterion_on_mean;
    if (i < 0) return `<span class="dim">not run</span>`;
    const sh = c.sham_values ? c.sham_values[i] : null;
    return `${f(c.values[i])} <span class="dim">(${sh === null || sh === undefined ? "–" : f(sh)})</span>`;
  };
  const seeds = [...new Set([...ga.seeds, ...gb.seeds])].sort((x, y) => x - y);
  const met = c => c.values.filter(v => c.op === ">=" ? v >= c.value : v <= c.value).length;
  const noise = c => c.p_sham === null || c.p_sham === undefined ? `<span class="warnline">no shams</span>`
    : `<span title="exact one-sided sign-flip test, ${c.n_pairs} seed pairs">p = ${c.p_sham.toFixed(3)}</span>${c.within_noise ? `, <span class="warnline">noise</span>` : ""}`;
  const verdict = c => `<span class="verdict ${c.pass ? "pass" : "fail"}">${c.pass ? "PASS" : "FAIL"}</span>`;
  const row = (label, a, b, cls = "") => `<tr><td>${label}</td><td class="${cls}">${a}</td><td class="${cls}">${b}</td></tr>`;
  const both = [ga, gb], cs = [ca, cb], libs = [own, other];
  const perm = permutationP(ca.values, cb.values);
  const notes = libs.filter(l => l.note).map(l => `<div class="warnline"><b>${esc(l.id)}</b>: ${esc(l.note)}</div>`).join("");
  return `<h3>Across models <span class="chip measured">score_library.py</span></h3>
    <div class="sub">${esc(entry.trials.protocol)} beside <select id="model-pick">${cands.map(l => `<option value="${esc(l.id)}" ${l.id === other.id ? "selected" : ""}>${esc(model(l))}: ${esc(l.id)} (${groupOf(l, ga.protocol).seeds.length} seeds)</option>`).join("")}</select></div>
    ${notes}
    <table class="models">
    <tr><td>${esc(u)}</td><td class="num"><b>${esc(model(own))}</b><br><span class="dim" title="this run's library">${esc(own.id)}</span></td><td class="num"><b>${esc(model(other))}</b><br><span class="dim">${esc(other.id)}</span></td></tr>
    ${seeds.map(s => row(s === seed ? `<b>seed ${s}</b>` : `seed ${s}`, s === seed ? `<b>${val(ga, s)}</b>` : val(ga, s), val(gb, s), "num")).join("")}
    ${row("mean (SD)", ...cs.map(c => `<b>${f(c.value_measured)}</b> <span class="dim">(${(c.sd ?? 0).toFixed(dp)})</span>`), "num")}
    ${row("vs shams", ...cs.map(noise), "num")}
    ${row(`mean ${esc(ca.op)} ${ca.value}`, ...cs.map(verdict), "num")}
    ${row("seeds meeting it", ...cs.map(c => `${met(c)} of ${c.values.length}`), "num")}
    ${row("readout cells", ...both.map(g => `${g.readout_hz_mean.toFixed(1)} Hz <span class="dim">(${g.readout_hz_sd.toFixed(2)})</span>`), "num")}
    ${row("ran on", ...libs.map((l, i) => machines(l, both[i])), "num")}
    ${row("commit", ...libs.map(l => esc(l.commits.map(c => c.slice(0, 7)).join(", "))), "num wrap")}
    </table>
    <div class="dim">Per seed: the test minus the same seed's control, the same seed's one-cell sham in brackets; ${esc(ca.what || ca.metric)}. Readout cells: their mean rate during the stimulus.</div>
    <div style="margin:6px 0">${esc(model(own))} minus ${esc(model(other))} on the mean: <b>${f(ca.value_measured - cb.value_measured)} ${esc(u)}</b>${perm
      ? `; exact two-sided permutation test, the ${ca.values.length} and ${cb.values.length} runs as two samples (seeds share kick draws, not models): p = ${perm.p.toFixed(3)} (${perm.hit.toLocaleString()} of ${perm.all.toLocaleString()} splits)` : ""}
      <span class="chip guessed" title="not declared before the runs; the declared rule judges each model against its own shams">post hoc</span></div>
    <h3>What differs between the models</h3>
    <div id="model-diff" class="dim">reading the two runs' registry inventories…</div>`;
}
