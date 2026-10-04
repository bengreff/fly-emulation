// A flyemu-atlas/1 brain atlas: per-neuron identity and position, with
// partners and inspector strings fetched per shard on demand.
import { fetchJSON, fetchBlob, fetchGzJSON, idsToNumbers } from "./io.js";

export class Atlas {
  static async load(base) {
    const a = new Atlas();
    a.base = base.replace(/\/$/, "");
    a.info = await fetchJSON(`${a.base}/atlas.json`);
    a.arr = await fetchBlob(`${a.base}/neurons.bin.gz`, a.info.arrays);
    a.n = a.info.n;
    a.bodyId = idsToNumbers(a.arr.bodyid);
    a.index = new Map();
    for (let i = 0; i < a.n; i++) a.index.set(a.bodyId[i], i);
    a.vocab = a.info.vocab;
    a._edges = new Map();
    a._meta = new Map();
    return a;
  }

  typeName(i) { return this.vocab.type[this.arr.type[i]] || ""; }
  superclass(i) { return this.vocab.superclass[this.arr.superclass[i]] || ""; }
  className(i) { return this.vocab.class[this.arr.class[i]] || ""; }
  side(i) { return this.vocab.side[this.arr.side[i]] || ""; }
  label(i) {
    const t = this.typeName(i);
    return (t || "(untyped)") + " · " + this.bodyId[i];
  }

  // all neurons of a type code
  ofType(code) {
    if (!this._byType) {
      const n = this.n, t = this.arr.type;
      const start = new Uint32Array(this.vocab.type.length + 1);
      for (let i = 0; i < n; i++) start[t[i] + 1]++;
      for (let k = 0; k < start.length - 1; k++) start[k + 1] += start[k];
      const fill = start.slice(), idx = new Uint32Array(n);
      for (let i = 0; i < n; i++) idx[fill[t[i]]++] = i;
      this._byType = { start, idx };
    }
    const { start, idx } = this._byType;
    return idx.subarray(start[code], start[code + 1]);
  }

  shardOf(i) { return Math.floor(i / this.info.shard); }

  async edges(i) {
    const k = this.shardOf(i);
    if (!this._edges.has(k)) {
      if (!this._edgeIndex) this._edgeIndex = fetchJSON(`${this.base}/edges/index.json`);
      this._edges.set(k, this._edgeIndex.then(ix =>
        fetchBlob(`${this.base}/edges/${String(k).padStart(3, "0")}.bin.gz`, ix[k])));
    }
    const e = await this._edges.get(k);
    const j = i - k * this.info.shard;
    const take = (ptr, idx, w) => {
      const out = [];
      for (let q = ptr[j]; q < ptr[j + 1]; q++) out.push([idx[q], w[q]]);
      return out.sort((a, b) => b[1] - a[1]);
    };
    return { out: take(e.out_ptr, e.out_idx, e.out_w), in: take(e.in_ptr, e.in_idx, e.in_w) };
  }

  async meta(i) {
    const k = this.shardOf(i);
    if (!this._meta.has(k))
      this._meta.set(k, fetchGzJSON(`${this.base}/meta/${String(k).padStart(3, "0")}.json.gz`));
    const recs = await this._meta.get(k);
    return recs[i - k * this.info.shard];
  }

  // case-insensitive type search: exact matches first, then prefix, then substring
  search(q, limit = 30) {
    q = q.trim();
    if (!q) return [];
    if (/^\d{5,}$/.test(q)) {
      const i = this.index.get(Number(q));
      return i === undefined ? [] : [{ kind: "neuron", i, label: this.label(i) }];
    }
    const lq = q.toLowerCase(), hits = [];
    const counts = this.info.type_counts;
    this.vocab.type.forEach((t, code) => {
      if (!t) return;
      const lt = t.toLowerCase();
      const rank = lt === lq ? 0 : lt.startsWith(lq) ? 1 : lt.includes(lq) ? 2 : -1;
      if (rank >= 0) hits.push({ kind: "type", code, label: t, n: counts[code], rank });
    });
    hits.sort((a, b) => a.rank - b.rank || a.label.length - b.label.length || a.label.localeCompare(b.label));
    return hits.slice(0, limit);
  }
}
