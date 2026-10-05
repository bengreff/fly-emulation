# Resting (standing) firing rates of insect leg motor neurons — literature search

Date: 2026-10-05. Budget: ~45 min, WebSearch + WebFetch + attempted Europe PMC/DOI fetches.

## Summary

- **Drosophila leg MNs, resting rate: only one pool has a measured number.** Azevedo et al. 2020 (eLife
  56754 / Azevedo, Dickinson, Tuthill et al., "A size principle for recruitment of Drosophila leg motor
  neurons") report the **slow tibia flexor MN at ~30 Hz** at rest (not ~25 Hz as sometimes
  paraphrased — the paper's own figure/text value is "approximately 30 Hz", n=14, Fig. 3D), with fast
  and intermediate flexor MNs **silent** at rest. Methyllycaconitine (MLA, 1 µM, nicotinic antagonist)
  cut the spontaneous rate and the resting holding force by **~1.5 µN (~15% of the fly's body weight)**
  (Fig. 4C). This is the full extent of the measured Drosophila number; the paper does not record resting
  activity of any coxa (promotor/remotor), trochanter (depressor: tergotrochanter/sternotrochanter), or
  femur-reductor MN pool. No later Drosophila paper found (Agrawal 2020, Dallmann 2023, Lesser et
  al. 2024 Nature connectome paper, Chen et al. 2023, "proprioceptive limit detector" 2025/2026 papers)
  reports a resting/standing firing rate or calcium level for those proximal-joint pools — all of their
  physiology is tuned to *movement* (proprioceptive responses, calcium during walking/grooming), not
  quiet standing. This confirms the prior search's conclusion: **no Drosophila recording of resting
  trochanter-depressor or coxa promotor/remotor rate exists in the literature found.**

- **Other insects give one directly comparable, well-replicated qualitative fact and one semi-quantitative
  lead, but no clean Hz number for a true analog of the coxa/trochanter depressor pool at rest:**
  - **Locust SETi (slow extensor tibiae):** Burns & Usherwood 1979 (J Exp Biol 79:69–98) state in the
    abstract (READ) that "**during standing only the SETi axons were active**" — i.e., tonically active
    at rest, unlike the fast extensor FETi. No Hz value is visible in the abstract; full text is
    paywalled (DOI 10.1242/jeb.79.1.69, $30 or subscription).
  - **Cricket SETi, by contrast, is silent at rest** (only bursts with ventilation) — Nishino, Sakai &
    Field 1999 (J Comp Physiol A 185:143–155), quoted secondarily by Kondoh/Zoological Science 2003
    paper (see below): species difference, so this cannot be generalized as "the" insect number.
  - **Cockroach slow coxal depressor Ds**: Pearson & Iles 1970 (J Exp Biol 52:139–165) and Pearson 1972
    (J Exp Biol 56:173–193) are the classic sources but I could not extract a verbatim resting-Hz number
    from either — the 1970 paper is paywalled (abstract only, no rate visible) and the 1972 PDF would not
    parse through the fetch tool (binary/encoded content stream). A paraphrase surfaced by the search
    engine (not independently verified by me against page text) describes Ds as tonically active in the
    quiescent intact animal with no visible twitch in the depressor muscle — flagged SECONDARY/UNVERIFIED
    below, not to be used as a number.
  - **Quimby, Amer & Zill 2006** (J Comp Physiol A 192, DOI 10.1007/s00359-005-0062-9) is reported by a
    search-engine synthesis (not by me reading the paywalled full text, which redirected to a Springer
    login wall) to state that "tonic firing of the slow trochanteral extensor [= coxal depressor]
    motoneuron (Ds) in each leg was strongly modulated by changing body load" during posture — i.e.
    **load-dependent, not a single fixed rate**. Flagged SECONDARY/UNVERIFIED; no Hz number obtained.
  - **Stick insect** (Bässler, Büschges, Schmitz school): abundant work on load/force feedback to the
    depressor trochanteris and extensor tibiae during standing, but no resting-Hz number surfaced in this
    search; the relevant statement found is qualitative ("interjoint reflex contributes to posture control
    of the resting, standing animal").

- **Fraction of maximal force used at rest:** not found for any insect leg muscle. The only quantitative
  anchor remains the Azevedo MLA result (~15% of body weight lost when the slow tibia flexor's tonic
  drive is blocked), which is a force, not a %-of-maximum.

**Bottom line for the model:** there is still no measured Drosophila (or clean cross-species homolog)
resting rate for the coxa promotor/remotor or trochanter-depressor pools. The best-supported, directly
read fact usable as a biological constraint is Azevedo's slow-tibia-flexor number (~30 Hz, silent
fast/intermediate neighbors, ~1.5 µN / ~15% bodyweight loss on block). The best cross-species qualitative
constraint is that a slow postural MN *can* be tonically active at rest in a leg homologous joint (locust
SETi, "during standing only SETi was active") while its fast synergist is silent — same qualitative
pattern as Drosophila tibia flexor — but the actual Hz is species- and even order-specific (crickets'
SETi is silent at rest, locusts' is tonic), so no single borrowed number should be taken as a cross-insect
universal; any ported rate must stay a labeled *inferred* parameter, not a measured one for the
coxa/trochanter pools.

## Table

| Species | MN / pool | Homologous Drosophila pool (basis) | Condition | Resting rate | Force/load info | Source (DOI) | READ/SECONDARY |
|---|---|---|---|---|---|---|---|
| D. melanogaster | Slow tibia flexor MN | — (same cell) | Resting, not walking, tethered fly, probe on tibia | **~30 Hz**, n=14 (Fig. 3D) | MLA block: resting force ↓ ~1.5 µN (~15% body weight), Fig. 4C | Azevedo et al. 2020, eLife 9:e56754, 10.7554/eLife.56754 | READ |
| D. melanogaster | Fast, intermediate tibia flexor MNs | — | Resting | **Silent** (0 Hz) | RMP: fast −68 mV, intermediate −60 mV, slow −48 mV (Fig. 3C) | same | READ |
| D. melanogaster | Coxa promotor/remotor, trochanter depressor (tergotrochanter/sternotrochanter), femur reductor | Target pools for this project | Resting | **Not recorded anywhere found** | none found | — | NOT FOUND |
| Locust (Schistocerca gregaria) | SETi (slow extensor tibiae) | Candidate functional analog of a slow tonic extensor/depressor class, joint-level not segment-level homology — basis: both are the slow, tonically-recruited synergist of a fast/slow MN pair at a leg joint | Standing (not walking), intact/semi-intact | "**During standing only the SETi axons were active**" — qualitative, no Hz given in accessible text | SETi fires 3–10 spikes during swing phase (search-synthesized, not independently verified page text) | Burns & Usherwood 1979, J Exp Biol 79:69–98, 10.1242/jeb.79.1.69 | READ (abstract only; full text paywalled) |
| Cricket (Gryllus bimaculatus) | SETi | same candidate analog as above | Standstill on horizontal substrate | "**completely silent... except occasional excitations with ventilatory movements**" | — | Nishino, Sakai & Field 1999, J Comp Physiol A 185:143–155 | SECONDARY (quoted by Kondoh et al. 2003, Zool. Sci. 20:697, 10.2108/zsj.20.697, which I did read directly) |
| Cockroach (Periplaneta americana) | Slow coxal depressor Ds (muscles 177D/E) | Best anatomical/functional candidate for Drosophila trochanter-depressor (tergotrochanter/sternotrochanter) pool — basis: Ds depresses the coxa-trochanter joint, serially homologous joint, slow tonic class | Quiescent, undissected, standing | No verified Hz number obtained | Pearson 1972 (J Exp Biol 56:173–193) secondary paraphrase: tonically active with no visible depressor-muscle twitch in the resting animal | Pearson 1972, 10.1242/jeb.56.1.173 (PDF would not parse); Pearson & Iles 1970, J Exp Biol 52:139–165, 10.1242/jeb.52.1.139 | SECONDARY/UNVERIFIED (1972); READ abstract only, no rate found (1970) |
| Cockroach | Ds (described as "slow trochanteral extensor" in the secondary summary) | same | Standing posture, under varying imposed body load | "tonic firing... **strongly modulated by changing body load**" — i.e., rate is load-dependent, no single baseline value obtained | Load increases → sharp increments in Ds firing (search-synthesized) | Quimby, Amer & Zill 2006, J Comp Physiol A 192:247–261 (title: "Common motor mechanisms support body load in serially homologous legs of cockroaches in posture and walking"), 10.1007/s00359-005-0062-9 | SECONDARY/UNVERIFIED (paywalled, Springer login wall; quote not independently confirmed against page text) |
| Stick insect (Carausius morosus) | Depressor trochanteris, retractor coxae, extensor tibiae slow MNs | Depressor trochanteris → trochanter-depressor candidate; retractor coxae → coxa remotor candidate | Standing, resistance-reflex studies | No Hz number found | Qualitative: "interjoint reflex action contributes to posture control of the resting, i.e. standing, animal" | Bässler/Büschges/Schmitz body of work (e.g. Büschges 1991 J Neurobiol 22:224; Hess & Büschges 1999 J Neurophysiol 81:1856) | NOT FOUND (number); general statement only, not independently page-verified |
| Any insect | leg muscle, standing | — | — | — | % of max tetanic force used during quiet standing | none found | NOT FOUND |

## Verbatim quotes

**Azevedo et al. 2020, eLife 9:e56754** (READ, fetched PMC7347388 full text):
> "the slow neuron had a resting spike rate of approximately 30 Hz (Figure 3D)" [periods when the fly was not moving; n=14]
> "While the fast and intermediate neurons were silent at rest, the slow neuron had a resting spike rate of approximately 30 Hz (Figure 3D)."
> "The average resting potential of fast motor neurons was lower (−68 mV) than that of intermediate (−60 mV) and slow (−48 mV) motor neurons (Figure 3C)."
> "Bath application of 1 μM MLA...led to a decrease in the spontaneous firing rate and reduced the resting force on the probe by ~1.5 μN, or ~15% of the fly's weight (Figure 4C)."
> (fetch tool's summary) "no resting activity recordings for [coxa, trochanter, femur reductor] pools—only the tibia flexor neurons were characterized electrophysiologically."

**Burns & Usherwood 1979, J Exp Biol 79:69–98** (READ, abstract only via journals.biologists.com):
> "During standing only the SETi axons were active."
(No Hz value visible on the abstract page; full text paywalled, DOI 10.1242/jeb.79.1.69.)

**Kondoh et al. 2003, Zool. Sci. 20:697** (READ full text via BioOne), quoting Nishino, Sakai & Field 1999 and Burns & Usherwood 1979/Hoyle 1980:
> "SETi activity is completely silent during normal standstill state on the horizontal substrate except occasional excitations with ventilatory movements" [cricket, attributed to Nishino et al. 1999]
> "SETi is continuously active in the resting locust" [attributed to Burns and Usherwood, 1979; Hoyle, 1980]
> "the static posture to resist gravity in the cricket must be primarily controlled by the combined activities of slow-type exciters and common inhibitors in the flexor muscle."

**Pearson & Iles 1970, J Exp Biol 52:139–165** (abstract page only; fetch tool found no Hz number):
> Abstract mentions bursts of levator motor-axon activity "strongly reciprocal and generally non-overlapping with those of a slow depressor motor axon" during rhythmic leg movements — walking context, not a resting rate.

**Pearson 1972, J Exp Biol 56:173–193** — SECONDARY, UNVERIFIED (PDF would not parse through the fetch tool; this is a search-engine paraphrase, not a sentence I confirmed on the page):
> "In the resting undissected animal, when this slow depressor neurone was presumably active, there were no visible signs of twitch contraction in any of the coxal depressor muscles, indicating that the slow depressor maintains tonic activity during standing." [paraphrase surfaced by WebSearch synthesis; do not treat as a measured number]

**Quimby, Amer & Zill 2006, J Comp Physiol A 192:247–261** — SECONDARY, UNVERIFIED (Springer full text behind an institutional-login redirect; not independently confirmed against page text):
> "In posture, tonic firing of the slow trochanteral extensor motoneuron (Ds) in each leg was strongly modulated by changing body load, with rapid load increases producing decreases in body height and sharp increments in extensor firing." [paraphrase surfaced by WebSearch synthesis]

## Access notes (paywalls)

- Pearson & Iles 1970: DOI 10.1242/jeb.52.1.139 — abstract free, full text paywalled (journals.biologists.com, subscription/purchase).
- Burns & Usherwood 1979: DOI 10.1242/jeb.79.1.69 — abstract free, full text paywalled ($30 or subscription).
- Pearson 1972: DOI 10.1242/jeb.56.1.173 — PDF found at biomimetic.pbworks.com but would not parse through the fetch tool (binary/encoded content streams); not confirmed open-access vs. just a hosted copy.
- Quimby, Amer & Zill 2006: DOI 10.1007/s00359-005-0062-9 — Springer, redirects to institutional login (idp.springer.com); not accessible without subscription.
- Noah, Quimby, Frazier & Zill 2004 (J Comp Physiol A 190:201–215, tibial campaniform sensilla under thorax-applied load) was located but is about sensory afferents, not Ds motor output, so dropped from the table — flagging in case it is wanted later; not independently fetched.
