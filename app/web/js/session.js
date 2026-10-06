// Session tab: write a protocol, check it against the atlas, start a live run on
// this machine and steer it (pause, resume, stop, stimulate). The server side is
// app/server/sessions.py; the recorder side app/server/live.py.
import { esc, approxChip } from "./inspector.js";

const post = (url, body) => fetch(url, {
  method: "POST", headers: { "Content-Type": "application/json", "X-Workbench": "1" }, body: JSON.stringify(body),
}).then(async r => ({ http: r.status, ...(await r.json().catch(() => ({ ok: false, error: `HTTP ${r.status}` }))) }));

// measured on this Mac (M2 library and the assay check): wall seconds per simulated second
const COST = { closed_loop: 100, brain_only: 55 };

export function template(rec) {
  const p = rec && rec.manifest.protocol;
  if (p) {
    const { resolved, heldout, ...rest } = p;
    return { ...rest, title: `Live: ${p.title || rec.manifest.run_id}` };
  }
  return {
    format: "flyemu-protocol/1", title: "Live session",
    config: { scan: "male-cns:v1.0", body: "flybody", seed: 12, overrides: {} },
    duration_ms: 2000, genotype: [], events: [], record: { watch: { type: ["MN9"] } },
  };
}

export class SessionPanel {
  constructor(el, { rec, onFollow }) {
    this.el = el; this.rec = rec; this.onFollow = onFollow;
    this.sessions = []; this.active = null; this.timer = null;
    this.render();
    this.poll();
  }

  render() {
    const pr = JSON.stringify(template(this.rec), null, 1);
    this.el.innerHTML = `
      <h3>Protocol</h3>
      <div class="dim">flyemu-protocol/1 (docs/APP_DESIGN.md). Leave config.profile out to use the working profile. In a live session
        duration_ms is the maximum; stimuli can also be sent while it runs.</div>
      <textarea id="ses-json" spellcheck="false" rows="16">${esc(pr)}</textarea>
      <div class="row"><button id="ses-check">check</button><button id="ses-start">start live session</button>
        <button id="ses-dl">download</button><button id="ses-reset">from this run</button><button id="ses-blank">blank</button></div>
      <div id="ses-result"></div>
      <h3>Stimulus</h3>
      <div class="stimform">
        <select id="ses-eff"><option>kick</option><option>current</option><option>CsChrimson</option><option>GtACR1</option></select>
        <input id="ses-target" placeholder="cell types or bodyIds, e.g. LB3b LB3c" value="">
        <input id="ses-val" type="number" step="any" value="100" title="kick: rate, Hz; others: mV"><span id="ses-unit">Hz</span>
        for <input id="ses-dur" type="number" step="any" value="200" title="duration, ms of simulated time"> ms
      </div>
      <div class="row"><button id="ses-add">add to the protocol</button> at <input id="ses-t" type="number" step="any" value="500" style="width:60px"> ms
        <button id="ses-send">send now to the live session</button></div>
      <div class="dim">"Send now" starts the stimulus at the step the run reads it (every 10 ms of simulated time) and writes it
        into the recording's protocol, so the recording replays from it. Held-out cells are refused either way.</div>
      <h3>Live session</h3>
      <div id="ses-state" class="dim">none running</div>
      <div class="row"><button id="ses-pause">pause</button><button id="ses-resume">resume</button><button id="ses-stop">stop</button></div>
      <div id="ses-log"></div>`;
    const $ = s => this.el.querySelector(s);
    $("#ses-check").onclick = () => this.check();
    $("#ses-start").onclick = () => this.start();
    $("#ses-dl").onclick = () => this.download();
    $("#ses-reset").onclick = () => { $("#ses-json").value = JSON.stringify(template(this.rec), null, 1); };
    $("#ses-blank").onclick = () => { $("#ses-json").value = JSON.stringify(template(null), null, 1); };
    for (const c of ["pause", "resume", "stop"]) $(`#ses-${c}`).onclick = () => this.command({ cmd: c });
    $("#ses-eff").onchange = e => { $("#ses-unit").textContent = e.target.value === "kick" ? "Hz" : "mV"; $("#ses-val").value = e.target.value === "kick" ? 100 : e.target.value === "GtACR1" ? -10 : 10; };
    $("#ses-send").onclick = () => { const ev = this.event(); if (ev) this.command({ cmd: "stim", event: ev }); };
    $("#ses-add").onclick = () => this.addEvent();
    this.$ = $;
  }

  protocol() {
    try { return JSON.parse(this.$("#ses-json").value); }
    catch (e) { this.show({ ok: false, error: `not JSON: ${e.message}` }); return null; }
  }

  show(r) {
    const cost = r.preparation && this.protocolCost();
    this.$("#ses-result").innerHTML = r.ok
      ? `<div class="ok">resolves${r.preparation ? ` (${esc(r.preparation)})` : ""}; ${r.watch ?? 0} cells watched${cost ? `; about ${cost}` : ""}</div>`
        + (r.recorded_as ? `<div>recorded as <span class="chip completed">${esc(r.recorded_as)}</span></div>` : "")
        + (r.items || []).map(x => `<div>${esc(x.kind)}: ${esc(x.label)} <span class="dim">${x.n} cells${x.t_ms !== undefined ? `, ${x.t_ms}+${x.dur_ms} ms` : ""}</span> ${x.approximation ? approxChip(x.approximation) : ""}</div>`).join("")
        + (r.note ? `<div class="dim">${esc(r.note)}</div>` : "")
      : `<div class="warnline">${esc(r.error || "refused")}</div>`;
  }

  protocolCost() {
    const p = this.protocol();
    if (!p) return "";
    const s = (p.duration_ms || 1000) / 1000 * (COST[(p.config || {}).preparation || "closed_loop"] || 100);
    return `${Math.round(s / 60 * 10) / 10} min to run (measured cost on this Mac, plus about 15 s to build)`;
  }

  async check() {
    const p = this.protocol();
    if (p) this.show(await post("api/check", { protocol: p }));
  }

  async start() {
    const p = this.protocol();
    if (!p) return;
    const r = await post("api/sessions", { protocol: p });
    if (!r.ok) return this.show(r);
    this.show(r.check);
    this.poll();
  }

  download() {
    const p = this.protocol();
    if (!p) return;
    const a = document.createElement("a");
    a.href = URL.createObjectURL(new Blob([JSON.stringify(p, null, 1) + "\n"], { type: "application/json" }));
    a.download = `${(p.title || "protocol").replace(/[^A-Za-z0-9]+/g, "-").replace(/^-|-$/g, "").toLowerCase()}.json`;
    a.click();
    URL.revokeObjectURL(a.href);
  }

  async command(c) {
    if (!this.active) return;
    const r = await post(`api/sessions/${encodeURIComponent(this.active)}`, c);
    if (!r.ok) this.$("#ses-state").innerHTML = `<span class="warnline">${esc(r.error)}</span>`;
    this.poll();
  }

  // the event the form describes (no time: a live stim starts when it is read)
  event() {
    const eff = this.$("#ses-eff").value, val = Number(this.$("#ses-val").value), dur = Number(this.$("#ses-dur").value);
    const types = this.$("#ses-target").value.split(/[\s,]+/).filter(Boolean);
    if (!types.length) { this.show({ ok: false, error: "name the target cells (cell types or bodyIds)" }); return null; }
    const target = types.every(t => /^\d+$/.test(t)) ? { bodyId: types.map(Number) } : { type: types };
    return { effector: eff, target, dur_ms: dur, ...(eff === "kick" ? { rate_hz: val } : { mv: val }) };
  }

  // a configuration chosen in the Fidelity tab (profile, body, scan, overrides) replaces
  // those fields of the protocol's config; the rest of the protocol stays
  setConfig(cfg) {
    const p = this.protocol();
    if (!p) return;
    p.config = { ...(p.config || {}), ...cfg };
    this.$("#ses-json").value = JSON.stringify(p, null, 1);
    this.check();
  }

  addEvent() {
    const p = this.protocol(), ev = this.event();
    if (!p || !ev) return;
    p.events = [...(p.events || []), { t_ms: Number(this.$("#ses-t").value), ...ev }];
    this.$("#ses-json").value = JSON.stringify(p, null, 1);
    this.check();
  }

  async poll() {
    clearTimeout(this.timer);
    let r;
    try { r = await fetch("api/sessions").then(x => x.json()); }
    catch { this.$("#ses-state").textContent = "server not reachable"; return; }
    this.sessions = r.sessions || [];
    this.active = r.active;
    const s = this.sessions.find(x => x.id === r.active) || this.sessions[this.sessions.length - 1];
    this.renderState(s);
    if (s && this.onFollow) this.onFollow(s);
    if (r.active) this.timer = setTimeout(() => this.poll(), 2000);
  }

  renderState(s) {
    const st = this.$("#ses-state"), log = this.$("#ses-log");
    if (!s) { st.textContent = "none running"; log.innerHTML = ""; return; }
    const lv = s.live || {}, slot = (s.log || []).some(l => l.includes("[slot] waiting"));
    const phase = !s.alive ? (s.returncode === 0 ? `finished (${esc(lv.state || s.status || "")})` : `<span class="warnline">exited ${s.returncode}</span>`)
      : !s.status ? (slot ? "waiting for a job slot / RAM" : "building the model (about 15 s)")
        : esc(lv.state || s.status);
    st.innerHTML = `<b>${esc(s.id)}</b>: ${phase}; ${(s.t_ms || 0).toFixed(0)} ms simulated`
      + (s.status ? ` · <a href="?rec=${encodeURIComponent(s.path.replace(/^runs\//, ""))}&tab=session">open in the viewer</a>` : "");
    const rows = (lv.log || []).slice(-10).reverse();
    log.innerHTML = (rows.length ? `<table>${rows.map(x => `<tr><td>${x.t_ms} ms</td><td class="${x.ok ? "" : "warnline"}">${esc(x.cmd)}: ${esc(x.result)}</td></tr>`).join("")}</table>` : "")
      + (!s.alive && s.returncode ? `<pre class="mono">${esc((s.log || []).join("\n"))}</pre>` : "");
  }
}
