// Binary I/O for the workbench formats (flyemu-rec/1, flyemu-atlas/1).
// Blobs are gzipped packs of little-endian arrays; a JSON index gives each
// array's dtype, shape and byte offset (8-byte aligned).

const CTOR = {
  uint8: Uint8Array, int8: Int8Array, uint16: Uint16Array, int16: Int16Array,
  uint32: Uint32Array, int32: Int32Array, float32: Float32Array,
  float64: Float64Array, int64: BigInt64Array,
};

export async function fetchJSON(url) {
  const r = await fetch(url);
  if (!r.ok) throw new Error(`${url}: HTTP ${r.status}`);
  return r.json();
}

export async function fetchText(url) {
  const r = await fetch(url);
  if (!r.ok) throw new Error(`${url}: HTTP ${r.status}`);
  return r.text();
}

// Fetch a .gz file and return the decompressed bytes. A server may already
// have decoded it (Content-Encoding), so check the gzip magic first.
export async function fetchGz(url) {
  const r = await fetch(url);
  if (!r.ok) throw new Error(`${url}: HTTP ${r.status}`);
  const buf = await r.arrayBuffer();
  const b = new Uint8Array(buf, 0, 2);
  if (b[0] !== 0x1f || b[1] !== 0x8b) return buf;
  const ds = new Blob([buf]).stream().pipeThrough(new DecompressionStream("gzip"));
  return new Response(ds).arrayBuffer();
}

export function views(buf, index) {
  const out = {};
  for (const [name, d] of Object.entries(index)) {
    const C = CTOR[d.dtype];
    if (!C) throw new Error(`${name}: dtype ${d.dtype}`);
    const count = d.shape.reduce((a, b) => a * b, 1);
    out[name] = new C(buf, d.offset, count);
    out[name].shape = d.shape;
  }
  return out;
}

export async function fetchBlob(url, index) {
  return views(await fetchGz(url), index);
}

export async function fetchGzJSON(url) {
  return JSON.parse(new TextDecoder().decode(await fetchGz(url)));
}

// int64 bodyIds -> Float64 (exact below 2^53, which covers male-cns ids)
export function idsToNumbers(big) {
  const out = new Float64Array(big.length);
  for (let i = 0; i < big.length; i++) out[i] = Number(big[i]);
  return out;
}

// Minimal RFC 4180 CSV parser (quoted fields, embedded commas and newlines).
export function parseCSV(text) {
  const rows = [];
  let row = [], f = "", q = false;
  for (let i = 0; i < text.length; i++) {
    const c = text[i];
    if (q) {
      if (c === '"') {
        if (text[i + 1] === '"') { f += '"'; i++; } else q = false;
      } else f += c;
    } else if (c === '"') q = true;
    else if (c === ",") { row.push(f); f = ""; }
    else if (c === "\n") { row.push(f); rows.push(row); row = []; f = ""; }
    else if (c !== "\r") f += c;
  }
  if (f.length || row.length) { row.push(f); rows.push(row); }
  const head = rows.shift() || [];
  return rows.filter(r => r.length === head.length)
    .map(r => Object.fromEntries(head.map((h, i) => [h, r[i]])));
}
