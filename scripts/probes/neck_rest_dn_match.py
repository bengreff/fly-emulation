"""Match the rest-encoding DN positions of Aymanns, Chen & Ramdya 2022 to connectome types (inferred).

Aymanns et al. 2022 (eLife 11:e81527, Fig 2e) imaged the thoracic cervical connective in cross-section
and report that rest-encoding DNs lie "medially, close to the giant fibers, as well as in the lateral
extremities". Cell types were not identified. This script places every BANC descending neuron in the
BANC neck cross-section (Dataverse doi:10.7910/DVN/8TFGGB v8.1, neck_connective_y92500.tab, one point
per axon at the plane y = 92500) and lists the DN types inside each band, under two band widths.

Units: BANC voxels are 4 x 4 x 45 nm (x lateral, z dorsoventral; inferred: high z is dorsal because the
giant fibers, dorsomedial in the connective, sit at high z, and Kenyon cell somata also have high z).
Band definitions are guessed translations of the paper's words, so two widths are run for each.
Aymanns' driver "lacks expression in the subesophageal zone (SEZ)", so types with gnathal somata (DNg,
DNge, DNxl names; in male-cns these carry somaNeuromere LB/MX/MD/GNG) are marked excluded. A BANC type
counts as SEZ if its male-cns match name, or failing that its BANC name, has one of those prefixes.
Matches are inferred; nothing here sets a model drive.

    PYTHONPATH=src uv run python scripts/probes/neck_rest_dn_match.py
"""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[2]
NECK = REPO / "data/raw/banc/dataverse_v8.1/neck_connective_y92500.orig"
META = REPO / "data/raw/banc/banc_888_meta.feather"
OUT = REPO / "runs/s12/dnrest/neck_rest_match.json"
VOX = np.array([0.004, 0.045])          # um per voxel, x and z (BANC 4 x 4 x 45 nm)
MEDIAL_UM = (5.0, 8.0)                  # guessed: "close to the giant fibers" = within this of either GF centre
LATERAL_Q = (0.90, 0.80)                # guessed: "lateral extremities" = beyond this quantile of |x - midline|
SEZ_PREFIX = ("DNg", "DNxl")            # gnathal-soma DN names (DNge starts with DNg)


def is_sez(banc_type: str, malecns: list[str]) -> bool:
    names = [t.removeprefix("auto:") for t in malecns] or [banc_type]
    return all(t.startswith(SEZ_PREFIX) for t in names)


def main() -> None:
    x = pd.read_csv(NECK)
    m = pd.read_feather(META)
    ids: dict[int, int] = {}
    for c in ("root_id", "root_626", "root_850", "root_888", "root_890", "banc_888_id"):
        for i, v in zip(m.index, pd.to_numeric(m[c], errors="coerce")):
            if pd.notna(v):
                ids.setdefault(int(v), i)
    x["mi"] = x.pt_root_id.map(lambda r: ids.get(int(r)))
    n_unjoined = int(x.mi.isna().sum())
    x = x[x.mi.notna()].copy()
    x["mi"] = x.mi.astype(int)
    p = x.pt_position.str.split(",", expand=True).astype(float)
    x["xu"], x["zu"] = p[0] * VOX[0], p[2] * VOX[1]
    pts = x.groupby("mi")[["xu", "zu"]].mean()          # a few axons have several points: average
    meta = m.loc[pts.index, ["super_class", "cell_type", "malecns_cell_type", "side", "pd_width"]]
    a = pts.join(meta)
    dn = a[a.super_class == "descending"].copy()
    gf = dn[dn.cell_type == "DNp01"]
    assert len(gf) == 2, gf
    mid = gf.xu.mean()
    gfxz = gf[["xu", "zu"]].to_numpy()
    allr = (a.xu - mid).abs()
    dn["dx"] = dn.xu - mid
    dn["dz"] = dn.zu - gf.zu.mean()
    dn["d_gf"] = np.min(np.hypot(dn.xu.to_numpy()[:, None] - gfxz[None, :, 0],
                                 dn.zu.to_numpy()[:, None] - gfxz[None, :, 1]), axis=1)
    dn["lat"] = (dn.dx.abs() / allr.quantile(1.0)).round(3)
    dn["t"] = dn.cell_type.fillna("untyped").astype(str)
    dn = dn[dn.t != "DNp01"]

    def band(mask: pd.Series) -> dict[str, dict]:
        out = {}
        for t, g in dn.groupby("t"):
            k = int(mask[g.index].sum())
            if k:
                out[t] = dict(in_band=k, of=len(g), malecns=sorted(set(g.malecns_cell_type.dropna().astype(str))),
                              pd_width_um=round(float(g.pd_width.astype(float).median()), 2))
        return out

    med = {r: band(dn.d_gf < r) for r in MEDIAL_UM}
    lat = {q: band(dn.dx.abs() >= allr.quantile(q)) for q in LATERAL_Q}

    def grade(t: str, narrow: dict, wide: dict) -> str:
        # excluded: SEZ soma, not labelled by the driver. low: in the narrow band, with every cell of
        # the type in the wide band. very low: otherwise.
        if is_sez(t, wide[t]["malecns"]):
            return "excluded (SEZ soma)"
        if t in narrow and wide[t]["in_band"] == wide[t]["of"]:
            return "low"
        return "very low"

    rows = []
    for name, d, (nr, wd) in (("medial_near_GF", med, MEDIAL_UM), ("lateral_extreme", lat, LATERAL_Q)):
        for t, v in sorted(d[wd].items(), key=lambda kv: (-(kv[0] in d[nr]), kv[0])):
            rows.append(dict(band=name, banc_type=t, **v, in_narrow=t in d[nr],
                             confidence=grade(t, d[nr], d[wd]), label="inferred"))
    # model state at rest (seed 12 run of dn_rest_rates.py), by male-cns type
    rest = json.loads((REPO / "runs/s12/dnrest/dn_rest_s12.json").read_text())
    act = {}
    for r in rest["active"]:
        act.setdefault(r["type"], []).append(r["hz"])
    for r in rows:
        r["model_rest_hz_s12"] = {t: act.get(t, [0.0]) for t in r["malecns"]}
    # orientation check: Aymanns place DNx01 (BANC super_class sensory_descending) "ventral to the
    # giant fiber neurons axons"
    dx01 = a[a.cell_type == "DNx01"]
    orient = dict(dnx01_dz_um=(dx01.zu - gf.zu.mean()).round(2).tolist(), dnx01_dx_um=(dx01.xu - mid).round(2).tolist(),
                  expect="dz < 0 if high z is dorsal")
    res = dict(
        orientation_check=orient,
        source=dict(doi="10.7910/DVN/8TFGGB", version="8.1", file="neck_connective_y92500.tab", file_id=11844868,
                    md5_tab="5c0857091b4f153610c108bfe069602e", plane_y_vox=92500),
        n_points=int(len(x)), n_unjoined=n_unjoined, n_dn_axons=int(len(dn) + 2),
        gf_um=dict(left=gfxz[0].round(2).tolist(), right=gfxz[1].round(2).tolist(),
                   separation_um=round(float(np.hypot(*(gfxz[0] - gfxz[1]))), 2)),
        connective_um=dict(width=round(float(a.xu.max() - a.xu.min()), 1), depth=round(float(a.zu.max() - a.zu.min()), 1)),
        bands=dict(medial_um=MEDIAL_UM, lateral_quantile=LATERAL_Q,
                   lateral_cut_um={q: round(float(allr.quantile(q)), 1) for q in LATERAL_Q}),
        n_types=dict(medial={r: len(v) for r, v in med.items()}, lateral={q: len(v) for q, v in lat.items()}),
        n_by_grade={b: {g: sum(1 for r in rows if r["band"] == b and r["confidence"] == g)
                        for g in ("low", "very low", "excluded (SEZ soma)")}
                    for b in ("medial_near_GF", "lateral_extreme")},
        rows=rows,
    )
    OUT.write_text(json.dumps(res, indent=1, default=str))
    print(json.dumps({k: v for k, v in res.items() if k != "rows"}, indent=1, default=str))
    for r in rows:
        if r["confidence"] != "excluded (SEZ soma)":
            print(r["band"], r["confidence"], r["banc_type"], r["in_band"], "/", r["of"], r["malecns"],
                  r["pd_width_um"], r["model_rest_hz_s12"])


if __name__ == "__main__":
    main()
