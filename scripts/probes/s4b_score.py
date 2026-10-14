"""S4b scoring (s13; DECISIONS 14 Oct 00:12, S4b pre-registration). Written before any S4b output existed.

    fit      25 mV members only: class rates against Azevedo 2020's force-probe rates, the silent-at-rest constraint,
             and the rhythm pass (S4a's criterion with the 7-16 Hz band). Picks s*. Prints nothing at 15/40 mV.
    heldout  at s* only (spend once): recruitment order across 15/25/40 mV; spike precedence reported.

    python scripts/probes/s4b_score.py fit runs/s13/bypass/s4b
    python scripts/probes/s4b_score.py heldout runs/s13/bypass/s4b --scale <s*>
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
from bypass_moddepth import depth  # noqa: E402

TARGET_HZ = {"fast": 1.0, "intermediate": 10.0, "slow": 60.0}   # Azevedo 2020 Fig 5-fig supp 1A, read off the plot
ACCEPT = np.log(3.0)                                              # per-class bar on |log((r+1)/(r*+1))|
PRE, DRV, POST, SCORED = (0, 300), (300, 1300), (1300, 1500), (500, 1300)
COXA_ANTAGONIST = {("promotor", "remotor"), ("anterior rotator", "posterior rotator")}
CLASSES = ("slow", "intermediate", "fast")


def load(d: Path, s: float, mv: float):
    return np.load(d / f"s4b_s{s:g}_{mv:g}mv_traces.npz", allow_pickle=False)


def scales(d: Path) -> list[float]:
    return sorted({float(m[0]) for m in json.loads((d / "meta.json").read_text())["members"]})


def legs(z) -> np.ndarray:
    return np.char.add(z["mn_neuromere"].astype(str), z["mn_side"].astype(str))


def rate(counts: np.ndarray, w) -> np.ndarray:
    """Per-MN rate (Hz) over window w (ms), counts (ms, mn)."""
    return counts[w[0]:w[1]].sum(0) / ((w[1] - w[0]) / 1000.0)


def class_rates(z, w) -> dict:
    """{leg: {class: mean per-MN rate}} for the tibia flexors."""
    r, cls, lg = rate(z["mn_counts"].astype(float), w), z["mn_cls"].astype(str), legs(z)
    return {l: {c: float(r[(lg == l) & (cls == c)].mean()) for c in CLASSES if ((lg == l) & (cls == c)).any()}
            for l in sorted(set(lg[cls != ""]))}


def antagonists(a: str, b: str) -> bool:
    if a[:2] != b[:2]:
        return False
    if " coxa " in a and " coxa " in b:
        return (a.split(" coxa ")[1], b.split(" coxa ")[1]) in COXA_ANTAGONIST | {(y, x) for x, y in COXA_ANTAGONIST}
    ja, sa = a.rsplit(" ", 1)
    jb, sb = b.rsplit(" ", 1)
    return ja == jb and float(sa) == -float(sb)


def smooth(x, k=20):
    return np.convolve(x, np.ones(k) / k, mode="same")


def lagged(a, b, lo=10, hi=30):
    """Best r over |lag| in [lo, hi] ms (S4a: lagged peak 10-30 ms)."""
    best = -2.0
    for L in range(lo, hi + 1):
        for x, y in ((a[L:], b[:-L]), (a[:-L], b[L:])):
            if x.std() > 0 and y.std() > 0:
                best = max(best, float(np.corrcoef(x, y)[0, 1]))
    return best


def rhythm(z) -> dict:
    """S4a pass with the 7-16 Hz band: two antagonist pools of one leg both transfer-pass, phase relation
    r <= -0.3 at zero lag or a lagged peak (10-30 ms) r >= 0.5; summed leg-MN rate post-drive <= 1.5x pre-drive."""
    pr, names = z["pool_rate"].astype(float), [str(x) for x in z["pool_names"]]
    passed = {}
    for j, nm in enumerate(names):
        x = pr[SCORED[0]:SCORED[1], j]
        if x.sum() < 10:
            continue
        s = depth(x, 1e-3, 3.0, hi=16.0)
        rb = pr[PRE[0]:PRE[1], j].mean()
        drive_dep = rb == 0 or x.mean() / rb >= 2.0
        if drive_dep and s["f0_hz"] and 7 <= s["f0_hz"] <= 16 and s["depth"] >= 0.5 and s["frac_cycles_floor"] >= 2 / 3:
            passed[nm] = s
    pairs = []
    for i, a in enumerate(sorted(passed)):
        for b in sorted(passed)[i + 1:]:
            if antagonists(a, b):
                xa = smooth(pr[SCORED[0]:SCORED[1], names.index(a)])
                xb = smooth(pr[SCORED[0]:SCORED[1], names.index(b)])
                r0 = float(np.corrcoef(xa, xb)[0, 1]) if xa.std() > 0 and xb.std() > 0 else None
                rl = lagged(xa, xb)
                if (r0 is not None and r0 <= -0.3) or rl >= 0.5:
                    pairs.append((a, b, r0, round(rl, 3)))
    tot = pr.sum(1)
    pre, post = tot[PRE[0]:PRE[1]].mean(), tot[POST[0]:POST[1]].mean()
    stops = bool(post <= 1.5 * pre)
    return dict(transfer_pass=sorted(passed), antagonist_pairs=pairs, post_over_pre=round(post / pre, 2) if pre else None,
                stops=stops, rhythm_pass=bool(pairs) and stops)


def cmd_fit(a) -> None:
    d = Path(a.dir)
    rows = {}
    for s in scales(d):
        z = load(d, s, 25.0)
        drv, pre = class_rates(z, SCORED), class_rates(z, PRE)
        errs = {c: [np.log((v[c] + 1) / (TARGET_HZ[c] + 1)) for v in drv.values() if c in v] for c in CLASSES}
        e_rate = float(np.mean([e ** 2 for c in CLASSES for e in errs[c]]))
        mean_drv = {c: round(float(np.mean([v[c] for v in drv.values() if c in v])), 2) for c in CLASSES}
        mean_pre = {c: round(float(np.mean([v[c] for v in pre.values() if c in v])), 2) for c in CLASSES}
        silent = mean_pre["intermediate"] <= 1.0 and mean_pre["fast"] <= 1.0
        accept = all(abs(np.log((mean_drv[c] + 1) / (TARGET_HZ[c] + 1))) <= ACCEPT for c in CLASSES)
        rows[s] = dict(e_rate=round(e_rate, 3), class_hz_drive=mean_drv, class_hz_pre=mean_pre,
                       silent_at_rest=silent, rates_within_3x=accept, **rhythm(z))
        r = rows[s]
        print(f"s {s:>5g}: E_rate {r['e_rate']:.3f}  drive {mean_drv}  pre {mean_pre}  silent {silent}  "
              f"within3x {accept}  transfer {len(r['transfer_pass'])}  pairs {len(r['antagonist_pairs'])}  "
              f"post/pre {r['post_over_pre']}  rhythm {r['rhythm_pass']}")
    ok = [s for s, r in rows.items() if r["silent_at_rest"] and r["rhythm_pass"]]
    best = min(ok, key=lambda s: rows[s]["e_rate"]) if ok else None
    verdict = ("FALSIFIED: no scale in 1-25 passes the rhythm with interneuron/fast MNs silent at rest" if best is None
               else "FIT ACCEPTED" if rows[best]["rates_within_3x"] else "FIT REJECTED: rhythm passes but rates off by >3x")
    print(f"s* = {best}  ->  {verdict}")
    (d / "fit.json").write_text(json.dumps(dict(rows={str(k): v for k, v in rows.items()}, s_star=best,
                                                verdict=verdict), indent=1, default=str))


def cmd_heldout(a) -> None:
    d = Path(a.dir)
    out = {"scale": a.scale, "drives": {}}
    for mv in (15.0, 25.0, 40.0):
        z = load(d, a.scale, mv)
        c, cls, lg = z["mn_counts"].astype(float), z["mn_cls"].astype(str), legs(z)
        n_spk = c[DRV[0]:DRV[1]].sum(0)
        frac = {k: round(float((n_spk[cls == k] >= 2).mean()), 3) for k in CLASSES}
        # Fig 5C-style precedence: intermediate spikes with a same-leg slow spike in the preceding 25 ms, vs chance
        prec, chance = [], []
        for l in sorted(set(lg[cls != ""])):
            sl = c[:, (lg == l) & (cls == "slow")].sum(1)
            it = c[DRV[0]:DRV[1], (lg == l) & (cls == "intermediate")].sum(1)
            cs = np.concatenate([[0], np.cumsum(sl)])
            for t in np.flatnonzero(it):
                tt = t + DRV[0]
                prec += [cs[tt] - cs[max(tt - 25, 0)] > 0] * int(it[t])
            rs = sl[DRV[0]:DRV[1]].mean() * 1000.0
            chance += [1 - np.exp(-rs * 0.025)] * int(it.sum())
        out["drives"][mv] = dict(recruited_fraction=frac, int_spikes=len(prec),
                                 int_preceded_by_slow=round(float(np.mean(prec)), 3) if prec else None,
                                 chance=round(float(np.mean(chance)), 3) if chance else None)
    F = [out["drives"][mv]["recruited_fraction"] for mv in (15.0, 25.0, 40.0)]
    ordered = all(f["slow"] >= f["intermediate"] >= f["fast"] for f in F)
    nondegenerate = any(f["intermediate"] > 0 and (f["slow"] > f["intermediate"] or f["intermediate"] > f["fast"])
                        for f in F)
    out["recruitment_order_pass"] = bool(ordered and nondegenerate)
    print(json.dumps(out, indent=1))
    (d / f"heldout_s{a.scale:g}.json").write_text(json.dumps(out, indent=1, default=str))


def main() -> None:
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    f = sub.add_parser("fit"); f.add_argument("dir")
    h = sub.add_parser("heldout"); h.add_argument("dir"); h.add_argument("--scale", type=float, required=True)
    a = ap.parse_args()
    {"fit": cmd_fit, "heldout": cmd_heldout}[a.cmd](a)


if __name__ == "__main__":
    main()
