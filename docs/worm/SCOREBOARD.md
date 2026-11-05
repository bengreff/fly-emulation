# C. elegans emulation: validation scoreboard

Derived from `STATE_OF_THE_ART.md` section 3 (behaviour corpus) and `PLAN.md` section c (fitting
architecture, held-out split). Nothing here changes either document's content or numbering; this
file adds the columns needed to run the scoreboard (protocol, dataset access, real spread, proposed
FIT/HELD-OUT split) and cross-references the original corpus IDs throughout. Canon (corpus item
list, mechanism ledger, loss table, held-out policy in PLAN c.4) is treated as locked and is not
reopened here.

Pass bar (PLAN c.4, unchanged): a prediction counts as a pass when it lands within mean +/- 2 SD of
the real animal-to-animal spread (SD from SEM x sqrt(n) where only SEM is published), at >= 80% of
the scored quantities of its type, AND a named wrong model fails the same test. A test with no wrong
model named is not scored as informative.

## 0. How to read this

- **ID** follows `STATE_OF_THE_ART.md` section 3 numbering (1-87, 90) where the entry exists there.
  New entries (ephys-class holdouts, Kato 2015, named mutants) start at 91. IDs 88-89 from the corpus
  are excluded here: they describe other groups' models (BAAIWorm/MetaWorm, modWorm), not independent
  real-animal ground truth, so they cannot be a target to predict against.
- **Layers** cites mechanism-ledger row numbers from `PLAN.md` section a (1-23), taken directly from
  each row's own "Needed for" column (inverted). Rows 1-6 (cell inventory, morphology, channel
  presence/kinetics/densities, calcium handling) underlie essentially every neural entry and are not
  repeated row by row; only the differentiating rows (7 onward) are listed unless an entry is itself
  an ephys target, in which case 2/5/6 are named explicitly.
- **Split**: FIT (used in the loss), HELD-OUT (sealed, no refit, scored once per PLAN c.4), or
  DEFERRED (out of scope for the first, hermaphrodite-only, single-snapshot-adult animal, per PLAN's
  own scoping of items 54-60 and the Gaps section's treatment of item 76). This is a *proposed*
  instance of the split, not a replacement for PLAN c.4's "about a third, chosen by seed" procedure;
  the seed draw is still the thing that finalizes it.
- **Real spread**: given where a specific SD/range/n is already established in the literature cited;
  flagged "extract before scoring" where the source almost certainly reports it but it was not pulled
  into this pass (same evidence-labelling convention as `STATE_OF_THE_ART.md` section 4 - do not
  invent a number to fill the cell).
- Totals: 100 entries. 92 scored (61 FIT, 31 HELD-OUT), 8 DEFERRED (male mating 54-60, and item 76,
  connectome-across-development, which needs a development model not built for the first animal).
  Counts by category are in section 20.

## 1. Locomotion, gait, and motor-circuit structure

| # | Entry | Quantity (units) | Protocol | Dataset (paper; access) | Real spread (n) | Layers | Split |
|---|---|---|---|---|---|---|---|
| 1 | Crawling speed | mm/s, ~0.21-0.26 | NGM agar plate, fed young adult, free locomotion, 2-5 min track | Fang-Yen 2010 PNAS (arXiv 2006.10122); OWMD (movement.openworm.org) - public, Zenodo, CSV/HDF5 tracks; not yet on backhouse | CV roughly 15-20% typical for this assay class; exact SD/n extract from Fang-Yen 2010 Fig. 1 | 12,21,22 | FIT |
| 2 | Swimming speed | mm/s, ~0.35-0.36 | M9 buffer droplet, free swim, same duration | same source | extract before scoring | 12,21,22 | FIT |
| 3 | Crawling bend frequency | Hz, ~0.3-0.5 | as #1, posture skeleton | same source | extract before scoring | 12,21,22 | FIT |
| 4 | Swimming bend frequency | Hz, ~1.5-2 | as #2 | same source | extract before scoring | 12,21,22 | FIT |
| 5 | Crawling wavelength | mm, ~0.79 (~2 bends/body length) | as #1 | same source | extract before scoring | 12,21,22 | FIT |
| 6 | Swimming wavelength | mm, ~2.12 (~1 bend/body length) | as #2 | same source | extract before scoring | 12,21,22 | FIT |
| 7 | Gait transition vs. viscosity | freq/wavelength/speed vs. methylcellulose viscosity, continuous curve | dish series at several viscosities (1-50+ cP), track at each, same animals not required | Fang-Yen 2010 PNAS; Boyle, Berri & Cohen 2012 model paper | per-viscosity-bin SD typically reported; n ~20/bin in Fang-Yen 2010 (extract exact) | 12,17,21,22 | **HELD-OUT** - W2 roadmap target: blind prediction at viscosities not in the fitting set |
| 8 | VNC oscillator chaining (no single pacemaker) | qualitative/structural: local oscillation persists after simulated mid-body "cut" | compare simulated transection response to published forward/backward wave persistence after real transection | Izquierdo & Beer bioRxiv; Olivares et al. 2021 | not an SD test; scored pass/fail against the published qualitative result | 7,8,21 | **HELD-OUT** - tests the circuit didn't cheat with a hidden pacemaker |
| 9 | Spontaneous reversal rate | reversals/min, baseline | plate, no stimulus, 10-30 min track | OWMD; Yemini et al. 2013 Nat Methods - public; OWMD Zenodo CSV/HDF5; Yemini feature matrices via paper supplement, ~10,000 worms/300+ strains | strain/condition dependent; N2 baseline extract before scoring, n in the hundreds of worms available | 7 | FIT |
| 10 | Omega-turn rate and geometry | turns/min + curvature profile | same tracking as #9 | Tierpsy Tracker; Yemini 2013 | extract before scoring | 7,12,21 | FIT |
| 72 | Proprioceptive gait feedback | curvature-dependent modulation of local bend amplitude | compare local bend amplitude vs. local body curvature (not just time) in freely moving animals | proprioceptive-feedback literature, arXiv 1705.02301 | reported as a fitted gain/correlation, not yet pulled as SD; extract before scoring | 7,8,12,17 | FIT - also the mechanism zeroed by the "no proprioception" control (section 16) |
| 73 | Ablation of AVA/AVB/PVC/AVD: locomotor deficits | specific loss of forward-only / backward-only / coordination phenotype per ablated cell | laser-ablate the named cell(s) in the simulated connectome (zero the cell, no refit), compare to published ablation phenotype | classic ablation literature, used as validation in Kunert et al. models | phenotypes mostly qualitative (loss/retention of forward or backward locomotion); quantify from the cited papers before scoring | 7 | **HELD-OUT** - ablation test, no refit |

## 2. Mechanosensation, touch, and tap-withdrawal

| # | Entry | Quantity (units) | Protocol | Dataset (paper; access) | Real spread (n) | Layers | Split |
|---|---|---|---|---|---|---|---|
| 11 | Anterior gentle-touch response (ALM/AVM) | reversal probability on anterior touch | eyebrow-hair touch anterior to mid-body, scored reversal yes/no over N trials | Chalfie et al. 1985 J Neurosci (laser ablation) | probability with binomial CI; n = cells/animals per ablation group, small classic study - extract before scoring | 7,8,17 | FIT |
| 12 | Posterior gentle-touch response (PLM) | forward-acceleration probability on posterior touch | as #11, posterior | Chalfie et al. 1985 | as #11 | 7,8,17 | FIT |
| 13 | Harsh-touch response (PVD) | withdrawal distinct from gentle-touch pathway (different latency/kinematics) | harsh mechanical pinch, compare response profile to gentle touch | WormBook Mechanosensation | qualitative distinctness, not a shared SD; extract quantitative withdrawal-latency distribution before scoring | 7,11,17 | **HELD-OUT** - tests a genuinely separate nociceptive pathway emerges, not a relabelled gentle-touch circuit |
| 14 | Nose-touch avoidance | reversal probability on anterior collision | worm driven into an obstruction (hair/bead), reversal scored | ASH IP3R paper, PLoS Genetics 2009 | extract before scoring | 7,17 | FIT |
| 15 | Tap-withdrawal habituation (short-term) | response decrement over repeated taps, trials | plate tap series, fixed ISI, response amplitude per trial | Rankin, Beck & Chiba 1990 | decrement curve with SEM per trial, n = tens of worms per group (classic design) | 7,18 | FIT |
| 16 | Tap-withdrawal long-term habituation | retention over hours after spaced training | spaced-training protocol, retest hours later | Rankin et al., reviewed Learn. Mem. 2001 | extract before scoring | 7,18 | **HELD-OUT** - protein-synthesis-dependent plasticity, a distinct mechanism from short-term habituation |
| 17 | Tap response probability vs. ISI | parametric response curve | tap series at varying inter-stimulus intervals | temporal-processing lit, arXiv 1803.04085 | curve with error bars per ISI bin; extract n | 7 | FIT |

## 3. Chemosensation

| # | Entry | Quantity (units) | Protocol | Dataset (paper; access) | Real spread (n) | Layers | Split |
|---|---|---|---|---|---|---|---|
| 18 | NaCl chemotaxis | chemotaxis index (-1 to +1) toward NaCl gradient | radial gradient plate, worms placed at edge, scored after fixed time | classic Ward/Bargmann assays, WormBook Chemotaxis | plate-level SD typically ~0.1-0.2 CI units, n(plates) ~5-15, n(worms/plate) ~50-200 - extract exact | 7,17,22 | FIT |
| 19 | Diacetyl attraction (AWA) | chemotaxis index | same plate assay, diacetyl spot | AWA-mediated attraction lit | as #18 | 7,17,22 | FIT |
| 20 | Benzaldehyde/isoamyl alcohol attraction (AWC) | chemotaxis index | same plate assay | AWC-mediated attraction lit | as #18 | 7,17,22 | FIT |
| 21 | Biased-random-walk / klinotaxis strategy | pirouette-rate modulation + weathervaning curvature bias, as a function of gradient slope | track full trajectories in a gradient, decompose into pirouette vs. weathervaning components | Pierce-Shimomura klinotaxis analyses | decomposition statistics per animal; extract n | 7,17 | FIT |
| 22 | CO2 avoidance | avoidance index | CO2 gradient plate assay | PNAS 2008 (BAG/TAX-2/4) | extract before scoring | 7,17,22 | FIT |
| 23 | Oxygen preference / aerotaxis | peak preference, ~8-10% O2 | O2 gradient chamber | PLoS Biology 2006 | extract before scoring | 7,17,22 | FIT |
| 24 | O2-CO2-temperature cross-modulation | URX tonic signalling sets CO2-response gain, measured as a shift in the CO2 avoidance curve under different O2/temperature backgrounds | combined gas/temperature gradient assay | PLoS Genetics 2014 | extract before scoring | 7,17,22 | **HELD-OUT** - a mechanistic prediction (gain set by a different sensor) rather than a fitted curve |
| 25 | Hyperosmotic (glycerol) avoidance | fraction escaping a glycerol ring, fixed time | glycerol-ring assay | ASH osmotic-avoidance lit | extract before scoring | 7,11,16,17,22 | FIT |
| 26 | Osmotic avoidance adaptation | reduced avoidance after pre-exposure | pre-expose to osmotic stimulus, retest | osmotic-avoidance adaptation lit | extract before scoring | 7,11,17,18,22 | **HELD-OUT** - adaptation dynamics, also the glia-shaping test (section 2 control) |
| 27 | Copper avoidance | avoidance index, food-state dependent | copper-ring assay, fed vs. starved | dopamine-modulated avoidance, PMC3061029 | extract before scoring | 7,10,11,17,22 | FIT |

## 4. Thermosensation, nociception, and dauer

| # | Entry | Quantity (units) | Protocol | Dataset (paper; access) | Real spread (n) | Layers | Split |
|---|---|---|---|---|---|---|---|
| 28 | Thermotaxis set-point (isothermal tracking) | tracks near cultivation temperature | radial thermal gradient plate | Mori & Ohshima 1995 Nature | extract before scoring | 7,17,22 | FIT |
| 29 | Bidirectional thermotaxis strategy | distinct strategies above vs. below set point | as #28, scored separately above/below set point | PNAS 2014 | extract before scoring | 7,17,22 | FIT |
| 30 | Noxious-heat avoidance | rapid withdrawal latency, distinct circuit from thermotaxis | focal laser/heat-probe stimulus | FLP/AFD nociceptive lit | extract before scoring | 7,17,22 | FIT |
| 31 | Dauer formation vs. pheromone + temperature | dauer-entry fraction as a function of ascaroside dose and temperature | dose-response plate assay, several ascaroside concentrations x 2 temperatures | classic dauer-pheromone dose-response lit | dose-response curve with per-point SEM; extract n | 9,17,18,19 | FIT |

## 5. Feeding and pharynx

| # | Entry | Quantity (units) | Protocol | Dataset (paper; access) | Real spread (n) | Layers | Split |
|---|---|---|---|---|---|---|---|
| 32 | Pharyngeal pumping rate (fed) | ~4-5 Hz, ~250 pumps/min | electropharyngeogram (EPG) or visual count, on food | Avery & Horvitz 1989; WormBook Feeding | ~20-30 pumps/min SD typical for this assay (approx); n ~20-30 worms - extract exact | 13 | FIT |
| 33 | Single-pump duration | ~170 ms | EPG trace | same source | extract before scoring | 13 | FIT |
| 34 | Food-dependent on/off switching | pumping ceases within seconds off food | remove from food, time to pumping cessation | WormBook Feeding | extract before scoring | 13 | **HELD-OUT** - qualitative behavioural switch, strong mechanism test |
| 35 | Serotonin regulation of pumping | rate modulated by exogenous serotonin dose | bath-applied serotonin, dose series, EPG | Scientific Reports 2016 | dose-response curve; extract SD/n | 10,13 | FIT |
| 36 | Foraging head-swing rate (on vs. off food) | head-swing frequency change | tracked head angle, on vs. off food | eLife 2022 automated feeding-tracking | extract before scoring | 7,17,22 | FIT |

## 6. Internal states: sleep, roaming/dwelling, social

| # | Entry | Quantity (units) | Protocol | Dataset (paper; access) | Real spread (n) | Layers | Split |
|---|---|---|---|---|---|---|---|
| 37 | Roaming/dwelling bout durations and switching | bout-duration distribution, minutes-scale | long (hours) single-worm tracking, classify roaming vs. dwelling by speed/turning | Flavell et al. 2013 Cell | bout-duration distributions with per-animal variability; n = tens of worms - extract exact | 9,10,18,20 | FIT |
| 38 | Lethargus duration per larval stage | ~2 h per molt, quiescent | long tracking through larval transitions, quantify quiescent-bout duration per molt | Raizen et al. 2008 Nature | ~2 h mean; SD/n extract before scoring | 9,18 | **HELD-OUT** - a slow-states target the model must reach without having been fit to molt timing directly |
| 39 | Developmental-sleep homeostatic rebound | increased quiescence after deprivation | mechanically deprive quiescence during lethargus, measure rebound | Raizen 2008; eLife 2015 follow-up | extract before scoring | 9,18 | FIT |
| 40 | Satiety quiescence onset after refeeding | gradual inhibition of feeding/movement after refeeding | starve then refeed, track onset/time-course of quiescence | You, Kim, Raizen & Avery 2008 Cell Metab | extract before scoring | 9,18,20 | FIT |
| 41 | Global quiescent brain state during lethargus | brain-wide downregulation of activity | whole-brain imaging through a lethargus bout | Nichols et al. 2017 Science | scored as the whole-brain statistics in section 17, not a single scalar | 9,18 | FIT |
| 42 | Social feeding / aggregation (npr-1-dependent) | solitary vs. social feeding phenotype | compare bacterial-lawn-border aggregation, wild-type-like vs. npr-1 allele background | classic npr-1 aggregation lit | categorical phenotype, scored pass/fail per genetic background | 9 | **HELD-OUT** - genotype-dependent phenotype, mutant-style test |

## 7. Egg-laying and defecation

| # | Entry | Quantity (units) | Protocol | Dataset (paper; access) | Real spread (n) | Layers | Split |
|---|---|---|---|---|---|---|---|
| 43 | Egg-laying rate, basal | ~1-3 eggs/hr, temperature-dependent | single-worm plate, count laid eggs over hours | Comm Biology 2022; Byerly et al. 1976 (wormatlas.org PDF) | rate with SD per temperature bin; n extract | 10,15 | FIT |
| 44 | Egg-laying rate, serotonin/nicotine-stimulated | ~7.4 eggs/hr | bath-applied serotonin or nicotine, same count protocol | Comm Biology 2022 | extract before scoring | 10,15 | **HELD-OUT** - pairs with the tph-1 mutant test (#98), a cross-check of the same serotonergic mechanism |
| 45 | Egg-laying rate, peak adulthood | up to ~9 eggs/hr at ~92 h post-hatch | same count protocol across the adult timeline | life-cycle/egg-laying lit | extract before scoring | 15 | FIT |
| 46 | Inter-egg-interval distribution | bimodal timing (active/inactive HSN states) | continuous single-worm egg-laying event timing | classic egg-laying-state lit (WormBook) | bimodal fit parameters; n per animal and across animals - extract | 15 | **HELD-OUT** - distributional shape, not a mean rate; tests bistability, not just average output |
| 47 | Brood size | ~300 offspring/hermaphrodite | daily transfer, count total progeny | Byerly et al. 1976 | SD roughly 10-20% of mean typical for this measure; n = tens of worms - extract exact | 15,20 | FIT |
| 48 | Generation time | ~3.5 days at 20 degC | egg to egg-laying adult, timed | Byerly et al. 1976 | extract before scoring | 20 (whole-organism; not individually ledgered) | FIT |
| 49 | Defecation motor program cycle period | 45 s (+/- < 3 s at 20 degC), temperature-insensitive 19-30 degC | single-worm video, time successive defecation events | WormBook Defecation; Thomas 1990 | SD < 3 s already stated in the corpus; n = multiple worms, > 100 cycles pooled (Thomas 1990 design) - confirm exact n | 14 | FIT |
| 50 | Defecation IP3R-dependent rhythm | ~45-50 s rhythm from posterior-intestine Ca2+ oscillation | as #49, with intestinal Ca2+ imaging alongside | Dal Santo et al. 1999 Cell | extract before scoring | 14 | **HELD-OUT** - a distinct mechanistic claim (what sets the period) from #49 (the period itself) |
| 51 | Defecation reset by touch | next DMP occurs 45 s after a touch perturbation, not at the pre-perturbation phase | mechanical touch at a known phase of the cycle, measure next-event timing | WormBook Defecation | extract before scoring | 14 | FIT |
| 52 | Defecation step sequence (pBoc, aBoc, eBoc) | discrete steps, fixed order and timing | video, annotate step onsets | WormBook Defecation | extract before scoring | 14 | FIT |
| 53 | HSN/defecation circuit coupling | egg-laying command neurons shift defecation timing | compare defecation-cycle statistics with/without recent egg-laying events | PMC7252377 | extract before scoring | 14,15 | FIT |

## 8. Male mating (deferred)

Items 54-60 (full mating sequence, response/latency, ventral turning, vulva-location search, spicule
insertion, sperm transfer, shared defecation-circuit reuse during mating) are **DEFERRED**: PLAN.md
section a states male-specific items are out of scope for the first animal (answer 7). Listed here
only so the corpus total is traceable; not scored FIT or HELD-OUT until a male model is built.

## 9. Learning and memory

| # | Entry | Quantity (units) | Protocol | Dataset (paper; access) | Real spread (n) | Layers | Split |
|---|---|---|---|---|---|---|---|
| 61 | Salt (NaCl) chemotaxis associative learning | shift from attraction to avoidance after salt+starvation pairing | pair NaCl exposure with starvation, retest chemotaxis index | classic salt-learning paradigm, reviewed Learn. Mem. 2010 | pre/post CI shift with SEM; extract n | 7,18 | FIT |
| 62 | NMDA-dependent long-term memory for salt learning | memory persists hours vs. short-term (minutes) | as #61, retest at multiple delays, +/- NMDA-pathway perturbation | Kano et al., Current Biology | extract before scoring | 7,18 | FIT |
| 63 | Thermotaxis associative learning | learned association of feeding state with cultivation temperature | rear at a temperature x feeding-state combination, retest thermotaxis set point | thermotaxis-plasticity lit (Mori 1997 and successors) | extract before scoring | 7,18 | FIT |
| 64 | Chemosensory adaptation (ASH to repellents) | reduced Ca2+ response after repeated exposure | repeated-exposure Ca imaging in ASH | EMBO J ASH imaging paper | extract before scoring | 7,11,17,18 | FIT |
| 65 | Pathogen (aversive) learning | single-exposure shift in bacterial-lawn preference | single pathogenic-bacteria exposure, retest lawn choice | pathogen-avoidance learning lit | extract before scoring | 7,9,10,18 | **HELD-OUT** - generalizes the learning mechanism (built mainly from salt-learning data) to a different modality and a single-trial paradigm |

## 10. Life history and aging

| # | Entry | Quantity (units) | Protocol | Dataset (paper; access) | Real spread (n) | Layers | Split |
|---|---|---|---|---|---|---|---|
| 66 | Lifespan / survival curve | median ~2-3 weeks at 20 degC | cohort survival assay, daily scoring | standard C. elegans lifespan lit | survival-curve CI; standard cohort n ~50-100+ per assay (field convention) - confirm exact | 19,20 | FIT |
| 67 | Locomotor decline with age | measurable slowing of crawling speed across adult lifespan | repeat protocol #1 at several ages across the lifespan | lifespan/locomotion-aging lit (Tierpsy-based) | decline curve with per-age-bin SD; extract n | 12,19,21 | **HELD-OUT** - tests whether a generic aging rate (not fit to this curve) plus the young-adult neuromuscular model predicts the real decline |
| 68 | Pharyngeal pumping decline with age | reduced pumping rate in aged animals | repeat protocol #32 at several ages | feeding/aging lit | extract before scoring | 13,19 | FIT |
| 69 | Dauer exit kinetics (recovery on food) | time course of dauer-to-L4 recovery | return dauer-stage animals to food, time recovery | classic dauer-recovery lit | extract before scoring | 18,19 | FIT |

## 11. Sensory misc, connectome, and structural checks

| # | Entry | Quantity (units) | Protocol | Dataset (paper; access) | Real spread (n) | Layers | Split |
|---|---|---|---|---|---|---|---|
| 70 | Photophobic (UV/blue-light) avoidance | avoidance response, LITE-1-mediated | focal UV/blue-light stimulus, score avoidance | LITE-1 photoreception lit | extract before scoring | 17 | FIT |
| 71 | Electrotaxis | directed movement along an applied electric field | DC field across an agar arena, track heading | electrotaxis assay lit | extract before scoring | 17 | **HELD-OUT** - the sensing mechanism itself is not identified in the ledger (corpus flags it "unknown field-sensing circuit"); an informative failure is expected, not a confident pass |
| 74 | Signal-propagation sign/strength/kinetics (23,433 pairs) | sign, amplitude, delay of response to optogenetic stimulation of each of many neurons | reproduce stimulation protocol per probed pair, score against the functional atlas via the GCaMP observation model | Randi et al. 2023 Nature; DANDI 001075 (raw, not fetched), OSF e2syt (processed, 637 MB, on backhouse per MANIFEST.md) - public | trial-to-trial spread per pair, directly in the dataset; n = repeats per pair, varies | 7,9,23 | **HELD-OUT** - PLAN c.4: hold out 20% of stimulated neurons, all their responses, by neuron not by trial |
| 75 | Brain-wide state representations across timescales | multiplexed behaviour/state encoding in whole-brain activity | freely moving NeuroPAL-identified imaging across conditions, score via section 17 statistics | Atanas et al. 2023 Cell; Zenodo 8185377 (714 MB, on backhouse per MANIFEST.md) - public, CC BY 3.0 US | animal-to-animal and condition-to-condition spread in the dataset itself | 7,9,23 | **HELD-OUT** - PLAN c.4: hold out ~25% of whole animals and at least one whole condition |
| 76 | Connectome change across development (8 animals) | synaptic-weight change while overall geometry stays fixed | n/a - no development model built for the first animal | Witvliet et al. 2021 Nature; OpenWorm toolbox (91 MB, on backhouse) - public | n/a | 2 | **DEFERRED** - requires a development model (Gaps section, explicitly priority (2) after the base animal) |
| 77 | Individual-to-individual connectome variability | spread in wiring across fixed-stage animals | run the model as a population with connectomes varied across Witvliet's 8 animals; compare simulated population spread in a behaviour (e.g. #1, #9) to the real spread | Witvliet et al. 2021 | spread across 8 animals, directly measurable from the dataset | 2 | **HELD-OUT** - this *is* PLAN c.4's "many worms" test: variability itself as a scored output |
| 78 | Nerve-ring contactome organisation | precisely wired core circuit embedded in a variable background | compare simulated synapse-formation priors against the contact-map's core/variable split | Brittin et al. 2021 Nature; Zenodo 4763083 - public, not yet on backhouse | core-vs-variable classification given in the paper; no per-animal SD needed (it's a structural, not behavioural, comparison) | 2 | FIT - structural prior on where synapses can form, not itself a blind behavioural target |
| 90 | Innexin expression breadth (UNC-7/UNC-9 dominance) | broadest-expressed gap-junction genes identified | compare the model's fitted innexin-pairing bounds to the expression-breadth ranking | Altun et al. 2009; misc/bhattacharya2019_innexin (168 KB, on backhouse) | expression breadth ranking, not an SD | 8 | FIT - sets which innexin pairings get the tightest (best-characterized) bounds |

## 12. Single-neuron/muscle biophysics and per-class ephys

| # | Entry | Quantity (units) | Protocol | Dataset (paper; access) | Real spread (n) | Layers | Split |
|---|---|---|---|---|---|---|---|
| 79 | Body-wall-muscle whole-cell dynamics | preferred oscillation frequency, matching the locomotor band | whole-cell current-clamp of a dissected BWM preparation, drive at several frequencies | Du, Crodelle et al. 2024 PLoS Comp Biol | extract before scoring | 12 | FIT |
| 80 | AWCon/RMD single-neuron current traces | voltage/current-clamp traces | reproduce the published clamp protocol per cell, compare to the HH model's reproduction | Nicoletti et al. 2019 PLoS ONE / ModelDB 267187 (code only, no raw traces; figures need digitising) | n not stated in the model repo; figure-digitised traces per paper - extract | 2,5,6 | FIT |
| 81 | Bulk body mechanical response under hydrostatic pressure | bulk modulus independent of cuticle | isotropic-pressure loading of an intact worm | Biophysical Journal 2015, "Worms under pressure" | extract before scoring | 16,21 | **HELD-OUT** - an independent-technique cross-check against whichever AFM/cantilever-derived stiffness range is used to fit the body (Gaps section flags the 2+ orders-of-magnitude disagreement across techniques) |
| 82 | Body Young's modulus (cuticle/muscle/pseudocoelom) | cuticle 75-140 kPa; muscle 600-2,100 kPa; pseudocoelom 42-275 kPa | AFM indentation / finite-element reconstruction per tissue | Frontiers Bioeng. 2024 | ranges as stated are the spread itself (by technique); treat per-technique range as the fitting bound | 21 | FIT - defines the bounded range the fit is not allowed to leave |
| 91 | AIY current/voltage-clamp | mV traces, current-clamp steps -15 to +35 pA by 5 pA (11 steps); population voltage-clamp I-V | reproduce the Naudin 2022 clamp protocol in Jaxley | Naudin et al. 2022 PLoS ONE; Mendeley 6pgdf3zrp3 (36 MB, on backhouse) - public, CC BY 4.0 | n = 7 cells (current-clamp file is 1 cell + a separate n=5-7 voltage-clamp population, per `ephys_sources.md`) | 2,5,6 | **HELD-OUT** - already run: SPIKE.md W0 result, both held-out bars passed, train bar narrowly failed |
| 92 | RIM current/voltage-clamp | mV traces, same clamp protocol | as #91 | Naudin et al. 2022; same Mendeley dataset, on backhouse | n = 3 cells | 2,5,6 | **HELD-OUT** - W1 roadmap target |
| 93 | AFD current/voltage-clamp | mV traces, 11-step current-clamp at 10 kHz raw | as #91, AFD-specific | Naudin et al. 2022; same Mendeley dataset, on backhouse | n = 3 cells | 2,5,6 | **HELD-OUT** - W1 roadmap target |
| 94 | AWA current-clamp (spiking, Ca-mediated) | mV/current traces | reproduce published clamp protocol (exact steps not yet pulled from Methods) | Liu et al. 2018 Cell; Mendeley tngf9w3pgd, 809 MB - public, CC BY 4.0, **not yet fetched to backhouse** | cell count not confirmed this pass; extract from paper | 2,5,6 | FIT - spiking/Ca-action-potential mechanism needs its own calibration pass before a holdout is meaningful |

## 13. Metabolism and phenotyping

| # | Entry | Quantity (units) | Protocol | Dataset (paper; access) | Real spread (n) | Layers | Split |
|---|---|---|---|---|---|---|---|
| 83 | Metabolic flux landscape (whole organism) | semi-quantitative flux map, isotope-validated | compare model-predicted fluxes to stable-isotope tracing results | Nature 2025 (Perturb-seq + isotope tracing) | isotope-tracing CI per flux; extract | 20 | **HELD-OUT** - the isotope-tracing arm is independent ground truth, not used to build the network itself |
| 84 | Tissue-resolved metabolic predictions | muscle/intestine/hypodermis-specific flux differences | compare tissue-specific predictions to MERGE's resolved outputs | MERGE, Mol Syst Biol 2020 | extract before scoring | 20 | FIT - used to set tissue-specific metabolic parameters |
| 85 | Gene-essentiality prediction | lethal/viable classification per gene knockout | zero the gene in the metabolic network, compare to iCEL1273's lethal/viable call | Yilmaz & Walhout 2016 Cell Systems | classification accuracy over the gene set tested; extract n genes | 20 | **HELD-OUT** - predict essentiality for a held-out gene subset not used to tune the network |
| 86 | Phenotypic feature battery across strains | 700+ quantified behavioural features/worm, 300+ strains | Tierpsy/Yemini feature pipeline on tracked worms | Yemini et al. 2013 Nat Methods; ~10,000 worms | n = 10,000 worms, 300+ strains (stated in the paper) | 23 | FIT - defines the feature-space baseline and variability envelope |
| 87 | Strain classification from postural features | classification accuracy vs. feature-set size | run the same classifier the Tierpsy benchmark used, on simulated-vs-real feature vectors | Tierpsy Tracker benchmark (56.2% at 1,024 features vs. 47.8% at 256, in-paper) | the two reported accuracy numbers are the target; no per-animal SD | 23 | **HELD-OUT** - a genuinely blind numeric comparison against a benchmark number already in print |

## 14. Whole-brain cross-check

| # | Entry | Quantity (units) | Protocol | Dataset (paper; access) | Real spread (n) | Layers | Split |
|---|---|---|---|---|---|---|---|
| 95 | Low-dimensional motor-command manifold | correlation structure, state-transition rates in immobilized/restrained whole-head imaging | reproduce Kato's immobilized imaging condition in silico, score via section 17 statistics | Kato et al. 2015 Cell | dataset not yet located as a standalone small public download this pass (flagged in MANIFEST.md); n = animals in the original study, extract | 7,9,23 | **HELD-OUT** - a different animal set and a different restraint condition from Atanas 2023, so it's an independent cross-check of the same mechanism, not a repeat of #75 |

## 15. Mutants and genetic ablations (held-out by rule)

Every entry below zeroes a specific gene (or synthesizes the loss directly, where the mechanism is a
transporter/channel/synthesis enzyme rather than a receptor) in the model's own parameter tables, with
**no refit**, and compares to the published mutant phenotype. Per PLAN c.4: "Mutant predictions are
the strongest test of 'the same brain', because they probe internal mechanism, not just output" - so
unlike the rest of the corpus, these are not partially split; all of them are HELD-OUT, and each needs
its own named must-fail control (section 16) alongside the real mutant comparison.

| # | Gene | Mechanism removed | Predicted phenotype to match | Dataset (paper; access) | Layers | Split |
|---|---|---|---|---|---|---|
| 96 | unc-31 (CAPS) | dense-core-vesicle release of neuropeptides | broad locomotor/foraging deficits from loss of peptidergic signalling; used by Randi 2023 itself as a perturbation (OSF has an `exported_data_unc31` variant, not fetched - see MANIFEST.md) | Randi 2023 OSF e2syt (unc-31 variant not yet on backhouse); classic unc-31 phenotype lit | 9 | **HELD-OUT** |
| 97 | tdc-1 | tyramine/octopamine synthesis (tyrosine decarboxylase) | loss of tyramine-dependent escape/pumping modulation | tdc-1 phenotype lit | 10 | **HELD-OUT** |
| 98 | tph-1 | serotonin synthesis (tryptophan hydroxylase) | reduced serotonin-stimulated egg-laying (cross-check against #44) and reduced dwelling | tph-1 phenotype lit | 10 | **HELD-OUT** |
| 99 | cat-2 | dopamine synthesis (tyrosine hydroxylase) | loss of the basal slowing response on food, altered copper-avoidance gain (cross-check against #27) | cat-2 phenotype lit | 10 | **HELD-OUT** |
| 100 | eat-4 | vesicular glutamate transporter | broad loss of glutamatergic chemosensory/synaptic transmission, measurable as a reduced chemotaxis index (cross-check against #18-20) | eat-4 phenotype lit | 7 | **HELD-OUT** |
| 101 | unc-7 | innexin (gap junction) | locomotor/backward-escape coordination deficit, distinct from the full "no gap junctions" control (section 16) | unc-7 phenotype lit | 8 | **HELD-OUT** |
| 102 | unc-9 | innexin (gap junction) | as unc-7, overlapping but non-identical deficit (the two innexins pair asymmetrically) | unc-9 phenotype lit | 8 | **HELD-OUT** |

Not duplicated here: entry #73 (AVA/AVB/PVC/AVD laser ablation) and #42 (npr-1 aggregation) are already
HELD-OUT mutant/ablation-style tests in their own category tables above; #96-102 extend the same
principle to the specific genes the brief named.

## 16. Must-fail controls, one named wrong model per category

Per DECISION 2 (PLAN.md): every HELD-OUT test that lacks a named wrong model expected to fail it is
"declared uninformative." These are the controls; each must land outside the +/-2 SD band on the
listed tests, or that test does not count.

| Wrong model | What's removed/replaced | Layer(s) zeroed | Must fail these HELD-OUT tests | Why this is the right falsifier |
|---|---|---|---|---|
| Connectome-only weights | EM synapse count as the sole conductance; no transmitter/receptor sign, no Randi calibration | 7 (sign/strength step) | 74, 75, 8, 73 | Randi 2023's own headline finding: the anatomical connectome alone predicts function poorly |
| No neuropeptides | zero row 9 entirely | 9 | 38, 42, 44, 46, 65 | peptide signalling is structurally necessary for slow-state and modulated behaviours (Gaps section, hardest problem #1) |
| No monoamines | zero row 10 entirely | 10 | 35, 44, 37 | distinguishes the engineered "whole layer off" control from the real tph-1/tdc-1/cat-2 null mutants (#96-99), which remove one gene, not the whole modulatory system |
| Passive membranes | remove all active conductances, leak only | 3,4,5 | 91, 92, 93 | the exact failure mode flagged in DECISION 2 itself (F-W0-6): a too-lenient band can pass a barely-fitted or degenerate model |
| No proprioception | zero stretch-receptor feedback into motor neurons | 17 (proprioceptive branch) | 7, 72 | named explicitly in the brief; gait-vs-viscosity adaptation should collapse without it |
| No gap junctions | zero row 8 entirely | 8 | 8, 73 | VNC chaining and ablation-deficit patterns depend on electrical coupling, not just chemical synapses |
| Static sensory transduction | remove adaptation dynamics from row 17 | 17 | 26, 71 | adaptation is the behaviour being tested, not incidental to it |
| No slow intracellular signalling | zero row 18 (egl-4/PKG, insulin, CREB, etc.) | 18 | 38, 67 | removes the only mechanism that can produce hours-scale state change |
| No individual variability | single deterministic parameter point, no population spread | 2 (population draw) | 77 | #77 is defined as a test of variability itself; a point model cannot pass it by construction |
| Lumped, tissue-blind metabolism | one whole-body metabolic state, no tissue resolution | 20 | 83, 85 | tissue-resolved predictions are the thing being scored |

## 17. Whole-brain activity tests: scoring statistics

Per PLAN c.2 (loss L3): trajectory MSE is explicitly rejected ("spontaneous activity is not
repeatable trial by trial, so trajectory MSE would reward memorising"). The four named datasets are
scored on statistics, not frame-by-frame traces:

- **Randi et al. 2023** (entry 74, driven/evoked, not spontaneous): sign agreement (% of probed
  pairs where the model's response sign matches, excitatory/inhibitory/none), amplitude correlation
  (Pearson r between model and measured response amplitude, through the shared GCaMP observation
  model, row 23), response delay/kinetics (onset latency and rise-time error, scored within the
  measured trial-to-trial spread, not against a single trial), and causal-direction concordance
  (does stimulating i still produce the measured effect on j and not a spurious reverse effect).
- **Atanas et al. 2023** (entry 75) and **Kato et al. 2015** (entry 95), both spontaneous: pairwise
  correlation structure (compare the model's neuron-neuron correlation matrix to the real one, e.g.
  Frobenius-norm or representational-similarity comparison, not element-by-element trace matching),
  state-transition-rate matrix (forward/reversal/turn dwell-time distributions and transition rates,
  compared via a distributional test such as KS, within animal-to-animal spread), behaviour-encoding
  of identified neurons (does the simulated AVA/AVB/RIB/etc. encode the forward/reverse/turn state
  the same way the real recordings show - an encoding-model R^2 comparison, following Atanas's own
  CePNEM-style tuning-curve method), and manifold dimensionality (variance explained by the leading
  PCs of population activity, compared to Kato's reported low-dimensional embedding).
- **NeuroPAL** (Yemini et al. 2021) is not itself a dynamics dataset; it is the identity ground truth
  that lets Randi's and Atanas's traces be assigned to neuron classes in the first place. It is
  scored as part of the observation model (ledger row 23): does the model's simulated marker-colour
  signature per neuron class match the reference NeuroPAL pattern closely enough that a simulated
  imaging pipeline could, in principle, resolve the same identities. This is a feasibility/consistency
  check on the pipeline, not a behavioural prediction, and does not get its own FIT/HELD-OUT entry.

## 18. Mutants and ablations as held-out predictions

Covered in full in section 15 above (entries 96-102) plus the two mutant/ablation-style tests already
in the main corpus (#73 neuron ablation, #42 npr-1). Together these are 9 of the 31 HELD-OUT entries
(29%), consistent with PLAN c.4's framing of mutant predictions as the strongest test available. Two
genes named in the brief are not given their own scoreboard row because the corpus already carries an
equivalent, better-evidenced test for that pathway rather than duplicating it: npr-1 (aggregation, a
receptor not a synthesis/transport gene) is entry #42, and mod-1 (serotonin receptor for the
roaming/dwelling switch, entry #37) is the receptor-side complement to the tph-1 synthesis test (#98).

## 19. Datasets: downloadable now, with sizes

**Already on backhouse** (`~/worm-data/`, see `MANIFEST.md` for full provenance, licence and sha256):

| Dataset | Feeds scoreboard entries | Size | Format | Public / licence |
|---|---|---|---|---|
| cook2019 (Cook 2019 connectome) | all neural-circuit entries | 12 MB | xlsx adjacency matrices | public; Emmons Lab copyright, no stated reuse terms |
| witvliet2021 (8 developmental connectomes) | 76, 77, 78 | 91 MB | JSON (connections/trajectories/annotations) | public; GPL-3.0 (repo licence) |
| cengen (gene expression, partial) | all CeNGEN-derived channel/receptor/mutant entries | 426 MB | CSV/TSV + one Monocle3 object | public; no licence stated |
| peptide_connectome (Beets 2023, Ripoll-Sanchez 2023, Bentley 2016) | 9, 10, 31, 37-42, 65, 96-99 | 1.0 GB | xlsx/csv/zip | public; MIT (repo) / CC BY 4.0 (Bentley) / Beets licence unconfirmed |
| randi2023 (functional atlas) | 74, 96 (unc-31 variant not fetched) | 637 MB | tar.gz/zip/h5 processed exports | public; no licence set on OSF node, GPL-3.0 (companion package) |
| atanas2023 (whole-brain imaging + NeuroPAL labels) | 75 | 714 MB | HDF5 (bz2) + Julia dict | public; CC BY 3.0 US |
| morphologies (OpenWorm CElegansNeuroML) | 2, 91-94 (morphology input) | 121 MB | NeuroML2 + xls/csv | public; no licence stated |
| misc (Bhattacharya 2019 innexin expression) | 8, 90, 101, 102 | 168 KB | docx | not open access; NIH public-access copy |
| ephys (Naudin 2022, AIY/RIM/AFD) | 91, 92, 93 | 36 MB | tab-delimited txt + xlsx | public; CC BY 4.0 |

Total already fetched: 2.5 GB of a 150 GB budget.

**Public, not yet fetched** (next in line for backhouse):

| Dataset | Feeds scoreboard entries | Size | Format | Notes |
|---|---|---|---|---|
| Liu et al. 2018 AWA ephys+Ca imaging | 94 | 809 MB (15 zips; one Ca-imaging file alone is 219 MB) | likely Igor/Clampfit exports, not yet inspected | CC BY 4.0, Mendeley `tngf9w3pgd`; deferred as the harder spiking/Ca-action-potential target |
| Brittin et al. 2021 contactome | 78 | not measured (EM-derived contact tables; likely well under 1 GB) | not inspected this pass | Zenodo 4763083, public |
| Open Worm Movement Database | 1-10, 86 (cross-check) | 14,874 tracking records; size not measured | video/skeleton/feature, via Zenodo community | public |
| Yemini et al. 2013 feature matrices | 86, 87 | ~10,000 worms x 700+ features; size not measured | via paper supplement | public; raw video likely not public, feature matrices likely are |
| Randi 2023 unc-31 variant exports | 96 | up to 1.1 GB per variant (OSF lists several) | tar.gz | public, OSF e2syt, same licence status as the main export |
| Kato et al. 2015 whole-brain imaging | 95 | not located as a standalone small public download this pass | unknown | flagged in `MANIFEST.md`; needs a dedicated search pass |
| Yemini et al. 2021 NeuroPAL data/strain | observation model (row 23), section 17 | not located as a standalone small public download this pass | unknown | strain itself available via CGC; imaging data location not confirmed |
| iCEL1273 metabolic network | 85 | small (gene/reaction list, well under 10 MB expected) | supplementary tables | public, Yilmaz & Walhout 2016 |
| MERGE tissue-resolved model | 84 | not measured, expected small-to-moderate | supplementary tables | public, Mol Syst Biol 2020 |
| 2025 metabolic flux landscape (Perturb-seq + isotope tracing) | 83 | processed tables likely small; raw Perturb-seq reads likely tens of GB on GEO/PRIDE, out of scope per the "under ~10 GB" convention used elsewhere in MANIFEST.md | supplementary tables + GEO/PRIDE raw | public, Nature 2025 |
| Du, Crodelle et al. 2024 BWM model | 79 | not measured, expected small (code/model, not raw ephys) | likely NEURON/code repo | public |
| Nicoletti 2019/2024 figure data (AWC, RMD, AVA, VA5, VB6, VD5) | 80, and the remaining per-class ephys targets beyond #91-93 | code-only repos are small; raw traces must be digitised from paper figures, not downloaded | ModelDB .ode files; GitHub NEURON/Python | public; licence unconfirmed for the 2024 repo (no LICENSE file found) |

## 20. Counts

| Category | FIT | HELD-OUT | DEFERRED | Total |
|---|---|---|---|---|
| Locomotion, gait, motor structure | 9 | 3 | 0 | 12 |
| Mechanosensation, touch, tap-withdrawal | 5 | 2 | 0 | 7 |
| Chemosensation | 8 | 2 | 0 | 10 |
| Thermosensation, nociception, dauer | 4 | 0 | 0 | 4 |
| Feeding and pharynx | 4 | 1 | 0 | 5 |
| Internal states | 4 | 2 | 0 | 6 |
| Egg-laying and defecation | 7 | 4 | 0 | 11 |
| Male mating | 0 | 0 | 7 | 7 |
| Learning and memory | 4 | 1 | 0 | 5 |
| Life history and aging | 3 | 1 | 0 | 4 |
| Sensory misc, connectome, structural | 2 | 4 | 1 | 7 |
| Single-neuron/muscle biophysics, ephys | 3 | 4 | 0 | 7 |
| Metabolism and phenotyping | 2 | 3 | 0 | 5 |
| Whole-brain cross-check | 0 | 1 | 0 | 1 |
| Mutants and ablations (new, #96-102) | 0 | 7 | 0 | 7 |
| **Total** | **61** | **31** (33.7% of the 92 scored) | **8** | **100** |

Layer coverage check (ledger rows 7-23, PLAN.md section a): every row has at least one HELD-OUT
representative above (7: #8,73,74,75,100; 8: #8,73,90-analog,101,102; 9: #38,42,65,96; 10: #44,65,97-99;
11: #26; 12: #67; 13: #34; 14: #50; 15: #46; 16: #81; 17: #26,71; 18: #16,38,65,67; 19: #67; 20: #83,85;
21: #7,67,81; 22: #7,24; 23: #74,75,87,95). Rows 1-6 (inventory, morphology, channel presence/kinetics,
densities, calcium) are covered by the per-class ephys holdouts (#91-93) and the connectome-variability
test (#77).
