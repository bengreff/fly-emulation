# Literature check: C. elegans intestinal Ca2+ oscillation / intercellular wave

Date of search: 2026-11-09 (run `date` before using this elsewhere).

Checked by wbody2, 9 Nov 04:05 CST (written by a Sonnet literature agent, 03:41-03:48):
- Opened and confirmed: Peters et al. 2007 (the Jorgensen lab PDF): 340 +- 140 um/s in behaving worms (n 10); inx-16
  108 +- 29 and 39 +- 14 um/s; 99.1 +- 3.0 % and 98.2 +- 4.0 % (mean +- SD, Fig 3D-E); per-worm median cycles 43-49 s.
  Espelt et al. 2005 (PMC2266627): 33 +- 3 um/s (Table II, 1 Hz imaging, 2 of 30 waves too fast to quantify); waves
  travel 80 +- 3 % (n 10) of the dissected intestine before terminating.
- Correction to 2c: the ring spacing is about 80 um (WormAtlas ~720 um over 9 rings; Spec int_ring_length_um), not
  25-30 um, so at 340 um/s the per-ring delay is about 0.24 s (derived), not 0.1 s.
- Not checked by me: Baylis et al. 1999's Kd, the Kemp 2012 and Nehrke 2008 quotes, and the author names in section 1
  (the AVL/DVB paper at 10.1038/s41467-022-30452-y is cited elsewhere in this project as Jiang et al. 2022,
  PMC9120479).
- Used in: check_intestine.py's 9 Nov bar and the night file log 03:40-04:05.

Scope: does published literature give a computational model, or a measured propagation
mechanism, that we are missing for the worm intestinal Ca2+ wave (defecation motor program
pacemaker)? Our model: 20 cells, Li & Rinzel 1994 IP3R Ca oscillator per cell (generic
kinetics), int9 pacemaker by higher basal IP3, IP3 and Ca both diffuse through INX-16 gap
junctions (lumped, guessed permeability). Period ~49 s and velocity ~33 um/s fitted to
Espelt et al. 2005. Failure: in 600 s int9 fires 12x but only 1/11 waves reaches int2 in
order; only 1/1000 random draws in guessed ranges passes.

## 1. Published computational/mathematical models of the intestinal Ca2+ oscillator or wave

**Not found.** No paper gives equations and fitted parameters for a C. elegans intestinal
Ca2+ oscillator or intercellular wave model (Li-Rinzel-type, Othmer-Tang, or otherwise).
Searched directly for this (see query list below) across PubMed/Europe PMC/bioRxiv/Google
and did not find one. What exists instead:

- Computational Ca2+ models exist for *other* C. elegans cells: the ASH sensory neuron
  (Gaudet/Bhattacharya group? — Yu et al., "A mathematical and computational model of the
  calcium dynamics in Caenorhabditis elegans ASH sensory neuron," PLoS ONE 2018, PMC6062085,
  also bioRxiv 10.1101/201962) and the AVL/DVB enteric motor neurons (Dhakshinamoorthy et al.,
  "C. elegans enteric motor neurons fire synchronized action potentials underlying the
  defecation motor program," Nat Commun 2022, 10.1038/s41467-022-30452-y — this is a
  Hodgkin-Huxley-style single/few-neuron model of AVL, not the intestine). Neither models
  the intestinal epithelial Ca2+ oscillator or the intercellular wave.
- Checked one bioRxiv hit that looked promising by abstract ("tuning the strength of calcium
  stimulation modulates organ size control," Paravitorghabeh, Soundarrajan, Zartman, bioRxiv
  10.1101/649582): this is a *Drosophila* wing-disc model (initiator cells + gap-junction
  coupled standby cells), not C. elegans. Mentioned only because its general model form
  (regenerative wave from a small initiator population through gap-junction-coupled
  followers) resembles our int9-pacemaker-plus-followers structure, but it is not
  worm-specific and gives no transferable parameter values.
- Checked a BioSystems 2023 paper (Mobille, Follmann, Vidal-Gadea, Rosa, "Quantitative
  description of neuronal calcium dynamics in C. elegans' thermoreception," BioSystems 223,
  104814) found via search for "C. elegans calcium model" — this is the AFD thermoreceptor
  neuron, unrelated to the intestine.
- Generic (non-worm) theoretical calcium-wave models exist, e.g. Sneyd et al. 1994 ("A model
  for the propagation of intercellular calcium waves," Am J Physiol Cell Physiol 266:C293,
  gap-junctional Ca2+ diffusion) and a 2001 Biophys J theoretical study of gap-junctional Ca2+
  diffusion waves (Höfer et al.? exact authors not confirmed, S0006-3495(01)75996-6). These
  are generic reaction-diffusion treatments, not parameterized to worm intestine data, and we
  already use the same general form (Li-Rinzel + diffusive coupling).

**Conclusion for Q1: there is no missing published mechanistic model to port.** Our general
model form (Li-Rinzel oscillator + diffusive IP3/Ca coupling + one elevated-excitability
pacemaker) is consistent with how the field has informally described the system (see
section 2), but nobody has published fitted equations for it. The 49 s period / 33 um/s
velocity fit target (Espelt et al. 2005) is the most quantitative public anchor that exists.

## 2. Measured propagation mechanism

### 2a. Does IP3 or Ca2+ (or both) cross INX-16 junctions?

**Not resolved experimentally — both are explicitly floated as open hypotheses, not
distinguished.** Peters et al. 2007 (Current Biology 17:1601-1608, PMC not available, full
text obtained from jorgensen.biology.utah.edu lab PDF) states directly:

> "What is the molecule that passes through the pannexin gap junction? IP3 activates the IP3
> receptor, and it is conceivable that IP3 passes through the junctions to initiate a calcium
> wave in every cell. Alternatively, calcium itself could be the signal that travels through
> the gap junction because calcium can produce a regenerative spike [ref 20, Bezprozvanny
> 1991]. Thus, calcium flux from one cell to an adjacent cell through gap junctions could
> stimulate a regenerative calcium spike." (Discussion, p. 1604)

Espelt et al. 2005 (J Gen Physiol 126:379-392, PMC2266627) says the same thing in near-identical
words: "One mechanisms by which Ca2+ waves are thought to be propagated between cells is by
diffusion of IP3 and/or Ca2+ through gap junctions" (Discussion) — again framed as a
hypothesis, not a demonstrated result. So our choice to let *both* IP3 and Ca2+ cross the
gap junction (lumped) is literally what the field's two leading papers say is "conceivable" —
it is not contradicted by anything we found, but it is also not confirmed; it is their
unresolved alternative, not ours to blame for the failure.

Indirect evidence that favors IP3R-mediated (not purely electrical/direct-Ca) signalling:
Teramoto & Iwasaki 2006 (Cell Calcium 40:319-327; abstract obtained via Europe PMC, full text
not open access) found that applying the IP3 receptor inhibitor **heparin at the mid-intestine**
blocks wave propagation past that point and eliminates the second/third motor steps — i.e.
blocking ITR-1 locally, not just blocking a diffusible messenger generically, stops the wave,
which is consistent with each cell needing its own ITR-1 activation to keep the wave going
(a form of regeneration), not pure passive Ca2+ diffusion through the cytoplasm.

### 2b. Cell-autonomous PLC regeneration (Ca2+ -> IP3 production in each cell)

**Not demonstrated directly as "Ca-stimulated PLC" in the published work we could access,
but strongly implied as a requirement.** What is established:
- EGL-8 (PLC-beta) and PLC-3 (PLC-gamma) are both required for normal Ca2+ oscillations
  (Espelt et al. 2005 abstract/discussion, confirmed by WebFetch of PMC2266627).
- Nehrke, Denton & Mowrey 2008 (Am J Physiol Cell Physiol 294:C333-344, PMID 17942636, not
  open access; abstract obtained via Europe PMC) found that in **egl-8/PLC-beta mutants**,
  "Ca2+ waves ... initiate ectopically, often traveling in reverse, and fail to trigger a
  complete DMP," and conclude "the normal supremacy of the posterior intestinal cells is not
  obligatory for Ca2+ wave occurrence but instead helps to coordinate the DMP." This shows
  PLC-beta activity is needed in non-pacemaker cells for correctly directed, complete
  propagation — consistent with (but not direct proof of) each cell needing its own
  Ca-triggered PLC activity to keep regenerating the wave forward.
- Kemp, Allman, Immerman, Mohnen, Peters, Nehrke & Abbott 2012 (Curr Biol 22:2213-2220,
  PMC3586602, the miR-786/elo-2 paper) report "EGL-8[PLC-beta] is enriched at points of
  cell-cell contact in the posterior intestine," which is structurally consistent with a
  junction-adjacent regenerative PLC step, though the paper's main point is about the
  pacemaker threshold, not the propagation step (see 2d).

No paper we accessed gives a quantitative Ca-to-PLC feedback term (e.g. Hill coefficient for
Ca-stimulated PLC activity) for the worm intestine. Our Ca-stimulated PLC term is therefore
still "generic Li-Rinzel-adjacent," not measured — same label it already has.

### 2c. Intercellular delays, refractory periods, how often the wave reaches int1/int2 in order

This is the section with the most load-bearing numbers for our failure mode, and it has a
real and important discrepancy depending on preparation:

- **Isolated/dissected intestine (Espelt et al. 2005, PMC2266627):** "Waves traveled 80 ± 3%
  (n = 10) of the length of the dissected intestine before terminating." I.e. even in wild
  type, in the cut-open, ex vivo preparation, the wave does *not* reliably reach the anterior
  end — it terminates partway, on average at 80% of the gut's length, in every one of the 10
  waves measured. No per-ring delay time or termination-frequency distribution is given
  beyond this mean ± SEM.
- **Intact, behaving worm (Peters et al. 2007, Current Biology 17:1601-1608):** wave speed is
  **340 ± 140 um/s (n = 10)** in wild type, "roughly match[ing] the rate of posterior body
  contraction, approximately 270 um/s." This is about **10x faster** than the 33 um/s Espelt
  number used for our fit. In this intact-worm regime, the wave reaching the anterior is
  measured indirectly via the two late motor steps it triggers: "wild-type: 99.1% ± 3.0%"
  of cycles execute the anterior body contraction, and "98.2% ± 4.0%" execute the enteric
  muscle contraction (their Figure 3D/E; these require "Calcium flux in the anterior
  intestine," per their own citation of ref [1]=Teramoto & Iwasaki 2006). So in the intact
  worm, the wave reaches far enough anterior to drive these contractions in ~98-99% of
  cycles — a completely different reliability than the ex vivo 80%-of-length-then-stops
  number.
- Peters et al. 2007 also give the defecation period precisely: "The median cycle time of
  wild-type worms only varies 6 s, from 43-49 s" across 11 worms, with the across-worm
  average median 45.60 s; the per-worm coefficient of variation of cycle time is 4.9 ± 1.9%.
  This period matches our 49 s target reasonably well.
- Peters et al. 2007 do not give a per-ring delay number either, but their wave-speed numbers
  let you derive one: at 340 um/s and a ring spacing of order 25-30 um (int1-int9 span the
  ~250-300 um intestine over 9 rings, derived, not stated in this paper), that is roughly
  0.1 s of delay per ring in the intact worm — an order of magnitude shorter than our fitted
  49 s/9-ish-rings traversal would imply if the wave had to cross all rings inside one period.

**This is the key finding for your failure mode.** The 33 um/s / 49 s combination you fit to
is the *dissected-gut* regime (Espelt 2005), where even wild type does not reliably complete
the wave (80% of length, and that's a mean over complete propagations only — some waves in
that prep die earlier still, per Peters' description of the general phenomenon of abortive
waves). The near-100%-reliable, anterior-reaching wave that the real animal relies on for
the defecation motor program is the *intact-worm* regime (Peters 2007, and implicitly
Teramoto & Iwasaki 2006), which runs at ~340 um/s, ~10x faster, with the same ~45-50 s period.
If your model is being asked to reproduce "49 s period, 33 um/s velocity, AND >90% reliable
anterior arrival" simultaneously, you may be combining numbers measured in two different
preparations that are not expected to coexist in the real animal. The dissected-gut
measurement is the slow/unreliable regime; the intact-animal measurement is the fast/reliable
one. The animal does not do both at once.

- Also relevant: Nehrke, Denton & Mowrey 2008 abstract states "an underlying pacemaker
  appears to oscillate at a faster frequency than the defecation cycle and ... arrhythmia may
  result from uncoupling the pacemaker from the DMP rather than from disrupting the pacemaker
  itself" — i.e. the literature itself notes that the posterior pacemaker's intrinsic rate and
  the "successful behavioral cycle" rate are not automatically the same thing, and that
  uncoupling (not pacemaker malfunction) is a recognized failure mode. This is at least
  structurally similar to your int9-fires-12x-but-only-1-wave-completes situation, in that the
  literature treats "pacemaker fires" and "a complete wave results" as separable events, not a
  1:1 pair, even in some wild-type-adjacent conditions.
- "Reverse" waves: both Peters et al. 2007 (in inx-16 mutants, "travel in the opposite
  direction," and ectopic initiation in >half of mutant waves, 17/27) and Nehrke/Denton/Mowrey
  2008 (in egl-8 mutants, "often traveling in reverse") report reversed waves, but only as a
  mutant/disrupted-gap-junction or disrupted-PLC phenotype, not as a wild-type occurrence.

### 2d. Wave direction and the pacemaker mechanism

- Direction: posterior (int9 ring) to anterior (int1), in both dissected (Espelt 2005: "began
  in the distal end ... proceeded in a posterior-to-anterior direction") and intact (Peters
  2007: "calcium spike in the most posterior cells initiates a calcium wave that travels the
  length of the intestine") preparations.
- Pacemaker identity: the posterior intestinal ring, int9, specifically (confirmed by multiple
  sources referring to "int9" as the posteriormost ring and the site of pacemaker activity;
  Dal Santo et al. 1999, Cell 98:757-767, established ITR-1 in the posterior intestine as "an
  essential element of the pattern generator"; abstract via Europe PMC).
- Mechanism for *why* int9 is the pacemaker — this is the one place the literature gives a
  specific, different-from-ours mechanism. Kemp, Allman, Immerman, Mohnen, Peters, Nehrke &
  Abbott 2012 (Curr Biol 22:2213-2220, PMC3586602) propose it is **not** simply higher basal
  IP3 production, but a **lower threshold for Ca2+ release set by membrane lipid composition**:
  "miR-786 confers pacemaker status on posterior intestinal cells for the control of
  calcium-wave initiation through the regulation of elo-2" (a fatty-acid elongase), and
  "pacemaker activity likely involves establishing a different threshold for intracellular
  calcium release in the posterior intestine relative to neighboring intestinal cells" via
  elo-2-dependent palmitate levels changing membrane/channel excitability. Peters et al. 2007
  separately note that when INX-16 is disrupted, more than half of mutant waves initiate
  ectopically in non-int9 cells (17/27), concluding "the most posterior cell is not
  fundamentally different from all other intestinal cells; other intestinal cells are capable
  of initiating a calcium wave in the absence of the normal pacemaker," i.e. int9's advantage
  is a quantitative threshold/excitability edge, reinforced by gap-junction coupling forcing
  synchrony, not a qualitatively unique mechanism. **This differs from our "int9 has higher
  basal IP3 production" assumption**: the literature's preferred account is a lower
  activation threshold (membrane-lipid-mediated) for the same stimulus, which in Li-Rinzel
  terms is closer to a lower effective Ca2+/IP3 co-activation threshold or higher IP3R open
  probability at a given [IP3], rather than higher resting [IP3] itself. In practice these two
  knobs (basal IP3 vs. activation threshold) may be interchangeable for getting int9 to fire
  first, but if your parameter search treats "basal IP3" as the only excitability knob for
  int9, you have a narrower, and possibly wrong-shaped, search space than the mechanism the
  literature actually proposes.

## 3. Measured numbers usable as bounds

| Quantity | Value | Label | Source |
|---|---|---|---|
| Defecation/Ca-wave period, wild type | 45.60 s mean of per-worm medians; range of per-worm medians 43-49 s; CV 4.9% ± 1.9% (n=11 worms) | measured | Peters et al. 2007, Curr Biol 17:1601-1608, Fig 3B/C |
| Defecation/Ca-wave period, wild type (alt.) | 50-60 s period for DMP generally | measured | Teramoto & Iwasaki 2006 abstract (via Europe PMC); Kwan et al. 2008 BMC Physiol 8:11 ("mean period 45-50 s at 20 C"), PMC2409367 |
| Ca-wave velocity, isolated/dissected intestine | 33 um/s (mean) | measured | Espelt et al. 2005, J Gen Physiol 126:379-392, PMC2266627 |
| Ca-wave velocity, intact behaving worm, wild type | 340 ± 140 um/s (n=10) | measured | Peters et al. 2007, Curr Biol 17:1601-1608 |
| Ca-wave velocity, intact worm, inx-16 "slow" mutant | 108 ± 29 um/s (4/12 waves) | measured | Peters et al. 2007 |
| Ca-wave velocity, intact worm, inx-16 "very slow" mutant | 39 ± 14 um/s (8/12 waves; cross-checked 35.7 um/s with inverse pericam vs 42.5 um/s with cameleon) | measured | Peters et al. 2007, incl. Supplemental Experimental Procedures |
| Fraction of dissected-gut length wave travels before terminating, wild type | 80 ± 3% (n=10) | measured | Espelt et al. 2005 |
| Fraction of cycles with anterior body contraction (proxy for wave reaching anterior), wild type | 99.1% ± 3.0% | measured | Peters et al. 2007, Fig 3D |
| Fraction of cycles with enteric muscle contraction, wild type | 98.2% ± 4.0% | measured | Peters et al. 2007, Fig 3E |
| Same, inx-16(ox144) mutant | anterior: 23.6% ± 24.6%; enteric: 15.5% ± 12.9% | measured | Peters et al. 2007, Fig 3D/E |
| Fraction of inx-16(ox144) worms with no wave at all (spike stays in posterior cells) | 21% (7/34) | measured | Peters et al. 2007 |
| Fraction of inx-16(ox144) waves with ectopic (non-posterior) initiation | 17/27 (of worms that had any wave) | measured | Peters et al. 2007 |
| ITR-1 (worm IP3 receptor) InsP3-binding-domain affinity | Kd = 7 ± 4 nM (recombinant binding domain, in vitro) | measured | Baylis, Furuichi, Yoshikawa, Mikoshiba & Sattelle 1999, J Mol Biol 294:467-476 |
| INX-16 junctional/dye coupling | qualitative only: lucifer yellow dye transfer "not qualitatively different" between inx-16(ox144) and wild type ("data not shown") — no conductance or diffusion-coefficient number given | measured (qualitative) | Peters et al. 2007 |
| IP3/Ca2+ diffusion coefficient between intestinal cells | not found — no paper gives a permeability or diffusion-coefficient number for intestinal gap junctions | not found | — |
| Resting/peak intestinal cytosolic [Ca2+], absolute units | not found — all cited papers (Espelt 2005, Xing/Yan/Estevez/Strange 2008 PMC/JGP 131:245-255) report only ratiometric (cameleon/pericam) or relative fluo-4 fluorescence, no absolute nM/uM values | not found | Espelt et al. 2005; Xing et al. 2008, J Gen Physiol 131:245-255 |
| sca-1 (SERCA) rate constants in intestine | not found — only qualitative statement that sca-1 is the relevant Ca-ATPase for intestinal Ca2+ dynamics and defecation phenotype, no kinetic constants | not found | search only (see queries) |
| Per-ring delay time (direct measurement) | not found directly; order-of-magnitude derived from intact-worm velocity (340 um/s) and approximate ring spacing (~25-30 um, derived from total intestine length / 9 rings, not itself a cited measurement) is roughly 0.1 s/ring | derived | derived from Peters et al. 2007 velocity figure |

## Queries tried

- "C. elegans intestinal calcium wave mathematical model IP3 receptor"
- "defecation motor program C. elegans mathematical model calcium oscillation"
- "inx-16 gap junction calcium wave intestine C. elegans Peters"
- "Teramoto Iwasaki 2006 Cell Calcium PLC-beta EGL-8 PLC-gamma PLC-3 intestine wave C elegans"
- "Dal Santo 1999 Cell itr-1 IP3 receptor defecation intestine calcium"
- "Nehrke Denton Mowrey 2008 calcium wave intestine C elegans defecation"
- ""Peters" "inx-16" Current Biology 2007 PMC pannexin calcium wave"
- "computational model intestinal calcium oscillator C elegans ITR-1 IP3 receptor kinetic parameters thesis"
- ""C. elegans" intestine calcium wave simulation model "IP3" diffusion gap junction parameters biorxiv"
- "sca-1 SERCA C elegans intestine calcium ATPase rate kinetics measured"
- "intestinal calcium wave C elegans model Hodgkin-Huxley OR FitzHugh-Nagumo OR \"ordinary differential equation\" int9 pacemaker posterior intestine"
- "Walker Baylis ITR-1 C elegans IP3 receptor binding affinity Kd biochemical characterization"
- "\"int9\" pacemaker C elegans intestine calcium defecation posterior ring cell identity"
- Europe PMC REST queries by PMID/EXT_ID for: Peters 2007 (PMID 17825560, not in PMC, not OA),
  Teramoto & Iwasaki 2006 (PMID 16780946, not in PMC, not OA — abstract only),
  Nehrke/Denton/Mowrey 2008 (PMID 17942636, not in PMC, not OA — abstract only),
  Dal Santo et al. 1999 (PMID 10499793, not in PMC, not OA — abstract only)
- Direct PMC/PDF fetches: Espelt et al. 2005 (PMC2266627, full text, open), Peters et al. 2007
  (full text PDF from jorgensen.biology.utah.edu lab site, extracted with pdftotext — this is
  the one case where a full, non-abstract text was obtained for a non-PMC paper), Xing et al.
  2008 TRPM paper (PMC2248719, open), Kwan et al. 2008 TRPM/BMC Physiology paper (PMC2409367,
  open), Kemp et al. 2012 miR-786 paper (PMC3586602, open).
- Not found / gave up on: full text of Teramoto & Iwasaki 2006 (Cell Calcium, Elsevier,
  no PMC deposit, no open-access mirror found), full text of Dal Santo et al. 1999 (Cell,
  no PMC deposit for a 1999 paper, cell.com full text returned 403 Forbidden), full text of
  Nehrke/Denton/Mowrey 2008 (AJP Cell, no PMC deposit, journals.physiology.org returned 403).
  Only abstracts of these three were obtained (via Europe PMC's abstractText field).

## Verdict

**No published model or measured mechanism contradicts our model form.** The field's own
leading papers (Peters et al. 2007; Espelt et al. 2005) describe the propagation mechanism as
an open question between "IP3 diffuses through INX-16," "Ca2+ diffuses through INX-16 and
regenerates a spike in the next cell," or both — which is exactly our lumped IP3-and-Ca
diffusion plus Li-Rinzel-regeneration design. No paper publishes a fitted computational model
of the intestinal oscillator or wave (only generic theoretical gap-junction-wave papers and
models of unrelated C. elegans neurons exist) and no paper measures an INX-16
conductance/diffusion-coefficient number, so there is nothing to port in for Q1 or for a
hard numeric bound on coupling strength in Q3.

**One real difference from our assumption:** the literature's preferred account of why int9
is the pacemaker is a lipid-mediated *lower activation threshold* in posterior cells (Kemp et
al. 2012, miR-786/elo-2), not simply *higher basal IP3 production* as we assumed. This is a
different knob in Li-Rinzel terms (threshold/affinity vs. basal ligand level) and may matter
if your parameter search only varies int9's basal IP3.

**The most load-bearing finding is a preparation mismatch, not a missing mechanism.** The
49 s-period/33 um/s-velocity numbers we fit to (Espelt et al. 2005) come from the *dissected,
ex vivo* intestine, where even wild type only gets the wave 80% of the way down the gut before
it stops (not 100%, not measured per-ring). The near-universal (~98-99%) anterior-arrival
reliability that the real worm's defecation program depends on is measured in the *intact,
behaving* animal (Peters et al. 2007) at a wave speed of 340 ± 140 um/s — about 10x faster
than the dissected-prep number, with the same ~45-50 s period. These two regimes are not
expected to coexist: slow-and-unreliable is the cut-open-gut condition; fast-and-reliable is
the intact-animal condition. If the check is holding the model to "33 um/s AND 49 s period
AND >90% of waves reach int2 in order," it may be asking for a combination the real animal
never produces — the real animal's fast intact-worm wave is the one that is reliable, not
the slow dissected-gut one. Worth checking against the brief whether the ~33 um/s number
should still be the propagation-speed target if the reliability bar is meant to be met, or
whether period (49 s, present in both preps) is the only number that should be shared
between regimes, with velocity and reliability bars drawn from the matching (intact-worm)
measurement instead.
