"""Convert the old viewer's recordings (runs/organism-record-*/replay_data.js)
into flyemu-rec/1 so the workbench can open them, flagged as legacy.

    python app/build/convert_legacy.py [--src runs] [--out runs/app/legacy] [--reference runs/app/<native run>]

What the old files hold: body poses, torque and contact at 200 Hz, and motor
neuron spikes only, as (1 ms bin, motor-neuron index). Motor neurons carry no
bodyId; the i-th is the i-th vnc_motor row of the model table. The converter
joins them to bodyIds by that order and accepts the join only if the stored
motor_type sequence matches the atlas types exactly; otherwise rows stay unjoined.
Torque limits are not stored; they are taken by actuator name from a native
recording of the same body (assumed unchanged) and flagged.
"""
from __future__ import annotations

import argparse
import base64
import gzip
import json
import sys
from pathlib import Path

import numpy as np

APP = Path(__file__).resolve().parents[1]
REPO = APP.parent
sys.path.insert(0, str(APP / "server"))
from recfmt import RecReader, RecWriter, spikes_to_csr  # noqa: E402

CHUNK_MS = 250.0


def load_js(path: Path) -> dict:
    s = path.read_text()
    return json.loads(s[s.index("{"): s.rstrip().rstrip(";").rindex("}") + 1])


def b64(d: dict, k: str, dtype) -> np.ndarray:
    return np.frombuffer(base64.b64decode(d[k]), dtype)


def atlas_motor(atlas_dir: Path):
    info = json.loads((atlas_dir / "atlas.json").read_text())
    buf = gzip.open(atlas_dir / "neurons.bin.gz").read()
    arr = {k: np.frombuffer(buf, d["dtype"], int(np.prod(d["shape"])), d["offset"]).reshape(d["shape"])
           for k, d in info["arrays"].items() if k in ("bodyid", "type", "superclass", "in_model")}
    mn = arr["superclass"] == info["vocab"]["superclass"].index("vnc_motor")
    types = np.array(info["vocab"]["type"], object)
    # the model table keeps atlas order, so its vnc_motor rows are the atlas's in order
    rows = np.flatnonzero(mn & (arr["in_model"] > 0))
    full = np.flatnonzero(mn)
    return {
        "policy": (arr["bodyid"][rows], [types[arr["type"][i]] or "unnamed" for i in rows]),
        "all": (arr["bodyid"][full], [types[arr["type"][i]] or "unnamed" for i in full]),
    }, info


def convert(src: Path, out: Path, ref_limits: dict | None, motors: dict, atlas_info: dict) -> dict:
    d = load_js(src / "replay_data.js")
    M = d["meta"]
    prov_f = next(src.glob("*.provenance.json"), None)
    prov = json.loads(prov_f.read_text()) if prov_f else {}
    cfg = prov.get("config", {})
    ts, NF, NB = M["timestep_ms"], M["n_frames"], M["n_bodies"]
    frame_ms = 1000.0 / M["web_hz"]
    xpos = b64(d, "xpos", np.float32).reshape(NF, NB, 3)
    xquat = b64(d, "xquat", np.float32).reshape(NF, NB, 4)
    torque = b64(d, "torque", np.float32).reshape(NF, -1)
    contact = b64(d, "contact", np.float32).reshape(NF, -1)
    sp = b64(d, "motor_spikes", np.int32).reshape(-1, 2)
    n_mn = len(d["motor_type"])

    # join motor neurons to bodyIds by table order, verified by the type sequence
    key = "policy" if M["n_neurons"] == atlas_info["n_in_model_policy"] else "all"
    ids, types = motors[key]
    match = len(ids) == n_mn and list(types) == list(d["motor_type"])
    row_bodyid = ids.astype(np.int64) if match else np.zeros(n_mn, np.int64)
    join = (f"motor neuron i = the i-th vnc_motor of the {'status-policy' if key == 'policy' else 'full'} "
            f"table; type sequence {'matches' if match else 'DOES NOT match'} the atlas "
            f"({sum(a == b for a, b in zip(types, d['motor_type']))} of {n_mn})")

    acts = d["actuator_names"]
    if ref_limits:
        lim = {a: (lo, hi, l) for a, lo, hi, l in zip(ref_limits["names"], ref_limits["lo"], ref_limits["hi"], ref_limits["limited"])}
        got = [next((lim[k] for k in (a, "flybody/" + a, "flybody/" + a + "-motor") if k in lim), None) for a in acts]
        limits = None if any(g is None for g in got) else {
            "lo": [g[0] for g in got], "hi": [g[1] for g in got], "limited": [g[2] for g in got],
            "source": "taken by actuator name from a native recording of the current body (assumed unchanged)"}
    else:
        limits = None

    run_id = "legacy/" + src.name.removeprefix("organism-record-")
    profile = cfg.get("profile") or "none (pre-profile)"
    clip = None
    if limits:
        hi = np.array(limits["hi"]); lo = np.array(limits["lo"])
        clip = ((torque >= hi * 0.999) | (torque <= lo * 0.999)).mean(0).round(4).tolist()
    manifest = {
        "run_id": run_id, "title": f"legacy: {src.name.removeprefix('organism-record-')} ({profile}, {M['duration_ms'] / 1000:g} s)",
        "created": prov.get("started_utc"), "flags": ["legacy", "motor spikes only"],
        "protocol": {"format": "flyemu-protocol/1", "config": {}, "resolved": {"genotype": [], "events": [], "watch": []}},
        "config": {"scan": "male-cns:v1.0", "body": "flybody", "seed": cfg.get("seed"), "profile": profile,
                   "min_synapses": cfg.get("min_synapses"), "overrides": M.get("overrides", {}), "start": "rest"},
        "timestep_ms": ts, "chunk_ms": CHUNK_MS, "n_rows": n_mn, "n_model_neurons": M["n_neurons"],
        "n_edges": M["n_edges"], "n_synapses": M["n_synapses"],
        "profile_status": "legacy recording, not validated",
        "names": {"bodies": d["body_names"], "actuators": acts, "contacts": d["contact_names"],
                  "modulators": [], "nt": [], "nt_source": []},
        "streams": {
            "spikes": {"bin_ms": 1.0, "desc": "motor-neuron spikes only, 1 ms bins (sub-bin time not stored)",
                       "rows": "motor neurons (static.row_bodyid)"},
            "xpos": {"rate_hz": M["web_hz"], "units": "mm (flygym model units)"},
            "xquat": {"rate_hz": M["web_hz"], "units": "w,x,y,z"},
            "torque": {"rate_hz": M["web_hz"]}, "contact": {"rate_hz": M["web_hz"], "units": "N"},
        },
        "limits": limits,
        "inventory": None,
        "provenance": {"commit": prov.get("code", {}).get("flyemu_commit"),
                       "dirty_files": "dirty" if prov.get("code", {}).get("flyemu_dirty") else "clean",
                       "command": "scripts/record_organism.py " + " ".join(f"--set {s}" for s in cfg.get("set", [])),
                       "host": prov.get("environment", {}).get("hostname"),
                       "python": prov.get("environment", {}).get("python"),
                       "converted_by": "app/build/convert_legacy.py", "source": f"runs/{src.name}/replay_data.js"},
        "summary": {"spikes_total": int(M["total_spikes"]), "mean_rate_hz": M["mean_hz"],
                    "motor_spikes": int(len(sp)), "torque_clip_fraction": clip, "n_eye_frames": 0},
        "join": join,
        "caveats": [
            {"id": "legacy", "text": "Converted from the old viewer's file: only motor-neuron spikes were saved, "
             "so the brain map lights motor neurons only; population rates, voltages and the eye are absent.", "basis": "configuration"},
            {"id": "network", "text": f"{M['n_neurons']:,} neurons and {M['n_edges']:,} connections were simulated "
             f"({M['total_spikes']:,} spikes in all, mean {M['mean_hz']:.2f} Hz per neuron).", "basis": "measured in this run"},
            {"id": "join", "text": "Motor neurons joined to bodyIds by table order: " + join + ". Within a type "
             "(for example the left and right cell of a pair) identity rests on the order alone.", "basis": "derived"},
            {"id": "limits", "text": "Torque limits were not stored; " + (limits["source"] if limits else "none available, so torque is not normalised") + ".",
             "basis": "configuration"},
            {"id": "start", "text": "Every neuron starts at rest and the body starts above the ground; the opening "
             "fall and first tens of ms are transients of that choice.", "basis": "configuration"},
        ],
    }
    mapped = np.asarray(d["motor_mapped"], np.uint8)
    static = {"row_bodyid": row_bodyid, "mn_rows": np.arange(n_mn, dtype=np.int32), "mn_mapped": mapped,
              "body_parent": np.asarray(d["body_parent"], np.int32), "body_radius": np.asarray(d["body_radius"], np.float32)}
    w = RecWriter(out, manifest, static)
    steps_per_bin = int(round(1.0 / ts))
    frame_step = (np.arange(NF) * frame_ms / ts).round().astype(np.uint32)
    spike_step = sp[:, 0].astype(np.int64) * steps_per_bin
    t = 0.0
    while t < M["duration_ms"] - 1e-9:
        t1 = min(M["duration_ms"], t + CHUNK_MS)
        s0, s1 = int(round(t / ts)), int(round(t1 / ts))
        m = (spike_step >= s0) & (spike_step < s1)
        f = (frame_step >= s0) & (frame_step < s1)
        arrays = spikes_to_csr(spike_step[m], sp[m, 1].astype(np.uint32), s0, int(round(t1 - t)), steps_per_bin)
        arrays.update({"frame_step": frame_step[f], "xpos": xpos[f], "xquat": xquat[f],
                       "torque": torque[f], "contact": contact[f]})
        w.add_chunk(t, t1, arrays)
        t = t1
    w.finish("complete")
    return {"id": run_id, "spikes": int(len(sp)), "join_ok": bool(match), "limits": limits is not None}


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--src", type=Path, default=REPO.parent.parent.parent / "runs"
                    if (REPO / ".git").is_file() else REPO / "runs")
    ap.add_argument("--out", type=Path, default=REPO / "runs" / "app" / "legacy")
    ap.add_argument("--reference", type=Path, default=REPO / "runs" / "app" / "m9-s12-2000ms")
    ap.add_argument("--atlas", type=Path, default=APP / "data" / "atlas" / "male-cns-v1.0")
    a = ap.parse_args()
    motors, info = atlas_motor(a.atlas)
    ref = None
    if (a.reference / "manifest.json").exists():
        rm = RecReader(a.reference).manifest
        ref = {"names": rm["names"]["actuators"], **rm["limits"]}
    srcs = sorted(p.parent for p in a.src.glob("organism-record-*/replay_data.js"))
    print(f"{len(srcs)} legacy recordings in {a.src}")
    for s in srcs:
        r = convert(s, a.out / s.name.removeprefix("organism-record-"), ref, motors, info)
        print(f"  {r['id']}: {r['spikes']:,} motor spikes; join {'verified' if r['join_ok'] else 'FAILED (unjoined)'}; "
              f"limits {'from reference' if r['limits'] else 'absent'}")


if __name__ == "__main__":
    main()
