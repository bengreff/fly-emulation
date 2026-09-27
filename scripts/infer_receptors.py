"""Receptor complement per cell type: measured where profiled, inferred elsewhere.

Fills synapse blanks (glutamate sign per target, GABA-B share, NMDA, monoamine
receptors) from transcriptomes, and tests whether the connectome alone can
predict them for the ~14k types nobody has profiled.

Data: Davis, Nern et al. 2020 eLife 9:e50901, GEO GSE116969, dataTable7b
(per-cell-type expression probabilities from a bimodal on/off model of TAPIN-seq
nuclear RNA; 77 cell populations). A probability is "expressed" at >= 0.5.

Steps
  1. crosswalk Davis cell names -> male-cns types (declared, with basis);
  2. per mapped type, receptor calls  -> data/derived/receptor_calls_davis2020.csv;
  3. inference test: for each variable receptor gene, predict the on/off call of a
     held-out type from connectome features only (input-transmitter composition,
     own transmitter, superclass, log input count), leave-one-type-out, against the
     majority-class baseline -> data/derived/receptor_inference_cv.csv.
     A gene's connectome predictions may be used (labelled inferred) only where
     the CV beats the baseline by a declared margin (balanced accuracy >= 0.70 and
     >= baseline + 0.15).

    uv run python scripts/infer_receptors.py
"""
from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[1]
RAW = REPO / "data/raw/davis2020/GSE116969_dataTable7b.genes_x_cells_p_expression.modeled_genes.txt.gz"
TPM = REPO / "data/raw/davis2020/GSE116969_dataTable7a.genes_x_cells_TPM.modeled_genes.txt.gz"
OUT = REPO / "data/derived"

# Davis cell -> male-cns types, basis, note. Unlisted Davis cells (driver pools,
# glia, muscle, combos, unresolved PFN subtypes) are not mapped.
WOLFF = "Wolff & Rubin 2018 name in Davis 2020 Supp file 1A"
CROSSWALK = {
    **{c: ([c], "derived", "identical type name (optic lobe)") for c in (
        "C2 C3 Dm1 Dm10 Dm11 Dm12 Dm4 Dm9 L1 L2 L3 L4 L5 Lai Lawf1 Lawf2 LC10a LC10b "
        "LC16 LC4 LC6 LLPC1 LPC1 LPLC1 LPLC2 Mi1 Mi15 Mi4 Mi9 Pm3 Pm4 T1 Tm1 Tm2 Tm20 "
        "Tm29 Tm3 Tm4 Tm9 TmY3 TmY5a").split()},
    "Dm3": (["Dm3a", "Dm3b", "Dm3c"], "inferred", "Dm3 later split into 3 subtypes"),
    "Dm8": (["Dm8a", "Dm8b"], "inferred", "Dm8 later split into 2 subtypes"),
    "T4": (["T4a", "T4b", "T4c", "T4d"], "derived", "all T4 subtypes profiled together"),
    "T5": (["T5a", "T5b", "T5c", "T5d"], "derived", "all T5 subtypes profiled together"),
    "R1-6": (["R1-R6"], "derived", "outer photoreceptors"),
    "R8_Rh5": (["R8p"], "inferred", "Rh5 = pale R8"),
    "R8_Rh6": (["R8y"], "inferred", "Rh6 = yellow R8"),
    "KC_ab_c": (["KCab-c"], "derived", "MB594B, Aso 2014"),
    "KC_ab_p": (["KCab-p"], "derived", "MB371B, Aso 2014"),
    "KC_ab_s": (["KCab-s"], "derived", "MB185B, Aso 2014"),
    "KC_gd": (["KCg-d"], "derived", "MB419B/MB607B, Aso 2014"),
    "PAM_1": (["PAM02"], "inferred", "PAM-b'2a (MB109B); hemibrain PAM numbering"),
    "PAM_3": (["PAM04", "PAM10"], "inferred", "PAM-b1 + PAM-b2 pooled (MB213B)"),
    "PAM_4": (["PAM07", "PAM08"], "inferred", "PAM-g4 + g4<g1g2 pooled (MB312B)"),
    "PB_1": (["Delta7"], "inferred", f"PB18.s-GxD7Gy.b (SS00116); {WOLFF}"),
    "PB_2": (["EPG"], "inferred", f"PBG1-8.b-EBw.s-D/Vgall.b (SS00090); {WOLFF}"),
    # PB_3 = PEN_a by name, but Davis report optic-lobe cells (incl. Mi1) outnumbering
    # the PB cells in that driver: recorded, never used to fill.
    "PB_3": (["PEN_a(PEN1)"], "contaminated", f"PBG2-9.s-EBt.b-NO1.b (SS02268); {WOLFF}; OL cells outnumber PB cells"),
}

# Receptor genes and their model interpretation.
GENES = {
    "GluClalpha": "glutamate-gated chloride: inhibitory glutamate",
    "GluRIA": "AMPA-like iGluR: excitatory glutamate", "GluRIB": "AMPA-like iGluR",
    "Nmdar1": "NMDA obligatory subunit: slow, voltage-dependent excitation",
    "Nmdar2": "NMDA subunit", "mGluR": "metabotropic glutamate",
    "Rdl": "GABA-A (fast inhibition)", "Lcch3": "GABA-A-like", "Grd": "GABA-gated (cation?)",
    "GABA-B-R1": "GABA-B (slow inhibition)", "GABA-B-R2": "GABA-B", "GABA-B-R3": "GABA-B",
    "nAChRalpha1": "nicotinic", "nAChRalpha5": "nicotinic", "nAChRalpha6": "nicotinic",
    "nAChRalpha7": "nicotinic", "mAChR-A": "muscarinic (Gq)", "mAChR-B": "muscarinic (Gi)",
    "Dop1R1": "D1-like, Gs", "Dop1R2": "D1-like, Gs/Gq", "Dop2R": "D2-like, Gi", "DopEcR": "DA/ecdysone",
    "Oamb": "OA alpha1-like, Gq", "Octalpha2R": "OA alpha2, Gi", "Octbeta1R": "OA beta, Gs",
    "Octbeta2R": "OA beta, Gs", "Octbeta3R": "OA beta, Gs",
    "5-HT1A": "Gi", "5-HT1B": "Gi", "5-HT2A": "Gq", "5-HT2B": "Gq", "5-HT7": "Gs",
    "HisCl1": "histamine-gated Cl", "ort": "histamine-gated Cl",
}
NTS = ["acetylcholine", "gaba", "glutamate", "dopamine", "serotonin", "octopamine", "histamine", "unclear"]


def crosswalk() -> pd.DataFrame:
    return pd.DataFrame([{"davis_cell": d, "male_cns_type": t, "basis": b, "note": note}
                         for d, (ts, b, note) in CROSSWALK.items() for t in ts])


def features(types: list[str]) -> pd.DataFrame:
    """Connectome features per type: input-transmitter shares, own NT, superclass, log inputs."""
    n = pd.read_parquet(REPO / "data/cache/male_cns_neurons.parquet",
                        columns=["bodyId", "type", "superclass", "predictedNt"])
    n = n[n.type.notna()]
    want = n[n.type.isin(types)]
    e = pd.read_parquet(REPO / "data/cache/male_cns_edges.parquet",
                        filters=[("post", "in", want.bodyId.tolist())])
    e = e[e.weight >= 5]
    nt = n.set_index("bodyId").predictedNt
    e["nt"] = e.pre.map(nt).fillna("unclear")
    e["type"] = e.post.map(want.set_index("bodyId").type)
    comp = e.pivot_table(index="type", columns="nt", values="weight", aggfunc="sum", fill_value=0)
    for c in NTS:
        if c not in comp:
            comp[c] = 0
    tot = comp[NTS].sum(axis=1)
    f = comp[NTS].div(tot, axis=0).add_prefix("in_")
    f["log_inputs_per_cell"] = np.log10(tot / want.groupby("type").size().reindex(f.index))
    own = want.groupby("type").predictedNt.agg(lambda s: s.value_counts().index[0])
    for c in ("acetylcholine", "gaba", "glutamate", "dopamine", "histamine"):
        f[f"own_{c}"] = (own.reindex(f.index) == c).astype(float)
    sc = want.groupby("type").superclass.agg(lambda s: s.value_counts().index[0]).reindex(f.index)
    for c in ("ol_intrinsic", "visual_projection", "cb_intrinsic", "ol_sensory"):
        f[f"sc_{c}"] = (sc == c).astype(float)
    return f


def logreg_fit(X, y, lam=1.0, iters=50):
    w = np.zeros(X.shape[1])
    for _ in range(iters):
        p = 1 / (1 + np.exp(-X @ w))
        g = X.T @ (p - y) + lam * w
        H = X.T @ (X * (p * (1 - p))[:, None]) + lam * np.eye(len(w))
        w -= np.linalg.solve(H, g)
    return w


def balanced_acc(y, yhat):
    pos, neg = y == 1, y == 0
    parts = [(yhat[pos] == 1).mean() if pos.any() else np.nan, (yhat[neg] == 0).mean() if neg.any() else np.nan]
    return float(np.nanmean(parts))


def main():
    p = pd.read_csv(RAW, sep="\t", index_col=0)
    tpm = pd.read_csv(TPM, sep="\t", index_col=0)
    cw = crosswalk()
    cw.to_csv(OUT / "davis2020_crosswalk.csv", index=False)
    genes = [g for g in GENES if g in p.index]
    rows = []
    for r in cw.itertuples():
        for g in genes:
            rows.append({"male_cns_type": r.male_cns_type, "davis_cell": r.davis_cell, "gene": g,
                         "p_expressed": round(float(p.at[g, r.davis_cell]), 3),
                         "tpm": round(float(tpm.at[g, r.davis_cell]), 1),
                         "call": int(p.at[g, r.davis_cell] >= 0.5),
                         "crosswalk_basis": r.basis, "role": GENES[g]})
    calls = pd.DataFrame(rows)
    calls.to_csv(OUT / "receptor_calls_davis2020.csv", index=False)
    print(f"receptor calls: {calls.male_cns_type.nunique()} male-cns types x {len(genes)} genes")

    # --- glutamate sign per postsynaptic type from GluCl vs iGluR ------------------
    # Rule (session 8, v2): GluClalpha expressed and AMPA-like iGluR (GluRIA+GluRIB) TPM
    # < 0.1 x GluClalpha TPM -> -1 (GluCl-dominated; agrees with the transmitter default,
    # live, no behaviour change). GluClalpha not expressed and iGluR expressed -> +1.
    # Otherwise (mixed or neither) no row. The 0.1 ratio is a declared threshold (guessed).
    # Cross-check: Turner-Evans et al. 2020 (GSE155329) bulk RNA-seq agrees for Delta7, EPG,
    # and adds PEN_b and PEG (GluCl-dominated), below.
    w = calls[calls.crosswalk_basis != "contaminated"].pivot_table(
        index="male_cns_type", columns="gene", values="call", aggfunc="first")
    tp = calls[calls.crosswalk_basis != "contaminated"].pivot_table(
        index="male_cns_type", columns="gene", values="tpm", aggfunc="first")
    ratio = (tp.GluRIA + tp.GluRIB) / tp.GluClalpha.clip(lower=1e-9)
    igl = (w.GluRIA == 1) | (w.GluRIB == 1)
    src = "Davis & Nern et al. 2020 eLife 9:e50901, GEO GSE116969 dataTable7a/7b"
    rows_live, rows_cand = [], []
    for t in w.index:
        if w.at[t, "GluClalpha"] == 1 and ratio[t] < 0.1:
            rows_live.append((t, -1.0, src, f"GluCl-dominated (iGluR/GluClalpha TPM ratio {ratio[t]:.3f} "
                              "< 0.1): glutamatergic input inhibitory; mRNA, not synaptic localisation"))
        elif w.at[t, "GluClalpha"] == 0 and igl[t]:
            rows_cand.append((t, 1.0, src, "iGluR (GluRIA/GluRIB) expressed, GluClalpha not: glutamatergic "
                              "input excitatory; mRNA presence, not synaptic localisation"))
    te = "Turner-Evans et al. 2020 Neuron, GEO GSE155329 bulk/low-cell RNA-seq (data/derived/turnerevans2020_bulk_receptors.csv)"
    for t, why in (("PEN_b(PEN2)", "low-cell median CPM GluClalpha 558 vs GluRIA+B 74 (ratio 0.13; bulk replicate 2 ratio 0.02)"),
                   ("PEG", "bulk TPM GluClalpha 47-79 vs GluRIA+B 3-4 (ratio ~0.05)")):
        rows_live.append((t, -1.0, te, f"GluCl-dominated: {why}; mRNA, not synaptic localisation"))
    for rows, path in ((rows_live, OUT / "glutamate_sign_transcript_live_rows.csv"),
                       (rows_cand, REPO / "data/params/candidates_s8_glu_igluR.csv")):
        pd.DataFrame([{"type": t, "param": "glutamate_receptor_sign", "value": v, "units": "sign",
                       "basis": "inferred", "source": sr, "justification": j} for t, v, sr, j in rows]
                     ).to_csv(path, index=False)
    print(f"glutamate sign: {len(rows_live)} types GluCl-dominated (-1), {len(rows_cand)} iGluR-only (+1)")

    # --- inference test: one row per Davis cell (types sharing a cell are pooled) ----
    use = cw[cw.basis != "contaminated"]
    first = use.groupby("davis_cell").male_cns_type.apply(list)
    F = features(sorted(use.male_cns_type))
    Xc = pd.DataFrame({d: F.reindex(ts).mean() for d, ts in first.items()}).T.dropna()
    cells = Xc.index.tolist()
    X = Xc.to_numpy()
    X = (X - X.mean(0)) / (X.std(0) + 1e-9)
    X = np.hstack([X, np.ones((len(X), 1))])
    central = np.array([c.startswith(("KC", "PAM", "PB")) for c in cells])
    out = []
    for g in genes:
        y = (p.loc[g, cells].to_numpy() >= 0.5).astype(float)
        if y.min() == y.max() or min(y.sum(), (1 - y).sum()) < 3:
            out.append({"gene": g, "n_types": len(y), "n_on": int(y.sum()), "variable": False})
            continue
        pred = np.zeros_like(y)
        for i in range(len(y)):
            m = np.arange(len(y)) != i
            w = logreg_fit(X[m], y[m])
            pred[i] = float(X[i] @ w > 0)
        base = np.full_like(y, float(y.mean() >= 0.5))
        ba, bb = balanced_acc(y, pred), balanced_acc(y, base)
        out.append({"gene": g, "n_types": len(y), "n_on": int(y.sum()), "variable": True,
                    "loo_balanced_acc": round(ba, 3), "baseline_balanced_acc": round(bb, 3),
                    "central_correct": f"{int((pred[central] == y[central]).sum())}/{int(central.sum())}",
                    "usable": bool(ba >= 0.70 and ba >= bb + 0.15)})
    cv = pd.DataFrame(out)
    cv.to_csv(OUT / "receptor_inference_cv.csv", index=False)
    print(f"training types (Davis cells): {len(cells)}, of which central brain: {int(central.sum())}")
    print(cv.to_string(index=False))


if __name__ == "__main__":
    main()
