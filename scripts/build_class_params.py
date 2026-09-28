"""Write the per-circuit-class N3/N5 rows of data/model/parameters.csv (session 10).

One row per (circuit class, property) for the four class-grain properties that
lif._class_scales reads (registry keys `class:<circuit_class>|<property>`).
Idempotent: previous class rows (param_id n3c_* / n5c_*) are replaced.

    uv run python scripts/build_class_params.py
"""
from pathlib import Path

import pandas as pd

REPO = Path(__file__).resolve().parents[1]
PAR = REPO / "data" / "model" / "parameters.csv"
CLS = REPO / "data" / "model" / "classes.csv"

# property -> (mechanism, prefix, unit, lo, hi, basis, bound source, dist, a, b, stage, prior basis)
SPEC = {
    "release_scale": ("N5", "n5c_rel", "dimensionless", 0.1, 20, "guessed",
                      "one decade below to the measured ORN->PN excess (10.9x the global "
                      "efficacy, F-AL-4) and ~2x beyond", "lognormal", 1, 0.5, 1,
                      "neutral (m4): every class releases the shared efficacy"),
    "input_scale": ("N5", "n5c_inp", "dimensionless", 0.1, 20, "guessed",
                    "as release_scale (postsynaptic input resistance varies ~2-10x across "
                    "central neurons; larval uEPSPs 1-10 mV)", "lognormal", 1, 0.5, 1,
                    "neutral (m4)"),
    "tonic_drive": ("N3", "n3c_drive", "mV", -10, 20, "guessed",
                    "as the global row n3_drive: tonic depolarisation must keep spontaneous "
                    "rates below ~50 Hz in most central neurons; rest-potential spread "
                    "-48 to -68 mV (Gouwens & Wilson 2009; larval survey 2002)",
                    "normal", 0, 2, 1, "neutral (m4): no tonic drive; measured spontaneous "
                    "rates exist for few classes (PN 1-5 Hz, KC ~0.1 Hz; both spent)"),
    "noise": ("N3", "n3c_noise", "mV/sqrt(ms)", 0, 3, "guessed",
              "as the global row n14_noise: membrane noise of a few mV rms", "normal", 0, 0.5, 2,
              "neutral (m4): noiseless, as Shiu 2024"),
}


def main():
    par = pd.read_csv(PAR, dtype=str, keep_default_na=False)
    par = par[~par.param_id.str.match(r"^(n3c|n5c)_")]
    cls = pd.read_csv(CLS, keep_default_na=False)
    cc = cls.groupby("circuit_class").n_cells.sum()
    rows = []
    for c, n in cc.items():
        for prop, (mech, pre, unit, lo, hi, basis, src, dist, a, b, stage, pbasis) in SPEC.items():
            neutral = 1 if prop.endswith("scale") else 0
            rows.append(dict(
                param_id=f"{pre}_{c}", mechanism_id=mech, grain="class",
                applies_to=f"circuit class {c} ({n} cells)", unit=unit,
                registry_key=f"class:{c}|{prop}", bio_min=lo, bio_max=hi, bound_basis=basis,
                bound_source=src, bound_verified="unverified", prior_dist=dist, prior_a=a,
                prior_b=b, prior_basis="guessed", prior_source=pbasis, value_fixed="",
                current_m4=neutral, release_stage=stage, label="guessed",
                notes="s10 class grain (scripts/build_class_params.py)"))
    out = pd.concat([par, pd.DataFrame(rows).astype(str)], ignore_index=True)
    out.to_csv(PAR, index=False)
    print(f"{len(rows)} class rows for {len(cc)} circuit classes -> {PAR.relative_to(REPO)}")


if __name__ == "__main__":
    main()
