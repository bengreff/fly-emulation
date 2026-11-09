"""wneuro item 1 (a), second probe (written Sun 8 Nov 2026 23:08 CST, before running): neuromod's part alone.

Why: the in-brain probe (probe_a.py, 23:06) failed at every point, and the trace shows a cause outside neuromod: the
intestine releases NLP-40 in proportion to the MEAN Hill(Ca) of its 20 cells, and the mean is not locked to the int9
peak (cycle 1 peaks about 15 s after it, cycle 3 about 14 s before it; measured, tau10k run). Wang et al. 2013's DVB
spike is locked to the posterior contraction, and the intestinal wave crosses the gut in a few seconds, so a
phasic release follows int9. This probe asks whether neuromod's pool, AEX-2 occupancy and Gs make a phasic DVB drive
from such a release, for some clearance inside its range.

Method: mech.neuromod.Mech alone on the unit checks' stand-in brain (302 neurons held at -80 mV, so neuronal DCV
release is negligible), the ledger values (at_ledger.patch), DVB's read weights set to its measured membrane shares
(0, 0, 0.707, 0.293; geom.py). Input: the intestine's own release law applied to int9's Ca (the template run's
recorded int9L/R mean, 150 s, 100 ms steps): r = R x Hill(Ca; k, n) nM/s into the posterior body. Two release
shapes: the template (R 15 nM/s, k 0.3 uM, n 2) and the corner without the tonic part (R 100, k 1.0, n 4), both
inside wbody2's ranges. Clearance pep_degrade_tau_s = 10, 30, 100, 300, 600 s (D4's range 10-600).

Bar: probe_a.py's, unchanged: in each cycle after the first, (peak - trough) / peak >= 0.5 for both DVB's AEX-2
occupancy and its Gs (peak = max in the 10 s after the int9 peak, trough = min in the 5 s before it). A pass at some
point means neuromod's clearance is a D gap (a passing value exists in range; not adopted) and the in-brain failure
is upstream (the intestine's release timing and tonic part, wbody2's). Peak Gs is reported, no bar (the Gs-to-spike
link is item 1 (b), not identified).

Addendum (23:27 CST, before running it): `aex2_ec50_source=wang2013` as an argument runs the same grid with Wang
2013's 3.39 nM instead of Beets' 7.645 nM (class C toggle). Same bar; report only. Expectation: the lower EC50
saturates AEX-2 more, so modulation can only fall.

Usage: python probe_a2.py [template_run.json] [aex2_ec50_source=wang2013] -> runs/worm/wneuro/probe_a2[_wang2013].json
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "scripts" / "worm"))
sys.path.insert(0, str(ROOT / "scripts" / "worm" / "wneuro"))
import at_ledger  # noqa: E402

at_ledger.patch(["neuromod"])
import neuromod_unit_check as U  # noqa: E402
from probe_a import modulation  # noqa: E402
from wormemu.mech import neuromod as N  # noqa: E402

DVB_W = np.array([0.0, 0.0, 0.707, 0.293])
SHAPES = {"template": (15.0, 0.3, 2.0), "corner": (100.0, 1.0, 4.0)}
TAUS = (10.0, 30.0, 100.0, 300.0, 600.0)


def run(t, ca, tau, shape, extra=None):
    R, k, n = SHAPES[shape]
    T = {s.id: s.template for s in N.SPECS}
    m = N.Mech(U.BRAIN, {**T, "pep_degrade_tau_s": tau}, {"peptides": "compartments", "monoamines": "off", **(extra or {})})
    j = U.NEURONS.index("DVB")
    m.pep_W[j] = DVB_W
    m.e_Wp = m.pep_W[m.e_cell[m.e_pep]]
    row = N.PRECURSORS.index("nlp-40")
    sel = np.flatnonzero((m.e_cell == j) & (m.e_lig == row) & m.e_pep)
    sel_p = np.flatnonzero(m.e_pep)
    ip = [int(np.flatnonzero(sel_p == s)[0]) for s in sel]
    Vp = m.pep.V[2] / 1000.0 * N.NA_PL                     # molecules per nM in the posterior body
    v = np.full(len(U.NEURONS), -80.0)
    dt_ms = (t[1] - t[0]) * 1000.0
    occ, gs, read = [], [], []
    for x, c in zip(t, ca):
        r = R * c ** n / (c ** n + k ** n)
        cx = U.ctx(v, x * 1000.0)
        cx.outputs["peptide_release"] = {"nlp-40@posterior_body": r * Vp}
        m.step(cx, dt_ms)
        cp = m.pep.nM()[row]
        read.append(float(DVB_W @ cp))
        occ.append(float(DVB_W @ N._hill(cp, m.e_ec50[sel[0]], m.p["gpcr_hill"])))
        gs.append(float(m.G[j, 2]))
    return np.array(occ), np.array(gs), np.array(read), len(ip)


def main():
    args = [a for a in sys.argv[1:] if "=" not in a]
    extra = dict(a.split("=", 1) for a in sys.argv[1:] if "=" in a)
    src = args[0] if args else str(ROOT / "runs/worm/wneuro/dmp_trace_cells-dmp_150s.json")
    r = json.load(open(src))
    t, ca = np.array(r["trace"]["t"]), np.array(r["trace"]["int9"])
    pk = r["int9_peaks_s"]
    rows = []
    for shape in SHAPES:
        for tau in TAUS:
            occ, gs, read, n_aex2 = run(t, ca, tau, shape, extra)
            mo, mg = modulation(t, occ, pk), modulation(t, gs, pk)
            ok = bool(mo and mg and all(x["mod"] >= 0.5 for x in mo) and all(x["mod"] >= 0.5 for x in mg))
            rows.append(dict(shape=shape, tau_s=tau, phasic=ok, occ_mod=[round(x["mod"], 3) for x in mo],
                             gs_mod=[round(x["mod"], 3) for x in mg], gs_peak=[round(x["peak"], 3) for x in mg],
                             gs_trough=[round(x["trough"], 3) for x in mg], read_max_nM=round(float(read.max()), 2),
                             aex2_entries_at_dvb=n_aex2))
            print(json.dumps(rows[-1]))
    out = dict(source_run=src, toggles=extra, int9_peaks_s=pk, dvb_weights=DVB_W.tolist(), shapes=SHAPES, rows=rows,
               any_pass=any(x["phasic"] for x in rows))
    tag = "".join(f"_{v}" for v in extra.values())
    (ROOT / f"runs/worm/wneuro/probe_a2{tag}.json").write_text(json.dumps(out, indent=1))
    print("any_pass", out["any_pass"])


if __name__ == "__main__":
    main()
