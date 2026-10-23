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

## Synaptic events at rest (no run; partner rates from `runs/s20/mb/confirm_s12.json`)

Each type's input weight × the presynaptic type's rate at rest (MB types from the confirm run; every other cell at
the whole-brain mean 0.034 Hz). Sign from consensusNt, else predictedNt: ACh +, GABA and glutamate − (the model's
GluCl convention, inferred), dopamine no fast sign. These are synaptic events per s per cell, not currents.

| type | excitatory ev/s | inhibitory ev/s | of which from active MB types | model / data |
|---|---|---|---|---|
| MBON11 | 355 | 7,423 | 7,420 | 0.23 |
| PPL101 | 2,042 | 3,114 | 3,035 | 0.34 |
| PPL106 | 614 | 470 | 432 | 0.44 |
| MBON12 | 233 | 3,478 | 3,455 | 0.53 |
| PPL103 | 1,287 | 3,135 | 3,089 | 0.56 |
| MBON13 | 219 | 2,988 | 2,966 | 0.78 |
| MBON14 | 543 | 2,466 | 2,462 | 0.79 |
| PPL105 | 878 | 1,342 | 1,310 | 0.89 |
| MBON17 | 512 | 807 | 798 | 1.07 |
| MBON18 | 377 | 1,789 | 1,756 | 1.13 |
| PPL104 | 4,641 | 263 | 238 | 1.92 |

- Inhibitory events against the model/data ratio: ρ −0.67 (p 0.023); excitatory: +0.17 (0.61).
- Almost all the inhibition at rest comes from other MBONs firing at 11-16 Hz: the glutamatergic MBON → MBON
  links of the MB output network. MBON11's largest are MBON05 (203 synapses per cell, 12.8 Hz) and MBON06 (123,
  13.1 Hz). PPL101's largest is MBON11 itself (GABA).
- So candidate 2 has support. Two of its parts are open: the sign of glutamate at these links (GluCl inhibition
  is inferred, not measured for MBON → MBON), and the MBON rates themselves. Where in vivo MBONs fire at Huang's
  rates, KC drive (candidate 1) would have to balance this. PPL1-α3 (PPL106) is the exception: little inhibition,
  still slow, so it points to candidate 3 or to missing excitation.

## Model drive at rest, in the network's own weights (`scripts/probes/s22_mb_rest_drive.py`, no simulation)

The m10f3 network as built for the MB rest run (fitted class noise, plasticity off). Drive = Σ final signed weight
× presynaptic rate at rest, mV/s per cell (rates as above). Output `runs/s20/mb/rest_drive.json`, wall 4 s.

| type | inhibitory, from MB | excitatory, from MB | net (all sources) | KC drive per 1 Hz of KC firing | KC Hz that would cancel net | model / data |
|---|---|---|---|---|---|---|
| MBON11 | −1,146 | 32 | −1,115 | 3,034 | 0.37 | 0.23 |
| PPL101 | −456 | 274 | −172 | 1,102 | 0.16 | 0.34 |
| PPL106 | −63 | 47 | −14 | 377 | 0.04 | 0.44 |
| MBON12 | −505 | 22 | −487 | 693 | 0.70 | 0.53 |
| PPL103 | −430 | 160 | −267 | 1,361 | 0.20 | 0.56 |
| MBON13 | −452 | 12 | −443 | 781 | 0.57 | 0.78 |
| MBON14 | −378 | 80 | −299 | 743 | 0.40 | 0.79 |
| PPL105 | −197 | 104 | −94 | 389 | 0.24 | 0.89 |
| MBON17 | −122 | 49 | −75 | 191 | 0.39 | 1.07 |
| MBON18 | −269 | 37 | −237 | 1,022 | 0.23 | 1.13 |
| PPL104 | −13 | 697 | +683 | 93 | (net excitatory) | 1.92 |

- **Candidate 3 is out in the current model.** Every one of the 11 types has τ_m 20 ms, threshold gap 7 mV and
  input gain 1.0. There is no per-type intrinsic row, so all type differences come from synaptic drive at rest.
- **Candidate 2 holds in model units.** Inhibition from active MB partners against model/data: ρ +0.69 (p 0.019;
  inhibition is negative, so more inhibition goes with a lower ratio). Excitation: +0.26 (0.43).
- **Candidate 1 is the class-level counterweight.** KC drive per Hz is largest for MBON11 (3,034 mV/s) and
  correlates with the gap (ρ −0.57, p 0.066). A single KC rate of 0.04-0.70 Hz would cancel the net inhibition
  type by type. This is mean drive only; rates also depend on fluctuations, so it needs a run.

## Next

1. **Measured KC rate (read 23 Oct, Sonnet reader, KC rates only; MBON and DAN rates barred and not seen).**
   - Turner, Bazhenov & Laurent 2008 J Neurophysiol 99:734: "very low spontaneous firing (0.1 ± 0.4 spike/s)"
     (mean ± s.d.). Whole-cell at the soma; 71 KCs, 14 of which never fired; Canton-S **females**, 1-2 days old;
     subtypes pooled. Text value; measured, other sex.
   - Gruntman & Turner 2013 Nat Neurosci 16:1821: "most cells had a baseline rate of zero" (no number).
   - Murthy et al. 2008 and Inada et al. 2017 give no baseline rate of their own (Inada cites Turner).
   - No per-subtype spontaneous rate exists in these papers.
2. **At 0.1 Hz, KC drive offsets only part of the inhibition** (mean drive, the network's weights):
   - MBON11 +303 against −1,115 mV/s (27 %), MBON12 14 %, MBON13 18 %, MBON14 25 %, MBON17 26 %, MBON18 43 %;
   - PPL101 64 %, PPL103 51 %, PPL105 41 %; PPL106 turns net excitatory.
   - So KC firing at the measured mean is a partial counterweight, largest in absolute terms for MBON11. It
     cannot close MBON11's gap alone, and the MBON → MBON inhibition stays the main lever.
3. **Next.**
   - A rest run with KCs at 0.1 Hz (Poisson, class level, measured, switch off by default). Descriptive only:
     Huang is spent, so adoption needs a new held-out MB rate source, registered first.
   - Read the evidence for the sign of glutamate at MBON → MBON and MBON → DAN links (GluCl inhibition is inferred
     in the model). MBON11's inhibition at rest comes mostly from glutamatergic MBON05 and MBON06.
