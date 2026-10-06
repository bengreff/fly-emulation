// The Fidelity tab (M4): what this run's model is made of and how much of it rests on
// evidence. Two sources, kept apart on the page:
// - the run's inventory.csv: every value the model's build asked for, with its basis
//   (written by the model at record time; a raw record of this run);
// - data/model/fidelity.json (app/build/fidelity.py): the model's construction tables
//   (mechanisms, unknowns with biological bounds, profiles) at the app's checkout.
// Values come from the first; statuses, bounds and profile lists from the second.
import { esc, chip } from "./inspector.js";

export const BASES = ["measured", "derived", "inferred", "guessed", "absent", "unknown"];
const GROUPS = { B: "body and periphery", S: "internal state and organs", N: "nervous system",
  D: "development", X: "model infrastructure (not counted in the ledger)" };
const STATUS_CHIP = { have: "measured", partial: "guessed", absent: "unknown" };

// entity|property with `*` as the only wildcard, as flyemu.model_data._pattern
export function keyPattern(p) {
  return new RegExp("^" + p.split("*").map(s => s.replace(/[.*+?^${}()|[\]\\]/g, "\\$&")).join(".*") + "$");
}

const keyOf = r => `${r.entity}|${r.property}`;

// every construction-table row whose pattern matches a registry key, as model_data.owners
export function ownerIndex(fid) {
  const pats = [
    ...fid.parameters.filter(r => r.registry_key).map(r => ({ kind: "parameter", re: keyPattern(r.registry_key), row: r, mech: r.mechanism_id })),
    ...fid.structural.map(r => ({ kind: r.kind, re: keyPattern(r.key_pattern), row: r, mech: r.mechanism_id })),
    ...fid.mechanisms.flatMap(m => m.switch.map(s => ({ kind: "mechanism switch", re: keyPattern(s), row: { key_pattern: s }, mech: m.id }))),
  ];
  return key => pats.filter(p => p.re.test(key));
}

// the run's inventory counted by basis, per subsystem and in total
export function basisBySubsystem(inv) {
  const out = { all: {} };
  for (const r of inv) {
    const s = r.subsystem || "unknown", b = BASES.includes(r.basis) ? r.basis : "unknown";
    out[s] = out[s] || {};
    out[s][b] = (out[s][b] || 0) + 1;
    out.all[b] = (out.all[b] || 0) + 1;
  }
  return out;
}

// numeric run values against the biological range [bio_min, bio_max] of every parameter row
// that owns their key
export function boundsCheck(inv, owners) {
  let ranged = 0;
  const outside = [];
  for (const r of inv) {
    const v = Number(r.value);
    if (r.value === "" || !Number.isFinite(v)) continue;
    const ps = owners(keyOf(r)).filter(o => o.kind === "parameter" && (o.row.bio_min != null || o.row.bio_max != null));
    if (!ps.length) continue;
    ranged++;
    for (const o of ps)
      if ((o.row.bio_min != null && v < o.row.bio_min) || (o.row.bio_max != null && v > o.row.bio_max))
        outside.push({ key: keyOf(r), value: v, basis: r.basis, param: o.row });
  }
  return { ranged, outside };
}

// keys where two profiles differ (a key missing from one is a difference)
export function profileDiff(a, b) {
  const keys = [...new Set([...Object.keys(a.values), ...Object.keys(b.values)])].sort();
  return keys.filter(k => JSON.stringify(a.values[k]?.[0]) !== JSON.stringify(b.values[k]?.[0]))
    .map(k => ({ key: k, a: a.values[k] || null, b: b.values[k] || null }));
}

// the status the recorder writes for a configuration (app/server/record.py profile_status);
// no profile means the working profile
export function configStatus(fid, profile, overrides) {
  const name = profile || fid.working, added = Object.keys(overrides || {}).length ? "overrides" : "";
  if (name === fid.working) return added ? `adopted profile with ${added}: custom, not validated` : "adopted (working profile)";
  const p = fid.profiles.find(x => x.name === name), named = p && !p.status.startsWith("custom") ? p.status : null;
  if (named && added) return `${name} (${named}) with ${added}: custom, not validated`;
  return named || "custom, not validated";
}

function bar(counts) {
  const n = BASES.reduce((s, b) => s + (counts[b] || 0), 0) || 1;
  return `<div class="basisbar">${BASES.filter(b => counts[b]).map(b =>
    `<i class="b-${b}" style="width:${(100 * counts[b] / n).toFixed(2)}%" title="${b}: ${counts[b]}"></i>`).join("")}</div>`;
}

const fmt = v => v == null ? "" : typeof v === "number" ? String(+v.toPrecision(6)) : String(v);
const range = p => p ? `[${fmt(p.bio_min) || "-inf"}, ${fmt(p.bio_max) || "inf"}] ${esc(p.unit || "")}` : "";
const runCommit = m => { const p = m.provenance || {}; return (p.model_src || {}).commit || p.commit || (p.git || {}).commit || ""; };

export class FidelityPanel {
  constructor(el, { onConfigure } = {}) { this.el = el; this.onConfigure = onConfigure; }

  bind(fid, rec) {
    this.fid = fid; this.rec = rec;
    this.inv = rec.inventory || [];
    this.byKey = new Map(this.inv.map(r => [keyOf(r), r]));
    this.owners = fid ? ownerIndex(fid) : null;
    this.render();
  }

  render() {
    const { fid, rec } = this, m = rec.manifest, cfg = m.config || {};
    if (!fid) {
      this.el.innerHTML = `<h2>Fidelity</h2><div class="warnline">The model's construction tables are not built: run
        <span class="mono">app/build/fidelity.py</span>. This run's own values are in the Run tab.</div>`;
      return;
    }
    const prof = fid.profiles.find(p => p.name === cfg.profile);
    // compared by default with the profile defined before it: what this one adds
    const pi = fid.profiles.indexOf(prof), base = prof && (fid.profiles[pi - 1] || fid.profiles[pi + 1]);
    const rc = runCommit(m), fc = fid.source.commit || "";
    const same = rc && fc && rc.slice(0, 9) === fc.slice(0, 9) && !(fid.source.tables_modified || []).length;
    const counts = this.inv.length ? basisBySubsystem(this.inv) : null;
    const bc = this.inv.length ? boundsCheck(this.inv, this.owners) : null;
    const st = fid.state;
    this.el.innerHTML = `
      <h2>Fidelity</h2>
      <div class="sub">What this run's model is made of, and how much of it rests on evidence.</div>
      <h3>Configuration</h3>
      <table>
        <tr><td>profile</td><td><b>${esc(cfg.profile || "none")}</b> <span class="chip completed">${esc(m.profile_status || "")}</span>
          ${prof && /^adopted/.test(m.profile_status || "") !== (cfg.profile === fid.working) ? `<br><span class="dim">status as recorded; in the current
            tables ${esc(cfg.profile)} is "${esc(prof.status)}" and the working profile is ${esc(fid.working)}</span>` : ""}
          ${Object.keys(cfg.overrides || {}).length ? `<br><span class="warnline">${Object.keys(cfg.overrides).length} override(s): ${esc(JSON.stringify(cfg.overrides))}</span>` : ""}
          ${m.extra_params ? `<br><span class="warnline">${m.extra_params.rows.length} variant row(s) added (Run tab)</span>` : ""}</td></tr>
        <tr><td>scan</td><td>${fid.scans.map(s => s.id === cfg.scan || (s.simulate && cfg.scan === undefined)
          ? `<b>${esc(s.id)}</b> (${esc(s.coverage)}, ${esc(s.sex)}) <span class="chip measured">used</span>`
          : `<span class="dim" title="${esc(s.why)}">${esc(s.id)}: ${s.simulate ? "available" : "not simulated"}; ${esc(s.why)}</span>`).join("<br>")}</td></tr>
        <tr><td>body</td><td>${fid.bodies.map(b => b.id === cfg.body
          ? `<b>${esc(b.id)}</b> <span class="chip measured">used</span>`
          : `<span class="dim">${esc(b.id)}: ${b.simulate ? "available" : "not selectable"}; ${esc(b.why)}</span>`).join("<br>")}</td></tr>
        <tr><td>tables</td><td>model tables at commit <span class="mono">${esc(fc.slice(0, 9))}</span>, built ${esc(fid.source.built || fid.built)}
          ${same ? "" : `<br><span class="warnline">${rc ? `this run's model is commit ${esc(rc.slice(0, 9))}` : "this run records no model commit"}${(fid.source.tables_modified || []).length ? `; tables modified since the commit: ${esc(fid.source.tables_modified.join(", "))}` : ""}. Values below are the run's own (inventory); statuses, bounds and profiles are the tables'.</span>`}</td></tr>
      </table>

      <h3>Configure a run</h3>
      <div class="row">
        <label class="dim">profile <select id="cfg-profile">${fid.profiles.slice().reverse().map(p =>
          `<option value="${esc(p.name)}"${p.name === (cfg.profile || fid.working) ? " selected" : ""}>${esc(p.name)}: ${esc(p.status)}${p.earlier ? " (earlier)" : ""}</option>`).join("")}</select></label>
        <label class="dim">body <select id="cfg-body">${fid.bodies.map(b =>
          `<option value="${esc(b.id)}"${b.simulate ? "" : " disabled"}${b.id === cfg.body ? " selected" : ""} title="${esc(b.why)}">${esc(b.id)}${b.simulate ? "" : " (not selectable)"}</option>`).join("")}</select></label>
        <label class="dim">scan <select id="cfg-scan">${fid.scans.map(s =>
          `<option value="${esc(s.id)}"${s.simulate ? "" : " disabled"}${s.id === cfg.scan ? " selected" : ""} title="${esc(s.why)}">${esc(s.id)}${s.simulate ? "" : " (not simulated)"}</option>`).join("")}</select></label>
      </div>
      <details id="cfg-sw-box"><summary class="dim">switches: override a value <span id="cfg-n"></span></summary><table id="cfg-switches"></table></details>
      <div class="row"><span id="cfg-status"></span><button id="cfg-send">set in the Session tab</button></div>
      <div class="dim">Writes profile, body, scan and overrides into the Session tab's protocol, where it is checked and can be
        run; the rest of that protocol stays, including any extra_params (variant rows), and its check shows the status
        the run will be recorded with. A changed profile is recorded as "custom, not validated".</div>

      <h3>This run's values by evidence <span class="chip measured">this run</span></h3>
      ${counts ? `<table class="basis">
        <tr><td>all</td><td class="num">${this.inv.length}</td><td>${bar(counts.all)}</td></tr>
        ${Object.entries(counts).filter(([s]) => s !== "all").sort((a, b) => sum(b[1]) - sum(a[1])).map(([s, c]) =>
          `<tr><td>${esc(s.replace(/_/g, " "))}</td><td class="num">${sum(c)}</td><td>${bar(c)}</td></tr>`).join("")}</table>
        <div class="basislegend">${BASES.map(b => `<span><i class="b-${b}"></i>${b} ${counts.all[b] || 0}</span>`).join("")}</div>
        <div class="dim">${this.inv.length} values in the run's inventory.csv, written by the model at record time. measured: read from
          data or a recording; derived: computed from measured inputs; inferred: from indirect evidence (fitted, borrowed, class prior);
          guessed: a placeholder; absent: a registered mechanism that is not built.</div>`
        : `<div class="warnline">This run wrote no inventory.csv.</div>`}

      ${bc ? `<h3>Biological bounds <span class="chip inferred">derived</span></h3>
        <div>${bc.ranged} numeric values have a declared range in parameters.csv;
          ${bc.outside.length ? `<span class="warnline">${bc.outside.length} outside it</span>` : "none is outside it"}.</div>
        ${bc.outside.length ? `<table>${bc.outside.map(o => `<tr><td class="mono">${esc(o.key)}</td><td>${fmt(o.value)} outside ${range(o.param)} (${esc(o.param.bound_basis)}) ${chip(o.basis)}</td></tr>`).join("")}</table>` : ""}` : ""}

      <h3>Construction ledger <span class="chip inferred">model tables</span></h3>
      <table>
        <tr><td>tier</td><td class="num">have</td><td class="num">partial</td><td class="num">absent</td></tr>
        ${Object.entries(st.by_tier).map(([t, c]) => `<tr><td>${esc(t)} ${esc({ A: "posture, walking, senses", B: "flight, take-off, landing", C: "grooming, feeding, state, learning" }[t] || "")}</td>
          <td class="num">${c.have}</td><td class="num">${c.partial}</td><td class="num">${c.absent}</td></tr>`).join("")}
      </table>
      <div class="dim">${st.n_mechanisms} mechanisms. ${st.n_unknowns} unknowns: bounds from data for ${st.bounded_by_data}
        (${st.bounds_verified} checked against the source), fixed by measurement ${st.fixed_by_measurement}; labels
        ${Object.entries(st.by_label).map(([k, v]) => `${esc(k)} ${v}`).join(", ")}.
        ${st.legacy_outside_bounds.length ? `<span class="warnline">m4 values outside their bounds: ${esc(st.legacy_outside_bounds.join("; "))}</span>` : ""}</div>

      <h3>Mechanisms and switches</h3>
      <div class="row"><label class="dim">status <select id="fid-status"><option value="">all</option><option>have</option><option>partial</option><option>absent</option></select></label>
        <label class="dim">tier <select id="fid-tier"><option value="">all</option><option>A</option><option>B</option><option>C</option></select></label>
        <label class="dim"><input type="checkbox" id="fid-switched"> with a switch only</label></div>
      <div id="fid-mechs"></div>

      <h3>Values in this run</h3>
      <div class="row"><input id="fid-q" placeholder="search key or evidence, e.g. v_rest, Mi1, adhesion" autocomplete="off">
        <select id="fid-sub"><option value="">every subsystem</option>${Object.keys(counts || {}).filter(s => s !== "all").sort().map(s => `<option>${esc(s)}</option>`).join("")}</select>
        <select id="fid-basis"><option value="">every basis</option>${BASES.map(b => `<option>${b}</option>`).join("")}</select></div>
      <div id="fid-vals"></div>

      <h3>Profiles <span class="chip inferred">model tables</span></h3>
      <table>${fid.profiles.slice().reverse().map(p => `<tr${p.name === cfg.profile ? ` class="on"` : ""}><td class="mono">${esc(p.name)}</td>
        <td>${esc(p.status)}${p.earlier ? " (earlier profile)" : ""}${p.name === cfg.profile ? ` <span class="chip measured">this run</span>` : ""}</td>
        <td class="num">${Object.keys(p.values).length}</td></tr>`).join("")}</table>
      <div class="dim">Values each profile sets (the rest are registry defaults). Newest first.</div>
      ${prof ? `<div class="row"><label class="dim">${esc(prof.name)} against <select id="fid-other">${fid.profiles.filter(p => p !== prof).reverse().map(p =>
        `<option${p === base ? " selected" : ""}>${esc(p.name)}</option>`).join("")}</select></label></div>
      <div id="fid-diff"></div>` : `<div class="warnline">This run's profile ${esc(cfg.profile || "none")} is not in the tables.</div>`}`;
    const $ = s => this.el.querySelector(s);
    for (const id of ["#fid-status", "#fid-tier", "#fid-switched"]) $(id).onchange = () => this.mechs();
    for (const id of ["#fid-q", "#fid-sub", "#fid-basis"]) $(id).oninput = () => this.values();
    if (prof) $("#fid-other").onchange = () => this.diff();
    $("#cfg-profile").onchange = () => this.switches();
    $("#cfg-switches").oninput = () => this.cfgStatus();
    $("#cfg-send").onclick = () => this.onConfigure && this.onConfigure(this.config());
    this.mechs(); this.values(); this.switches(); if (prof) this.diff();
  }

  // the mechanism switches (no wildcards) with the chosen profile's value and an override box
  switches() {
    const $ = s => this.el.querySelector(s), p = this.fid.profiles.find(x => x.name === $("#cfg-profile").value);
    const own = p && p.name === this.rec.manifest.config.profile;
    // switch keys named by a mechanism, then the structural table's switch rows (most profile
    // additions are there); wildcard keys are typed into the protocol instead
    const mech = Object.fromEntries(this.fid.mechanisms.map(m => [m.id, m]));
    const rows = [...this.fid.mechanisms.flatMap(m => m.switch.map(s => ({ s, m, note: m.neutral && `neutral: ${m.neutral}` }))),
      ...this.fid.structural.filter(r => r.kind === "switch").map(r => ({ s: r.key_pattern, m: mech[r.mechanism_id] || { id: r.mechanism_id, status: "" }, note: r.note }))]
      .filter((x, i, a) => !x.s.includes("*") && a.findIndex(y => y.s === x.s) === i)
      .sort((a, b) => a.m.id.localeCompare(b.m.id, "en", { numeric: true }) || a.s.localeCompare(b.s));
    $("#cfg-switches").innerHTML = rows.map(({ s, m, note }) => {
      const v = p && p.values[s], r = this.byKey.get(s);
      return `<tr><td class="mono wrap">${esc(s)}<br><span class="dim">${esc(m.id)} ${esc(m.status)}</span></td>
        <td>${v ? `${esc(fmt(v[0]))} ${chip(v[1])} <span class="dim">set by ${esc(p.name)}</span>`
          : `<span class="dim">not set by ${esc(p ? p.name : "the profile")}: registry default${own && r ? ` (this run: ${esc(r.value)})` : ""}</span>`}
          ${note ? `<br><span class="dim">${esc(note)}</span>` : ""}</td>
        <td><input type="number" step="any" data-key="${esc(s)}" placeholder="keep" style="width:70px"></td></tr>`;
    }).join("");
    this.cfgStatus();
  }

  config() {
    const $ = s => this.el.querySelector(s), overrides = {};
    for (const i of this.el.querySelectorAll("#cfg-switches input"))
      if (i.value !== "" && Number.isFinite(Number(i.value))) overrides[i.dataset.key] = Number(i.value);
    return { profile: $("#cfg-profile").value, body: $("#cfg-body").value, scan: $("#cfg-scan").value, overrides };
  }

  cfgStatus() {
    const c = this.config(), st = configStatus(this.fid, c.profile, c.overrides), n = Object.keys(c.overrides).length;
    this.el.querySelector("#cfg-n").textContent = n ? `(${n} set)` : "";
    this.el.querySelector("#cfg-status").innerHTML = `this configuration: <span class="chip ${/not validated/.test(st) ? "guessed" : "completed"}">${esc(st)}</span>`;
  }

  // mechanisms grouped by kind, each with its switches' values in this run
  mechs() {
    const $ = s => this.el.querySelector(s), st = $("#fid-status").value, tier = $("#fid-tier").value, sw = $("#fid-switched").checked;
    const ms = this.fid.mechanisms.filter(m => (!st || m.status === st) && (!tier || m.tier === tier) && (!sw || m.switch.length));
    const groups = {};
    for (const m of ms) (groups[m.id[0]] = groups[m.id[0]] || []).push(m);
    $("#fid-mechs").innerHTML = Object.entries(groups).map(([g, list]) => `
      <div class="grp">${esc(GROUPS[g] || g)} <span class="dim">${list.length}</span></div>
      ${list.map(m => {
        const vals = m.switch.flatMap(s => { const re = keyPattern(s); return this.inv.filter(r => re.test(keyOf(r))).map(r => ({ s, r })); });
        const missing = m.switch.filter(s => !vals.some(v => v.s === s));
        return `<details class="mech"><summary><b class="mono">${esc(m.id)}</b> ${esc(m.name)} <span class="dim">tier ${esc(m.tier)}</span>
            <span class="chip ${STATUS_CHIP[m.status] || "unknown"}">${esc(m.status)}</span>${vals.length ? ` <span class="dim">${vals.slice(0, 3).map(v => `${esc(v.s.includes("*") ? v.r.entity : v.r.property)} = ${esc(v.r.value)}`).join(", ")}${vals.length > 3 ? ", …" : ""}</span>` : ""}</summary>
          <table>
            ${vals.map(v => `<tr><td class="mono">${esc(keyOf(v.r))}</td><td>${esc(v.r.value)} ${chip(v.r.basis, v.r.method)}<br><span class="dim">${esc(v.r.evidence)}</span></td></tr>`).join("")}
            ${missing.map(s => `<tr><td class="mono">${esc(s)}</td><td class="dim">not in this run's inventory</td></tr>`).join("")}
            ${m.neutral ? `<tr><td>neutral</td><td>${esc(m.neutral)}</td></tr>` : ""}
            <tr><td>tests</td><td>${m.test.length ? m.test.map(t => `<span class="mono">${esc(t)}</span>`).join("<br>") : `<span class="warnline">none yet</span>`}</td></tr>
            ${m.absent_reason ? `<tr><td>why absent</td><td>${esc(m.absent_reason)}</td></tr>` : ""}
            ${m.notes ? `<tr><td>notes</td><td>${esc(m.notes)}</td></tr>` : ""}
          </table>
          ${m.rejoined.length ? `<div class="warnline">${esc(m.rejoined.join(", "))}: a comma in the unquoted YAML text split this field; the app rejoined it (mechanisms.yaml needs quotes).</div>` : ""}
        </details>`;
      }).join("")}`).join("") || `<div class="empty">No mechanism matches.</div>`;
  }

  // the run's values, filtered, with the owning parameter row's bounds
  values(limit = 150) {
    const $ = s => this.el.querySelector(s), q = $("#fid-q").value.trim().toLowerCase(), sub = $("#fid-sub").value, b = $("#fid-basis").value;
    const rows = this.inv.filter(r => (!sub || r.subsystem === sub) && (!b || r.basis === b)
      && (!q || `${keyOf(r)} ${r.evidence} ${r.model_use}`.toLowerCase().includes(q)));
    $("#fid-vals").innerHTML = `<table>${rows.slice(0, limit).map(r => {
      const own = this.owners(keyOf(r)), p = own.find(o => o.kind === "parameter");
      return `<tr><td class="mono wrap">${esc(keyOf(r))}</td><td>${esc(r.value)} ${esc(r.units || "")} ${chip(r.basis, r.method)}
        ${p ? `<br><span class="dim">bounds ${range(p.row)} (${esc(p.row.bound_basis)}); ${esc(p.row.param_id)}, ${esc(p.mech)}</span>`
          : own.length ? `<br><span class="dim">${esc(own[0].kind)}, ${esc(own[0].mech)}</span>` : `<br><span class="warnline">no row in the construction tables</span>`}
        <br><span class="dim">${esc(r.evidence)}</span></td></tr>`;
    }).join("")}</table>
      <div class="dim">${rows.length} of ${this.inv.length} values${rows.length > limit ? `; the first ${limit} shown, refine the search` : ""}.</div>`;
  }

  diff() {
    const prof = this.fid.profiles.find(p => p.name === this.rec.manifest.config.profile);
    const other = this.fid.profiles.find(p => p.name === this.el.querySelector("#fid-other").value);
    const d = profileDiff(prof, other);
    const cell = e => e ? `${esc(fmt(e[0]))} ${chip(e[1])}<br><span class="dim">${esc(e[2])}</span>` : `<span class="dim">not set (registry default)</span>`;
    this.el.querySelector("#fid-diff").innerHTML = `<table class="diff"><tr><td>key</td><td>${esc(prof.name)}</td><td>${esc(other.name)}</td></tr>
      ${d.map(x => `<tr><td class="mono">${esc(x.key)}</td><td>${cell(x.a)}</td><td>${cell(x.b)}</td></tr>`).join("")}</table>
      <div class="dim">${d.length} of ${new Set([...Object.keys(prof.values), ...Object.keys(other.values)]).size} keys differ.</div>`;
  }
}

function sum(c) { return Object.values(c).reduce((s, x) => s + x, 0); }
