# s23: what gate G's silent window tests, and whether m10f9c's failure is the model or the gate

24 Oct 2026. The Director's challenge (01:30) is in `docs/DECISIONS.md` (24 Oct 01:31), and the amendment G2 was
registered there before any rescoring. Nothing here is held out: the gate seeds are engineering seeds.

## The facts in the built networks (checked, not run)

- G runs 1 s with all senses and noise. The silent window then follows (300 ms): external drive zero and all noise
  removed (`noise_mv`, `noise_class_mv`). Per-type tonic cells are excluded, and eye classes are reported apart
  (F-VISION-5 option (a)).
- G passes when there are 0 non-eye spikes in the last 100 ms and the eye count does not grow between the last two
  100 ms bins (Ben, 13 Oct).
- **Release at rest in m10f9b and m10f9c is 0** for all 36,360 graded cells: `graded_r0` is None, the chain never
  sets `cell_type:ol_graded|release_at_rest`, and the per-type rows are off. By class: 6,091 photoreceptors, 8,884
  LMCs, 7,370 optic columnar, 13,580 T4/T5, 433 IN13B and 2 APL.
- No eye class has a per-type or class tonic drive.
- A graded cell releases `graded_rmax × clip((V − V_rest)/range, 0, 1)`. So in the silent window a graded cell
  releases only while it is still depolarised from the noisy phase or by its inputs.
- The eye activity in G's window is therefore **not tonic dark release**. At 01:31 it was read as a slow recurrent
  tail. G2's 1000 ms window shows a self-sustained state instead (see the verdict).

| stage | seed | eye spikes per 100 ms, bins 2 → 3 | ratio | non-eye, last 100 ms |
|---|---|---|---|---|
| m10f9b (rmax 100) | 12 | 19 → 4 | 0.21 | 0 |
| m10f9b | 13 | 19 → 4 | 0.21 | 0 |
| m10f9c (rmax 300) | 12 | 842 → 597 | 0.71 | 6 |
| m10f9c | 13 | 828 → 604 | 0.73 | 4 |

- Tripling graded_rmax triples the gain of the recurrent graded optic-lobe loops. Over 300 ms this looked like a
  decay with τ ≈ 290 ms instead of ≈ 65 ms; over 1000 ms it plateaus.
- In m10f9c, part of that slow tail reaches DNs, AL local neurons, central cells and one non-leg MN. Over the whole
  300 ms window that is 8 DN, 10-3 AL_LN, 11-6 central_other and 1 MN_other spikes.

## (1) What the silent window protects against

It tests whether the noise-free network is stable at rest: activity that persists or grows with no afferent drive,
no noise and no per-type tonic drive is self-sustained. In the full run, self-sustained activity becomes a runaway.
The s13 graded VNC hemilineages (arm A) and F-S23-7 (m10f9, MN_other 0.5 → 8.4 Hz) are the cases it caught.

It is not a claim that the fly brain is silent at rest. The noise term stands for the unmodelled inputs that keep
real neurons spontaneously active, and measured resting rates are matched with the noise on (Huang's DANs in the MB
check, the S band).

The pass rule, "0 non-eye spikes in the last 100 ms of 300 ms", is an engineering convention. It assumes every
stable network falls silent within 200-300 ms, which is a claim about decay speed, not stability. Biology could
make it wrong in two ways:
- **A real deterministic tonic source.** Graded release at rest in darkness, or an intrinsically tonic type, would
  keep downstream cells active without noise. That source is absent from this chain (r0 = 0), so it is not what
  failed m10f9c. It will matter once a sourced r0 is turned on, and G2's future clause covers it.
- **A slow but stable mode.** The convention would fail a network that returns to rest more slowly than the window
  allows.

One limit is not addressed by G2: a model whose head-direction bump self-sustains without noise would fail G and G2
alike, although the real bump persists in darkness.

## (2) A test that does not forbid real tonic activity

G2 (DECISIONS 24 Oct 01:31) keeps the stability purpose and drops the speed assumption:
- **Window:** 1000 ms.
- **(a) No growth** in any pair of consecutive 100 ms bins, within 3 Poisson SD, for eye and non-eye counts
  separately.
- **(b) Return to rest:** 0 non-eye spikes in the last 100 ms.
- **Bounded:** no NaN, 0 warnings, no class above 200 Hz, as in G.

The Director's other conditions are covered elsewhere. Bounded, stationary rates inside measured bands with noise
on are what S tests over 60 s; G2 tests only the stability that S cannot see. When a sourced r0 > 0 is adopted,
(b) is scored with the tonic source's output clamped, and the non-eye rate with it on must be stationary.

## (3) Measured resting activity of the lamina in darkness

From open sources (Sonnet reader, 24 Oct). Behnia 2014 was not opened (held out).

| quantity | value | animal | source |
|---|---|---|---|
| tonic transmission in the dark | photoreceptor → LMC synapses are "tonically active both in the dark and in the light" | *Calliphora* | Laughlin 1989 J Exp Biol 146:39 |
| same | tonic release in darkness at the photoreceptor → LMC synapse (abstract only; full text on Ben's list) | *Calliphora* | Uusitalo et al. 1995 J Neurophysiol 74:470; Juusola et al. 1995 J Gen Physiol (PMC2216927, abstract) |
| dark resting potentials | photoreceptor terminal −60.3 ± 3.9 mV (n 32); L1/L2 −41.6 ± 8.1 mV (n 18); L3 −59 ± 8.4 mV (n 7) | *Calliphora* | Weckström & Laughlin 2010 J Neurosci 30:9557 |
| operating point at rest | the synapse sits in "the steep mid-region of the synaptic characteristic curve", voltage gain about ×10-12 | *Calliphora* | same |
| release at rest in a model fitted to recordings | transfer ratio at rest L3 0.62, L1/L2 0.32 (a model quantity, not a measurement) | *Calliphora* | Rusanen & Weckström 2016 (PMC4869513): synapses "constantly active" |
| what dark release does to LMCs | in *hdc* mutants (no histamine), LMCs are tonically depolarised in dark and light; *hdc* photoreceptors −54.5 ± 1.7 mV vs wild type −61.8 ± 1.74 mV | *Drosophila* | Dau et al. 2016 |
| LMC response range | 30-40 mV, hyperpolarising from dark rest | *Calliphora* | Laughlin & Osorio 1989 |
| blocking photoreceptor release | *shibire*<sup>ts1</sup> block hyperpolarises photoreceptors by 10-15 mV | *Drosophila* | Zheng et al. 2006 |
| not found | a measured fraction of maximal release at dark rest; a light-OFF return time constant; dark spontaneous rates for H1/H2, HS/VS, T4/T5 or LC cells (H1 8.4 ± 1.6 Hz at rest without flight, lighting not stated) | — | searched |

What this says for the model and the gate:
- **Tonic dark release at the first visual synapse is measured, and the model lacks it.** The synapse rests
  mid-curve, so a sourced `release_at_rest` would be well above 0, but no open text states the fraction. The model
  has r0 = 0, so the dark activity in m10f9c cannot be this release.
- **The sign matters.** Photoreceptor histamine opens chloride channels on L1-L3. In the dark, tonic release
  therefore holds the LMCs more hyperpolarised than they would sit without it; *hdc* LMCs are depolarised (inferred
  from Dau 2016). Adding r0 > 0 at the photoreceptors would add a tonic inhibitory current into the lamina. It would
  not simply excite the brain, and its effect beyond the lamina has to be run, not assumed.
- **Rates beyond the lamina.** No open source gives dark spontaneous rates for the optic-lobe cell types that carry
  m10f9c's silent-window activity, with or without photoreceptor input. So the size of the eye's dark drive to the
  central brain is not measured here.

## Verdict on m10f9c: a model failure, not a gate artefact

G2 (1000 ms window, scored once; `runs/s23/g2/`). Counts are spikes per 100 ms bin.

| stage | seed | eye bins 1-10 | non-eye bins 1-10 | G | G2 |
|---|---|---|---|---|---|
| m10f9b (rmax 100) | 12 | 52 19 4 1 2 0 0 0 0 0 | 12 0 0 0 0 0 0 0 0 0 | pass | pass |
| m10f9b | 13 | 51 19 4 1 2 0 0 0 0 0 | 5 0 0 0 0 0 0 0 0 0 | pass | pass |
| m10f9b | 14 | 53 19 4 1 2 0 0 0 0 0 | 1 0 0 0 0 0 0 0 0 0 | pass | pass |
| m10f9b | 15 | 51 19 4 1 2 0 0 0 0 0 | 9 0 0 0 0 0 0 0 0 0 | pass | pass |
| m10f9c (rmax 300) | 12 | 735 842 597 607 606 597 674 671 667 689 | 19 5 6 6 5 2 6 6 6 11 | fail | fail ((a) holds, (b) 11) |
| m10f9c | 13 | 750 828 604 587 599 572 613 689 734 739 | 7 7 4 4 6 4 4 6 9 9 | fail | fail ((a) holds, (b) 9) |
| m10f9c | 14 | 718 790 540 597 591 552 621 656 666 702 | 8 5 5 4 5 2 5 5 6 8 | fail | fail ((a) holds, (b) 8) |
| m10f9c | 15 | 697 820 583 600 569 557 565 633 658 647 | 8 7 6 3 5 2 4 4 6 5 | fail | fail ((a) fails, (b) 5) |

On seed 15, (a) fails at the first step after the noise is removed: eye bin 1 → 2 rises by 123, against a bar of
3√1517 = 117. On every m10f9c seed, bin 2 is above bin 1 (+107, +78, +72, +123), so removing the noise briefly
raises the eye's activity before the plateau. m10f9b falls over the same step (52 → 19). The registered prediction
"(a) holds on all four seeds" is wrong for seed 15.

The evidence:
1. **m10f9c's silent-window activity sustains itself.** There is no input, no noise and no tonic source (r0 = 0 in
   every graded cell), yet after the noise-off transient the eye counts stay flat or rise for 700 ms on all four
   seeds. That is not the τ ≈ 290 ms decay claimed at 01:31, which would leave about 50 spikes by bin 10.
   - The registered falsifier of that claim is not hit on any seed, though it is close: the last 300 ms are
     0.9-7.7 % below the first 300 ms, which carry the noise-off transient.
   - The shape refutes the decay all the same: 647-739 spikes in bin 10.

   The state lives in the optic lobe:
   - Last 100 ms of s12: 512 optic columnar, 122 optic other and 55 optic projection spikes.
   - It leaks 9 DN and 2 central spikes per 100 ms into the central brain.
   - The most active types are the GABAergic medulla Pm2a/Pm2b/Pm4/Pm5, T1, Dm9, Dm13, Tm6 and VS.
2. **One value creates it.** m10f9b and m10f9c differ only in `graded_rmax` (100 vs 300; checked in PROFILES).
   At 100 Hz, the same seeds go silent within 500-600 ms.
3. **That value is applied beyond its source.** 300 Hz is a photoreceptor-synapse rate. 30,269 of the 36,360
   graded cells (LMCs, optic columnar, T4/T5, APL, IN13B) get it without a source (N1 section below).
   **The localisation diagnostic** (registered 01:40 and scored 02:12, seed 12; `runs/s23/g2/locate_*.json`):

   | arm | 300 Hz applied to | eye spikes per 100 ms | non-eye spikes, last bin | outcome |
   |---|---|---|---|---|
   | P | photoreceptors only (the value's source) | 256, 103, 11, then 0 by bin 7 | 0 | returns to rest |
   | Q | the other graded classes only | 322 → 779, growing | 6 | sustains and grows |

   In Q, the graded cells still above rest at the end are L1-L5, Tm1-Tm3 and T5a-d. The spiking cells that carry
   the activity are the medulla Pm cells, T1, Dm13, Tm6 and VS. So the state sits in the gain applied beyond the
   value's source. At the photoreceptors, where the value is sourced, it is resting-safe.
4. **The biology the challenge cites is not what the model is doing.** The measured dark activity of the lamina is
   tonic photoreceptor release, which is inhibitory onto LMCs. The model does not have that release, so its dark
   activity has a different, unsourced cause: reverberation in recurrent optic-lobe loops driven by an unsourced
   gain. The central brain's measured resting rates (Huang's DANs) are matched with the noise on, which is the
   condition S scores. G removes the noise on purpose.

**Decision (01:31 rules).** (b) fails on all four seeds, and (a) fails on seed 15 at the noise-off step, so this
is a **model failure** (scored in DECISIONS 24 Oct 01:47). m10f9b and m10f10 pass G2 on seeds 12-15. G's
silent window is an engineering stability convention, not a claim that the brain is silent, and G2 now states
that. The convention did not cause this failure: the network does not return to rest, and nothing measured says
the real optic lobe reverberates without photoreceptor input.

What would flip the verdict:
- a recording showing the fly optic lobe sustaining activity with photoreceptor transmission blocked (e.g.
  *hdc* or *ort* mutants, or shibire<sup>ts</sup> in R1-8) at about these rates; or
- a sourced non-photoreceptor graded release rate near 300 Hz.

Neither was found.

**Two limits of G2, written down rather than changed:**
- **(a) is a test of consecutive pairs, so it is weak against slow drift.** In m10f9c s13, bins 6-10 rise
  monotonically, 572 → 739 (+29 % in 400 ms), with every step inside 3 SD. A trend test (for example, the last
  500 ms against the previous 500 ms) would catch it. That needs its own registration before it is used; it is
  not applied tonight.
- **(b) would also fail a real noise-free attractor**, such as the head-direction bump, as noted in (1).

## N1: is one photoreceptor-synapse rate the right source for every graded class?

No. The source covers the photoreceptors only (Sonnet reader, 24 Oct, open full text).

| class | quantity | value | source | read |
|---|---|---|---|---|
| locust ocellar L-neurons (second-order graded interneurons) | voltage range of release | "the postsynaptic neuron gradually began to depolarize as the presynaptic neuron was driven positive from approximately −8 mV"; linear transmission "for presynaptic potentials between −4 and +4 mV" (relative to dark rest) | Simmons & de Ruyter van Steveninck 2005 J Neurosci 25:7529 (PMC6725398), *Schistocerca*, n 6 | full text |
| same | contacts per connection | "an ensemble of several hundred discrete synaptic contacts" | same | full text |
| same | release rate | **not stated** (quanta not resolved; smallest IPSP < 0.1 mV, Simmons 1999 J Neurosci 19:10584, PMC6782427) | — | full text, absence confirmed |
| locust thoracic nonspiking interneurons → MNs | threshold | "a depolarization of only 2 mV is sufficient to effect the release of transmitter" | Burrows & Siegler 1978 J Physiol 285:231 (PMC1281754) | full text |
| same | tonic release at rest | "At their resting potential some interneurones tonically release sufficient transmitter to have a measurable post-synaptic effect" (no rate) | same | full text |
| Drosophila APL, L1/L2 medulla outputs, AL nonspiking LNs, optic columnar, T4/T5, VNC 13B | release rate | **not found** | searched (Takemura 2008 PMC2481516 gives vesicle counts only) | — |
| fly R1-6 terminal (comparison) | vesicles per terminal; tetrads | about 43,000 vesicles (Takemura, Lu & Meinertzhagen 2008, full text); about 50 tetrads per terminal (Meinertzhagen & O'Neil 1991, secondary) | — | — |

**Consequence.**
- `graded_rmax` 300 Hz is sourced (derived) for the 6,091 photoreceptors only.
- For the other 30,269 graded cells it is **applied beyond its source**: L1-L3, optic columnar, T4/T5, APL and IN13B.
- No open text gives a release rate for any non-photoreceptor graded synapse, insect or otherwise.
- The locust graded synapses give the voltage axis instead. In the ocellar L-neurons, release starts about 8 mV below dark rest and is linear from −4 to +4 mV, so rest sits inside the operating range: tonic release at rest. That is the shape a later `release_at_rest` derivation could use (other insect, labelled derived), but no rate.
- The `n1_graded_rmax` notes and the N1 row now say this.
