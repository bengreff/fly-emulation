"""Figure for the row 3 wave (wbody2, 9 Nov 2026): ring Ca of the isolated intestine, 600 s at dt 0.5 ms, at the
defaults and at the first set of intestine_speed_probe.py mode=joint that passes check_intestine's intact bars (P_ip3
300 um/s, outside its range and above the cytosolic diffusion bound; not adopted). Left: 600 s; right: one wave, with
each ring's half-amplitude crossing marked. -> runs/worm/wbody2/intestine_speed.png"""
import json
import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "src"))
from wormemu.mech import organs_intestine as I  # noqa: E402

joint = json.loads((ROOT / "runs/worm/wbody2/intestine_speed_probe_joint.json").read_text())
ok = [c for c in joint["confirmed_0p5ms"] if c["ok"]][0]
sets = [("defaults (P_ip3 2, P_ca 0.5 um/s): fail", {}),
        (f"P_ip3 {ok['values']['int_gap_p_ip3_um_s']:.0f}, P_ca {ok['values']['int_gap_p_ca_um_s']:.0f} um/s, a2 "
         f"{ok['values']['int_lr_a2_per_uM_s']:.3f}: passes (outside range; not adopted)", ok["values"])]
fig, axs = plt.subplots(2, 2, figsize=(14, 6.5), gridspec_kw=dict(width_ratios=[2.2, 1]))
for row, (name, v) in enumerate(sets):
    q = I.defaults()
    q.update(v)
    t, C, _, _ = I.run_isolated(q, 600.0, 0.5)
    R = np.stack([C[:, I.RING == r].mean(1) for r in range(1, 10)], 1)
    thr = R[:, 8].min() + 0.5 * (R[:, 8].max() - R[:, 8].min())
    up9 = t[np.flatnonzero((R[1:, 8] >= thr) & (R[:-1, 8] < thr)) + 1]
    t0 = up9[3] if len(up9) > 3 else up9[-1]
    ax, az = axs[row]
    for r in range(9):
        col = plt.cm.viridis(r / 8)
        ax.plot(t, R[:, r], lw=0.7, color=col, label=f"ring {r + 1}")
        w = (t >= t0 - 3) & (t < t0 + 25)
        az.plot(t[w] - t0, R[w, r], lw=0.9, color=col)
        u = t[np.flatnonzero((R[1:, r] >= thr) & (R[:-1, r] < thr)) + 1]
        u = u[(u >= t0 - 3) & (u < t0 + 25)]
        if len(u):
            az.plot(u[0] - t0, thr, "o", ms=3, color=col)
    L = q["int_ring_length_um"]
    ax.set_title(name, fontsize=9)
    ax.set_ylabel("ring mean Ca (uM)")
    az.axhline(thr, color="0.6", ls=":", lw=0.8)
    az.set_title(f"one wave from int9's crossing at {t0:.1f} s (ring length {L:.0f} um)", fontsize=9)
axs[0, 0].legend(ncol=9, fontsize=7, loc="upper right")
axs[1, 0].set_xlabel("time (s)")
axs[1, 1].set_xlabel("time after int9 crosses half amplitude (s); dots: each ring's crossing")
fig.tight_layout()
out = ROOT / "runs/worm/wbody2/intestine_speed.png"
fig.savefig(out, dpi=110)
print(out)
