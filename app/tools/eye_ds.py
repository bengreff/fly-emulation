"""Read the graded-medulla variant runs (app/tools/eye_sweep.py): do T4/T5 respond, and
are they direction selective?

    .venv/bin/python app/tools/eye_ds.py [--runs runs/app/eye] [--png docs/media/app_eye_ds.png]

For every watched T4/T5 cell (one per subtype per ommatidium of the left-eye patch) the
response to a moving bar is the change in membrane potential against the variant's own
control, which shares every random draw: mean and peak over both sweeps (each from its
start to 50 ms after its last step). Direction selectivity per cell is
DSI = (R_pref - R_null) / (|R_pref| + |R_null|) on the mean change in potential, with the
preferred direction from Maisak et al. 2013 (T4a/T5a front-to-back, b back-to-front,
c upward, d downward); on the left eye front-to-back is mosaic -x and upward -y
(inferred, eye_sweep.py). The test across cells is a two-sided Wilcoxon signed-rank
test of R_pref - R_null, Holm-corrected within each set of bars. Also checked: the runs
are identical to their control before the first bar (the variant changes nothing else).
Writes runs/app/eye/graded-summary.json and, with --png, a figure.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import stats

APP = Path(__file__).resolve().parents[1]
REPO = APP.parent
sys.path.insert(0, str(APP / "server"))
from recfmt import RecReader  # noqa: E402

V_REST, V_TH = -52.0, -45.0           # m9r, all cells (lif.default_params; inferred)
SWEEPS_MS, SPAN_MS = (300.0, 1100.0), 650.0
PREF = {"a": "-x", "b": "+x", "c": "-y", "d": "+y"}           # Maisak et al. 2013, left-eye mosaic axes
NULL = {"-x": "+x", "+x": "-x", "-y": "+y", "+y": "-y"}
DIRS = ["+x", "-x", "+y", "-y"]
COLUMNAR = ["L1", "L2", "L3", "Mi1", "Tm3", "Mi4", "Mi9", "C3", "Tm1", "Tm2", "Tm4", "Tm9"]


def load(path: Path) -> dict:
    R = RecReader(path)
    st = R.static()
    ch = [R.chunk(i) for i in range(len(R))]
    v = np.concatenate([c["v"] for c in ch]).astype(float)
    t = np.concatenate([c["v_step"] for c in ch]) * R.manifest["timestep_ms"]
    rows = np.asarray(st["watch_rows"])
    return {"v": v, "t": t, "bid": np.asarray(st["row_bodyid"])[rows].astype(np.int64),
            "spikes": R.all_spikes(), "manifest": R.manifest}


def window(t: np.ndarray) -> np.ndarray:
    return np.any([(t >= s) & (t < s + SPAN_MS) for s in SWEEPS_MS], axis=0)


def summary_v(v: np.ndarray, m: np.ndarray, late: np.ndarray) -> dict:
    x = v[late][:, m]
    return {"n": int(m.sum()), "median_mv": round(float(np.median(x)), 3), "max_mv": round(float(x.max()), 3),
            "min_mv": round(float(x.min()), 3), "sd_over_time_mv": round(float(np.median(x.std(0))), 3),
            "frac_above_rest": round(float(np.mean(x > V_REST)), 4),
            "mean_output": round(float(np.mean(np.clip((x - V_REST) / (V_TH - V_REST), 0, 1))), 4)}


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--runs", type=Path, default=REPO / "runs" / "app" / "eye")
    ap.add_argument("--png", type=Path)
    a = ap.parse_args()
    nr = pd.read_parquet(REPO / "data" / "cache" / "male_cns_neurons.parquet", columns=["bodyId", "type"])
    tmap = nr.set_index("bodyId")["type"]
    run = {k: load(a.runs / f"{k}-m9r-s0") for k in
           ["graded-A-control", "graded-B-control"] + [f"graded-A-{p}{d}" for p in ("on", "off") for d in DIRS]
           + [f"graded-B-pr{d}" for d in DIRS]}
    run["m9r-control"] = load(a.runs / "m9r-control-watch-s0")
    ty = tmap.reindex(run["m9r-control"]["bid"]).astype(str).to_numpy()
    for k, r in run.items():
        assert np.array_equal(r["bid"], run["m9r-control"]["bid"]), f"{k}: watch list differs"
    t = run["m9r-control"]["t"]
    late = t >= 200
    out = {"basis": "measured in the recordings (mV); derived statistics", "v_rest_mv": V_REST, "v_th_mv": V_TH,
           "commit": run["graded-A-control"]["manifest"]["provenance"]["git"]["commit"],
           "checks": {}, "levels": {}, "responses": {}, "ds": {}}

    # identity: a bar run equals its control before its first event (spikes and voltages)
    for k, r in run.items():
        if k.startswith("graded-") and "control" not in k:
            ctl = run["graded-A-control" if k.startswith("graded-A") else "graded-B-control"]
            pre = t < SWEEPS_MS[0]
            same_v = bool(np.array_equal(r["v"][pre], ctl["v"][pre]))
            (st, sr), (ct, cr) = r["spikes"], ctl["spikes"]
            same_s = bool(np.array_equal(st[st < SWEEPS_MS[0]], ct[ct < SWEEPS_MS[0]])
                          and np.array_equal(sr[st < SWEEPS_MS[0]], cr[ct < SWEEPS_MS[0]]))
            out["checks"][k] = {"identical_before_first_bar_v": same_v, "identical_before_first_bar_spikes": same_s}

    # levels: where each stage sits in the three controls
    for k in ("m9r-control", "graded-A-control", "graded-B-control"):
        out["levels"][k] = {T: summary_v(run[k]["v"], ty == T, late) for T in
                            ["R1-R6"] + COLUMNAR + [f"T{i}{s}" for i in "45" for s in "abcd"]
                            if (ty == T).any()}

    # responses to the bars: change against the arm's control, per watched cell
    w = window(t)
    for k, r in run.items():
        if not k.startswith("graded-") or "control" in k:
            continue
        ctl = run["graded-A-control" if k.startswith("graded-A") else "graded-B-control"]
        dv = r["v"][w] - ctl["v"][w]
        res = {}
        for T in COLUMNAR + [f"T{i}{s}" for i in "45" for s in "abcd"]:
            m = ty == T
            if m.any():
                res[T] = {"mean_dv": dv[:, m].mean(0).round(4).tolist(), "peak_dv": dv[:, m].max(0).round(3).tolist(),
                          "trough_dv": dv[:, m].min(0).round(3).tolist()}
        out["responses"][k] = res

    # direction selectivity: T4 from the ON medulla bars and the photoreceptor bars, T5 from the OFF bars
    pvals = []
    for arm, stem, cells in (("A medulla ON bars", "graded-A-on", "T4"), ("A medulla OFF bars", "graded-A-off", "T5"),
                             ("B photoreceptor ON bars", "graded-B-pr", "T4"), ("B photoreceptor ON bars", "graded-B-pr", "T5")):
        for s in "abcd":
            T = f"{cells}{s}"
            p, n = PREF[s], NULL[PREF[s]]
            rp = np.asarray(out["responses"][f"{stem}{p}"][T]["mean_dv"])
            rn = np.asarray(out["responses"][f"{stem}{n}"][T]["mean_dv"])
            den = np.abs(rp) + np.abs(rn)
            dsi = np.where(den > 1e-6, (rp - rn) / np.where(den > 1e-6, den, 1), 0.0)
            diff = rp - rn
            pv = float(stats.wilcoxon(diff).pvalue) if np.any(diff != 0) else 1.0
            # post hoc (added after the T5 means came out near zero, where the ratio is unstable):
            # the same index on the peak depolarisation
            pp = np.asarray(out["responses"][f"{stem}{p}"][T]["peak_dv"])
            pn = np.asarray(out["responses"][f"{stem}{n}"][T]["peak_dv"])
            pden = np.abs(pp) + np.abs(pn)
            pdsi = np.where(pden > 1e-6, (pp - pn) / np.where(pden > 1e-6, pden, 1), 0.0)
            ppv = float(stats.wilcoxon(pp - pn).pvalue) if np.any(pp != pn) else 1.0
            means = {d: float(np.mean(out["responses"][f"{stem}{d}"][T]["mean_dv"])) for d in DIRS}
            out["ds"][f"{arm}: {T}"] = {
                "n_cells": int(len(rp)), "pref_lit": p, "null_lit": n,
                "mean_dv_pref_mv": round(float(rp.mean()), 4), "mean_dv_null_mv": round(float(rn.mean()), 4),
                "mean_dv_by_direction_mv": {d: round(v, 4) for d, v in means.items()},
                "best_direction": max(means, key=means.get),
                "median_dsi": round(float(np.median(dsi)), 3), "n_dsi_positive": int((dsi > 0).sum()),
                "peak_dv_pref_median_mv": round(float(np.median(pp)), 3),
                "peak_dv_null_median_mv": round(float(np.median(pn)), 3),
                "wilcoxon_p": pv,
                "post_hoc_peak": {"median_dsi": round(float(np.median(pdsi)), 3),
                                  "n_dsi_positive": int((pdsi > 0).sum()), "wilcoxon_p": ppv}}
            pvals.append((f"{arm}: {T}", pv))
    for arm in ("A medulla ON bars", "A medulla OFF bars", "B photoreceptor ON bars"):
        ps = sorted([(p, k) for k, p in pvals if k.startswith(arm)])
        m = len(ps)
        run_max = 0.0
        for i, (p, k) in enumerate(ps):
            run_max = max(run_max, min(1.0, p * (m - i)))
            out["ds"][k]["holm_p"] = round(run_max, 5)
    path = a.runs / "graded-summary.json"
    path.write_text(json.dumps(out, indent=1) + "\n")
    print(json.dumps(out["checks"], indent=0))
    for k in ("m9r-control", "graded-A-control", "graded-B-control"):
        print(f"\n{k}")
        for T, s in out["levels"][k].items():
            print(f"  {T:6s} n={s['n']:3d} median {s['median_mv']:7.2f} min {s['min_mv']:7.2f} max {s['max_mv']:7.2f} "
                  f"sd {s['sd_over_time_mv']:.3f} >rest {s['frac_above_rest']:.3f} out {s['mean_output']:.4f}")
    print("\nresponses (median over cells of mean dV / peak dV, mV)")
    for k, res in out["responses"].items():
        print(f"  {k:20s} " + " ".join(f"{T}:{np.median(r['mean_dv']):+.2f}/{np.median(r['peak_dv']):+.2f}"
                                      for T, r in res.items()))
    print("\ndirection selectivity")
    for k, d in out["ds"].items():
        print(f"  {k:32s} n={d['n_cells']} pref({d['pref_lit']}) {d['mean_dv_pref_mv']:+.3f} null {d['mean_dv_null_mv']:+.3f} "
              f"best {d['best_direction']} medDSI {d['median_dsi']:+.2f} ({d['n_dsi_positive']}/{d['n_cells']} >0) "
              f"p {d['wilcoxon_p']:.2g} holm {d['holm_p']:.2g} | peak {d['peak_dv_pref_median_mv']:+.2f}/"
              f"{d['peak_dv_null_median_mv']:+.2f} DSI {d['post_hoc_peak']['median_dsi']:+.2f} "
              f"({d['post_hoc_peak']['n_dsi_positive']}/{d['n_cells']}) p {d['post_hoc_peak']['wilcoxon_p']:.2g}")
    print(f"\nwrote {path}")
    if a.png:
        figure(out, a.png)
    return 0


def figure(out: dict, png: Path) -> None:
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    arms = [("A medulla ON bars", "graded-A-on", "T4"), ("A medulla OFF bars", "graded-A-off", "T5"),
            ("B photoreceptor ON bars", "graded-B-pr", "T4"), ("B photoreceptor ON bars", "graded-B-pr", "T5")]
    short = {"+x": "B>F", "-x": "F>B", "+y": "down", "-y": "up"}
    fig, axs = plt.subplots(1, 4, figsize=(15, 4.2), sharey=True)
    rng = np.random.default_rng(0)
    top = 0.6 + max(max(r["peak_dv"]) for k, res in out["responses"].items() for t, r in res.items()
                    if t[:2] in ("T4", "T5"))
    for ax, (arm, stem, cells) in zip(axs, arms):
        for j, s in enumerate("abcd"):
            d = out["ds"][f"{arm}: {cells}{s}"]
            for i, k in enumerate(DIRS):
                pk = np.asarray(out["responses"][f"{stem}{k}"][f"{cells}{s}"]["peak_dv"])
                x = j * 5 + i
                col = "#c44" if k == d["pref_lit"] else "#48c" if k == d["null_lit"] else "#aaa"
                ax.bar(x, np.median(pk), color=col, width=0.85, alpha=0.6)
                ax.plot(x + rng.uniform(-0.25, 0.25, len(pk)), pk, ".", ms=2.5, color="k")
            ax.text(j * 5 + 1.5, top - 0.08, f"{cells}{s}", ha="center", va="top", fontsize=9)
            ax.text(j * 5 + 1.5, top - 0.3, f"DSI {d['post_hoc_peak']['median_dsi']:+.2f}", ha="center", va="top",
                    fontsize=7)
        ax.set_xticks([j * 5 + i for j in range(4) for i in range(4)])
        ax.set_xticklabels([short[k] for _ in range(4) for k in DIRS], fontsize=6, rotation=90)
        ax.axhline(0, color="k", lw=0.5)
        ax.set_ylim(-0.1, top)
        ax.set_title(f"{arm}: {cells}", fontsize=10)
    axs[0].set_ylabel("peak change in potential vs the arm's control (mV)")
    fig.suptitle("Graded-medulla variant (labelled, not adopted), m9r seed 0: watched T4/T5 cells of a left-eye patch, "
                 "moving bars injected as current. Bars: median of about 18 cells (dots).\n"
                 "Red: the direction the subtype prefers in flies (Maisak et al. 2013); blue: its opposite; grey: the "
                 "other axis. F>B front-to-back, B>F back-to-front (inferred axes). DSI: median per cell on the peak "
                 "(post hoc metric).", fontsize=9)
    fig.tight_layout()
    png.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(png, dpi=110)
    print(f"wrote {png}")


if __name__ == "__main__":
    raise SystemExit(main())
