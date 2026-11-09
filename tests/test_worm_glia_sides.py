"""mech/glia (row 11): the left and right amphid K+ compartments share no term. The two amphids are separate organs,
each with its own sheath (WormAtlas, after Perkins et al. 1986); 8 Nov 2026 (wbody2 item 8) the check's sides bar was
dropped for this structural test."""
from types import SimpleNamespace

import numpy as np

from wormemu.brain_layers import AMPHID
from wormemu.mech import glia


def _mech(kb="kir"):
    names = sorted(AMPHID)
    brain = SimpleNamespace(idx={n: i for i, n in enumerate(names)}, spec=None)
    return glia.Mech(brain, {}, {"glia_cells": "off", "glia_kbuffer": kb, "glia_v0_window": "first"}), names


def test_left_load_leaves_right_at_bath():
    for kb in ("kir", "null"):
        m, names = _mech(kb)
        v = np.full(len(names), -60.0)
        left = np.array([n.endswith("L") for n in names])
        t = 0.0
        while t < glia.GLIA_V0_MS + 3000.0:
            if t >= glia.GLIA_V0_MS:
                v = np.where(left, -20.0, -60.0)
            r = m.step(SimpleNamespace(v=v, t_ms=t), 5.0)
            t += 5.0
        ko = r["out"]["amphid_k_mM"]
        bath = m.q["glia_k_bath_mM"]
        assert ko[0] > bath + 0.01                       # the left side loads
        assert ko[1] == bath                             # the right side does not move
        assert np.all(r["I_pA"][~left] == 0.0)           # and its neurons get no current
