"""s23 frontier stages m10f6-m10f8 (DECISIONS 23 Oct 22:58, 23:20): gate, MB unit check, N26 LD check and the
60 s smokes, in one figure. Panels with no data yet say so.

    python3 scripts/probes/s23_frontier_figure.py   # -> docs/media/s23_frontier.png
"""
from __future__ import annotations

import json
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402

FC = Path("runs/s23/fc")
STAGES = ["m10f3", "m10f6", "m10f7", "m10f8"]
SEEDS = (12, 13, 14, 15)


def load(p: Path):
    return json.loads(p.read_text()) if p.exists() else None


def main(out: Path = Path("docs/media/s23_frontier.png")) -> None:
    fig, ax = plt.subplots(2, 2, figsize=(13, 9.5))
    # A: gate whole-brain rate per seed, marker filled if the silent window passed
    a = ax[0, 0]
    for i, st in enumerate(STAGES):
        for j, s in enumerate(SEEDS):
            d = load(FC / f"gate_{st}_s{s}.json")
            if d is None:
                continue
            ok = (d["silent_last100ms_noneye_spikes_per_ms"] == 0.0 and not d["nan_state"]
                  and d["mujoco_warnings"] == 0 and max(d["hz_by_class"].values()) <= 200)
            a.plot(i + (j - 1.5) * 0.08, d["whole_brain_hz"], "o", color="C0" if ok else "C3",
                   mfc="C0" if ok else "none")
    a.set_xticks(range(len(STAGES)), STAGES)
    a.set_ylabel("whole-brain rate, 1 s gate (Hz)")
    a.set_title("A  Gate G, seeds 12-15 (filled = all gate checks pass)")
    # B: MB types at m10f7, isolated CNS, two seeds, with the stage's training bands
    b = ax[0, 1]
    mb = [load(FC / f"mb_m10f7_s{s}.json") for s in (12, 13)]
    if all(mb):
        types = sorted(t for t in mb[0]["type_hz"] if t.startswith(("MBON", "PAM", "PPL")))
        x = np.arange(len(types))
        for k, (d, s) in enumerate(zip(mb, (12, 13))):
            b.plot(x, [d["type_hz"][t] for t in types], ".", ms=4, label=f"seed {s}", color=f"C{k}")
        for t, lo, hi in (("PPL105", 6.0, 10.0), ("MBON14", 9.7, 15.1)):
            if t in types:
                xi = types.index(t)
                b.vlines(xi, lo, hi, color="k", lw=3, alpha=0.5)
                b.annotate(t, (xi, hi), textcoords="offset points", xytext=(3, 3), fontsize=8)
        b.set_xticks([])
        b.set_xlabel(f"{len(types)} MBON, PAM and PPL types (alphabetical)")
        b.set_ylabel("rate (Hz)")
        b.legend(fontsize=8)
    b.set_title("B  m10f7 MB unit check (bars = training bands)")
    # C: N26 LD check, CT at each lights-on
    c = ax[1, 0]
    ld = load(Path("runs/s23/n26_ld_m10f6.json"))
    if ld:
        wrap = lambda v: (v + 12) % 24 - 12  # noqa: E731
        reg = [wrap(v) for v in ld["registered"]["ct_at_lights_on_by_day"]]
        jmp = ld["reported_jump_ct6"]["ct_at_lights_on_by_day"]
        c.plot(range(len(reg)), reg, "o-", label="start CT 0 (registered: last within ±2 h)")
        c.plot(range(len(jmp)), jmp, "s--", label="start CT 6 (6 h jump, reported)")
        c.axhspan(-2, 2, color="0.9", zorder=0)
        c.set_xlabel("day of 12:12 LD at 1000 lux")
        c.set_ylabel("model CT at lights-on (h)")
        c.legend(fontsize=8)
    c.set_title("C  m10f6 N26 LD check (grey = pass band)")
    # D: smokes, per-class rate against m10f3
    dd = ax[1, 1]
    ref = load(FC / "smoke_m10f3_s12.json")
    txt = []
    if ref:
        r = {k: v[0] for k, v in ref["hz_by_class"].items()}
        for k, st in enumerate(STAGES[1:]):
            d = load(FC / f"smoke_{st}_s12.json")
            if d is None:
                txt.append(f"{st}: smoke not finished")
                continue
            q = {kk: v[0] for kk, v in d["hz_by_class"].items()}
            ks = sorted(set(r) & set(q))
            dd.loglog([max(r[kk], 1e-3) for kk in ks], [max(q[kk], 1e-3) for kk in ks], "o", ms=4,
                      color=f"C{k + 1}", alpha=0.7,
                      label=f"{st}: whole brain {d['rates']['whole_brain_hz']:.3f} Hz, "
                            f"active {d['rates']['frac_active']:.3f}")
        dd.plot([1e-3, 100], [1e-3, 100], "k:", lw=0.8)
        dd.set_xlabel(f"m10f3 class rate, 60 s smoke (Hz; whole brain {ref['rates']['whole_brain_hz']:.3f})")
        dd.set_ylabel("stage class rate (Hz; 0 drawn at 1e-3)")
        if dd.lines[:-1]:
            dd.legend(fontsize=8)
    if txt:
        dd.text(0.03, 0.97, "\n".join(txt), transform=dd.transAxes, va="top", fontsize=9)
    dd.set_title("D  Smoke S, 60 s, seed 12 (pass: 0.162-0.486 Hz, active 0.014-0.042)")
    fig.tight_layout()
    out.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out, dpi=110)
    print(out)


if __name__ == "__main__":
    main()
