# Second-cell-type GABA-B check: literature read

Compiled 2026-10-23 (date confirmed via `date`). Working files in /tmp/fly2n/ (PDFs, extracted .txt via
pdftotext, and cropped figure PNGs used for pixel reads are named n2_/n3_/n7_*). Read levels: "full text"
= I read the article text/figure myself (pdftotext or stripped HTML, or viewed the actual figure image);
"secondary" = abstract/snippet/another paper's citation only. Where a number came from reading pixel
positions on a published figure (axis has no printed number), I say so explicitly and give my own
estimate with an uncertainty, not an invented "exact" value.

---

## Topic 1 (priority): Kenyon cells — GABA-A vs GABA-B share of APL-mediated inhibition

**Source:** Inada K, Tsuchimoto Y, Kazama H (2017). "Origins of Cell-Type-Specific Olfactory Processing in
the Drosophila Mushroom Body Circuit." *Neuron* 95:357–367 (not 95:1393 as in the brief — the paper's own
header gives 357–367, July 19 2017 issue; DOI 10.1016/j.neuron.2017.06.039). Downloaded from the Kazama
lab site (open PDF), full text read (pdftotext + direct figure inspection at 600 dpi).
File: /tmp/fly2n/n7_inada2017.pdf, n7_inada2017.txt.

Conditions throughout: adult female flies, electrophysiology at 3 days post-eclosion, whole-cell patch
clamp from KC somata, ex vivo whole-brain preparation, room temperature (25°C, text states experiments
"conducted at room temperature (25°C)"). Picrotoxin (PTX, Sigma P1675) and CGP54626 (Tocris 1088) used as
GABA-A and GABA-B antagonists respectively. **Concentrations as extracted by pdftotext read "5 mM and 10
mM, respectively"** — this is implausibly high for these antagonists (typical use is low micromolar) and I
suspect a PDF-encoding artifact that dropped a micro-sign (μM read as mM); I could not confirm the correct
unit from the extracted text and did not invent a corrected number. If this value matters, pull it from
the original PDF's embedded font table or contact the authors.

### Qualitative result (full text, not numeric)
- Figure 3F (KC inhibitory offset responses to Mz19-PN-driven feedback via APL): "Inhibitory offset
  responses were significantly suppressed by GABA receptor antagonists (**p<0.01, paired t test, n=10)."
  Both PTX and CGP54626 were applied together here (combined block), so this does not separate a GABA-A
  vs GABA-B share — it only shows GABA-A+GABA-B together account for most (not all) of the offset
  response. Saline mean ≈ −6 mV, PTX&CGP mean ≈ −2 mV (read directly off Figure 3F, y-axis in mV, not a
  normalized/percent value — full text read of the panel, points and error bars visible, no stated
  numeric means in the text itself).
- Figure 4D/4E: GABA receptor antagonists (PTX+CGP together) and optogenetic silencing of APL (Arch) both
  significantly decrease the a'/b' KC "slope" (mV/spike) of inhibition (paired t test, p<0.01 and p<0.05
  respectively; n=7,8,7 and n=6,6,7 for a/b, a'/b', g KCs). Again PTX and CGP were applied together, not
  separately, so no GABA-A/GABA-B split is extractable from this panel either.

### Quantitative GABA-A vs GABA-B split (figure-read, Figure 5C)
This is the one place in the paper where the two drugs were added **sequentially** (PTX alone, then
PTX+CGP on top), which lets GABA-A and GABA-B be separated. Figure 5 legend (full text): "(C) KCs receive
inhibition from APL neurons through both GABA-A and GABA-B receptors (n = 10 KCs)." KCs of all types
pooled, APL activated optogenetically with CsChrimson, IPSP-like response recorded in KC soma; error bars
are SEM (STAR Methods, full text: "All mean values are reported as mean ± SEM").

The panel plots "Normalized response" (0–1 scale, Saline = 1.0 by definition) for three conditions: Saline
→ PTX → PTX&CGP. I measured the three data-point positions by pixel analysis of the 600 dpi figure
(axis top = 1.0 at y=210px, axis bottom = 0 at y=650px, linear scale; marker centers found as the
widest-row-sum y-position within each category's x-band). This is a figure-axis read, not a number stated
in the text — treat it as approximate (my own pixel-position estimate, no vendor-supplied error bound on
the digitization itself, typical reading uncertainty ±0.02–0.03 of the 0–1 scale given marker/line width):

| Condition | Normalized response (read from Fig. 5C) |
|---|---|
| Saline | 1.00 (by definition) |
| + PTX (GABA-A blocked) | ≈ 0.52 |
| + PTX & CGP54626 (GABA-A and GABA-B both blocked) | ≈ 0.29 |

Interpreting by simple subtraction (assuming linear summation, which the paper does not itself state):
- GABA-A-attributable fraction of the control IPSP ≈ 1.00 − 0.52 = **0.48** (48%)
- GABA-B-attributable fraction (the further drop when CGP is added on top of PTX) ≈ 0.52 − 0.29 = **0.23**
  (23%)
- Residual after both blockers ≈ 0.29 (29%) — not abolished, unexplained by this simple model (could be
  incomplete block, a third conductance, or non-linear interaction).
- Restricting to the blockable component only (0.48+0.23=0.71), GABA-B's **share of the GABA-blockable
  inhibition ≈ 0.23/0.71 ≈ 32%**, GABA-A's share ≈ 68%.

This is a genuine second cell type (KC, mushroom body, outside the antennal lobe) with a measured
postsynaptic GABA-B contribution to inhibition, directionally **opposite** in magnitude to Wilson & Laurent
2005's PN result (PN: ~46% GABA-A / ~54% GABA-B by picrotoxin-vs-CGP54626 block, see Topic 2 below for full
figures) — in KCs the GABA-A share looks larger and GABA-B share smaller. Caveat: my number is a pixel
read of a bar/line graph with no printed axis ticks beyond 0 and 1, not a number stated anywhere in the
paper's text or tables, and it conflates "share of total response" with "share of drug-blockable response"
depending on how you normalize; different choices of denominator change the percentage split substantially
(23% of total vs 32% of blockable). I recommend treating this as "GABA-B contributes a measurable, smaller
than GABA-A, but nontrivial fraction of APL→KC inhibition" rather than pinning a single precise percentage.

### Other leads checked for Topic 1
- Liu & Davis 2009 Nat Neurosci (Rdl in MB), Lin et al. 2014 Nat Neurosci (APL, sparse coding), Prisco et
  al. 2021 eLife (APL-KC), Amin et al. 2020: **not opened** — ran out of budget after the Inada 2017 figure
  work; these are plausible leads for a GABA-A-only (Rdl) story but I have no evidence either way on a
  GABA-B split from them. Flag for a follow-up pass if a second independent KC number is wanted.
- Dahdal et al. 2010 Neuron (LNv GABA-B-R2, circadian clock neurons): **not opened** this session (time
  budget). This is a plausible non-AL, non-MB cell type with GABA-B involvement worth checking next, but I
  have no pharmacology-split number from it to report — don't infer one.

---

## Topic 2: decay time constant / duration of a GABA-B-mediated IPSP or IPSC

I could not find a stated numeric decay tau (ms or s) for a GABA-B IPSP/IPSC anywhere in the papers I
opened — only qualitative language ("slower kinetics", "briefer duration", "more transient") plus two
time-course figures I read directly. No full-text number exists in these papers for this quantity as far
as I found; what follows are figure reads, clearly marked.

### Wilson & Laurent 2005, J Neurosci 25:9069–9079 ("Role of GABAergic Inhibition in Shaping Odor-Evoked
Spatiotemporal Patterns in the Drosophila Antennal Lobe"). Full text read (open PDF via UCSD course
mirror). File: /tmp/fly2n/n2_wilsonlaurent2005.pdf / .txt.

This is the source paper for the 46%/54% split named in the prompt — confirmed in the actual text (full
text read): "picrotoxin blocked less than one-half (46 ± 5%) of the GABA-gated hyperpolarization in PNs
(n = 14)" (p. 9072). Related numbers, all full text, all from brief (4–7 ms) microiontophoretic GABA
pulses onto the antennal lobe neuropil, whole-cell current clamp, adult flies (sex/age not stated in the
excerpt I pulled), room temperature, nicotinic blocker D-tubocurarine (50 μM) present:
- Picrotoxin (250 μM) blocked 98 ± 3% of the GABA hyperpolarization in LNs (n=6) — LNs have no GABA-B
  component (matches the brief's background).
- CGP54626 (50 μM) blocked 97 ± 2% of the picrotoxin-resistant (GABA-B) component in PNs (n=5), and had no
  effect in LNs (101 ± 6% of control, n=5).
- Text states explicitly (full text, no number given): "different kinetics of GABA-A- and GABA-B-mediated
  currents (Fig. 2C3). The slower kinetics of GABA-B receptors will tend to bias GABA-B control toward the
  later portions of the response... they may see a relatively slower profile of GABA rise and decay than
  that seen by GABA-A receptors." Figure 2C3 shows subtracted traces (picrotoxin-sensitive component vs
  CGP54626-sensitive component) that would let a tau be measured, but **I did not extract pixel values from
  this trace** (ran out of budget on this figure; it is a subtracted-trace plot without a clean % or mV
  axis zero-crossing landmark the way Inada's Fig 5C had, so a reliable read would need more time than I
  had left). No numeric decay constant is given in the main text or in what I could search of the
  reference list; the paper directs readers to "supplemental Fig. 3" at jneurosci.org for additional PTX
  dose-response detail (not retrieved this session).

### Olsen & Wilson 2008, Nature 452:956–960 ("Lateral presynaptic inhibition mediates gain control in an
olfactory circuit"). **Presynaptic** GABA-B (on ORN axon terminals), not postsynaptic — label accordingly.
PMC full text + two figure images read directly. File: /tmp/fly2n/n3_olsenwilson2008.txt,
n3_olsenwilson_fig3.jpg, n3_olsenwilson_fig4.jpg (PMC2824883).

Conditions: whole-cell voltage-clamp recording of ORN-evoked EPSCs in PNs, GABA delivered by brief
iontophoretic pulse into the antennal lobe neuropil (marked by "*" in the figures), ex vivo Drosophila
brain; pharmacology CGP54626 (GABA-B antagonist, "CGP") vs genetic removal of presynaptic GABA-B signaling
by ORN-specific pertussis toxin expression ("PCT", a selective Gi/Go inhibitor that blocks GABA-B
signal transduction presynaptically) vs control ("normal ORNs" / "no antagonists").

No decay tau is stated in the text in ms or s. Text (full text, qualitative only): "In these flies [PCT in
ORNs], GABA still inhibited ORN-PN EPSCs, but now this inhibition had a briefer duration than in wild-type
flies (Fig. 4a,b)... this inhibition was completely resistant to the GABA-B antagonist and completely
blocked by the GABA-A antagonist... This demonstrates that GABA-B receptors inhibit ORN-PN synapses at a
purely presynaptic locus." Figure 3: "A GABA-B receptor antagonist blocked the late phase of this
inhibition, but had only a modest effect on the early phase... The late phase of inhibition evidently
involves only GABA-B receptors."

I read Figure 4b directly (EPSC amplitude, % of baseline, vs time in seconds after the GABA pulse;
n=11 cells for pertussis-toxin-in-ORNs, i.e. GABA-A-only recovery; n=13 for normal ORNs, i.e. GABA-A+
GABA-B recovery, reproduced from Fig. 3f; mean ± SEM, error bars on the plot). This has printed axis
numbers (0, 1, 2 s on x; 0, 50, 100 % on y), so the read is more trustworthy than the Inada case, though I
am still estimating curve positions by eye/pixel rather than quoting stated numbers:
- Both curves fall together to a common trough of roughly 5–10% of baseline by about t ≈ 0.4 s after the
  GABA pulse (GABA-A dominates the fast onset in both conditions, consistent with the Wilson & Laurent
  2005 "GABA-A shapes the early phase" finding).
- GABA-A-only recovery (pertussis-toxin-in-ORNs curve): reaches ~50% of baseline by t ≈ 1.0 s, and is back
  to ~95–100% of baseline by about t ≈ 1.4–1.5 s.
- Full GABA-A+GABA-B recovery (normal-ORNs curve): reaches ~50% of baseline later, around t ≈ 1.5–1.6 s,
  and is still only at ~75–78% of baseline at the last point plotted (t ≈ 2.3–2.4 s) — recovery is not
  complete within the recorded window.
- So the GABA-B component's contribution to total inhibition duration, by this figure read, is roughly
  **an extra ~1 second or more** of suppression beyond what GABA-A alone produces (comparing time-to-full-
  recovery: ~1.4 s GABA-A-only vs >2.4 s, not yet resolved, with GABA-B intact). This is presynaptic
  inhibition of ORN output, not a postsynaptic IPSP/IPSC decay tau — label it "presynaptic, figure-read,
  approximate" if used.
- Figure 3 also states (full text) that "both the GABA-A and GABA-B components of EPSC inhibition are
  associated with an increase in the paired-pulse ratio (Supplementary Fig. 7)" — I could not retrieve
  Supplementary Fig. 7 (PMC blocks supplementary PDF downloads behind a proof-of-work JS challenge I could
  not solve with curl in this sandbox); the actual PPR numbers from that figure are not in this report.

### Other Topic-2 leads checked
- Root et al. 2008, Neuron 59:311–321 ("A presynaptic gain control mechanism fine-tunes olfactory
  behavior"), PMC2539065: full text read via WebFetch (PMC HTML; PDF blocked by the same proof-of-work
  wall). No decay/duration/kinetic numbers found anywhere in the paper by my own follow-up grep of a
  locally stripped copy of the Root 2008-adjacent search; WebFetch's own read confirms: "no explicit
  numeric values for time constants, decay kinetics, or durations... present in relative-change/percent-
  suppression terms only." Treat this sub-finding as **secondary** (WebFetch summary, not my own full-text
  grep — I did not manage to download Root 2008's own PDF to verify directly).
- Nagel, Hong & Wilson 2015, Nat Neurosci 18:56–65, PMC4289142: full text read (PMC HTML stripped and
  grepped). GABA is mentioned 11 times but always with CGP54626+picrotoxin applied together as a combined
  blocker to remove "all inhibition" for a different purpose (characterizing PN frequency response); no
  GABA-B-specific kinetic number, no paired-pulse ratio in this paper either (grepped for "paired-pulse",
  zero hits).
- Dahdal et al. 2010 Neuron (LNv GABA-B-R2) and Enell et al. 2007: **not opened**, time budget.

---

## Topic 3: Kazama & Wilson 2008 / 2009 — ORN→PN paired-pulse ratio and unitary EPSC/EPSP

### Kazama H, Wilson RI (2008). "Homeostatic Matching and Nonlinear Amplification at Identified Central
Synapses." *Neuron* 58:401–413. PMC2429849, full text read (PMC HTML, stripped and grepped directly — not
just a WebFetch summary; I independently confirmed every number below by searching the stripped text
myself). File: /tmp/fly2n/n3_kazama2008.html / .txt.

Conditions (full text, Methods): adult female flies, 2–7 days post-eclosion, whole-cell patch clamp from
PN somata, ex vivo brain, voltage-clamp command potential −65 mV for EPSC recordings, current-clamp
(K+-based internal) for EPSP recordings; antennal nerve stimulated with a brief (50 μs) current pulse via
suction electrode; external saline 1.5 mM CaCl2 (exact Mg2+ not re-confirmed in my excerpt); no explicit
bath temperature stated in the text I searched (not found — likely room temperature per lab convention,
but I did not find the sentence that says so, so don't label it measured).

- **Unitary EPSC amplitude**: "minimal stimulation of the antennal nerve at 0.033 Hz evoked an average
  uEPSC measuring 29.0 ± 2.6 pA (n = 45) in antennal PNs" (full text, confirmed verbatim in the stripped
  HTML).
- **Unitary EPSP amplitude**: "Averaged across PNs, uEPSP amplitude was 6.19 ± 0.45 mV (n = 23)" (full
  text, confirmed verbatim).
- **Paired-pulse ratio: NOT reported in this paper.** I grepped the full stripped text for "paired-pulse",
  "ratio", "ms" context, ANOVA etc. and found no classic two-pulse PPR protocol at fixed ISIs (20/50/100 ms)
  anywhere. Instead, the paper characterizes **short-term depression during repetitive trains** at various
  frequencies mimicking natural ORN spike trains (7, 20, 50 Hz; Figure 8), reporting that strong/fast
  trains rapidly depress uEPSC amplitude and that this depression is presynaptic in origin (judged from a
  1/CV² vs mean-amplitude correlation, Pearson r=0.79, p<10⁻⁴, n=6 cells, Fig. 8G) — but the actual percent
  depression per stimulus is plotted only in Figure 8F, which I did not pixel-read (time budget). If a
  depression-magnitude number is wanted from this paper, it would need to come from a figure read of
  Fig. 8F/8D–G, which I have not done.

### Kazama H, Wilson RI (2009). "Origins of correlated activity in an olfactory circuit." *Nat Neurosci*
12:1136–1144. PMC2751859, full text read (same method). File: /tmp/fly2n/n3_kazama2009.html / .txt. Grepped
for "paired-pulse": zero hits. This paper is about spike-train correlation between sibling ORNs/PNs, not
synaptic PPR — it is not a source for the PPR number either, contrary to how it might read from the title
alone.

### Nagel, Hong & Wilson 2015 (checked per the brief's suggestion as a possible independent PPR source):
grepped full text, zero hits for "paired-pulse". Not a source for PPR either.

**Net result for Topic 3**: I could not find a stated ORN→PN paired-pulse ratio value (at 20/50/100 ms or
any other ISI) in any of the four papers checked. The only place a paired-pulse ratio is even mentioned in
anything I read this session is Olsen & Wilson 2008's statement that GABA-A and GABA-B presynaptic
inhibition each *increase* the paired-pulse ratio at the ORN-PN synapse (Supplementary Fig. 7, numbers not
retrieved — see Topic 2). The unitary EPSC (29.0 ± 2.6 pA, n=45) and unitary EPSP (6.19 ± 0.45 mV, n=23)
amplitudes from Kazama & Wilson 2008 are solid, full-text-confirmed numbers and are usable as-is.

---

## 5-line summary

1. **Usable, inside a measured range, source cited**: KC GABA-A/GABA-B split, Inada et al. 2017 Fig. 5C
   (figure-read, ≈48% GABA-A / ≈23% GABA-B of total control response, or ≈68%/32% of the drug-blockable
   component, n=10 KCs) — a genuine second, non-AL cell type with a measured postsynaptic GABA-B share.
2. **Usable, full text**: PN GABA-A/GABA-B split from Wilson & Laurent 2005 itself, confirmed verbatim
   (46 ± 5% PTX-sensitive, n=14; 97 ± 2% of the PTX-resistant component blocked by CGP54626, n=5) — this is
   the calibration anchor the model was already built on, not new, but now independently re-verified from
   primary text rather than taken on faith.
2b. **Usable but presynaptic, figure-read**: Olsen & Wilson 2008 Fig. 4b gives an approximate ~1 s-or-more
   extension of ORN-terminal GABA suppression attributable to GABA-B beyond GABA-A alone (n=11 vs n=13,
   mean±SEM visible on the plotted points) — no fitted tau, but a defensible order-of-magnitude duration.
3. **Usable, full text, solid**: Kazama & Wilson 2008 unitary EPSC (29.0 ± 2.6 pA, n=45) and unitary EPSP
   (6.19 ± 0.45 mV, n=23) at the ORN→PN synapse — directly usable as a held-out physiological scale check,
   independent of anything used to set the GABA-B kinetics.
4. **Not found despite checking the named leads**: no stated numeric GABA-B IPSP/IPSC decay time constant
   anywhere (only qualitative "slower"/"briefer" language plus the one figure read above); no ORN→PN
   paired-pulse ratio in either Kazama & Wilson paper or in Nagel/Hong/Wilson 2015 — don't use a PPR number
   from these three, and don't invent one.
5. **Independent held-out check**: items 1 and 2b are the closest things to a true second, independent
   cell-type check on the model's GABA-B fraction/kinetics (KC postsynaptic share, ORN-terminal
   presynaptic duration) since neither was used to fit the PN-calibrated GABA-B parameters; item 3 (uEPSC/
   uEPSP) is independent evidence for amplitude scale, not for the GABA-B split, and should not be
   conflated with a GABA-B check. Treat the Inada 2017 percentage and the Olsen/Wilson duration as
   approximate, figure-derived numbers requiring a wider error bar than a text-stated value would carry.
