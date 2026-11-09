"""Does AFD's thermosensory current count twice under afd_membrane naudin22? (docs/worm/night/2026-11-08_wbrain2.md,
"AFD under naudin22: does the thermosensory current count twice?", written before this ran; wbrain2, 9 Nov 2026).

Embedded AFDL alone (single_cell_sanity: no synapses, no gaps), Naudin's model and BAAIWorm's default fit,
sens_thermo off (bar 4's run) and on (the cascade, default form), head temperature at the template's 20 C = T*. Rest: 3 s at 0 pA, the cascade's CNG Po,
conductance and current. Then FIT2's six training sweeps through ephys_score.score.

  python scripts/worm/debug2/naudin22_afd_thermo.py FEATURES.npz OUT.json
"""
import json
import sys
from pathlib import Path

FEATS, OUT = sys.argv[1], sys.argv[2]
sys.argv = [sys.argv[0], FEATS]                          # ephys_score reads its features path from argv[1]
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "triage"))
import ephys_score as E  # noqa: E402

FORMS = {"thermo_off": {"afd_membrane": "naudin22", "sens_thermo": "off"},
         "thermo_cascade": {"afd_membrane": "naudin22", "sens_thermo": "cascade"},
         "baaiworm_thermo_off": {"afd_membrane": "baaiworm", "sens_thermo": "off"},
         "baaiworm_thermo_cascade": {"afd_membrane": "baaiworm", "sens_thermo": "cascade"}}


def rest(extra):
    br = E.S.build(cells=[E.fit2.CELL["AFD"]], extra=extra)
    br.reset()
    br.extra_pA[:] = 0.0
    for _ in range(3000):
        v = br.step(None, 1.0).v_mV
    c = br.cell_names.index(E.fit2.CELL["AFD"])
    o = br.mech_out
    po = (o.get("sens_cng_po") or {}).get(br.cell_names[c])
    r = dict(v_rest_mV=float(v[c]), cng_po=po, cgmp_uM=(o.get("sens_cgmp_uM") or {}).get(br.cell_names[c]))
    if "sens_g_nS" in o:                                   # senses_chem's point-process conductance and current
        r.update(cng_g_nS=float(o["sens_g_nS"][c]), cng_I_pA_inward=float(o["sens_I_pA"][c]))
    return r


res = {}
for k, ex in FORMS.items():
    res[k] = dict(rest=rest(ex), score=E.score(ex, ["AFD"])["AFD"])
    r = res[k]
    print(k, r["rest"], "rmse", round(r["score"]["rmse_mV"], 2), "steady", r["score"]["model"]["steady"], flush=True)
for pre in ("", "baaiworm_"):
    a, b = res[pre + "thermo_off"]["score"]["model"]["steady"], res[pre + "thermo_cascade"]["score"]["model"]["steady"]
    res[pre + "steady_shift_mV"] = [round(y - x, 2) for x, y in zip(a, b)]
    res[pre + "max_abs_shift_mV"] = max(abs(s) for s in res[pre + "steady_shift_mV"])
    res[pre + "negligible"] = res[pre + "max_abs_shift_mV"] <= 1.0
    print(pre or "naudin22_", "shift", res[pre + "steady_shift_mV"], "negligible", res[pre + "negligible"])
res["naudin_gL_nS_embedded"] = 0.004 * 4.008 / 6.6       # S2 Table gL x our C / Naudin's C (derived)
Path(OUT).write_text(json.dumps(res, indent=1))
