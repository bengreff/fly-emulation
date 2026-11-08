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
    with pytest.raises(NotImplementedError, match="ACh clearance"):
        D.simulate(None, D.Experiment(drugs=[("aldicarb", 1000.0, 0.0)]))
    with pytest.raises(NotImplementedError, match="cell"):
        D.simulate(None, D.Experiment(genotype=[D.Allele("tax-4")]))
    with pytest.raises(ValueError, match="developmental"):
        D.simulate(None, D.Experiment(genotype=[D.Allele("unc-31", timing="acute")]))
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
