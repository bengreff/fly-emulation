"""s13 (fly2, F-GJ-3): identified types take their transmitter from physiology when the switch is on.

PSI is 'unclear' in male-cns (sign 0, transmits nothing); Fayyazuddin et al. 2006 recorded the
PSI-DLMn synapse as cholinergic. Claims: switch 0 leaves the dataset call; switch 1 sets the
table's transmitter, so the sign follows; the row is registered with its basis and source.
"""
from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "src"))

from flyemu import connectome  # noqa: E402
from flyemu.registry import Policy, Registry, Status  # noqa: E402

KEY = "connectome:identified|nt_from_physiology"


def _tables():
    nrn = pd.DataFrame({"bodyId": [1, 2, 3], "type": ["DNp01", "PSI", "DLMn c-f"], "status": "Traced",
                        "predictedNt": ["acetylcholine", "unclear", "unclear"], "class": "x",
                        "superclass": ["descending", "vnc_intrinsic", "vnc_motor"], "size": 1e9})
    edges = pd.DataFrame({"pre": [1, 2], "post": [2, 3], "weight": [40, 50]})
    return nrn, edges


def _build(on):
    r = Registry(Policy.MINIMAL)
    if on:
        r.overrides[KEY] = 1.0
    nrn, edges = _tables()
    return connectome.build(r, neurons=nrn, edges=edges, min_synapses=5), r


def test_neutral_keeps_the_dataset_call_and_psi_transmits_nothing():
    c, _ = _build(False)
    assert c.neurons.predictedNt.tolist()[1] == "unclear"
    assert c.sign[1] == 0


def test_switch_on_makes_psi_cholinergic_with_its_source():
    c, r = _build(True)
    assert c.neurons.predictedNt.tolist()[1] == "acetylcholine"
    assert c.sign[1] == 1
    inv = r.inventory()
    row = inv[(inv.entity == "cell_type:PSI") & (inv.property == "transmitter")].iloc[0]
    assert str(row.status) in (Status.MEASURED.value, str(Status.MEASURED))
    assert "Fayyazuddin" in str(row.evidence)
