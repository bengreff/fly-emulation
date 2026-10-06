"""Figure: first-synapse gain test (s12 vision, DECISIONS 6 Oct 03:42). Reads runs/s12/vision flash_* runs and their .score.json; writes docs/media/s12_vision_first_synapse.png."""
import json, sys
import numpy as np, matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
R = "runs/s12/vision/"
dim = {1: "flash_dim_i0.01", 10: "flash_kR10_i0.01", 30: "flash_kR30_i0.01"}
full = {1: "flash_G_k1", 30: "flash_kR30_i1"}
def score(f):
    s = json.load(open(R + f + ".score.json"))
    return {k.split(":")[0] + (":" + k.split(":")[1] if k.startswith(("Tm1", "Tm2")) else ""): v["median_connected"] for k, v in s.items()}
fig, ax = plt.subplots(2, 3, figsize=(15, 8.5))
ks = sorted(dim)
sc = {k: score(dim[k]) for k in ks}
R0 = [sc[k]["R1-R6"] for k in ks]
g = [-sc[k]["L1"] / sc[k]["R1-R6"] for k in ks]
pred_k = np.linspace(1, 40, 200); pred = 1.24 * (pred_k / (1.16 + 0.04 * pred_k) ** 2) / (1 / 1.2 ** 2)
a = ax[0, 0]
a.plot(ks, g, "o-", label="model, dim flash i 0.01 (connected median)")
a.plot(pred_k, pred, "--", c="gray", label="pre-registered small-signal arithmetic")
a.axhline(13, c="r", ls=":", label="Juusola 1995 ~13 (Calliphora, ~160 photons/s)")
a.axhspan(1.5, 4.5, color="r", alpha=0.08, label="Juusola 1995 1.5-4.5 (500,000 photons/s)")
a.set_xscale("log"); a.set_xlabel("class:photoreceptor|release_scale k"); a.set_ylabel("R1-R6 -> L1 gain (|dV_L1| / dV_R)")
a.set_title("First-synapse small-signal gain saturates near 6"); a.legend(fontsize=7)
a = ax[0, 1]
for ty, c in (("Mi1", "C0"), ("Tm3", "C1")):
    a.plot(ks, [sc[k][ty] for k in ks], "o-", c=c, label=f"{ty} ON (dim)")
a.plot(ks, [-sc[k]["L1"] for k in ks], "s--", c="k", label="|L1| ON (dim)")
a.set_xscale("log"); a.set_xlabel("k"); a.set_ylabel("mV (connected median)"); a.legend(fontsize=8)
a.set_title("Dim flash: L1 grows, Mi1 vanishes at k 30")
a = ax[0, 2]
names = ["L1", "L2", "Mi1", "Tm3", "Tm1:off_max", "Tm2:off_max"]
s1, s30 = score(full[1]), score(full[30])
x = np.arange(len(names))
a.bar(x - 0.2, [abs(s1[n]) for n in names], 0.4, label="k 1")
a.bar(x + 0.2, [abs(s30[n]) for n in names], 0.4, label="k 30")
rec = [45, 45, 20, 15, 17.5, 17.5]
a.plot(x, rec, "r_", ms=20, mew=2, label="recorded")
a.set_xticks(x); a.set_xticklabels(["|L1| ON", "|L2| ON", "Mi1 ON", "Tm3 ON", "Tm1 OFF", "Tm2 OFF"], fontsize=8)
a.set_ylabel("mV (connected median)"); a.set_title("Full flash: k 30 vs k 1"); a.legend(fontsize=8)
for j, (ty, lim) in enumerate((("L1", None), ("Mi1", None), ("Tm3", None))):
    a = ax[1, j]
    for f, lab, st in ((full[1], "full k 1", "-"), (full[30], "full k 30", "-"), (dim[1], "dim k 1 (x20)", ":"), (dim[30], "dim k 30 (x20)", ":")):
        d = json.load(open(R + f + ".json")); t = np.asarray(d["t_ms"]); x_ = np.asarray(d["trace"][ty])
        base = x_[(t >= 100) & (t < 300)].mean(); sc_ = 20 if "dim" in lab else 1
        a.plot(t, (x_ - base) * sc_, st, label=lab)
    a.axvspan(300, 800, color="y", alpha=0.15, label="dim flash 300-800"); a.axvspan(300, 1300, color="y", alpha=0.07, label="full flash 300-1300")
    a.set_title(f"{ty} type mean (all cells, diluted ~0.45 connected)"); a.set_xlabel("ms"); a.set_ylabel("mV from dark")
    a.legend(fontsize=7)
fig.suptitle("s12 vision: first-synapse gain test, class:photoreceptor|release_scale (R1-R8), gain-block base set; dim flash 500 ms (300-800), full 1 s (300-1300)")
fig.tight_layout(); fig.savefig("docs/media/s12_vision_first_synapse.png", dpi=90)
print("ok")
