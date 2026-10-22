"""s25 analytic fit of the DA-only restoration rate to Hattori et al. 2017 Fig 6F (DECISIONS 22 Oct 04:11).

R(n) = 1 - (1 - r)^(S n): recovery after n stimulations of S DAN spike-steps each, weighted least squares
(weights 1/SEM^2) on the four figure estimates. S is 10 pulses x spikes per pulse (2 guessed; 1 and 4 as
sensitivity). Provisional until S is counted in the network (the in-network confirm). Also prints the
pre-registered resting check: memory lifetime tau = -1/(f ln(1 - r)) at a resting DAN rate f. And a derived
(not pre-registered) resting-depression check: with KCs at rest at f_kc, the mean eligibility is f_kc tau_e, so
weights relax to w*/w0 = r / (r + r_ltd f_kc tau_e) with time constant 1 / (f (r + r_ltd f_kc tau_e)).

    .venv/bin/python scripts/probes/s25_restore_fit.py
"""
from __future__ import annotations

import numpy as np
from scipy.optimize import minimize_scalar

N = np.array([1, 3, 6, 10])
Y = np.array([0.08, 0.18, 0.33, 0.40])        # Hattori 2017 Fig 6F, figure estimates (s25 figure check)
SEM = np.array([0.05, 0.07, 0.06, 0.06])
BAND = [(-0.02, 0.18), (0.04, 0.32), (0.21, 0.45), (0.28, 0.52)]   # pre-registered: mean +- 2 SEM
R_LTD, F_KC, TAU_E = 0.42991, 0.1, 1.0   # m10f4 depression rate (fitted), KC rest (Turner 2008), eligibility (guessed)


def fit(spikes_per_stim: int) -> tuple[float, np.ndarray, float]:
    def chi2(r):
        return float(np.sum(((1 - (1 - r) ** (spikes_per_stim * N) - Y) / SEM) ** 2))
    r = minimize_scalar(chi2, bounds=(1e-6, 0.5), method="bounded", options={"xatol": 1e-9}).x
    return r, 1 - (1 - r) ** (spikes_per_stim * N), chi2(r)


def main() -> None:
    for per_pulse in (2, 1, 4):
        s = 10 * per_pulse
        r, pred, c2 = fit(s)
        inside = all(lo <= p <= hi for p, (lo, hi) in zip(pred, BAND))
        tag = "primary" if per_pulse == 2 else "sensitivity"
        print(f"{tag}: {per_pulse} spikes/pulse, S {s}: r_res {r:.5f} per DAN spike; "
              f"R(1,3,6,10) {np.round(pred, 3).tolist()}; chi2 {c2:.2f} (3 dof); all inside bands {inside}")
        taus = {f: -1 / (f * np.log(1 - r)) for f in (6.0, 8.0, 10.0)}
        print("   resting check, memory tau at DAN rate 6/8/10 Hz (Huang 2018): "
              + ", ".join(f"{t:.0f} s" for t in taus.values())
              + f"; N22 bracket needs >= {2.3 * 3600:.0f} s -> FAIL" if min(taus.values()) < 2.3 * 3600 else "")
        f_max = -1 / (2.3 * 3600 * np.log(1 - r))
        print(f"   highest resting DAN rate compatible with tau >= 2.3 h: {f_max:.4f} Hz")
        print(f"   Hige backward (4 pulses) under a cap-2 variant: ratio {1 + (1 - (1 - r) ** 4):.4f}")
        d = R_LTD * F_KC * TAU_E
        print(f"   resting depression (derived; r_ltd {R_LTD}, KC {F_KC} Hz, tau_e {TAU_E} s): w*/w0 {r / (r + d):.3f}, "
              "approach tau " + ", ".join(f"{1 / (f * (r + d)):.1f} s" for f in (6.0, 8.0, 10.0))
              + f" at 6/8/10 Hz; without restoration w -> 0 with tau {1 / (8.0 * d):.1f} s at 8 Hz")


if __name__ == "__main__":
    main()
