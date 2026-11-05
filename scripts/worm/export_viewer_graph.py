"""Export the wiring graph the worm viewer draws (a VIEW of the data, not the model).

Inputs (copied from backhouse ~/worm-data, pinned in docs/worm/MANIFEST.md):
  soma_positions.txt   first <proximal> point of each OpenWorm CElegansNeuroML generatedNeuroML2 cell
                       (soma centre, um, Virtual Worm coordinates: y = anterior-posterior, x = left-right,
                       z = dorsal-ventral). Label: inferred (reconstructed 3D atlas, not one animal's scan).
  cook_si5.xlsx        Cook et al. 2019 SI 5, adjacency matrices corrected July 2020: hermaphrodite chemical
                       (synapse counts, rows pre, cols post) and gap jn symmetric. Label: measured (EM).
  01022024_neuropeptide_connectome_short_range_model.csv  Ripoll-Sanchez et al. 2023, peptide-GPCR pair
                       counts per neuron pair (short-range diffusion model). Label: inferred (expression).
  08062023_monoamine_connectome.csv  Bentley et al. 2016 monoamine network. Label: inferred (expression).

Usage: uv run --no-project --with pandas --with openpyxl python scripts/worm/export_viewer_graph.py SRC OUT
"""
import json
import re
import sys
from pathlib import Path

import pandas as pd

src = Path(sys.argv[1])
out = Path(sys.argv[2])

# ---- soma positions
pos = {}
for line in (src / "soma_positions.txt").read_text().splitlines():
    name, rest = line.split("|", 1)
    m = re.search(r'x="([-\d.eE]+)" y="([-\d.eE]+)" z="([-\d.eE]+)" diameter="([-\d.eE]+)"', rest)
    if m and not re.fullmatch(r"M[DV][LR]\d+", name):  # MDL08.cell.nml is a muscle, not a neuron
        # NeuroML writes DA1, Cook 2019 writes DA01: use Cook's zero-padded names throughout
        name = re.sub(r"^([A-Z]{2})(\d)$", r"\g<1>0\2", name)
        pos[name] = [float(m.group(i)) for i in range(1, 5)]

# ---- Cook 2019 chemical and gap matrices
def matrix(sheet):
    df = pd.read_excel(src / "cook_si5.xlsx", sheet, header=None)
    cols = df.iloc[2, 3:].tolist()
    rows = df.iloc[3:, 2].tolist()
    groups = df.iloc[3:, 0].ffill().tolist()
    vals = df.iloc[3:, 3:]
    return cols, rows, groups, vals

cols, rows, groups, chem = matrix("hermaphrodite chemical")
gcols, grows, _, gap = matrix("hermaphrodite gap jn symmetric")

group_of = {}
for r, g in zip(rows, groups):
    if isinstance(r, str):
        group_of[r] = str(g)

neurons = sorted(pos.keys())
# muscle names in Cook 2019: dBWML1..24 / dBWMR / vBWML / vBWMR
muscles = [c for c in cols if isinstance(c, str) and re.fullmatch(r"[dv]BWM[LR]\d+", c)]

cell_set = set(neurons) | set(muscles)
chem_edges, nmj_edges, gap_edges = [], [], []
for i, r in enumerate(rows):
    if not isinstance(r, str) or r not in pos:
        continue
    for j, c in enumerate(cols):
        if not isinstance(c, str):
            continue
        v = chem.iat[i, j]
        if pd.notna(v) and float(v) > 0:
            if c in pos:
                chem_edges.append([r, c, int(v)])
            elif c in muscles:
                nmj_edges.append([r, c, int(v)])
for i, r in enumerate(grows):
    if not isinstance(r, str) or r not in pos:
        continue
    for j, c in enumerate(gcols):
        if not isinstance(c, str) or c not in cell_set:
            continue
        v = gap.iat[i, j]
        if pd.notna(v) and float(v) > 0 and (c in muscles or r < c):
            gap_edges.append([r, c, int(v)])

def expr_net(fname):
    df = pd.read_csv(src / fname, index_col=0)
    e = []
    for r in df.index:
        if r not in pos:
            continue
        row = df.loc[r]
        for c, v in row.items():
            if c in pos and v > 0 and c != r:
                e.append([r, c, int(v)])
    return e

pep_edges = expr_net("01022024_neuropeptide_connectome_short_range_model.csv")
mono_edges = expr_net("08062023_monoamine_connectome.csv")

def quad(m):
    return m[0].upper() + m[4]  # dBWML3 -> DL

graph = {
    "neurons": [{"name": n, "x": pos[n][0], "y": pos[n][1], "z": pos[n][2], "d": pos[n][3],
                 "group": group_of.get(n, "OTHER END ORGANS" if n.startswith("CAN") else "UNLISTED")} for n in neurons],
    "muscles": [{"name": m, "quadrant": quad(m), "index": int(re.sub(r"\D", "", m))} for m in muscles],
    "edges": {"chemical": chem_edges, "electrical": gap_edges, "peptide": pep_edges,
              "monoamine": mono_edges, "nmj": nmj_edges},
    "sources": {
        "positions": "OpenWorm CElegansNeuroML generatedNeuroML2 soma proximal points (inferred atlas)",
        "chemical": "Cook et al. 2019 SI5 corrected July 2020, hermaphrodite chemical (measured, EM synapse counts)",
        "electrical": "Cook et al. 2019 SI5 corrected July 2020, hermaphrodite gap jn symmetric (measured, EM)",
        "peptide": "Ripoll-Sanchez et al. 2023 short-range neuropeptide connectome (inferred from expression)",
        "monoamine": "Bentley et al. 2016 monoamine connectome (inferred from expression)",
        "nmj": "Cook et al. 2019 chemical synapses onto body-wall muscles (measured)",
    },
}
out.parent.mkdir(parents=True, exist_ok=True)
out.write_text(json.dumps(graph, separators=(",", ":")))
print("neurons", len(neurons), "muscles", len(muscles), {k: len(v) for k, v in graph["edges"].items()})
from collections import Counter
print(Counter(quad(m) for m in muscles), Counter(n["group"] for n in graph["neurons"]))
print("bytes", out.stat().st_size)
