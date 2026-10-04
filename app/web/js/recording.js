// A flyemu-rec/1 recording in the browser: chunks merged into whole-run arrays.
// A run that is still recording can be refreshed; new chunks are appended.
import { fetchJSON, fetchBlob, fetchText, idsToNumbers, parseCSV } from "./io.js";

function cat(parts, C) {
  const n = parts.reduce((a, p) => a + p.length, 0);
  const out = new C(n);
  let o = 0;
  for (const p of parts) { out.set(p, o); o += p.length; }
  return out;
}

export class Recording {
  constructor(base) {
    this.base = base.replace(/\/$/, "");
    this.chunks = [];
  }

  static async load(base, onProgress) {
    const r = new Recording(base);
    r.manifest = await fetchJSON(`${r.base}/manifest.json`);
    const m = r.manifest;
    if (m.format !== "flyemu-rec/1") throw new Error(`${base}: not flyemu-rec/1`);
    r.static = await fetchBlob(`${r.base}/${m.static.file}`, m.static.arrays);
    r.rowBodyId = idsToNumbers(r.static.row_bodyid);
    r.ts = m.timestep_ms;
    r.binMs = m.streams.spikes.bin_ms;
    await r._loadChunks(m.chunks, onProgress);
    // a manifest may say there is no inventory (legacy conversions)
    if (m.inventory !== null) {
      try {
        r.inventory = parseCSV(await fetchText(`${r.base}/inventory.csv`));
      } catch { r.inventory = null; }
    }
    return r;
  }

  async refresh() {
    const m = await fetchJSON(`${this.base}/manifest.json?t=${Date.now()}`);
    const fresh = m.chunks.slice(this.chunks.length);
    this.manifest = m;
    if (fresh.length) await this._loadChunks(fresh);
    return fresh.length;
  }

  async _loadChunks(list, onProgress) {
    let done = 0;
    const loaded = await Promise.all(list.map(async c => {
      const a = await fetchBlob(`${this.base}/${c.file}`, c.arrays);
      onProgress && onProgress(++done, list.length);
      return { meta: c, a };
    }));
    this.chunks.push(...loaded);
    this._merge();
  }

  _merge() {
    const C = this.chunks;
    const get = k => C.filter(c => c.a[k]).map(c => c.a[k]);
    // spikes: one CSR over the whole run, bins of binMs from t = 0
    const ptrs = [], rows = [], subs = [];
    let off = 0;
    ptrs.push(new Uint32Array([0]));
    for (const c of C) {
      const p = c.a.spike_ptr;
      const q = new Uint32Array(p.length - 1);
      for (let i = 1; i < p.length; i++) q[i - 1] = p[i] + off;
      off += p[p.length - 1];
      ptrs.push(q); rows.push(c.a.spike_row); subs.push(c.a.spike_sub);
    }
    this.spikePtr = cat(ptrs, Uint32Array);
    this.spikeRow = cat(rows, Uint32Array);
    this.spikeSub = cat(subs, Uint8Array);
    this.nBins = this.spikePtr.length - 1;
    this.frameStep = cat(get("frame_step"), Uint32Array);
    this.nFrames = this.frameStep.length;
    for (const k of ["xpos", "xquat", "qpos", "torque", "contact", "mod_level", "v"])
      this[k] = cat(get(k), Float32Array);
    this.vStep = cat(get("v_step"), Uint32Array);
    this.eyeStep = cat(get("eye_step"), Uint32Array);
    this.eye = cat(get("eye"), Uint8Array);
    const c0 = C[0] && C[0].a;
    this.nBodies = c0 && c0.xpos ? c0.xpos.shape[1] : 0;
    this.nAct = c0 && c0.torque ? c0.torque.shape[1] : 0;
    this.nContact = c0 && c0.contact ? c0.contact.shape[1] : 0;
    this.nWatch = c0 && c0.v && c0.v.shape.length > 1 ? c0.v.shape[1] : 0;
    this.duration = this.manifest.duration_ms || this.nBins * this.binMs;
  }

  // index of the last sample at or before t (ms) in a step array
  static at(stepArr, t, ts) {
    let lo = 0, hi = stepArr.length - 1;
    if (hi < 0) return -1;
    const s = t / ts;
    if (s < stepArr[0]) return 0;
    while (lo < hi) {
      const mid = (lo + hi + 1) >> 1;
      if (stepArr[mid] <= s) lo = mid; else hi = mid - 1;
    }
    return lo;
  }

  frameAt(t) { return Recording.at(this.frameStep, t, this.ts); }
  vAt(t) { return Recording.at(this.vStep, t, this.ts); }
  eyeAt(t) { return Recording.at(this.eyeStep, t, this.ts); }

  // spike count per row (whole run)
  countsPerRow() {
    if (!this._counts) {
      const c = new Uint32Array(this.manifest.n_rows);
      for (let i = 0; i < this.spikeRow.length; i++) c[this.spikeRow[i]]++;
      this._counts = c;
    }
    return this._counts;
  }

  // spike times (ms) of one row
  spikeTimes(row) {
    const out = [];
    for (let b = 0; b < this.nBins; b++) {
      for (let k = this.spikePtr[b]; k < this.spikePtr[b + 1]; k++)
        if (this.spikeRow[k] === row) out.push(b * this.binMs + this.spikeSub[k] * this.ts);
    }
    return out;
  }

  watchIndex(row) {
    if (!this._watch) {
      this._watch = new Map();
      const w = this.static.watch_rows || [];
      for (let i = 0; i < w.length; i++) this._watch.set(w[i], i);
    }
    return this._watch.has(row) ? this._watch.get(row) : -1;
  }
}
