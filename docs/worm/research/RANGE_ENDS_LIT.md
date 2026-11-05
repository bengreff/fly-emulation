# Range ends: literature check for graded-synapse parameters

Narrowing a few parameter ranges the 302-neuron C. elegans model is sensitive to,
using measured values or tight published bounds where they exist. Every number is
labelled:

- **measured** — read off a real electrophysiology/imaging experiment
- **derived** — arithmetic done here from measured numbers (shown inline)
- **model assumption** — a value chosen by another simulation paper, not measured
- **gap** — not found in this search; not guessed

Search limits hit this session: WebSearch quota was exhausted almost immediately, so
all of this was done via direct fetches of PubMed/PMC/Europe PMC pages and a few
open-access PDFs/GitHub files. Several papers are paywalled or only partly
text-extractable (figures aren't read); those gaps are flagged, not filled.

## 1. Excitatory reversal potential (cholinergic, glutamatergic)

- **Cholinergic (nicotinic + levamisole receptors), body wall muscle**, whole-cell
  patch, dissected worm: Richmond & Jorgensen 1999, *Nat Neurosci* 2:791-797
  (PMC2585773), Fig. 4c — ACh-evoked current reversal **+11 mV (n=4)**, linear fit of
  I-V from -80 to +10 mV steps; holding potential -80 mV used throughout. Levamisole
  current reverses similarly (n=3). **Measured.** Both ACR-16-type and
  UNC-29/UNC-38/LEV-1 levamisole receptors are non-selective cation channels, so a
  reversal near 0 mV is expected on general grounds too, not just this one record.

- **Glutamatergic (GLR-1 AMPA-like), interneuron AVA**, intact worm, ChR2
  optogenetic stimulation of presynaptic ASH + patch clamp: Lindsay, Thiele &
  Lockery 2011, *Nat Commun* 2:306 (PMC3935721), Fig. 6b — synaptic current reversal
  **-7.0 ± 3.2 mV**, matching the reversal of currents evoked by exogenous glutamate
  in dissected AVA ("near 0 mV"). Holding potential -55 mV, steps -80 to +40 mV.
  **Measured.**

- **Gap:** no reversal potential retrieved for ACR-16 in isolation (Francis et al.
  2005, *Neuron* 46:581-594 — paywalled, no PMC copy found) or from Mellem et al.
  2002, *Neuron* (decoding polymodal stimuli — abstract gives no reversal value,
  full text not reachable).

- **Model check:** both measured values (+11 mV, -7 mV) sit inside the model's
  current -10 to +10 mV range, on opposite sides of the 0 mV default. Nothing found
  that requires widening the range; if anything it could tighten to about -10 to
  +15 mV.

## 2. Graded release transfer curve (threshold, slope)

- **AFD -> AIY**, optogenetic depolarization + dual-electrode recording: Narayan,
  Laurent & Sternberg 2011, *PNAS* 108:9667-9672 (PMC3111291) — static synaptic gain
  **0.056 mV postsynaptic per mV presynaptic** (linear regression, R²=0.69, Fig. 4B).
  Postsynaptic potential 3-5 mV and current ~0.5 pA for a 20 ms AFD stimulus.
  Synaptic potential reverses between -20 and 0 mV (Fig. 4D). The authors state they
  "could characterize transfer... only in its linear range; technical and
  biophysical constraints prevented us from measuring threshold and saturation."
  **Measured** (gain only) — threshold/slope explicitly **not measured**.

- **ASH -> AVA**: Lindsay, Thiele & Lockery 2011 (PMC3935721) — response amplitude is
  an "increasing function of stimulus irradiance" with no discontinuities over
  0.07-12.5 mW/mm² (2 log units, Fig. 1a, Fig. 4): smooth, no threshold found. No
  presynaptic-voltage-to-current slope given (irradiance, not voltage, was the
  independent variable). **Measured** (qualitative: graded, no threshold).

- **NMJ (motor neuron -> muscle)**: Liu, Hollopeter & Jorgensen 2009, *PNAS*
  106:10823-10828 (PMC2705609) — "the evoked postsynaptic current scaled with the
  strength of the stimulation"; hyperpolarization reduced tonic release. No
  threshold voltage or sigmoid slope parameter found in the accessible text.
  **Measured** (qualitative: graded only).

- **"RIM graded vs spiking" — name mismatch:** the cited "Liu et al. 2018 Cell"
  could not be located. Closest match: Mellem, Brockie, Madsen & Maricq 2008,
  *Nat Neurosci* 11:865-867 (PMC2697921) — **RMD** (not RIM) shows a
  bistable/regenerative voltage response: linear -80 to -60 mV, then regenerative,
  settling near -10 mV; **AVA** stayed graded, resting -20 to -30 mV, only
  short-lived depolarization to glutamate. Clearest documented graded-vs-spiking
  contrast found, but it's RMD vs AVA, not RIM. **Measured**, citation flagged as a
  mismatch with the task's reference.

- **Model check:** none of the three measured synapses above (AFD-AIY, ASH-AVA,
  NMJ) give a sigmoid threshold or slope in mV — two papers explicitly say it
  couldn't be measured. The model's threshold range (includes -45 mV) and slope
  range (2-10 mV) cannot be checked against data; this is a real gap in the
  literature, not a search failure.

## 3. Per-synapse conductance / quantal size

- **NMJ ACh miniature current (single vesicle)**: Liu, Hollopeter & Jorgensen 2009
  (PMC2705609), Fig. 3E — baseline mEPSC amplitude **17.6 ± 0.9 pA**.
  Derived conductance, using the ACh reversal +11 mV (Richmond & Jorgensen 1999,
  same lab/prep) and -80 mV holding potential (confirmed in the 1999 paper;
  carried over as an assumption here since the 2009 methods defer to an
  inaccessible SI file):
  driving force = -80 - (+11) = **-91 mV**
  g = 17.6 pA / 91 mV ≈ **0.19 nS**. **Derived** (current measured, holding
  potential assumed from the same lab's earlier paper — flagged).

- **NMJ ACh evoked compound current** (many release sites together), same paper,
  Fig. 2C: **2.01 ± 0.11 nA** (electrical stim), **1.96 ± 0.18 nA** (ChR2 light).
  Derived total conductance at the same driving force: 2010 pA / 91 mV ≈ **22 nS**
  — summed over an unconfirmed number of release sites onto the recorded muscle
  cell. No reliable EM-counted contact number per connection was found this
  session (White et al. 1986 / Varshney et al. 2011 would be the source; not
  checked). **Gap** on the per-contact count, not guessed.

- **NMJ GABA evoked compound current**, same paper, Fig. 2B: **1.23 ± 0.12 nA**
  (n=13), decay τ = 24.8 ± 2.7 ms. Conductance **not derived**: GABA-A reversal
  depends heavily on recording-solution Cl- (see item 4), so no safe driving-force
  number exists without knowing their exact solution.

- **Interneuron (AFD -> AIY)**: Narayan et al. 2011 (PMC3111291) — postsynaptic
  current ~0.5 pA for a single 20 ms stimulus, the smallest confirmed graded
  synaptic current found. **Measured.** Not converted to conductance: reversal
  only given as a range (-20 to 0 mV), not a point value.

- **Gap:** no mPSC/evoked-current pA value or EM contact count found specifically
  for AVA-class interneuron synapses.

- **Model check:** derived single-quantum conductance (~0.19 nS) sits near the
  bottom of the model's 0.1-2 nS range. Derived whole-junction evoked conductance
  (~22 nS, many sites) is far above the model's 2 nS ceiling — consistent with
  "per-synapse" in the model meaning one EM contact, not a whole summed NMJ.

## 4. Inhibitory synapses: threshold and reversal

- **GABA-A (UNC-49), body wall muscle**: Richmond & Jorgensen 1999 (PMC2585773),
  Fig. 3c — GABA-evoked current reversal **+17 mV (n=4)**, "close to the predicted
  chloride reversal potential of +24 mV" for their recording solution. Muscimol:
  **+20 mV (n=3)**. Replacing external acetate with chloride shifted the reversal to
  **-10 mV**, "near the predicted reversal potential of -8 mV" — confirms Cl-
  selectivity and that the reversal tracks the experimenter-imposed Cl- gradient,
  not a fixed intrinsic value. **Measured, but solution-dependent** — not the same
  as the native, physiological reversal potential in an intact worm.
  - **Consequence:** the model's inhibitory range includes -45 mV. The only direct
    patch measurement found gives a *positive* reversal (+17 to +20 mV) under an
    imposed Cl- gradient built to produce large currents, not native intracellular
    Cl-. No measurement of native intracellular [Cl-] in a C. elegans neuron or
    muscle (e.g. a Cl--sensitive dye/sensor study) was found this session. **Gap,
    not guessed** — -45 mV cannot be checked against a direct physiological number.

- **GluCl (AVR-14, AVR-15, GLC-1/2/3) and ACh-gated chloride (ACC-1 to ACC-4,
  LGC-46):** reversal potentials **not retrieved**. Dent, Davis & Avery 1997,
  *EMBO J* 16:5867-5879 (avr-15, PMC1170218) and Putrenko, Zakikhani & Dent 2005,
  *J Biol Chem* 280:6392-6398 (ACC-1/ACC-2) establish these channels are
  glutamate/ACh-gated chloride channels (oocyte and pharyngeal muscle recordings),
  but the reversal-potential numbers sit in figures/results not extracted as text
  here (JBC PDF returned HTTP 403). **Gap, not guessed.**

- **Context only (conductance/EC50, not reversal):** a 2023 Cys-loop receptor
  review (*Biophys Rev*, PMC10480131) reports levamisole receptor single-channel
  conductance ~30-35 pS (citing Rayes et al. 2007; Hernando et al. 2012) and UNC-49B
  homomer ~37 pS / UNC-49B+C heteromer ~30 pS (citing Bamber et al. 1999, HEK
  cells), plus EC50 values for ACh, levamisole, GABA, glutamate, ivermectin. No
  reversal potentials in it. **Measured** (secondary source).

- **Model-assumption comparison** (full context in item 5): Wicks, Roehrig & Rankin
  1996 use inhibitory reversal **-48 mV**; c302 parameter set C2 uses **-70 mV**
  (neuron-neuron) and **-35 mV** (neuron-muscle). Both bracket the model's -45 mV,
  but both are modeling choices, not measurements.

## 5. Published model parameter sets (comparison only — none of this is measured)

| Model | Exc. reversal | Inh. reversal | Threshold | Slope | Conductance | Source |
|---|---|---|---|---|---|---|
| Wicks, Roehrig & Rankin 1996 | 0 mV | -48 mV | n/a (uses VEQ) | VRANGE=35 mV (10-90% width), K=-4.3944 | 0.6 nS/synapse | *J Neurosci* 16:4017-4031, Table 1 & Eq. 6 |
| Boyle, Berri & Cohen 2012 (conductance variant) | weight-based, w_ACh=3 | weight-based, w_GABA=-0.5 | V0,NMJ = -22 mV | k_NMJ = 50 mV⁻¹ (≈0.02 mV e-fold; near step) | not conductance-based | *Front Comput Neurosci* 6:10, Eq. 15, Table 2 |
| c302 (Gleeson et al. 2018 framework), set C2 | -10 mV (n-n), +37 mV (n-m) | -70 mV (n-n), -35 mV (n-m) | 0 mV | delta = 5 mV | 0.49/0.10/0.29/1.29 nS (exc n-n/n-m, inh n-n/n-m) | github.com/openworm/c302, `parameters_C2.py`; paper (PMC6158223) describes framework, not these numbers |
| Izquierdo & Beer 2013 (klinotaxis) | evolved, no fixed number | evolved | evolved, no range reported | evolved | n/a (activation-based) | *PLoS Comput Biol* 9:e1002890, Eq. 3; paper states "no measured values... determined solely through evolutionary optimization" |
| Kunert, Shlizerman & Kutz 2014 | not retrieved | not retrieved | not retrieved | not retrieved | not retrieved | *Phys Rev E* 89:052805 — no open-access full text found this session |
| BAAIWorm / MetaWorm 2024 | not found | not found | not found | not found | not found | Could not locate this paper/preprint this session |

The spread between rows (inhibitory reversal -70 to -35 to -48 mV; slope-equivalent
from a near-step 0.02 mV to a broad 35 mV) shows published models disagree with
each other by far more than the measured data above actually constrains — several
of these values were fitted to reproduce behaviour, not read off a recording.

## 6. Proprioceptive gain (stretch receptor current per unit curvature)

- **B-type motor neurons**, closed-loop microfluidic trap + calcium imaging +
  behavior: Wen et al. 2012, *Neuron* 76:750-761 (PMC3508473) — posterior body
  curvature rises linearly with imposed anterior curvature, slope **0.62 ± 0.03**
  (dimensionless curvature-to-curvature gain, Fig. 4C). Spatial extent of coupling
  ~200 µm (Results/Discussion). Propagation delay ~300 ms, roughly constant across
  viscosities tested; limiting delay for transducing a bending signal between
  regions ~80 ms. **Best measured proxy found** — but it's a curvature-to-curvature
  (behavioral) gain, not current-per-curvature (electrophysiological). Fig. 7 of
  the same paper shows B-neuron calcium activity (VB9, DB6) positively correlated
  with curvature direction (p<0.005) but with no numeric slope given in the text.
  **Measured**, units mismatch with what the model needs flagged.

- **DVA (TRP-4)**: Li, Feng, Sternberg & Xu 2006, *Nature* 440:684-687
  (PMC2865900) — establishes TRP-4 mediates a DVA stretch response via calcium
  imaging and posture phenotypes; no patch-clamp recording of the current itself.
  **Gap, not guessed.**

- **SMDD (TRP-1/TRP-2)**: Yeon et al. 2018, *PLoS Biol* 16:e2004929 (PMC6010301) —
  SMDD stretch-sensing and steering control confirmed; calcium activity correlates
  with head-bending direction (Fig. 2A-B) but no numeric dF/F-per-angle slope was
  retrievable from the extracted text (likely only in supplementary data).
  **Gap, not guessed.**

- Fouad et al. 2018, *eLife* 7:e29913 (PMC5780042) confirms B-neurons sense
  curvature and propagate bending posteriorly, but cites Wen 2012 and Boyle 2012
  for the quantitative feedback model rather than reporting a new number itself.

- **Model check:** no value was found in the units the model needs (current per
  unit curvature). Wen et al. 2012's 0.62 ± 0.03 curvature-to-curvature gain is the
  best cited range available and should be read as a rough behavioral anchor, not
  a direct substitute for the electrophysiological parameter.

## Summary table

| Parameter | Model range now | Best literature value/range | Label | Source | Moves default? |
|---|---|---|---|---|---|
| Excitatory reversal, cholinergic | -10 to +10 mV (default 0) | +11 mV | measured | Richmond & Jorgensen 1999, Fig. 4c | No — inside range |
| Excitatory reversal, glutamatergic | -10 to +10 mV (default 0) | -7.0 ± 3.2 mV | measured | Lindsay et al. 2011, Fig. 6b | No — inside range; suggests default could sit slightly negative of 0 rather than at 0 |
| Graded release threshold | includes -45 mV | not measured (3 papers checked, 2 say unmeasurable) | gap | Narayan 2011; Lindsay 2011; Liu 2009 | Can't confirm or rule out |
| Graded release slope | 2-10 mV | not measured; published models span 0.02-35 mV equivalent | gap (measured) / model assumption (comparison) | Wicks 1996; Boyle 2012; c302 | Can't confirm from data; model literature disagrees by >100x, so 2-10 mV is not obviously wrong but is unconstrained |
| Per-synapse conductance | 0.1-2 nS | ~0.19 nS (single quantum, NMJ ACh) | derived | Liu 2009 Fig. 3E + Richmond & Jorgensen 1999 Fig. 4c | No — bottom of range looks right for a single release event |
| Inhibitory reversal | includes -45 mV | +17 to +20 mV measured (solution-dependent, not physiological); native intracellular Cl- unmeasured | measured (caveat) / gap (physiological value) | Richmond & Jorgensen 1999, Fig. 3c | Can't confirm -45 mV; the only direct measurement has the opposite sign under an artificial Cl- gradient |
| Inhibitory threshold | includes -45 mV | not measured | gap | — | Can't confirm |
| Proprioceptive gain | model-specific units (current/curvature) | 0.62 ± 0.03 (curvature-to-curvature, dimensionless) | measured, different units | Wen et al. 2012, Fig. 4C | Units mismatch — use only as a rough behavioral anchor, not a direct substitute |
