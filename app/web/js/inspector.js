// The inspector: everything known about one neuron, each value tagged with its
// layer (measured from the scan, inferred by rule or classifier, a guessed
// prior, or completed by a fitted profile) and its source.
const PARAMS = [
  // static array, inventory property, label, units
  ["tau_m", "tau_m", "membrane time constant", "ms"],
  ["v_rest", "v_rest", "resting potential", "mV"],
  ["v_th", "v_th", "spike threshold", "mV"],
  ["v_reset", "v_reset", "reset potential", "mV"],
  ["t_ref", "t_ref", "refractory period", "ms"],
  ["spont_mv", "spontaneous_drive", "tonic drive", "mV"],
  ["input_gain", "input_gain", "input gain", ""],
  ["release_gain", "release_gain", "release gain", ""],
];
const NT_SOURCE = ["EM classifier prediction", "dataset consensus", "hemilineage rule"];

export function esc(s) {
  return String(s ?? "").replace(/[&<>"]/g, c => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c]));
}

// layer chip from an inventory basis (and method)
export function chip(basis, method) {
  const b = (basis || "unknown").toLowerCase();
  const layer = b === "measured" ? "measured" : (b === "derived" || b === "inferred") ? "inferred"
    : b === "guessed" ? "guessed" : "unknown";
  const text = { measured: "measured", inferred: b, guessed: "guessed prior", unknown: "unknown" }[layer];
  let out = `<span class="chip ${layer}" title="inventory basis: ${esc(basis)}">${esc(text)}</span>`;
  if (method === "profile") out += `<span class="chip completed" title="value set by the run's profile">set by profile</span>`;
  if (method === "per-type table") out += `<span class="chip inferred" title="per-type table">per type</span>`;
  return out;
}

// an effector that stands in for something it is not (protocol.APPROX)
export function approxChip(text) {
  return text ? `<span class="chip guessed" title="${esc(text)}">approximation</span>`
    : `<span class="chip unknown" title="the protocol declares no approximation for this effector">none declared</span>`;
}

export class Inspector {
  constructor(el, onSelect, onType) {
    this.el = el;
    this.onSelect = onSelect;
    this.onType = onType;
    el.addEventListener("click", e => {
      const b = e.target.closest("[data-i]");
      if (b) { this.onSelect(Number(b.dataset.i)); return; }
      const t = e.target.closest("[data-type]");
      if (t) { this.onType(Number(t.dataset.type)); return; }
      const om = e.target.closest("[data-omm]");
      if (om && this.onOmm) { e.preventDefault(); this.onOmm(...om.dataset.omm.split(",").map(Number)); }
    });
  }

  bind(atlas, rec, rowOfAtlas) {
    this.atlas = atlas; this.rec = rec; this.rowOfAtlas = rowOfAtlas;
    this.inv = this._indexInventory(rec.inventory || []);
  }

  _indexInventory(rows) {
    const byProp = new Map();
    for (const r of rows) {
      if (!r.entity || !r.entity.startsWith("cell_type:")) continue;
      const ent = r.entity.slice(10);
      const e = { ...r, ids: ent.startsWith("bodyId:") ? new Set(ent.slice(7).split(";").map(Number)) : null, all: ent === "all" };
      if (!byProp.has(r.property)) byProp.set(r.property, []);
      byProp.get(r.property).push(e);
    }
    return byProp;
  }

  // the most specific inventory row for a property and a neuron
  evidence(prop, bodyId) {
    const rows = this.inv.get(prop) || [];
    return rows.find(r => r.ids && r.ids.has(bodyId)) || rows.find(r => r.all) || null;
  }

  clear(msg) {
    this.el.innerHTML = `<div class="empty">${esc(msg || "Click a neuron in the brain map, or search by type or bodyId.")}</div>`;
  }

  async show(i) {
    const a = this.atlas, rec = this.rec, bid = a.bodyId[i];
    const row = this.rowOfAtlas.get(bid);
    const typeCode = a.arr.type[i], type = a.typeName(i);
    const basis = a.vocab.pos_basis[a.arr.pos_basis[i]];
    const posLayer = a.arr.pos_basis[i] <= 1 ? "measured" : "inferred";
    const h = [];
    h.push(`<h2>${esc(type || "(untyped)")}</h2>
      <div class="sub">bodyId ${bid} · ${esc(a.superclass(i))}${a.className(i) ? " / " + esc(a.className(i)) : ""} · side ${esc(a.side(i) || "?")}</div>`);
    h.push(`<div class="row">${type ? `<button data-type="${typeCode}">show all ${a.info.type_counts[typeCode]} of this type</button>` : ""}</div>`);
    h.push(`<h3>Identity <span class="chip measured">from the scan</span></h3><table>
      <tr><td>status</td><td>${esc(a.vocab.status[a.arr.status[i]])}</td></tr>
      <tr><td>synapses</td><td>${a.arr.n_pre[i].toLocaleString()} out, ${a.arr.n_post[i].toLocaleString()} in</td></tr>
      <tr><td>position</td><td>${esc(basis)} <span class="chip ${posLayer}">${posLayer === "measured" ? "measured" : "derived (display)"}</span></td></tr>
      <tr><td>transmitter (atlas)</td><td>${esc(a.vocab.nt[a.arr.nt[i]] || "unknown")} <span class="chip inferred">inferred</span></td></tr>
      <tr><td>in model</td><td>${row !== undefined ? `yes, row ${row}` : a.arr.in_model[i] ? "in policy, not in this run" : "no (status policy excludes it)"}</td></tr>
      ${this._omm(bid)}</table>`);
    if (row !== undefined) h.push(this._model(row, bid));
    h.push(`<div id="insp-meta"></div><div id="insp-edges"><h3>Partners</h3><div class="dim">loading…</div></div>`);
    this.el.innerHTML = h.join("");
    this.current = i;
    const [meta, edges] = await Promise.all([a.meta(i), a.edges(i)]);
    if (this.current !== i) return;
    this.el.querySelector("#insp-meta").innerHTML = this._meta(meta);
    this.el.querySelector("#insp-edges").innerHTML = this._edges(edges);
    return edges;
  }

  // a photoreceptor's ommatidium (set by the Eye tab through this.eyeOf)
  _omm(bid) {
    const m = this.eyeOf && this.eyeOf(bid);
    if (!m) return "";
    return `<tr><td>ommatidium</td><td><a href="#" data-omm="${m.e},${m.o}">${m.e ? "right" : "left"} eye, ${m.o}</a>
      <span class="chip inferred">derived topology, inferred alignment</span></td></tr>`;
  }

  _model(row, bid) {
    const st = this.rec.static, rec = this.rec;
    const graded = st.graded && st.graded[row];
    const h = [`<h3>In this run</h3><table>`];
    const n = rec.countsPerRow()[row], dur = rec.duration / 1000;
    const ntSrc = st.nt_source ? NT_SOURCE[st.nt_source[row]] : "";
    const ntUsed = st.nt_used ? rec.manifest.names.nt[st.nt_used[row]] : "";
    h.push(`<tr><td>spikes</td><td>${n} (${(n / dur).toFixed(1)} Hz) <span class="chip measured" title="counted from this recording">this run</span></td></tr>`);
    for (const e of (this.targets && this.targets.get(row)) || [])
      h.push(`<tr><td>targeted by</td><td>${esc(e.label)} ${approxChip(e.approximation)}</td></tr>`);
    const c = this.cmp;
    if (c) {
      const s = (c.win.t1 - c.win.t0) / 1000, a = c.during.run[row] / s, b = c.during.ctrl[row] / s;
      h.push(`<tr><td>vs control</td><td>${a.toFixed(1)} Hz here, ${b.toFixed(1)} Hz in the control during the stimulus (${c.win.t0.toFixed(0)} to ${c.win.t1.toFixed(0)} ms) <span class="chip measured" title="counted from the two recordings">this run</span></td></tr>`);
    }
    if (graded) h.push(`<tr><td>output</td><td>graded (continuous release; spikes not its output) <span class="chip inferred">model rule</span></td></tr>`);
    if (ntUsed) h.push(`<tr><td>transmitter used</td><td>${esc(ntUsed)} <span class="chip inferred" title="${esc(ntSrc)}">${esc(ntSrc)}</span></td></tr>`);
    if (rec.watchIndex(row) >= 0) h.push(`<tr><td>voltage</td><td>recorded (see trace)</td></tr>`);
    h.push(`</table><h3>Model parameters</h3>`);
    if (!PARAMS.some(([k]) => st[k])) {
      h.push(`<div class="dim">This recording did not store per-cell parameters.</div>`);
      return h.join("");
    }
    h.push(`<table class="params">`);
    for (const [k, prop, label, units] of PARAMS) {
      if (!st[k]) continue;
      const v = st[k][row], ev = this.evidence(prop, bid);
      const iv = ev ? Number(ev.value) : NaN;
      const differs = ev && isFinite(iv) && Math.abs(iv - v) > 1e-3 * Math.max(1, Math.abs(v));
      h.push(`<tr title="${esc(ev ? (ev.evidence || "") + (ev.uncertainty ? " | uncertainty: " + ev.uncertainty : "") : "no inventory row")}">
        <td>${esc(label)}</td><td>${fmt(v)} ${esc(units)}</td>
        <td>${ev ? chip(ev.basis, ev.method) : '<span class="chip unknown">no record</span>'}${differs ? ` <span class="dim">(inventory ${fmt(iv)}; per-cell value differs)</span>` : ""}</td></tr>`);
    }
    h.push(`</table><div class="dim">Values are read from the model for this cell. The chip is the inventory's basis for the most specific matching entry; group-level scales (class:…) apply on top and are not resolved per cell here.</div>`);
    return h.join("");
  }

  _meta(m) {
    if (!m) return "";
    const rows = [
      ["instance", m.instance], ["hemilineage", m.hemilineage || m.itoleeHl || m.trumanHl],
      ["soma neuromere", m.somaNeuromere], ["entry nerve", m.entryNerve],
      ["EM transmitter prediction", m.predictedNt ? `${m.predictedNt}${m.predictedNtProb ? ` (p ${Number(m.predictedNtProb).toFixed(2)})` : ""}` : ""],
      ["consensus transmitter", m.consensusNt], ["type-level prediction", m.celltypePredictedNt],
    ].filter(r => r[1]);
    const xw = [["FlyWire (FAFB) type", m.flywireType], ["hemibrain type", m.hemibrainType], ["MANC bodyId", m.mancBodyid], ["systematic type", m.systematicType], ["synonyms", m.synonyms]].filter(r => r[1]);
    let h = `<h3>Annotations <span class="chip inferred">scan annotation</span></h3><table>${rows.map(r => `<tr><td>${esc(r[0])}</td><td>${esc(r[1])}</td></tr>`).join("")}</table>`;
    if (xw.length) h += `<h3>Crosswalk to other scans</h3><table>${xw.map(r => `<tr><td>${esc(r[0])}</td><td>${esc(r[1])}</td></tr>`).join("")}</table>`;
    return h;
  }

  _edges(e) {
    const a = this.atlas;
    const list = (arr, dir) => arr.slice(0, 12).map(([j, w]) =>
      `<tr data-i="${j}" class="link"><td>${esc(a.typeName(j) || "(untyped)")}</td><td>${w}</td><td class="dim">${esc(a.vocab.nt[a.arr.nt[j]] || "")}</td></tr>`).join("");
    const tot = arr => arr.reduce((s, x) => s + x[1], 0);
    return `<h3>Partners <span class="chip measured">synapse counts, ≥5</span></h3>
      <div class="cols"><div><div class="dim">${e.in.length} inputs, ${tot(e.in).toLocaleString()} synapses</div><table>${list(e.in)}</table></div>
      <div><div class="dim">${e.out.length} outputs, ${tot(e.out).toLocaleString()} synapses</div><table>${list(e.out)}</table></div></div>`;
  }
}

function fmt(v) {
  if (!isFinite(v)) return String(v);
  const a = Math.abs(v);
  return a !== 0 && (a < 0.01 || a >= 1e4) ? v.toExponential(2) : (+v.toFixed(3)).toString();
}
