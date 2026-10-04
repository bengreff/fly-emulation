"""flyemu-rec/1: the recording format shared by the recorder, the live server and
the browser.

A recording is a directory:

    manifest.json      config, stream descriptions, chunk index, caveats, provenance
    static.bin.gz      per-run constant arrays (model row -> bodyId, per-row parameters)
    chunks/NNNNN.bin.gz  one per `chunk_ms` of simulated time, appended as the run goes
    inventory.csv      the run's evidence inventory (copied from the model's registry)

Every .bin.gz is a gzip of a packed blob: arrays concatenated little-endian, each
starting on an 8-byte boundary. The manifest gives each array's dtype, shape and
byte offset, so the browser maps typed arrays straight onto the decompressed
buffer. The manifest is rewritten (atomically) after every chunk, so a reader
can follow a run that is still going.
"""
from __future__ import annotations

import gzip
import json
import os
from pathlib import Path

import numpy as np

FORMAT = "flyemu-rec/1"
ALIGN = 8
DTYPES = {"uint8", "int8", "uint16", "int16", "uint32", "int32", "float32", "float64", "int64"}


def pack(arrays: dict[str, np.ndarray]) -> tuple[bytes, dict]:
    """Concatenate arrays on 8-byte boundaries; return (blob, index)."""
    parts, index, off = [], {}, 0
    for name, a in arrays.items():
        a = np.ascontiguousarray(a)
        if a.dtype.byteorder == ">":
            a = a.astype(a.dtype.newbyteorder("<"))
        dt = a.dtype.name
        if dt not in DTYPES:
            raise TypeError(f"{name}: dtype {dt} not in the format")
        pad = (-off) % ALIGN
        if pad:
            parts.append(b"\0" * pad)
            off += pad
        b = a.tobytes()
        index[name] = {"dtype": dt, "shape": list(a.shape), "offset": off, "nbytes": len(b)}
        parts.append(b)
        off += len(b)
    return b"".join(parts), index


def unpack(blob: bytes, index: dict) -> dict[str, np.ndarray]:
    out = {}
    for name, d in index.items():
        a = np.frombuffer(blob, dtype=np.dtype(d["dtype"]).newbyteorder("<"),
                          count=int(np.prod(d["shape"])) if d["shape"] else 1,
                          offset=d["offset"])
        out[name] = a.reshape(d["shape"])
    return out


def _atomic_write(path: Path, data: bytes) -> None:
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_bytes(data)
    os.replace(tmp, path)


def write_blob(path: Path, arrays: dict[str, np.ndarray]) -> dict:
    blob, index = pack(arrays)
    _atomic_write(path, gzip.compress(blob, compresslevel=6))
    return index


def spikes_to_csr(steps: np.ndarray, rows: np.ndarray, step0: int, n_bins: int,
                  steps_per_bin: int) -> dict[str, np.ndarray]:
    """Spikes as (absolute step, row) -> CSR by bin within a chunk.

    ptr[b]..ptr[b+1] index the spikes in bin b; `sub` is the step within the bin,
    so exact spike times survive the binning."""
    rel = steps - step0
    b = rel // steps_per_bin
    order = np.lexsort((rows, rel))
    b, rel, rows = b[order], rel[order], rows[order]
    counts = np.bincount(b, minlength=n_bins)[:n_bins] if b.size else np.zeros(n_bins, np.int64)
    ptr = np.zeros(n_bins + 1, dtype=np.uint32)
    np.cumsum(counts, out=ptr[1:])
    return {"spike_ptr": ptr, "spike_row": rows.astype(np.uint32),
            "spike_sub": (rel - b * steps_per_bin).astype(np.uint8)}


class RecWriter:
    """Writes a recording incrementally. `manifest` holds everything that is not
    a chunk; `chunks` grows as the run proceeds."""

    def __init__(self, out: Path, manifest: dict, static: dict[str, np.ndarray]):
        self.out = Path(out)
        (self.out / "chunks").mkdir(parents=True, exist_ok=True)
        self.manifest = {"format": FORMAT, "status": "recording", **manifest, "chunks": []}
        self.manifest["static"] = {"file": "static.bin.gz",
                                   "arrays": write_blob(self.out / "static.bin.gz", static)}
        self._flush()

    def add_chunk(self, t0_ms: float, t1_ms: float, arrays: dict[str, np.ndarray]) -> None:
        k = len(self.manifest["chunks"])
        name = f"chunks/{k:05d}.bin.gz"
        index = write_blob(self.out / name, arrays)
        self.manifest["chunks"].append({"file": name, "t0_ms": t0_ms, "t1_ms": t1_ms,
                                        "arrays": index})
        self.manifest["duration_ms"] = t1_ms
        self._flush()

    def finish(self, status: str = "complete", **fields) -> None:
        self.manifest.update(fields)
        self.manifest["status"] = status
        self._flush()

    def _flush(self) -> None:
        _atomic_write(self.out / "manifest.json",
                      json.dumps(self.manifest, indent=1, default=_json_default).encode())


def _json_default(o):
    if isinstance(o, np.generic):
        return o.item()
    if isinstance(o, np.ndarray):
        return o.tolist()
    if isinstance(o, Path):
        return str(o)
    raise TypeError(type(o))


class RecReader:
    def __init__(self, path: Path):
        self.path = Path(path)
        self.manifest = json.loads((self.path / "manifest.json").read_text())
        if self.manifest.get("format") != FORMAT:
            raise ValueError(f"{path}: not {FORMAT}")

    def static(self) -> dict[str, np.ndarray]:
        s = self.manifest["static"]
        return unpack(gzip.decompress((self.path / s["file"]).read_bytes()), s["arrays"])

    def chunk(self, k: int) -> dict[str, np.ndarray]:
        c = self.manifest["chunks"][k]
        return unpack(gzip.decompress((self.path / c["file"]).read_bytes()), c["arrays"])

    def __len__(self) -> int:
        return len(self.manifest["chunks"])

    def all_spikes(self) -> tuple[np.ndarray, np.ndarray]:
        """(time_ms, row) for every spike in the recording."""
        bin_ms = self.manifest["streams"]["spikes"]["bin_ms"]
        step_ms = self.manifest["timestep_ms"]
        ts, rs = [], []
        for k in range(len(self)):
            c, t0 = self.chunk(k), self.manifest["chunks"][k]["t0_ms"]
            ptr = c["spike_ptr"].astype(np.int64)
            b = np.repeat(np.arange(ptr.size - 1), np.diff(ptr))
            ts.append(t0 + b * bin_ms + c["spike_sub"] * step_ms)
            rs.append(c["spike_row"])
        if not ts:
            return np.zeros(0), np.zeros(0, np.uint32)
        return np.concatenate(ts), np.concatenate(rs)
