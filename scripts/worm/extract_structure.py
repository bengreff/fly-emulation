"""Extract the worm's structural tables (measured data) from ~/worm-data on backhouse into small tidy CSVs.

Run on backhouse (needs openpyxl): python extract_structure.py OUTDIR. Inputs pinned by docs/worm/MANIFEST.md.
Outputs (all measured data, copied without change except reshaping):
  cells.csv          every cell in Cook 2019 SI 4 (pharynx, sex-shared, hermaphrodite-specific sheets):
                     name, category, sheet, note
  chem_edges.csv     hermaphrodite chemical adjacency, SI 5 corrected July 2020: pre, post, n (EM synapse count)
  gap_edges.csv      hermaphrodite gap junctions, symmetric sheet: a, b, n (a < b), EM gap-junction count
  cengen_t2.csv      CeNGEN threshold-2 (medium) presence, genes of the families listed below x 128 neuron classes
"""
import csv, os, re, sys
import openpyxl

D = os.path.expanduser("~/worm-data")
OUT = sys.argv[1]
os.makedirs(OUT, exist_ok=True)

# gene families that carry mechanisms in the template (channels, gap junctions, receptors, transmitter
# markers, peptides and their receptors, sensory transduction, slow signalling)
FAM = re.compile(r"^(egl-19|unc-2|cca-1|nca-[12]|unc-80|unc-79|shl-1|shk-1|shw-[1-3]|kvs-[1-5]|egl-36|exp-2|kqt-[1-3]|"
                 r"egl-2|unc-103|irk-[1-3]|slo-[12]|kcnl-[1-4]|twk-\d+|sup-9|unc-58|egl-23|egl-58|"
                 r"inx-\d+|unc-7|unc-9|eat-5|che-7|"
                 r"glr-\d+|nmr-[12]|avr-1[45]|glc-[1-4]|acc-[1-4]|acr-\d+|lgc-\d+|unc-29|unc-38|unc-63|lev-[18]|"
                 r"unc-49|exp-1|gab-1|ggr-[1-3]|mod-1|ser-[1-7]|dop-[1-6]|tyra-[23]|octr-1|gar-[1-3]|gbb-[12]|"
                 r"mgl-[1-3]|"
                 r"eat-4|unc-17|cha-1|unc-25|unc-47|tph-1|cat-[12]|tdc-1|tbh-1|bas-1|mod-5|dat-1|snf-3|unc-46|"
                 r"flp-\d+|nlp-\d+|ins-\d+|pdf-[12]|ntc-1|snet-1|capa-1|trh-1|npr-\d+|frpr-\d+|dmsr-\d+|pdfr-1|"
                 r"ckr-[12]|ntr-1|tkr-\d|seb-3|egl-6|aex-[25]|egl-3|egl-21|unc-31|sbt-1|"
                 r"gnrr-\d+|nmur-\d+|sprr-\d+|trhr-1|pdfr-\d+|"  # receptors of the Beets 2023 pairs (5 Nov)
                 r"gcy-\d+|daf-11|odr-1|tax-[24]|cng-[13]|ocr-[1-4]|osm-9|trp-[124]|trpa-1|pkd-2|lov-1|mec-[1-6]|mec-10|"
                 r"deg-1|del-\d+|unc-8|lite-1|odr-10|str-2|sra-\d+|srx-\d+|"
                 r"egl-4|unc-43|cmk-1|crh-1|daf-[27]|daf-16|daf-2|daf-28|tax-6|cnb-1|itr-1|egl-30|goa-1|gsa-1|"
                 r"egl-8|dgk-1|eat-16|unc-13|unc-18|unc-10|rab-3|snb-1|unc-64|ric-4|cpx-1|tom-1|"
                 r"pmk-[1-3]|nhr-\d+|crt-1|unc-68|sca-1|calu-1|ncx-\d+|mca-[1-3]|"
                 r"unc-64|unc-17|ryr-1)$")

def sheet_rows(path, sheet):
    ws = openpyxl.load_workbook(path, read_only=True, data_only=True)[sheet]
    return [list(r) for r in ws.iter_rows(values_only=True)]

# 1. cells
SI4 = f"{D}/cook2019/SI 4 Cell lists.xlsx"
with open(f"{OUT}/cells.csv", "w", newline="") as fh:
    w = csv.writer(fh); w.writerow(["name", "category", "sheet", "note"])
    for sh in ("pharynx", "sex-shared", "hermaphrodite specific"):
        for r in sheet_rows(SI4, sh):
            vals = [x for x in r if x is not None]
            if not vals or vals[0] == "cell type":
                continue
            w.writerow([str(vals[0]).strip(), str(vals[1]).strip() if len(vals) > 1 else "", sh,
                        "; ".join(str(v) for v in vals[2:])])

# 2. adjacency
SI5 = f"{D}/cook2019/SI 5 Connectome adjacency matrices, corrected July 2020.xlsx"
def adjacency(sheet):
    rows = sheet_rows(SI5, sheet)
    cols = rows[2][3:]
    out = {}
    for r in rows[3:]:
        if r[2] is None:
            continue
        for c, x in zip(cols, r[3:]):
            if c is not None and isinstance(x, (int, float)) and x > 0:
                out[(str(r[2]).strip(), str(c).strip())] = x
    return out
chem = adjacency("hermaphrodite chemical")
with open(f"{OUT}/chem_edges.csv", "w", newline="") as fh:
    w = csv.writer(fh); w.writerow(["pre", "post", "n"])
    for (a, b), n in sorted(chem.items()):
        w.writerow([a, b, n])
gap = adjacency("hermaphrodite gap jn symmetric")
seen = {}
for (a, b), n in gap.items():
    if a == b:
        continue
    k = tuple(sorted((a, b)))
    seen[k] = max(seen.get(k, 0), n)
with open(f"{OUT}/gap_edges.csv", "w", newline="") as fh:
    w = csv.writer(fh); w.writerow(["a", "b", "n"])
    for (a, b), n in sorted(seen.items()):
        w.writerow([a, b, n])

# 3. CeNGEN
def filt(src, dst, sep):
    with open(src) as fi, open(dst, "w", newline="") as fo:
        r = csv.reader(fi, delimiter=sep); w = csv.writer(fo)
        hdr = next(r); w.writerow(hdr)
        gi = hdr.index("gene_name") if "gene_name" in hdr else None
        for row in r:
            g = row[gi] if gi is not None else row[0]
            if FAM.match(g.strip('"')):
                w.writerow(row)
filt(f"{D}/cengen/021821_medium_threshold2.csv", f"{OUT}/cengen_t2.csv", ",")
print("done", len(chem), "chem", len(seen), "gap")
