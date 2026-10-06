"""Score visual_flash.py runs against recorded flash amplitudes, on cells whose cartridge has photoreceptor input.

Half of the L1/L2 cells get no R1-R6 synapse in the scan (lamina truncation, F-VISION-4), so type means
dilute the response. A cell counts as connected when:
- L1/L2: at least one R1-R6 synapse (edges at the model's 5-synapse threshold);
- Mi1, Tm3: at least half of its L1 input synapses come from connected L1 cells; Tm1, Tm2 the same with L2;
- T4a-d: at least half of its Mi1 input from connected Mi1; T5a-d: of its Tm1 + Tm2 input from connected cells.
The score is the median over connected cells of the deflection where the recording peaks (from the dark
baseline, last flash of the run). Targets (DECISIONS 6 Oct, gain block): R1-R6 and Mi1 are training values
(R1-R6 fit by luminance_gain, Mi1 by the LMC release scale), and every other row is held out.

    uv run python scripts/probes/visual_flash_score.py runs/s12/vision/flash_RTc.json [more runs]
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[2]
MIN_SYN = 5
# type: (window and sign of the recorded peak, recorded mV, role, source)
TARGETS = {
    "R1-R6": ("on_max", 60.0, "train", "Juusola & Hardie 2001, >=60 mV saturating (text)"),
    "L1": ("on_min", -45.0, "held", "Zheng et al. 2006, up to 45 mV (text)"),
    "L2": ("on_min", -45.0, "held", "Zheng et al. 2006, up to 45 mV (text)"),
    "Mi1": ("on_max", 20.0, "train", "Behnia et al. 2014 Fig. 2 (figure estimate)"),
    "Tm3": ("on_max", 15.0, "held", "Behnia et al. 2014 Fig. 2 (figure estimate)"),
    "Tm1": ("off_max", 17.5, "held", "Behnia et al. 2014 Fig. 2, OFF +15-20 (figure estimate)"),
    "Tm2": ("off_max", 17.5, "held", "Behnia et al. 2014 Fig. 2, OFF +15-20 (figure estimate)"),
}
EXTRA = {"Tm1": "on_min", "Tm2": "on_min", "T4a": "on_max", "T5a": "off_max"}


def connected(types: pd.Series) -> dict[str, set[int]]:
    e = pd.read_parquet(REPO / "data/cache/male_cns_edges.parquet")
    e = e[e.weight >= MIN_SYN]
    t = types
    e = e.assign(tpre=t.reindex(e.pre).to_numpy(), tpost=t.reindex(e.post).to_numpy())
    con: dict[str, set[int]] = {}
    pr = e[e.tpre == "R1-R6"]
    for lt in ("L1", "L2"):
        con[lt] = set(pr[pr.tpost == lt].post)

    def share(post_types, pre_types, good: set[int]) -> set[int]:
        s = e[e.tpost.isin(post_types) & e.tpre.isin(pre_types)]
        s = s.assign(ok=s.pre.isin(good) * s.weight)
        g = s.groupby("post")[["ok", "weight"]].sum()
        return set(g.index[g.ok >= 0.5 * g.weight])

    con["Mi1"] = share(["Mi1"], ["L1"], con["L1"])
    con["Tm3"] = share(["Tm3"], ["L1"], con["L1"])
    con["Tm1"] = share(["Tm1"], ["L2"], con["L2"])
    con["Tm2"] = share(["Tm2"], ["L2"], con["L2"])
    for s4 in "abcd":
        con[f"T4{s4}"] = share([f"T4{s4}"], ["Mi1"], con["Mi1"])
        con[f"T5{s4}"] = share([f"T5{s4}"], ["Tm1", "Tm2"], con["Tm1"] | con["Tm2"])
    return con


def main() -> None:
    runs = sys.argv[1:]
    nn = pd.read_parquet(REPO / "data/cache/male_cns_neurons.parquet", columns=["bodyId", "type"])
    types = nn.set_index("bodyId").type.fillna("")
    con = connected(types)
    out = {}
    for r in runs:
        d = json.loads(Path(r).read_text())
        cells = d.get("cells", {})
        print(f"== {r}  set {d['meta']['set']}")
        if "bounds" in d["meta"]:
            b = d["meta"]["bounds"]
            print(f"  cells outside {b['range_mv']} mV: {b['n_outside']} of {b['n']} (extremes {b['vmin']} / "
                  f"{b['vmax']}) {b['types']}")
        rows = {}
        for ty, key in [(k, v[0]) for k, v in TARGETS.items()] + list(EXTRA.items()):
            if ty not in cells:
                continue
            c = cells[ty]
            b = np.asarray(c["bodyId"])
            v = np.asarray(c[key])
            m = np.isin(b, list(con[ty])) if ty in con else np.ones(b.size, bool)
            med = float(np.median(v[m])) if m.any() else float("nan")
            tgt = TARGETS.get(ty) if TARGETS.get(ty, ("",))[0] == key else None
            base = d["res"][ty]["flashes"][-1]["base_mv"]
            rows[f"{ty}:{key}"] = {"median_connected": round(med, 3), "base_mv": base, "n_connected": int(m.sum()), "n": int(b.size),
                                   "median_all": round(float(np.median(v)), 3),
                                   "recorded": tgt[1] if tgt else None, "role": tgt[2] if tgt else "extra"}
            tx = f"recorded {tgt[1]:+.1f} ({tgt[2]})  ratio {med / tgt[1]:.3f}" if tgt else ""
            print(f"  {ty:6s} {key:7s} dark {base:6.1f}  median connected {med:+8.3f} (n {m.sum()}/{b.size}; all {np.median(v):+7.3f})  {tx}")
        out[r] = rows
    for r in runs:
        Path(r).with_suffix(".score.json").write_text(json.dumps(out[r], indent=1))


if __name__ == "__main__":
    main()
