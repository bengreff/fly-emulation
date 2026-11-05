# C. elegans whole-animal emulation: the plan

Written 2026-11-04 23:20 CST (from `date`), from Ben's ten binding answers (`~/director/goals.md`, fly-emulation
section), `docs/worm/STATE_OF_THE_ART.md` (prior efforts, data by layer, a 90-item behaviour corpus, gaps),
`docs/worm/research/adoption_tests.md` (tool install tests on backhouse), the data on backhouse
(`~/worm-data`, `docs/worm/MANIFEST.md`) and tonight's spike (`docs/worm/SPIKE.md`). This plan does not repeat
the state-of-the-art survey; it cites its sections.

Labels: **measured** (read off data or timed by us), **derived** (arithmetic on measured numbers, shown),
**inferred** (taken from a source by reasoning, e.g. homology), **guessed** (an estimate with no direct
basis, kept only where a plan needs a number).

## 0. Verdict first

1. **Every layer Ben listed is needed, but not at once.** The behaviour corpus has items that cannot be scored
   without each layer (section a, "needed for" column), so none can be dropped from the full scope. What the
   plan controls is the order and the test of necessity: each mechanism enters neutral (off or unity), and stays
   only if it improves held-out prediction. That gives Ben the answer to "which mechanisms are actually needed",
   per behaviour, as a measured ablation result rather than a guess.
2. **The engine is Jaxley, with NEURON as the CPU reference.** Jaxley installs with CUDA on backhouse, runs the
   Nicoletti 2024 channel library to 0.000 mV RMS of NEURON at the published AIY settings (measured), takes
   gradients through 8 s of biology, and runs a whole-worm-sized network (446 cells, 1784 compartments, 4841
   chemical connections, 1342 gap-junction pairs) at 2.36 s wall per biological second forward and 19.3 s with
   gradients, on one CPU core (measured, section b). That is fast enough to fit and run the whole worm on
   backhouse at reduced compartment counts; full EM-resolution compartments cost more (derived, section c.5).
3. **Throwing compute works for the neurons; the body is the open risk.** Sibernetic (the validated 3D soft
   body) did not link in WSL (no OpenCL platform; measured). The plan fits with a fast Cosserat rod in JAX and
   cross-checks against a 3D body, which needs Sibernetic on Windows-native OpenCL or a GPU port (DECISION
   NEEDED 4).
4. **Code layout.** `src/bioemu/` is the new organism-agnostic core (tonight: NeuroML morphology to SWC, and a
   fused multi-channel Jaxley membrane built from any channel library); `src/wormemu/` is the worm species layer
   (tonight: the Nicoletti 2024 channel library); `src/flyemu/` is untouched while the fly is paused. Generic
   fly modules move into `bioemu` only when the fly resumes, with the fly battery as the regression check
   (section d). Reason: Ben's answer 9 (same repo, organism-agnostic) without risking the fly's adopted state.
5. **The spike failed its pre-registered training bar and passed both held-out bars** (measured, `SPIKE.md`
   RESULTS). One AIY neuron, 4 compartments, its CeNGEN channel set (12 densities) and, side by side, the
   published 7-channel set, each fitted with gradients to one cell's current-clamp steps: training mean RMSE 4.79
   and 4.80 mV against a bar of 4; held-out steps 3.78 and 3.77 mV mean (bar 5), worst 5.68 and 5.81 (bar 8);
   held-out population voltage clamp 100% inside mean +/- 2 SD (bar 80%, but the bar does not discriminate:
   F-W0-6). The two channel sets fit equally well and the published fit drives SHL-1 to near zero, consistent with
   CeNGEN calling it absent. The misfit is systematic (steady-state voltages 5-8 mV off), so the next step is
   more biology (bounded gating shifts, soma and neurite densities), not more iterations. Cost on 2 CPU cores
   with backhouse heavily loaded: 1.5 h per fit, 5.4 gradient and 31-33 forward simulations of 8 s per second.
   The fits ran on CPU, not the GPU (a deviation, recorded before scoring; F-W0-4).

## a. Mechanism ledger, layer by layer

Grain (Ben's answer 6): cells, plus molecular signalling where it carries state. Neurons are multicompartment
from morphology with CeNGEN channels (answer 2); every layer in answer 3 is in; the body is 3D soft body plus
fluid/agar with a fast rod for fitting (answer 4). Data paths are on backhouse under `~/worm-data/` unless
marked "not local".

Cost classes (per simulated second of the whole animal, relative to the neurons):
- **K0** static table, no runtime cost.
- **K1** a few state variables per cell or per connection; under about 10% of the neuron cost (guessed from
  state counts; a synapse has 1 state against about 17 per compartment for the membrane, measured from the
  library).
- **K2** comparable to the neuron membrane: scales with compartments x time steps.
- **K3** dominant and separate: 3D continuum mechanics on the GPU.

"Needed for" cites behaviour numbers from STATE_OF_THE_ART section 3. Items 54-60 are male and out of scope
for the first animal (answer 7); items 76-78, 83-85 and 88-89 are structural, metabolic or model-comparison
items rather than behaviours, and are scored as checks.

| # | Layer and mechanism | Data source (local path) | Measured | Fitted or inferred | Cost | Needed for |
|---|---|---|---|---|---|---|
| 1 | **Cell inventory**: 302 neurons in 118 classes, muscles, glia, end organs | Cook 2019 node list (`cook2019/`); CeNGEN class list | identity and count: 460 nodes in the hermaphrodite graph (302 neurons, 132 muscles, 26 end organs; Cook 2019, quoted in SotA s2); 446 of them carry chemical synapses (measured from the adjacency tonight) | nothing | K0 | all |
| 2 | **Morphology and compartments** | OpenWorm CElegansNeuroML (`morphologies/`, Virtual Worm geometry); EM nerve-ring skeletons in Witvliet 2021 (`witvliet2021/`, coverage to be checked); Brittin 2021 contactome (not local) | soma and neurite paths of the Virtual Worm atlas; EM contact areas | the Virtual Worm geometry is itself a reconstruction, so label **inferred** geometry; compartment count per cell is a numerical choice, checked by convergence | K2 (linear in compartments) | all neural items; 80 |
| 3 | **Ion channels per neuron class**: presence | CeNGEN thresholds (`cengen/`, partial: thresholds, bulk tsvs, one neuron-only single-cell object) | transcript presence per class, at a threshold | which threshold maps to a functional channel is **inferred** (tonight: threshold 2; DECISION NEEDED 5) | K0 | all neural items |
| 4 | **Ion channel kinetics** | Nicoletti 2019/2024 library (13 channels, ported and checked tonight); BAAIWorm `eworm` .mod files (adds egl-2, egl-36, irk, kqt-3, kvs-1, shk-1; adoption_tests s5) | in the source papers, from heterologous and native recordings | kinetics shared by gene across all cells (one value per gene, not per cell); each port checked against NEURON before use | K2 | all neural items |
| 5 | **Channel densities, Cm, leak, Ra** per class | direct ephys for a minority of classes (AIY, RIM, AFD in `ephys/naudin2022_liu_aiy_rim_afd/`; AWA in Liu 2018, 809 MB, not local; AWC, RMD, ASER, AVA, VA5, VB6, VD5 via published models and figures) | current-clamp and voltage-clamp traces where they exist | **fitted**, bounded, one value per class; classes without ephys get bounds from the recorded classes and are constrained by circuit data (rows 7, 18) | K0 (parameters) | all neural items |
| 6 | **Calcium handling**: nanodomains, bulk pool, buffers | Nicoletti 2024 (nanodomain coupling SLO-1/2 to EGL-19/UNC-2, bulk pool for KCNL) | in source | pool time constants and volumes **fitted** within bounds | K1 | all neural items |
| 7 | **Chemical synapses**: count, sign, graded release, receptor kinetics | Cook 2019 counts (`cook2019/`); Witvliet 2021 eight animals (`witvliet2021/`); transmitter identity (published atlases; not yet local); receptor genes from CeNGEN; Randi 2023 functional atlas (`randi2023/`, 23,433 probed pairs) | EM synapse counts per pair; transmitter identity per neuron; receptor gene presence; functional sign and kinetics for probed head pairs | sign **inferred** from transmitter plus postsynaptic receptor; strength = EM count x a unit conductance **fitted** per (transmitter, receptor class), not per synapse; graded release curve per presynaptic class **fitted** | K1 | 8-30, 36, 61-65, 72-75 |
| 8 | **Gap junctions per innexin** | Cook 2019 gap counts (1342 cell pairs among the 446 cells, measured tonight); Bhattacharya 2019 innexin expression (`misc/`); UNC-7/UNC-9 heterologous ephys (literature) | gap counts; innexin expression per class | conductance per innexin pairing **fitted** in bounds; rectification **inferred** from the closest characterised pair; most pairings uncharacterised (SotA s4) | K1 | 8, 9, 11-13, 72, 90 |
| 9 | **Neuropeptides and receptors** | Ripoll-Sanchez 2023 network and Beets 2023 peptide-GPCR pairs (`peptide_connectome/`) | which peptide can activate which receptor; in-vitro potency for deorphanised pairs (Beets 2023) | release rate, diffusion in the pseudocoelom, degradation, G-protein coupling to channels: **inferred** mechanism, **fitted** rates in bounds; one concentration state per peptide per body region | K1 | 37-42, 31, 40, 65, 74, 75 |
| 10 | **Monoamines**: serotonin, dopamine, tyramine, octopamine | Bentley 2016 monoamine connectome (`peptide_connectome/`); receptor genes from CeNGEN | producing cells; receptor expression | release, clearance and receptor coupling **fitted** in bounds (the fly's `neuromod.py` pool mechanism carries over) | K1 | 27, 35, 37, 43-44, 65 |
| 11 | **Glia** (56 cells; amphid and cephalic sheath first) | expression data partial (CeNGEN is neuron-only; glial atlases not yet local) | anatomy | mechanisms (K+ and Cl- handling around sensory endings, sheath shaping of AFD/ASH responses) **inferred**; parameters **fitted**; borrow mechanism, not values, from other invertebrates | K1 | 14, 25-28, 64 |
| 12 | **Body-wall muscle** (95 cells) and excitation-contraction | published BWM ephys and the Du/Crodelle 2024 whole-cell model (SotA s1-2); Cook 2019 NMJ counts | BWM action potentials and currents | channel densities **fitted** as for neurons; Ca to force (Hill-type) **inferred** with bounds | K2 for membrane, K1 for force | 1-10, 67, 72, 79 |
| 13 | **Pharynx**: 20 pharyngeal neurons, pharyngeal muscle | Cook 2019 pharyngeal graph; electropharyngeogram literature | E/P spike signature, pump rate | pharyngeal muscle channel set **inferred** from body-wall muscle plus tissue expression; **fitted** to the EPG | K2 | 32-35, 68 |
| 14 | **Intestine and defecation clock** (20 intestinal cells) | WormBook defecation chapter; IP3 receptor literature | cycle period about 45-50 s (literature, not checked tonight) | IP3/Ca oscillator **inferred** mechanism, rates **fitted**; peptide output to AVL/DVB through row 9 | K1 | 49-53 |
| 15 | **Egg-laying system**: HSN, VC, vulval and uterine muscle, egg production | Cook 2019; egg-laying literature | egg-laying rates and intervals | vulval muscle **inferred** from body-wall muscle; egg supply as a lumped germline rate **fitted** | K1-K2 | 43-47, 53 |
| 16 | **Other non-neural cells**: hypodermis and seam, excretory canal, coelomocytes | anatomy only | anatomy | lumped where they carry state (osmotic balance, body pressure); otherwise mechanical tissue only (row 21) | K1 | 25, 81 |
| 17 | **Sensory transduction** per modality: salt (ASE, guanylyl cyclases to cGMP to TAX-2/4), odour (AWA, AWC), temperature (AFD), nociception (ASH, FLP, PVD), touch (ALM, AVM, PLM, PVM), O2 and CO2 (URX, AQR, PQR, BAG), light (LITE-1), proprioception (DVA, SMD, B-type motor neurons) | modality literature; calcium response datasets | dose-response and adaptation curves where published | cascade structure **inferred**, rates **fitted** in bounds; the world reaches the brain only through these (standing rule) | K1 | 11-31, 36, 64, 70-72 |
| 18 | **Slow intracellular signalling that carries state**: cGMP/PKG (EGL-4), CaMK nuclear translocation (AFD adaptation over hours), receptor trafficking (GLR-1), insulin/DAF-16, TGF-beta (DAF-7), CREB (CRH-1) | literature per pathway; CeNGEN baseline | steady-state expression; a few time courses | each pathway one or two state variables per cell, modulating densities inside their bounds; rates **fitted** to the slow behaviours | K1 (stepped at about 1 s) | 15-16, 26, 31, 37-40, 61-65, 69 |
| 19 | **Gene expression beyond row 18** | CeNGEN, condition-dependent RNA-seq (not local) | baseline transcripts | only where it carries state (answer 6); otherwise a fixed parameter source, not a dynamic layer | K1 | 31, 66-69 |
| 20 | **Metabolism**: energy, fat, feeding state | iCEL1273 genome-scale model and the 2025 flux landscape (not local) | tissue-level fluxes | a few lumped states per tissue (intestinal fat, energy charge) driving insulin/TGF-beta outputs, **fitted**; the genome-scale model is a check, not run per step | K1 | 37, 40, 47, 66, 83-85 |
| 21 | **Body**: 3D soft body (cuticle, muscle, pseudocoelom pressure) | geometry from the Virtual Worm; modulus measured but spread over 2+ orders by method (SotA s2) | geometry; stiffness ranges by technique; bulk response under pressure | stiffnesses **fitted** inside the technique-matched range; Cosserat rod for fitting, 3D continuum for the cross-check | K3 (3D), K1 (rod) | 1-10, 67, 81-82 |
| 22 | **Environment**: Newtonian and viscoelastic fluid, agar, chemical and temperature fields, food lawn, O2/CO2, tap and touch | gait-vs-viscosity data (Fang-Yen 2010); plate assay geometries | drag regimes, field geometries | resistive-force or slender-body drag for the rod path; SPH or FEM for the 3D path; agar surface coefficients **fitted** to crawling kinematics | K1 (rod) to K3 (3D) | 1-7, 18-30, 36, 42 |
| 23 | **Observation models**: GCaMP (Ca to fluorescence), tracker skeleton and features, NeuroPAL identity uncertainty | Atanas 2023 (`atanas2023/`), Randi 2023 (`randi2023/`), Tierpsy feature definitions | indicator kinetics (literature), imaging rates | indicator parameters **fitted** per indicator, shared across cells; needed so the model is scored against what the instruments saw, not against inferred activity | K1 | 74, 75, 86-87 |

Fill fraction. As for the fly, every row above becomes a set of blanks in data tables (mechanism, parameter,
bounds, evidence label, source), and progress is the fraction filled on evidence. The tables do not exist yet
(roadmap W1).

## b. Adoption verdicts, with evidence

All install tests ran on backhouse (WSL2 Ubuntu, i7-14700K, RTX 4070 Ti SUPER) on 2026-11-04;
details in `docs/worm/research/adoption_tests.md` and `SPIKE.md`.

| Tool | Installs | Runs | Licence | Fidelity (evidence) | Speed (measured) | Verdict |
|---|---|---|---|---|---|---|
| **Jaxley 0.14.0** (JAX 0.12, CUDA 12) | yes | yes, CPU and GPU | Apache 2.0 (LICENSE file in the installed package) | Nicoletti 2024 AIY reproduced at 0.000 mV RMS vs NEURON; all 13 channels on: at most 0.009 mV RMS, 0.16 mV max (once E_Ca is pinned; see FINDINGS) | whole-worm-sized network (446 cells x 4 compartments, full 13-channel membrane, all chemical and gap connections), dt 0.1 ms: forward 2.36 s and forward+gradient 19.3 s wall per biological second on one CPU core; on the GPU 3.18 s and 21.2 s while another user held it at 65-99% utilisation; batched GPU: section c.5 | **Adopt** as the simulator and the fitting engine, with one fix before network fits: its synapse linearisation makes gap junctions fully explicit, unstable on highly coupled cells at dt 0.1 ms; a half-implicit patch is stable but inaccurate, so the coupling must be solved implicitly on both sides (F-W0-5). Done 5 Nov: `ImplicitGap` matches NEURON to 1.2e-5 mV and stays stable, at about 2x the explicit gradient cost (F-W0-9) |
| **NEURON 9.0.2** | yes | yes | BSD-3 | the reference the published worm models were written in | about 25-70x slower than Arbor on toy cases (adoption_tests s1-2) | **Adopt as the CPU reference path** (standing rule); every new channel is checked Jaxley vs NEURON before use |
| **Arbor 0.12.2** | yes | yes | BSD-3 | same cable equation as NEURON | 1 s of a 100-compartment cable in 0.0048 s wall (4 threads) | **Hold**. Not differentiable; worth it only if long forward runs (hours to days) outgrow Jaxley |
| **OpenWorm c302** 0.12.1 (+ pyNeuroML, jNeuroML) | yes | yes | MIT (c302); LGPL-3 (pyNeuroML) | cells are leaky-integrator or simplified conductance models, not per-gene channels | 2 neurons + 1 muscle near real time | **Use as a structure source and baseline**, not as the neuron model (it is below answer 2's bar) |
| **Sibernetic** (3D SPH body) | compiles, does not link | no: no OpenCL platform in WSL | MIT | the only validated open 3D worm body | not measured | **Untested**; try a Windows-native OpenCL build next (NVIDIA ships OpenCL with the Windows driver), else port its SPH to JAX or Warp (DECISION NEEDED 4) |
| **BAAIWorm / MetaWorm** (`eworm`) | yes (eworm only) | yes | Apache 2.0 | NEURON multicompartment cells with gene-named channels, wired by the connectome | 136-cell circuit, 100 ms in 0.65 s wall on 4 threads, about 0.15x real time | **Adopt pieces**: the extra channel .mod files (port and check as with Nicoletti), and its cell models as a comparison. The GPU body and environment (OptiX) were not tested |

## c. Fitting architecture

### c.1 One parameter vector, all bounded, shared by class

Every unknown is a biological quantity with a cited range, shared by class (neuron class, muscle class,
innexin pairing, transmitter-receptor pairing, peptide), and labelled fitted. No per-synapse, per-cell or
per-trace free knob; no decoders. Each value is stored as an unbounded variable passed through a sigmoid onto
its range (log-scaled for densities and rates), so the optimiser cannot leave the range and a value sitting at
a bound is flagged as "set by the bound". This is what the spike does (`scripts/worm/fit_aiy.py`).

Rough size (guessed): 118 neuron classes x (about 8 CeNGEN-present channels + Cm, leak, leak reversal, Ra) is
about 1,400; synaptic unit conductances and release curves per (transmitter, receptor class) are about 100;
innexin pairings about 30; peptides and monoamines about 300 (release, clearance, receptor coupling); muscle,
body and environment about 50. About 2,000 parameters in all (guessed). A reverse-mode gradient costs about the same for 10 or 2,000
parameters (reverse mode), which is why one joint fit is feasible.

### c.2 Losses, by dataset

Each loss compares what the instrument saw (row 23 observation models), not inferred internal quantities.

| Loss | Dataset | What is compared | Fits mainly |
|---|---|---|---|
| L1 single-cell ephys | Naudin 2022 (AIY, RIM, AFD), Liu 2018 (AWA), the Nicoletti 2019/2024 source recordings (AWC, RMD, AVA, VA5, VB6, VD5; figure digitising needed), muscle ephys | voltage traces under current clamp; currents under voltage clamp | rows 4-6, 12 |
| L2 signal propagation | Randi 2023 functional atlas | response of neuron i to optogenetic stimulation of neuron j, through the GCaMP model: sign, amplitude, delay | rows 7-10 |
| L3 whole-brain dynamics | Atanas 2023 (freely moving, NeuroPAL), Kato 2015 | statistics, not trajectories: correlation structure, state-transition rates, the behaviour-encoding of identified neurons. Spontaneous activity is not repeatable trial by trial, so trajectory MSE would reward memorising | rows 7-10, 18 |
| L4 locomotion kinematics | Open Worm Movement Database, Yemini 2013, Fang-Yen 2010 | bend frequency, wavelength, speed, gait vs viscosity, reversal and turn rates | rows 12, 17, 21-22 |
| L5 sensory behaviours | chemotaxis, thermotaxis, touch, tap assays (corpus 11-30) | assay indices and response probabilities, with the plate geometry simulated | row 17 |
| L6 slow states | roaming/dwelling, quiescence, lethargus, egg-laying, defecation (corpus 37-53) | bout durations, rates, cycle periods over hours | rows 9-10, 14-15, 18, 20 |

Order: L1 per class first (cheap, minutes per class), then L1-L2 jointly on the head circuit, then everything at
once. Each later stage starts from the earlier fit and keeps the earlier losses in the objective, so fitting
circuits cannot silently break single cells.

### c.3 Optimisers

- **Gradients** (Adam, many starts) through Jaxley for driven, short windows: ephys protocols, Randi
  stimulation responses, a few seconds of locomotion with the rod body. Gradients through long chaotic runs are
  unreliable, so long runs are cut into windows; each window starts from the model's own state (from its own
  earlier run under the same conditions), never from an optimised per-window state (standing rule: no hidden
  state that encodes the future target).
- **Evolutionary search** (CMA-ES, batched on the GPU) for what gradients cannot reach: hours-long statistics
  (L6), discrete events, the 3D body, and the slow parameters of rows 18-20. Ben's answer 10.
- **Many starts and a population**: every fit runs many starts; the spread of good solutions is reported, not
  just the best, because a parameter that the data do not pin down should be shown as such.

### c.4 Held-out split for the blind-prediction bar (answer 5)

Spend once; written down and seeded before the first fit of each stage; kept in the sealed register in HANDOFF.

- **Ephys**: per class, hold out a protocol (e.g. voltage clamp when fitting current clamp) and, where n allows,
  whole cells. The spike does this (held-out current steps and the population voltage-clamp I-V).
- **Randi 2023**: hold out 20% of the stimulated neurons, with all their responses (by neuron, not by trial, so
  a held-out pair cannot be learned from its own repeats).
- **Atanas 2023**: hold out whole animals (about 25%) and at least one whole condition.
- **Behaviour corpus**: seal about a third of the in-scope items, chosen by seed, including mutant and ablation
  predictions (remove a gene from the CeNGEN table, or ablate cells, with no refit). Mutant predictions are the
  strongest test of "the same brain", because they probe internal mechanism, not just output.
- **"Within real variability"**: the prediction lies within the animal-to-animal spread of the measurement,
  operationally mean +/- 2 SD (SD from SEM x sqrt(n) where only SEM is published), at >= 80% of the scored
  quantities of each type. This is the definition the spike uses. It is lenient where n is small (the spike's
  voltage-clamp test passed a barely fitted model; F-W0-6), so from W1 on each test also names a wrong model
  that must fail it (DECISION 2, decided).
- **Many worms**: the model is also run as a population (parameters drawn inside their fitted spread,
  connectomes varied as across Witvliet's eight animals), and the population spread is compared with the
  measured spread, so variability itself becomes a scored output (ties to Ben's order item 3).

### c.5 Compute: measured costs and the whole-worm extrapolation

Measured tonight (backhouse; network = 446 Cook 2019 cells x 4 compartments each, AIY morphology and full
13-channel membrane in every cell, 4841 chemical connections, 1342 gap-junction pairs, dt 0.1 ms):

| Case | Device | Forward, wall s per bio s | Forward+gradient, wall s per bio s |
|---|---|---|---|
| network, batch 1 | 1 CPU core | 2.36 | 19.3 |
| network, batch 1 | GPU, shared (another user at 65-99%) | 3.18 | 21.2 |
| network, batch 8 | GPU, shared | 0.37 (2.70 bio s per wall s in total) | 2.46 (0.41 bio s per wall s in total) |
| network, batch 32 | GPU, shared | 0.096 (10.4 bio s per wall s in total) | 0.94 (1.07 bio s per wall s in total) |
| network, batch 128 | GPU, shared | 0.115 (8.7 bio s per wall s in total) | out of memory (needed 10.9 GB; 5.6 GB cap, the other user held about 9.8 GB) |
| AIY spike cell (4 compartments, dt 0.4 ms, float32), 16 starts x 6 traces of 8 s | 2 CPU cores, backhouse load about 30 | 31-33 simulations per second (about 0.004 wall s per bio s) | 5.3-5.4 simulations per second (about 0.023 wall s per bio s); 17.7-18.0 s per Adam step; 87-89 min per 300-step fit |

Batch costs are per network copy (derived: wall time / batch). The GPU's time per step barely moved from batch 1
to 32 (318 to 307 us forward; measured), so up to 32 copies ride along nearly free; forward saturates between
32 and 128. At batch 32 the GPU does about 25x one CPU core forward and about 20x with gradients (derived: 2.36 /
0.096 and 19.3 / 0.94). The batched gradients came out non-finite. Traced (FINDINGS F-W0-5): Jaxley 0.14 linearises a
synaptic current by nudging pre- and postsynaptic voltage together, so a gap-junction current g (post - pre)
gets slope 0 and is integrated fully explicitly; the most-coupled cell in the stand-in (the hypodermis, 57
partners, AIY-sized) then swings to +/-1,700 mV at 1.5x conductance and dt 0.1 ms (measured), while dt 0.025 ms
is stable and its gradient finite (measured). The membrane gradients are finite everywhere tested
(`scripts/worm/check_grad_nan.py`). Consequence for the build: gap junctions need a coupling solved implicitly on
both sides before network fits. A half-implicit patch (`bioemu.jx_gap.Gap`) was tested on 5 Nov: it never blows
up but slows coupled cells' common relaxation by about 1 + a, a = dt g / C (measured on a pair, F-W0-5), so it is
not adopted. **Solved on 5 Nov (decided):** `bioemu.jx_gap.ImplicitGap` puts the junctions into the same
backward-Euler solve as the cable and matches NEURON's fully implicit coupling to 1.2e-5 mV in a strongly coupled
active chain (pre-registered, GAPCHECK.md, F-W0-9); at 1.5x on this bench every cell stays within -60 to +0.5 mV
and the gradient is finite (measured). With its junction system solved by GMRES (gapcheck5) it costs 0.66-0.74 ms per
forward step and 3.7-3.9 ms per gradient step on one core (measured), about 2.6x and 2x the explicit form, so the
explicit-form timings above roughly double for any run with gap junctions (derived).

Derived (arithmetic from the table; assumptions labelled):
- **Running the worm.** At 4 compartments per cell and dt 0.1 ms, one biological hour costs 3600 x 2.36 =
  8,500 s, about 2.4 h, on one core (derived). If dt 0.4 ms holds accuracy (checked on the spike cell, SPIKE.md),
  cost falls about 4x to about 0.6 h per biological hour (derived, assuming cost is linear in steps). With 20
  compartments per cell (guessed as enough for EM-level dendrites; to be set by a convergence check), about 5x
  more (derived, assuming cost linear in compartments, as Jaxley's per-step work is), so about 3 h of wall time
  per biological hour and about 3 days per biological day on one core (derived). Independent worms run one per
  core, about 16 at once on backhouse (guessed safe share of 28 threads), or 32 at once on the GPU at 10.4 bio s
  per wall s in total (measured at 4 compartments), so 32 worms x 1 biological hour in about 3 h (derived). So hours-scale experiments are
  feasible now; day-scale ones at full compartment counts need the slow layers (rows 18-20) on a coarser step
  and the fast membrane only where it matters, or more machines.
- **Fitting the worm.** If one gradient step of a joint fit uses 100 biological seconds of data (guessed: e.g.
  a few hundred Randi stimulation windows of a fraction of a second each plus kinematics windows) and the fit
  takes 1,000 steps (guessed; the spike used 300 for 10-15 parameters), the cost is 100 x 19.3 x 1,000 = 1.9e6
  core-seconds, about 540 core-hours: about 34 h on 16 CPU cores, or 1e5 / 1.07 = 26 h on the GPU at batch 32,
  or about 15 h using both (derived from the guesses). At 20 compartments per cell and dt 0.4 ms, about 1.25x
  that (derived). So one joint whole-worm fit is about a day on backhouse, not months; eight starts make it
  about a week, which is why starts should be cheap stage-wise fits first (section c.2).
- **Not yet measured**: the body. The rod is cheap (guessed under 10% of the neural cost); the 3D body is
  unmeasured because Sibernetic did not run.

## d. The fly framework: what is organism-specific, and how to generalise it

The fly code (`src/flyemu/`, 42 modules) was written for one species, but most of its structure is not
fly-specific. Sorted by reading each module's header:

**Generic already (move to `bioemu` as is, with tests):**
- `registry.py`: the parameter registry with STRICT, MINIMAL and CONVENTIONAL require-policies.
- `model_data.py`: the construction data model. `mechanisms.yaml`, `parameters.csv` and `structural_keys.csv`
  carry bounds, priors and evidence labels; `sample_fly` becomes `sample_individual`.
- `profiles.py`: named parameter profiles, each value with its own evidence label.
- `provenance.py`: run provenance capture.
- `stubs.py`: mechanisms that are inventoried but not built.
- The packaging and scoring machinery (`flyzip.py`, `pack.py`, `run.py`, `score.py`, `check.py`): one file
  holds the organism, plus a scoreboard runner. Generalise to an organism zip with a species layer; the
  scoreboard protocols themselves are species data.

**Generic mechanism, fly parameters (keep the mechanism in `bioemu`, the values in the species layer):**
- `neuromod.py` (monoamine pools with per-cell receptor maps): the worm adds peptides to the same pool scheme.
- `receptors.py` (receptor shares from transcriptomes): the worm's version reads CeNGEN.
- `transducers.py` (sensory adaptation per class), `internal_state.py` (lumped organs and slow states),
  `lifetime.py` (homeostatic plasticity), `percell.py` (values within a type).
- `morph.py` (passive multicompartment cells from EM skeletons): now joined by `bioemu.morph` (NeuroML to SWC
  to Jaxley).
- `muscles.py` (Hill-type muscles) and `deadfly.py` (the "dead organism lies still" test).

**Fly-specific (stay in `flyemu`):**
- The body and its parts: `body.py` (MuJoCo flybody), `adhesion.py`, `flight.py`, `jump.py`, `joints.py`,
  `legangles.py`, `passive.py`, `neuromuscular.py`.
- The senses: `vision.py`, `olfaction.py`, `extrasenses.py`, `sensory.py`.
- `connectome.py` (the male-CNS neuPrint graph).
- `lif.py`: per-type leaky integrate-and-fire. Most worm neurons are non-spiking and graded, so the worm
  needs the conductance-based multicompartment cell, not LIF.
- `electrical.py`: spike-triggered gap-junction kicks; the worm needs continuous ohmic, rectifying coupling.

**How (and when):**
1. New worm code goes into `bioemu` when it is organism-agnostic (tonight: `morph.py`, `jx_membrane.py`) and
   into `wormemu` when it is worm data or worm-only mechanism (tonight: `nicoletti.py`).
2. The fly is not edited while paused. When it resumes, generic modules move from `flyemu` to `bioemu` one at a
   time, with `flyemu` re-exporting them, and the fly battery (307/0 at the last adoption) must pass after each
   move.
3. Data tables follow the same split: `data/model/` schema rows gain an `organism` column; worm tables live in
   `data/worm/`; large data stays on backhouse under `~/worm-data`, pinned by `MANIFEST.md`.
4. The fly's ledger idea (`data/ontology/fly_information.yaml`, fill fraction) is reused for the worm ledger
   rows in section a.

## e. Staged roadmap, with the first "done on evidence" targets

Each stage is pre-registered (objective, held-out split, falsifier) before it is scored, as the spike was.
"Done on evidence" means the pre-registered held-out bar passed.

| Stage | What | First "done on evidence" target |
|---|---|---|
| **W0 (tonight)** | the spike: one AIY neuron, CeNGEN channel set, Virtual Worm morphology, gradient fit | the pre-registered SPIKE.md bars: train RMSE <= 4 mV; held-out current steps <= 5 mV mean, none > 8 mV; held-out population voltage clamp within mean +/- 2 SD at >= 80% of voltages. Result (measured, 5 Nov): **train bar failed** (4.79 and 4.80 mV), both held-out bars passed (SPIKE.md RESULTS) |
| **W1 cell library** | ledger tables (section a rows as blanks); BAAIWorm channels ported and checked against NEURON; RIM and AFD from the same deposit; AWA (Liu 2018), AWC and RMD (Nicoletti 2019 figures); body-wall muscle | RIM and AFD each pass the same three-part bar on their own held-out steps and population I-V |
| **W2 motor system and rod body** | VNC motor circuit, NMJ, body-wall muscle, Cosserat rod in fluid and on agar | blind prediction of bend frequency, wavelength and speed at held-out viscosities, within real variability (corpus 1-7) |
| **W3 head circuit** | all head neurons, synapses (row 7), gap junctions (row 8), fitted to the Randi atlas | blind prediction of held-out stimulated neurons' responses (sign, amplitude, delay), within trial-to-trial spread, against a connectome-only baseline (Randi 2023 found the connectome alone predicts poorly: a direct test of rows 9-10) |
| **W4 closed loop, senses** | rows 17, 22: plates and gradients | chemotaxis (salt, diacetyl, benzaldehyde) and thermotaxis indices on held-out assay conditions (corpus 18-29) |
| **W5 states, hours** | rows 9, 10, 18, 20 | roaming/dwelling bout distributions and quiescence (corpus 37-41) over multi-hour runs |
| **W6 non-neural rhythms** | rows 13-15 | pharyngeal pumping rate, defecation period, egg-laying intervals (corpus 32-35, 43-53) |
| **W7 learning** | plasticity and the slow pathways of row 18 | salt-starvation learning and tap habituation curves (corpus 15-16, 61-63) |
| **W8 3D body cross-check** | Sibernetic on Windows OpenCL, or a GPU port | the rod and the 3D body agree on corpus 1-7 within the measured spread; where they disagree, the 3D body is the reference |
| **W9 sealed scoreboard** | spend the sealed third of the corpus once, with mutants and ablations | the fraction of sealed items within real variability is the headline number |

## DECISIONS (decided 2026-11-05 00:59 CST: the Director adopted all five recommendations as Ben's defaults; reversible; logged in `~/director/decisions/fly.md` and going to Ben in the morning report)

Each item keeps its reasoning. The text marked *Decided (default)* was the recommendation and is now the decision
in force until Ben changes it.

1. **Morphology source.** The local morphologies are the Virtual Worm atlas (NeuroML), not EM tracings; true EM
   neurite geometry is available at best for the nerve ring (Witvliet 2021; coverage not yet checked).
   *Decided (default):* use the Virtual Worm geometry now, labelled inferred; swap in EM skeletons where they exist
   and test whether it changes any held-out prediction. If it never does, compartments can stay coarse.
2. **The operational meaning of "within real variability".** *Decided (default):* mean +/- 2 SD of
   animal-to-animal spread, at >= 80% of the scored quantities of each type, as pre-registered in the spike,
   **plus a control that must fail**: each pre-registration names a deliberately wrong model (for example
   passive membrane only, or connectome-only weights) that has to land outside the band, or the test is
   declared uninformative. Reason (measured, FINDINGS F-W0-6): with n = 5-7 cells the 2 SD band is so wide that
   a 2-iteration fit and the published model both put 100% of AIY's voltage-clamp points inside it.
3. **GPU time.** The GPU was shared tonight (another user at 65-99%), and small cells ran faster on one CPU core
   than on the shared GPU (measured, SPIKE.md). *Decided (default):* single-cell and per-class fits on CPU cores;
   batched network fits on the GPU at night (22:00-06:00) and outside the 17:00-22:00 cap.
4. **The 3D body.** *Decided (default):* spend about one session trying a Windows-native Sibernetic build with
   NVIDIA OpenCL; if it fails, write the 3D body in JAX (gradients come free), validated against Sibernetic's
   published results.
5. **CeNGEN threshold.** Threshold 2 (used tonight) gives AIY no SHL-1, although the published AIY model uses
   it. *Decided (default):* treat channel presence near the threshold as a bounded density whose lower bound is
   zero, so the data decide; record which classes' fits want a channel CeNGEN calls absent.
