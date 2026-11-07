"""Fit 1's parameter table (scripts/worm/fit1/fit1_core.py, docs/worm/FIT1.md section 3): every fitted value's
range is its ledger row's bio_min..bio_max (or the module's Spec), the template sits inside it, the bounded
transform never leaves it, and to_x inverts to_values. No NEURON build."""
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts" / "worm" / "fit1"))

import fit1_core as fc  # noqa: E402
from wormemu.brain import sample_worm  # noqa: E402

B = fc.bounds()


def test_ranges_are_the_ledger_rows():
    spec = sample_worm(None)
    P = spec.led.parameters.set_index("param_id")
    assert len(fc.IDS) == len(set(fc.IDS)) == len(B)
    for pid in fc.IDS:
        t, lo, hi, label, tr = B[pid]
        assert lo < hi and lo <= t <= hi and tr in ("log", "lin"), pid
        assert tr == "lin" or lo > 0, pid
        if pid in P.index:
            assert (lo, hi) == (float(P.loc[pid].bio_min), float(P.loc[pid].bio_max)), pid


def test_transform_stays_inside_and_inverts():
    rng = np.random.default_rng(0)
    for x in [np.full(len(fc.IDS), -40.0), np.full(len(fc.IDS), 40.0), *rng.normal(0, 3, (20, len(fc.IDS)))]:
        v = fc.to_values(x, B)
        for pid in fc.IDS:
            _, lo, hi, _, _ = B[pid]
            eps = 1e-12 * (hi - lo)
            assert lo - eps <= v[pid] <= hi + eps, pid
    x = rng.normal(0, 1.5, len(fc.IDS))
    assert np.allclose(fc.to_x(fc.to_values(x, B), B, clip=1e-9), x, atol=1e-6)


def test_make_spec_puts_one_value_per_row():
    v = fc.to_values(np.zeros(len(fc.IDS)), B)
    spec = fc.make_spec(v)
    for pid, val in v.items():
        cur = spec.values.get(pid)
        got = np.unique(np.asarray(cur, float)) if cur is not None else None
        if got is not None:
            assert got.size == 1 and np.isclose(got[0], val), pid
