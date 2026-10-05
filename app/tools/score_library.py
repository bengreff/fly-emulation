"""Score the intervention library: each stimulated run against its matched
control and its protocol's pre-declared criterion, with every sham run (same
configuration) read over the same window as a noise floor. An independent implementation of what the
page's Compare tab computes (app/web/js/compare.js), so the two can be checked
against each other.

    .venv/bin/python app/tools/score_library.py [--lib runs/app/lib]

Writes <lib>/scores.json and prints a table. Every number is derived from the
recordings; thresholds are the protocols' own (guessed, declared before viewing).
"""
from __future__ import annotations

import argparse
import gzip
import json
import math
import re
import sys
from pathlib import Path

import numpy as np

APP = Path(__file__).resolve().parents[1]
REPO = APP.parent
sys.path.insert(0, str(APP / "server"))
from recfmt import RecReader, unpack  # noqa: E402

ATLAS = APP / "data" / "atlas" / "male-cns-v1.0"
CACHE = REPO / "data" / "cache"


def incomplete_cells() -> dict[int, str]:
    """bodyId -> instance of cells the reconstructors flag as incompletely traced.
    The readout drops them, as scripts/assay_pathways.py does (F-DATA-3: MN9_R has
    633 inputs against MN9_L's 6,358)."""
    import pandas as pd
    lab = pd.read_parquet(CACHE / "male_cns_extra.parquet", columns=["bodyId", "statusLabel"])
    bad = lab[lab.statusLabel.fillna("").str.contains("Hard to trace|Partially")]
    inst = pd.read_parquet(CACHE / "male_cns_neurons.parquet", columns=["bodyId", "instance"]).set_index("bodyId").instance
    return {int(b): str(inst.get(b) or b) for b in bad.bodyId}


class Run:
    def __init__(self, path: Path):
        self.path = path
        self.r = RecReader(path)
        self.m = self.r.manifest
        self.pr = self.m.get("protocol") or {}
        self.ts = self.m["timestep_ms"]
        t, rows = self.r.all_spikes()
        self.steps = np.round(t / self.ts).astype(np.int64)
        self.rows = rows.astype(np.int64)
        ch = [self.r.chunk(k) for k in range(len(self.r))]
        self.frame_step = np.concatenate([c["frame_step"] for c in ch]).astype(np.int64)
        self.xpos = np.concatenate([c["xpos"] for c in ch])
        self.xquat = np.concatenate([c["xquat"] for c in ch])

    @property
    def control(self):
        return bool(self.pr) and not self.pr.get("events") and not self.pr.get("genotype")

    def counts(self, s0: int, s1: int) -> np.ndarray:
        keep = (self.steps >= s0) & (self.steps < s1)
        return np.bincount(self.rows[keep], minlength=self.m["n_rows"])

    def pose(self, step: int):
        f = max(0, int(np.searchsorted(self.frame_step, step, side="right")) - 1)
        w, x, y, z = self.xquat[f, 1]
        return self.xpos[f, 1], math.atan2(2 * (w * z + x * y), 1 - 2 * (y * y + z * z))

    def movement(self, s0: int, s1: int) -> dict:
        (p0, a0), (p1, a1) = self.pose(s0), self.pose(s1)
        dx, dy = p1[0] - p0[0], p1[1] - p0[1]
        turn = (math.degrees(a1 - a0) + 540) % 360 - 180
        return {"forward": float(math.cos(a0) * dx + math.sin(a0) * dy),
                "left": float(-math.sin(a0) * dx + math.cos(a0) * dy), "turn": float(turn)}


def window(run: Run):
    ev = run.pr["resolved"]["events"]
    if ev:
        return min(e["on_step"] for e in ev), max(e["off_step"] for e in ev)
    return 0, int(round(run.m["duration_ms"] / run.ts))


def first_divergence(a: Run, b: Run):
    n = a.m["n_rows"]
    ka, kb = np.sort(a.steps * n + a.rows), np.sort(b.steps * n + b.rows)
    m = min(ka.size, kb.size)
    d = np.flatnonzero(ka[:m] != kb[:m])
    if d.size:
        return int(min(ka[d[0]], kb[d[0]]) // n)
    if ka.size != kb.size:
        return int((ka[m] if ka.size > m else kb[m]) // n)
    return None


def measure(run: Run, ctrl: Run, s0: int, s1: int, readout: list[str], types: np.ndarray,
            drop: dict[int, str]) -> dict:
    sec = (s1 - s0) * run.ts / 1000
    ca, cb = run.counts(s0, s1), ctrl.counts(s0, s1)
    delta = (ca - cb) / sec
    bid = run.r.static()["row_bodyid"]
    rows = np.flatnonzero(np.isin(types, readout))
    dropped = [drop[int(bid[r])] for r in rows if int(bid[r]) in drop]
    rows = np.array([r for r in rows if int(bid[r]) not in drop], np.int64)
    mr, mc = run.movement(s0, s1), ctrl.movement(s0, s1)
    return {
        "readout_delta_hz": float(delta[rows].mean()) if rows.size else None,
        "readout_hz": float(ca[rows].mean() / sec) if rows.size else None,
        "readout_hz_control": float(cb[rows].mean() / sec) if rows.size else None,
        "readout_cells": {str(int(bid[r])): [int(ca[r]) / sec, int(cb[r]) / sec] for r in rows},
        "readout_excluded_incomplete": dropped,
        "forward_mm_vs_control": mr["forward"] - mc["forward"],
        "turn_left_deg_vs_control": mr["turn"] - mc["turn"],
        "move_run": mr, "move_control": mc,
        "cells_changed": int((ca != cb).sum()), "up_1hz": int((delta >= 1).sum()), "down_1hz": int((delta <= -1).sum()),
        "spikes_run": int(ca.sum()), "spikes_control": int(cb.sum()),
    }


def trials(rows: list[dict]) -> list[dict]:
    """Runs of one protocol at several seeds (run_library --seeds names them <protocol>-s<seed>):
    the readout per trial and its mean and SD, as the model owner reports its assays. A rate
    criterion judged on the mean over trials is a rule added on 4 October 2026 after the first
    library was viewed, so it is reported beside the single-trial verdicts, not instead of them."""
    groups: dict[str, list[dict]] = {}
    for r in rows:
        m = re.fullmatch(r"(.+)-s(\d+)", r["run"])
        if m and r.get("readout_hz") is not None:
            groups.setdefault(m.group(1), []).append(r)
    out = []
    for name, rs in sorted(groups.items()):
        if len(rs) < 2:
            continue
        rs.sort(key=lambda r: r.get("seed") or 0)
        hz = np.array([r["readout_hz"] for r in rs])
        d = [r.get("readout_delta_hz") for r in rs if "error" not in r]
        g = {"protocol": name, "seeds": [r.get("seed") for r in rs], "readout_hz": hz.tolist(),
             "readout_hz_mean": float(hz.mean()), "readout_hz_sd": float(hz.std(ddof=1)),
             "excluded_incomplete": rs[0].get("readout_excluded_incomplete", [])}
        if d and len(d) == len(rs):
            g["readout_delta_hz"] = d
            g["readout_delta_hz_mean"] = float(np.mean(d))
            c = rs[0].get("criterion")
            if c and c["metric"] == "readout_delta_hz":
                v = g["readout_delta_hz_mean"]
                g["criterion_on_mean"] = {"op": c["op"], "value": c["value"], "value_measured": v,
                                          "pass": v >= c["value"] if c["op"] == ">=" else v <= c["value"],
                                          "rule": "mean over trials; added 4 Oct 2026 after the first library was viewed"}
        out.append(g)
    return out


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--lib", type=Path, default=REPO / "runs" / "app" / "lib")
    a = ap.parse_args()
    info = json.loads((ATLAS / "atlas.json").read_text())
    arr = unpack(gzip.open(ATLAS / "neurons.bin.gz").read(), info["arrays"])
    type_of = dict(zip(arr["bodyid"].tolist(), np.asarray(info["vocab"]["type"], object)[arr["type"]].tolist()))
    drop = incomplete_cells()
    runs = []
    for man in sorted(a.lib.glob("*/manifest.json")):
        m = json.loads(man.read_text())
        if m.get("status") == "complete" and m.get("protocol"):
            runs.append(Run(man.parent))
    # kick_rng only changes kicks, which a control has none of
    by_cfg = lambda r: json.dumps({k: v for k, v in r.m["config"].items() if k != "kick_rng"}, sort_keys=True)
    out = []
    for run in runs:
        if run.control:
            continue
        ctrls = [c for c in runs if c.control and by_cfg(c) == by_cfg(run)
                 and c.m["duration_ms"] >= run.m["duration_ms"]]
        types = np.array([type_of.get(int(b), "") for b in run.r.static()["row_bodyid"]], object)
        ex = run.pr.get("expect") or {}
        readout = (ex.get("readout") or {}).get("type", [])
        s0, s1 = window(run)
        if not ctrls:
            # no control to compare with; the run's own readout rate still stands (the
            # model owner's assay reports absolute rates)
            res = measure(run, run, s0, s1, readout, types, drop)
            out.append({"run": run.path.name, "error": "no matched control", "seed": run.m["config"].get("seed"),
                        "window_ms": [s0 * run.ts, s1 * run.ts],
                        **{k: res[k] for k in ("readout_hz", "readout_cells", "readout_excluded_incomplete")}})
            continue
        ctrl = ctrls[0]
        res = measure(run, ctrl, s0, s1, readout, types, drop)
        div = first_divergence(run, ctrl)
        div = None if div is not None and div * run.ts >= run.m["duration_ms"] else div   # control runs longer
        row = {"run": run.path.name, "control": ctrl.path.name, "title": run.pr.get("title"), "role": run.pr.get("role"),
               "seed": run.m["config"].get("seed"), "preparation": (run.m.get("preparation") or {}).get("coupling", "closed_loop"),
               "window_ms": [s0 * run.ts, s1 * run.ts], "first_divergence_step": div, "first_event_step": s0,
               "matched": div is None or div >= s0, **res}
        shams = [s for s in runs if s.pr.get("role") == "sham" and s is not run and by_cfg(s) == by_cfg(run)]
        shams.sort(key=lambda s: (s.path.name != "sham-one-cell", s.path.name))    # the original sham first
        if shams:
            row["shams"] = [{"run": s.path.name, **measure(s, ctrl, s0, s1, readout, types, drop)} for s in shams]
            row["sham"] = row["shams"][0]
        c = ex.get("criterion")
        if c:
            v = res.get(c["metric"])
            row["criterion"] = {**c, "value_measured": v,
                                "pass": None if v is None else (v >= c["value"] if c["op"] == ">=" else v <= c["value"])}
            if shams:
                # the noise floor: every sham read on this test's measure over its window;
                # a result no larger in size than the largest sham's cannot be told from noise
                sv = [x.get(c["metric"]) for x in row["shams"]]
                sv = [x for x in sv if x is not None]
                row["criterion"]["sham_value"] = row["sham"].get(c["metric"])
                row["criterion"]["sham_values"] = sv
                row["criterion"]["n_shams"] = len(sv)
                row["criterion"]["sham_max_abs"] = max(map(abs, sv)) if sv else None
                row["criterion"]["within_sham"] = v is not None and bool(sv) and abs(v) <= max(map(abs, sv))
        out.append(row)
    commit = {r.path.name: ((r.m.get("provenance") or {}).get("git") or {}).get("commit") for r in runs}
    doc = {"format": "flyemu-scores/1", "lib": str(a.lib.relative_to(REPO)) if a.lib.is_relative_to(REPO) else str(a.lib),
           "basis": "derived from the recordings by app/tools/score_library.py; thresholds guessed and declared in the protocols",
           "commits": commit, "scores": out, "trials": trials(out)}
    (a.lib / "scores.json").write_text(json.dumps(doc, indent=1) + "\n")
    print(f"{'run':20} {'verdict':16} {'measured':>10} {'needed':>10} {'sham max|x|':>12}  first diff / onset   cells up/down (sham)"
          "   readout Hz run / control")
    for r in out:
        if "error" in r:
            ro = "" if r.get("readout_hz") is None else f"; readout {r['readout_hz']:.2f} Hz" + (
                f" (excl. {', '.join(r['readout_excluded_incomplete'])})" if r["readout_excluded_incomplete"] else "")
            print(f"{r['run']:20} {r['error']}{ro}")
            continue
        ro = "-" if r["readout_hz"] is None else f"{r['readout_hz']:.2f} / {r['readout_hz_control']:.2f}"
        ro += f" (excl. {', '.join(r['readout_excluded_incomplete'])})" if r["readout_excluded_incomplete"] else ""
        c = r.get("criterion")
        verdict = "-" if not c else "n/a" if c["pass"] is None else "PASS" if c["pass"] else "FAIL"
        verdict += "" if not c else " (no spike)" if r["first_divergence_step"] is None else " (noise)" if c.get("within_sham") else ""
        meas = f"{c['value_measured']:.2f}" if c and c["value_measured"] is not None else "-"
        need = f"{c['op']}{c['value']}" if c else "-"
        sham = f"{c['sham_max_abs']:.2f} n{c['n_shams']}" if c and c.get("sham_max_abs") is not None else "-"
        sh = r.get("sham", {})
        print(f"{r['run']:20} {verdict:16} {meas:>10} {need:>10} {sham:>12}  {r['first_divergence_step']} / {r['first_event_step']}"
              f"{'' if r['matched'] else ' NOT MATCHED'}   {r['up_1hz']}/{r['down_1hz']} ({sh.get('up_1hz', '-')}/{sh.get('down_1hz', '-')})"
              f"   {ro}")
    for g in doc["trials"]:
        ex = f" (excl. {', '.join(g['excluded_incomplete'])})" if g["excluded_incomplete"] else ""
        line = (f"trials {g['protocol']}: seeds {g['seeds']}; readout Hz {[round(x, 2) for x in g['readout_hz']]}{ex}; "
                f"mean {g['readout_hz_mean']:.2f}, SD {g['readout_hz_sd']:.2f}")
        if "readout_delta_hz_mean" in g:
            line += f"; vs control mean {g['readout_delta_hz_mean']:+.2f} Hz"
        if "criterion_on_mean" in g:
            c = g["criterion_on_mean"]
            line += f"; on the mean {'PASS' if c['pass'] else 'FAIL'} ({c['op']}{c['value']}, post hoc rule)"
        print(line)
    return 0


if __name__ == "__main__":
    sys.exit(main())
