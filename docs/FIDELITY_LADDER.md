# Fidelity ladder

**Forward-looking; revised as rungs are built.** Ranked fidelity upgrades for the simulation, from 30 September 2026 (session 11). Ranking: plausible importance for behaviour emerging from the biology, tending toward simulating more. It is a judgement (inferred), not a measurement. Behaviour stays a guardrail, never the objective a rung is tuned toward (`docs/PLAN_NEXT.md`).

**Why the ladder exists (Ben, 30 September 2026, verbatim):** "is it possible to create an emulation of a biological brain that carries nearly 100% of the behavior of a typical member of that species, a brain upload, with current knowledge of neuroscience and a connectome scan as a starting point? And, if so, what amount of information from the scan do you actually need to reconstruct the ORIGINAL INDIVIDUAL?" The ladder serves the first part: a typical member's behaviour from biology at the highest plausible fidelity. The second part is the planned study at the end of this file.

Compute baseline (measured): the whole-CNS LIF closed loop costs ~50 s of wall time per simulated second on the Mac (M2 Pro, 10 cores, 16 GB; `docs/RUNNING.md`). On backhouse (RTX 4070 Ti SUPER 16 GB, 28 cores; offline in session 11) the batched GPU brain runs 0.37-0.45 s per member-second (F-GPU-1/2). Costs below are estimates (inferred) unless marked measured.

"On" means: the mechanism is built behind a registry switch, equals the current model at neutral (equivalence test), has its per-type values filled from data or a declared rule (labelled), and runs at its prior in the working profile, within bounds the search may explore.

| Rank | Rung | Why it plausibly matters | Data that constrains it | Cost: Mac / backhouse | Needed to be "on" |
|---|---|---|---|---|---|
| 1 | **Intrinsic conductances per type** (point neuron with A-type K, delayed-rectifier, M-type K, BK/SK with a Ca pool, HVA and T-type Ca, persistent Na, Ih; spike generation kept as threshold-reset) | Plateaus, rebound, bursting, adaptation and intrinsic rhythm come from these currents; the LIF has none of them. Session 11: no VNC rhythm from LIF, graded or adapting cells (F-RHYTHM-1). | Channel-gene expression per type: Davis 2020 (77 central/optic populations), Özel 2021 (~200 optic types), Allen 2020 VNC (hemilineage proxy). Channel kinetics: Drosophila voltage-clamp literature (Shal, Sh, Shab, slo, cac, Ih). Whole-cell recordings for calibration (Azevedo 2020 MNs, PN/LN/KC literature). | Mac ~1.3-2x the LIF step (7-9 extra state variables per cell, elementwise). GPU: small. | Module + switch (neutral 0); per-type expression table joined to male-cns types; density = class gbar x expression (gbar guessed, bounded); single-cell tests; full-CNS cost measured. |
| 2 | **Synapse dynamics per receptor**: conductance synapses with reversal potentials; rise and decay per receptor class (nAChR, GluCl, iGluR, GABA-A, GABA-B, mGluR, mAChR, NMDA-like); short-term depression and facilitation per presynaptic class; release probability | Fast inhibition by GluCl vs GABA-A differs in kinetics and reversal; STP sets gain at high rates. N7/N8/N9/N10 exist but sit at neutral. | Receptor calls per type (Davis, Özel, Allen; `infer_receptors.py`); Drosophila PSC kinetics (PN-KC, ORN-PN Nagel 2015, NMJ); STP literature per circuit. | Mac ~1.2x (extra channels already built). GPU: slow channels refused today; port needed. | Turn on N7-N10 at their priors; receptor kinetics per postsynaptic type from the receptor tables. |
| 3 | **Gap junctions from innexin data** | Electrical coupling synchronises motor pools and premotor cells, and makes GF and visual circuits fast. EM does not show electrical synapses; only curated sites are wired (N12, strength 0). | Innexin expression per type (shakB isoforms, ogre, Inx2/3/5/6/7) from the same atlases; known coupled pairs (GF-TTMn, VS-VS, eLN-PN); contact sites from the connectome as candidate locations. | Mac ~1.1x (sparse symmetric matrix, a few x 10^4 pairs). GPU: small. | Rule: candidate pairs = touching partners that both express compatible innexins; conductance per pair class (guessed, bounded); equivalence at 0. |
| 4 | **Neuromodulation by volume transmission**: DA, OA, 5-HT, TA and peptide release by identified cells; per-type receptor maps (Dop1R1/2, DopEcR, Octβ1-3R, OAMB, 5-HT1A/1B/2A/2B/7, TyrR); GPCR kinetics acting on channel conductances (rung 1) and release | State changes the whole network (arousal, locomotion vs flight, hunger). N19/N20 pools run but sensitivities are 0. | Receptor transcripts per type (atlases); release-cell identities from the connectome (transmitter predictions); arborisation by region; modulator time courses in the literature. | Mac ~1.1x (pools are few; per-cell sensitivity is elementwise). GPU: port needed. | Receptor maps per type from transcriptomes; targets = rung-1 conductances; gains bounded and searched. |
| 5 | **Body, muscle and sensor fidelity**: FeCO claw/hook/club dynamics and front-leg assignment; campaniform fields; hair plates; FlyMimic passive flexor element; mid/hind muscle parameters; coxa DOFs (F-COXA-1); neck and abdomen muscles | Sensory feedback and muscle mechanics close the loop (F-BODY-1, F-REFLEX-1 information gaps). | Mamiya 2018/2023 FeCO physiology; Lee 2025 FeCO annotation; FlyMimic MTUs; Azevedo 2020 forces; eLife 2025 passive stiffness; Dallmann campaniform data. | Mac: body is ~30% physics, 70% our Python (F-GPU-3); a few % per element. backhouse: CPU workers. | Each element behind a switch with its measured or derived values; dead-fly test still passes. |
| 6 | **Reduced multi-compartment neurons** (2-4 compartments: neurite/dendrite, spike-initiation zone, axon) | Insect neurons are unipolar: inputs and outputs share neurites far from the spike-initiation zone; graded cells compute locally. Matters most for large integrating cells (LPTCs, DNs, MNs). | male-cns skeletons and synapse positions (in hand); passive cable parameters (Gouwens & Wilson 2009; Cuntz 2013 LPTC models). | Mac ~3-5x (more state, synapses mapped to compartments). Needs backhouse for long runs. | Compartment assignment per synapse from morphology; coupling conductances from geometry; neutral = single compartment. |
| 7 | **Glia beyond lumped K+** (astrocyte uptake, OA/TA-gated astrocyte signalling, BBB) | Astrocytes gate modulator signalling (Ma 2016) and buffer K+ and glutamate. N27 is lumped K+ only. | Glial transcriptomes (Davis glia, FCA); astrocyte territories (not in EM inventory). | Mac ~1.05x. | Glial compartments per region; uptake kinetics from literature. |

## Rung 1 plan (first implementation milestone)

1. Per-type channel and innexin expression table from Davis 2020 and Özel 2021 (on/off probabilities and levels), joined to male-cns types through the existing crosswalks; coverage measured.
2. `src/flyemu/channels.py`: a vectorised intrinsic-conductance current added to the membrane drive, with gates by exponential Euler at the network step; spike generation stays threshold-reset (validity: subthreshold and slow currents; the spike waveform is abstracted).
3. Switch `cell_type:all|intrinsic_channels` (neutral 0 = current model, bit-identical), densities = per-gene class gbar (registry, guessed, bounded) x the type's expression call; cells without transcriptome data use a class prior (labelled).
4. Single-cell tests: Ih gives sag and rebound; A-type delays the first spike; SK and BK give adaptation; T-type gives a rebound burst.
5. The full CNS with every channel on at its prior: time per step on the Mac (measured); guardrails: no runaway, closed-loop seeds silent.

**Status (2026-09-30 21:12):**
- Done: items 1-4.
- Item 5 measured: 8.9x the LIF step on the Mac, and sugar -> MN9_L 1.7 Hz, so rung 1 is **not adopted** (switch neutral).
- **21:47: adopted as m8** after repair 1 (SK/BK/Kv2/Ih/Ca fitted to Azevedo 2020 slow-MN current steps; F-RUNG1-2), GPU port with CPU equivalence, G1 silent on seeds 12-13. Sugar -> MN9_L 2.7 Hz; joint gain re-search pre-registered (DECISIONS 22:01).
- **00:27: m9** = m8 + the re-searched class gains; all held-out tests pass (F-RS-1). Next is rung 2 (synapse dynamics per receptor).
- **01:00-02:44: rung 2 built, not adopted.** Conductance synapses (GPU = CPU), receptor shares from mRNA, tau_s_inh and charge-basis slow shares all exist and are neutral. Candidate m10p is silent after repair 1, but sugar -> MN9 is about 0 Hz because conductance synapses block it at GNG108 (F-R2-1). The next step is to fill v_rest and e_inh per type and re-search inhibitory gains.
- **03:01: m10q** (recorded e_inh, threshold-referenced weights): silent, sugar 2.4 Hz against a 5.5 bar; not adopted. Next is a class-gain re-search on m10q.
- Cause: the guessed spike-to-SK coupling (F-RUNG1-1).
- Next, in order (pre-registered in DECISIONS 21:12):
  - constrain the spike-triggered channels by recorded current-step f-I and adaptation;
  - cut the cost (tables or the GPU);
  - re-score.

## Planned study: how much of the scan reconstructs the original individual (not started)

The second part of Ben's question implies an experiment with a known answer. Status: **planned, not started.**
- **Prerequisites.**
  - A working model that carries the species' behaviour, which is the first part of the question.
  - A model of individual variation: which slots differ between flies and by how much. Derived from cross-specimen data: FAFB vs male-cns vs hemibrain, left vs right homologues, and per-type spread. Labelled inferred.
- **Ground truth.**
  - Build a fully specified possible fly: every ledger slot filled. Species values come from the adopted model. The individual layer is drawn within the variation model: per-cell and per-synapse values, channel densities, and a lifetime of plasticity under a recorded rearing history.
  - Draw several such individuals, "siblings", from the same species distribution.
  - All of them are synthetic and labelled as such. None is a claim about a real fly.
- **The scan.** Render from the ground-truth fly what a connectome scan yields:
  - morphology;
  - synapse locations and counts, with measured tracing error rates;
  - transmitter predictions with their confusion rates.
  Optionally add further modalities: per-cell transcriptome, a few recorded neurons, behaviour logs.
- **Reconstruction.**
  - Run the project's own construction pipeline (rules, transcriptome inference, bounded search) on subsets of that information, for example: the connectome alone; plus cell types; plus transcriptomes; plus k recorded cells; synapse weights coarsened or dropped.
  - The pipeline never sees the hidden values.
- **Measure.**
  - Identity is recovered when the reconstruction is closer to its original than the siblings are to each other.
  - Closeness is measured as distance in a behaviour repertoire: responses to a fixed battery of stimuli and internal states, including learned responses. Internal physiology is measured too.
  - The result is a curve of information supplied vs identity recovered: the information needed to reconstruct the original individual.
- **Design rules.**
  - Pre-register the battery and the identity criterion before any reconstruction is scored.
  - Generate the ground truth with a separate seed and code path from the reconstruction, so that no hidden value leaks.

