# BRAIN_PORT section 9: the pre-registered readouts of s9_ctrl and s9_roberts (20 s closed loops in /tmp/mine_c1/s9),
# written to data/worm/brain_runs/s9_signs/ with the figure s9.png. Section 8's readouts come from c1_readouts.
import sys, json
import numpy as np
import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
sys.path.insert(0, "/Users/ben/fly-emulation/scripts/worm/port")
from c1_readouts import readouts

IN, OUT = "/tmp/mine_c1/s9/", "/Users/ben/fly-emulation/data/worm/brain_runs/s9_signs/"
RUNS = [("s9_ctrl", "s9_ctrl: signs before (AVA<->AVB excitatory)"), ("s9_roberts", "s9_roberts: Roberts 2016 signs")]
BT = [f"VB{i:02d}" for i in range(1, 12)] + [f"DB{i:02d}" for i in range(1, 8)]


def load(k):
    m = json.load(open(IN + k + ".json")); nf = m["n_frames"]; cells = m["cells"]
    V = np.fromfile(IN + k + ".neural.f32", np.float32).reshape(-1, len(cells))
    A = np.fromfile(IN + k + ".act.f32", np.float32).reshape(nf, -1)
    X = np.fromfile(IN + k + ".frames.f32", np.float32).reshape(nf, -1, 3)
    return m, cells, V, A, X


def s9(k):
    r = readouts(IN + k, "receptor_sign=on,defecation=off")
    m, cells, V, A, X = load(k)
    ix = {c: i for i, c in enumerate(cells)}
    t = np.linspace(0, m["seconds"], len(V)); w = t >= 1.0
    ava = V[:, [ix["AVAL"], ix["AVAR"]]].mean(1); avb = V[:, [ix["AVBL"], ix["AVBR"]]].mean(1)
    sd = V[w][:, [ix[c] for c in BT]].std(0)
    r.update(co_active_fraction=float(((ava[w] > -20) & (avb[w] > -20)).mean()),
             ava_mean_mV=float(ava[w].mean()), avb_mean_mV=float(avb[w].mean()),
             ava_avb_r=float(np.corrcoef(ava[w], avb[w])[0, 1]),
             btype_sd_median_mV=float(np.median(sd)), btype_sd_max_mV=float(sd.max()),
             btype_mean_mV=float(V[w][:, [ix[c] for c in BT]].mean()))
    json.dump(r, open(OUT + k + ".s9.json", "w"), indent=1)
    return r


if __name__ == "__main__":
    res = {k: s9(k) for k, _ in RUNS}
    for k, v in res.items():
        print(k, json.dumps({x: v[x] for x in ("co_active_fraction", "ava_mean_mV", "avb_mean_mV", "ava_avb_r",
              "neurons_above_m20_last", "muscles_above_m20_last", "btype_sd_median_mV", "btype_sd_max_mV",
              "btype_mean_mV", "act_max", "centroid_net_body_lengths", "centroid_path_body_lengths",
              "midbody_dv_zero_crossings", "midbody_dv_p2p", "rhythm_candidate")}))
    fig, ax = plt.subplots(4, 2, figsize=(13, 12), sharex="row")
    for j, (k, lab) in enumerate(RUNS):
        m, cells, V, A, X = load(k); ix = {c: i for i, c in enumerate(cells)}; nf = m["n_frames"]
        t = np.linspace(0, m["seconds"], len(V)); ta = np.linspace(0, m["seconds"], nf)
        for c, col in (("AVAL", "C3"), ("AVAR", "C1"), ("AVBL", "C0"), ("AVBR", "C9")):
            ax[0, j].plot(t, V[:, ix[c]], color=col, lw=1, label=c)
        ax[0, j].axhline(-20, color="0.6", ls=":"); ax[0, j].set_ylim(-80, 20); ax[0, j].set_ylabel("soma V (mV)")
        ax[0, j].set_title(f"{lab}\nco-active {res[k]['co_active_fraction']:.2f}, r = {res[k]['ava_avb_r']:.2f}", fontsize=9)
        ax[0, j].legend(fontsize=7, ncol=4, loc="lower right")
        for c in BT:
            ax[1, j].plot(t, V[:, ix[c]], lw=0.7, color="C0" if c.startswith("VB") else "C3")
        ax[1, j].set_ylim(-80, 20); ax[1, j].set_ylabel("B-type soma V (mV)")
        ax[1, j].set_title(f"VB01-11 blue, DB01-07 red; SD median {res[k]['btype_sd_median_mV']:.2f} mV, "
                           f"max {res[k]['btype_sd_max_mV']:.2f}", fontsize=9)
        g = np.repeat(m["muscles"], 24); row = np.tile(np.arange(1, 25), 4); mid = (row >= 9) & (row <= 16)
        dv = A[:, mid & np.isin(g, ["MDR", "MDL"])].mean(1) - A[:, mid & np.isin(g, ["MVR", "MVL"])].mean(1)
        ax[2, j].plot(ta, A[:, np.isin(g, ["MDR", "MDL"])].mean(1), label="dorsal mean")
        ax[2, j].plot(ta, A[:, np.isin(g, ["MVR", "MVL"])].mean(1), label="ventral mean")
        ax[2, j].plot(ta, dv, "k", lw=1, label="mid-body D-V"); ax[2, j].set_ylim(-0.6, 0.9); ax[2, j].set_ylabel("activation")
        ax[2, j].set_xlabel("time (s)"); ax[2, j].legend(fontsize=7, loc="upper left")
        ax[2, j].set_title(f"zero crossings {res[k]['midbody_dv_zero_crossings']}, peak-to-peak "
                           f"{res[k]['midbody_dv_p2p']:.3f}, rhythm rule {'PASS' if res[k]['rhythm_candidate'] else 'fails'}", fontsize=9)
        P = X.reshape(-1, 3); mu = P.mean(0); ev = np.linalg.svd((P - mu)[::50], full_matrices=False)[2][:2]
        for f, c in ((0, "0.75"), (nf // 4, "C2"), (nf // 2, "C1"), (nf - 1, "k")):
            Y = (X[f] - mu) @ ev.T; ax[3, j].plot(Y[:, 0], Y[:, 1], ".", ms=0.5, color=c)
        ax[3, j].set_aspect("equal"); ax[3, j].set_xticks([]); ax[3, j].set_yticks([])
        ax[3, j].set_title(f"body (best-fit plane): t = 0 grey, 5 s green, 10 s orange, 20 s black; centroid net "
                           f"{res[k]['centroid_net_body_lengths']:.2f} L", fontsize=8)
    fig.suptitle("BRAIN_PORT section 9: 20 s closed loop, defecation off, receptor_sign on. Only difference: 9 signs "
                 "(AVA<->AVB, ASH->AVB inhibitory, Roberts 2016)", fontsize=10)
    fig.tight_layout(rect=(0, 0, 1, 0.97)); fig.savefig(OUT + "s9.png", dpi=85)
