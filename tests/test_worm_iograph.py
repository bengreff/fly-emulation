"""Interconnect (docs/worm/INTERCONNECT.md): the default model's module-to-module reads, recorded from a running
brain with the slow modules live, all follow iograph.LINKS (every read contracted and produced, every link's
producer writes, every consumer names its key); temperature reaches every compiled rate-class mod; one pressure.
NEURON is one simulator per process, so the brain runs in a subprocess."""
import json
import os
import subprocess
import sys
from pathlib import Path

from wormemu import iograph, params
from wormemu.body import layers
from wormemu.brain import BAAI, C302, OWN_MODS
from wormemu.mech import temperature

ROOT = Path(__file__).resolve().parents[1]
# a short set-point window so the slow modules read within the run; the conditional producers away from neutral
LIVE = {"slow_set_s": 0.01, "daf7_effect": -0.5, "afd_tstar_fast_frac": 0.5, "afd_tstar_slow_frac": 0.5}
SCRIPT = '''
import json, sys
from wormemu import iograph
g = iograph.record(ms=40, values=json.loads(sys.argv[1]))
print(json.dumps(g))
'''


def _record():
    env = dict(os.environ, PYTHONPATH=str(ROOT / "src"))
    r = subprocess.run([sys.executable, "-c", SCRIPT, json.dumps(LIVE)], capture_output=True, text=True, env=env,
                       cwd=ROOT, timeout=600)
    assert r.returncode == 0, r.stderr[-2000:]
    return json.loads(r.stdout.strip().splitlines()[-1])


def test_contract():
    g = _record()
    assert iograph.contract_check(g) == []
    made = {k for w in g["writes"].values() for k in w.get("out", ())}
    assert "ma_release_scale_slow" in made                       # DAF-7 -> RIM/RIC, once daf7_effect is not 0
    assert not set(iograph.OPEN_READS) & made


def test_temperature_reaches_every_rate_mod():
    mods = sorted((BAAI / "mod").glob("*.mod")) + sorted((C302 / "mod").glob("*.mod")) + \
        sorted(OWN_MODS.rglob("*.mod"))
    stems = {m.stem: m for m in mods}
    assert set(temperature.RATE_MODS) <= set(stems)
    for stem, (cls, states) in temperature.RATE_MODS.items():
        assert cls in temperature.CLASSES
        t = temperature.patch_mod(stem, stems[stem].read_text())
        assert "GLOBAL tadj" in t and "tadj = 1" in t, stem
        if states != "own":
            assert t.count("= tadj * (") >= 1, stem
    # an unlisted mod is untouched; Ca influx is not scaled
    assert temperature.patch_mod("cainternm", stems["cainternm"].read_text()) == stems["cainternm"].read_text()
    assert "cad' = tadj" not in temperature.patch_mod("du_bwm", stems["du_bwm"].read_text())


def test_one_pressure():
    p = layers.pressure_link()
    assert p["body_pressure_kPa"] == p["body_pressure_ctrl_kPa"]          # template medium: E_core unchanged
    E0 = layers.profile(__import__("numpy").array([0.0]), {**layers.P, **p})[0]
    assert abs(E0 - layers.P["body_E_core_kPa"]) < 1e-9
    hyper = layers.pressure_link(extra_mosm=50.0)
    assert hyper["body_pressure_kPa"] < p["body_pressure_kPa"]
    cat = params.catalog()
    linked = cat[cat.id.isin(list(layers.LINKED))]
    assert len(linked) == 2 and not linked.active.any()
