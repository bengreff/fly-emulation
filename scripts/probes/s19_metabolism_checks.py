"""S1-S4 physiology checks (s19; plan DECISIONS 22 Oct 02:06). The lumped Organs ODE alone, no nervous system.

Predictions, each from parameter-source values only (the held-out numbers never set a parameter):
    starvation   no food, water freely available (RH held at 1, so no evaporative loss), rest, 25 degC:
                 hours until the energy reserve (fat store + hemolymph sugar) falls to --residual of its
                 starting value
    desiccation  no food, no water, RH --rh, rest, 25 degC: hours until the fly has lost --lethal of its
                 body water (or starves first; both reported)
    cafe         daily food volume that balances the daily energy use at rest on a --food-mM glucose-eq
                 diet, times 1/--assimilation (energy balance; feeding behaviour is not simulated)
    rest_sugar   hemolymph sugar after 6 h without food, from the set point (consistency only)

Validity: basal use is the whole-fly routine metabolic rate (respirometry of freely moving flies), so
activity is 0 here; starvation-induced hyperactivity is not modelled; one glucose-eq store.

    .venv/bin/python scripts/probes/s19_metabolism_checks.py --sourced --residual 0.05 --lethal 0.4 \
        --food-mM 292 --out runs/s19/met/checks.json
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))
from flyemu import internal_state as S  # noqa: E402


def params(values: dict, sourced: bool = False) -> dict:
    p = S.default_params(sourced)
    unknown = set(values) - set(p)
    if unknown:
        raise SystemExit(f"unknown parameter names: {sorted(unknown)}")
    p.update(values)
    return p


def starvation_h(p, residual, dt=60.0, max_h=24 * 20):
    o = S.Organs(p)
    e0 = o.fat + o.sugar
    t = 0.0
    while o.fat + o.sugar > residual * e0 and t < max_h * 3600:
        o.step(dt, humidity_rh=1.0)
        t += dt
    return t / 3600.0


def desiccation_h(p, rh, lethal, residual, dt=60.0, max_h=24 * 20):
    o = S.Organs(p)
    w0, e0 = o.water_nl, o.fat + o.sugar
    t, t_water, t_energy = 0.0, None, None
    while t < max_h * 3600 and (t_water is None or t_energy is None):
        o.step(dt, humidity_rh=rh)
        t += dt
        if t_water is None and o.water_nl <= (1 - lethal) * w0:
            t_water = t / 3600.0
        if t_energy is None and o.fat + o.sugar <= residual * e0:
            t_energy = t / 3600.0
    return {"water_h": t_water, "energy_h": t_energy,
            "survival_h": min(x for x in (t_water, t_energy) if x is not None) if (t_water or t_energy) else None}


def cafe_ul_day(p, food_mM, assimilation):
    use_day = p["basal_nmol_s"] * 86400.0                     # nmol glucose-eq per day at rest, 25 degC
    return use_day / food_mM / assimilation                     # mM = nmol/uL


def rest_sugar_mM(p, hours=6.0, dt=60.0):
    """Hemolymph sugar after `hours` without food from the set point (AKH release from the store holds it)."""
    o = S.Organs(p)
    for _ in range(int(hours * 3600 / dt)):
        o.step(dt, humidity_rh=1.0)
    return o.sugar_mM


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--sourced", action="store_true", help="internal_state.SOURCED values (s19)")
    ap.add_argument("--values", type=Path, help="JSON {param field: value} overrides")
    ap.add_argument("--residual", type=float, default=0.0, help="reserve fraction left at starvation death")
    ap.add_argument("--rh", type=float, default=0.0)
    ap.add_argument("--lethal", type=float, required=True, help="fraction of body water lost at death")
    ap.add_argument("--food-mM", type=float, required=True, help="CAFE food sugar, mM glucose-eq")
    ap.add_argument("--assimilation", type=float, default=1.0)
    ap.add_argument("--out", type=Path, required=True)
    a = ap.parse_args()
    values = json.loads(a.values.read_text()) if a.values else {}
    p = params(values, a.sourced)
    out = {"sourced": a.sourced, "values": values, "residual": a.residual, "rh": a.rh, "lethal": a.lethal, "food_mM": a.food_mM,
           "assimilation": a.assimilation,
           "starvation_h": round(starvation_h(p, a.residual), 1),
           "desiccation": desiccation_h(p, a.rh, a.lethal, a.residual),
           "cafe_ul_day": round(cafe_ul_day(p, a.food_mM, a.assimilation), 3),
           "rest_sugar_mM_6h_fast": round(rest_sugar_mM(p), 2), "conc0_mM": p["conc0_mM"]}
    a.out.parent.mkdir(parents=True, exist_ok=True)
    a.out.write_text(json.dumps(out, indent=1))
    print(json.dumps(out))


if __name__ == "__main__":
    main()
