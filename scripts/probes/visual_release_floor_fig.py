"""Figure: LMC output release floor test (s12 vision, DECISIONS 6 Oct 04:19). Compares the v0 arm with v0r (v0 plus
L1/L2 release_at_rest 0.26) from runs/s12/vision flash_v0*/flash_v0r* (+ .score.json) and cstate_v0/cstate_v0r;
writes docs/media/s12_vision_release_floor.png."""
import json
import numpy as np, matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
R = "runs/s12/vision/"
def score(f):
    return {k: v["median_connected"] for k, v in json.load(open(R + f + ".score.json")).items()}
s0, s1 = score("flash_v0_i1"), score("flash_v0r_i1")
c0, c1 = json.load(open(R + "cstate_v0.json")), json.load(open(R + "cstate_v0r.json"))
fig, ax = plt.subplots(2, 3, figsize=(15, 8.5))
a = ax[0, 0]
names = ["L1:on_min", "L2:on_min", "Mi1:on_max", "Tm3:on_max", "Tm1:off_max", "Tm2:off_max"]
x = np.arange(len(names))
a.bar(x - 0.2, [abs(s0[n]) for n in names], 0.4, label="v0 arm (r0 0.5)")
a.bar(x + 0.2, [abs(s1[n]) for n in names], 0.4, label="v0r (L1/L2 r0 0.26)")
a.plot(x, [45, 45, 20, 15, 17.5, 17.5], "r_", ms=20, mew=2, label="recorded")
for xi, (lo, hi) in ((2, (4, 6.5)), (3, (7, 11))):
    a.plot([xi + 0.2] * 2, [lo, hi], c="k", lw=3, alpha=0.5, label="pre-registered range" if xi == 2 else None)
a.set_xticks(x); a.set_xticklabels(["|L1| ON", "|L2| ON", "Mi1 ON", "Tm3 ON", "Tm1 OFF", "Tm2 OFF"], fontsize=8)
a.set_ylabel("mV (connected median)"); a.set_title("Full flash amplitudes"); a.legend(fontsize=7)
a = ax[0, 1]
tys = ["L1", "L2", "Mi1", "Tm3", "Tm1"]
x = np.arange(len(tys))
for j, (c, lab) in enumerate(((c0, "v0"), (c1, "v0r"))):
    a.plot(x + (j - 0.5) * 0.25, [c["dark"][t]["v"] for t in tys], "o", c=f"C{j}", label=f"{lab} dark")
    a.plot(x + (j - 0.5) * 0.25, [c["light"][t]["v"] for t in tys], "v", c=f"C{j}", label=f"{lab} light (300 ms)")
a.set_xticks(x); a.set_xticklabels(tys); a.set_ylabel("mV (connected median)")
a.set_title("Conductance probe: dark and steady-light potentials"); a.legend(fontsize=7)
a = ax[0, 2]
for j, (c, lab) in enumerate(((c0, "v0"), (c1, "v0r"))):
    rel = [c[ph]["L1"]["release"] for ph in ("dark", "light")]
    a.bar(np.arange(2) + (j - 0.5) * 0.35, rel, 0.35, label=lab)
a.set_xticks([0, 1]); a.set_xticklabels(["dark", "light"]); a.set_ylabel("L1 release x span gain (r x g_k)")
a.set_title("L1 graded release"); a.legend(fontsize=8)
for j, ty in enumerate(("L1", "Mi1", "Tm3")):
    a = ax[1, j]
    for f, lab, st in (("flash_v0_i1", "v0", "-"), ("flash_v0r_i1", "v0r", "-")):
        d = json.load(open(R + f + ".json")); t = np.asarray(d["t_ms"]); x_ = np.asarray(d["trace"][ty])
        a.plot(t, x_ - x_[(t >= 100) & (t < 300)].mean(), st, label=lab)
    a.axvspan(300, 1300, color="y", alpha=0.1, label="flash 300-1300")
    a.set_title(f"{ty} type mean (all cells, diluted by unconnected cells)"); a.set_xlabel("ms"); a.set_ylabel("mV from dark")
    a.legend(fontsize=7)
fig.suptitle("s12 vision: LMC output release floor (L1/L2 release_at_rest 0.26, inferred) on the v0 arm; full flash i 1")
fig.tight_layout(); fig.savefig("docs/media/s12_vision_release_floor.png", dpi=90)
print("ok")
