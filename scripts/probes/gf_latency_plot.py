"""Figure for scripts/probes/gf_latency.py: model latency to muscle against the Augustin 2017 bands.

    .venv/bin/python scripts/probes/gf_latency_plot.py runs/s13/fly2/gf_latency_m10f.json
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

src = Path(sys.argv[1])
r = json.loads(src.read_text())
muscles = {"TTM": ["TTMn"], "DLM": ["DLMn a, b", "DLMn c-f"]}
fig, axes = plt.subplots(1, 2, figsize=(9, 3.6), sharey=True)
for ax, (m, mn_types) in zip(axes, muscles.items()):
    ref, (lo, hi) = r["reference"][m], r["band_ms"][m]
    ax.axhspan(lo, hi, color="0.88", label="WT band (young - 2 SEM to old)")
    for age, ls in (("young", "-"), ("mid", "--"), ("old", ":")):
        ax.axhline(ref[age], color="0.4", ls=ls, lw=1, label=f"WT {age} mean")
    x = 0
    ticks = []
    for arm, colour in (("gaps_off", "tab:blue"), ("gaps_on", "tab:red")):
        for ty in mn_types:
            v = r["arms"][arm]["types"][ty]
            if v["muscle_ms_median"] is None:
                ax.text(x, lo - 0.25, "no spike\nin 10 ms", ha="center", va="top", fontsize=7, color=colour)
            else:
                ax.plot(x, v["muscle_ms_median"], "o", color=colour, ms=7)
            ax.text(x, 0.08, f"follow {v['follow_fraction']:.2f}", ha="center", fontsize=7, color=colour)
            ticks.append((x, f"{arm.replace('_', ' ')}\n{ty}"))
            x += 1
    ax.set_xticks([t[0] for t in ticks], [t[1] for t in ticks], fontsize=7)
    ax.set_xlim(-0.6, x - 0.4)
    ax.set_ylim(0, 2.4)
    ax.set_title(f"{m}: GF spike to muscle (model median) vs Augustin 2017 WT")
    ax.title.set_fontsize(9)
axes[0].set_ylabel("latency to muscle (ms)")
axes[1].legend(fontsize=6, loc="upper right")
fig.suptitle(f"{r['profile']}, isolated CNS, {r['arms']['gaps_on']['trials']} GF kicks per arm; "
             "muscle = MN spike - GF spike + MN conduction + 0.5 ms NMJ", fontsize=8)
fig.tight_layout()
out = src.with_suffix(".png")
fig.savefig(out, dpi=130)
print("wrote", out)
