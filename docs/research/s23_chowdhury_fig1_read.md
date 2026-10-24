# s23 blind read of Chowdhury et al. 2023 Fig. 1 (24 October 2026)

Registered fallback of DECISIONS 23 Oct 00:53: the Dryad raw data (doi:10.5061/dryad.qnk98sfpp) needs a login or a
bot check, which was not circumvented, so the score uses this figure read with its read uncertainty added. Read after
the predictions were locked (DECISIONS 23 Oct 23:52, commit c492fb0). Scored in DECISIONS 24 Oct 00:15 and F-S23-6
with `scripts/probes/s23_chowdhury_score.py`.

- Reader: one Sonnet subagent, told the registered quantities and nothing of the predictions. Pixel reads with
  PIL/numpy on the full-resolution figure, tick-calibrated per panel.
- Figure: `data/raw/chowdhury2023/elife-91355-fig1.jpg` (git-ignored raw data), from
  https://cdn.elifesciences.org/articles/91355/elife-91355-fig1-v2.jpg, downloaded 23 Oct 23:54, 2495 x 2608 px,
  sha256 8e696f21b7d18a1ebc96c5594962a4eb684ec6fba56d6ec1cb4c8ee9910d2a96.
- Supplementary file 1: `data/raw/chowdhury2023/elife-91355-supp1.docx`, sha256
  b3184def8d19fe9d1918ce6b984011c825a5f05350b18ef1a48c77d3d7b4c63e.
- Text: `data/raw/chowdhury2023/PMC10642965_fullText.xml` (pinned 23 Oct 00:52).

The reader's report follows unedited apart from typography.

## 1. Text quotes bearing on Figure 1 numbers

No paragraph in the Results, Methods, or Figure 1 caption states a numeric mean, SEM, SD, or rebound value in minutes. The only Figure-1-specific numbers in the text are test statistics, p-values, and sample sizes. Exact quotes:

- **Figure 1 caption (fig1 element):** "A significant increase in sleep was observed for the 20 s trigger, but the 220 s trigger failed to show such increases when compared with undisturbed controls (*Kruskal-Wallis critical value* = 40.43, df = 2, p=1.66 × 10⁻⁹, followed by Bonferroni corrections for pairwise comparisons)." [Panel C]
- Caption, Panel F: "(*Kruskal-Wallis critical value* = 24.59, df = 2, p=4.5 × 10⁻⁶ …)"
- Caption, Panel I: "(*Kruskal-Wallis critical value* = 23.63, df = 2, p=7.41 × 10⁻⁶ …)"
- Caption, Panel J: "20 s trigger: *Kruskal-Wallis critical value* = 13.71, df = 2, p=0.0011 …; 220 s trigger: *Kruskal-Wallis critical value* = 1.96, df = 2, p=0.37 …"
- Caption, Panel K: "ANOVA *F₂,₂₅₀*=3.93, p=0.02."
- **Caption, n's:** "6 hr SD control n=44, sleep-deprived₂₀ s n=62, sleep-deprived₂₂₀ s n=57; 12 hr SD control n=32, sleep-deprived₂₀ s n=64, sleep-deprived₂₂₀ s n=64; 24 hr SD control n=64, sleep-deprived₂₀ s n=32, sleep-deprived₂₂₀ s n=64, sleep-deprived₁₂₀ s n=64; *<0.05 and NS (not significant)."
- Results text (two-way ANOVA definition relevant to Panel K): "we compared the sleep rebound produced by 24 hr of sleep deprivation with stimulation frequencies of 20 s, 120 s, and 220 s using a two-way ANOVA and found that there was a significant interaction effect of treatment × trigger frequency on the amount of sleep rebound (total sleep post-deprivation minus total sleep pre-deprivation)."
- Results text, Panel J statement used as a cross-check below: "the 6 hr deprivation condition, which produced the least amount of sleep loss displayed significantly higher rebound sleep compared to the 12 hr and 24 hr deprivation conditions."
- Methods, Statistical analysis section: no plotting convention stated for Figure 1 specifically (other figures are explicitly described as "mean ± SEM," e.g., Figure 1-figure supplement 1: "Plots are means ± SEM"; Figure 1 itself is never described this way, it is a box-and-whisker plot, confirmed visually, see below).

**No day-2 or day-3 rebound values appear anywhere in the Figure 1 text or caption.** All of panels C, F, I, J, K describe "sleep rebound" or "the 24 hours post-deprivation window" / "first recovery day", i.e., day 1 only. Panel L's x-axis (ZT 00→24/00, then 00→24 again) likewise shows only the deprivation day plus **one** post-deprivation day, not three.

## 2. What is actually plotted

- **Panels C, F, I**: box-and-whisker plots (no mean marker, no explicit SEM/CI) of per-fly "Sleep rebound (minutes)" for three groups (Ctrl, 20 s, 220 s), each at one deprivation duration (6, 12, 24 h respectively). Box = IQR (Q1–Q3), thick black band = median, dashed whiskers = range (likely 1.5×IQR or min/max, not specified), letters a/b = Bonferroni-corrected pairwise significance groups.
- **Panel J**: same box-plot style, split into left (20 s trigger) and right (220 s trigger) sub-panels, x-axis = deprivation duration (6H/12H/24H), y = "Sleep rebound (minutes)."
- **Panel K**: point-range plot ("Sleep rebound (mins)" vs "Trigger interval (sec)" categorical: 20, 120, 220), two series, red (dashed, sleep-deprived/focal) and black (dashed, undisturbed control), each point with a vertical error bar (cap-ended), connected across trigger levels with dashed lines. This is **not** the control-normalized quantity in C/F/I/J; per the two-way-ANOVA text it is raw (post-deprivation sleep − pre-deprivation sleep) plotted separately for treated and control flies. Marker size and symmetric appearance are consistent with mean ± SEM, but this is not stated in caption text for panel K specifically (other supplementary figures in the paper are captioned "mean ± SEM"), so this is an inference, not a quote.
- **Panel L**: continuous time course of cumulative "% Sleep lost/recovered" (mean ± error bars, by inspection) vs ZT, for 20 s (black), 120 s (blue), 220 s (red) triggers, 24-h deprivation only. Two dashed horizontal reference lines (human and fly published recovery %, per caption) are present. This is a percentage, not minutes, and the paper gives no minute value for total sleep lost during deprivation in Figure 1, so it cannot be defensibly converted to minutes.

## 3. Pixel calibration and readings

Method: PIL/numpy on the full-resolution JPG (2495×2608 px). For each panel, y-axis tick rows were located by finding short dark tick marks adjacent to the axis line; a linear fit (slope, intercept) converts row→minutes. Box edges/median and whisker caps were located as rows where a horizontal run of dark pixels spans ~70% of the box width (Q1/Q3/median) or ~50% of a narrower window centered on the box (whisker caps). All crops saved under `/tmp/chow_fig1/`.

### Table (Priority a–c; Priority d is qualitative only, see caveats)

| Panel | Arm (duration, trigger) | Day | What is plotted | Group | Value read (min) | Spread read (min) | Type of spread | Read uncertainty (min) | n | Pixel evidence (ticks → value row) |
|---|---|---|---|---|---|---|---|---|---|---|
| C | 6 h,, | 1 (only day shown) | box plot, per-fly post−pre sleep change | Ctrl | median 59.2 | Q1 −3.4, Q3 95.6; whiskers −138.8/217.2 | box = IQR, whiskers | ±2.9 (box/median); ±2.9 (whiskers) | 44 | ticks rows 168.5=400,237=300,306=200,374.5=100,443=0,512=−100; median row 402.5 |
| C | 6 h, 20 s | 1 | " | 20 s | median 181.5 | Q1 97.1, Q3 252.2; whiskers −73.2/474.2 | " | ±2.9 | 62 | median row 318.5 |
| C | 6 h, 220 s | 1 | " | 220 s | median 68.0 | Q1 11.9, Q3 116.8; whiskers −143.9/254.3 | " | ±2.9 | 57 | median row 396.5 |
| F | 12 h,, | 1 | box plot | Ctrl | median 29.6 | Q1 −11.7, Q3 92.9; whiskers −82.8/225.4 | box = IQR, whiskers | ±2.4 | 32 | ticks 711=400…1122=−100; median row 1015.5 |
| F | 12 h, 20 s | 1 | " | 20 s | median 143.9 | Q1 67.9, Q3 219.3; whiskers −60.3/399.2 | " | ±2.4 | 64 | median row 921.5 |
| F | 12 h, 220 s | 1 | " | 220 s | median 79.5 | Q1 23.0, Q3 131.8; whiskers −116.8/229.0 | " | ±2.4 | 64 | median row 974.5 |
| I | 24 h,, | 1 | box plot | Ctrl | median 58.2 | Q1 11.4, Q3 107.1; whiskers −46.2/225.5 | box = IQR, whiskers | ±2.2 | 64 | ticks 1335=400…1703=0; median row 1649.5 |
| I | 24 h, 20 s | 1 | " | 20 s | median 195.7 | Q1 149.5, Q3 275.5; whiskers 1.6/389.7 | " | ±2.2 | 32 | median row 1523 (confirmed by direct visual zoom, see caveats) |
| I | 24 h, 220 s | 1 | " | 220 s | median 87.5 | Q1 3.3, Q3 188.0; whiskers −67.4/344.6 | " | ±2.2 | 64 | median row 1622.5 |
| J-left | 6 h, 20 s | 1 | box plot, by duration | 6H | median 193.5 | Q1 128.6, Q3 278.9; whiskers −72.8/474.2 | box = IQR, whiskers | ±2.5 | 62 | ticks 1965=500…2446=−100; median row 2210.5 |
| J-left | 12 h, 20 s | 1 | " | 12H | median 128.6 | Q1 78.7, Q3 219.7; whiskers −14.8/370.6 | " | ±2.5 | 64 | median row 2262.5 |
| J-left | 24 h, 20 s | 1 | " | 24H | median 101.2 | Q1 66.9, Q3 141.1; whiskers 7.0/179.8 | " | ±2.5 | 32 | median row 2284.5 |
| J-right | 6 h, 220 s | 1 | box plot, by duration | 6H | median 67.4 | Q1 2.5, Q3 119.8; whiskers −154.2/254.0 | box = IQR, whiskers | ±2.5 | 57 | ticks 1965=500…2445.5=−100; median row 2311.5 |
| J-right | 12 h, 220 s | 1 | " | 12H | median 90.5 | Q1 23.7, Q3 136.1; whiskers −117.3/229.1 | " | ±2.5 | 64 | median row 2293 |
| J-right | 24 h, 220 s | 1 | " | 24H | median 88.0 | Q1 3.7, Q3 188.5; whiskers −67.4/345.2 | " | ±2.5 | 64 | median row 2295 |
| K | 24 h, 20 s | 1 | point + error bar, raw post−pre (not control-subtracted) | deprived (red) | mean(?) 213.1 | 141.8–284.0 | likely SEM (unconfirmed) | ±5 (marker), ±2 (caps) | 32 (deprived)/64 (ctrl, inferred) | ticks 1959.5=400…2481.5=−100; marker row 2154.5 |
| K | 24 h, 20 s | 1 | " | control (black) | mean(?) 49.8 | −21.0–121.2 | " | ±5/±2 | 64 (inferred) | marker row 2325 |
| K | 24 h, 120 s | 1 | " | deprived (red) | mean(?) 90.5 | 17.3–159.0 | " | ±5/±2 | 64 | marker row 2282.5 |
| K | 24 h, 120 s | 1 | " | control (black) | mean(?) 46.0 | −25.8–116.9 | " | ±5/±2 | 64 (inferred) | marker row 2329 |
| K | 24 h, 220 s | 1 | " | deprived (red) | mean(?) 108.3 | 40.3–182.0 | " | ±5/±2 | 64 | marker row 2264 |
| K | 24 h, 220 s | 1 | " | control (black) | mean(?) 100.1 | 32.6–174.8 | " | ±5/±2 | 64 (inferred) | marker row 2272.5 |

Days 2 and 3: **not shown** for any arm in Figure 1, only a single post-deprivation day ("first recovery day" / "24 hr post-deprivation window") is plotted in C, F, I, J, K, and L.

## 4. n per arm (from caption, verbatim)

- 6 h SD: control n=44, sleep-deprived₂₀s n=62, sleep-deprived₂₂₀s n=57
- 12 h SD: control n=32, sleep-deprived₂₀s n=64, sleep-deprived₂₂₀s n=64
- 24 h SD: control n=64, sleep-deprived₂₀s n=32, sleep-deprived₂₂₀s n=64, sleep-deprived₁₂₀s n=64
- Panel K's n's are not stated separately in the caption; I have assumed they equal the 24 h SD n's above (consistent with K being the 24 h, three-trigger comparison), but this is inferred, not quoted.

## 5. Panel L (qualitative only, priority (d), lowest priority, percentages not minutes)

Y-axis "% Sleep lost/recovered," one continuous curve per trigger (20 s black, 120 s blue, 220 s red) from start of deprivation through end of the single post-deprivation day. Two dashed horizontal reference lines are present, labeled by icon (human figure, fly figure) per caption as "Previously measured *Drosophila* (Huber et al., 2004) and human sleep … recovery amounts." By eye against the labeled axis (0, −20, −40, −60, −80, −100), the upper (human) dashed line sits at approximately **−61%** and the lower (fly) dashed line at approximately **−85%** (both read by eye only, uncertainty ±3–5%, I was not able to get a clean automated tick calibration for this panel's left axis within the time available, so these two numbers are weaker than the boxed-plot numbers above and should be treated as rough). By the end of the single post-day shown, the 20 s (black) trace has recovered to roughly **0 to +10%** (i.e., slightly above pre-deprivation baseline), while the 120 s (blue) and 220 s (red) traces plateau around **−90 to −93%**, consistent with the caption statement that "flies recover very little of total sleep lost." No panel in Figure 1 gives a direct minutes value for sleep occurring during the deprivation window itself (residual/debt sleep), only the time-course panels (A, B, D, E, G, H) show per-60-min sleep amounts during deprivation, and I did not quantify these precisely given the priority ordering.

## 6. Caveats

- **No numeric mean/SEM/SD values are stated anywhere in the article text for Figure 1.** Everything above is a pixel read of the figure image, not a reported number.
- **Box-plot type is inferred, not captioned.** Figure 1's caption never uses the words "box plot," "mean," or "SEM" for panels C/F/I/J/K; I inferred box-and-whisker from the rendered shape (median band thicker than box border, dashed whiskers with end caps) and visual cross-checking.
- **Whisker ends are of unknown statistical definition** (could be min/max or 1.5×IQR); not stated in caption or methods.
- **Panel K's error-bar type (SEM vs SD vs CI) is not stated in the caption** for Figure 1; I assumed SEM by analogy with other figures in the same paper (e.g., Fig. 1-figure supplement 1, "Plots are means ± SEM"), but this is an inference, flagged as uncertain.
- **Important internal inconsistency found and worth flagging explicitly**: Panel I's 20 s/24 h box shows median ≈195.7 min, but Panel J-left's 24H/20 s box (nominally the same condition, 24 h deprivation, 20 s trigger, day-1 rebound) shows median ≈101.2 min, a ~95-min discrepancy. I re-verified both readings independently with direct high-zoom pixel crops (not just automated detection) and both box locations are real, correctly calibrated, and visually confirmed against their own panels' tick marks (I 20 s median aligns almost exactly with that panel's "200" tick; J-left 24H median aligns with that panel's "100" tick). By contrast, the 220 s-trigger values **do** agree closely between the matching panels (C 220s median 68.0 vs J-right 6H median 67.4; I 220s median 87.5 vs J-right 24H median 88.0), which validates the reading method. So the 20 s/24 h discrepancy between Panels I and J appears to be a genuine feature of the published figure (possibly different underlying analysis/pooling between the two panels), not a measurement error on my part, I report both numbers rather than reconciling them.
- The ordering implied by Panel I/C/F alone (24H median 195.7 > 6H median 181.5 > 12H median 143.9) does not match the text's explicit claim that "the 6 hr deprivation condition … displayed significantly higher rebound sleep compared to the 12 hr and 24 hr deprivation conditions," whereas Panel J's own ordering (6H 193.5 > 12H 128.6 > 24H 101.2) does match the text. This supports treating Panel J (not Panel I) as the figure's intended within-trigger duration comparison, but I am not able to independently resolve why Panel I's 24 h/20 s box differs from Panel J's.
- Marker/line overlap in Panel K (especially at the 220 s point, where red and black series nearly coincide) makes the black-series mean/error-bar reads at 220 s the least reliable in that panel.
- Panel L's left-axis calibration could not be pinned down with the automated method in the time available; its two numeric dashed-line values (≈−61%, ≈−85%) are eyeball estimates only and carry larger uncertainty than the box-plot numbers.
- No survival times, food intake, or neuron firing rate data were encountered or reported (per instructions, none would have been reported regardless).
