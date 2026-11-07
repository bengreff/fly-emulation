# Channel genes with no published kinetics (catalog slots, row 4)

Written 7 Nov 2026 by wneuron. These are the ion-channel genes in the CeNGEN threshold-2 table (Taylor et al.
2021; `data/worm/structure/cengen_t2.csv`, 855 genes) that no published C. elegans model gives voltage or gating
kinetics for. They are slots, not code. "Classes" is the number of the 128 CeNGEN neuron classes that detect the
gene. Ligand-gated receptors are row 7 and are not listed here.

The genes that do have kinetics are in the brain. BAAIWorm (Nicoletti 2019) covers shk-1, shl-1, kvs-1, egl-2,
egl-36, irk-1/2/3, kqt-3, slo-1, slo-2, kcnl-1..4, egl-19, unc-2, cca-1 and nca-1/2. mech/channels (Nicoletti 2024)
adds kqt-1, unc-103, exp-2 and the bulk-Ca slo-1/slo-2.

| Gene(s) | Family | Classes | Note |
|---|---|---|---|
| twk-2, -3, -4, -7, -8, -9, -10, -11, -12, -13, -14, -16, -17, -18, -20, -22, -23, -24, -25, -26, -29, -30, -31, -32, -35, -39, -40, -42, -43, -44, -45, -46, -47, -48, -49 | K2P (TWK) leak K+ | 1 to 77 each | No C. elegans current is recorded per gene; the leak in BAAIWorm's pas lumps them. |
| sup-9, unc-58, egl-23 | K2P | 14, 54, 27 | Gain-of-function phenotypes only (muscle and HSN); no kinetics. |
| shw-1, shw-3 | Kv3 (Shaw) | 62, 37 | No neuronal current model. |
| kvs-2, kvs-3, kvs-4, kvs-5 | Kv2-like | 59, 29, 17, 26 | Only kvs-1 has a model (Nicoletti 2019). |
| kqt-2 | KCNQ | 1 | Detected in one class; no model. |
| unc-79, unc-80 | NALCN auxiliary subunits | 107, 128 | Part of the NCA complex, which BAAIWorm's nca stands for; no separate kinetics. |
| unc-8, del-1, del-2, del-4, del-5, del-8, del-9 | DEG/ENaC | 17, 30, 29, 2, 8, 18, 11 | No gating kinetics. |
| del-3, del-7 | DEG/ENaC | 12, 3 | senses_chem's NSM food template uses them as a receptor channel (occupancy), not as kinetics. |
| deg-1, mec-4, mec-10 | DEG/ENaC (mechanosensory) | 25, 6, 6 | senses_touch carries them (O'Hagan 2005 kinetics for MEC-4; ASH DEG-1 shares them). |
| trp-4 | TRP-N | 8 | senses_proprio carries it (DVA stretch) as a template current. |
| trp-1, trp-2 | TRPC | 26, 35 | senses_proprio cites them for SMD; no kinetics. |
| trpa-1 | TRPA | 45 | No neuronal kinetics. |
| osm-9, ocr-1, ocr-2, ocr-3, ocr-4 | TRPV | 14, 6, 8, 2, 1 | senses_chem's TRPV cells carry osm-9/ocr-2 as an occupancy template; no kinetics. |
| tax-2, tax-4, cng-1, cng-3 | CNG | 11, 17, 10, 12 | senses_chem / senses_cgmp's cGMP cascade gates TAX-2/TAX-4 in the cascade cells; cng-1/3 have no model. |
| itr-1, unc-68 | ER Ca release (IP3R, RyR) | 18, 100 | No neuron model; the bulk pool (row 6) has no ER. |
| lite-1 | photoreceptor (gustatory-receptor family) | 15 | A receptor, in senses_chem's light route; not a channel model. |
