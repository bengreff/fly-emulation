"""Score the model's resistance reflex against one recorded slow tibia flexor MN.

Order is enforced so a sealed held-out cell is opened only after the model's
outputs are saved:
  1. run the model protocol (scripts/probes/azevedo_reflex.py) for the standard
     conditions, in 3 parallel foreground subprocesses, and save them;
  2. extract the cell (scripts/azevedo_slow_mn.py --cell ...);
  1b. refuse (cell unopened) if the probe missed any start/end angle by > 1.5 deg
     (session 7: a leg that generates torque can beat a soft probe);
  3. score H1-H3 (DECISIONS 6b):
     H1 sign of d_hold agrees in >= 75% of step/ramp conditions excluding 0.8 deg;
     H2 d_hold of the 2.4 and 8 deg extension steps within a factor of 2 of measured;
     H3 extension-ramp transient > hold at every speed.

    uv run python scripts/score_reflex.py --cell 181021_F1_C1 --tag <candidate> [--set K=V ...]
"""
import argparse
import json
import subprocess
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
CONDS = [["step:-8", "step:-2.4", "step:-0.8", "step:8", "step:2.4"],
         ["step:0.8", "ramp:-8:40", "ramp:-8:80", "ramp:-8:120", "ramp:-8:240"],
         ["ramp:8:40", "ramp:8:80", "ramp:8:120", "ramp:8:240"]]


CLAMP_TOL_DEG = 1.5   # session 7: the probe must deliver the stimulus, or the run is invalid


def run_model(sets, out, probe_args=()):
    procs = []
    for group in CONDS:
        cmd = ["uv", "run", "python", "scripts/probes/azevedo_reflex.py", "--conds", ",".join(group),
               *probe_args]
        for s in sets:
            cmd += ["--set", s]
        procs.append(subprocess.Popen(cmd, cwd=ROOT, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, text=True))
    rows = []
    for p in procs:
        stdout, _ = p.communicate(timeout=3600)        # waits: nothing is left running
        rows += [json.loads(l) for l in stdout.splitlines() if l.startswith("{")]
    df = pd.DataFrame(rows)
    df["protocol"] = df.cond.str.split(":").str[0]
    df["disp_deg"] = df.cond.str.split(":").str[1].astype(float)
    df["speed_dps"] = df.cond.apply(lambda c: float(c.split(":")[2]) if c.startswith("ramp") else np.nan)
    df.to_csv(out, index=False)
    return df


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--cell", required=True)
    ap.add_argument("--tag", required=True)
    ap.add_argument("--set", action="append", default=["motor_unit:all|force_per_spike=10"])
    ap.add_argument("--kp", type=float, default=None, help="probe stiffness (azevedo_reflex default if unset)")
    ap.add_argument("--kd", type=float, default=None)
    a = ap.parse_args()
    outdir = ROOT / "runs" / f"reflex-{a.cell}-{a.tag}"
    outdir.mkdir(parents=True, exist_ok=True)
    probe = [x for k, v in (("--kp", a.kp), ("--kd", a.kd)) if v is not None for x in (k, str(v))]
    model = run_model(a.set, outdir / "model.csv", probe)   # 1. model first, saved
    # 1b. stimulus fidelity: if the leg beat the probe, the stimulus was not delivered
    err = np.maximum((model.theta_pre - model.start).abs(), (model.theta_hold - model.end_target).abs())
    bad = model[err > CLAMP_TOL_DEG]
    if len(bad):
        (outdir / "summary.json").write_text(json.dumps(
            {"cell": a.cell, "tag": a.tag, "sets": a.set, "probe": probe, "protocol_valid": False,
             "clamp_error_deg_max": round(float(err.max()), 2), "n_bad": int(len(bad))}, indent=1))
        print(bad[["cond", "start", "end_target", "theta_pre", "theta_hold"]].to_string(index=False))
        sys.exit(f"protocol invalid: clamp error up to {err.max():.1f} deg > {CLAMP_TOL_DEG}; "
                 "cell NOT opened")
    subprocess.run(["uv", "run", "python", "scripts/azevedo_slow_mn.py", "--cell", a.cell],
                   cwd=ROOT, check=True, stdout=subprocess.DEVNULL)   # 2. then open the cell
    cell = pd.read_csv(ROOT / f"data/derived/azevedo2020_slow_mn_{a.cell.split('_')[0]}.csv")
    key = lambda d: (d.protocol, round(float(d.disp_deg), 1),  # noqa: E731
                     round(float(d.speed_dps), 0) if d.protocol == "ramp" and pd.notna(d.speed_dps) else -1)
    cm = {key(r): r for r in cell.itertuples()}
    rows = []
    for r in model.itertuples():
        m = cm.get(key(r))
        if m is None:
            continue
        rows.append(dict(cond=r.cond, model_d_hold=r.d_hold_hz, cell_d_hold=round(m.d_hold_hz, 1),
                         model_d_tr=r.d_transient_hz, cell_d_tr=round(m.d_transient_hz, 1),
                         n=int(m.n)))
    sc = pd.DataFrame(rows)
    big = sc[~sc.cond.str.contains(r":-?0\.8")]
    h1 = float((np.sign(big.model_d_hold) == np.sign(big.cell_d_hold)).mean()) if len(big) else np.nan
    h2 = []
    for c in ("step:-2.4", "step:-8"):
        x = sc[sc.cond == c]
        if len(x):
            mv, cv = float(x.model_d_hold.iloc[0]), float(x.cell_d_hold.iloc[0])
            h2.append(cv != 0 and mv / cv >= 0.5 and mv / cv <= 2.0)
    ext_r = sc[sc.cond.str.startswith("ramp:-8")]
    h3 = bool(len(ext_r) and (ext_r.model_d_tr > ext_r.model_d_hold).all())
    summary = {"cell": a.cell, "tag": a.tag, "sets": a.set, "probe": probe, "protocol_valid": True,
               "clamp_error_deg_max": round(float(err.max()), 2), "H1_sign_agreement": round(h1, 2),
               "H1_pass": bool(h1 >= 0.75), "H2_pass": bool(h2 and all(h2)), "H3_pass": h3,
               "pass": bool(h1 >= 0.75 and h2 and all(h2))}
    sc.to_csv(outdir / "score.csv", index=False)
    (outdir / "summary.json").write_text(json.dumps(summary, indent=1))
    print(sc.to_string(index=False))
    print(json.dumps(summary))


if __name__ == "__main__":
    main()
