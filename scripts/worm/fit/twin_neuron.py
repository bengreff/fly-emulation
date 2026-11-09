"""Synthetic twin of a neural mechanism for the EKI (weki, 8 Nov 2026; FIT_GENERAL.md sections 5 and 10: "the rule is
re-run on a second, larger twin (a neural mechanism, more than 4 numbers) before the fit").

Forward (a twin forward, not a model component): the published Nicoletti 2024 AIY point neuron, its 7 channels (leak,
nca, egl19, kqt1, shl1, slo1egl19, slo1iso) with the kinetics of `wormemu.nicoletti` (the port checked against NEURON,
scripts/worm/check_port.py) and the published geometry, leak reversal and capacitance (scripts/worm/fit_aiy.py PUB).
No Ca pool (the published AIY model has none). Integration: gates by exponential Euler, the voltage by exponential
Euler with the gates held over the step (exact for frozen gates, stable), dt 0.5 ms, float64, every member and sweep in
one jax.lax.scan. Protocol and observations: FIT2's current clamp (scripts/worm/fit2.py): 2 s settle at 0 pA, then
7 s with a step from 1 to 6 s, sweeps -15, -5, 5, 15, 25, 35 pA, the 4 features per sweep of fit2.features (baseline,
early peak, steady state, after-step) on the 1 ms trace: 24 numbers. Validity: the twin tests the fitting algorithm on
a nonlinear, sloppy neural problem; it is not a claim about AIY.

Smoke (unscored, 22:33): the published densities give baseline -55.3 mV, -128.7 mV at -15 pA, peak +30.2 and steady
+21.5 mV at +35 pA; 100 prior members in 1.4 s on one core, all finite; feature SD across them 12-30 mV.

Pre-registered 8 Nov 22:34 CST (date), before any scored run: the 7 densities hidden, log-uniform box a factor 3 either
side of the published values (guessed); 20 hidden draws (rng 20262108 + k, unit positions uniform on [0.1, 0.9] in the
log box); y = G(x_true) + N(0, 1 mV^2) per feature, Gamma = 1 mV^2 diagonal; 100 members drawn uniform in the unit box
(logit z); the data-misfit controller to t = 1, at most 40 iterations; EKI seed 11 + k. Run for localise "corr" (what
the fit uses) and "fixed" (none), each at inflation 1.0, 1.02, 1.05, 1.1. Reported per (localise, inflation): coverage
(the fraction of the 140 (draw, value) pairs inside the ensemble's 2.5-97.5 % range), per value coverage, per value
recovered (median within a factor 1.25 of the truth) in n of 20, median 95 % width per value, failed members,
iterations. Bar: the fit's inflation is the smallest with coverage >= 0.90 under "corr" (as for the canal twin), and
that replaces the canal's pick in FIT_GENERAL (section 5 says the neural twin fixes it). Falsifier: no inflation in the
list reaches 0.90 under "corr": the EKI at J = 100 is overconfident on a 7-number neural problem, reported, and the fit
needs a remedy first (larger J, wider inflation, repeated starts); nothing is patched here. Identifiability per value
(recovered in >= 18 of 20) is reported with no bar; expectation written now (guessed, not a bar): at least 3 of the 7
identified, and slo1egl19 and slo1iso (two Ca/voltage-gated K) the least.

Result (22:34-23:04, Mac, one core; measured; outputs runs/worm/fit/twin_neuron/, gitignored). Coverage over the 140
pairs: corr 0.979 / 0.971 / 0.986 / 1.000 and none 0.943 / 0.964 / 0.971 / 0.986 at inflation 1.0 / 1.02 / 1.05 / 1.1,
so the rule picks 1.0 under corr (and under none). No member failed; every run reached t = 1 (median 8 iterations
under corr at 1.0, at most 11). Identified (median within 1.25 in >= 18 of 20, corr at 1.0): leak 20, nca 20, kqt1 19;
not: slo1egl19 15, egl19 11, shl1 8, slo1iso 4 (median 95 % width, a factor: leak 1.09, nca 1.05, kqt1 1.56,
slo1egl19 1.63, egl19 3.36, shl1 5.26, slo1iso 7.95 of the box's 9). Without localisation the ranges are narrower
(egl19 2.53, shl1 4.00) and still cover (0.943; nca alone 0.85). So the cut costs precision, not calibration, here.
Expectation against outcome: 3 of 7 identified (expected at least 3); slo1iso the least, as expected, but slo1egl19 is
the 4th best and shl1 the 2nd least, not as expected. All 7 within 1.25 in only 1 of 20 draws (the canal's bar, not
this twin's): FIT2's clamp features at 1 mV fix 3 of the published AIY model's 7 densities. Integrator check: dt 0.5
and 0.1 ms agree within 0.0002 mV on every feature at the published densities (measured).

Usage: python scripts/worm/fit/twin_neuron.py smoke
       python scripts/worm/fit/twin_neuron.py run OUT.json fixed|corr INFLATION [DRAWS]
"""
from __future__ import annotations

import json
import sys
import time
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "scripts" / "worm"))
import jax  # noqa: E402

jax.config.update("jax_enable_x64", True)
import jax.numpy as jnp  # noqa: E402
import fit2  # noqa: E402  (FIT2's protocol constants and features, read-only)
from wormemu import nicoletti as lib  # noqa: E402
from wormemu.fit import eki as E  # noqa: E402

CH = ["leak", "nca", "egl19", "kqt1", "shl1", "slo1egl19", "slo1iso"]
PUB_NS = {"leak": 0.14, "nca": 0.06, "egl19": 0.1, "kqt1": 0.2, "shl1": 0.5, "slo1egl19": 0.92, "slo1iso": 1.0}
EL, CM, SURF = -89.57, 1.6, 65.89e-8                     # mV, uF/cm2, cm2 (fit_aiy.PUB, published)
ST = ["egl19_m", "egl19_h", "kqt1_m", "kqt1_s", "shl1_m", "shl1_hf", "shl1_hs", "slo1egl19_m", "slo1iso_m"]
DT, V0 = 0.5, -65.0                                      # ms; mV (neuron_ref.py's v_init)
AMPS = fit2.AMPS_PA[fit2.FIT2_SWEEPS].astype(float)      # pA
NS = int(round((fit2.T_SETTLE + fit2.T_END) / DT))
BOX = 3.0                                                # each density within a factor 3 of the published one (guessed)
LO, HI = np.log([PUB_NS[c] / BOX for c in CH]), np.log([PUB_NS[c] * BOX for c in CH])
NOISE_MV = 1.0                                           # guessed: SD of each feature's observation noise


def _inf_tau(v, st):
    r, e, u = lib.all_rates(v, lib.CA_EQ_M)
    r.update(lib.coupled_rates(v, st, e, u, want={"slo1egl19_m"}))
    return {s: r[s] for s in ST}


def _i_total(v, st, g):
    i, _ = lib.currents(v, st, g, EL)
    return sum(i.values())


@jax.jit
def _run(g_ns, amps):
    """g_ns [N, 7] nS, amps [N] pA -> V [N, 7000] at 1 ms after the settle (the end of each ms)."""
    g = {c: g_ns[:, k] * 1e-9 / SURF for k, c in enumerate(CH)}          # S/cm2
    inj = amps * 1e-9 / SURF                                               # mA/cm2 per pA step
    v = jnp.full(amps.shape, V0)
    st = {s: it[0] for s, it in _inf_tau(v, {"egl19_m": lib.egl19_rates(v)[0]}).items()}   # gates at rest values

    def one(c, on):
        v, st = c
        it = _inf_tau(v, st)
        st = {s: it[s][0] + (st[s] - it[s][0]) * jnp.exp(-DT / it[s][1]) for s in ST}
        i0 = _i_total(v, st, g)
        G = _i_total(v + 1.0, st, g) - i0                                  # S/cm2 (linear in v, gates fixed)
        vinf = v - (i0 - on * inj) / G
        v = vinf + (v - vinf) * jnp.exp(-DT * G / (CM * 1e-3))
        return (v, st)

    def ms(c, k):
        on = ((k >= fit2.T_SETTLE + fit2.T_ON) & (k < fit2.T_SETTLE + fit2.T_OFF)).astype(float)
        c = one(c, on)
        c = one(c, on)
        return c, c[0]

    _, V = jax.lax.scan(ms, (v, st), jnp.arange(fit2.T_SETTLE + fit2.T_END))
    return V[fit2.T_SETTLE:].T


def forward(x):
    """x [J, 7] densities (nS) -> (G [J, 24], ok [J])"""
    J = len(x)
    V = np.asarray(_run(jnp.asarray(np.repeat(x, len(AMPS), 0)), jnp.asarray(np.tile(AMPS, J)))).reshape(J, len(AMPS), -1)
    t = np.arange(1, fit2.T_END + 1, dtype=float)
    ok = np.isfinite(V).all((1, 2))
    G = np.full((J, 4 * len(AMPS)), np.nan)
    for j in np.flatnonzero(ok):
        G[j] = fit2.features(t, V[j], AMPS).ravel()
    return G, ok


def to_x(z):
    return np.exp(LO + (HI - LO) / (1 + np.exp(-z)))


def smoke():
    x = np.array([[PUB_NS[c] for c in CH]])
    t0 = time.time()
    G, ok = forward(x)
    t1 = time.time()
    G100, ok100 = forward(to_x(np.random.default_rng(0).normal(size=(100, 7))))
    t2 = time.time()
    print("published features [sweep x (base, early, ss, post)] mV:\n", np.round(G.reshape(-1, 4), 2))
    print(f"first call (compile + 1 member) {t1 - t0:.1f} s; 100 members {t2 - t1:.1f} s; finite {ok100.sum()} / 100")
    print("100 prior members, feature SD across members (mV):", np.round(np.nanstd(G100, 0).reshape(-1, 4), 2))


def one(k, localise, infl):
    rng = np.random.default_rng(20262108 + k)
    u = rng.uniform(0.1, 0.9, len(CH))
    x_true = to_x(np.log(u / (1 - u)))
    y = forward(x_true[None])[0][0] + rng.normal(0, NOISE_MV, 4 * len(AMPS))
    u0 = rng.uniform(size=(100, len(CH)))
    e = E.EKI(np.log(u0 / (1 - u0)), y, np.full(len(y), NOISE_MV ** 2), seed=11 + k, inflation=infl, localise=localise)
    nfail = 0
    for _ in range(40):
        if e.done:
            break
        g, ok = forward(to_x(e.z))
        nfail += int((~ok).sum())
        e.update(g, ok)
    xs = to_x(e.z)
    med = np.median(xs, 0)
    lo, hi = np.percentile(xs, [2.5, 97.5], axis=0)
    return dict(x_true=x_true.tolist(), median=med.tolist(), ratio=(med / x_true).tolist(),
                inside=((lo <= x_true) & (x_true <= hi)).tolist(), width=(hi / lo).tolist(),
                rec=(np.abs(np.log(med / x_true)) < np.log(1.25)).tolist(), done=e.done, iterations=len(e.dts),
                failed_members=nfail)


def run(out, localise, infl, draws=20):
    t0 = time.time()
    rs = [one(k, localise, infl) for k in range(draws)]
    o = dict(localise=localise, inflation=infl, draws=draws, runs=rs,
             coverage=float(np.mean([v for r in rs for v in r["inside"]])),
             coverage_by_value=dict(zip(CH, np.mean([r["inside"] for r in rs], 0).tolist())),
             recovered_by_value=dict(zip(CH, np.sum([r["rec"] for r in rs], 0).tolist())),
             all_recovered=int(sum(all(r["rec"]) for r in rs)),
             median_width=dict(zip(CH, np.median([r["width"] for r in rs], 0).tolist())),
             all_done=all(r["done"] for r in rs), iterations=[r["iterations"] for r in rs],
             failed_members=sum(r["failed_members"] for r in rs), wall_s=time.time() - t0)
    Path(out).write_text(json.dumps(o, indent=1))
    print(localise, infl, "coverage", round(o["coverage"], 3), {c: round(v, 2) for c, v in o["coverage_by_value"].items()},
          "recovered", o["recovered_by_value"], "all", o["all_recovered"], "width",
          {c: round(v, 2) for c, v in o["median_width"].items()}, "done", o["all_done"], "failed", o["failed_members"],
          f"wall {o['wall_s']:.0f} s", flush=True)


if __name__ == "__main__":
    if sys.argv[1] == "smoke":
        smoke()
    else:
        run(sys.argv[2], sys.argv[3], float(sys.argv[4]), int(sys.argv[5]) if len(sys.argv) > 5 else 20)
