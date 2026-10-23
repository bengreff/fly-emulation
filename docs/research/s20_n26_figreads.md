# N26 figure reads: Kistenpfennig 2012 PRC; Liang/Holy/Taghert 2016 Ca2+ phases

Figures saved under `docs/research/figs/s20_n26/` (source PDF/JPG + crops used for pixel reads).
BLINDING: no phase-ADVANCE magnitude at CT/ZT 18-23 is reported anywhere below (Lamba 2014 not opened).

## Task 1 — Kistenpfennig, Hirsh, Yoshii, Helfrich-Förster 2012, JBR 27(2):117-125
PDF: https://epub.uni-regensburg.de/34459/1/117.full.pdf (saved as `data/raw/papers/kistenpfennig2012.pdf`, not in git)

| Value | Reading | Source |
|---|---|---|
| (a) zero-crossing flank 1 | CT17, **delay** (sign only; magnitude withheld — task spec for 1a asks CT+sign only) | stated in text, Table 1 |
| (a) zero-crossing flank 2 | CT19, **advance** (sign only; magnitude withheld, late-night advance, blinded) | stated in text, Table 1 |
| (a) interpolated zero crossing | **CT ≈ 18.5**, uncertainty ≈ ±0.3 CT-h (linear interp between CT17/CT19 SEM-propagated, plus discretization since points are 2h apart; component magnitudes not disclosed to avoid back-solving the advance value) | derived from Table 1 |
| (b) CT of maximal delay | **CT15** | stated in text, Table 1 |
| (b) magnitude of maximal delay | **-4.05 ± 0.18 h** (SEM, n per Fig.3 ANOVA df ≈ 20/point) — delay, reportable per task rules | stated in text, Table 1 |
| advance-curve peak (CT only, no magnitude) | control curve peaks at **≈ CT21** ("maximal phase advances at approximately CT21", Results) | stated in text |
| (c) pulse duration | 1 h (60 min) | stated in text |
| (c) intensity | 1000 lux = 150 µW/cm² | stated in text (Methods) |
| (c) light source | white LEDs, Lumitronix LED-Technik GmbH (no wavelength spectrum given) | stated in text |
| (c) temperature | 20 °C constant throughout | stated in text |
| (c) genotype | control = *w1118* (Bloomington #6326); cry01 = *w1118;;cry01* | stated in text |
| (c) n per point | not tabulated per CT point; ANOVA control F11,238 implies total N≈250 across 12 points, ≈20/point (derived, approximate) | derived from stated F-stat df |
| (c) shift measurement | offset of evening locomotor activity in DD, anchored PRC: line fit through post-pulse offsets on day 1 of DD extrapolated back vs. unpulsed-control reference phase (59 control / 27 cry01 unpulsed flies for reference); pulses CT1-23 in 2h steps | stated in text (Methods, Fig.1) |
| (d) other genotype, different zero crossing | **cry01 mutant**: advance onset/crossing at **CT21** vs control's CT19 ("the phase advance started later in cry01 mutants at CT21 than in the control flies at CT19") — CT only, no magnitude given | stated in text |

Uncertainty note: all Task-1 numbers above are Table-1/Results text values (exact SEMs given in the paper), not pixel-read from Fig. 3; no figure pixel-calibration was needed since the underlying numbers are tabulated.

## Task 2 — Liang, Holy & Taghert 2016, Science 351:976-981
PMC4836443, DOI 10.1126/science.aad3997. Figure: `liang2016_fig1.jpg` (full), crops `panelG_*.png`, `panelJ_axis.png`.
Condition: *tim>GCaMP6s(,mCherry.NLS)* flies, 6 d prior 12:12 LD entrainment, imaged on **DD1** (first day constant darkness); temperature not stated in accessible text/methods excerpt.

Panel G (clock-face mean-vector phase per fly, n=13 flies total; not every group visible in every fly — per-group n in supp. Table S1, not accessed):

| Group | Peak CT (pixel-read, arrow direction) | Dot scatter range (pixel-read) | Source |
|---|---|---|---|
| s-LNv (M cells) | ≈ CT 22.5–23 | ≈ CT21–1 | figure, Panel G; axis calib: 24 ticks evenly spaced on circle (15°/h), 0/24 at top, 6 right, 12 bottom, 18 left |
| LNd (E cells) | ≈ CT 8 | ≈ CT5–10 | figure, Panel G |
| DN1 | ≈ CT 18.8–19 | ≈ CT17–20 | figure, Panel G |
| DN3 | ≈ CT 18.0–18.3 | ≈ CT14, 17–21 (one outlier ~CT14) | figure, Panel G |
| l-LNv | ≈ CT 5.5–6 | ≈ CT3–7 | figure, Panel G |

Panel J (ΨM,E = phase lag of each group's Ca2+ peak relative to s-LNv/M, hours; bar + SEM, pixel-read against 0–25 h axis, 5 h gridlines):

| Group | ΨM,E (h) | Significance vs Behavior | Source |
|---|---|---|---|
| Behavior (n=47 flies, DD1) | ≈9.5 ± 0.3 | — | figure, Panel J |
| LNd | ≈9.3 ± 0.8 | n.s. | figure, Panel J |
| l-LNv | ≈6.8 ± 0.9 | n.s. | figure, Panel J |
| DN3 | ≈18.8 ± 0.8 | * (p<0.05) | figure, Panel J |
| DN1 | ≈18.8 ± 0.8 | * (p<0.05) | figure, Panel J |

Text-stated qualitative cross-checks (not numeric): "M cells... peaked towards the end of the subjective night, whereas in E cells it peaked towards the end of the subjective day"; "~10 hour phase difference between Ca2+ rhythms in M and E pacemakers" (consistent with the ≈9 h read off Panel G/J above); "Ca2+ activations precede... behavioral outputs by ~4 hours."

Uncertainty note: Panel G/J values are pixel reads off a 150-DPI PMC figure (not vector); estimate ±0.3–0.5 CT-h for arrow directions and ±0.5 h for bar heights/error bars, limited by JPEG resolution and marker size, not a formal calibration-residual fit.
