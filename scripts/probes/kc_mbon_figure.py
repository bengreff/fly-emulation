"""Figure for F-S24-2 (fly2, s24): the Hige 2015 fit, the Handler 2019 held-out ISI curve and the N22
recovery check, from `kc_mbon_pairing.py` outputs in runs/s24/kc/.

    .venv/bin/python scripts/probes/kc_mbon_figure.py --dir runs/s24/kc --out runs/s24/kc/fig_kc_mbon.png
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402

SEEDS = (12, 13, 14, 15)


def cs(d: dict, which: str = "cs_plus") -> float:
    return next(x["charge_ratio"] for x in d["result"] if x["set"] == which)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dir", type=Path, default=Path("runs/s24/kc"))
    ap.add_argument("--out", type=Path, required=True)
    a = ap.parse_args()
    ld = lambda n: json.loads((a.dir / n).read_text())  # noqa: E731
    fig, ax = plt.subplots(1, 3, figsize=(14, 4.2))

    fits = [ld(f"fit_s{s}.json")["fit"]["r_ltd_fitted"] for s in SEEDS]
    conf = [cs(ld(f"confirm_s{s}.json")) for s in SEEDS]
    ax[0].axhspan(0.06, 0.14, color="0.9", label="pass band 0.10 ± 0.04")
    ax[0].axhline(0.10, color="k", lw=1, label="Hige 2015 Fig 3D (−90%)")
    ax[0].plot(SEEDS, conf, "o", color="C3", label=f"model, shared rate {np.mean(fits):.3f}")
    for s, r in zip(SEEDS, fits):
        ax[0].annotate(f"own fit {r:.3f}", (s, conf[SEEDS.index(s)]), textcoords="offset points",
                       xytext=(0, 8), ha="center", fontsize=7)
    ax[0].set(xlabel="seed (own odour KC set)", ylabel="CS+ KC->MBON charge, after / before",
              title="Fit: MBON-γ1pedc, one forward pairing", ylim=(0, 0.3), xticks=SEEDS)
    ax[0].legend(fontsize=7, loc="upper left")

    isis = (-1200, 0, 500, 6000)
    r = np.array([[cs(ld(f"handler_isi{i}_s{s}.json")) for s in SEEDS] for i in isis])
    x = np.array(isis) / 1000.0
    ax[1].axhline(1.0, color="k", lw=0.8)
    for j in range(len(SEEDS)):
        ax[1].plot(x, r[:, j], ".", color="0.6")
    ax[1].plot(x, r.mean(1), "o", ms=8, color="C0", label="model, mean of 4 seeds (only these ISIs run)")
    for xi, txt, y in ((-0.6, "Handler: potentiation\n(H3, expected fail: LTP off)", 1.12),
                       (0.0, "depression", 0.25), (0.5, "depression", 0.35), (6.0, "minimal", 0.8)):
        ax[1].annotate(txt, (xi, y), ha="center", fontsize=7, color="C2")
    ax[1].set(xlabel="ISI, DAN onset − KC onset (s)", ylabel="CS+ charge, after / before",
              title="Held out: Handler 2019 γ4 (signs only)", ylim=(0, 1.3))
    ax[1].legend(fontsize=7, loc="center right")

    rec = ld("recovery_s12.json")["recovery"]
    t = np.array(rec["t_ms"])
    dev = np.array(rec["mean_dev"])
    ax[2].semilogy(t, np.abs(dev), ".", ms=3, label="model |mean w − w0|, CS+ edges")
    ax[2].semilogy(t, np.abs(dev[0]) * np.exp(-t / 1000.0), "k-", lw=0.8, label="tau 1000 ms (override)")
    ax[2].set(xlabel="ms after pairing (unstimulated)", ylabel="|mean deviation| (weight units)",
              title=f"N22 forgetting check: tau fit {rec['tau_fit_ms']:.1f} ms")
    ax[2].legend(fontsize=7)
    fig.suptitle("m10f4 KC->MBON (fly2 s24; DECISIONS 22 Oct 01:55): KC drive Turner 2008, isolated CNS",
                 fontsize=10)
    fig.tight_layout()
    a.out.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(a.out, dpi=130)
    print(a.out)


if __name__ == "__main__":
    main()
