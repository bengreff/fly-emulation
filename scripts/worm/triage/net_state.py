"""Item 4c (wtriage, 8 Nov 2026; diagnostic, no bar): where the whole brain's saturated/silent swing comes from.

Pre-registered (before the first run): the template worm at the ledger values (at_ledger.patch, sample_worm(None)),
the code's default toggles, brain only (no body, step(None), dt 1 ms), 6 bio s from reset; statistics over the last
2 s for the 302 neurons: the fraction above -20 mV, the fraction below -70 mV, the median voltage, and the fraction
whose voltage moves less than 1 mV over those 2 s (pinned). Conditions, one process each:
  default       as built
  mask_off      expression_map off (BAAIWorm's per-cell densities without the CeNGEN mask, brain.py:427-433)
  isolated      default, no synapses and no gaps (single_cell_sanity's wiring patch): the cells' own resting state
  isolated_mask isolated with expression_map off
  syn_x0.5      every chemical pair's strength times 0.5 (syn_strength_per_pair and, since the class rule
                replaces it by default, every syn_nchan_per_em_*; amended 14:24 before the rerun)
  syn_x2, syn_x4  times 2 and 4 (x4 added 14:24 with the amendment)
No published bar exists for "fraction above -20 mV" (C. elegans neurons are mostly graded; see DEBUG_TRIAGE item 4c),
so this scores nothing. It asks two questions: how many of the default network's depolarised cells are depolarised on
their own (isolated), and how far the fraction moves for a 2x change in one shared guessed strength.

Usage (backhouse): python net_state.py CONDITION [SECONDS]
Output: runs/worm/triage/net_state/CONDITION.json
"""
from __future__ import annotations

import json
import sys
import time
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "scripts" / "worm"))
import at_ledger  # noqa: E402

at_ledger.patch()
from wormemu import brain as B  # noqa: E402


def main():
    cond = sys.argv[1]
    secs = float(sys.argv[2]) if len(sys.argv) > 2 else 6.0
    tog, spec = {}, B.sample_worm(None)
    if cond in ("mask_off", "isolated_mask"):
        tog["expression_map"] = "off"
    if cond.startswith("isolated"):
        B.Brain._wire_cook = lambda self: None
        B.Brain._wire_baaiworm = lambda self: None
    if cond.startswith("syn_x"):
        f = float(cond[5:])
        spec.values = dict(spec.values)
        spec.values["syn_strength_per_pair"] = spec.values["syn_strength_per_pair"] * f
        # with structure_rules on (the default) the per-pair value is replaced by the class rule (brain.py:717-718):
        # scale every class's syn_nchan_per_em_* too (the first syn_x runs, 14:17, scaled only the per-pair value
        # and matched default to every printed digit, so they were void)
        from wormemu.mech import structure_rules as SR
        for sp in SR.SPECS:
            if sp.id.startswith("syn_nchan_per_em_"):
                spec.values[sp.id] = f * float(spec.values.get(sp.id, sp.template))
    t0 = time.time()
    b = B.Brain(spec, toggles=tog)
    t_build = time.time() - t0
    neur = ~b.is_muscle
    b.reset()
    n, keep = int(round(secs * 1000)), int(round(min(2.0, secs / 2) * 1000))
    V = np.zeros((keep, int(neur.sum())), np.float32)
    finite = True
    t0 = time.time()
    for k in range(n):
        o = b.step(None, 1.0)
        v = o.v_mV[neur]
        finite &= bool(np.isfinite(v).all())
        if k >= n - keep:
            V[k - (n - keep)] = v
    names = [c for c, m in zip(b.cell_names, neur) if m]
    last = V[-1]
    hi, lo = (V.mean(0) > -20), (V.mean(0) < -70)
    out = dict(condition=cond, seconds=secs, finite=finite, build_s=t_build, wall_per_bio_s=(time.time() - t0) / secs,
               n_neurons=len(names), frac_above_m20=float(hi.mean()), frac_below_m70=float(lo.mean()),
               median_v=float(np.median(V.mean(0))), frac_pinned=float(((V.max(0) - V.min(0)) < 1.0).mean()),
               v_max=float(V.max()), v_min=float(V.min()),
               above=[c for c, x in zip(names, hi) if x], below=[c for c, x in zip(names, lo) if x],
               v_mean={c: round(float(x), 2) for c, x in zip(names, V.mean(0))}, v_last_max=float(last.max()))
    p = ROOT / "runs/worm/triage/net_state" / f"{cond}.json"
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(out, indent=1))
    print(cond, "above -20: %.3f  below -70: %.3f  pinned %.3f  median %.1f mV  %.1f s/bio s" % (
        out["frac_above_m20"], out["frac_below_m70"], out["frac_pinned"], out["median_v"], out["wall_per_bio_s"]),
        flush=True)


if __name__ == "__main__":
    main()
