"""Session 12 (F-DAMP-2): MuJoCo's noslip iterations behind contact:floor|noslip_iterations."""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from flyemu import passive  # noqa: E402
from flyemu.body import Body  # noqa: E402
from flyemu.registry import Registry  # noqa: E402


def test_neutral_keeps_the_flybody_arena_noslip():
    b = Body(vision=False)
    assert b.sim.mj_model.opt.noslip_iterations == 3
    assert passive.register_noslip(Registry("minimal"), b) == 3
    assert b.sim.mj_model.opt.noslip_iterations == 3


def test_switch_sets_the_iterations():
    reg = Registry("minimal")
    reg.overrides["contact:floor|noslip_iterations"] = 0.0
    b = Body(vision=False)
    assert passive.register_noslip(reg, b) == 0
    assert b.sim.mj_model.opt.noslip_iterations == 0
