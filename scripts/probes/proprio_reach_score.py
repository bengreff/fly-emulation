"""Score proprio_reach.py runs against the step R criterion (DECISIONS 13 Oct 23:58).

A pool is reached if max/min of its rate across the two stimulus bins (flexing vs extending for clamp, during vs
before for load) is >= 1.25 with a difference >= 2 Hz per MN; for clamp, the same pool's ratio in the matching
zero-afferent control must be < 1.08.

    uv run python scripts/probes/proprio_reach_score.py [runs/s13/proprio/reach]
"""
import json
import sys
from pathlib import Path


def ratio(v, stim):
    a, b = (v["flexing"], v["extending"]) if stim == "clamp" else (v["during"], v["before"])
    return (max(a, b) + 1e-3) / (min(a, b) + 1e-3), abs(a - b)


def main() -> None:
    d = Path(sys.argv[1] if len(sys.argv) > 1 else "runs/s13/proprio/reach")
    runs = {p.stem: json.loads(p.read_text()) for p in sorted(d.glob("*.json"))}
    for tag, r in runs.items():
        ctrl = runs.get(f"clamp_{r['leg']}_zero") if r["stim"] == "clamp" else None
        print(f"== {tag}  gain {r['gain_mv']:g} mV  zero {r['zero_afferents']}  warnings {r['warnings']}  "
              f"wall {r['wall_s']} s")
        reached = []
        for nme, v in r["pools_hz_per_mn"].items():
            rat, diff = ratio(v, r["stim"])
            crat = ratio(ctrl["pools_hz_per_mn"][nme], "clamp")[0] if ctrl and not r["zero_afferents"] else None
            hit = rat >= 1.25 and diff >= 2.0 and (crat is None or crat < 1.08) and not r["zero_afferents"]
            reached += [nme] if hit else []
            bins = " ".join(f"{k} {v[k]:6.2f}" for k in v if k != "n")
            c = f" ctrl {crat:4.2f}" if crat is not None else ""
            print(f"  {nme:34s} n {v['n']:2d}  {bins}  ratio {rat:5.2f}{c}{'  REACHED' if hit else ''}")
        print("  afferents Hz/cell:", {g: {k: x for k, x in v.items() if k != 'n'} | {"n": v["n"]}
                                       for g, v in r["afferent_hz_per_cell"].items()})
        print("  inhibitors Hz/cell:", {g: [x for k, x in v.items() if k != "n"] for g, v in r["inhibitor_hz_per_cell"].items()})
        print("  reached:", reached or "none")


if __name__ == "__main__":
    main()
