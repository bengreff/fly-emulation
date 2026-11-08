"""wormemu.datamodel: simulate(theta, experiment) -> observations (docs/worm/DATA_MODEL.md). Each brain runs in its
own process (one NEURON per process)."""
import json
import os
import subprocess
import sys
from pathlib import Path

import numpy as np
import pytest

from wormemu import datamodel as D

ROOT = Path(__file__).resolve().parents[1]


def _run(code):
    env = dict(os.environ, PYTHONPATH=str(ROOT / "src"))
    r = subprocess.run([sys.executable, "-c", code], capture_output=True, text=True, env=env, cwd=ROOT, timeout=900)
    assert r.returncode == 0, r.stderr[-2000:]
    return json.loads(r.stdout.strip().splitlines()[-1])


SIM = """
import json, numpy as np
from wormemu import datamodel as D
r = D.simulate(None, {ex})
c = r.get("clamp_pA", np.zeros(0))
print(json.dumps(dict(cells=r["cells"], notes=r["notes"], v=r["v_mV"].tolist(), clamp=c.tolist())))
"""


def test_template_experiment_is_a_plain_brain_run():
    """No intervention, 20 C, default fields: the same voltages as Brain(sample_worm(None)) stepped open loop."""
    plain = _run("""
import json
from wormemu.brain import Brain, sample_worm
b = Brain(sample_worm(None)); b.reset()
print(json.dumps(dict(v=[b.step(None, 1.0).v_mV.tolist() for _ in range(30)], cells=b.cell_names)))
""")
    dm = _run(SIM.format(ex="D.Experiment(duration_ms=30)"))
    assert dm["cells"] == plain["cells"]
    assert np.array_equal(np.array(dm["v"]), np.array(plain["v"]))


def test_interventions_land():
    """Clamps, an ablation and a channel null each do what they say."""
    clamps = "[D.Clamp('AVAL', 'voltage', 10, 25, -40.0), D.Clamp('AVBL', 'current', 10, 25, 30.0)]"
    ex = f"D.Experiment(duration_ms=40, ablations=['AVAR'], observe=('v_mV', 'clamp_pA'), clamps={clamps})"
    r = _run(SIM.format(ex=ex))
    base = _run(SIM.format(ex="D.Experiment(duration_ms=40, ablations=['AVAR'])"))
    null = _run(SIM.format(ex="D.Experiment(duration_ms=40, ablations=['AVAR'], genotype=[D.Allele('egl-19')])"))
    cells = r["cells"]
    assert "AVAR" not in cells and "AVAL" in cells
    v, v0, vn = np.array(r["v"]), np.array(base["v"]), np.array(null["v"])
    a, b = cells.index("AVAL"), cells.index("AVBL")
    assert abs(v[30, a] + 40.0) < 1.0                       # held during the clamp (samples end at t + 1 ms)
    clamp = np.array(r["clamp"])
    assert np.all(np.abs(clamp[:9]) < 1e-3) and abs(clamp[30, 0]) > 10   # off: 1e9 MOhm passes about 1e-5 pA
    assert v[30, b] > v0[30, b] + 1.0                       # +30 pA depolarises AVBL
    assert np.allclose(v[:9], v0[:9], atol=1e-6)            # nothing before the clamps (the off clamp passes < 1e-7 nA)
    assert np.max(np.abs(vn - v0)) > 0.1                    # egl-19 null moves the network


def test_unrepresentable_inputs_raise():
    with pytest.raises(NotImplementedError, match="UNC-49"):
        D.simulate(None, D.Experiment(drugs=[("muscimol", 1000.0, 0.0)]))
    with pytest.raises(NotImplementedError, match="cell"):
        D.simulate(None, D.Experiment(genotype=[D.Allele("tax-4")]))
    with pytest.raises(ValueError, match="developmental"):    # unc-31 is locked (HELDOUT.md): the check needs heldout
        D.simulate(None, D.Experiment(genotype=[D.Allele("unc-31", timing="acute")], heldout=True))
    with pytest.raises(KeyError):
        D.simulate(None, D.Experiment(genotype=[D.Allele("no-such-gene")]))


def test_gene_table_targets_exist():
    """Every ("g", name) target is a conductance the brain knows; every "tx" a transmitter it assigns."""
    from wormemu import mech
    from wormemu.brain_structure import MARKERS
    for gene, (eff, _) in D.GENES.items():
        for kind, x in eff:
            assert kind in ("g", "tx", "tpm", "spec"), gene
            if kind == "g":
                assert x in mech.G_SCALE_NAMES, (gene, x)
            if kind == "tx":
                assert x in MARKERS, (gene, x)
    assert not set(D.GENES) & set(D.NOT_YET)
    import wormemu
    assert callable(wormemu.simulate)


def test_marker_null_silences_fast_release():
    """eat-4 null: glutamate leaves every cell's identity, and the glutamate-only cells are listed for fast release 0
    (simulate), so the unknown-transmitter graded stand-in does not take their synapses over."""
    r = _run("""
import json
from wormemu import datamodel as D
from wormemu.brain_structure import load_structure
st, left = D._structure([(D.Allele("eat-4"), D.GENES["eat-4"][0])])
print(json.dumps(dict(left=left, glu=sum("glutamate" in s for s in st.transmitter.values()),
                      glu0=sum("glutamate" in s for s in load_structure().transmitter.values()))))
""")
    assert r["glu"] == 0 and r["glu0"] > 50 and "AIBL" in r["left"]


DRUG = """
import json, numpy as np
from wormemu import datamodel as D
r = D.simulate({th}, D.Experiment(duration_ms=100, drugs={dr}, every_ms=50,
                                 observe=("v_mV", "muscle_activation", "out:drugs", "out:neuromod")))
bwm = [i for i, c in enumerate(r["cells"]) if "BWM" in c]
d = r["out:drugs"][-1]
print(json.dumps(dict(v=float(np.mean(r["v_mV"][-1][bwm])), act=float(np.mean(r["muscle_activation"][-1])),
                      drugs=d if isinstance(d, dict) else {{}}, ser=r["out:neuromod"][-1]["ma_serotonin_max_nM"])))
"""


def test_drugs_act_through_their_targets():
    """Bath 1 mM, uptake at its fastest bound: levamisole depolarises the body-wall muscle through L-AChR, aldicarb
    raises the cholinergic cleft ACh and with it muscle activation, bath serotonin reaches neuromod's compartments.
    Without a drug the module is silent (the template test holds the run bit-identical)."""
    fast = lambda d, frac=1.0: {f"drug_{d}_uptake_tau_s": 30.0, f"drug_{d}_cuticle_frac": frac}
    base = _run(DRUG.format(th=None, dr=[]))
    lev = _run(DRUG.format(th=fast("levamisole"), dr=[("levamisole", 1000.0, 0.0)]))
    ald = _run(DRUG.format(th={**fast("aldicarb"), "drug_aldicarb_ic50_uM": 0.1}, dr=[("aldicarb", 1000.0, 0.0)]))
    ser = _run(DRUG.format(th=fast("serotonin", 0.1), dr=[("serotonin", 1000.0, 0.0)]))
    assert base["drugs"] == {}
    assert lev["drugs"]["drug_levamisole_max_nS"] > 1 and lev["v"] > base["v"] + 10
    assert ald["drugs"]["ach_cleft_factor"] > 2 and ald["act"] > base["act"]
    assert ser["ser"] > 100 * base["ser"]


def test_heldout_identifiers_are_excluded_by_default():
    """docs/worm/HELDOUT.md: loaders drop locked identifiers unless asked; simulate refuses an experiment that
    reproduces a locked corpus item or names a locked source, before it builds anything."""
    from wormemu import heldout as H
    assert H.exclude("ephys_single_cell", ["AIY", "RIM", "AFD", "AWA"]) == ["AIY", "AFD", "AWA"]
    assert H.exclude("ephys_single_cell", ["RIM"], allow_heldout=True) == ["RIM"]
    assert {"unc-31", "AML508", "RIML"} <= H.locked("randi2023")
    assert "2023-03-08-03" in H.locked("atanas2023")                     # pradhan2025, locked whole
    assert {"unc-29", "glr-1"} <= H.locked("owmd_javer2018")             # its own draw and the corpus's genes
    with pytest.raises(H.HeldOut):
        H.check("yemini2013", ["egl-2(n693)V"])
    with pytest.raises(H.HeldOut):
        D.simulate(None, D.Experiment(genotype=[D.Allele("slo-1")]))
    with pytest.raises(H.HeldOut):
        D.simulate(None, D.Experiment(ablations=["AVAL", "AVAR", "AVBL", "AVBR", "PVCL", "PVCR", "AVDL", "AVDR"]))
    with pytest.raises(H.HeldOut):
        D.simulate(None, D.Experiment(sources=[("atanas2023", "2021-06-11-01")]))
    assert H.experiment_locks(["egl-19"], ["AVAR"], [("atanas2023", "2021-06-11-02")]) == []
    lock = H.load()["datasets"]
    for name, ds in lock.items():                                         # every dataset's list is reachable
        L = ds["locked"]
        assert len(H.locked(name)) >= (sum(len(c["ids"]) for c in L.values()) if isinstance(L, dict) else len(L))


def test_body_on_closes_the_loop():
    """body='on': the FEM body steps with the brain at its own exchange (1/240 s) and posture comes back."""
    r = _run("""
import json, tempfile, numpy as np
from wormemu import datamodel as D
r = D.simulate(None, D.Experiment(duration_ms=50, body="on", observe=("posture", "muscle_activation"), every_ms=25,
                                  body_out=tempfile.mkdtemp()))
a = np.array(r["muscle_activation"])
print(json.dumps(dict(t=r["t_ms"].tolist(), p=np.array(r["posture"]).tolist(), a=a.tolist())))
""")
    p = np.array(r["p"])
    assert p.shape == (2, 49) and np.isfinite(p).all()
    assert np.allclose(r["t"], [25.0, 50.0], atol=0.3)                    # the body's 4.167 ms exchange
    assert np.array(r["a"]).shape == (2, 95)
