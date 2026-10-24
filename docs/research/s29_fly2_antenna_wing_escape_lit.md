# Literature read: antenna mechanics, resting wing angle, GF escape kinematics

Working notes. Files saved in /tmp/fly2n/: b1_gopfertrobert2002.pdf(+.txt), b1_pnas2003.html(+.txt),
b2_riabinina2011.pdf(+.txt), b3_card2008.pdf(+.txt), b3_directional2022.pdf(+.txt), b3_vonreyn2014.html (paywalled, no numbers extracted).

All numbers below were read from the actual article text (pdftotext or HTML-stripped text that I grepped
and read myself), not from a search engine's summary, unless marked "secondary". Where an AI search-engine
summary gave a number I could not independently verify in the source text, I have dropped it rather than
report it.

---

## Topic 1: Antenna (arista/funiculus) mechanics - best frequency f0 and Q

### Measurement A - Göpfert & Robert 2002, J Exp Biol 205:1199-1208, "The mechanical basis of Drosophila audition"
Read level: **full text** (downloaded via Wayback Machine mirror of the JEB PDF, confirmed by pdfinfo
metadata: Title "Auditory mechanics of Drosophila melanogaster", Author "M. C. Göpfert and D. Robert").

- Animals: wild-type *Drosophila melanogaster*, **Oregon-R strain**, reared 22-25°C. For the mechanical
  (laser Doppler vibrometry) experiment, flies were briefly CO2-anaesthetized only to remove wings/legs and
  wax them to a holder; measurements were done at **room temperature 24-26°C** (paper's Methods, "Animals"
  section). The paper does not state whether the fly was still CO2-affected or fully recovered at the moment
  of recording; this is the paper's main "intact/mounted" condition, not their separate "postmortem" condition
  (postmortem is only mentioned later, without quantitative f0/Q given for it in this paper - see Measurement
  in the 2003 PNAS paper for that).
- Stimulus: pseudo-random noise, 100-1000 Hz, free sound field (loudspeaker + near-field pressure-gradient
  microphone calibration). Arista-tip vibration velocity measured by LDV, perpendicular-to-arista orientation.
- Result (text, p.1204, "Arista tip response"): "Examination of four male and four female aristae revealed a
  low inter-individual variability and no apparent sex differences... Individual values of f0 varied between
  405 and 445 Hz (**426±16 Hz; mean ±1 S.D.**). **The quality factor Q ranged between 1.1 and 1.3 (1.2±0.1)**.
  At f0, mechanical sensitivity vvib/vair reached its maximum, ranging between 1.1 and 1.5 (1.3±0.2) for the
  eight aristae examined."
  - n = 8 (4 male, 4 female); forced (driven) mechanical response, not free fluctuation.
  - Read level: full text, direct quote, Fig. 4C/D and p.1204 text.
- Caveat for model use: this paper's own Fig. 7A shows f0 is **intensity-dependent** in the living fly: "f0
  shifted from approximately 360 to 620 Hz with an average increase of 7.3 Hz dB-1" across the stimulus range
  tested. So 426±16 Hz is the f0 at whichever (unstated exact dB) intensity was used for the 8-fly tip-response
  series, not a single fixed biophysical constant. The paper frames the receiver as "a moderately damped simple
  harmonic oscillator" with a non-linear (level-dependent) stiffness.
- No second, independently-measured Q value was found anywhere else in the material I could access (Riabinina
  2011 full text has no Q; the PNAS 2003 paper has no Q; a Nadrowski & Göpfert 2009 review explicitly states no
  Q number). **Q = 1.2±0.1 (n=8) is therefore a single-source value - I could not find an independent second
  measurement of Q to use as a held-out check.**

### Measurement B(1) - Göpfert & Robert 2003, PNAS 100:5514-5519, "Motion generation by Drosophila mechanosensory neurons"
Read level: **full text** (PMC154376, HTML-stripped and grepped myself; confirmed title/authors/journal in the
page metadata).

- Methods: room temperature 22-24°C; flies mounted ventrum-down, wings/legs removed, wax-stabilized (same
  general prep family as the 2002 paper). Sex/age/strain not stated in the visible text.
- **Passive (postmortem) forced-response best frequency: f_R = 809 ± 34 Hz** (n=10 flies). Quote: "the
  mechanics of the receiver became linear when measured postmortem. Responses to different stimulus
  intensities superimposed, with f_Rs clustering around 809 ± 34 Hz (Fig. 1 B and C)."
- **Passive (postmortem) free-fluctuation best frequency: f_R = 792 ± 36 Hz** (n=7). Quote: "the postmortem
  fluctuations of the receiver... exhibited the expected resonant tuning with f_R = 792 ± 36 Hz (n = 7)"
  (from spontaneous-oscillation experiment, Fig. 3F).
- CO2 anaesthesia (reversible) produces the same linearization to ~800 Hz: "linearization at frequencies
  ≈800 Hz also took place when the animals were transiently anesthetized by CO2 (Fig. 2)... reverted back to
  lower frequencies, restoring the initial nonlinearity within ≈80 s."
- **Living (active), forced-response, intensity-dependent best frequency**: shifts from 395 ± 46 Hz (at low
  stimulus particle velocity, 10^-5 m/s) up to 815 ± 37 Hz (at high particle velocity, 10^-3 m/s), average
  slope 10.6 Hz/dB (n=10, Fig. 1 B,C).
- **Living (active), free-fluctuation (spontaneous-oscillation) best frequency: f_R = 207 ± 49 Hz** (n=7,
  Fig. 3A), described as "tuned to fly song frequencies."
- No Q/damping value given anywhere in the visible text.

### Measurement B(2) - Riabinina, Dai, Duke & Albert 2011, Curr Biol 21:658-664, "Active process mediates species-specific tuning of Drosophila ears"
Read level: **full text** (downloaded the real PDF via a Wayback Machine mirror of the Cell Press PDF;
pdftotext confirms running header "Species-Specific Tuning of Drosophila Ears", p.659).

- Method: laser Doppler vibrometry of **free fluctuations** (no forced stimulus) in awake flies and in
  CO2-anaesthetized flies, modeled as a simple harmonic oscillator (same free-fluctuation approach as G&R 2003
  Fig. 3). CO2 is cited (ref [5], i.e. Göpfert & Robert 2003) as reversibly eliminating active feedback.
- **D. melanogaster active (awake) free-fluctuation best frequency: 147 ± 20 Hz** (Fig. 1B top; Table S1,
  "all standard deviations specify inter-individual variation").
- **D. melanogaster passive (CO2-anaesthetized) free-fluctuation best frequency: 789 ± 45 Hz** (Fig. 1B
  bottom; Table S1).
- n and sex not stated in the main-text pages I could read (likely in Supplemental Experimental Procedures /
  Table S1, which I did not retrieve - not found in the archived PDF's visible pages).
- No Q value given.

### Cross-check (what each pair buys you)

**Passive/dead-or-CO2 best frequency** - two independent papers, same broad method family (free-fluctuation
LDV), good quantitative agreement:
- Göpfert & Robert 2003 PNAS: 792±36 Hz (n=7, free fluctuation) / 809±34 Hz (n=10, forced)
- Riabinina et al. 2011 Curr Biol: 789±45 Hz (CO2, free fluctuation, melanogaster)
=> These two can be used as **set-from-one, test-on-other**: ~790-810 Hz, SD ~35-45 Hz. Consistent to within
each other's SD.

**Active/living best frequency (free-fluctuation / low-stimulus limit)** - two independent papers, same rough
range but with a real quantitative gap:
- Göpfert & Robert 2003 PNAS: 207±49 Hz (n=7, spontaneous oscillation)
- Riabinina et al. 2011 Curr Biol: 147±20 Hz (awake, free fluctuation)
=> Same order of magnitude (150-210 Hz) but the two central values differ by ~30%, more than either SD alone
would suggest; treat as a **loose** check, not a tight one. (Göpfert & Robert's forced-response value at their
lowest tested intensity, 395±46 Hz, is higher still - the "active best frequency" is stimulus/condition
dependent and these three numbers are not measuring quite the same thing: spontaneous self-oscillation
frequency vs. forced-response resonance at a given sound level.)

**Q / damping** - only one usable number found: **Q = 1.2±0.1 (n=8, Göpfert & Robert 2002)**, from a forced
response in an intact (not CO2/dead) fly at an unstated moderate stimulus intensity. No second,
independently-measured Q exists in what I could retrieve, so this cannot presently be cross-checked - flag
this gap explicitly if Q is used as a model parameter.

---

## Topic 2: Resting folded wing angle

This came back much weaker than topic 1. Summary of what I found, and what I could not find:

- **No paper gave a directly measured numeric resting (folded) wing angle for wild-type Drosophila
  melanogaster with a stated mean ± SD/SEM and n.** I checked: a JEB review on directional hearing (no wing
  content); Fontaine et al. 2009 J Exp Biol 212:1307 "Wing and body motion during flight initiation..." (full
  text read via a PDF from the Caltech repository - this paper's angle-accuracy numbers, e.g. "stroke amplitude
  and deviation are estimated within 3.3 deg. and 2.1 deg.," are tracker-validation errors, not resting-posture
  measurements; it never reports a baseline/resting wing angle value); several courtship papers (von
  Philipsborn-style wing-angle tracking literature, PMC12952713 "Sequencing of distinct wing behaviors during
  Drosophila courtship," 2026 Curr Biol, full text read via PMC); PLOS ONE "Image Tracking Study on Courtship
  Behavior of Drosophila" (full text attempted via WebFetch).
- What these courtship-tracking papers do give, repeatedly and consistently (read level: full text for
  PMC12952713; secondary/search-snippet for a couple of others making the same statement): an **angle
  convention**, not a measurement - "Wing angles were calculated as the angle between each wing (thorax-to-
  wing-tip vector) and the body axis, with **0° representing wings folded against the body** and 90°
  representing full extension." This is a *definitional* zero point chosen by the trackers, not an
  independently measured resting angle with uncertainty. I could not find the actual measured distribution of
  wing angle during the "stillness"/resting phase in any of these papers' visible text (PMC12952713's "wing
  angle during stillness" is not reported with a number - confirmed by direct query of its full text).
- The only **numeric, method-described** wing-angle value I found for Drosophila is for a **mutant**, not
  wild-type: in the "tilt (tt)" phenotype characterization paper (PMC10183093, full text), live OreR and *tilt*
  males were **photographed** (Leica MZ16F stereomicroscope + Nikon D300S camera, 35 mm culture dish, 80x
  magnification) and the paper states "**the tilt wing is held out at 45° from the body in both the
  dorsal/ventral and anterior/posterior directions**," while "OreR wings are held tight to the body" - described
  only qualitatively, with no numeric angle, no SD, and no n given for the wild-type control. So even here, the
  wild-type baseline itself is not quantified.
- I did not find Fry/Dickinson resting-posture papers or wing-display "scissoring" papers reporting the
  baseline closed-wing angle as a number, despite targeted searches (multiple query variants on wing fold,
  wing overlap angle, abdomen-overlap angle, SLEAP/DeepLabCut resting distributions).

**Bottom line for topic 2: no usable "inside a measured range, source cited" number for the resting wing
angle was found in the time available.** The only concrete, method-backed datum is the 45° tilt-mutant angle
(PMC10183093, photograph-based), which is explicitly an abnormal/mutant posture, not a WT value, and so is not
directly usable for setting a WT body-model parameter; it would at best serve as a photographed-angle sanity
check on the measurement method itself. I recommend treating "resting wing angle" as **not yet in the
measured-literature ledger** rather than filling it with an invented or convention-only ("0° by definition")
number.

---

## Topic 3: Giant-fiber short-mode escape take-off kinematics

### Primary source - Card & Dickinson 2008, J Exp Biol 211:341-353, "Performance trade-offs in the flight initiation of Drosophila"
Read level: **full text** (downloaded the real PDF via a Wayback Machine mirror of the JEB PDF; pdftotext
confirms "G. Card and M. Dickinson" / journal running headers).

- Animals: **3-day-old mated female** *Drosophila melanogaster*, wild-type, "descended from 200 wild-caught
  females" (not a standard inbred lab stock). Reared in incubators at **25°C**, tested at **room temperature
  22-25°C** (Methods).
- Stimulus/preparation: flies tethered by a pipette on the abdomen tip, stimulated with a visually looming
  black disk (falling disk) to elicit escape take-off ("escape" condition, giant-fiber-pathway-mediated per
  the paper's framing, citing Allen et al. 2006 review) vs spontaneous/odor-induced "voluntary" take-offs
  (non-GF pathway). High-speed video, 3 synchronized cameras, **6000 frames/s**.
- **Escape (GF) take-off latency from stimulus onset to lift-off: median 190.67 ms (IQR = 15.29), n = 17**
  flies (Table 1, "Start of stimulus to lift-off"). Flies that responded outside a 0-228 ms window after
  stimulus release were excluded. Note: this is latency to visual escape behavior, not a direct electrical-GF-
  stimulation latency (the paper does not do direct GF electrical stimulation itself; it cites Tanouye & Wyman
  1980 for that - see below).
- **Mesothoracic leg extension duration (start of leg motion to end of extension): escape (GF) median 3.33 ms
  (IQR = 0.46), n = 27**, vs voluntary median 5.50 ms (IQR = 2.00), n = 16 (Table 1; text: "5.5 ms, IQR=2.0 vs
  3.3 ms, IQR=0.46"; difference P<0.001, Kruskal-Wallis).
- **Wing-leg interval** (time from start of wing opening to start of leg extension): escape median **1.00 ms
  (IQR = 2.67)** vs voluntary 34.83 ms (IQR = 45.42) (Table 1, P<0.001). In escapes "wing raising preceded leg
  extension in almost all (96%)" responses, but in 80% of those cases (22/27) the wings never reached full
  extension before the legs kicked, so "most escape jumps occurred with the wings in the closed position" -
  i.e., wings get pulled back against the body during the actual jump, consistent with the short-mode
  phenotype described by von Reyn et al.
- **Leg-to-downstroke interval**: escape median 0.67 ms (IQR = 0.83) vs voluntary 3.33 ms (IQR = 2.33)
  (Table 1, P<0.001). The paper notes this interval is of interest because "a short and fixed latency between
  TTM and DLM activation is a hallmark of the giant fiber pathway," citing **Tanouye & Wyman 1980: 0.44 ± 0.05
  ms delay** between TTM and DLM motor activation upon direct GF electrical stimulation (this is a
  secondary/cited number inside Card & Dickinson 2008's text, not independently re-measured by them - read
  level for the 0.44±0.05 ms figure itself: **secondary**, i.e. quoted from Tanouye & Wyman 1980 as cited in
  Card & Dickinson 2008's Table 1 footnote text).
- Also cited (secondary, from Trimarchi & Schneiderman 1995a, as quoted in Card & Dickinson's text): a wing-
  raising-to-leg-extension interval of "10.5 ± 5.4 ms, mean ± s.d., N = 4" for voluntary take-offs - this
  contradicts/extends their own larger voluntary-takeoff value (34.83 ms median) and the paper explicitly notes
  theirs was "substantially longer and more variable" than this earlier report.
- **Body (center-of-mass) take-off velocity, first 2 ms of flight: escape mean ± SEM = 0.48 ± 0.01 m/s** vs
  voluntary 0.28 ± 0.02 m/s (P<<0.001, ANOVA). Escape speeds "approached the maximum flight speeds observed in
  Drosophila (0.6 m/s)" (cited to David 1979; Budick & Dickinson 2006).
- **Peak vertical center-of-mass acceleration: escape 112 m/s² (IQR = 47.8)** vs voluntary 57.0 m/s²
  (IQR = 35.8) (P<<0.001, Kruskal-Wallis).
- **Peak horizontal center-of-mass acceleration: escape 107 m/s² (IQR = 50.0)** vs voluntary 46.1 m/s²
  (IQR = 28.8) (same test). Ratio of vertical:horizontal peak acceleration ≈1 in both conditions, i.e. roughly
  a 45° launch angle from horizontal.
- Angular kinematics: escape peak pitch velocity 5710 ± 661 deg/s vs voluntary 2370 ± 350 deg/s; escape peak
  roll velocity 10 200 ± 1480 deg/s vs voluntary 2860 ± 1090 deg/s (means ± SEM as per the paper's general
  convention stated in Methods, "mean ± s.e.m."). Roll acceleration "maintained a plateau for nearly 5 ms
  after lift-off."
- Wingbeat frequency of the first 3 strokes after becoming airborne: escape 277 Hz (IQR=11.2) vs voluntary
  261 Hz (IQR=26.6), both "20-30% higher than the 200-220 Hz wing beat frequency measured for steadily
  hovering flies in free flight" (cited to Fry et al. 2005).
- Direct quote giving a simple summary figure for the GF pathway itself (not this paper's own measurement,
  general statement in the Introduction, uncited to a specific number but framing the whole phenomenon):
  "strong visual stimuli... cause a fly to quickly extend its middle legs, propelling itself off the ground in
  **less than 5 ms** without the aid of coordinated wing motion."

### von Reyn et al. 2014, Nat Neurosci 17:962-970, "A spike-timing mechanism for action selection"
**Could not retrieve full text.** This paper is not open access and is not deposited in PMC or Europe PMC
(confirmed via Europe PMC API query on the DOI: `isOpenAccess: N, inEPMC: N, inPMC: N, hasPDF: N`). The Nature
webpage (even via a Wayback Machine snapshot) returned only template/paywall markup with no body text
("authorization: status false", "Hybrid Access"). I could not find an open PDF mirror (ResearchGate, bioRxiv,
Janelia/Card-lab page) within the time budget. **No numbers from this paper are reported here** - do not treat
"short mode"/"long mode" duration splits as sourced from von Reyn et al. 2014 until someone with journal
access (or an institutional proxy) pulls the actual figures; Card & Dickinson 2008 above predates the
short/long-mode terminology and its "escape" category is likely a mix of what von Reyn 2014 later split into
short- and long-mode responses.

### Secondary context - Card lab 2022 preprint on bioRxiv ("Directional invariance in the Drosophila giant fiber escape circuit", Jang, Goodman & von Reyn)
Read level: full text skimmed, but **no quantitative GF/short-mode timing numbers were present** in the
sections I checked - it cites von Reyn et al. 2014 repeatedly for the concept of short-mode vs long-mode
takeoffs and GF-driven leg extension/wing depression, but does not restate the original timing numbers in the
text I retrieved.

### Not retrieved in the time available
- Trimarchi & Schneiderman 1993/1995 (J Exp Biol) direct text - only available to me as quoted inside Card &
  Dickinson 2008 (the "10.5±5.4 ms, N=4" figure above is from this chain, read level **secondary**).
- Zumstein, Forman, Nongthomba, Sparrow & Elliott 2004, J Exp Biol 207:3515, "Distance and force production
  during jumping in wild-type and mutant Drosophila melanogaster" (this is the correct title/citation for the
  "TTM" lead in the brief - the title "Take-off and flight in Drosophila: TTM" does not appear to be this
  paper's actual title). Not opened due to time budget; flagged for a follow-up read.
- Direct GF electrical-stimulation jump kinematics (beyond the single secondary 0.44±0.05 ms TTM-DLM delay
  number) were not retrieved.

---

## Five-line summary

1. Antenna passive/CO2 best frequency: **usable, two independent sources, good agreement** - Göpfert & Robert
   2003 PNAS (792±36 to 809±34 Hz) vs Riabinina et al. 2011 Curr Biol (789±45 Hz); set from one, test on the
   other, expect ~790-810 Hz.
2. Antenna active/living best frequency: **usable but loose, two independent sources, same order of
   magnitude** - Göpfert & Robert 2003 PNAS (207±49 Hz, spontaneous) vs Riabinina et al. 2011 (147±20 Hz,
   awake free-fluctuation); treat the ~150-210 Hz band as the measured range, not a tight point value.
3. Antenna Q/damping: **single-source only** - Göpfert & Robert 2002 JEB, Q=1.2±0.1 (n=8); no independent
   second measurement found, so this cannot presently be cross-checked - flag as a gap if used to set a model
   parameter.
4. Resting folded wing angle: **not usable** - no wild-type measured value with method and error found
   anywhere in the time available; the only numeric, photograph-based value found (45°) is for the *tilt*
   mutant, not wild-type, and is a figure-caption description rather than a quantified measurement with n/SD.
5. GF short-mode escape kinematics: **usable from one well-documented primary source** (Card & Dickinson 2008
   JEB, full text, n=17-27 per measure: ~191 ms stimulus-to-liftoff latency, 3.33 ms leg-extension duration,
   0.48±0.01 m/s take-off speed, ~110 m/s² peak CoM acceleration), but the intended second/cross-check source
   (von Reyn et al. 2014 Nat Neurosci, which named and split "short mode" vs "long mode") is paywalled and not
   in PMC/Europe PMC - I could not pull its numbers, so there is currently only one independent measurement
   for this topic, not two.
