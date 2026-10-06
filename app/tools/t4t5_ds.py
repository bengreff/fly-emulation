"""T4/T5 direction selectivity of a model profile, in one command: record the watched
visual pathway with moving bars, then report per T4/T5 subtype whether the cells respond
and whether they prefer the direction that subtype prefers in flies.

    .venv/bin/python app/tools/t4t5_ds.py --profile m9r --out runs/app/t4t5/m9r
    .venv/bin/python app/tools/t4t5_ds.py --profile <rung> [--set 'entity|property=value'] \\
        [--model-root ~/fly-emulation] [--parallel 7] --out runs/app/t4t5/<label>

--model-root records the model in another checkout (its src/ and data/), so a rung on the
fly worker's branch can be tested without merging the app; the recordings note that
checkout's commit. Recording is resumable (complete runs are skipped) and goes through
run_library.py, so on the Mac each run takes a slot from the Director's limiter.
--analyse-only re-reads the recordings in --out.

Cost (measured on backhouse, 7 at a time: about 330 s and 2.4 to 3 GB per 2 s run): 17
runs for both stimulus sets, about 15 minutes at --parallel 7 on backhouse; on the Mac
expect about an hour at the limiter's pace.

The design was fixed on 6 October 2026 before any rung was tested; it is the fly worker's
held-out test for per-type temporal dynamics, so run it on a rung once its values are set,
not while fitting them, and record each call in DECISIONS.

Stimuli: fixed files in app/protocols/t4t5 (each run records the file's md5), built once by
--write-stimuli with eye_sweep.py's bars on the patch and watch list of the library control
app/protocols/eye/control-watch-visual-m9r-s0.json (19 left-eye ommatidia around 298); the
medulla bars are the events of the graded-medulla run, so that run is the reference:
  medulla        ON bars into the T4 inputs under the bar (Mi1, Tm3, Mi4, C3 +4 mV; Mi9
                 -4 mV) and OFF bars into the T5 inputs (Tm1, Tm2 +4 mV), 4 directions.
                 Tests the circuit from the medulla inputs to T4/T5.
  photoreceptor  ON (+3 mV) and OFF (-3 mV) bars into R1-R6, R7 and R8 of the ommatidia
                 under the bar, 4 directions. Tests the whole path from the eye.
Bars are current injected through the model's external input (labelled an approximation;
the arena has no moving stimulus yet), 2 columns wide, one column every 50 ms, swept twice
(300 and 1100 ms). Both sets share one control. Amplitudes are guessed.

Readout, per watched T4/T5 cell (17 to 19 per subtype): the peak change in membrane
potential against the control (same seed, so identical until the first bar) over both
sweeps. T4 are read from the ON bars, T5 from the OFF bars. DSI = (pref - null) /
(|pref| + |null|) per cell, with the direction each subtype prefers in flies (Maisak et
al. 2013: a front-to-back, b back-to-front, c upward, d downward; on the left-eye mosaic
-x, +x, -y, +y, inferred). Two-sided Wilcoxon signed-rank test of pref - null across
cells, Holm-corrected over the 8 subtypes of a stimulus set. Verdict per subtype:
  no response                    median peak below 0.5 mV in all 4 directions (guessed floor)
  not selective                  Holm p >= 0.05
  selective as in flies          Holm p < 0.05 and median DSI > 0
  selective, opposite to flies   Holm p < 0.05 and median DSI < 0
A stimulus set passes when all 8 subtypes are selective as in flies; that needs opposite
preferences within each pair (a/b, c/d), which a bias shared by all cells cannot give.
Reference (the graded-medulla variant, APP_DESIGN section 14): T4/T5 respond to medulla
bars (peaks 1.2 to 2.0 mV) with |DSI| at most 0.02: not selective.
"""
from __future__ import annotations

import argparse
import copy
import hashlib
import json
import os
import subprocess
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import stats

APP = Path(__file__).resolve().parents[1]
REPO = APP.parent
sys.path.insert(0, str(APP / "tools"))
from eye_sweep import CONTROL, DIR_NOTE, DIRS, OFF, ON, PR_MV, SWEEPS_MS, bar_events  # noqa: E402
from eye_ds import NULL, PREF, load, window  # noqa: E402

STIM = APP / "protocols" / "t4t5"
SETS = {"medulla": "med", "photoreceptor": "pr"}
RESP_MV = 0.5        # guessed floor for "responds"
ALPHA = 0.05
SUBTYPES = [f"T{i}{s}" for i in "45" for s in "abcd"]
PATHWAY = ["R1-R6", "R7", "R8", "L1", "L2", "L3", "L4", "L5", "Mi1", "Tm3", "Mi4", "Mi9", "C3",
           "Tm1", "Tm2", "Tm4", "Tm9", "T4", "T5"]
FLIES = ("In flies T4 respond to ON edges and T5 to OFF edges, and each subtype prefers one "
         "direction: a front-to-back, b back-to-front, c upward, d downward (Maisak et al. 2013, "
         "calcium imaging).")


def protocols(profile: str, seed: int, overrides: dict, extra: str | None, sets: list[str]) -> dict:
    """The control and the bar runs of the chosen sets, as flyemu-protocol/1 dicts keyed by
    run name: the fixed stimuli in app/protocols/t4t5 with the model to test filled in."""
    label = f"{profile} seed {seed}" + (" with overrides" if overrides else "") + (" with variant rows" if extra else "")
    tags = {"control"} | {SETS[s] for s in sets}
    out = {}
    for f in sorted(STIM.glob("*.json")):
        if f.stem.split("-")[0] not in tags:
            continue
        p = json.loads(f.read_text())
        p["title"] += f", {label}"
        p["config"].update(profile=profile, seed=seed, overrides=dict(overrides))
        if extra:
            p["config"]["extra_params"] = extra
            p["variant"] = {"name": "extra per-type rows", "rows": extra,
                            "note": "a labelled variant of the profile; not adopted"}
        p["harness"]["stimulus_md5"] = hashlib.md5(f.read_bytes()).hexdigest()
        out[f.stem] = p
    return out


def build_stimuli() -> dict:
    """The fixed stimuli (written once with --write-stimuli, from the eye mosaic and the column
    placement; both are built, not tracked, so the files are what the test ships)."""
    ctl = json.loads(CONTROL.read_text())
    body = APP / "data" / "body" / "flybody"
    eye, cols = json.loads((body / "eye.json").read_text()), json.loads((body / "columns.json").read_text())
    omm = np.c_[eye["centroid"]["x"], eye["centroid"]["y"]]
    sp, centre = cols["spacing_px"], omm[ctl["watch_note"]["patch_centre_ommatidium"]]
    c = cols["cells"]
    names = np.asarray(cols["types"])[np.asarray(c["type"])]
    left = np.asarray(c["eye"]) == 0
    cpos, cid = np.c_[c["x"], c["y"]], np.asarray(c["bodyId"], np.int64)
    pr = eye["photoreceptors"]["L"]
    ppos, pid = omm[np.asarray(pr["ommatidium"])], np.asarray(pr["bodyId"], np.int64)

    def base(title: str) -> dict:
        p = copy.deepcopy(ctl)
        p["title"] = f"T4/T5 direction test: {title}"
        p["config"].pop("extra_params", None)
        p["expect"] = {"text": FLIES, "source": "Maisak et al. 2013 Nature 500:212", "status": "observed in flies"}
        p["harness"] = {"tool": "app/tools/t4t5_ds.py"}
        p["events"] = []
        return p

    out = {"control": base("control with the visual pathway watched")}
    for d in DIRS:
        for pol, pat, what in (("on", ON, "ON bar into T4 inputs"), ("off", OFF, "OFF bar into T5 inputs")):
            m = left & np.isin(names, list(pat))
            p = base(f"{what} moving {d} ({DIR_NOTE[d]})")
            p["events"] = bar_events(cpos[m], cid[m], np.array([pat[t] for t in names[m]]), d, centre, sp, what)
            out[f"med-{pol}{d}"] = p
        for pol, mv in (("on", PR_MV), ("off", -PR_MV)):
            what = f"photoreceptor {pol.upper()} bar"
            p = base(f"{what} moving {d} ({DIR_NOTE[d]})")
            p["events"] = bar_events(ppos, pid, np.full(len(pid), mv), d, centre, sp, what)
            out[f"pr-{pol}{d}"] = p
    for k, p in out.items():
        p["harness"].update(run=k)
    return out


def holm(ps: dict) -> dict:
    order = sorted(ps, key=ps.get)
    out, run_max = {}, 0.0
    for i, k in enumerate(order):
        run_max = max(run_max, min(1.0, ps[k] * (len(order) - i)))
        out[k] = run_max
    return out


def verdict(peak_by_dir: dict, pref: str, null: str, p_holm: float) -> tuple[str, float]:
    pp, pn = np.asarray(peak_by_dir[pref]), np.asarray(peak_by_dir[null])
    den = np.abs(pp) + np.abs(pn)
    dsi = float(np.median(np.where(den > 1e-6, (pp - pn) / np.where(den > 1e-6, den, 1), 0.0)))
    if max(float(np.median(v)) for v in peak_by_dir.values()) < RESP_MV:
        return "no response", dsi
    if p_holm >= ALPHA:
        return "not selective", dsi
    return ("selective as in flies" if dsi > 0 else "selective, opposite to flies"), dsi


def score(peaks: dict) -> dict:
    """peaks[subtype][direction] = per-cell peak change (mV) -> per-subtype statistics and verdicts."""
    res, ps = {}, {}
    for T, by in peaks.items():
        pref = PREF[T[-1]]
        diff = np.asarray(by[pref]) - np.asarray(by[NULL[pref]])
        ps[T] = float(stats.wilcoxon(diff).pvalue) if np.any(diff != 0) else 1.0
        res[T] = {"n_cells": len(diff), "pref_in_flies": pref,
                  "median_peak_mv": {d: round(float(np.median(v)), 3) for d, v in by.items()},
                  "wilcoxon_p": ps[T]}
    for T, p in holm(ps).items():
        res[T]["holm_p"] = p
        res[T]["verdict"], res[T]["median_dsi"] = verdict(peaks[T], res[T]["pref_in_flies"],
                                                         NULL[res[T]["pref_in_flies"]], p)
        res[T]["median_dsi"] = round(res[T]["median_dsi"], 3)
        med = res[T]["median_peak_mv"]
        res[T]["best_direction"] = max(med, key=med.get)
    n_ok = sum(r["verdict"] == "selective as in flies" for r in res.values())
    return {"subtypes": res, "n_selective_as_in_flies": n_ok, "n_subtypes": len(res),
            "pass": n_ok == len(res) == 8}


def analyse(out: Path, sets: list[str]) -> dict:
    tmap = pd.read_parquet(REPO / "data" / "cache" / "male_cns_neurons.parquet",
                           columns=["bodyId", "type"]).set_index("bodyId")["type"]
    ctl = load(out / "control")
    ty = tmap.reindex(ctl["bid"]).astype(str).to_numpy()
    group = np.array(["R7" if T.startswith("R7") else "R8" if T.startswith("R8") else T[:2] if T[:2] in ("T4", "T5")
                      else T for T in ty])
    t = ctl["t"]
    w, pre = window(t), t < SWEEPS_MS[0]
    man = ctl["manifest"]
    prov = man.get("provenance", {})
    rep = {"tool": "app/tools/t4t5_ds.py", "basis": "measured in the recordings (mV); derived statistics",
           "profile": man["config"].get("profile"), "seed": man["config"].get("seed"),
           "overrides": man["config"].get("overrides"), "extra_params": man.get("extra_params"),
           "profile_status": man.get("profile_status"), "app_commit": prov.get("git", {}).get("commit"),
           "model_src": prov.get("model_src"), "response_floor_mv": RESP_MV, "alpha": ALPHA,
           "checks": {}, "pathway": {}, "sets": {}}
    for s in sets:
        tag = SETS[s]
        peaks = {T: {} for T in SUBTYPES}
        rep["pathway"][s] = {}
        for pol in ("on", "off"):
            fam = "T4" if pol == "on" else "T5"
            path = {}
            for d in DIRS:
                r = load(out / f"{tag}-{pol}{d}")
                if not np.array_equal(r["bid"], ctl["bid"]):
                    raise SystemExit(f"{tag}-{pol}{d}: watch list differs from the control")
                (st, sr), (cs, cr) = r["spikes"], ctl["spikes"]
                rep["checks"][f"{tag}-{pol}{d}"] = bool(
                    np.array_equal(r["v"][pre], ctl["v"][pre]) and np.array_equal(st[st < SWEEPS_MS[0]], cs[cs < SWEEPS_MS[0]])
                    and np.array_equal(sr[st < SWEEPS_MS[0]], cr[cs < SWEEPS_MS[0]]))
                dv = r["v"][w] - ctl["v"][w]
                pk, tr = dv.max(0), dv.min(0)
                for T in SUBTYPES:
                    if T.startswith(fam):
                        peaks[T][d] = pk[ty == T].tolist()
                for g in PATHWAY:
                    if (group == g).any():
                        path.setdefault(g, []).append((float(np.median(pk[group == g])), float(np.median(tr[group == g]))))
            rep["pathway"][s][pol] = {g: {"peak_mv": round(max(x[0] for x in v), 3), "trough_mv": round(min(x[1] for x in v), 3)}
                                      for g, v in path.items()}
        rep["sets"][s] = score(peaks)
        rep["sets"][s]["peaks_mv"] = {T: {d: [round(x, 3) for x in v] for d, v in by.items()} for T, by in peaks.items()}
    rep["paired"] = all(rep["checks"].values())
    return rep


def report(rep: dict) -> str:
    L = [f"T4/T5 direction test: profile {rep['profile']}, seed {rep['seed']}"
         + (f", overrides {rep['overrides']}" if rep["overrides"] else "")
         + (f", variant rows {rep['extra_params']['path']}" if rep["extra_params"] else ""),
         f"  status: {rep['profile_status']}; app commit {rep['app_commit']}"
         + (f"; model from {rep['model_src']['root']} at {rep['model_src'].get('commit')}" if rep["model_src"] else ""),
         "  paired with the control (identical before the first bar): "
         + ("yes" if rep["paired"] else "NO: " + ", ".join(k for k, v in rep["checks"].items() if not v))]
    for s, r in rep["sets"].items():
        L.append(f"\n{s} bars: {'PASS' if r['pass'] else 'FAIL'}, {r['n_selective_as_in_flies']} of 8 subtypes "
                 "selective as in flies")
        L.append("  pathway, median over watched cells of the largest rise/fall (mV), ON bars | OFF bars:")
        on, off = rep["pathway"][s]["on"], rep["pathway"][s]["off"]
        cells = [f"{g:5s} {on[g]['peak_mv']:+.2f}/{on[g]['trough_mv']:+.2f} | {off[g]['peak_mv']:+.2f}/"
                 f"{off[g]['trough_mv']:+.2f}" for g in on]
        L += ["    " + "    ".join(cells[i:i + 4]) for i in range(0, len(cells), 4)]
        for T, x in r["subtypes"].items():
            m = x["median_peak_mv"]
            L.append(f"  {T}: {x['verdict']:29s} DSI {x['median_dsi']:+.2f}  Holm p {x['holm_p']:.2g}  peak (mV) "
                     + " ".join(f"{d} {m[d]:+.2f}" for d in DIRS) + f"  (flies prefer {x['pref_in_flies']}, n {x['n_cells']})")
    return "\n".join(L)


def figure(rep: dict, png: Path) -> None:
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    short = {"+x": "B>F", "-x": "F>B", "+y": "down", "-y": "up"}
    sets = list(rep["sets"])
    fig, axs = plt.subplots(len(sets), 2, figsize=(11, 3.6 * len(sets)), squeeze=False, sharey=True)
    top = 0.6 + max(max(v) for s in sets for by in rep["sets"][s]["peaks_mv"].values() for v in by.values())
    rng = np.random.default_rng(0)
    for row, s in enumerate(sets):
        for col, fam in enumerate(("T4", "T5")):
            ax = axs[row][col]
            for j, sub in enumerate("abcd"):
                T = f"{fam}{sub}"
                x_ = rep["sets"][s]["subtypes"][T]
                for i, d in enumerate(DIRS):
                    pk = np.asarray(rep["sets"][s]["peaks_mv"][T][d])
                    x = j * 5 + i
                    c = "#c44" if d == x_["pref_in_flies"] else "#48c" if d == NULL[x_["pref_in_flies"]] else "#aaa"
                    ax.bar(x, np.median(pk), color=c, width=0.85, alpha=0.6)
                    ax.plot(x + rng.uniform(-0.25, 0.25, len(pk)), pk, ".", ms=2.5, color="k")
                ax.text(j * 5 + 1.5, top - 0.05 * top, f"{T}\nDSI {x_['median_dsi']:+.2f}\n{x_['verdict']}",
                        ha="center", va="top", fontsize=6.5)
            ax.set_xticks([j * 5 + i for j in range(4) for i in range(4)])
            ax.set_xticklabels([short[d] for _ in range(4) for d in DIRS], fontsize=6, rotation=90)
            ax.axhline(0, color="k", lw=0.5)
            ax.set_ylim(min(-0.1, ax.get_ylim()[0]), top)
            ax.set_title(f"{s} {'ON' if fam == 'T4' else 'OFF'} bars: {fam}", fontsize=9)
        axs[row][0].set_ylabel("peak change vs control (mV)")
    fig.suptitle(f"T4/T5 direction test, {rep['profile']} seed {rep['seed']} ({rep['profile_status']})\nBars: median "
                 "over watched cells (dots). Red: the direction flies prefer (Maisak et al. 2013); blue: its opposite; "
                 "grey: other axis. F>B front-to-back.", fontsize=8)
    fig.tight_layout()
    fig.savefig(png, dpi=110)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--profile", required=True, help="model profile to test (flyemu.profiles)")
    ap.add_argument("--set", action="append", default=[], metavar="'entity|property=value'",
                    help="override added to the profile (repeatable; the runs are labelled custom)")
    ap.add_argument("--extra-params", help="candidate per-type rows (record.py --extra-params; labelled a variant)")
    ap.add_argument("--model-root", type=Path, help="checkout whose src/ and data/ hold the model (default: this one)")
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--stimulus", choices=["medulla", "photoreceptor", "both"], default="both")
    ap.add_argument("--parallel", type=int, default=1, help="runs at once; about 3 GB each")
    ap.add_argument("--timeout-min", type=float, default=45.0, help="per run")
    ap.add_argument("--out", type=Path, required=True)
    ap.add_argument("--analyse-only", action="store_true")
    ap.add_argument("--write-stimuli", action="store_true", help="maintenance: rewrite app/protocols/t4t5 "
                    "from the eye mosaic and column placement (changes the held-out test; say so in DECISIONS)")
    if "--write-stimuli" in sys.argv:
        STIM.mkdir(parents=True, exist_ok=True)
        for k, p in build_stimuli().items():
            (STIM / f"{k}.json").write_text(json.dumps(p, indent=1) + "\n")
        print(f"wrote {len(list(STIM.glob('*.json')))} files to {STIM}")
        return 0
    a = ap.parse_args()
    sets = list(SETS) if a.stimulus == "both" else [a.stimulus]
    overrides = {}
    for item in a.set:
        k, _, v = item.partition("=")
        overrides[k] = float(v)
    if not a.analyse_only:
        pdir = a.out / "protocols"
        pdir.mkdir(parents=True, exist_ok=True)
        for name, p in protocols(a.profile, a.seed, overrides, a.extra_params, sets).items():
            f, text = pdir / f"{name}.json", json.dumps(p, indent=1) + "\n"
            if f.exists() and f.read_text() != text:
                raise SystemExit(f"{f} was written with other settings; use a new --out")
            f.write_text(text)
        env = {k: v for k, v in os.environ.items() if k != "FLYEMU_EXTRA_PARAMS"}
        env.update(OMP_NUM_THREADS="1", OPENBLAS_NUM_THREADS="1", MKL_NUM_THREADS="1")
        if a.model_root:
            env["FLYAPP_MODEL_ROOT"] = str(a.model_root.expanduser().resolve())
        r = subprocess.run([sys.executable, str(APP / "tools" / "run_library.py"), "--protocols", str(pdir),
                            "--out", str(a.out), "--parallel", str(a.parallel), "--timeout-min", str(a.timeout_min)],
                           cwd=REPO, env=env)
        if r.returncode:
            return r.returncode
    rep = analyse(a.out, sets)
    (a.out / "ds.json").write_text(json.dumps(rep, indent=1) + "\n")
    figure(rep, a.out / "ds.png")
    print(report(rep))
    print(f"\nwrote {a.out / 'ds.json'} and {a.out / 'ds.png'}")
    return 0 if all(r["pass"] for r in rep["sets"].values()) else 3


if __name__ == "__main__":
    raise SystemExit(main())
