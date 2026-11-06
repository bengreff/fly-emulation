# What generates the C. elegans locomotor rhythm: literature check

Context: a 302-neuron biophysical model (BAAIWorm/NEURON cells, Cook 2019 wiring, Fenyves 2020
synapse signs) in closed loop with a ported 3D soft body, every parameter at a literature-range
midpoint, produces no rhythm: AVA and AVB are co-depolarised, all motor neuron classes are high,
muscles co-contract into a tonic C-curl, B-type motor neurons barely move (1-1.5 mV) with the
body. This asks what the literature says generates the rhythm and the AVA/AVB switch in the real
animal, and whether an existing open-source model already does this and could be ported, before
deciding whether to port a rhythm mechanism or keep fitting parameters in range.

Every number below is labelled **measured** (read off a real recording/experiment), **derived**
(arithmetic done here from measured numbers, shown inline), or **model assumption** (a value
another simulation chose, not measured). Gaps are marked **gap** and left unfilled, not guessed.

## 1. What generates the forward rhythm in the real worm (measured evidence)

**Wen, Mo, Wu, Fenyves, et al. 2012, *Neuron* 76:750-761 (PMC3508473) — proprioceptive coupling,
B-type motor neurons.** Mechanism: each body segment's B-type motor neuron senses the curvature
of the segment just anterior to it and bends in response, a local "chain of reflexes" that
converts a rhythm already present near the head into a posteriorly-propagating wave. Numbers:
posterior-curvature-vs-anterior-curvature gain **0.62 ± 0.03** (**measured**, linear fit, Fig.
4C); propagation delay **~300 ms** at low viscosity (water to ~100 mPa·s), rising to **~1 s** at
300 mPa·s (**measured**, Fig. 5D-E); wave speed **~2.6 mm/s** in water (**measured**, Fig. 5F).
Calcium imaging: DB6 and VB9 activity are negatively correlated with each other (Fig. 7B1) and
positively correlated with dorsal/ventral bending respectively (Fig. 7B2-3), **measured**.
Ablation/silencing: hyperpolarising all cholinergic neurons, or B-type neurons specifically via an
active K+ channel, blocks posterior segments from following anterior curvature (Fig. 6A-F,
**measured**); A-type, D-type motor neurons, DVA, and muscle gap junctions (UNC-9) are **not**
required for this coupling (Fig. S4, **measured**). Channels/connections needed: a curvature-
sensing current in B-type neurons (molecular identity not resolved in this paper) and B-to-B
chemical/gap connectivity along the ventral/dorsal cords. The paper's own statement: a CPG near
the head generates the initial rhythm; proprioception "suffices to translate" it posteriorly but
cannot by itself initiate oscillation. **This paper is about propagation, not generation.**

**Fouad, Teng, Mark, et al. 2018, *eLife* 7:e29913 (PMC5780042) — distributed rhythm generators.**
Mechanism: forward locomotion is driven by multiple separate oscillators along the body, not one
head CPG broadcasting outward. Numbers/evidence: optogenetically silencing anterior body-wall
muscle or cholinergic neurons leaves posterior undulation intact (Fig. 2A-B, **measured**);
disrupting neck coupling produces "two-frequency undulation" (2FU), head and tail beating at
different rates simultaneously (Fig. 3A-E, **measured**); severing both nerve cords leaves
isolated posterior segments oscillating, at a **higher** frequency than the head (Fig. 6-7,
**measured**); the smallest segment still able to oscillate on its own spans **VB9-VB11 and
DB6-DB7** (Fig. 7, **measured**). B-type motor neurons are necessary for 2FU (ablating most
DB+VB nearly abolishes it, Fig. 5B-C, **measured**); A-type and D-type motor neurons are not
required (Fig. 4 supp. 1C, Fig. 4D-E, **measured**); AVB ablation nearly abolishes 2FU, most other
premotor interneurons (AVA, AVD, AVE, PVC) do not affect it (Fig. 4A,E, **measured**). Coupling is
bidirectional: posteriorward via Wen 2012's proprioception, and a novel anteriorward route —
rhythmic 2 Hz mid-body stimulation entrained the head down to ~1 Hz (Fig. 8C-D, **measured**).
Conclusion stated by the authors: multiple rhythm-generating units of different intrinsic rate,
coupled strongly enough to phase-lock into one coherent wave.

**Xu, Huo, Shao, Po, Kawano, Lu, Wu, Zhen, Wen 2018, *PNAS* 115:4493-4498 (PMC5948959) — AVB-B
gap junctions and descending drive.** Mechanism: AVB premotor interneurons are electrically
coupled to B-type motor neurons via UNC-7 (in AVB) / UNC-9 (in B-type) heterotypic gap junctions
(Fig. 1A); this coupling drives B-type neurons through a **bifurcation from a stationary fixed
point to a limit-cycle oscillator** — i.e. AVB's tonic input is what turns B-type neurons into
oscillators, it does not itself oscillate. AVB's own calcium activity is explicitly described as
"nonoscillatory" / tonic during forward locomotion (Fig. 4E, **measured**). Mutant numbers: in
*unc-7* and *unc-9* mutants, bending amplitude falls off monotonically from head to tail (losing
the wild-type plateau) and bending frequency is significantly reduced (Fig. 1B-D, Fig. S1A,
**measured**); proprioceptive coupling (Wen 2012) remains intact in these mutants (Fig. 2B-C,
**measured**), so the two mechanisms are separable. The paper's own bifurcation model uses a gap-
junction conductance of **100 pS** for AVB-B coupling (Fig. 5B) — stated explicitly as a fitted
parameter for the model, not a patch-clamp number (**model assumption**). Channels/connections
needed: AVB-to-B-type gap junctions (UNC-7/UNC-9) plus the proprioceptive B-to-B coupling from Wen
2012, acting "synergistically" per the paper's own discussion — descending drive sets up the
oscillation, proprioception entrains/propagates it.

**Gao, Guan, Fouad, Meng, et al. 2018, *eLife* 7:e29915 (PMC5780044) — A-type motor neurons as
intrinsic oscillators (backward).** Mechanism: cholinergic A-type motor neurons (A-MNs) are
themselves intrinsic oscillators, sufficient for backward locomotion with premotor interneurons
(AVA, AVD, AVE) removed entirely. Numbers: in dissected neuromuscular preparations with premotor
interneurons and B-type neurons ablated, rhythmic postsynaptic currents recurred at **~90 s**
intervals in 70% of preps, each burst lasting 2-3 s and composed of 3-10 Hz depolarising events
(Fig. 4A-C, **measured**); in intact immobilised animals the same ablation gives a **~50 s**
oscillatory cycle (Fig. 4F-H, **measured**); in freely moving animals cycle period is below 50 s
and shortens (speeds up) with crawling speed (Fig. 5B-C, **measured**). Channel: the P/Q/N-type
voltage-gated calcium channel **UNC-2** is required — loss-of-function reduces oscillation
amplitude and frequency, gain-of-function increases both (Fig. 7A-F, **measured**); the L-type
channel EGL-19 and the NALCN-type sodium leak channels (NCA-1/2, UNC-79/80) are **not** required
(Fig. 7 supp. 1A, **measured**). Oscillation persists with chemical synaptic transmission
abolished (*unc-13* mutant, Fig. 7G-I) and with AVA-A-MN gap junctions removed (*unc-7* mutant,
Fig. 9 supp. 1A-C) — i.e. the oscillator is cell-intrinsic to the A-MN, not a network property.
AVA's role is dual and state-dependent: at rest, AVA-A-MN gap junctions (UNC-7) **inhibit**
(shunt) the oscillation (removing them in *unc-7* mutants gives robust oscillation, restoring
UNC-7 only in AVA dampens it again, Fig. 9D-F, **measured**); when AVA is optogenetically
activated, its chemical synapses onto A-MNs instead **evoke** rPSC bursts matching the endogenous
ones (Fig. 6A-D, **measured**). Channels/connections needed: intrinsic UNC-2 calcium current in
A-type motor neurons, plus AVA-A-type gap junctions (inhibitory/shunting at rest) and AVA-A-type
chemical synapses (excitatory on activation).

**Kawano, Po, Gao, Leung, Ryu, Zhen 2011, *Neuron* 72:572-586 (DOI 10.1016/j.neuron.2011.09.005,
PMID 22099460) — gap junctions bias the system towards forward.** No PMC or open-access full text
was reachable this session (Cell Press paywall; Semantic Scholar's own copy has the abstract
elided by the publisher) — **figure-level numbers below are a gap, not guessed.** From the
abstract itself (**measured**, calcium imaging of the motor circuit in behaving animals): C.
elegans sets movement direction by holding the forward and backward motor circuits in an
*imbalanced* activity state, and switches direction by flipping which circuit dominates. UNC-7/
UNC-9 innexin-dependent premotor-interneuron-to-motoneuron gap junctions prevent a balanced
(non-directional) state and act as a **shunt that lowers backward-circuit activity specifically**,
producing a persistent bias towards the high-forward-circuit state — i.e. gap junctions here
actively suppress backward output rather than generating rhythm themselves. This is the same
UNC-7/UNC-9 gap-junction system examined mechanistically in Gao 2018 (AVA-A-MN) and Xu 2018
(AVB-B); Kawano 2011 is the earlier paper establishing the behavioural-bias consequence.

**Head oscillator: Kaplan, Salazar Thula, Khoss, Zimmer 2020, *Neuron* 105:562-576 (PMC7014571) —
nested timescales.** Numbers (all **measured**, calcium imaging + behaviour in freely moving
animals): a three-level nested hierarchy — SMD-driven head-casts at **~1 Hz** (Fig. 3A, Fig. 1F,
Fig. 7G), nested within B-type-driven propagated body bends at **~0.5 Hz** (Fig. 1D, Summary),
nested within forward/reverse switching at **~0.05 Hz** (Fig. 1D, Fig. 8B). AIB inhibition
abolishes the forward/reverse-dependent modulation of SMD frequency and amplitude (Fig. 6B-C);
RIM/tyramine signalling gives a smaller modulation of SMDD frequency only (Fig. S6); RIB sets the
speed of the body-bend cycle and thereby which phases of it permit a head-cast (Fig. 8C-H); AVA
is described as modulating the whole slow (direction-switching) cycle (Fig. 2D). This is the
clearest evidence that the head rhythm and body rhythm are **separate oscillators at different
intrinsic frequencies**, phase-locked by specific interneurons, not one shared clock.

**Head oscillator, weaker fit: Ouellette, Desrochers, Gheta, Ramos, Hendricks 2018, *eNeuro* 5:
e0121-18 (PMC6325537) — gate-and-switch for head orientation.** This paper (likely what "Hendricks"
refers to in the task) covers SMD-to-RIA-to-motor-neuron head-steering circuitry but frames it as
a sensory gate + output switch, not as an intrinsic oscillator, and does **not** compare head
frequency to body/AVA-AVB rhythm (an explicit gap in that paper, not this search). For the actual
head-oscillator-vs-body-oscillator numbers, Kaplan 2020 above is the stronger source.

## 2. What makes AVA and AVB mutually exclusive (forward/backward switching)

**Kato, Kaplan, Schrodel, Skora, Lindsay, Yemini, Lockery, Zimmer 2015, *Cell* 163:656-669 (DOI
10.1016/j.cell.2015.09.034, PMID 26478179) — whole-brain imaging, descriptive not mechanistic.** No
PMC/open-access full text reachable this session (Cell Press paywall) — only the abstract (PMID
26478179, **measured**) and a secondary review (Kaplan, Nichols, Zimmer 2018, *Phil Trans R Soc B*
373:20170371, PMC6158224) were available. Core finding: whole-brain calcium activity traces out a
repeating cyclic trajectory; each segment of the cycle maps onto a motor command (forward, turn,
reversal), giving a "run-and-turn action sequence" (**measured**, abstract). Per the 2018 review
(not independently verified against Kato's own figures — **gap** on exact figure numbers): AVB and
RIB form one ensemble, active together; AVA, AVE, RIM and AIB form an antagonistic ensemble, active
together in the opposite phase of the cycle; AIB's reversal-coupling is "as reliable as AVA's."
Four discrete phases are named (Low, Rise, High, Fall) but no correlation coefficient or phase
duration number could be recovered this session. **Important for the task at hand: Kato 2015
itself is correlative — it describes AVA/AVB as occupying anti-phase ensembles but does not propose
or test a mechanism for why.** The mechanism comes from the papers below.

**Roberts, Augustine, Lawton, et al. 2016, *eLife* 5:e12572 (PMC4798983) — stochastic AVA/AVB/
RIM/AIB model, Lockery lab, with optogenetic validation.** Mechanism: the model pools the command
circuit into two stochastic binary units, forward (ℱ) and reverse (ℛ), each representing the
AVB/RIB-type and AVA/AVE/RIM/AIB-type ensembles respectively, coupled by six weights (two
cross-inhibitory, two self-excitatory, two external-input). The cross weights, fit to match
wild-type behavioural statistics (**derived**, Table 2, baseline switching rate A = 0.4 Hz):
**W_FR = -5.40 ± 0.43** (forward inhibits reverse) and **W_RF = -0.81 ± 0.06** (reverse inhibits
forward, about 6-7x weaker) — i.e. the model requires **asymmetric mutual inhibition**, not
symmetric, to reproduce the behaviourally observed long forward / short reversal dwell times.
This asymmetric-inhibition structure was then tested directly with optogenetics (**measured**,
Fig. 6B-E): photoactivating AVA or AVB and recording the other evokes a synaptic current whose
reversal potential sits negative of the zero-current potential, confirming **monosynaptic,
cholinergic (acetylcholine-mediated) inhibition** between AVA and AVB — i.e. ACh acting through an
inhibitory (not the usual excitatory nicotinic) receptor at this synapse. Behavioural dwell times,
wild type (**measured**, Table 1 col. A): forward dF = 5.33 ± 0.25 s, reverse dR = 1.94 ± 0.04 s,
pause states dX = 0.44 ± 0.03 s, dY = 0.21 ± 0.02 s. Switching timescale bounded by ablation
experiments: **0.40 Hz <= A <= 0.86 Hz** (**measured/derived**). Channels/connections needed: an
inhibitory ACh receptor at the AVA<->AVB synapse (molecular identity not given in what was
retrieved — candidates in the worm genome are the ACh-gated chloride channels, e.g. ACC-1/ACC-2/
LGC-46 family, already flagged as a reversal-potential gap in `RANGE_ENDS_LIT.md` item 4), plus
asymmetric synaptic strength (forward-inhibits-reverse much stronger than the reverse direction).

**Liu, Chen, Wang 2020, *Nat Commun* 11:5076 (PMC7544903) — a second, upstream loop: GABAergic
(D-type) motor neurons retrogradely inhibit AVA.** Mechanism: this is not a direct AVA-AVB synapse
but a feedback loop through the motor neurons themselves: AVA chemically excites A-type (backward)
motor neurons; A-type motor neurons cholinergically excite D-type (GABAergic) motor neurons via
LGC-46 receptors; D-type motor neurons then feed back **onto AVA itself** via GABA-A (UNC-49)
receptors, inhibiting it and biasing the whole system back towards the AVB/forward side. Measured:
optogenetically activating D-type motor neurons suppressed spontaneous postsynaptic currents in
VA5 (a backward motor neuron) by **>90%** (Fig. 2a) and evoked an outward (hyperpolarising)
current in AVA (Fig. 2b); knocking down *lgc-46* specifically in D-type motor neurons increased the
backward/forward movement ratio (Fig. 1f). Left-right AVA-AVA gap junctions (UNC-9) were shown to
amplify and balance the asymmetric GABAergic inputs reaching the two AVA cells (Fig. 9a). The
authors' own framing: this is a retrograde, motor-neuron-to-command-neuron feedback loop that
*supplements* direct AVA-AVB inhibition, not a replacement for it — it means part of what sets
"AVB wins" is downstream motor-circuit activity feeding back onto AVA, not only a single
interneuron-to-interneuron synapse.

**Kawano et al. 2011 (full citation in Section 1)** supplies the gap-junction side of the same
picture: UNC-7 (interneuron)/UNC-9 (motor neuron) gap junctions act as a **shunt that lowers
backward-circuit activity**, which (per the abstract, **measured**) is what prevents a balanced,
non-directional state and gives the resting bias towards the forward/AVB side. Separately, this
project's own `GAP_RECT_DIRECTION.md` (same research area, already on file) establishes, from Liu,
Chen, Mailler, Wang 2017 *Nat Commun* 8:14818 (PMC5364397, in-vivo dual patch clamp on AVA and
VA5) that the AVA-A-type gap junction **strongly rectifies**: current flows from the motor neuron
into AVA far more easily than the reverse direction (**measured**, "probably the strongest
rectification ever observed... in native tissues," no numeric ratio given), with Kawano 2011 and
Starich et al. 2009 (PMC2694797, Xenopus oocyte UNC-7/UNC-9 pairs) agreeing on the same polarity
but calling the effect physiologically minor. Net picture: gap-junction rectification is a real,
measured asymmetry in the backward circuit's wiring, but by itself it is a shunt/bias term, not a
bistable switch.

**Wang, Zhang, Xin, Hung, Florman, Huo, Xu, Xie, Alkema, Zhen, Wen 2020, *eLife* 9:e56942
(PMC7338056, likely "Wang 2020" in the task) — a third mechanism, downstream of AVA.** This paper
does not directly quantify AVA/AVB activity or co-activity (confirmed by direct fetch; a **gap**
for that specific question). What it does show: a separate "turning module" (AIB-RIV, electrically
coupled, with **mutual inhibition** between AIB and RIV controlling timing flexibility) terminates
a reversal and initiates an omega turn; when the turning-module neurons (RIV/SAA/SMB) are ablated,
reversals run abnormally long (**measured**), implying feedback from the turning module normally
suppresses the backward-encoding ensemble (AVA/AIB/RIM) to let the forward/AVB side resume. This
adds a third, timing-control layer on top of the direct AVA-AVB inhibition (Roberts 2016) and the
retrograde D-type-to-AVA loop (Liu 2020).

**"Li et al. 2014":** no paper matching this description (AVA/AVB switching, 2014) could be
identified with confidence this session. **Gap, not guessed** — likely a different citation than
what was searched for, or a paper not indexed under an obvious author/keyword combination.

**Bottom line for Section 2:** the exclusivity is not explained by one synapse. Three separate,
independently-measured mechanisms stack: (1) direct, asymmetric, cholinergic-but-inhibitory
synapses between AVA and AVB (Roberts 2016, strongly forward-dominant); (2) UNC-7/UNC-9 gap
junctions that shunt the backward circuit and rectify so current preferentially drains from the
motor neurons into AVA rather than the reverse (Kawano 2011; Liu 2017 in `GAP_RECT_DIRECTION.md`);
and (3) a retrograde GABAergic feedback loop from D-type motor neurons back onto AVA (Liu 2020),
plus a separate turning-module feedback that terminates reversals (Wang 2020). All of 1-3 are
needed in a model that has only a forward excitatory AVB pathway and a backward excitatory AVA
pathway wired in parallel, with no inhibitory cross-connection and no feedback loop, to produce
anything other than both staying on together whenever both receive excitatory drive.

## 3. Published open-source neuromechanical models that produce C. elegans locomotion rhythm

| Model | How rhythm is made | Neuron model | Fitted to behaviour? | Code / licence | Port difficulty onto a biophysical 302-neuron model |
|---|---|---|---|---|---|
| Boyle, Berri & Cohen 2012, *Front Comput Neurosci* 6:10 (PMC3296079); precursor Boyle, Berri, Tassieri, Hope & Cohen 2011, *Front Behav Neurosci* 5:10 (PMC3053488) | **No CPG.** Proprioceptive feedback alone: B-type neurons are binary bistable switches (Eq. 8) driven by stretch receptors integrating local+posterior curvature (Eq. 9); oscillation is closed-loop, through the body's own shape, not a neural clock | Abstract (binary bistable), with a conductance-based variant (Eq. 14) added for validation against optogenetic data | Drag coefficients from slender-body theory/Wallace 1969 (literature); neural/muscle params "chosen" to match behaviour qualitatively, not fitted by optimisation | Supp. info S14, CC-BY-NC 3.0 | Medium: mechanism (proprioceptive bistable switch) is a hypothesis, not drawn from Cook 2019 wiring; would need re-deriving from real B-type connectivity and is explicitly a *propagation*, not generation, mechanism (same gap as Wen 2012, Section 1) |
| Izquierdo & Beer 2018, *Phil Trans R Soc B* 373:20170374 (PMC6158225) | Head circuit (SMD/RMD) as the oscillator; 40/46 evolved solutions need stretch-receptor feedback to sustain head oscillation, 6/46 oscillate intrinsically; VNC only propagates via short-range posterior proprioception, does not generate | Abstract leaky-integrator/isopotential nodes with sigmoid synapses | **Evolved**: genetic algorithm, 30 free parameters, fitness = match worm's average agar velocity; 100 runs, 46 solutions at fitness >= 0.95 | github.com/edizquierdo/RoyalSociety2018; licence not stated | Hard: head-only circuit, evolved weights with no claim to be the real synaptic strengths; would need redoing with real head connectivity and biophysical channels |
| Olivares, Izquierdo & Beer 2018, *Netw Neurosci* 2:323 (PMC6145852) and 2021, *Front Comput Neurosci* 15:572339 (PMC7930337) | Multiple VNC pattern generators (motivated directly by Fouad 2018's distributed-oscillator finding), coupled by gap junctions between motor neuron classes; explicitly **no proprioceptive feedback needed** in this version | Abstract rate-coding neurons, first-order nonlinear dynamics (Eq. 3), sigmoidal synapses | **Evolved**: genetic algorithm, 44 free parameters, fit to match measured bending frequency **0.44 Hz** and forward velocity **0.22 mm/s** (**measured** targets, from C. elegans experiments cited in the paper); 160 runs, 15 filtered solutions (Fig. 2) | Not stated in the fetched text (gap) | Hard: uses a repeating "identical subunit" for 6 motor classes (AS/DA/DB/DD/VA/VB) across 7 segments, not the real connectome (paper's own words: "connectome data is incomplete for the VNC," relies on Haspel & O'Donovan 2011 statistics); omits ~290 of 302 neurons entirely. Porting to the full connectome means replacing the repeating-unit assumption and scaling to hundreds of unknown parameters |
| Denham, Ranner & Cohen 2018, *Phil Trans R Soc B* 373:20180208 (PMC6158217) | **No CPG.** Same family as Boyle 2012: binary B-type activation driven purely by posterior-curvature proprioception; oscillation is a self-organised neuromechanical property, not network-intrinsic | Abstract binary activation function along the body (Fig. 1a) | Mixed: Young's modulus (100 kPa), drag coefficients, proprioceptive range (0.5) from literature/prior models (Table 1); reproduces the measured swim-crawl transition across viscosity | bitbucket.org/leedswormlab/curve-worm-royal-society-paper; licence not stated in fetched text (gap) | Medium-hard, same caveat as Boyle 2012: this is a propagation-only mechanism, and the paper's own point is to characterise the phase-lag *signature* of proprioceptive vs CPG control, not to supply a validated generator |
| Sarma, Lee, Portegys, et al. 2018, *Phil Trans R Soc B* 373:20170382 (PMC6158220) — OpenWorm (c302 + Sibernetic) | **No rhythm produced.** c302 computes neuron/muscle activation, passed one-way to Sibernetic (SPH body solver); paper states explicitly "currently only a uni-directional flow of information from c302 to Sibernetic," with sensory feedback "under development" | c302: abstraction-dependent, up to HH-like conductance-based (see this project's own `c302_port.md`, which ran the C2 level and also got no rhythm, all-"BlindGuess" parameters) | Not fitted; paper states the model's "level of detail... is inadequate for biological research" | github.com/openworm/c302 (MIT), Sibernetic (separate repo, GPLv3 per OpenWorm docs) | This project has already ported c302 itself (see `c302_port.md`): confirms open-loop, no validated rhythm, same symptom (saturating depolarisation, not oscillation) as what prompted this research task |
| BAAIWorm / MetaWorm 2024, *Nat Comput Sci* 4:1021 + bioRxiv eworm preprint 2024.02.22.581686 | Closed-loop brain-body-environment: sensory neurons sense simulated food concentration, network drives muscles, body motion changes sensory input. **Rhythm appears driven by the periodicity of the sensory input loop, not a confirmed autonomous CPG**: the paper's own stated limitation is that "when sensory input was non-periodic, the trajectory... was not as regular as that observed in the experiment" (Discussion) — i.e. take away a sufficiently periodic external drive and the regular undulation degrades. No oscillation frequency is given for AVB or B-type specifically in what was retrieved. Traveling dorsal/ventral muscle-activation waves are shown (Fig. 8E) but not clearly attributed to an intrinsic network oscillator | Biophysical, multicompartment, NEURON, 14 ion channel classes per neuron, realistic morphology (136-neuron core brain; full integration paper adds body+environment) | Passive params and channel densities tuned (reported as genetic algorithm in secondary sources, not confirmed from primary text) to match single-neuron electrophysiology; network-level validation is a static activity **correlation-matrix match** to whole-brain imaging data (already documented in this project's `OPENWORM_AND_NOVELTY.md` section 1.3), not a dynamic rhythm fit | Not confirmed in this search (gap) | This is the closest published analogue to this project's own model (same neuron model type, same connectome-scale ambition) and its own text suggests it has the **same open question we have**: whether the undulation is genuinely network-generated or scaffolded by input periodicity. Worth direct comparison/contact, but porting its method does not obviously solve the rhythm problem — it may not have solved it either |

**Other models, noted but not deeply fetched this session (time-boxed):** Ji, Fouad, Teng, et al. 2021,
*eLife* 10:e69905 (PMC8560089) — phase-response analysis arguing the rhythm is a **relaxation
oscillator** (abrupt switching between two quasi-stable states, not a smooth limit cycle), which
would predict specific phase-response-curve shapes; relevant to *which kind* of oscillator a fitted
model should aim for, not itself a connectome-scale model. Deng, Denham, Arya, Yuval, Cohen & Haspel
2021, *eNeuro* 8 (PMC7986531) — same Cohen/Haspel lineage as Denham 2018, reports that inhibition
(not just excitation) is required for the fast undulatory gait specifically. modWorm (Kim, Florman,
Santos, Alkema & Shlizerman) and EP-GAN are already covered in this project's own
`OPENWORM_AND_NOVELTY.md` (section 1.4): modWorm tunes conductances "with respect to a given
locomotion task" over the full 279-neuron mapped connectome but its own fitting method is not
detailed as rhythm-specific; EP-GAN fits single neurons one at a time and was never used to assemble
a whole-circuit rhythm.

**Pattern across every open-source model found:** every model that actually *produces* a rhythm
(Boyle 2012, Izquierdo & Beer 2018, Olivares 2018/2021, Denham 2018) uses **abstract neurons**
(binary, leaky-integrator, or rate-coding) with **evolved or hand-chosen weights**, not biophysical
HH-type channels from literature ranges, and most use an incomplete or repeating-unit connectome,
not the full Cook 2019 wiring. Every model found that uses **biophysical, connectome-scale, literature-
range neurons** (c302/Sibernetic via Sarma 2018 and this project's own port; BAAIWorm, with caveats
above) has **not** been shown to produce a validated, self-sustained locomotor rhythm from first
principles.

## 4. Whole-brain data usable for fitting AVA/AVB/motor dynamics

- **Kato, Kaplan, Schrodel, et al. 2015, *Cell* 163:656 (PMID 26478179, no PMC).** Whole-brain
  calcium imaging (GCaMP) in immobilised/weakly-moving animals, with simultaneous fictive motor
  output; this is the dataset behind the AVB/RIB vs AVA/AVE/RIM/AIB anti-phase ensemble finding
  (Section 2). **Measured.** Where to get it: not found as a standalone public repository in this
  search (**gap**) — the paper predates the field's current data-sharing norms; likely available
  on request from the Zimmer lab or embedded in later re-analyses (e.g. Brennan & Proekt 2019,
  PMC6624016, which models "conserved macroscopic dynamics" from this and related datasets).

- **Atanas, Kim, Wang, Bueno, et al. 2023, *Cell* 186:4134 (PMC10836760) — the largest and most
  directly usable dataset for this task.** Whole-brain calcium imaging (nuclear-localised GCaMP7f
  + NLS-mNeptune2.5, spinning-disk confocal) in **14 freely-moving animals**, averaging **143 ± 12
  head neurons per animal** (**measured**, Fig. 1), plus 40 additional animals used for NeuroPAL-
  based identity confirmation. Simultaneous behaviour: velocity, head curvature, angular velocity,
  feeding rate, body posture, from brightfield tracking (Fig. 1). Direct result for this task's
  question (**measured**, Fig. 4A): **AVB, RIB, AIY and RID encode forward movement; AVA, RIM and
  AIB encode reversal** — the same ensembles as Kato 2015, now with identified, targetable neuron
  classes and a published probabilistic encoding model (CePNEM, Fig. 2) that assigns each neuron a
  timescale and tuning curve rather than a single on/off label. Optogenetic silencing of AIM, RIC,
  AUA, AVL, RIF confirmed/altered predicted velocity encoding (Fig. S4I, **measured**). **Publicly
  available**: wormwideweb.org, plus Zenodo/GitHub DOIs in the paper's Key Resources Table — this
  is the dataset to fit AVA/AVB/motor dynamics against if a quantitative target is needed. Note:
  **Morrison & Young 2025, *PLoS Comput Biol* (PMC12768384)** already built a 15-neuron
  (5 forward: AVB-type/RIB-type cluster, 8 reversal: AVA-type/AIB-type cluster, 2 AVD) biophysical-
  ish network fit to 22 of these Atanas datasets plus White 1986 connectivity and voltage-clamp
  data, and reproduced the forward/reversal high/low-state switching (Fig. 3) — code at
  github.com/mmtree/Celegans_premotor. This is close prior art for exactly the fitting step Section
  5 below recommends, on a 15-neuron scale, not yet the full 302.

- **Uzel, Kato, Zimmer 2022, *Curr Biol* 32:3443 (DOI 10.1016/j.cub.2022.06.039, PMID 35809568, no
  PMC found).** Re-analysis combining the Cook 2019-era connectome's graph structure with
  nervous-system-wide activity correlations (presumably the Kato 2015 dataset or a successor).
  Finding (**measured**, from the abstract only — full-text figures not reached, **gap**): non-local
  connectome features (triplet motifs, input similarity) predict functional (activity-correlation)
  relationships between neurons better than local connection strength; a small set of **hub
  neurons** is disproportionately responsible for brain-wide correlation structure, and silencing
  multiple hubs disrupts those correlations. Relevant to this task if the fitting strategy in
  Section 5 needs to prioritise which few neurons/synapses matter most for global dynamics.

- **Yemini, Lin, Nejatbakhsh, Varol, Sun, Mena, Samuel, Paninski, Venkatachalam, Hobert 2021,
  *Cell* 184:272 (PMC10494711) — NeuroPAL.** Not an activity dataset; a multicolour fluorescent
  landmark strain/method for unambiguously identifying all ~302 neurons by position and colour
  code in a live animal. Used as the identity-confirmation layer underneath Atanas 2023 (above) and
  increasingly standard in the field (e.g. the 2025 community-dataset-unification paper, Sprague et
  al., *Cell Rep Methods*, PMC11840940, which merges multiple labs' whole-brain imaging datasets
  using NeuroPAL-based registration). Relevant here only as infrastructure: it is what makes
  cross-dataset, cross-lab neuron identity consistent enough to pool recordings (e.g. combining
  Atanas 2023 with other whole-brain datasets) when fitting a 302-neuron model.

## 5. Summary (inference)

**Your inference, not a citation.** Three things recur across every measured mechanism in Sections
1-2, and every one of them is a specific nonlinear or asymmetric structure, not a value that can
sit quietly at a "midpoint":

1. **The AVA-AVB and AVA-A-type connections in the real circuit are strongly asymmetric and partly
   inhibitory, not symmetric excitatory drive.** Roberts 2016 had to fit forward-inhibits-reverse
   about 6-7x stronger than reverse-inhibits-forward (W_FR = -5.40 vs W_RF = -0.81) to reproduce
   real dwell times, and confirmed by optogenetics that the AVA-AVB synapse is monosynaptic and
   *inhibitory* despite being cholinergic. Kawano 2011 and Liu 2017 add a rectifying gap junction
   that specifically shunts the backward circuit. Liu 2020 adds a retrograde GABAergic loop from
   D-type motor neurons back onto AVA. If a model's AVA-AVB connection is parameterised at a
   literature-midpoint *conductance* without the correct *sign* (inhibitory) and the correct
   *asymmetry*, both AVA and AVB will simply rise together whenever both receive excitatory sensory/
   command drive — which is exactly the reported symptom (AVA and AVB co-depolarised).

2. **B-type motor neurons need to cross a bifurcation, not just depolarise.** Xu 2018's own model
   states explicitly that AVB's tonic input must push B-type neurons from a stable fixed point into
   a limit cycle; Gao 2018 shows the backward (A-type) analogue is an UNC-2-dependent intrinsic
   oscillator that is abolished or weakened when UNC-2 conductance is too low. A conductance sitting
   at a literature-midpoint that is sub-threshold for this bifurcation will depolarise the neuron a
   little and stop there — never entering the oscillatory regime. This matches the reported symptom
   precisely: B-type motor neurons moving only 1-1.5 mV, i.e. perturbed but not switched into a
   limit cycle.

3. **Every open-source model that actually produces a rhythm (Section 3) relies on a strong,
   explicitly-chosen nonlinearity or asymmetry** (binary bistable switches, evolved sigmoid gains,
   relaxation-oscillator-like switching per Ji 2021) and most are not biophysical, connectome-scale
   models at all. The two efforts that *are* biophysical and connectome-scale and literature-range-
   constrained — c302/Sibernetic (Sarma 2018, and this project's own `c302_port.md`) and BAAIWorm —
   show the same failure mode reported here: c302's own C2 run saturated into one tonic, near-
   uniform depolarisation across the network rather than oscillating, and BAAIWorm's own stated
   limitation is that its undulation regularity degrades once the external sensory drive is no
   longer periodic, i.e. it has not clearly demonstrated an autonomous network oscillator either.
   That is independent-ish confirmation that "all literature-midpoint, all mechanisms nominally
   switched on" is not sufficient for rhythm in this model *class*, not a problem unique to this
   project's implementation.

**What the literature suggests doing first:** this points at (b), fitting within literature ranges,
over (a), porting a whole published model wholesale — but fitting aimed at specific, named targets
rather than a broad range sweep. None of the working rhythm models in Section 3 can be ported
directly: the abstract ones would throw away the biophysical/connectome fidelity that is the point
of this project, and the biophysical/connectome-scale ones (c302, BAAIWorm) have the same unsolved
problem. The literature instead identifies which few parameters and which qualitative properties to
fit first, in priority order: (i) the sign and relative strength of the AVA<->AVB synapse, fit to
reproduce the measured asymmetric dwell times (Roberts 2016, Table 1) and the anti-correlated AVB/
RIB vs AVA/RIM/AIB ensembles (Kato 2015; Atanas 2023 Fig. 4A — the directly fittable public dataset);
(ii) the A-type/B-type intrinsic calcium conductance (UNC-2-type) and the AVB-B gap-junction
strength, tuned to sit past the bifurcation threshold rather than merely in-range (Gao 2018; Xu
2018); (iii) only after (i)-(ii) reproduce the measured ensemble switching pattern, revisit whether
a distinct head oscillator (Kaplan 2020, ~1 Hz) needs to be added on top to get phase structure right.
Morrison & Young 2025 (PMC12768384) already demonstrates this exact strategy works at a 15-neuron
scale, fit to Atanas 2023 — a close, concrete precedent and starting point rather than a ground-up
derivation.
