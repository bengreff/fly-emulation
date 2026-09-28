import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from flyemu.transducers import Adaptation  # noqa: E402


def test_adaptation_is_phasic_tonic_and_neutral_at_zero():
    idx = np.array([1, 3])
    ad = Adaptation(idx, np.array([0.8, 0.0]), np.array([100.0, 100.0]), 0.1)
    d = np.zeros(5, np.float32); d[[1, 3]] = 10.0
    first = ad.apply(d)
    for _ in range(10000):                      # 1 s = 10 tau
        last = ad.apply(d)
    assert abs(first[1] - 10.0) < 0.2           # onset passes in full
    assert abs(last[1] - 2.0) < 0.05            # sustained: (1 - k) of onset
    assert first[3] == last[3] == 10.0          # k = 0: unchanged
    assert last[0] == 0.0
