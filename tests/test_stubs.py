"""s12 blanks audit: registered stubs are read at neutral and refused when set."""
import sys
from pathlib import Path

import pytest
import yaml

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "src"))

from flyemu import stubs  # noqa: E402
from flyemu.registry import Policy, Registry  # noqa: E402


def test_stubs_are_read_at_neutral_and_refused_otherwise():
    reg = Registry(Policy.MINIMAL)
    stubs.read(reg)                                   # neutral: no error
    keys = set((reg.inventory().entity + "|" + reg.inventory().property))
    assert set(stubs.STUBS) <= keys                   # every stub is in the inventory
    for key, (mech, neutral, _) in stubs.STUBS.items():
        r = Registry(Policy.MINIMAL)
        r.overrides[key] = neutral + 1.0
        with pytest.raises(NotImplementedError):
            stubs.read(r)


def test_every_stub_is_an_absent_mechanism_that_owns_its_switch():
    mech = {m["id"]: m for m in yaml.safe_load((REPO / "data/model/mechanisms.yaml").read_text())}
    for key, (mid, *_rest) in stubs.STUBS.items():
        assert mech[mid]["status"] == "absent" and key in mech[mid]["switch"], mid
        assert mech[mid].get("absent_reason"), mid


def test_every_ledger_row_has_a_carrier_and_upgrades_are_real():
    mech = {m["id"] for m in yaml.safe_load((REPO / "data/model/mechanisms.yaml").read_text())}
    onto = yaml.safe_load((REPO / "data/ontology/fly_information.yaml").read_text())
    for e in onto:
        assert e["mech"] in mech, e["quantity"]       # s12: no row carried by "none"
        assert e.get("upgrade", e["mech"]) in mech, e["quantity"]
