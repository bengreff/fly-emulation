"""wneuro Open 5 (written Mon 9 Nov 2026 00:33 CST, before running): the DMSR-1 isoform toggle against the
line 14 check.

Question. Table S6 (Beets et al. 2023) measures FLP-25 on both DMSR-1 isoforms: DMSR-1-2 (B) 0.6 pM, DMSR-1-1 (A)
1.6 uM (measured, 2.65e6-fold). The default per-pair rule keeps the most potent row, so FLP-25 reads B everywhere.
Which isoform RIS (or any cell) makes is not stated in any source read (Rossi et al. 2025 PMC7617803; Iannacone et al.
2017 cloned isoform A). The 8 Nov ris_gi.py diagnostic found FLP-25 on DMSR-1 carries 0.76 of RIS's Gi with FLP-11
removed (measured, template values), so the isoform choice may decide line 14.

Method. neuromod_unit_check's check 4 exactly (stand-in brain, template values, RIS at 0 mV, every other neuron at
-80 mV, 6000 steps of 100 ms; with / without the RIS DMSR-1 autoreceptor; each with FLP-11 release removed), run under
dmsr1_isoform = most_potent (default) and dmsr-1a. Also reported, for the "with" run: Gi of every cell that has a
FLP-25 on DMSR-1 entry, under both settings (how far the toggle reaches).

Bar (line 14's, unchanged, applied to each setting): plateau (< 1% change over the last 60 s) with and without; FLP-11
lower with the autoreceptor; RIS Gi > 0.1 with; DMSR-1's share of RIS's FLP-11-dependent Gi >= 0.9. Class C: both
settings are reported; the default does not change on this check alone (no source says which isoform RIS makes).
Falsifier for "the isoform decides line 14": both settings give the same pass / fail.

Usage: PYTHONPATH=src .venv/bin/python scripts/worm/wneuro/dmsr1_isoform.py -> runs/worm/wneuro/dmsr1_isoform.json
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "scripts" / "worm"))
import neuromod_unit_check as U  # noqa: E402
from wormemu.mech import neuromod as N  # noqa: E402

ris = U.NEURONS.index("RIS")
f11, f25 = N.PRECURSORS.index("flp-11"), N.PRECURSORS.index("flp-25")
v = np.full(len(U.NEURONS), -80.0)
v[ris] = 0.0
out = {}
for iso in N.DMSR1_ISO:
    r4, gi_cells = {}, {}
    for name, add in (("with", None), ("without", {}), ("with_no_flp11", None), ("without_no_flp11", {})):
        m = N.Mech(U.BRAIN, U.T, {"peptides": "compartments", "monoamines": "off", "dmsr1_isoform": iso}, expr_add=add)
        if name.endswith("no_flp11"):
            m.pep_share[:, f11] = 0.0
        tr = []
        for k in range(6000):
            m.step(U.ctx(v, k * 100.0), 100.0)
            tr.append(float(m.pep.nM()[f11, 0]))
        tr = np.array(tr)
        r4[name] = dict(flp11_head_nM_end=tr[-1], change_last_60s=float(abs(tr[-1] / tr[-601] - 1)),
                        ris_gi=float(m.G[ris, 1]))
        if name == "with":
            cells = sorted({int(m.e_cell[e]) for e in range(len(m.e_cell)) if m.e_pep[e] and m.e_lig[e] == f25
                            and m.e_ec50[e] in (U.T["pep_ec50_flp-25_dmsr-1_nM"], U.T["pep_ec50_flp-25_dmsr-1_isoA_nM"])})
            gi_cells = {U.NEURONS[c]: float(m.G[c, 1]) for c in cells}
            r4[name]["flp25_nM"] = m.pep.nM()[f25].tolist()
    d_with = r4["with"]["ris_gi"] - r4["with_no_flp11"]["ris_gi"]
    d_without = r4["without"]["ris_gi"] - r4["without_no_flp11"]["ris_gi"]
    share = 1.0 - d_without / d_with if d_with > 0 else 0.0
    ok = dict(plateau=r4["with"]["change_last_60s"] < 0.01 and r4["without"]["change_last_60s"] < 0.01,
              lower_with=r4["with"]["flp11_head_nM_end"] < r4["without"]["flp11_head_nM_end"],
              ris_gi_with=r4["with"]["ris_gi"] > 0.1, share=share >= 0.9)
    out[iso] = dict(**r4, flp11_gi_with=d_with, flp11_gi_without=d_without, dmsr1_share_of_flp11_gi=share,
                    parts={k: bool(x) for k, x in ok.items()}, passed=bool(all(ok.values())), gi_flp25_dmsr1_cells=gi_cells)
    print(iso, "share", round(share, 3), "RIS Gi with", round(r4["with"]["ris_gi"], 4), "passed", out[iso]["passed"],
          {k: bool(x) for k, x in ok.items()}, flush=True)
a, b = out["most_potent"]["gi_flp25_dmsr1_cells"], out["dmsr-1a"]["gi_flp25_dmsr1_cells"]
out["gi_change_cells"] = {c: dict(most_potent=a[c], dmsr_1a=b[c]) for c in a}
print("cells with a FLP-25 on DMSR-1 entry:", len(a), {c: (round(a[c], 3), round(b[c], 3)) for c in a})
(ROOT / "runs/worm/wneuro/dmsr1_isoform.json").write_text(json.dumps(out, indent=1, default=float))
