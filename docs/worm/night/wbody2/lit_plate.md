# Literature search: C. elegans experimental-plate quantities

Search date 2026-11-09. Budget: ~45-50 min via NCBI E-utilities (PMC) and Europe PMC. Full text of each
source quoted below was fetched and read with curl/efetch or the Europe PMC XML and checked by hand. No
numbers are reported that I did not read myself in the body text (not abstract-only) unless marked "secondary".

## Summary table

| # | Quantity | Value found | Label | Source |
|---|---|---|---|---|
| 1 | OP50 lawn: seed volume -> spot diameter | 40 uL -> 11.2 mm diameter (derived: radius 5.6 mm) | measured | Madirolas et al. 2023, Commun Biol, PMC10425387 |
| 1b | OP50 lawn: seed volume (no diameter given) | 40 uL on 60 mm plate | measured | Flavell et al. 2013, Cell, PMC3614513 |
| 2 | OP50 lawn OD600 used experimentally | OD 0.5 (behaviour) and OD 1 (biomass calibration) | measured | Madirolas et al. 2023, Commun Biol, PMC10425387 |
| 3 | Lawn border ratio / rim width | not found (openly) | not found | see below; Gray et al. 2004 Nature is paywalled |
| 4 | O2 inside OP50 lawn, quantitative % | not found (openly); qualitative confirmation only | secondary / not found | Chang et al. 2006, PLoS Biol, PMC1540710, citing Gray 2004 Nature and Rogers 2006 Curr Biol (both paywalled) |
| 5 | CO2 inside OP50 lawn | not found | not found | see below |
| 6 | Gentle-touch eyelash force | saturating threshold ~2 uN (half-max <1 uN in a 0.5-5 uN sweep); actual human-delivered force on real assay median 26 uN, mean 61 uN | measured | Petzold et al. 2013, Integr Biol, PMC3701114 (threshold); Nekimken et al. 2017, PLoS ONE, PMC5438190 (applied force) |
| 7 | Tap force/acceleration | not found in force units; solenoid drive reported as 70 ms, 24 V DC pulse | not found (as force); measured (as drive parameters) | e.g. PMC6054533 (Ardiel/Rankin-style tap protocol, following Swierczek et al. 2011) |
| 8 | Nose-touch force | not found | not found | see below |

---

## 1. OP50 lawn size (seed volume and resulting spot diameter/radius)

**Found, measured, matches geometry well.**

Madirolas G, Al-Asmar A, Gaouar L, Marie-Louise L, Garza-Enriquez A, Rodriguez-Rada V, et al. "Caenorhabditis
elegans foraging patterns follow a simple rule of thumb." Communications Biology, 2023. PMC10425387 (open
access).

Methods section, verbatim quote:

> "In all cases, we used 40 μL drops, which spread to a diameter of 11.2 mm on average."

This is for bacterial food patches pipetted onto NGM foraging plates (35-150 mm diameter dishes used across
their assays), i.e. the same geometry as our model (OP50/bacterial lawn on standard NGM agar, not liquid
culture, not microfluidics).

Derived: radius = 11.2 mm / 2 = **5.6 mm** (derived from the quoted diameter). This lands almost exactly on
our model's guessed radius of 5 mm (range 2-15 mm), for a 40 uL seed volume.

Same paper also gives maintenance-plate seeding, a different (larger, saturating) protocol:

> "in 100mm-diameter Petri dishes seeded with 200 μL of a saturated culture of E. coli OP50 bacteria (grown
> overnight on LB at 22 °C)"

No diameter is given for this 200 uL maintenance lawn (it is meant to cover most of a 100 mm dish, not a
discrete spot), so no radius can be derived from it.

A second, independent measured data point for seed volume (no diameter reported):

Flavell SW, Pokala N, Macosko EZ, Albrecht DR, Larsch J, Bargmann CI. "Serotonin and the neuropeptide PDF
initiate and extend opposing behavioral states in C. elegans." Cell, 2013. PMC3614513 (open access).

Methods, verbatim quote:

> "Assay plates (60 mm diameter) were seeded with 40 µl OP50 E. coli and grown overnight at 37°C to produce
> a thin bacterial lawn."

This confirms 40 uL as a standard single-worm-assay seed volume on a 60 mm NGM plate, consistent with the
Madirolas value, but this paper does not state the resulting spot diameter, so I can't independently
cross-check the 11.2 mm number from it.

## 2. OP50 lawn density (OD600 of culture seeded; bacterial density in the lawn)

**Partially found.** Madirolas et al. 2023 (PMC10425387, same paper as above) is the only source I found
that reports both an OD600 value actually used for lawns and a method for converting OD to cell density.

Verbatim quotes:

> "Our experiment took place at OD = 0.5 (black dashed line), where DA1885 is about 10 times more attractive
> than CR266 (circles)."

> "We prepared cultures at OD = 0.5 for both strains..."

> "a Biomass density for each strain at OD = 1 (measured in grams of dry weight, gDW, per liter)... b Number
> of cells per microliter at OD = 1 for each strain..." (figure legend)

> "We determined the CFU density as follows. After determining the OD of the bacterial culture, we performed
> 10-fold serial dilutions in M9 worm buffer... and plated four 10-microliter drops of each dilution..."

This directly brackets our model's OD guess (OD 1, range 0.1-10): the paper's own experiments run at OD 0.5,
and their calibration curve (biomass, cells/uL) is referenced to OD 1. I could not extract the actual
cells/uL or cells/cm^2 numbers from the figure (the data lives in a figure/table that didn't come through in
the plain-text strip of the XML, and checking the figure image was outside the time budget), so the absolute
density number itself is **not found** even though the OD values used (0.5, 1) are **measured** and quoted
above. No thickness-in-um measurement was found for any paper in the time available.

Geometry: this matches our model closely — real OP50 (and related E. coli strains) on real NGM agar, in the
context of foraging/feeding assays, not liquid culture.

## 3. Lawn border (thickness/density ratio of edge vs interior, rim width)

**Not found.** Gray et al. 2004 Nature (the paper you flagged as the usual citation, "Oxygen sensation and
social feeding mediated by a C. elegans guanylate cyclase homologue") is not open access and has no PMC
record (PMID 15220933, isOpenAccess: N, no PMC id in Europe PMC). I could not get its full text through
NCBI efetch (no PMC id to fetch) or Europe PMC.

Queries tried: "bacterial lawn border thickness C. elegans rim Gray navigation" (Europe PMC) — returned only
conference abstract books, no relevant primary paper. "OP50 lawn density/edge/rim" variants did not surface a
paper that measured or imaged the lawn border quantitatively. I did not find any other paper (free full text)
that measured a border-to-interior thickness or density ratio, or a rim width in mm/um, for an OP50 lawn.
This quantity stays guessed; I have no better source than what the model already cites.

## 4. O2 inside/at an OP50 lawn (measured, vs 21% ambient)

**Not found as a direct open quantitative measurement.** The two papers that would have the number are both
paywalled:

- Gray JM, Karow DS, Lu H, Chang AJ, Chang JS, Ellis RE, Marletta MA, Bargmann CI. "Oxygen sensation and
  social feeding mediated by a C. elegans guanylate cyclase homologue." Nature 430:317-322, 2004. PMID
  15220933. No PMC id, isOpenAccess: N. Could not fetch full text.
- Rogers C, Persson A, Cheung B, de Bono M. "Behavioral motifs and neural pathways coordinating O2 responses
  and aggregation in C. elegans." Curr Biol 16:649-659, 2006. isOpenAccess: N, no PMC id in Europe PMC. Could
  not fetch full text.

What I did find and can quote (open access), as a **secondary**, qualitative-only confirmation that O2 is
measurably depleted in/around bacterial lawns and aggregates, citing the above two papers as its primary
sources:

Chang AJ, Chronis N, Karow DS, Marletta MA, Bargmann CI. "A distributed chemosensory circuit for oxygen
preference in C. elegans." PLoS Biology, 2006. PMC1540710 (open access).

Verbatim quote, Discussion section:

> "C. elegans consumes oxygen, so oxygen levels within an aggregate of C. elegans are lower than those in the
> surrounding bacterial lawn ([17]; M. Peliti, personal communication)."

Reference [17] in that paper is Rogers et al. 2006 (above, paywalled) — so this is a secondary citation of a
primary source I could not open. No percentage value (e.g. "~10% inside the lawn") is given anywhere in the
Chang et al. 2006 text I read; it is qualitative only ("lower than... surrounding... lawn"). I did not find
any other open paper with a microsensor or stated-percent O2 measurement inside an OP50 lawn specifically (as
opposed to inside a worm aggregate, which is a related but distinct geometry — a cluster of worms sitting in
one place, versus the O2 drawdown from the bacterial lawn itself).

Geometry note: even if the Gray/Rogers numbers had been reachable, their measurements were made with
O2-sensing circuitry/behaviour assays on normal NGM plates with OP50/HB101 lawns, which does match our
geometry; it is the aggregate-vs-ambient comparison, not necessarily a plain lawn-vs-ambient comparison, that
the open text above speaks to.

## 5. CO2 inside an OP50 lawn (check only)

**Not found.** I did not locate any open, full-text paper with a direct CO2 measurement inside an OP50 lawn
in the time available. I did not find a secondary mention either. This is consistent with the task's framing
that this is "no number; a check only" — I have nothing to add.

## 6. Gentle-touch eyelash force (uN)

**Found, measured, two complementary sources.** This is the best-covered quantity in this search.

### 6a. The saturating/threshold force (primary, MEMS force-clamp, not plate geometry)

Petzold BC, Park SJ, Mazzochette EA, Goodman MB, Pruitt BL. "MEMS-based force-clamp analysis of the role of
body stiffness in C. elegans touch sensation." Integrative Biology (Camb), 5(6):853-864, 2013. PMC3701114
(open access, NIH manuscript).

Verbatim quote, Results section:

> "Across a population of animals stimulated with force pulses between 0.5 and 5 μN, we observed a
> half-maximal response force (F1/2) of less than 1 μN in the resting state."

Geometry: **does not match our plate geometry.** This is a MEMS microfluidic force-clamp device that
immobilizes the worm on-chip and applies calibrated force pulses directly; it is not a freely-moving worm on
an NGM plate touched with a hair. It is, however, the primary source for the actual force-response curve
(the touch assay's "2 uN" figure below is this paper's data, read off Fig. 5C by later authors).

### 6b. The actual classical hair-touch assay, on a real plate (measured, matches geometry)

Nekimken AL, Mazzochette EA, Goodman MB, Pruitt BL. "Forces applied during classical touch assays for
Caenorhabditis elegans." PLoS ONE 12(5):e0178080, 2017. PMC5438190 (open access).

Verbatim quotes:

> "The mean (61 μN) and median forces (26 μN) were more than ten times higher than the 2-μN force known to
> saturate the probability of evoking a reversal in adult C. elegans."

> "Our results indicate that both expert and novice human volunteers deliver forces that are consistently
> higher than the 2-μN force known to saturate the probability of a touch response in C. elegans [14]."
> (reference [14] is Petzold et al. 2013, above)

> "...delivered forces greater than 0.5 μN and less than 1.1 mN (see Methods for details)."

> "the median force from all trials was 26 μN... the mean force was 61 μN."

Geometry: **matches our geometry directly** — this paper used real experimenters touching real, freely
moving worms on real NGM plates with a real eyebrow hair, and measured the force with a calibrated
microcantilever standing in for the worm. So:

- The force needed to reliably evoke a response (saturating threshold, F1/2 <1 uN, "about 2 uN" as commonly
  cited) sits right at our model's guessed value of 2 uN.
- The force an actual experimenter delivers in the classical assay is substantially higher (median 26 uN,
  mean 61 uN) — i.e. real experimenters overshoot the minimum threshold by roughly an order of magnitude
  (overshoot ratio, derived: 26/2 ≈ 13x at the median, 61/2 ≈ 30x at the mean). This is useful context: 2 uN
  is the right number for "minimum to reliably evoke a response," but if you want "what a real hand-applied
  stimulus actually delivers," 26-61 uN is the better figure, which is still within our model's stated range
  (0.1-10 uN) only at its low end and actually exceeds the top of our range (10 uN) for the hand-delivered
  force. Worth flagging: our range's upper bound of 10 uN may be too low for what real touch-assay
  experimenters deliver, even though it comfortably covers the behavioural threshold.

## 7. Plate tap force / acceleration (tap-habituation tapper)

**Not found in force units.** I found the mechanical description of the modern tap device, but it is
specified by its electrical drive, not a calibrated force or acceleration in N/uN/g.

[Ardiel-style tap protocol, following Swierczek et al. 2011's Multi-Worm Tracker tapper] — PMC6054533
("Temporal processing and context dependency in Caenorhabditis elegans response to mechanosensation", 2018,
open access), Methods section, verbatim quote:

> "Taps were delivered to the side of 9 cm plates containing the animals by means of a solenoid, following a
> method similar to that described by Swierczek et al. (2011). An electric solenoid tapper (Small Push-Pull
> Solenoid, Adafruit) was driven with a 70 ms, 24 V, DC pulse under Labview control via a LabJack DAQ and a
> solid-state relay."

This is on a real 9 cm NGM plate (matches geometry), but the stimulus is characterized by drive voltage and
pulse duration (70 ms, 24 V), not by a measured force or acceleration delivered to the plate/worm. I could
not reach Swierczek AB, Giles AC, Rankin CH "Rapid phenotypic-change habituation..." / the original
Multi-Worm Tracker paper (Swierczek NA, Giles AC, Rankin CH, Kerr RA, Nat Methods 2011) to see whether it
quantifies the tap force; it did not surface as an open full-text item in PMC or Europe PMC search within the
time budget. The original Rankin, Beck & Chiba 1990 description (Behav Brain Res) of the mechanical tapper
was not checked for a force value either, for the same reason (not found open in the time available).

So: for this quantity, the field's actual reported "calibration" is an electrical drive specification, not a
force in any unit. I cannot give you a verified N/uN/mN value for tap force from primary literature within
the time spent. This should stay guessed, with a note that the literature's own convention is to report
solenoid drive parameters rather than calibrated force.

## 8. Nose-touch force (hair stimulus to the nose)

**Not found.** I did not find an open, full-text paper that reports a calibrated force value (in uN or any
other force unit) for the nose-touch assay specifically (as opposed to the body/gentle-touch assay covered
in #6). Searches tried: "nose touch C. elegans calibrated force glass probe microN" (Europe PMC) — no
relevant hits; the classical nose-touch papers (Kaplan & Horvitz 1993 PNAS; Colbert, Smith & Bargmann 1997 J
Neurosci) describe the stimulus as a fine hair/platinum wire touched to the nose but, as far as I could check
in the time available, do not report it in force units, and I did not manage to pull their full text within
budget to confirm this one way or the other. I'd treat this as an open gap rather than a confirmed "no
primary measurement exists" — a longer follow-up search of Kaplan & Horvitz 1993 and Colbert et al. 1997
directly (and the Goodman-lab MEMS papers already found for #6, which may have a nose-touch analogue I didn't
check for) would be the next place to look.

---

## Other notes

- WormBook chapters (wormbook.org) were not reachable: the site returns a Cloudflare/reCAPTCHA challenge page
  to curl regardless of user-agent, both at the main domain and via NCBI Bookshelf (https://www.ncbi.nlm.nih.gov/books/NBK235860/,
  the "Assaying mechanosensation" chapter by Chalfie, Hart, Rankin & Goodman 2014) which also served a
  reCAPTCHA challenge page instead of content. The NCBI PMC record for the same chapter (PMC4448936) explicitly
  states "The publisher of this article does not allow downloading of the full text in XML form," confirming
  it is not programmatically retrievable through efetch either. This chapter would very likely have been the
  best single source for #6/#7/#8 (it is the field's own methods review) but I could not open it.
- Gray et al. 2004 Nature and Rogers et al. 2006 Curr Biol (the two most likely primary sources for #4) are
  both paywalled with no PMC record, so they were genuinely unreachable, not just hard to find.
