"""N21/N22 probe (fly2, s24): one odour-DAN pairing in the whole network, and the KC->MBON change it leaves.

Isolated CNS (no body), membrane noise as in the profile (off in m10f). An "odour" is a fixed random set of Kenyon cells (--kc-frac of all KCs,
seeded) each firing Poisson spikes in the odour window (--kc-spikes per KC on average), driven by kicks;
the sensory path to the KCs is bypassed, as in an explant with KC drive. A second disjoint set is the CS-.
The DAN train kicks every cell of --dan at the given times relative to odour onset (negative = DAN first).
Hige et al. 2015 Neuron 88:985: MBON-γ1pedc>α/β (MBON11), PPL1-γ1pedc (PPL101). Handler et al. 2019 Cell
178:60: MBON-γ4>γ1γ2 (MBON05), PAM-γ4 (PAM08).

Measured here, per MBON type: the CS+ and CS- "charge ratio" after / before pairing on the KC->MBON
component, sum over that set's KC->MBON edges of (KC spikes in the pairing) x weight. It is the charge one
re-presentation of the same KC pattern would carry through the plastic synapses. With --fit-target the
pairing is first run with the depression rate at 0, the KC eligibility of every CS+ KC is recorded at
each DAN spike, and the rate that gives the target ratio is solved by replaying the rule offline; then the
pairing is rerun at that rate to confirm it in the network.

    .venv/bin/python scripts/probes/kc_mbon_pairing.py --profile m10f3 --fit-target 0.10 \\
        --out runs/s24/kc/hige_fit.json

Pre-registered in DECISIONS 22 Oct 01:55 (fit, Handler 2019 held-out ISIs, N22 recovery check).
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))
from flyemu import connectome, electrical, lif, profiles  # noqa: E402
from flyemu.registry import Policy, Registry  # noqa: E402

DT = 0.1
SW = "cell_type:all|"


def build(profile: str, ov: dict[str, float], seed: int):
    reg = Registry(Policy.MINIMAL)
    prof = profiles.apply(reg, profile)
    reg.overrides.update(ov)
    conn = connectome.build(reg, min_synapses=profiles.WORKING_MIN_SYNAPSES)
    params = lif.default_params(reg, conn, timestep_ms=DT)
    el = electrical.build(reg, conn)
    net = lif.Network(conn, params, DT, rng=np.random.default_rng(seed))
    net.elec = el if len(el[0]) else None
    return prof, conn, net


def run_pairing(net, conn, kick_mv, cs_plus, cs_minus, kc_times, dan, dan_ms, odour_ms, settle_ms,
                record_elig=False):
    """Settle, then one pairing. Returns per-KC spike counts in the pairing, the KC->MBON weights
    before and after, and (optionally) the CS+ eligibility at each DAN kick."""
    for _ in range(int(settle_ms / DT)):
        net.step()
    t0 = min(0.0, min(dan_ms)) - 100.0
    t1 = max(odour_ms, max(dan_ms)) + 300.0
    steps = np.arange(int(round(t0 / DT)), int(round(t1 / DT)))
    kc_steps = {}
    for c, ts in zip(cs_plus, kc_times):
        for tt in ts:
            kc_steps.setdefault(int(round(tt / DT)), []).append(int(c))
    dan_steps = {int(round(t / DT)) for t in dan_ms}
    w_before = net.w[net.kc_e].copy()
    n_spk = np.zeros(conn.n, np.int32)
    elig = []
    for s in steps:
        idx = list(kc_steps.get(int(s), []))
        if int(s) in dan_steps:
            if record_elig:
                elig.append(net.kc_elig.copy())   # decayed to this step before the DAN spike lands
            idx += [int(d) for d in dan]
        sp = net.step(kick=(np.array(idx, np.int64), kick_mv) if idx else None)
        n_spk[sp] += 1
    return n_spk, w_before, net.w[net.kc_e].copy(), elig


def charge_ratio(net, conn, mbon, kcset, n_spk, w_before, w_after):
    m = np.isin(net.kc_post, mbon) & np.isin(net.kc_pre, kcset)
    q = n_spk[net.kc_pre[m]].astype(np.float64)
    b = float((q * w_before[m]).sum())
    return (float((q * w_after[m]).sum()) / b if b else float("nan")), int(m.sum()), b


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--profile", default="m10f3")
    ap.add_argument("--set", action="append", default=[], help="extra override entity|property=value")
    ap.add_argument("--mbon", default="MBON11")
    ap.add_argument("--dan", default="PPL101")
    ap.add_argument("--dan-ms", default="200,700,1200,1700", help="DAN kick times from odour onset")
    ap.add_argument("--odour-ms", type=float, default=1000.0)
    ap.add_argument("--kc-frac", type=float, default=0.06, help="Turner 2008: 6 +- 5% of KCs respond")
    ap.add_argument("--kc-spikes", type=float, default=2.2, help="mean spikes per CS+ KC per odour")
    ap.add_argument("--kc-spikes-by-type", default="KCab:2.2,KCa'b':4.9",
                    help="type prefix:mean spikes, first match wins; others take --kc-spikes "
                         "(Turner, Bazhenov & Laurent 2008 J Neurophysiol 99:734, 0.5 s odours)")
    ap.add_argument("--settle-ms", type=float, default=300.0)
    ap.add_argument("--seed", type=int, default=12)
    ap.add_argument("--fit-target", type=float, default=None, help="CS+ charge ratio to fit the LTD rate to")
    ap.add_argument("--recovery-ms", type=float, default=0.0, help="N22 check: unstimulated ms after pairing")
    ap.add_argument("--out", type=Path, required=True)
    a = ap.parse_args()
    ov = {k: float(v) for k, v in (s.rsplit("=", 1) for s in a.set)}
    dan_ms = [float(x) for x in a.dan_ms.split(",")]
    rng = np.random.default_rng(a.seed)

    def setup(ov_run):
        prof, conn, net = build(a.profile, ov_run, a.seed)
        t = conn.neurons.type.fillna("")
        kc = np.flatnonzero((conn.neurons["class"].fillna("") == "Kenyon_Cell").to_numpy())
        return prof, conn, net, t, kc

    out = {"profile": a.profile, "overrides": ov, "mbon": a.mbon, "dan": a.dan, "dan_ms": dan_ms,
           "odour_ms": a.odour_ms, "kc_frac": a.kc_frac, "kc_spikes": a.kc_spikes,
           "kc_spikes_by_type": a.kc_spikes_by_type, "seed": a.seed}
    runs = []
    ov_fit = dict(ov)
    if a.fit_target is not None:
        ov_fit[SW + "kc_mbon_ltd_timing_rate"] = 1e-9   # rule built and recording, weights unchanged
    prof, conn, net, t, kc = setup(ov_fit)
    if net.kc_edge is None:
        raise SystemExit("KC->MBON plasticity is not built in this profile (all rates 0)")
    perm = rng.permutation(kc)
    k = int(round(a.kc_frac * len(kc)))
    cs_plus, cs_minus = np.sort(perm[:k]), np.sort(perm[k:2 * k])
    by_type = [(k_, float(v_)) for k_, v_ in (x.rsplit(":", 1) for x in a.kc_spikes_by_type.split(",") if x)]
    mean_of = [next((v_ for k_, v_ in by_type if t.iat[c].startswith(k_)), a.kc_spikes) for c in cs_plus]
    kc_times = [np.sort(rng.uniform(0.0, a.odour_ms, rng.poisson(mu))) for mu in mean_of]
    mbon = np.flatnonzero(t.isin(a.mbon.split(",")).to_numpy())
    dan = np.flatnonzero(t.isin(a.dan.split(",")).to_numpy())
    comp = np.asarray(net.M_da[:, dan].sum(axis=1)).ravel() > 0
    out.update({"n_kc": int(len(kc)), "n_cs_plus": int(k), "n_mbon": int(len(mbon)), "n_dan": int(len(dan)),
                "dan_contacts_mbon": bool(comp[mbon].all()),
                "kc_to_mbon_edges_cs_plus": int((np.isin(net.kc_post, mbon) & np.isin(net.kc_pre, cs_plus)).sum())})
    n_spk, wb, wa, elig = run_pairing(net, conn, prof["kick_mv"], cs_plus, cs_minus, kc_times, dan, dan_ms,
                                      a.odour_ms, a.settle_ms, record_elig=a.fit_target is not None)
    if a.fit_target is not None:
        m = np.isin(net.kc_post, mbon) & np.isin(net.kc_pre, cs_plus)
        pre_m, q = net.kc_pre[m], n_spk[net.kc_pre[m]].astype(np.float64)
        w0 = wb[m].astype(np.float64)
        hit = [bool(comp[mbon].any())] * len(elig)

        def ratio(r):
            f = np.ones(len(pre_m))
            for e, h in zip(elig, hit):
                if h:
                    f *= np.clip(1.0 - r * e[pre_m], 0.0, 1.0)
            return float((q * w0 * f).sum() / (q * w0).sum())
        lo, hi = 0.0, 1.0
        while ratio(hi) > a.fit_target and hi < 1e3:
            hi *= 2.0
        for _ in range(60):
            mid = 0.5 * (lo + hi)
            lo, hi = (mid, hi) if ratio(mid) > a.fit_target else (lo, mid)
        r_fit = 0.5 * (lo + hi)
        out["fit"] = {"target": a.fit_target, "r_ltd_fitted": r_fit, "replay_ratio": ratio(r_fit),
                      "elig_at_dan_mean_cs_plus": [float(e[cs_plus].mean()) for e in elig],
                      "kc_spikes_per_cs_plus_kc": float(n_spk[cs_plus].mean())}
        print("fit", json.dumps(out["fit"]), flush=True)
        ov[SW + "kc_mbon_ltd_timing_rate"] = r_fit
        prof, conn, net, t, kc = setup(ov)
        n_spk, wb, wa, _ = run_pairing(net, conn, prof["kick_mv"], cs_plus, cs_minus, kc_times, dan, dan_ms,
                                       a.odour_ms, a.settle_ms)
    for name, s in (("cs_plus", cs_plus), ("cs_minus", cs_minus)):
        # the CS- set did not fire in the pairing: weigh it by the CS+ mean count so the ratio is defined
        q = n_spk.copy()
        if name == "cs_minus":
            q[s] = max(1, int(round(n_spk[cs_plus].mean())))
        r, ne, b = charge_ratio(net, conn, mbon, s, q, wb, wa)
        runs.append({"set": name, "charge_ratio": r, "edges": ne, "kc_spikes_mean": float(n_spk[s].mean())})
        print(name, json.dumps(runs[-1]), flush=True)
    out["result"] = runs
    if a.recovery_ms > 0:
        # N22 unit check: unstimulated, the mean CS+ deviation (w - w0) on this MBON should decay with tau
        m = np.isin(net.kc_post, mbon) & np.isin(net.kc_pre, cs_plus)
        w0 = net.kc_w0[m].astype(np.float64)
        tt, dev = [], []
        for s_ in range(int(a.recovery_ms / DT)):
            net.step()
            if s_ % 100 == 0:
                tt.append(s_ * DT)
                dev.append(float((net.w[net.kc_e][m] - w0).mean()))
        y = np.abs(np.array(dev))
        ok = y > 1e-3 * y[0]
        tau = float(-1.0 / np.polyfit(np.array(tt)[ok], np.log(y[ok]), 1)[0])
        out["recovery"] = {"t_ms": tt, "mean_dev": dev, "tau_fit_ms": tau, "points": int(ok.sum())}
        print("recovery", json.dumps({"tau_fit_ms": tau, "points": int(ok.sum()), "dev0": dev[0]}), flush=True)
    out["final_overrides"] = ov
    a.out.parent.mkdir(parents=True, exist_ok=True)
    a.out.write_text(json.dumps(out, indent=1))


if __name__ == "__main__":
    main()
