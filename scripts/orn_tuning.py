"""Join connectome ORN types to measured DoOR 2.0 response profiles.

Writes data/derived/orn_tuning_door.csv (long: orn_type, door_unit, odour
InChIKey, response). The response is DoOR's consensus, normalised 0-1 per
unit: **measured** (relative), not spikes/s. The ORN_<glomerulus> ->
DoOR unit join uses DoOR's receptor-to-glomerulus mapping (measured); where
one glomerulus has several units, all are kept and flagged.
"""
from pathlib import Path
import pandas as pd

REPO = Path(__file__).resolve().parents[1]
RAW = REPO / "data" / "raw" / "door"

m = pd.read_csv(RAW / "door_mappings.csv", sep=";")
resp = pd.read_csv(RAW / "door_response_matrix.csv", sep=";", index_col=0)
n = pd.read_parquet(REPO / "data" / "cache" / "male_cns_neurons.parquet")
orn = n[n.type.fillna("").str.startswith("ORN_")].type.value_counts()

rows, cover = [], []
for t, cnt in orn.items():
    glom = t[4:]
    def names(g):
        # DoOR writes e.g. "DL2d/v": expand the suffix shorthand to DL2d, DL2v
        out = []
        for part in [x for x in pd.Series([g]).str.split(r"[, ]").iloc[0] if x]:
            head, *alts = part.split("/")
            out.append(head)
            out += [head.rstrip("dvlmp") + a if len(a) <= 2 else a for a in alts]
        return out
    units = m[m.glomerulus.fillna("").map(lambda g: glom in names(g))]
    # exact matches first; DoOR lists e.g. "DL2d/v"
    units = units[units.receptor.isin(resp.columns)]
    cols = [u for u in units.receptor if resp[u].notna().any()]
    cover.append(dict(orn_type=t, cells=int(cnt), door_units=";".join(cols),
                      n_units=len(cols),
                      n_odours=int(resp[cols].notna().any(axis=1).sum()) if cols else 0))
    for u in cols:
        s = resp[u].dropna()
        rows.extend(dict(orn_type=t, door_unit=u, odour_inchikey=k, response=float(v),
                         basis="measured (DoOR consensus, normalised 0-1)")
                    for k, v in s.items() if k != "SFR")
pd.DataFrame(rows).to_csv(REPO / "data" / "derived" / "orn_tuning_door.csv", index=False)
cov = pd.DataFrame(cover).sort_values("n_odours")
cov.to_csv(REPO / "data" / "derived" / "orn_tuning_coverage.csv", index=False)
print(f"{len(cov)} ORN types; with a DoOR profile: {(cov.n_units > 0).sum()}; "
      f"multi-unit: {(cov.n_units > 1).sum()}; response entries: {len(rows):,}")
print("no profile:", cov[cov.n_units == 0].orn_type.tolist())
