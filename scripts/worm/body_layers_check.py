"""Row 21 checks: the layered body and its internal damping (src/wormemu/body/layers.py).

1. Neutral forms. A --tet_youngs file of uniform 2e5 Pa (the constructor's modulus) must give frames bit-identical
   to no flag; so must --damping backholm2013 at tau 0.
2. Unit check, bar written before running: the model's section bending modulus (derived from the per-tet moduli on
   the mesh) is inside Backholm et al. 2013's whole-worm E = 110 +/- 30 kPa, taken as 50-170 kPa (2 SD). Expected
   to FAIL: the Frontiers 2024 moduli come from local indentation, where the pressurised core reads stiff.
3. The defaults (layers + damping) on the agar film, 3 s of the published travelling wave (1.76 Hz): finite.
   Damping bar, written before running: the mean damping time constant during the wave is at most 5.3 ms, the
   bound derived from Fang-Yen et al. 2010 (internal viscosity < 5e-16 N m^2 s over 9.5e-14 N m^2).
Writes docs/worm/night/wbody/body_layers_row21.json.
"""
from __future__ import annotations

import json
import sys
import time
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))
from wormemu.body import layers  # noqa: E402
from wormemu.body import metaworm as mw  # noqa: E402

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "runs" / "worm" / "night_wbody"
OUT.mkdir(parents=True, exist_ok=True)
DOC = ROOT / "docs" / "worm" / "night" / "wbody" / "body_layers_row21.json"
WAVE = dict(mode="wave", seconds=3.0, f=1.76, lam=1.54, amp=0.157, frame_every=8)
BAR = "section bending modulus inside 50-170 kPa (Backholm 2013 E = 110 +/- 30 kPa, 2 SD)"


def run(name, extra):
    t = time.time()
    r = mw.run(str(OUT / name), world={**mw.AGAR_FILM, **extra}, **WAVE)
    return r, time.time() - t


def main():
    res = {"bar_unit_check": BAR, "wave": WAVE}
    base, w0 = run("layers_upstream", {})
    flat = OUT / "layers_uniform2e5.tet_youngs.f64"
    np.full(len(layers.read_mesh()[1]), 2e5).tofile(flat)
    uni, _ = run("layers_uniform2e5", {"tet_youngs": str(flat)})
    d0, _ = run("layers_damp_tau0", {"damping": "backholm2013", "damp_tau_ms": 0})
    res["neutral_uniform_bit_identical"] = bool(np.array_equal(base["X"], uni["X"]))
    res["neutral_damp_tau0_max_dx"] = float(np.abs(base["X"] - d0["X"]).max())
    res["neutral_pass"] = res["neutral_uniform_bit_identical"] and res["neutral_damp_tau0_max_dx"] == 0.0

    E, s = layers.tet_moduli()
    res["moduli"] = s
    res["unit_check_value_kPa"] = s["E_bending_kPa"]
    res["unit_check_pass"] = bool(50 <= s["E_bending_kPa"] <= 170)
    res["unit_check_ratio_to_110"] = s["E_bending_kPa"] / 110

    world, info = layers.world_flags(None, str(OUT / "layers_default"), mw.AGAR_FILM)
    on, w1 = run("layers_default", {k: v for k, v in world.items() if k not in mw.AGAR_FILM})
    lay, _ = run("layers_only", {"tet_youngs": world["tet_youngs"]})
    res["default"] = {"finite": bool(np.isfinite(on["X"]).all()), "wall_s": w1, "wall_upstream_s": w0,
                      "damp_tau_ms_mean": on["meta"]["world"]["damp_tau_ms_mean"],
                      "damp_w_mean": on["meta"]["world"]["damp_w_mean"],
                      "flags": {k: v for k, v in world.items() if k not in mw.AGAR_FILM}}
    res["damping_bar"] = "mean tau during the 1.76 Hz wave <= 5.3 ms (Fang-Yen 2010 bound)"
    res["damping_pass"] = bool(res["default"]["damp_tau_ms_mean"] <= 5.3)
    fr = mw.Frame(base["meta"], base["X"][0])
    for name, r in [("upstream", base), ("layers_only", lay), ("layers_damping", on)]:
        g = mw.gait(r, WAVE["f"], 1.0, fr)
        res.setdefault("gait", {})[name] = {k: (float(v) if np.ndim(v) == 0 else None) for k, v in g.items()}
    DOC.parent.mkdir(parents=True, exist_ok=True)
    json.dump(res, open(DOC, "w"), indent=1)
    print(json.dumps(res, indent=1))


if __name__ == "__main__":
    main()
