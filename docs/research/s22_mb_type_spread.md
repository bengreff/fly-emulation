# s22 MB type spread (Director item 3): first look at a per-type source

Written 23 Oct 2026, s22, while a probe waited for a slot. Exploratory, no run. Huang 2024 is spent (F-S21-1),
so nothing here can be scored on it again. A per-type mechanism found from this needs a new held-out source.

## Per-type inputs against the model/data ratio

male-cns v1.0 cache (`data/cache/male_cns_edges.parquet`, all edges), mean per cell. KC inputs are the
presynaptic cells whose type starts with "KC". Model rates are from the fitted MB rest run (σ*_DAN 1.477,
σ*_MBON 2.287; `runs/s20/mb/huang_score.json`), and the data are Huang 2024 medians.

| type | Huang name | cells | size (10⁶ voxels) | input synapses | from KCs | not from KCs | model Hz | data Hz | model / data |
|---|---|---|---|---|---|---|---|---|---|
| MBON11 | MBON-γ1 | 2 | 3,948 | 23,441 | 20,730 | 2,711 | 7.9 | 34.8 | 0.23 |
| PPL101 | PPL1-γ1 | 2 | 4,124 | 19,568 | 12,034 | 7,534 | 7.0 | 20.4 | 0.34 |
| PPL106 | PPL1-α3 | 2 | 1,938 | 8,560 | 5,528 | 3,032 | 6.2 | 14.0 | 0.44 |
| MBON12 | MBON-γ2 | 4 | 1,529 | 6,983 | 5,651 | 1,332 | 11.2 | 20.9 | 0.53 |
| PPL103 | PPL1-γ2 | 2 | 4,362 | 15,788 | 11,650 | 4,138 | 6.5 | 11.7 | 0.56 |
| MBON13 | MBON-α′2 | 2 | 1,891 | 6,471 | 5,097 | 1,374 | 12.1 | 15.6 | 0.78 |
| MBON14 | MBON-α3 | 4 | 1,220 | 6,296 | 5,554 | 742 | 12.0 | 15.2 | 0.79 |
| PPL105 | PPL1-α2 | 2 | 1,779 | 8,636 | 6,344 | 2,292 | 7.6 | 8.5 | 0.89 |
| MBON17 | MBON-α′3m | 2 | 533 | 2,010 | 1,510 | 500 | 14.0 | 13.1 | 1.07 |
| MBON18 | MBON-α2sc | 2 | 1,834 | 8,512 | 6,962 | 1,550 | 11.0 | 9.8 | 1.13 |
| PPL104 | PPL1-α′3 | 2 | 1,380 | 3,586 | 1,568 | 2,018 | 14.9 | 7.7 | 1.92 |

Spearman ρ over the 11 types (n = 11, p uncorrected, descriptive only):

| feature | vs model Hz | vs data Hz | vs model / data |
|---|---|---|---|
| total input synapses | −0.83 (p 0.002) | +0.34 (0.31) | −0.72 (0.013) |
| size (voxels) | −0.77 (0.005) | +0.28 (0.40) | −0.67 (0.023) |
| from KCs | −0.65 (0.029) | +0.35 (0.29) | −0.58 (0.060) |
| not from KCs | −0.79 (0.004) | +0.01 (0.98) | −0.53 (0.096) |

## Reading

- **The gap is mostly on the model side.** In the model, the cells with more inputs fire less. In the data, they
  fire about the same or a little more. The three failing types (γ1 pair, PPL1-α3) and PPL1-γ2 are the large,
  heavily innervated cells.
- **Class noise does not scale with size** (`lif.py`: one draw per cell, same σ across a class). So the fall with
  input count comes from synaptic input at rest or from per-type intrinsic rows.
- Candidates for next session, each a biological quantity at class level, no per-type knob:
  1. **Spontaneous KC firing.** KCs sit at 0 Hz in the isolated model. In vivo they fire sparsely at rest, so
     the cells with the most KC synapses lose the most drive here. A measured class-level KC rate would add drive
     in proportion to KC input count. The KC column alone is only marginal (ρ −0.58), so this cannot be the
     whole story.
  2. **Net inhibition at rest.** The active presynaptic partners at rest may be mostly inhibitory, so more inputs
     means more inhibition. Check: split each type's mean synaptic current at rest by source sign, in a short
     run.
  3. **Size and intrinsic rows.** Does any per-type τ_m, threshold or leak row scale with size between types? The
     within-type size rule (`percell.py`) is within-type only.
- Note: male-cns `predictedNt` calls 4,058 KCs "dopamine". The build already overrides this with consensusNt
  acetylcholine (`connectome.py`, Davis 2020), so the model is not affected.

## Next

A rest run with the input current split by source (KC, inhibitory, excitatory non-KC, noise) per type. That
decides between 1-3 before any source is read for a rate.
