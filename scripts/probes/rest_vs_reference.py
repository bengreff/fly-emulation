"""S0 (s13, 13 Oct): one profile run's resting rates by group against docs/research/s13_resting_rates_reference.csv.

Input: a smoke_live.py --rates-out npz. Single published numbers are widened to a factor of 2 either side
(guessed band, stated in range_used); LH local/output cannot be mapped to male-cns types yet (n/a).

    uv run python scripts/probes/rest_vs_reference.py runs/s13/smoke/m10f0_s12_rates.npz runs/s13/rest/m10f0_s12_vs_reference.csv
"""
import sys, numpy as np, pandas as pd
sys.path.insert(0, "src")
from flyemu.connectome import load_tables
nrn, _ = load_tables()
z = np.load(sys.argv[1])
hz = pd.Series(z["hz"], index=z["body_id"])
n = nrn.set_index("bodyId").reindex(hz.index)
t = n["type"].fillna("").astype(str); c = n["class"].fillna("").astype(str); sc = n["superclass"].fillna("").astype(str)
cc = pd.read_csv("data/model/classes.csv", keep_default_na=False)
circ = t.map(dict(zip(cc.type, cc.circuit_class))).fillna("")
def grp(mask):
    h = hz[mask.to_numpy()]
    return len(h), float(h.mean()) if len(h) else np.nan, float(h.median()) if len(h) else np.nan, float((h > 0).mean()) if len(h) else np.nan
G = {
 "ORN (all ORN_ types)": t.str.startswith("ORN_"),
 "uPN (circuit AL_PN)": circ == "AL_PN",
 "AL LN (circuit AL_LN)": circ == "AL_LN",
 "KC": circ == "KC",
 "MBON-a3 (MBON14)": t == "MBON14",
 "MBON (all)": circ == "MBON",
 "LH local (not mapped)": c == "__none__",
 "LH output (not mapped)": c == "__none__",
 "P-EN (PEN_a, PEN_b)": t.str.startswith("PEN_"),
 "DN1a": t == "DN1a",
 "DN (circuit DN)": circ == "DN",
 "labellar GRN (sensory_gustatory)": circ == "sensory_gustatory",
 "R1-6": t.str.match(r"^R1-6$|^R[1-6]$"),
}
ref = {  # value, low, high from s13_resting_rates_reference.csv (row label)
 "ORN (all ORN_ types)": ("8 (1-30); pb1A 12.8 (10.2-15.4)", 1, 30),
 "uPN (circuit AL_PN)": ("1-5; 4.6 (0.4-8.8); 1.4", 0.4, 8.8),
 "AL LN (circuit AL_LN)": ("4.6 (1.8-7.4)", 1.8, 7.4),
 "KC": ("0.1 (up to 0.5); 5-6% responsive", 0.0, 0.5),
 "MBON-a3 (MBON14)": ("12.1 (x2 band guessed)", 6, 24),
 "MBON (all)": ("only MBON-a3 measured: 12.1", np.nan, np.nan),
 "LH local (not mapped)": ("1", 0.5, 2),
 "LH output (not mapped)": ("0.1", 0.0, 0.5),
 "P-EN (PEN_a, PEN_b)": ("3.9 (2.4-5.4)", 2.4, 5.4),
 "DN1a": ("12 (ZT0-4), 6 (ZT20-24)", 6, 12),
 "DN (circuit DN)": ("few active at rest (qualitative)", np.nan, np.nan),
 "labellar GRN (sensory_gustatory)": ("0-3; bitter 0.7-1.8", 0.0, 3.0),
 "R1-6": ("2.5 (2-3) dark bumps, events/s not spikes", np.nan, np.nan),
}
rows = []
for k, m in G.items():
    nn, mean, med, fa = grp(m)
    lab, lo, hi = ref[k]
    verdict = "no number" if np.isnan(lo) else ("n/a" if nn == 0 else ("in" if lo <= mean <= hi else ("LOW" if mean < lo else "HIGH")))
    rows.append(dict(group=k, cells=nn, model_mean_hz=round(mean, 2), model_median_hz=round(med, 2), frac_active=round(fa, 3),
                     published=lab, range_used=f"{lo}-{hi}", verdict=verdict))
df = pd.DataFrame(rows); print(df.to_string(index=False)); df.to_csv(sys.argv[2], index=False)
