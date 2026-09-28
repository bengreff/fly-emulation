"""Declared class-level search (DECISIONS s10, "class-level search for a stable
template brain"): candidate evaluation on backhouse, orchestrated from the Mac.

A candidate is a dict of registry overrides (class rows only). Each candidate is
evaluated by the template closed loop on seeds 0-2 (scripts/probes/closed_loop_check.py
--template --out) and sugar->MN9 (assay_pathways.py, 100 Hz, 10 trials).

    uv run python scripts/search/class_search.py launch <batch> <cands.json> [--par 6] [--seeds 0,1,2] [--no-sugar]
    uv run python scripts/search/class_search.py collect <batch>
"""
from __future__ import annotations

import argparse
import json
import math
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
BH = ["ssh", "backhouse", "wsl -d Ubuntu -- bash -s"]


def bh(script: str) -> str:
    return subprocess.run(BH, input=script, capture_output=True, text=True, timeout=600).stdout


def sets(c: dict) -> str:
    return " ".join(f"--set '{k}={v:.6g}'" for k, v in c.items())


def launch(batch: str, cands: list[dict], par: int, seeds, sugar: bool, extra: str = "") -> None:
    lines = []
    for i, c in enumerate(cands):
        for s in seeds:
            lines.append(f"uv run python scripts/probes/closed_loop_check.py --template --seed {s} {sets(c)} {extra} "
                         f"--out runs/{batch}/c{i:03d}_cl{s}.json > runs/{batch}/c{i:03d}_cl{s}.log 2>&1")
        if sugar:
            lines.append(f"uv run python scripts/assay_pathways.py --assay sugar_mn9 --rates 100 --shuffles 0 "
                         f"--trials 10 {sets(c)} --tag {batch}_c{i:03d} > runs/{batch}/c{i:03d}_sugar.log 2>&1 "
                         f"&& cp runs/assay-sugar_mn9-m4-{batch}_c{i:03d}/trials.csv runs/{batch}/c{i:03d}_sugar.csv")
    (REPO / "runs" / batch).mkdir(parents=True, exist_ok=True)
    (REPO / "runs" / batch / "cands.json").write_text(json.dumps(cands, indent=1))
    body = "\n".join(lines)
    script = (f"cd ~/fly-emulation && mkdir -p runs/{batch} && cat > runs/{batch}/cands.json <<'EOC'\n"
              f"{json.dumps(cands)}\nEOC\npython3 scripts/mkjobs.py runs/{batch} /dev/stdin <<'EOL'\n{body}\nEOL\n"
              f"tmux new-session -d -s {batch} -c ~/fly-emulation \"xargs -P {par} -n 1 bash < runs/{batch}/joblist.txt "
              f"> runs/{batch}/xargs.log 2>&1\" </dev/null >/dev/null 2>&1; echo launched {len(lines)} jobs")
    print(bh(script))


def collect(batch: str) -> list[dict]:
    out = bh(f"cd ~/fly-emulation/runs/{batch} && shopt -s nullglob; for f in c*_cl*.json; do echo \"$f $(cat $f)\"; done; "
             f"for f in c*_sugar.csv; do echo \"$f\"; cat $f; echo; done; tmux has-session -t {batch} 2>/dev/null && echo RUNNING")
    cands = json.loads((REPO / "runs" / batch / "cands.json").read_text())
    res = [dict(cand=c, cl={}, mn9=None) for c in cands]
    lines = out.splitlines()
    for k, ln in enumerate(lines):
        if "_cl" in ln and ln.endswith("}") and ".json " in ln:
            f, js = ln.split(" ", 1)
            i, s = int(f[1:4]), int(f.split("_cl")[1].split(".")[0])
            res[i]["cl"][s] = json.loads(js)
        if ln.endswith("_sugar.csv"):
            i = int(ln[1:4])
            hdr = lines[k + 1].split(",")
            col = hdr.index("readout_hz")
            vals = []
            for row in lines[k + 2:]:
                if not row or not row[0].isalpha():
                    break
                vals.append(float(row.split(",")[col]))
            res[i]["mn9"] = sum(vals) / len(vals) if vals else None
    running = "RUNNING" in out
    for i, r in enumerate(res):
        r["silent"] = {s: v["silent_last100ms_spikes_per_ms"] for s, v in r["cl"].items()}
        r["J"] = objective(r)
    (REPO / "runs" / batch / "results.json").write_text(json.dumps(res, indent=1))
    print(f"{batch}: running={running}")
    return res


def prior_cost(c: dict) -> float:
    cost = 0.0
    for k, v in c.items():
        if k.endswith("_scale"):
            cost += (math.log(v) / 0.5) ** 2
        elif k.endswith("tonic_drive"):
            cost += (v / 2.0) ** 2
    return cost


def objective(r: dict, seeds=(0, 1, 2)) -> float | None:
    if any(s not in r["silent"] for s in seeds):
        return None
    pen = sum(10 * math.log1p(r["silent"][s]) for s in seeds)
    if r["mn9"] is not None:
        pen += 10 * max(0.0, 5.5 - r["mn9"])
    return prior_cost(r["cand"]) + pen


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("cmd", choices=["launch", "collect"])
    ap.add_argument("batch")
    ap.add_argument("cands", nargs="?")
    ap.add_argument("--par", type=int, default=6)
    ap.add_argument("--seeds", default="0,1,2")
    ap.add_argument("--no-sugar", action="store_true")
    a = ap.parse_args()
    if a.cmd == "launch":
        launch(a.batch, json.loads(Path(a.cands).read_text()), a.par,
               [int(s) for s in a.seeds.split(",")], not a.no_sugar)
    else:
        for i, r in enumerate(collect(a.batch)):
            print(i, r["cand"], r["silent"], None if r["mn9"] is None else round(r["mn9"], 2),
                  None if r["J"] is None else round(r["J"], 2))
