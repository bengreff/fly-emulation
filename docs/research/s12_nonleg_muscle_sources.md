# Session 12 B: sources for non-leg muscle force (head, proboscis, antenna, abdomen, wing, haltere)

Literature search by a Sonnet Explore agent, 2026-10-04, for measured force, cross-section,
moment arm, motor-unit count, inertia, stiffness or damping of any non-leg Drosophila (or
Calliphora) muscle or joint. Its report is kept below as returned, apart from the title line.
"Full text" means the agent fetched and quoted the page; "snippet" means a search summary
only, not checked against the paper. Nothing here is a model value until a table row cites it.

Use in the model: none of these give a non-leg torque directly. data/params/nonleg_motor_forces.csv
(scripts/build_nonleg_forces.py) therefore transfers the measured leg motor-unit twitch forces
(Azevedo et al. 2020) and labels the result inferred. The neck limit of +/-15 deg (Cellini &
Mongeau 2022) agrees with the flybody head yaw range already in the model. The proboscis
motor-neuron counts (McKellar et al. 2020, Table 1) are a check on the motor_targets mapping,
not yet applied.

Paywalled primary sources that would replace the inference (on Ben's list): Strausfeld, Seyan &
Milde 1987 (neck muscles and motor neurons); Rajashekhar & Singh 1994 (proboscis muscles);
Tu & Dickinson 1994/1996 (b1/b2 steering muscles); Zanker 1988 (abdomen); Chan et al. 1998
(haltere muscles).

---

Scope note: many WebSearch results returned AI-generated summaries of search snippets, not verified full-text quotes. I flag those as "secondary/snippet" rather than "full text," and distinguish them from pages I actually fetched and quoted from (Walker et al. 2014; Miller/Swank jump-muscle paper; the force-per-CSA review; McKellar et al. 2020 PMC). Several target papers (Strausfeld/Seyan/Milde 1987; Rajashekhar & Singh 1994; Zanker 1988; Chan et al. 1998; Tu & Dickinson 1994/1996) are pre-2000 and paywalled — I could not get full text (403/paywall) in the time budget; only citation-level/snippet information is reported for them.

## 1. Neck muscles
- **~25 pairs of neck motor neurons** innervate head muscles controlling yaw/pitch/roll. Gorko et al. 2024, *Nature* — snippet-level (WebSearch summary of abstract; "Head movements of Drosophila are controlled by about 25 pairs of neck motor neurons innervating predominantly thoracic neck muscles"). Not independently fetched/quoted from primary text.
- **Head/thorax saccade velocities**: "high angular velocities of up to a few thousand degrees per second"; between saccades, head angular velocity ≈ half of thorax, "mostly in the range 0–100°/s" (yaw, pitch, roll). Schilstra & van Hateren 1998, *Nature* ("Stabilizing gaze in flying blowflies") — abstract/snippet level only; full text not accessed (paywalled).
- **Drosophila saccades**: mean peak angular velocity 567±270°/s (visual fixation) and 976±457°/s (spontaneous); free-flight saccades >1000°/s; duration ~50 ms. Kim et al. 2017-type studies — snippet level, source conflation possible (search engine summary, not verified against the actual Current Biology paper).
- **Neck joint anatomical limit ≈ ±15°** (figure caption). Cellini & Mongeau 2022, eLife 80880 / PMC9651946 — this is the one quote I could verify by fetching the PMC page directly (full text attempted, but figures/equations with I, C, stiffness values did not render in the fetch; only this qualitative limit was extracted).
- No moment of inertia, muscle force, CSA, or motor-unit-count data for neck muscles were recoverable. Strausfeld, Seyan & Milde 1987 (Calliphora neck muscles/motor neurons, J Comp Physiol A 160:205–238) is the correct primary source for muscle anatomy and motor-neuron counts but I could not get past citation-level detail (paywalled; no PMC copy found).

## 2. Wing steering muscles
- **Steering muscles = <3% of total flight-muscle mass** (quote, full text). Walker et al. 2014, PLoS Biology (pbio.1001823) — full text fetched.
- **Wingbeat frequency 145 Hz** in the microtomography preparation (full text, Walker 2014).
- **Muscle strain amplitudes** (full text, Walker 2014, Fig. 8/9 region): b1 strain **2.3% (high-amplitude wing) vs 5.5% (low-amplitude wing)**; b3 strain "four times as high on the high-amplitude wing"; i1 effective strain along attachment line "four times the amplitude of actual I1 muscle strain" on high-amplitude wing; iii1 "no significant time-periodic strain."
- **b1 negative work rate**: 0.04–0.06 mW (high-amplitude wing) vs 0.18–0.30 mW (low-amplitude wing) (full text, Walker 2014).
- **12 control muscles per wing**, divided into "steadily active" and "transiently active" classes. Lindsay, Sustar & Dickinson 2017, Current Biology — snippet-level (WebFetch of cell.com blocked with 403; this is from WebSearch summary only).
- Tu & Dickinson 1996 (J Exp Biol 178:813–830, Calliphora b1/b2) and Tu & Dickinson 1994 (J Exp Biol 192:207–224, negative work modulation) are correctly identified but **no numeric force/CSA/moment-arm values were retrieved** — paywalled, snippet level only.
- Melis, Siwanowicz & Dickinson 2024, Nature 628:795–803 (wing-hinge control via ML) — confirmed as correct citation (snippet level); no numeric muscle force/CSA data retrieved.
- **Conclusion: no measured absolute force, CSA, or moment-arm numbers were found for any individual steering muscle (b1/b2/b3/i1/i2/iii1/iii3/iii4/hg1–4) in Drosophila or Calliphora** within the accessed sources. Only relative strain/mass/timing data (above) are available.

## 3. Haltere muscles
- **Haltere musculature**: one asynchronous power muscle (hDVM) plus steering muscles described in one secondary source as "six steering muscles," in another as "seven direct synchronous steering muscles: hB1, hB2 (basalares) and hI1, hI2, hIII1, hIII2, hIII3 (axillaries)." Both are snippet-level (WebSearch summaries), not internally consistent, and not traced to a specific verified primary page — flagged as needing confirmation.
- Chan, Prete & Dickinson 1998, Science 280:289–292 (haltere gyroscope visual input) correctly identified but **no numeric force/CSA data retrieved** (snippet level only; full text not accessed).
- **No measured force, CSA, moment arm, or motor-unit-count data found for any haltere steering muscle.**

## 4. Proboscis muscles
- **16 proboscis muscles identified** (quote, full text): "We find a total count of 16 proboscis muscles." McKellar et al. 2020, eLife 54978 / PMC7316511 — full text fetched directly.
- **Motor-neuron counts**: most muscles innervated by 1 motor neuron, some (muscles 3, 8, 10, 11, 12) by 2; full per-muscle counts in **Table 1** (full text, McKellar 2020).
- **Kinematics**: rostrum/haustellum joint angles measured at 200 ms after extension onset, extension ratios in Figs. 7–9 (full text, McKellar 2020) — exact angle values not extracted by the fetch (only location identified).
- Schwarz et al. 2017, eLife 19892 ("Motor control of Drosophila feeding behavior"): "~20 distinct motor neurons per hemisphere control 13 muscle groups" — snippet level only; direct WebFetch of the eLife page and PDF both failed to load content.
- Rajashekhar & Singh 1994 (Int J Insect Morphol Embryol 23:225–242): cited as showing 12 pairs of muscles drive proboscis extension response — snippet-level citation only; paper not in PMC/Europe PMC full text, could not verify numbers.
- **No CSA, force, fiber count, or moment-arm data found for any proboscis muscle.**

## 5. Antennal muscles
- Mamiya & Dickinson 2015, J Neurosci 35:7977–7991: muscles are housed in the scape (A1) and actuate the scape–pedicel (A1–A2) joint; one snippet states "four muscles" are described in the first antennal segment, with motor neurons identified via genetic driver lines. Snippet level only — WebFetch not performed on this paper; no numeric CSA/force/MN-count/moment-arm data retrieved.
- **No measured mechanical data found.** This group has the thinnest coverage of all seven.

## 6. Abdominal muscles
- Zanker 1988 (J Comp Physiol A 162:581–588) is the correct primary reference on lateral abdomen deflection and yaw torque; full text inaccessible (Springer paywall). Only the mechanism description (shift of center of mass/drag line of action) was retrieved at snippet level.
- Dyhr et al. 2013, J Exp Biol 216:1523 ("Flexible strategies for flight control: an active role for the abdomen") — partial full-text fetch: moment of inertia of abdomen/thorax computed from an ellipse/circle geometric model (no explicit number extracted from the visible text); **transfer function delay of 41 ms** and high-pass behavior above ~0.5 Hz (quote, from Summary); visual stimulus velocities tested were 225, 450, 675°/s (these are stimulus values, not abdomen response kinematics). No force or EMG data reported in this study.
- **No measured muscle force, CSA, or moment-arm data for abdominal muscles found anywhere.**

## 7. General specific tension / cross-species checks
- **Arthropod muscle specific tension: 300–700 kPa** (quote, full text): "This rule was extended to arthropod muscles with values in the range 300–700 kPa." Insect jump muscle: click beetle 700 kPa, locust extensor tibiae 700 kPa; locust flight muscle 363 kPa; bumblebee DVM 38 kPa (Table 4). Vertebrate striated muscle ≈200–300 kPa. Source: "Force per cross-sectional area from molecules to muscles" review, PMC4968477 — full text fetched and quoted directly.
- A table entry in that review lists "*Drosophila* IFM: 3.6 kPa" — this value looks anomalously low compared to all other insect flight-muscle entries (tens–hundreds of kPa) and I could not verify it against the review's original source; **treat as suspect/unverified**, not for direct use.
- **Drosophila jump muscle (TDT) isometric tension: 37 ± 3 mN/mm² (wild-type), 53 ± 5 mN/mm² (embryonic myosin isoform)**, at sarcomere length 3.6 µm (quote, Table 2, full text). This is from Miller/Swank-type Biophysical Journal paper (PMC2849092), **not confirmed to be the Jarvis 2021 paper** you referenced — I could not get sciencedirect.com (403) or confirm the specific "34.7 mN/mm²" figure from Jarvis et al. 2021, Arch Biochem Biophys 701. Treat the 34.7 mN/mm² figure as **unconfirmed**; the verified, closely-related number is 37±3 mN/mm² from a different (but closely related) TDT paper.

## Summary Table

| Group | Quantity | Value | Species | Source + location | Read level |
|---|---|---|---|---|---|
| Neck | # neck motor neurons | ~25 pairs | Drosophila | Gorko et al. 2024 Nature, abstract | Secondary/snippet |
| Neck | Neck joint ROM | ±15° | Drosophila | Cellini & Mongeau 2022 eLife/PMC9651946, Fig 3C caption | Full text (partial) |
| Neck | Head/thorax saccade angular velocity | few thousand °/s (saccade); 0–100°/s (inter-saccade) | Calliphora | Schilstra & van Hateren 1998 Nature, abstract | Secondary/snippet |
| Wing | Steering muscle mass fraction | <3% of flight muscle mass | Calliphora vicina | Walker et al. 2014 PLoS Biol, Results | Full text |
| Wing | b1 strain | 2.3% / 5.5% (high/low amp wing) | Calliphora vicina | Walker et al. 2014, Fig. 8A | Full text |
| Wing | b1 negative work rate | 0.04–0.06 / 0.18–0.30 mW | Calliphora vicina | Walker et al. 2014, Results | Full text |
| Wing | Control muscles per wing | 12 | Drosophila | Lindsay et al. 2017 Curr Biol, abstract | Secondary/snippet |
| Haltere | Steering muscle set | hDVM + 6–7 steering muscles (hB1/2, hI1/2, hIII1-3) | Calliphora/Drosophila | secondary reviews (inconsistent count) | Secondary/snippet |
| Proboscis | # muscles | 16 | Drosophila | McKellar et al. 2020 eLife/PMC7316511 | Full text |
| Proboscis | MNs per muscle | 1 (most), 2 (muscles 3,8,10,11,12) | Drosophila | McKellar et al. 2020, Table 1 | Full text |
| Proboscis | MNs/muscle groups | ~20 MNs/hemisphere, 13 muscle groups | Drosophila | Schwarz et al. 2017 eLife, abstract | Secondary/snippet |
| Antenna | # muscles | 4 (scape) | Drosophila | Mamiya & Dickinson 2015, abstract | Secondary/snippet |
| Abdomen | Feedback delay | 41 ms | Drosophila | Dyhr et al. 2013 JEB, Summary | Full text (partial) |
| General | Arthropod muscle specific tension | 300–700 kPa | mixed arthropods | Force-per-CSA review, PMC4968477, Table 4 | Full text |
| General | Jump muscle (TDT) isometric tension | 37±3 mN/mm² (WT), 53±5 (EMB) | Drosophila | PMC2849092, Table 2 | Full text |

## What is missing (explicit gaps)
- No measured absolute force, CSA, fiber count, or moment arm for any named wing steering muscle, haltere muscle, proboscis muscle, antennal muscle, or abdominal muscle.
- No measured head, antenna, proboscis, or abdomen moment of inertia; no measured neck/antennal/abdominal joint stiffness or damping constants.
- Jarvis et al. 2021's specific "34.7 mN/mm²" figure could not be confirmed (paywalled); only a related TDT value (37±3 mN/mm²) was verified from a different paper.
- Primary anatomical papers (Strausfeld/Seyan/Milde 1987, Rajashekhar & Singh 1994, Zanker 1988, Chan et al. 1998, Tu & Dickinson 1994/1996, Heide & Götz 1996) remain paywalled/not in PMC — their numeric content (muscle counts, force traces, CSA) is unverified here and would need institutional access or document-delivery to extract.
