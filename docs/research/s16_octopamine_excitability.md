# S16: octopamine and motor-neuron / premotor excitability — usable ranges and gaps

Full rows, quotes, and labels: `docs/research/s16_octopamine_excitability.csv` (26 rows, `s16_oa_001`-`s16_oa_026`).
Searched: PubMed/PMC, journals.physiology.org, Nature, PNAS, Wiley (many full-text blocked by paywall —
flagged `verified=abstract` below; do not treat those as numeric evidence). No number in this file was invented;
where a paper only stated direction, the row says so and gives no value.

## Bottom line for the pre-registration

**There is no adult Drosophila VNC leg-MN or premotor-interneuron intracellular recording with OA, in any
preparation, in the literature found this session.** Every quantitative or semi-quantitative motor-circuit number
is from locust, stick insect, or Drosophila larva. The per-value bar ("consistent with some fly of this species")
cannot be met for adult VNC leg MNs from measured data; any class-level parameter there would be **inferred**
across species/stage, not measured, and must be labelled that way.

## What the numbers say, by quantity (MN vs premotor interneuron)

| quantity | motor neuron | premotor / interneuron |
|---|---|---|
| resting potential | no usable number found (nothing altered in the one in-situ check, s16_oa_003/004) | no number found |
| input resistance | **unchanged** by tyramine (TA, 1e-5 M) in larval RP2 MN (measured, qualitative, s16_oa_003); no OA number | no number found |
| spike threshold / rheobase | **unchanged** by TA in RP2 MN (s16_oa_004); **OA itself had no effect at all** on RP2 MN responses to current injection, at 1e-6 and 1e-5 M (s16_oa_006) | no number found |
| f-I gain / firing rate | TA *decreases* RP2 firing rate (direction only, no Hz; s16_oa_001); OA: no effect on this larval MN (s16_oa_006) | locust flight interneurons: OA-driven rhythmic bursts at 4-16 Hz, 50-75 ms bursts (descriptive of the OA-active state, not a before/after delta; s16_oa_008/009) |
| adaptation / delay to first spike | TA *increases* delay to first spike in RP2 MN (direction only; s16_oa_002) | — |
| AHP | no number found in any preparation | no number found |
| spontaneous rate | — | Drosophila OA descending neurons themselves: VUM_DN 4.12 ± 3.12 Hz (n=11, brain explant, carried from s13); VPM1/VPM2 firing increases at locomotor-bout onset (Wilcoxon p<0.0001, in vivo; s16_oa_015), but VUMd1-3 do **not** change with locomotion (s16_oa_016) — the "OA tone" is not one uniform signal even among OA neurons themselves |
| synaptic release / EPSP at a central synapse | locust fSR→BA1 flight MN: OA 1e-4 M **decreases** EPSP amplitude (direction only; s16_oa_010) — i.e. not always facilitatory | stick insect retractor-coxae MNs: descending OA (DUM) neuron spikes **increase** load-reflex depolarization (direction only; s16_oa_011); stick insect FT-joint resistance-reflex gain: OA injection gives a normal-looking gain at 3.5-12 min, then **gain = 0** at 15-20 min post-injection — same manipulation, opposite outcome over tens of minutes (s16_oa_012/013) |
| tonic depolarization (walking-related) | stick insect leg MNs: OA increases tonic depolarization during fictive walking; its antagonist mianserin decreases it; **the paper attributes this to premotor neurons, not a direct MN-intrinsic effect** (abstract-level only, not independently confirmed; s16_oa_014) | — |

## Receptor expression / coupling on MNs and premotor classes

- Four OA receptors in Drosophila: OAMB/Octα1R (Gq, Ca²⁺), Octβ1R/Octβ2R/Octβ3R (Gs, cAMP up, EC50 ≈0.03 µM
  octopamine, HEK293), Octα2R/OctαR (Gi, cAMP down, classification only) — s16_oa_018-020, carried/extended
  from s13.
- **OctαR (Gi) is functionally required in adult Drosophila motor neurons**: D42-GAL4 (pan-MN driver) knockdown
  significantly impairs climbing (t=10.396, df=28, P<0.001; El-Kholy et al. 2022, full text) — the only
  full-text-confirmed receptor-on-MN finding in this search. Receptor presence is inferred from driver
  specificity, not a direct stain of leg MNs.
- Octβ2R is an autoreceptor on OA (type II) larval NMJ terminals and a paracrine receptor on glutamatergic
  (type I) larval MN terminals, driving bouton/arbor growth (Koon et al. 2011) — **peripheral, structural,
  hours-to-days timescale, not acute excitability.**
- Allen et al. 2020 eLife (VNC single-cell atlas, full text checked): does **not** report which clusters express
  which OA receptor. El-Kholy et al. 2015 (GAL4 reporter map of all 7 OA/TA receptors): reports broad CNS/
  mushroom-body expression but **leg-MN-specific resolution was not found in the available text**.
- No synapse-count data from Tdc2/OA descending neurons onto named leg-MN or premotor classes was found in the
  literature (Babski et al. 2024 states they target "a majority of central, non-projecting interneurons",
  no counts). This would need a direct connectome query (male-CNS/MANC), not a literature search.

## Behavioural anchors (numbers, not narrative)

- Yellman et al. 1997 PNAS (decapitated adult, OA applied at 10 mM to the cut cervical connective): significant
  locomotor stimulation (P≤0.007, n=30/group, means±SEM). **This paper does not test chlordimeform or
  naphazoline** — only dopamine, serotonin and octopamine. The brief's association of those agonists with this
  paper does not hold; they belong to other papers (e.g. Longden & Krapp 2009 for CDM on visual neurons).
- Schretter et al. 2018 Nature: OA (10 mg/mL, fed) or thermogenetic Tdc2>dTRPA1 activation increases walking
  speed to axenic-like levels; n=13-46/group; exact mm/s values are in figure panels only, not extracted.
- Larval behaviour (Saraswati 2004, Fox/Soll/Wu 2006): OA and TA have opposite effects on locomotion; Tbh
  mutants (low OA, high TA) show fewer peristaltic waves and shorter crawl distance — qualitative only, no
  numbers obtained (paywalled).

## What this means for the proposed "aroused / OA-high" state arm

1. **No adult VNC number exists to fit to.** Any class-level OA parameter for leg MNs or VNC premotor
   interneurons in our model would be labelled **inferred** (from locust/stick-insect/Drosophila-larva), not
   measured, and that must be written into the state arm's pre-registration, not discovered later.
2. The one place OA was tested on a Drosophila MN's intrinsic excitability (larval RP2, full text), **OA did
   nothing** to firing threshold, input resistance, or current-injection responses — it was tyramine, not
   octopamine, that changed firing rate and spike delay (s16_oa_001-006). If the hand-off fix is modelled as
   "OA raises leg-MN intrinsic excitability," that specific mechanism has a direct negative result sitting
   against it in the one preparation where both amines were tested on the same cell.
3. Two separate lines (stick-insect tonic depolarization, s16_oa_014; locust fSR→BA1 EPSP, s16_oa_010 decreasing)
   point toward OA acting on **premotor gain and synaptic release**, not on MN intrinsic excitability — closer to
   what the hand-off problem actually needs (premotor→MN transfer), but still cross-species and still a release/
   gain change, not a validated "MN excitability" number.
4. The stick-insect reflex-gain data (s16_oa_012/013) show the same OA manipulation can first look like arousal
   and then abolish a reflex ~15-20 minutes later — a caution against treating "OA-high" as a single switch with
   a monotonic effect; if adopted, the arm needs a time constant, not just an on/off gain.

## Gaps for the ledger

- No adult Drosophila VNC leg-MN or premotor-interneuron OA electrophysiology (any receptor, any method).
- No MN5/DLM (adult flight MN) OA intracellular recording found (the only MN5-adjacent hit, Consoulas/Duch/
  Pflüger developmental work, is about larva→adult excitability change, not OA, and was not used here).
- No per-cell-class OA receptor map for VNC leg MNs or premotor interneurons (Allen 2020 atlas doesn't carry it;
  El-Kholy 2015 doesn't resolve it at that granularity in the text obtained).
- No synapse counts from OA/Tdc2 neurons onto leg-MN or premotor classes in the connectome literature — a direct
  query of male-CNS/MANC would answer this and is not a literature-search task.
- Several real numbers (RP2 Hz/ms/pA deltas, Schretter mm/s, locust %EPSP change) exist only in figure panels of
  papers whose text was readable but whose figures were not; these would need targeted figure extraction, not a
  fresh search.
