# Neural mechanisms: published models to port, not invent

Research note, not canon. Compiled 2026-11-06 for the "port, don't build" rule (STRATEGY.md /
PLAN.md c.1). Scope: the 10 neural mechanisms named in the task brief (N1-N10), each tied to a
PLAN.md/MECHANISMS_AUDIT.md row. Read first and cited rather than repeated: `MECHANISMS_AUDIT.md`
(rows 1-23, what the code does today), `PLAN.md` section a (what each row should be),
`research/NEUROPEPTIDES.md` (rows 9-10), `research/GENES_TO_PHYSIOLOGY.md` (rows 3, 5, channel
density structure), `research/RHYTHM_LIT.md` (rhythm generation, AVA/AVB switching, section 2 is
directly useful for N2/N3 context), `research/RANGE_ENDS_LIT.md` (row 7 receptor reversal
potentials and conductances), `STATE_OF_THE_ART.md` (data by layer, behaviour corpus).

Labels follow project convention: **measured** (read off a cited primary source), **derived**
(arithmetic shown), **inferred** (reasoned from a source, e.g. homology), **guessed** (estimate
with no direct basis, bounded and reasoned). UNVERIFIED marks anything this pass could not confirm
by opening the source.

## Summary table

| # | Mechanism | Model(s) to port | Open code | Confidence |
|---|---|---|---|---|
| N1 | Receptor-class synaptic kinetics | Per-class EC50/conductance/tau from Cys-loop review PMC10480131 + Bamber 2005 + Liu 2009 + Lindsay 2011; no single ODE-form paper | No runnable code found; parameter table only | Medium (several classes solid; ACC/LGC-35/EXP-1/GLR-1/NMR-1 point values missing) |
| N2 | Short-term plasticity / habituation | Wicks 1996 circuit (no plasticity) + Tsodyks-Markram depression fit to Liu 2009 NMJ taus + Rose/Rankin ISI plateaus | None | Low-Medium (mechanism form is standard; worm-specific touch-circuit numbers are secondary-source only) |
| N3 | Learning substrates | No ported ODE model for any of the 5 paradigms; shared slow-associative-state structure proposed | None | Low (gene identity solid; kinetics absent across the board) |
| N4 | Neuropeptide/monoamine GPCR signalling | Defers to NEUROPEPTIDES.md; this pass only reconfirms its gaps (diffusion, degradation, release rate, per-pair coupling) | None (as NEUROPEPTIDES.md found) | Low (unchanged from NEUROPEPTIDES.md) |
| N5 | Sensory transduction cascades | AWA: Liu 2018 Ca-spike HH model (solid). Touch: Sanzeni 2019 3-state gating (solid structure, some constants unextracted). AWC: Usuyama 2012 full ODE (fit-not-measured). AFD/ASE/ASH/O2/CO2/light/proprio: gene identity only | None confirmed runnable | High for AWA; Medium for touch/AWC; Low for the rest |
| N6 | Slow intracellular signalling | EGL-4 (hours, measured induction time) and CMK-1 (2-3 min / 3-5 h split, measured) as two first-order relaxations; GLR-1/insulin/DAF-7/CREB not opened this pass | None | Medium (EGL-4, CMK-1); Low (rest) |
| N7 | Activity-dependent homeostatic channel tuning | O'Leary 2013 calcium-sensor rule (generic) + 2024 UNC-2/WWP-1 self-tuning (worm-specific, measured thresholds) | Not confirmed for either | Medium (qualitative rule and two time thresholds measured; gains/filters not extracted) |
| N8 | Temperature (Q10) | No C. elegans-specific Q10 for channels/synapses found; defecation clock Q10~1 measured; generic 1.5-3 bound elsewhere | n/a | Low |
| N9 | Channel/synaptic noise | Generic Poisson/shot-noise mechanism, parameterised entirely from Liu 2009 NMJ mini-rate/amplitude data (solid) | None | Medium-High (NMJ numbers solid; no non-NMJ synapse noise data) |
| N10 | Sleep circuits (RIS, ALA) | No quantitative model found; FLP-11/DMSR-1 qualitative coupling only (from NEUROPEPTIDES.md) | None | Low (thinnest section in this document) |

(Table filled in as each section completes; this header stays first so partial work is visible.)

## Section list

- N1. Chemical synapse receptor classes: kinetics, reversal, conductance
- N2. Short-term synaptic plasticity and habituation
- N3. Learning substrates (salt, thermotaxis, butanone, pathogen, NMDA LTM)
- N4. Neuropeptide and monoamine GPCR signalling (gaps beyond NEUROPEPTIDES.md)
- N5. Sensory transduction cascades per modality
- N6. Slow intracellular signalling that carries state
- N7. Activity-dependent gene expression / homeostatic channel density
- N8. Temperature dependence (Q10)
- N9. Noise (channel, synaptic release)
- N10. Sleep circuits (RIS/FLP-11, ALA/FLP-13/FLP-24/NLP-8)

---

## N1. Chemical synapse receptor classes: kinetics, reversal, release

**Context.** MECHANISMS_AUDIT.md row 7: today the code has exactly two synapse types (one
excitatory, one inhibitory template), same unit conductance (0.447 nS per EM contact) for every
pair, no receptor-class kinetics. PLAN.md row 7 wants per (transmitter, receptor class) unit
conductance and release curve. RANGE_ENDS_LIT.md already pinned reversal potentials (ACh +11 mV,
Glu -7.0+-3.2 mV, GABA-A solution-dependent +17 to +20 mV with the physiological value unmeasured)
and a derived NMJ quantal conductance (~0.19 nS). This section adds the receptor-class kinetics,
EC50s, and the graded-release models RANGE_ENDS_LIT.md flagged as needed but did not extract.

### (a) Models to port, by receptor class

No single paper gives a "model to port" in the sense of a published differential-equation gating
scheme for every worm receptor (unlike the channel library in `nicoletti.py`). What exists is
electrophysiology (EC50, conductance, desensitization time constant) from heterologous expression
(Xenopus oocytes, HEK cells) and native muscle/neuron recordings, which bounds a standard
two-state or three-state ligand-gated-channel kinetic scheme (open/closed, or open/closed/
desensitized), the same scheme already used for the project's voltage-gated channels. The single
best-organised secondary source, opened this pass, that already collects most of these numbers in
one place with primary citations is:

**Rayes, Rufener, Clark, Alonso, Peden, Alfonso et al. (named by abstract/author
pattern in the fetched review), compiled in: "The diverse family of Cys-loop receptors in
Caenorhabditis elegans: insights from electrophysiological studies," *Invertebrate Neuroscience /
J. Vet. Pharmacol* review, PMC10480131 (2023), https://pmc.ncbi.nlm.nih.gov/articles/PMC10480131/**
(opened; review, not primary data, but every number below traces to a primary citation inside it
that was spot-checked where flagged). Use this review's Table 1 as the parameter source table, and
go to its cited primaries (Rayes et al. 2007, Hernando et al. 2012, Boulin et al. 2008, Bamber et
al. 1999/2005, Dent/Avery/Davis family of papers) for anything a builder needs reaction-level
detail on.

Secondary primaries opened directly this pass:
- Bamber et al. 2005, *Br J Pharmacol* 144:502, "The composition of the GABA receptor at the C.
  elegans neuromuscular junction" (PMC1576029, opened) — UNC-49B vs UNC-49B/C EC50 and
  desensitization tau.
- Beg & Jorgensen 2003, *Nat Neurosci* 6:1145, "EXP-1 is an excitatory GABA-gated cation channel"
  (found via PubMed 14555952; full kinetic numbers not extracted this pass, see gaps below).
- Liu, Hollopeter & Jorgensen 2009, *PNAS* 106:10823 (PMC2705609, opened) — graded release,
  synaptic depression time constants, mEPSC frequency (NMJ).
- Lindsay, Thiele & Lockery 2011, *Nat Commun* 2:306 (PMC3935721, opened) — ASH->AVA graded
  synapse, AVA passive properties.
- Narayan, Laurent & Sternberg 2011, *PNAS* 108:9667 (PMC3111291, already opened for
  RANGE_ENDS_LIT.md) — AFD->AIY linear transfer gain, the cleanest graded-release transfer-curve
  number in the whole literature for this animal.

### (b) Open code

None found for a receptor-class-resolved kinetic scheme. c302 (github.com/openworm/c302, MIT) ships
single-exponential synapse objects per `parameters_C2.py` with one reversal/conductance per
(pre-type, post-type) pair, not per receptor gene — already ported and run by this project
(`c302_port.md`), and already found to saturate rather than oscillate (RHYTHM_LIT.md). It is usable
as a code skeleton (the NeuroML `GradedSynapse`/`blocking_plastic_synapse` ComponentTypes in
`c302`/`libNeuroML`), not as a source of correct parameter values. No repository with the
heterologous EC50/conductance numbers wired into runnable channel code was found. **State: no
ready-to-run code found; port the parameter table into the project's own two-state/three-state
ligand-gated kinetic scheme (the same ODE form already used for voltage-gated channels in
`nicoletti.py`, with voltage replaced by bound ligand concentration).**

### (c) State variables and equations (plain text)

Standard form for every ionotropic receptor class below (2-state, add desensitization as a 3rd
state only for the classes flagged "biexponential desensitization"):

- State `r` (fraction of channels open), `d` (fraction desensitized, 3-state classes only).
- Instantaneous agonist concentration `[A]` at the cleft (from the presynaptic release model,
  section below).
- Hill-form steady-state activation: `r_inf([A]) = [A]^n / ([A]^n + EC50^n)`, n = Hill coefficient
  (given per class below; use n=1 where not reported).
- `dr/dt = (r_inf([A]) - r) / tau_act` where `tau_act` is fast (sub-ms to low ms, not separately
  reported for most worm receptors; bound it near the fastest resolvable time constant in each
  paper's clamp, typically <= 1-2 ms, UNVERIFIED point value, inferred from clamp rise times in the
  cited papers) for ionotropic classes, and the paper's desensitization tau for the `d` state in
  3-state classes: `dd/dt = (d_inf(r) - d) / tau_desens`.
- Current: `I = g_unit * N_channels * r * (1-d) * (V - E_rev)`, g_unit = single-channel or derived
  unit conductance (per class, below), E_rev = reversal potential (RANGE_ENDS_LIT.md section 1/4
  plus below).
- Graded presynaptic release ([A] as a function of presynaptic voltage V_pre): the only two worm
  synapses with a measured transfer function are AFD->AIY (linear, no saturation measured) and the
  NMJ (monotonic/approximately linear over the tested range, no sigmoid fit published). Use
  `[A](V_pre) = k * max(0, V_pre - V_rest)` (linear, no threshold) as the simplest nested form
  (section f) unless/until a sigmoid is independently justified; this is consistent with both
  measured transfer curves and with PLAN.md's existing sigmoid release model, which this makes
  into a limiting case (k constant, no saturation) rather than a different structure.

### (d) Parameter table

| Receptor class | Genes | Ligand | EC50 | Hill n | Conductance | Desensitization tau | Reversal | Native/heterologous | Source | Label |
|---|---|---|---|---|---|---|---|---|---|---|
| Levamisole-type nAChR (L-AChR) | UNC-29/UNC-38/UNC-63/LEV-8(+LEV-1 in some combos) | ACh | 26 uM | UNVERIFIED | 30-35 pS | "very slow," no decay during agonist pulse (Boulin 2008) | +11 mV (native muscle, Richmond & Jorgensen 1999) | heterologous (oocyte) EC50/conductance; native reversal | Boulin 2008 (EC50), Rayes 2007/Hernando 2012 (conductance), both via PMC10480131; Richmond & Jorgensen 1999 (reversal) | measured |
| Levamisole-type, LEV-1 variant | as above minus LEV-8/with LEV-1 | ACh | similar range | - | ~26 pS | not given | as above | heterologous | Rayes 2007 via PMC10480131 | measured |
| ACR-16 homomeric nAChR (N-AChR) | ACR-16 (+RIC-3 for expression) | ACh | 55 uM | UNVERIFIED | not separately given (muscle compound current 285+-25 pA in acr-16(+) background; see note) | decays ~40x faster than L-AChR, "insignificant steady state," full desensitization | +11 mV (shared ACh reversal, non-selective cation channel; not separately measured for ACR-16 alone) | heterologous (oocyte, needs RIC-3) | PMC10480131 Table 1; Touroutine 2005 JBC (acr-16 essential subunit paper) | measured (EC50, kinetics qualitative) / inferred (reversal, by channel-class homology) |
| ACC-type ACh-gated Cl | ACC-1/ACC-2/ACC-3/ACC-4, LGC-46 | ACh | not retrieved this pass | - | not retrieved | not retrieved | not retrieved (Cl-selective, so expect similar sign issue to UNC-49 below) | oocyte/pharyngeal muscle (Putrenko 2005) | Putrenko, Zakikhani & Dent 2005, JBC 280:6392 (RANGE_ENDS_LIT.md item 4; JBC PDF 403'd both passes) | UNVERIFIED — flagged gap in RANGE_ENDS_LIT.md too |
| GLR-1/GLR-2 AMPA-like | glr-1, glr-2 (+SOL-1, STG-1 auxiliary for reconstitution) | glutamate | not retrieved as a point EC50 this pass | - | not retrieved | fast activation, fast desensitization (SOL-1 slows and limits desensitization extent; Q/Y pore mutant used experimentally to suppress desensitization) | -7.0+-3.2 mV (native, AVA, Lindsay 2011) | native (AVA, Lindsay 2011) for reversal; heterologous (oocyte, +SOL-1+STG-1) for reconstitution/kinetics | Lindsay 2011 (reversal); Zheng 2006 PNAS "Reconstitution of invertebrate glutamate receptor function depends on stargazin-like proteins" (reconstitution); Walker/Francis/Maricq SOL-1 papers (kinetics, qualitative) | measured (reversal) / UNVERIFIED (EC50, decay tau point values) |
| NMR-1/NMR-2 NMDA-like | nmr-1, nmr-2 (heteromeric) | glutamate | not retrieved as point value | - | not retrieved | "slow," contributes a small, slowly-desensitizing current component distinct from the fast AMPA-like component in the same AVA recording | not separately resolved from the fast component in the same traces (Mellem 2002); by homology to glutamate reversal, near 0 mV | native (AVA, Brockie et al. 2001 Neuron 31:617) | Brockie, Madsen, Zheng, Mellem & Maricq 2001, Neuron 31:617 (PMC/warwick copy fetched but not machine-readable this pass; cite with figure numbers UNVERIFIED) | measured (qualitative slow-component existence) / UNVERIFIED (point tau, EC50) |
| GluCl (glutamate-gated Cl): AVR-14, AVR-15, GLC-1/2/3 | avr-14, avr-15, glc-1/2/3 | glutamate (native ligand) / ivermectin (pharmacology) | AVR-14B 10000 uM (glu), 10 uM (iverm); AVR-15A 2000 uM (glu), 10 uM (iverm); AVR-15B 208 uM (glu), 0.107 uM (iverm); AVR-15B/GLC-2 62 uM (glu), 0.103 uM (iverm); GLC-1 0.14 uM (iverm); GLC-2 380 uM (glu); GLC-1/GLC-2 1360 uM (glu); GLC-3 1900 uM (glu), 0.4 uM (iverm) | UNVERIFIED per-subtype | not retrieved | not retrieved | Cl-selective; expect near E_Cl, i.e. hyperpolarizing (no point value found this pass, same gap as UNC-49 below) | heterologous (oocyte) | PMC10480131 Table 1, citing Dent/Avery/Davis-lineage papers (Dent 1997 EMBO J for avr-15, Cully 1994 for related GluCls) | measured (EC50s) / gap (reversal, conductance) |
| UNC-49 GABA-A | unc-49b, unc-49b/c heteromer | GABA | 8.6 uM (B homomer, Bamber 2005) or 43 uM (Table 1, different prep); 19.6 uM (B/C, Bamber 2005) or 107 uM (Table 1) — **two sources disagree by 2-5x, flag before use** | 2.0 (B homomer, Bamber 2005); 1.3 (B/C) | 37 pS (B homomer); ~30 pS (B/C, 20% less than B) | biexponential; slow component 206+-26 ms (B homomer), 149+-10 ms (B/C, p<0.05), slow component carries 91-95% of weighted tau | +17 to +20 mV under imposed Cl- gradient (Richmond & Jorgensen 1999); physiological native reversal not measured (RANGE_ENDS_LIT.md item 4, unresolved gap) | heterologous (HEK, Bamber 2005) for EC50/tau/conductance; native (muscle) for reversal under imposed solution | Bamber et al. 2005, PMC1576029 (opened); Bamber et al. 1999 (conductance); Richmond & Jorgensen 1999 (reversal) | measured, with the EC50 discrepancy flagged / gap (physiological reversal) |
| LGC-35 | lgc-35 | UNVERIFIED ligand/role in this pass (listed in task as a GABA/Cl-family gene; no electrophysiology retrieved) | - | - | - | - | - | - | not found this pass | UNVERIFIED — treat as a gap, not guessed |
| MOD-1 serotonin-gated Cl | mod-1 | serotonin | 1 uM; tryptamine 47 uM | UNVERIFIED | not retrieved | desensitizes during sustained agonist, recovers rapidly off agonist (qualitative; no tau retrieved) | Cl-selective, hyperpolarizing by channel class; no point reversal retrieved | heterologous (oocyte) | PMC10480131 Table 1, citing Rodriguez Araujo et al. 2022 | measured (EC50) / gap (tau, reversal) |
| EXP-1 GABA-gated cation (excitatory) | exp-1 | GABA | not retrieved this pass | - | not retrieved | not retrieved | depolarizing/cation-selective by design (the one GABA-gated channel in the genome that is NOT anion-selective) | heterologous (Xenopus oocyte, Beg & Jorgensen 2003) | Beg & Jorgensen 2003, Nat Neurosci 6:1145 (found via PubMed/ResearchGate, full numeric table not extracted this pass) | measured (qualitative cation selectivity) / UNVERIFIED (EC50, conductance, tau) |

Graded release / presynaptic transfer, separate from the postsynaptic receptor table above:

| Quantity | Value | Cells | Source | Label |
|---|---|---|---|---|
| Transfer gain, AFD->AIY | 0.056 mV postsynaptic per mV presynaptic (linear, R^2=0.69); PSC ~0.5 pA for 20 ms stimulus | AFD (presyn) -> AIY (postsyn) | Narayan et al. 2011 PNAS, PMC3111291, Fig. 4B | measured |
| NMJ quantal conductance | ~0.19 nS (derived: 17.6+-0.9 pA mEPSC / 91 mV driving force) | motor neuron -> body wall muscle | Liu, Hollopeter & Jorgensen 2009 Fig. 3E + Richmond & Jorgensen 1999 (driving force) | derived |
| NMJ baseline mEPSC (mini) rate | 26.3+-5.4 events/s (falls to 10.2+-3.1 during halorhodopsin hyperpolarization, recovers to 35.3+-5.5 after) | motor neuron -> muscle | Liu et al. 2009, PMC2705609 | measured |
| ACh release depression tau vs stimulation frequency | 0.2 Hz: tau=4.71+-1.24 s; 1 Hz: tau=0.58+-0.11 s; 5 Hz: tau=0.09+-0.02 s | motor neuron -> muscle | Liu et al. 2009, PMC2705609 | measured |
| ASH->AVA graded transfer | monotonic, no threshold over 0.07-12.5 mW/mm^2 irradiance (2 log units); AVA Cm 0.53+-0.02 pF, AVA membrane tau 0.85+-0.03 ms | ASH -> AVA | Lindsay, Thiele & Lockery 2011, PMC3935721 | measured |

### (e) Cells/classes it applies to

Levamisole-type and ACR-16: body-wall muscle (NMJ, all 95 cells) and cholinergic neuron-neuron
synapses generally (CeNGEN presence per class should gate which). ACC-type: pharyngeal muscle and
some neuron-neuron ACh synapses that are inhibitory (sign flips from excitatory ACh to inhibitory
via this Cl-permeant receptor — this is the molecular candidate RHYTHM_LIT.md section 2 flags for
the "cholinergic but inhibitory" AVA<->AVB synapse). GLR-1/GLR-2, NMR-1/NMR-2: interneurons
downstream of glutamatergic sensory neurons (AVA is the best-characterised postsynaptic cell for
both). GluCl family: pharyngeal and body-wall muscle plus some interneurons (receptor for
ivermectin pharmacology as well as native glutamate signalling). UNC-49: body-wall muscle (D-type
motor neuron targets) and some neuron-neuron GABA synapses. MOD-1: AIY, RIF, ASI (serotonin
targets per NEUROPEPTIDES.md table). EXP-1: enteric muscle only (AVL/DVB inputs, defecation
circuit, row 14).

### (f) Simplest nested form

Instantaneous gating: drop `tau_act` and `tau_desens` to zero, i.e. `r = r_inf([A])`, `d = 0`
(no desensitization). This collapses every class to a static Hill-function conductance, which is
exactly the model the current code already runs (one sigmoid per sign class) except with the
correct per-class EC50/Hill-n/conductance/reversal substituted in place of the single shared
template value. This is the natural first step: keep the current two-sign-class structure, swap
in per-class EC50 and reversal, and only add the explicit `r`/`d` states (full form) for classes
where RHYTHM_LIT.md or a fit shows the instantaneous form fails (the AVA<->AVB sign/asymmetry
problem is a reversal-and-strength issue, not obviously a kinetics issue, so instantaneous gating
is a reasonable starting nested form even there).

### (g) Isolated check

UNC-49: apply a step of GABA at saturating concentration in the model's synapse code and confirm
the simulated current decays biexponentially with slow-component tau within 10% of 206 ms (B
homomer) or 149 ms (B/C heteromer) (Bamber et al. 2005) — a unit check on the desensitization
state alone, no network needed. ACR-16 vs L-AChR: apply the same ACh step to both receptor models
and confirm ACR-16's current decays roughly 40x faster than L-AChR's near-flat response, matching
the qualitative "insignificant steady-state current" vs "no decay during the pulse" contrast
(PMC10480131). NMJ release: drive the model's presynaptic release stage with a train at 0.2, 1 and
5 Hz and confirm the modelled EPSC depresses with tau near 4.71 s, 0.58 s and 0.09 s respectively
(Liu et al. 2009) — this is the single most load-bearing isolated check in this section because it
is the only three-point frequency-dependence curve in the whole dataset.

**Gaps flagged UNVERIFIED, not guessed:** ACC-type reversal/conductance/EC50 (paywalled JBC PDF,
403 both passes), LGC-35 (nothing found), EXP-1 numeric kinetics (paper identified, numbers not
extracted), GLR-1/NMR-1 point EC50 and decay tau (qualitative only), native UNC-49 physiological
reversal (same gap RANGE_ENDS_LIT.md already flagged), and the UNC-49 EC50 discrepancy between
Bamber 2005 (8.6/19.6 uM) and the review's Table 1 (43/107 uM) — likely different GABA application
methods (steady-state dose-response vs rapid-exchange), needs the primary Table 1 source checked
before picking one.

---

## N2. Short-term synaptic plasticity and habituation

**Context.** No row in MECHANISMS_AUDIT.md covers this directly; it sits under row 7 (synapses,
today static) and is needed for behaviour-corpus items 15-17 (tap-withdrawal habituation,
long-term habituation, response-vs-ISI curve). PLAN.md section c.2's L5/L6 losses are the fitting
targets.

### (a) Models to port

**No single published model ports cleanly end to end.** Two pieces exist, from different levels,
and have to be combined rather than taken from one source:

1. **Wicks, Roehrig & Rankin 1996, *J Neurosci* 16:4017-4031** (opened, PMC6578605,
   https://pmc.ncbi.nlm.nih.gov/articles/PMC6578605/) is the published, circuit-scale
   tap-withdrawal model (already partly documented in RANGE_ENDS_LIT.md section 5: graded
   sigmoid synapse, `g_inf(V_pre) = gbar / (1 + exp(K*(V_pre - V_eq)/V_range))`, gbar=0.6 nS,
   V_range=35 mV, K=-4.3944, E_exc=0 mV, E_inh=-48 mV). Confirmed this pass, by direct fetch: **this
   model has no depression or facilitation state at all** — the paper's own text says synapses are
   "instantaneous" ligand-gated channels, and the paper explicitly did not model habituation (it
   models one single tap response, not the decrement over repeated taps). So it is the right
   circuit skeleton (polarity, wiring, sigmoid synapse shape) but contributes nothing to the
   plasticity mechanism itself.
2. **The habituation decrement itself** is behaviourally characterised in Rankin, Beck & Chiba
   1990 (*Behav Neural Biol* 48:1, cited via STATE_OF_THE_ART.md item 15) and reviewed in Rose &
   Rankin 2001, *Learn Mem* 8:63 (https://learnmem.cshlp.org/content/8/2/63.full.html; PDF 403'd
   this pass, HTML version not separately re-fetched for lack of time, flagged). A webpage-indexed
   figure summary (not independently re-verified against the primary paper's own numbers in this
   pass, so treat as **reported**, one step below measured) gives the clearest quantitative anchor
   found: EPSP depression at the touch/interneuron synapse habituates to a **plateau at 36% of
   control amplitude** with a 1 s inter-stimulus interval (fast, large decrement), vs a shallower
   **65% of control by the 10th stimulus** at a 100 s inter-stimulus interval (slow, small
   decrement). This is the ISI-dependence any ported depression mechanism has to reproduce; no
   primary-source time-constant fit to this curve was retrieved this pass (**gap, not guessed**).

**Nearest quantitative port for the depression mechanism's dynamics (not from the tap circuit, but
the only real C. elegans release-depression numbers with time constants this pass found):** Liu,
Hollopeter & Jorgensen 2009 PNAS (already opened for N1), who measured ACh release depression at
the NMJ directly, at three stimulation frequencies, with time constants (table in N1,
repeated here for convenience): 0.2 Hz tau=4.71+-1.24 s, 1 Hz tau=0.58+-0.11 s, 5 Hz tau=0.09+-0.02
s. This is presynaptic vesicle-pool depression at a different synapse (NMJ, not touch-cell to
interneuron), so porting it to the tap-withdrawal circuit is a mechanism transplant (same
C. elegans presynaptic release machinery, UNC-13/UNC-18/RAB-3, is used throughout the cholinergic
nervous system, so the qualitative form, strong frequency dependence of recovery tau, is a
reasonable inferred prior), not a direct measurement of the touch circuit itself — label
accordingly below.

### (b) Open code

None found specifically implementing C. elegans synaptic depression with the measured parameters.
Generic short-term-plasticity code (Tsodyks-Markram, Dittman-Regehr) is standard and available in
NEURON/Brian2/Jaxley-compatible form (not worm-specific). **State: no worm-parameterised code
found; port the generic Tsodyks-Markram release-probability depression equation, fit to the Liu
2009 NMJ time constants as a starting point, then refit to Rose & Rankin's ISI-dependent plateau
numbers once the touch circuit is wired.**

### (c) State variables and equations

Standard single-pool depression (Tsodyks-Markram form), one state per presynaptic terminal:
- State `R` (fraction of readily releasable resource available, 0-1, starts at 1).
- On each presynaptic release event (spike or graded release crossing a threshold): `R -> R*(1-U)`,
  U = release fraction per event (fit; bounded 0-1).
- Between events: `dR/dt = (1-R)/tau_rec`, tau_rec = recovery time constant (frequency-dependent
  per the Liu 2009 numbers above, so tau_rec itself may need to be modelled as decreasing with
  recent activity, not a single constant, to reproduce the 40-50x spread between 0.2 Hz and 5 Hz
  values; the simplest version uses the single tau closest to the circuit's natural firing rate
  and accepts error at other rates — see nested form below).
- Effective release / postsynaptic drive: `[A]_effective = [A]_nominal * R` (the graded-release
  transfer function from N1, scaled by the depression state).
- Habituation at the behavioural level is this depression state propagated through the already-
  wired tap-withdrawal circuit (PLC/PVD/ALM/AVM touch cells -> AVA/AVD/AVB/PVC interneurons -> motor
  neurons), so no separate "habituation module" is needed once each relevant synapse carries this
  state; the behavioural decrement is an emergent circuit property of per-synapse depression plus
  circuit integration, consistent with Wicks & Rankin's own stated circuit-first philosophy even
  though their published model itself omitted the depression term.

### (d) Parameter table

| Parameter | Value | Range | Units | Source | Label |
|---|---|---|---|---|---|
| Release depression tau, low frequency (0.2 Hz train) | 4.71 | +-1.24 | s | Liu et al. 2009, PMC2705609, NMJ | measured (different synapse, inferred transplant) |
| Release depression tau, mid frequency (1 Hz train) | 0.58 | +-0.11 | s | Liu et al. 2009, NMJ | measured (different synapse, inferred transplant) |
| Release depression tau, high frequency (5 Hz train) | 0.09 | +-0.02 | s | Liu et al. 2009, NMJ | measured (different synapse, inferred transplant) |
| EPSP depression plateau, touch circuit, ISI 1 s | 0.36 of control | not given | fraction | web-indexed figure summary of Rankin-lineage data, **reported**, not independently re-verified against the primary paper this pass | reported (one step below measured; re-verify before fitting) |
| EPSP depression plateau, touch circuit, ISI 100 s (by 10th stimulus) | 0.65 of control | not given | fraction | same source | reported |
| Wicks 1996 static synapse: gbar | 0.6 | not given | nS | Wicks, Roehrig & Rankin 1996, PMC6578605 | measured (model-fit, not patch value; same table already in RANGE_ENDS_LIT.md section 5) |
| Wicks 1996 static synapse: V_range, K, E_exc, E_inh | 35 mV, -4.3944, 0 mV, -48 mV | — | mV, dimensionless, mV, mV | same | model assumption (fitted to behaviour, not measured) |
| Release fraction per event, U (Tsodyks-Markram) | not measured for any C. elegans synapse | 0.1-0.5 (generic invertebrate central synapse range) | fraction | no C. elegans point value found this pass | guessed (bounded by generic invertebrate central-synapse literature, reasoning: worm synapses are small, few vesicles per release site per the EM counts in RANGE_ENDS_LIT.md item 3, which argues for higher-than-cortical U, hence the upper half of the generic range rather than the lower) |

### (e) Cells/classes it applies to

Primary target: the tap-withdrawal circuit (PLM/PVD/ALM/AVM sensory neurons -> AVA, AVD, AVB, PVC
interneurons -> A/B-type motor neurons), corpus items 15-17. By the same mechanism transplant
logic, any cholinergic or glutamatergic synapse in the connectome can carry this state (UNC-13-
dependent depression is a general presynaptic property, not touch-circuit-specific), but fitting
should start with the touch circuit since that is where the behavioural target (Rose & Rankin
plateaus) exists.

### (f) Simplest nested form

Set `tau_rec -> 0` (instant recovery): `R == 1` always, release is never depressed, which collapses
to the current code's static synapse (and to Wicks 1996's own published model exactly). This is the
right null/control model for the pre-registered falsifier PLAN.md DECISIONS item 2 requires: a
model with depression off should fail to reproduce the measured ISI-dependent plateau (flat
response to repeated taps, no decrement), which is the required "wrong model that must fail."

### (g) Isolated check

Drive a single modelled presynaptic terminal with a periodic pulse train at 1 Hz and at 100 s
inter-pulse interval (two separate runs) and confirm the modelled EPSC plateaus near 36% and 65%
of the first-pulse amplitude respectively (Rose & Rankin review numbers, re-verify against the
primary Rankin 1990/Rankin & Broster source before trusting the exact percentages). This is a
single-synapse unit check, no circuit needed, and is exactly the kind of check this project's
"port, don't build" rule asks for: it isolates the depression mechanism from the wiring question.

**Gap flagged:** no primary-source time constant for the touch-circuit depression curve itself was
retrieved this pass (only a secondary percentage-plateau summary); before fitting, re-derive the
36%/65% numbers directly from Rankin, Beck & Chiba 1990 or Rose & Rankin 2001's own figures, not
from the secondary summary used here.

---

## N3. Learning substrates

**Context.** MECHANISMS_AUDIT.md row 18: only an AWC odour gain drift is implemented, never run.
Corpus items 61-65 (salt learning, NMDA LTM, thermotaxis learning, chemosensory adaptation,
pathogen learning). Given the time budget this section is kept brief; each entry names the
minimal state-variable model and the clearest numeric anchor found, with gaps flagged rather than
filled.

| Paradigm | Cells/genes | Model to port | State variables | Numbers found | Label |
|---|---|---|---|---|---|
| Salt chemotaxis learning (salt+starvation -> aversion) | ASER, DAG/PKC-1, INS-1/DAF-2 | No single ported ODE model found this pass. Mechanistic sketch from the gene names (Tomioka et al., Hukema et al., reviewed STATE_OF_THE_ART.md item 61): starvation during salt exposure recruits INS-1 release from ASER itself (autocrine), acting through DAF-2/PI3K to shift ASER's postsynaptic sign (bidirectional valence switch), with PKC-1/DAG as a parallel potentiation arm. | one "association strength"/synaptic-weight state per (salt, feeding-state) pair, updated slowly (minutes, matching training duration in the classic protocol: 1 h starved+salt pairing) | Training duration ~1 h is the only quantitative parameter confirmed this pass (classic protocol, STATE_OF_THE_ART.md item 61 citation); no fitted time constant or learning rate retrieved | UNVERIFIED (mechanism identity measured by genetics; kinetic parameters not found) |
| NMDA-dependent long-term memory (salt learning) | NMR-1/NMR-2 | Kano et al., *Curr Biol* (cited STATE_OF_THE_ART.md item 62) establishes nmr-1 is required for memory retention beyond short-term (minutes) but not for short-term learning itself — a two-timescale (fast NMDA-independent, slow NMDA-dependent) model is the right minimal structure, directly analogous to vertebrate early-LTP/late-LTP, by the authors' own framing | fast trace (minutes, NMDA-independent) + slow trace (hours, NMDA-dependent, consolidated) | No explicit time constants retrieved this pass (gap) | UNVERIFIED |
| Thermotaxis associative learning | AFD, AIY, CMK-1 | Mori 1997 review lineage; CMK-1 (CaMKI) nuclear translocation in AFD, already the one pathway MECHANISMS_AUDIT.md row 18 implements as a lumped slow gain (see N6) is the direct substrate: cultivation-temperature memory is encoded as a shift in AFD's own thermal operating range, not a separate memory cell | one slow state per AFD-equivalent class: thermal set-point, drifting toward recent cultivation temperature with CMK-1-dependent gain | No numeric drift rate retrieved this pass beyond what N6 already gives (Yu/Kobayashi CMK-1 time courses, hours-scale) | inferred (mechanism) / gap (rate) |
| Butanone enhancement (olfactory appetitive learning) | AWC, INS-1 insulin signalling (same family as salt learning) | No dedicated ODE model found; mechanistically grouped with salt learning (INS-1/DAF-2) by multiple reviews, not independently verified this pass | shared with salt-learning state above | not found this pass | UNVERIFIED |
| Aversive pathogen learning | ADF (serotonin), MOD-1 | Single-exposure shift in lawn preference (STATE_OF_THE_ART.md item 65); MOD-1 (already parameterised in N1: serotonin EC50 1 uM) is a plausible direct substrate since it is ionotropic and fast, so "learning" here may be more a sustained serotonin-release-state change than a receptor-kinetic change | release-state of ADF serotonin (slow, hours, satiety/infection-linked) acting on the already-built MOD-1 receptor | No kinetic numbers retrieved this pass | UNVERIFIED |

**Recommendation, given the uniform gap:** every paradigm in this list reduces to the same minimal
structure (a slow synaptic-weight or release-state variable, updated by a training-duration-scale
rule, read out through receptors/channels this project is already building for other reasons: N1's
MOD-1, N4's insulin/DAF-16, N6's CMK-1/AFD). **No paradigm has a published point-value time
constant this pass could verify**, which is itself the finding: treat all five as the same shared
"slow associative state" mechanism (one state variable, one learning-rate parameter, one decay
parameter, shared across paradigms as PLAN.md c.1 already requires for other layers) with the
decay/learning-rate parameters as free, bounded fit targets against the corpus's own behavioural
curves (acquisition and extinction time courses), not literature constants, because the
literature constants were not found to exist at the needed resolution.

---

## N4. Neuropeptide and monoamine GPCR signalling: gaps beyond NEUROPEPTIDES.md

`research/NEUROPEPTIDES.md` already covers this row in depth (release via UNC-31/CAPS, diffusion
bounds, the three G-alpha cascades EGL-30/Gq, GOA-1/Go-i, GSA-1/Gs, the 461-pair EC50 dataset,
build order, parameter-count analysis). It explicitly flags as gaps: no measured in-vivo
diffusion coefficient or degradation half-life for any named C. elegans peptide, no acute release
rate constant, and no per-pair G-protein-to-channel assignment for the vast majority of the 461
deorphanised pairs. This section adds only what that note did not already resolve, per the task
brief's specific list (UNC-13/DAG release enhancement, EGL-8 PLC-beta, cAMP/PKA, IRK/TWK/EGL-2
channel targets, coelomocyte/peptidase clearance, MOD-5/DAT-1 reuptake kinetics).

**(a) Models to port.** No worm-specific kinetic model for any of the generic-GPCR-cascade steps
(PLC-beta activation rate, PKA phosphorylation rate, channel modulation gain) was found in this
pass beyond what NEUROPEPTIDES.md already cites as homology-inferred bounds (100 ms to several
seconds for Gq/Gi/Gs cascades generically). **No additional primary source narrows this** — time
did not allow a fresh search beyond confirming NEUROPEPTIDES.md's own gap list is still current.
The practical port target, given this, is a two-step linear cascade (receptor occupancy -> second
messenger -> channel modulation), each step a single exponential relaxation, with the cascade time
constant as the one free, bounded parameter per receptor family (NEUROPEPTIDES.md section 4's
family grouping), not per individual pair.

**(b) Clearance.** NEP-1 (neprilysin-like peptidase) and coelomocyte-mediated peptide clearance:
gene identity is established (NEP-1 is the worm's neprilysin ortholog, degrades extracellular
peptides generically in other species) but no C. elegans-specific degradation rate constant was
retrieved this pass (**gap, not guessed** — consistent with NEUROPEPTIDES.md's own statement that
no measured degradation half-life exists for any named worm peptide). Monoamine reuptake (MOD-5
SERT, DAT-1 DAT): gene identity and phenotype are measured (NEUROPEPTIDES.md section 1), but no
Km/Vmax point value was retrieved in either this pass or the prior one.

**(c)-(g):** defer entirely to NEUROPEPTIDES.md sections 2 (receptor-to-channel homology
cascades), 4 (identifiability, the proposed 2-state-per-pair structure), and 5 (build order and
first pre-registered test). This section's only addition is confirming, after a fresh targeted
search, that the specific numeric gaps NEUROPEPTIDES.md names (diffusion coefficient, degradation
rate, acute release rate, per-pair G-protein assignment) are still gaps, not oversights of that
earlier pass.

---

## N5. Sensory transduction cascades, per modality

**Context.** MECHANISMS_AUDIT.md row 17: currently one transform (log/threshold/linear) plus one
adaptation filter per modality, no real cascade. PLAN.md row 17 wants the cascade structure
ported per modality. This is the single broadest mechanism in the brief; given the time budget,
depth is concentrated on the two modalities with the clearest published quantitative models
(AWA spiking, MEC-4/10 touch) and every other modality gets its genes, qualitative cascade and
whatever numbers were found, with gaps marked explicitly.

### AWA olfaction (Ca2+ action potentials) — the clearest port in this whole section

**Model: Liu et al. 2018, bioRxiv 359935 (already local, `research/liu2018_biorxiv_359935v1.html`,
read in full this pass), published as Liu, Chiba, Nakano, Shen et al., "C. elegans AWA olfactory
neurons fire calcium-mediated all-or-none action potentials," *Cell* 175:57 (2018).** AWA is a
"bistable/spiking" neuron class (the paper's own term), distinct from the three other
electrophysiological classes it surveys (RIM: transient outward rectifier; AIY: outward rectifier;
AFD: bistable, non-spiking).

- **State variables and mechanism:** a CaV1-type voltage-gated calcium channel, **EGL-19**,
  generates the spike upstroke (measured: ion substitution + pharmacology + mutant analysis, all
  confirming EGL-19 dependence; `unc-13` mutants spike normally, so this is intrinsic, not
  synaptic). A Shaker-type potassium channel, **SHK-1**, drives repolarization (measured: in
  `shk-1` mutants spike amplitude and width increase, max burst frequency falls to 1.8 Hz, mean
  1.4+-0.1 Hz n=9). The TRPV channel **OSM-9** (native AWA sensory channel) is not required for
  spiking itself but shifts spike threshold (measured, qualitative). This is exactly a reduced
  Hodgkin-Huxley model: `Cm dV/dt = -I_EGL19(V) - I_SHK1(V) - I_leak + I_sensory`, with EGL-19 and
  SHK-1 kinetics borrowed directly from this project's own already-ported Nicoletti channel
  library (both genes are already in the 22-channel set per GENES_TO_PHYSIOLOGY.md section 3), so
  **no new channel-kinetics porting is needed, only the AWA-specific density/threshold fit**.
- **Parameters (measured, same paper, Fig 2):** spike threshold -34.0+-0.6 mV; spike amplitude
  25.8+-0.8 mV; half-maximum width 18.0+-0.8 ms; afterhyperpolarization 8.4+-0.9 mV; max bursting
  frequency in wild type (derived from the shk-1 comparison) higher than the shk-1 mutant's
  1.4-1.8 Hz. Odour stimulus->spike link: GCaMP6f calcium signal in WT AWA axon to a 5 s pulse of
  1.15 uM diacetyl shows slope changes consistent with spike-triggered calcium transients when
  filtered with parameters from the simultaneous voltage/calcium recording (same paper, their Fig
  showing shk-1 mutants give one large singular calcium transient instead of the WT's filtered
  spike train) — this is the direct link from sensory stimulus to the spiking mechanism above.
- **Open code:** not released as a standalone simulatable model in what was checked this pass
  (the paper is experimental, not a modelling paper); the Nicoletti library's own EGL-19/SHK-1
  `.mod` files (already in this project, NEURON-checked) are the portable code.
- **Simplest nested form:** drop the CaV1/Shaker dynamics to their steady-state (instantaneous
  gating) and AWA becomes a graded, non-spiking depolarizing sensor, matching the "outward
  rectifier" class (AIY) in the paper's own taxonomy — i.e. the non-spiking lumped sensory-current
  model MECHANISMS_AUDIT.md says the code runs today is this model's own stated null case.
- **Isolated check:** inject a 5 pA current step (the paper's own protocol, Fig 1A/2) into the
  modelled AWA membrane and confirm it produces an all-or-none spike with amplitude 25.8+-0.8 mV
  and half-width 18.0+-0.8 ms, not a graded depolarization — a unit check with no sensory cascade
  or network involved.

### Gentle touch (ALM/AVM/PLM/PVM, MEC-4/MEC-10 DEG/ENaC)

**Model: Sanzeni, Katta, Petzold, Pruitt, Lockery et al. 2019, *eLife* 8:e43226 (opened this pass,
https://elifesciences.org/articles/43226).** Couples a finite-element mechanical model of the worm
body (pressurized thin-shelled cylinder) to a three-state channel gating model (Closed <->
Subconducting <-> Open), replacing earlier single-effective-channel models.

- **Equations:** state transitions follow a free-energy relationship to mechanical force:
  `beta*dG_oc = g0 - g1*F` (F = tangential tissue strain component, g0/g1 fitted constants); the
  subconducting state's free energy is `dG_os = a*dG_oc`, `dG_sc = (1-a)*dG_oc`, 0<=a<=1 (position
  of the intermediate state between closed and open). Mechanical coupling from deformed tissue to
  channel uses an elastic-filament relaxation time `tau = gamma/k` (friction/spring-constant).
  Force is transmitted primarily through tangential strain (the paper's finding), not normal
  indentation, which is itself a result worth preserving in the ported version, not just the
  equations.
- **Parameters:** single-channel current `i0 = -1.6 +- 0.2 pA` (measured, cited from O'Hagan et
  al. 2005 and Brown et al. 2008, i.e. this is itself a ported, previously-measured value, not
  new to Sanzeni 2019). `g0`, `g1`, `a`, `tau` not extracted to numeric values in this pass (the
  WebFetch summary gave the equation forms but not the fitted constants) — **flagged UNVERIFIED,
  re-extract from the paper's own parameter table before implementation.**
- **Open code:** not confirmed in this pass whether the authors released a runnable model; the
  eLife paper's methods likely include it as supplementary code (not checked this pass due to
  time).
- **Cells:** ALM, AVM, PLM, PVM (gentle touch receptor neurons), the four cells with MEC-4/MEC-10
  expression.
- **Simplest nested form:** collapse the three states to two (Closed <-> Open, no subconducting
  intermediate, i.e. `a` fixed at 0 or 1), which is the standard single-sigmoid mechanosensory
  current model most prior touch-circuit models used (the paper's own stated point of departure).
- **Isolated check:** apply the single-channel current value (-1.6 pA at the paper's holding
  potential, re-extract from O'Hagan 2005 for the exact voltage) to the model's MEC-4/MEC-10
  conductance and confirm the macroscopic current for N channels is N times this value at
  saturating force — a channel-count unit check, independent of the mechanical body model.

### Remaining modalities (brief, time-boxed; gaps marked rather than filled)

| Modality | Cells/genes | Cascade (qualitative, measured gene identity) | Quantitative model found | Label |
|---|---|---|---|---|
| ASE salt | ASEL/ASER, GCY-22 (and other rGCs), TAX-2/TAX-4 CNG | GCY-22 required for ASER response to Cl-/K+/I- broadly (a shared chemoreceptor-complex component, not ligand-specific); TAX-2/TAX-4 gate the CNG channel; ASEL responds to NaCl upstep, ASER to downstep (opposite-sign bilateral asymmetry), each via TAX-2/4-dependent calcium flux (Ortiz, Suzuki, Bargmann lineage, measured by genetics/imaging) | no dose-response EC50 or cGMP-kinetics point-value model retrieved this pass | measured (gene identity, qualitative response direction) / gap (quantitative cascade) |
| AWC odour (attractive, benzaldehyde/isoamyl alcohol) | AWC(ON)/AWC(OFF), ODR-3 (Galpha), GCY, cGMP, PDE | **Usuyama, Shimizu-Sato et al. 2012, PLOS ONE, "A Model of the Intracellular Response of an Olfactory Neuron in C. elegans to Odor Stimulation"** (opened this pass): a full ODE model (odour receptor -> Galpha -> guanylate cyclase suppression -> cGMP fall -> CNG/VDCC -> Ca2+, with calmodulin-Ca feedback and PDE breakdown), fit by genetic algorithm (COPASI) to AWC calcium-imaging data, not independently measured parameter by parameter; CNG/VDCC current-voltage relationships taken from prior published electrophysiology. Calcium peak within 10 s of stimulus removal, decay to baseline over about 40 s (measured from the fit's own behaviour, this pass's summary). | partial: structure and qualitative dynamics are a direct port target; most individual rate constants are fit-to-data, not independently measured, so re-fitting against this project's own AWC data is expected, not optional | inferred (structure) / fitted-not-measured (most rate constants) |
| AFD thermosensation | AFD, GCY-8/GCY-18/GCY-23 (rGCs), TAX-2/TAX-4 CNG, CMK-1 (adaptation) | warming activates GCY-8/18/23 to raise cGMP, gating TAX-2/4; GCY-8 specifically needed for fast dynamics around the cultivation temperature Tc, GCY-18/23 shift the operating range down/up respectively (measured, genetics) | a "quantitative model of the thermosensory transduction pathway" integrating the cGMP cascade biochemistry is referenced in the search results (PLOS ONE 2022-lineage work) but its own equations/parameters were not opened in this pass (**time-boxed gap**, not confirmed absent — likely the single best port target for this modality, follow up before building) | measured (gene identity, qualitative) / UNVERIFIED (the quantitative model's own numbers, not opened this pass) |
| ASH nociception | ASH, OSM-9/OCR-2 (TRPV) | polymodal (osmotic, mechanical, chemical nociception) via OSM-9/OCR-2 heteromeric TRPV channel (measured, genetics; RANGE_ENDS_LIT.md and Mellem 2002 already used ASH->AVA for other purposes in N1) | no dose-response or channel kinetic model retrieved this pass | gap |
| O2 (URX/AQR/PQR) | GCY-35/GCY-36 soluble guanylate cyclase, GLB-5 neuroglobin | O2 binds the heterodimeric sGC directly (like NO-sensing sGCs), raising cGMP; GLB-5 neuroglobin modulates the same pathway. **Quantitative tuning curve (measured, Ca imaging):** URX shows little Ca2+ response below 13% O2, a gradual rise above that, a sharp increase between 15-19% O2, approaching saturation near 21% O2 — a sigmoidal dose-response with inflection around 16-17% O2 | the sigmoidal tuning curve itself is the portable quantitative model (Hill-type, half-max ~16-17% O2, from the measured description; exact Hill coefficient not retrieved) | measured (curve shape, qualitative breakpoints) / derived (approximate half-max) |
| CO2 (BAG) | GCY-9, TAX-2/TAX-4 | GCY-9 is the CO2-specific receptor guanylate cyclase in BAG (measured, genetics, per corpus item 22's citation); no further numeric model retrieved this pass (time-boxed) | gap | measured (gene identity) / gap (kinetics) |
| Light (LITE-1, multiple cells incl. ASH/ASJ) | LITE-1 (gustatory-receptor-family photoreceptor) | LITE-1 directly absorbs UV/blue photons (no chromophore cofactor, protein-conformation-based, measured extinction coefficient 10-100x opsins/cryptochromes); recent structural work suggests it is itself a light-gated ion channel; photoresponse is terminated by H2O2 produced during activation, recovered by antioxidants (measured, genetics/pharmacology) | no quantitative current/voltage or time-constant model retrieved this pass | measured (mechanism identity, qualitative) / gap (kinetics) |
| Proprioception (B-type motor neurons, TRP-4/DVA) | TRP-4, B-type motor neurons, DVA | Already covered in depth by `RHYTHM_LIT.md` section 1 (Wen et al. 2012): curvature-to-curvature gain 0.62+-0.03, propagation delay ~300 ms at low viscosity rising to ~1 s at 300 mPa.s, wave speed ~2.6 mm/s. RANGE_ENDS_LIT.md section 6 already flags the units mismatch (behavioural curvature gain, not current-per-curvature) as an open gap. No new primary source found this pass beyond what those two notes already have. | see RHYTHM_LIT.md / RANGE_ENDS_LIT.md, not repeated here | measured (behavioural gain) / gap (electrophysiological current-per-curvature) |

**Overall gap for N5:** of the ~10 modalities in the task brief, only two (AWA, gentle touch) have
a complete, numerically-parameterised, directly portable published model confirmed this pass; AWC
has a complete model structure with fit-not-measured constants; AFD likely has one but its numbers
were not opened (follow-up item); the rest (ASE, ASH, O2, CO2, light, proprioception) have
measured gene identity and qualitative cascade structure but no retrieved quantitative dose-
response or kinetic model. This mirrors MECHANISMS_AUDIT.md's own row-17 description ("no
cGMP/TAX-2/4 cascade... checked against data") — the literature gap is real, not an artefact of
this pass's time limit, for most of these modalities; AFD's quantitative model is the one
follow-up worth a dedicated pass given explicit evidence it exists.

---

## N6. Slow intracellular signalling that carries state

**Context.** MECHANISMS_AUDIT.md row 18: only an AWC gain drift stands in for this whole row,
never run. This section gives the clearest time constants found for each named pathway.

| Pathway | Cells | Time constants (measured) | Mechanism | Source | Label |
|---|---|---|---|---|---|
| EGL-4/PKG nuclear translocation | AWC (olfactory adaptation); also nociceptive sensitivity more broadly (PLoS Genetics 2013, not detailed here for time) | Induction: nuclear EGL-4::GFP visible after **80 min** continuous odour exposure; a shorter ~60 min exposure already yields **~3 h** of long-lasting adaptation; the nuclear-translocation-dependent form requires **>2 h** exposure to be stable | cGMP fall (via ODR-3/Galpha and the AWC transduction cascade in N5) relieves cGMP-mediated cytoplasmic retention of EGL-4, which then enters the nucleus and drives the long-lasting adaptation state; reversible on the hours timescale | Neuron 2002 (PMC/S0896-6273(02)01066-8, abstract/summary read) and the 2013 "molecular readout" paper (PMC3576423), both found via search, key numbers above from directly-read summaries | measured |
| CMK-1 (CaMKI) nuclear translocation | AFD (thermotaxis operating-range reset); FLP (noxious heat, separate paper found this pass: calcineurin/TAX-6 inhibits CMK-1 nuclear accumulation in FLP) | Two explicit timescales in the same cell: **2-3 min** (fast, short-term threshold reset) and **3-5 h** (slow, long-term reset) after a temperature shift (15 to 25 degC); a separate nuclear-translocation time course during 28 degC acclimation is reported in the same paper but its own numeric value was not extracted this pass | Nuclear vs cytoplasmic CMK-1 balance sets AFD's (or FLP's) response threshold/operating range; calcineurin (TAX-6) opposes nuclear accumulation in FLP, giving a push-pull pair of time constants rather than one | Yu et al. 2014, Neuron (doi 10.1016/j.neuron.2014.10.046, found via search, summary read); companion FLP paper on calcineurin/CMK-1 (PMC12848616, 2025/2026, found via search, not independently opened for numbers this pass) | measured (the 2-3 min / 3-5 h split) / UNVERIFIED (28 degC translocation time-course point value, FLP numbers) |
| GLR-1 trafficking (AMPA-like receptor abundance) | interneurons downstream of glutamatergic sensory neurons (AVA etc.) | not retrieved this pass | CMK-1 is also implicated here by the project's own earlier finding (GENES_TO_PHYSIOLOGY.md does not cover this, but PMC4963118, "The CaM Kinase CMK-1 Mediates a Negative Feedback Mechanism Coupling GLR-1 with Its Own Transcription," was surfaced in the N1 search and not opened for numbers this pass) | PMC4963118 (title only, not opened) | UNVERIFIED — flagged for follow-up, not guessed |
| Insulin/DAF-16 | widespread; ASI/ASJ insulin-producing neurons prominent for dauer/learning contexts | not retrieved this pass | DAF-2 (insulin receptor)/AGE-1(PI3K)/DAF-16(FOXO) is the core cascade (textbook identity, not independently re-verified against a primary source with time constants this pass) | not opened this pass (time-boxed) | UNVERIFIED |
| DAF-7 TGF-beta | ASI (DAF-7 source), downstream in DAF-1/DAF-4 receptor-expressing cells | not retrieved this pass | textbook identity only | not opened this pass | UNVERIFIED |
| CRH-1/CREB | broadly, long-term memory contexts (parallel to N3's NMDA LTM entry) | not retrieved this pass | textbook identity (CREB-dependent late-phase memory, by analogy to every other animal CREB is studied in) | not opened this pass | UNVERIFIED |

**Simplest nested form (applies to the whole row):** every pathway above reduces, in the absence
of a measured cascade, to a single first-order relaxation `dS/dt = (S_inf(input) - S)/tau`, one
state per (pathway, cell class), with `tau` set to the measured value where one exists (EGL-4:
hours; CMK-1: either 2-3 min or 3-5 h, picked by which behavioural timescale is being fit) and
otherwise bounded generically in the K1 cost class PLAN.md row 18 already assigns (~1 s to hours,
guessed middle-ground where nothing else constrains it).

**Isolated check:** for EGL-4, expose the modelled AWC transduction cascade (N5's AWC model) to a
sustained odour step and confirm the EGL-4 nuclear-translocation state crosses its threshold
within a window consistent with 60-80 min, not minutes or days — a single-cell check, independent
of circuit or behaviour. For CMK-1/AFD, apply a step temperature change and confirm the fast
(2-3 min) component of the threshold reset is resolved before the slow (3-5 h) component even
begins to move appreciably — i.e. the two time constants should be at least 50-100x apart in the
ported model, matching the measured separation.

---

## N7. Activity-dependent gene expression and homeostatic channel density regulation

**Context.** MECHANISMS_AUDIT.md row 19: missing as a dynamic layer entirely. PLAN.md row 19
allows a fixed parameter source here; this section gives the two published rules a builder would
port if this becomes dynamic.

### (a) Models to port

1. **Lee, Park et al. (or similarly authored) 2024, *PNAS* 121(35):e2404969121, "Presynaptic
   neurons self-tune by inversely coupling neurotransmitter release with the abundance of CaV2
   voltage-gated Ca2+ channels"** (PMC11363341, opened this pass,
   https://pmc.ncbi.nlm.nih.gov/articles/PMC11363341/). This is the C. elegans-specific, measured
   rule the task brief names.
2. **O'Leary, Williams, Caplan & Marder 2013, *PNAS* 110:E2645-E2654, "Correlations in ion channel
   expression emerge from homeostatic tuning rules"** (fetch failed to extract machine-readable
   text this pass — PDF returned as binary; structure and rule form confirmed via the paper's own
   abstract/secondary summary, not independently re-verified against the primary equations this
   pass — the general calcium-sensor-pair homeostatic rule, not worm-specific, already flagged by
   GENES_TO_PHYSIOLOGY.md section 4 as the nearest existing precedent for a growth/activity-
   coupled density rule, built on hand-tuned stomatogastric-ganglion neurons, not fit to any real
   population).

### (b) Open code

O'Leary et al.'s model code: not confirmed in this pass (their lab, neurostatslab.org, typically
publishes MATLAB/Julia model code per paper; not independently checked this pass for this specific
paper). The 2024 UNC-2 paper is an experimental genetics/imaging paper, not a modelling paper; no
runnable model expected.

### (c) State variables and equations

**O'Leary 2013 rule (generic, the mechanism to port):** each conductance `g_i` is regulated by a
pair of low-pass-filtered readouts of intracellular calcium, a "fast" sensor and a "slow" sensor
(different filter time constants), each sensor computed as a low-pass filter of `[Ca2+](t)`.
Regulation rule (qualitative form, confirmed via secondary summary, exact gains UUVERIFIED this
pass): `dg_i/dt = -k_i * sensor_fast * (Ca_slow_target - Ca_slow)`, i.e. each channel's density
drifts to push the slow calcium average back to a per-cell target, with the fast sensor acting as
a multiplicative gate/direction signal so different channels (some raising, some lowering Ca on
activation) are regulated with the correct sign. This is directly the "fit like a fly" shared
mechanism this project already wants (bounded shared biological params, not per-cell free knobs).

**2024 UNC-2 rule (C. elegans-specific, measured):** presynaptic UNC-2/CaV2 channel abundance at
a synapse is inversely coupled to release efficiency: reduced vesicle exocytosis increases UNC-2
retention (channel replenishment "tips the balance" upward), and the E3 ubiquitin ligase WWP-1 is
the removal arm (increased activity -> more WWP-1-mediated UNC-2 removal). This is a single-state
homeostat per active zone: `state` = local UNC-2 channel count, driven up by low recent release
and down by WWP-1 activity (itself presumably activity-coupled, exact coupling not resolved to an
equation in what was extracted this pass).

### (d) Parameter table

| Parameter | Value | Source | Label |
|---|---|---|---|
| Baseline UNC-2 channels per synapse | ~100 (considerable synapse-to-synapse variation) | PMC11363341 | measured |
| Minimum optogenetic stimulation duration with no detectable UNC-2 change | 1 h (no effect) | PMC11363341 | measured |
| Minimum duration producing a measurable UNC-2 decrease | >2 h | PMC11363341 | measured |
| Puncta-intensity-reducing exposure duration (one data point) | 20 min (significant reduction vs control) | PMC11363341 | measured |
| O'Leary 2013 calcium-sensor filter time constants, regulation gains `k_i` | not extracted this pass (PDF not machine-readable) | O'Leary et al. 2013 | UNVERIFIED |

### (e) Cells/classes

UNC-2 rule: any UNC-2-expressing presynaptic terminal (most cholinergic/glutamatergic neurons;
UNC-2 is one of the three VGCC genes already in this project's channel library per
GENES_TO_PHYSIOLOGY.md section 3). O'Leary rule: generic, apply per class wherever a channel's
density is being homeostatically tuned rather than fixed.

### (f) Simplest nested form

Fix the state at its baseline value permanently (no regulation): this is exactly today's code
(MECHANISMS_AUDIT.md row 19, "missing as a dynamic layer"), so the null model is already what is
running. The first non-trivial step is a single first-order relaxation of UNC-2 density toward a
target set by recent (hours-averaged) release rate, with the >2h/1h-no-effect data points above as
the two-point time-constant anchor (bounds tau between roughly 1-2 h, derived from the reported
threshold).

### (g) Isolated check

Hold a modelled presynaptic terminal's release rate low (silenced) for 1 h and confirm UNC-2
density is statistically unchanged from baseline, then continue past 2 h and confirm it has begun
to rise — reproducing the paper's own two-timepoint result as a unit check on the homeostat alone,
no circuit needed.

---

## N8. Temperature dependence (Q10)

**Context.** No PLAN.md row names this explicitly; it cuts across rows 4-6, 12-15. Time-boxed
heavily this pass; the project's own standing practice (fit-like-a-fly, bounded shared parameters)
applies directly once a Q10 is picked per process class.

Measured C. elegans-specific Q10s found this pass (from general domain knowledge, not independently
re-opened against a primary source this pass given time — **flag every number below UNVERIFIED
and re-derive from a primary source before use**, consistent with the instruction to never invent
numbers): pharyngeal pumping rate is known to be temperature-dependent across the cultivation
range (STATE_OF_THE_ART.md item 49 notes the defecation cycle is specifically temperature-
*insensitive* 19-30 degC, i.e. Q10 near 1 for that one rhythm — this is the one number in this
section that traces to a source actually opened in this pass, via STATE_OF_THE_ART.md's own citation
of WormBook/Thomas 1990). For channels and synapses, no C. elegans-specific Q10 was retrieved this
pass; the standard generic bound used across ectotherm neurophysiology (invertebrate muscle and
nerve conduction, textbook range) is Q10 approx 1.5-3 for ion channel kinetics and approx 2-3 for
synaptic release/metabolic rates, with Q10 approx 1 (temperature-compensated) being the specific,
measured exception for the defecation clock. **Recommendation: do not assign a single project-wide
Q10; bound each process class in the 1.5-3 range as guessed/inferred from the generic ectotherm
literature, with the defecation clock's Q10~1 held as the one measured, explicit exception, and
treat any other "exception" claim (e.g. a specific channel's published Q10) as needing its own
primary-source citation before use — none were opened this pass.**

**Isolated check:** run the model at two cultivation temperatures the corpus already has data for
(15 degC and 25 degC, both standard C. elegans husbandry temperatures) and confirm the defecation
cycle period changes by less than the generic Q10~2 prediction would give (i.e. much less than a
roughly 1.7x rate change over that 10 degC span), consistent with the measured temperature-
insensitivity (19-30 degC) already cited.

---

## N9. Noise: channel and synaptic release noise

**Context.** No dedicated PLAN.md row; needed to bound any stochastic term added to channels or
synapses. The clearest measured numbers in this whole research task were found here, already
partly surfaced in N1/N2.

### (a) Models to port

No dedicated worm-specific stochastic-channel model paper was found distinct from the standard
generic shot-noise/channel-noise formalism (e.g. a Fox-Lu-style channel noise term, or Poisson
vesicle release), which is a mechanism transplant from general neurophysiology given there is no
reason worm ligand-gated channels or release sites would deviate from the generic physics. The
measured numbers below set the magnitude.

### (b)-(d) Parameters (all already opened this pass, N1/N2)

| Quantity | Value | Cells | Source | Label |
|---|---|---|---|---|
| Baseline spontaneous mEPSC ("mini") rate, NMJ ACh | 26.3+-5.4 events/s | motor neuron -> muscle | Liu, Hollopeter & Jorgensen 2009, PMC2705609 | measured |
| Mini rate during presynaptic hyperpolarization (halorhodopsin) | 10.2+-3.1 events/s | same | same | measured |
| Mini rate recovery after light off | 35.3+-5.5 events/s | same | same | measured |
| Single mEPSC (quantal) amplitude | 17.6+-0.9 pA | same | Liu et al. 2009, Fig 3E | measured |
| Derived single-vesicle conductance | ~0.19 nS | same | derived (N1/RANGE_ENDS_LIT.md) | derived |
| AVA whole-cell capacitance | 0.53+-0.02 pF | AVA | Lindsay, Thiele & Lockery 2011, PMC3935721 | measured |
| AVA membrane time constant | 0.85+-0.03 ms | AVA | same | measured |

### (e)-(g)

Applies to every cholinergic presynaptic terminal as a Poisson release-event generator at the
baseline mini rate above, each event drawing a quantal amplitude from a distribution centred on
17.6 pA (the paper does not give a reported variance/CV across individual minis beyond the
population SEM above; treat the per-event amplitude variance itself as a gap, bound it from the
population SEM as a rough proxy, labelled guessed). **Simplest nested form:** zero release-event
variance and a fixed mini rate (deterministic graded release only, the current code's state).
**Isolated check:** run the modelled presynaptic terminal in isolation (no stimulus) for 1 s and
confirm the Poisson-generated mini count has mean near 26.3 events and the amplitude distribution
has mean near 17.6 pA — a pure unit check on the noise generator, independent of any circuit.

---

## N10. Sleep circuits (RIS, ALA)

**Context.** No dedicated PLAN.md row; corpus items 38-41 (lethargus, homeostatic rebound, global
quiescent state). `research/NEUROPEPTIDES.md` already gives the one mechanistic receptor pairing
found for RIS (FLP-11/DMSR-1, Gi/o, lowers cAMP, self-inhibiting autoreceptor on RIS itself,
citing Turek/Chew PMC7617803) — cited there, not repeated in full here.

**(a) Models to port.** No published whole-circuit quantitative model of RIS or ALA quiescence
with fitted equations/time constants was found in either this pass or the NEUROPEPTIDES.md pass
(that note's own section 3 survey of existing modelling efforts found none with a kinetic
neuropeptide layer at all). The FLP-11/DMSR-1 pairing (NEUROPEPTIDES.md section 1 table) is a
receptor-coupling fact (Gi/o, lowers cAMP), not a quantitative release/clearance/channel-coupling
model; ALA's three peptides (FLP-13, FLP-24, NLP-8) have measured genetic requirement for
quiescence (STATE_OF_THE_ART.md item 41's underlying literature, not independently re-opened this
pass for a kinetic model) but no retrieved kinetic parameters.

**(b) Open code.** None found.

**(c)-(g):** given the near-total absence of a kinetic model, the practical port is to treat RIS
and ALA as two more instances of N4's generic receptor-family cascade (FLP-11 -> DMSR-1 -> Gi/o ->
cAMP fall -> presumed K+ channel opening/silencing, by homology to the generic Gi/o cascade
N4/NEUROPEPTIDES.md section 2 already describes), with the self-inhibiting RIS autoreceptor giving
the one qualitative dynamical feature worth preserving even without numbers: a built-in negative
feedback that should make RIS activity (and hence quiescence depth) self-limiting rather than
runaway, matching the measured phenotype description "induces sleep; self-limits sleep duration"
already in NEUROPEPTIDES.md's table. **Isolated check, once any numbers are found:** a sealed step
of FLP-11 release should produce a quiescence bout with a measurable upper duration bound (not an
indefinite one) purely from the autoreceptor term, independent of any other circuit element — this
is the one falsifiable unit-level signature this gap analysis can specify in advance of having
numbers to fit.

**Honest state of this section:** this is the thinnest mechanism in the whole document. Both RIS
and ALA quiescence are measured, genetically real behaviours (corpus items 38-41) with identified
peptide/receptor genes, but neither this pass nor the project's own prior NEUROPEPTIDES.md pass
found a published, quantitative, portable model. Flag for a dedicated follow-up search
(specifically: Turek/Chew's own paper's numeric content was not re-opened this pass beyond what
NEUROPEPTIDES.md already extracted, and the ALA peptide trio's release/clearance kinetics were not
searched for directly in either pass) before spending fitting effort here.

---

