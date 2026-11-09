"""pumps.Pump's reference area (wbody2, 9 Nov 2026; wbrain2's Request, b000d1a): each neuron's I_max and g_Na scale
by its membrane area over the median neuron's, and the median was taken over the cells the Brain built, so a
sub-brain gave a cell a different pump than the full brain (AIY alone 3.1x, AVAL alone 0.24x; wbrain2, derived).

This builds the full default brain once and prints, the way pumps.Mech measures them (the sum of seg.area() and
seg.volume() over every section of each hoc cell), the median membrane area over its neurons: the template of
pump_area_median_um2 (derived). With the full brain the new rule gives the old one's numbers (the check below).

Check (check=1; bar written 04:30 in the night file, before the edit): (1) the full default brain, every cell's
I_max, g_Na and volume bit-identical between the old rule (median over the built neurons) and the new one; (2) AIYL's
I_max and g_Na identical alone, with AFDL, and in the full brain.

    python pump_area_ref.py [cells=AIYL,AFDL] -> runs/worm/wbody2/pump_area_ref.json
    python pump_area_ref.py check=1 -> runs/worm/wbody2/pump_area_check.json
"""
import json
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "src"))
from wormemu import brain as B  # noqa: E402
from wormemu.mech import pumps as P  # noqa: E402


def pumps_of(cells):
    """The new rule's Pump and the old rule's I_max, g_Na and volume, for one build."""
    b = B.Brain(B.sample_worm(None), cells=cells) if cells else B.Brain(B.sample_worm(None))
    m = P.Mech(b, None, {})
    mus = np.asarray(b.is_muscle, bool)
    new = P.Pump(m.q, mus, m.geom)
    vol, area = (np.asarray(x, float) for x in m.geom)
    pick = lambda a, c: np.where(mus, m.q[c], m.q[a])
    rel = np.where(mus, 1.0, area / np.median(area[~mus]))
    old = dict(imax=pick("pump_imax_neuron_pA", "pump_imax_muscle_pA") * rel,
               gna=pick("pump_gna_neuron_nS", "pump_gna_muscle_nS") * rel,
               vol=np.where(mus, pick("pump_vol_neuron_um3", "pump_vol_muscle_um3"), vol))
    return b.cell_names, new, old


def check():
    names, new, old = pumps_of(None)
    full = {k: bool(np.array_equal(getattr(new, k), old[k])) for k in ("imax", "gna", "vol")}
    i = names.index("AIYL")
    aiy = {"full": (float(new.imax[i]), float(new.gna[i]))}
    old_aiy = {"full": (float(old["imax"][i]), float(old["gna"][i]))}
    for tag, cells in (("alone", ["AIYL"]), ("with_AFDL", ["AIYL", "AFDL"])):
        n2, p2, o2 = pumps_of(cells)
        j = n2.index("AIYL")
        aiy[tag] = (float(p2.imax[j]), float(p2.gna[j]))
        old_aiy[tag] = (float(o2["imax"][j]), float(o2["gna"][j]))
    bar2 = len(set(aiy.values())) == 1
    res = dict(bar1_full_brain_bit_identical=full, bar2_aiyl_same_in_every_build=bar2, aiyl_new=aiy, aiyl_old=old_aiy,
               PASS=bool(all(full.values()) and bar2))
    (ROOT / "runs/worm/wbody2/pump_area_check.json").write_text(json.dumps(res, indent=1))
    print(json.dumps(res, indent=1))


def main():
    kw = dict(a.split("=", 1) for a in sys.argv[1:])
    if kw.get("check"):
        return check()
    cells = kw["cells"].split(",") if "cells" in kw else None
    b = B.Brain(B.sample_worm(None), cells=cells) if cells else B.Brain(B.sample_worm(None))
    area = np.array([sum(seg.area() for sec in c.all for seg in sec) for c in b.cells], float)
    mus = np.asarray(b.is_muscle, bool)
    neur = [n for n, m in zip(b.cell_names, mus) if not m]
    a_n = area[~mus]
    res = dict(n_cells=len(area), n_neurons=int((~mus).sum()), median_um2=float(np.median(a_n)),
               median_repr=repr(float(np.median(a_n))), min_um2=float(a_n.min()), max_um2=float(a_n.max()),
               spec_um2=P.defaults().get("pump_area_median_um2"),
               area_um2={n: float(x) for n, x in zip(neur, a_n)})
    tag = "" if cells is None else "_" + "_".join(cells)
    out = ROOT / f"runs/worm/wbody2/pump_area_ref{tag}.json"
    out.write_text(json.dumps(res, indent=1))
    print(json.dumps({k: v for k, v in res.items() if k != "area_um2"}, indent=1))
    for n in ("AIYL", "AFDL", "AWAL", "AVAL", "AVAR"):
        if n in res["area_um2"]:
            print(n, round(res["area_um2"][n], 2), "rel", round(res["area_um2"][n] / res["median_um2"], 4))


if __name__ == "__main__":
    main()
