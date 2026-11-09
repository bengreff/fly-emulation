"""The organ conductances as NEURON point processes (wbody2, 9 Nov 2026, inbox 01:45, A): egg_g_solver and
pboc_g_solver, implicit (default) | explicit (the code before). Spec: docs/worm/night/wbody2/implicit_g_spec.md."""
import json
import os
import subprocess
import sys
from pathlib import Path

from wormemu.mech import organs_egglaying, organs_intestine

ROOT = Path(__file__).resolve().parents[1]


def test_defaults_are_implicit():
    d = {t[0]: t[3] for t in organs_egglaying.MECHANISMS + organs_intestine.MECHANISMS}
    assert d["egg_g_solver"] == "implicit" and d["pboc_g_solver"] == "implicit"


STEP = r"""
import json, sys, numpy as np
from wormemu.brain import Brain
from wormemu.fit import vitals
from wormemu.mech import organs_egglaying as ge, organs_intestine as gi
term, form, g = sys.argv[1], sys.argv[2], float(sys.argv[3])
cells = ["HSNL", "HSNR"] if term == "lgc55" else ["dBWML22", "vBWMR22"]
tname = "egg_g_solver" if term == "lgc55" else "pboc_g_solver"
b = Brain(cells=cells, toggles={"quantal_noise": "off", "channel_noise": "off", tname: form})
b.reset()
m = next(x for x in b.mechs if isinstance(x, ge.Mech if term == "lgc55" else gi.Mech))
q = m.q
if term == "lgc55":
    for k in ("egg_stretch_g_nS", "egg_5ht_g_nS", "egg_nlp3_g_nS"):
        q[k] = 0.0
    q["egg_lgc55_g_nS"], tgt = g, [b.idx["HSNL"], b.idx["HSNR"]]
else:
    m.cleft.p_open = lambda: 1.0
    q["pbo5_g_nS"], tgt = g, list(m.post_cells)
last, orig = {}, m.step
def wrapped(ctx, dt):
    last["r"] = orig(ctx, dt)
    return last["r"]
m.step = wrapped
V = []
for s in range(300):
    if term == "lgc55":
        m.tyr = 1e12
    b.step(None, 4.5)
    V.append(b._read(b._pv)[tgt].tolist())
V, r = np.array(V), last["r"]
I = np.asarray(r.get("I_pA", np.zeros(len(b.cell_names))))
inj = float(np.abs(I[tgt] - (q["egg_ret_gain_pA"] * r["out"]["egg_vm_act"] if term == "lgc55" else 0.0)).max())
print(json.dumps({"finite": bool(np.isfinite(V).all()), "alt": int(vitals.alternation(V).max()),
                  "alt_bar": vitals.ALT_STEPS, "inj_pA": inj}))
"""


def _run(*args):
    env = dict(os.environ, PYTHONPATH=str(ROOT / "src"), OMP_NUM_THREADS="1")
    r = subprocess.run([sys.executable, "-c", STEP, *args], capture_output=True, text=True, env=env, timeout=600)
    assert r.returncode == 0, r.stderr[-3000:]
    return json.loads(r.stdout.strip().splitlines()[-1])


def test_lgc55_on_hsn_is_stable_at_the_top_of_its_range_and_injects_no_conductance_current():
    """5 nS of LGC-55 on HSN (egg_lgc55_g_nS's top) at a 4.5 ms exchange step: the explicit form blew up (inbox 01:45,
    implicit_g_check); the implicit form is finite, does not alternate, and adds nothing to I_pA beyond the
    constant vm feedback current."""
    r = _run("lgc55", "implicit", "5.0")
    assert r["finite"] and r["alt"] < r["alt_bar"] and r["inj_pA"] < 1e-9, r


def test_pbo5_on_posterior_muscles_is_stable_at_twice_its_range():
    r = _run("pbo5", "implicit", "20.0")
    assert r["finite"] and r["alt"] < r["alt_bar"] and r["inj_pA"] < 1e-9, r
