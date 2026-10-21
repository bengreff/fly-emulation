# S21 — MN5 / GF→PSI→DLMn literature survey (sections A–D)

Compiled 2026-10-21. Scope: measured values to inform the MN5 doublet-vs-singlet fix (see
`docs/DECISIONS.md` N30 entry). Sealed items (E1/E2 — GF:DLM 1:1 vs doublet, refractory period,
following frequency, somatic spike amplitude of the axon-initiated spike) are written separately to
`docs/research/sealed/s21_gf_dlm_sealed.md` and are NOT included here or in numeric form anywhere in
this file.

Access method: web search + WebFetch of PMC/journal pages. Several APS (journals.physiology.org) and
Cell Press (cell.com) pages returned HTTP 403 and could not be read beyond what a search engine's own
summary surfaced; those cases are flagged explicitly as **unverified / secondary-summary only** — the
primary text was not read by me, so treat with lower confidence and re-check before using as a hard
constraint.

---

## A. MN5 intrinsic membrane properties

| Quantity | Value | n | Stage / prep | Temp | Source | Label |
|---|---|---|---|---|---|---|
| Resting potential (held) | −74 mV | — | adult, whole-cell patch, soma, post-protease | RT | Fayyazuddin et al. 2006 | measured (held value in methods, not a population statistic) |
| Input resistance | 102 ± 12 MΩ | 22 | adult MN5, soma patch | RT | Fayyazuddin et al. 2006 | measured — **but my fetch could not confirm whether n=22 is WT-only or WT+mutant pooled; flag for re-check against primary PDF** |
| Membrane capacitance | 43 ± 2 pF | 22 | adult MN5 | RT | Fayyazuddin et al. 2006 | measured (same n-pooling caveat as above) |
| Spike amplitude (direct somatic current injection) | 50–60 mV | — | adult MN5, Fig. 5D | RT | Fayyazuddin et al. 2006 | measured |
| Input resistance | 97 ± 31 MΩ | 52 | adult MN5, somatic patch | ~22 °C | Herrera-Valdez, McKiernan, Berger, Ryglewski, Duch, Crook 2012, *J Comput Neurosci* 34(2):211–229, PMC6595220 | measured (original data for this modeling paper) |
| Membrane capacitance | 127 ± 16 pF | 52 | adult MN5 | ~22 °C | same (Herrera-Valdez et al. 2012) | measured |
| Fraction of recorded MN5 that fired to current injection | 48/52 (92%) | 52 | adult MN5, 100 pA–2 nA square pulses | ~22 °C | Herrera-Valdez et al. 2012 | measured |
| Max dv/dt (used only to derive a model scaling constant ξ) | ~100 mV/ms | 52 (avg) | adult MN5 | ~22 °C | Herrera-Valdez et al. 2012 | measured, but purpose-built for their model fit, not an independent physiological constant |
| Resting potential (control, non-manipulated MN5) | −56.1 ± 5.1 mV | — | not independently confirmed — likely pupal/adult dendrite-growth study | not stated in what I could access | Duch, Vonhoff, Ryglewski 2008, *J Neurophysiol* 100(5):2525–2536 | **unverified / secondary-summary only** — journals.physiology.org returned 403; number comes from a search-engine snippet, not a page I read directly. Re-check before use. |
| Resting potential, voltage-clamp holding value (not a characterized population mean) | −65 mV | — | adult MN5 | RT | Ryglewski, Lance, Levine, Duch 2012, *J Physiol* 590(4):809–825, PMC3381312 | measured but stated only as a protocol holding potential, not reported with n/SD — do not treat as a characterized resting-potential statistic |
| Tonic firing range during flight | ~2–12 Hz | — | adult MN1–5, in-flight recording | — | cited via Huthmacher et al. 2025 bioRxiv (10.1101/2025.06.16.659928), attributing to Hürkey et al. 2023 — **I did not independently read Hürkey et al. 2023; this is a second-hand citation** | measured (provenance one step removed) |
| Firing rate example under one stated control condition | 5.2 ± 1.3 Hz | — | adult, in vivo | — | Huthmacher et al. 2025 bioRxiv, Fig. 2 | measured (preprint, not yet peer-reviewed) |
| F/I relationship | approximately linear, "type-I", working range ~3–30 Hz | — | adult MN5, square current injections 0–0.9 nA in 0.1 nA steps, 400 ms | fly-rearing 25 °C | Huthmacher et al. 2025 bioRxiv | measured (preprint) |

**Not found / gaps in A:** I could not retrieve, from any source I could actually read, a quantified
spike threshold, spike half-width, or AHP amplitude/duration for adult MN5 outside current-injection
context. Ryglewski & Duch 2009 (*J Neurophysiol* 102:3673–3688, Shaker/Shal paper) and Ryglewski, Kilo,
Duch 2014 (*Eur J Neurosci* 39(10):1572–1585 — the developmental spike-shape paper, which by title is
the most likely place for pupal-vs-adult spike amplitude/half-width/AHP data) were both behind 403
walls on journals.physiology.org / onlinelibrary.wiley.com and I found no PMC mirror. Anything attributed
to them beyond the bare citation should be treated as absent, not as "checked and not reported."

**Direct answer to the specific question asked:** yes — an adult MN5 input resistance other than
Fayyazuddin's 102 ± 12 MΩ (n=22) is reported. Herrera-Valdez et al. 2012 (*J Comput Neurosci*,
PMC6595220 — the paper behind the PMC ID the brief associated with "Kadas et al. 2019"; the correct
citation is Herrera-Valdez et al. 2012, not a 2019 Kadas paper) give Rin = 97 ± 31 MΩ and Cm = 127 ± 16
pF, both n=52, i.e. a larger, independently-measured sample with a similar mean Rin but much larger
spread than Fayyazuddin's.

---

## B. PSI→MN5 synaptic kinetics, and a class bracket for nicotinic EPSC/mEPSC decay in adult Drosophila CNS

| Quantity | Value | n | Prep | Source | Label |
|---|---|---|---|---|---|
| PSI→DLMn EPSP amplitude, wild type | 4.71 ± 0.35 mV | 10 | adult, soma current-clamp, Fig. 5E, "three independent methods" | Fayyazuddin et al. 2006, PMC1382016 | measured |
| Same, *gf*A1 mutant (not WT, context only) | 1.5 ± 0.32 mV | 7 | adult | Fayyazuddin et al. 2006 | measured (mutant, for contrast only) |
| EPSP rise time / half-width / decay τ | **not found** | — | — | Fayyazuddin et al. 2006 | gap — not reported in the content I could access; the paper reports EPSP amplitude but I found no quantified shape parameters |
| EPSC decay τ (voltage clamp) | **not reported** | — | — | Fayyazuddin et al. 2006 | the paper used current-clamp recordings only, per what I read; no EPSC/voltage-clamp decay constant exists in this source |

Class bracket — nicotinic EPSC/mEPSC decay time constants at other identified adult/cultured
Drosophila central cholinergic synapses (useful only as a plausibility bracket, not as a direct
PSI→MN5 measurement):

| Synapse | mEPSC/EPSC amplitude | 10–90% rise time | Decay τ | n | Prep | Source | Label |
|---|---|---|---|---|---|---|---|
| Cholinergic input onto Kenyon cells, in situ, adult whole brain | 3.8–4.9 pA (by genotype/driver) | 1.21–1.53 ms | 4.45–6.73 ms (single exponential) | 5–14 per group | adult, in situ whole-brain patch | Gu & O'Dowd 2006, *J Neurosci* 26(1):265–272, PMC6674319 | measured — full text read directly, high confidence |
| Nicotinic current onto cultured Kenyon cells | — | — | 1.35 ms (one representative cell; population mean/SEM not found) | not found | **cultured** (embryonic/larval-derived primary culture, not adult in situ) | Su & O'Dowd 2003, *J Neurosci* 23(27):9246–9253 | **unverified / secondary-summary only** — jneurosci.org 403'd; number is from a search-engine snippet, and I could not find the population statistic, only a single-cell example. Different prep (culture) from Gu & O'Dowd, so not directly comparable to adult in situ values. |
| ORN→PN EPSC (olfactory antennal lobe) | — | — | reported in search-engine summaries as ~2.8 ms | — | adult, in situ | Kazama & Wilson 2008, *Neuron* 58(3):401–413 | **unverified** — cell.com 403'd on every attempt; I could not read the primary text, so I cannot confirm this number against the source. Treat as unconfirmed, do not cite as if read directly. |

**Bottom line for B:** the actual PSI→MN5 EPSC/EPSP decay kinetics have not been found quantified
anywhere I could read (Fayyazuddin 2006 gives amplitude only). The one directly-confirmed class-bracket
data point (Gu & O'Dowd 2006, adult in situ Kenyon cells) puts nicotinic mEPSC decay at roughly 4.5–6.7
ms, i.e. in the same range as the model's current 5 ms synaptic-current duration — so the 5 ms decay
assumption is "consistent with some adult Drosophila central cholinergic synapse," but is not itself a
PSI→MN5 measurement. The Su & O'Dowd and Kazama & Wilson numbers could not be independently confirmed
and should not be relied on without re-fetching the primary text.

---

## C. Drosophila axial (cytoplasmic) resistivity Ri

| Source | Ri (Ω·cm) | Status | Fit target | Label |
|---|---|---|---|---|
| Gouwens & Wilson 2009, *J Neurosci* 29(19):6239–6249, PMC2709801 ("Signal propagation in Drosophila central neurons") | Cell 1: 163.9; Cell 2: 102.5; Cell 3: 266.1 | free parameter, fit per cell | current-clamp responses to brief current-pulse injection, cross-validated against white-noise current injection | **fitted**, not measured — confirmed by reading the full text directly (high confidence) |
| Same paper | Rm: 8.3, 20.4, 20.8 kΩ·cm²; Cm: 2.6, 1.5, 0.8 μF/cm² | free parameters, fit per cell, same 3 cells | same | fitted |
| Meier & Borst 2019, *Curr Biol*, "Extreme Compartmentalization in a Drosophila Amacrine Cell" (CT1 model) | reported in search-engine summaries as Ra ≈ 150 Ω·cm (model assumption), with an alternative fit elsewhere cited as ρi ≈ 400 Ω·cm, ρm ≈ 8000 Ω·cm² | unclear which is the paper's adopted value vs. a sensitivity-range endpoint | not confirmed | **unverified / secondary-summary only** — cell.com 403'd; I could not read the primary text, so neither number should be treated as confirmed. Re-fetch before using. |

I did not find time to search Cuntz/Borst LPTC modeling papers beyond Meier & Borst, nor any larval MN
compartmental model, for additional Ri values — flag as **not searched**, a gap rather than a
confirmed absence.

**Bottom line for C:** the only value I can vouch for with high confidence is Gouwens & Wilson 2009's
three per-cell FITTED values (102.5–266.1 Ω·cm, i.e. roughly a 2.6× spread across 3 cells of the same
identified neuron type), obtained by simultaneously co-optimizing Ri, Rm, and Cm against passive
current-clamp responses — it is explicitly a free/fitted parameter in their model, not an independently
measured physical constant.

---

## D. EM tissue shrinkage (FlyEM datasets) and MN5 axon diameter

This section is the weakest of the four — I could not find an explicit, quoted linear-shrinkage
correction factor for hemibrain, MANC, or male-cns v1.0, despite targeted searches of the primary
papers (Scheffer et al. 2020 eLife for hemibrain; Takemura et al. 2024/2025 eLife for MANC; the
male-cns v1.0 release documentation) and of general Drosophila EM fixation/embedding literature.

| Finding | Detail | Source | Label |
|---|---|---|---|
| Volumetric size comparison (not EM-specific) | "unfixed brains right after dissection in saline are 15–20% larger than the antibody-labeled brains mounted in 80% glycerol" | Scheffer et al. 2020, *eLife* 9:e57443 (hemibrain) | measured, **but this compares two light-microscopy preparation states (unfixed-in-saline vs. antibody-labeled-in-glycerol), not EM vs. native tissue** — it is at best an indirect, upper-bound-ish proxy for "how much a chemically processed Drosophila CNS can shrink/swell," not a validated EM linear-shrinkage factor. Do not use as if it were an EM correction factor. |
| General EM embedding shrinkage (non-Drosophila-specific) | epoxy resin embedding is generally reported to cause <2% linear shrinkage, versus much larger (tens of %) shrinkage through dehydration/CPD steps in some protocols | general EM methods literature (not Drosophila/connectome-specific) | class-bracket only, not a measured value for any FlyEM dataset |
| MANC/male-cns methods shrinkage statement | **not found** | searched Takemura et al. MANC eLife paper and male-cns v1.0 documentation directly; no explicit shrinkage factor located | gap |
| MN5/DLMn axon diameter (CNS or peripheral nerve) | **not found** | searched Phelps et al. 2021 *Cell* 184(3):759–774 (female VNC GridTape TEM), male-cns documentation, and general search; found only an unrelated leg-sensory-axon cross-section figure (3.63 ± 0.74 μm², n=6, a different axon class, same Phelps et al. 2021 paper) | gap — no MN5-specific number found |

**Bottom line for D:** no usable, dataset-specific EM linear shrinkage factor or MN5 axon diameter was
located. If this number is load-bearing for a geometry/cable-model decision, it should be treated as an
open gap requiring either a direct read of the hemibrain/MANC/male-cns supplementary methods (which I
could not access beyond the main text) or a fresh measurement from the connectome skeleton itself
(e.g., measuring the MN5 axon's EM-segmented diameter directly in neuPrint/CATMAID, which sidesteps the
shrinkage question for internal consistency, though not for absolute-scale biological accuracy).

---

## Sources list (full citations used above)

- Fayyazuddin A, Zaheer MA, Hiesinger PR, Bellen HJ (2006) The nicotinic acetylcholine receptor Dα7 is required for an escape behavior in *Drosophila*. *PLoS Biol* 4(3):e63. PMC1382016. (read directly)
- Herrera-Valdez MA, McKiernan EC, Berger SD, Ryglewski S, Duch C, Crook S (2012) Relating ion channel expression, bifurcation structure, and diverse firing patterns in a model of an identified motor neuron. *J Comput Neurosci* 34(2):211–229. PMC6595220. (read directly)
- Duch C, Vonhoff F, Ryglewski S (2008) Dendrite elongation and dendritic branching are affected separately by different forms of intrinsic motoneuron excitability. *J Neurophysiol* 100(5):2525–2536. (NOT read directly — 403; secondary summary only)
- Ryglewski S, Lance K, Levine RB, Duch C (2012) Ca_v2 channels mediate low and high voltage-activated calcium currents in Drosophila motoneurons. *J Physiol* 590(4):809–825. PMC3381312. (read directly)
- Ryglewski S, Duch C (2009) Shaker and Shal mediate transient calcium-independent potassium current in a Drosophila flight motoneuron. *J Neurophysiol* 102(6):3673–3688. (NOT accessible — 403, no PMC found; only a bare, unverifiable search snippet)
- Ryglewski S, Kilo L, Duch C (2014) Sequential acquisition of cacophony calcium currents, sodium channels and voltage-dependent potassium currents affects spike shape and dendrite growth during postembryonic maturation of an identified Drosophila motoneuron. *Eur J Neurosci* 39(10):1572–1585. (NOT accessible — 403; by title the most likely source for the asked-for spike-shape-by-stage data, but I could not read it)
- Huthmacher L et al. (2025) Motoneurons can count: a cell-intrinsic spike number memory compensates for deviations from rate coding. bioRxiv 10.1101/2025.06.16.659928 (preprint, not peer reviewed; read directly, HTML version)
- Gu H, O'Dowd DK (2006) Cholinergic synaptic transmission in adult Drosophila Kenyon cells in situ. *J Neurosci* 26(1):265–272. PMC6674319. (read directly)
- Su H, O'Dowd DK (2003) Fast synaptic currents in Drosophila mushroom body Kenyon cells are mediated by α-bungarotoxin-sensitive nicotinic acetylcholine receptors and picrotoxin-sensitive GABA receptors. *J Neurosci* 23(27):9246–9253. (NOT accessible — 403; secondary summary only)
- Kazama H, Wilson RI (2008) Homeostatic matching and nonlinear amplification at identified central synapses. *Neuron* 58(3):401–413. (NOT accessible — 403; secondary summary only, unconfirmed)
- Gouwens NW, Wilson RI (2009) Signal propagation in Drosophila central neurons. *J Neurosci* 29(19):6239–6249. PMC2709801. (read directly)
- Meier M, Borst A (2019) Extreme compartmentalization in a Drosophila amacrine cell. *Curr Biol* 29(8):1545–1550. (NOT accessible — 403; secondary summary only, unconfirmed)
- Scheffer LK et al. (2020) A connectome and analysis of the adult Drosophila central brain. *eLife* 9:e57443. (read directly, partial — the 15–20% quote was located via search, main text fetch did not independently surface it; moderate confidence)
- Phelps JS et al. (2021) Reconstruction of motor control circuits in adult Drosophila using automated transmission electron microscopy. *Cell* 184(3):759–774. (NOT accessible — 403/size-limited; only indirect search-engine-derived fragments obtained)
- Takemura SY et al. (2024/2025) A connectome of the male Drosophila ventral nerve cord (MANC). *eLife*. (not accessible in the form I tried; no shrinkage statement located)
- male-cns v1.0 release documentation, male-cns.janelia.org (searched; no shrinkage statement located)

## Honesty notes

- Several numbers above are flagged **unverified / secondary-summary only**: I never saw the primary
  sentence myself, only a paraphrase from a web-search tool's own summarization of the page. These
  should not be used as "measured, source cited" without a follow-up direct read.
- Where full text was blocked (mostly journals.physiology.org and cell.com, both of which 403'd every
  attempt), I did not guess or extrapolate numbers — I reported the gap instead.
- No numbers were invented. Anything not explicitly sourced above was not found.
