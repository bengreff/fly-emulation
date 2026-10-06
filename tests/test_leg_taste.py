"""Leg/wing taste modality per type (`sense:taste_leg|modality_source`, s12)."""
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from flyemu.extrasenses import TASTANTS, leg_taste_weights  # noqa: E402

TYPES = pd.Series(["LgLG4", "LgAG2", "WG2", "LgAG1", "LgLG1a", "WG3", "LgLG3", None])


def test_legacy_is_weak_to_everything():
    w = leg_taste_weights(TYPES, 0)
    assert w.shape == (len(TYPES), len(TASTANTS)) and np.all(w == 0.2)


def test_matched_types_follow_the_labellar_rule():
    w = leg_taste_weights(TYPES, 1)
    sugar, bitter = TASTANTS.index("sugar"), TASTANTS.index("bitter")
    for i in range(3):                                  # sugar receptor lines
        assert w[i, sugar] == 1.0 and w[i].sum() == 1.0
    assert w[3, bitter] == 1.0 and w[3].sum() == 1.0    # Gr33a line
    assert np.all(w[4:6] == 0.0)                        # contact pheromone
    assert np.all(w[6:] == 0.2)                         # unmatched stay guessed


def test_drive_at_one_molar_sugar_clears_threshold_only_when_matched():
    gain, K = 15.0, 0.05                                # mV, M (guessed, shared with labellum)
    sat = 1.0 / (1.0 + K)
    assert gain * sat * leg_taste_weights(TYPES, 0)[0, 0] < 3.0
    assert gain * sat * leg_taste_weights(TYPES, 1)[0, 0] > 14.0
