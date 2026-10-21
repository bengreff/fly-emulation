# SEALED — GF→DLM pathway: refractory period, following frequency, 1:1 vs doublet, somatic spike shape

**This file is sealed held-out evidence.** It was written by a literature-research task that was
explicitly instructed not to let these numbers leak into any other document, decision, or model-fitting
step before a pre-registration locks the test. Do not read this file casually while building or tuning
the two-compartment DLMn model (N30 / F-GJ-6) — it exists so that the eventual held-out check is spent
only once. Whoever unseals this should log that event in `docs/HANDOFF.md`'s sealed/held-out register
per the standing rules, with a `date`-stamped entry.

Compiled 2026-10-21.

---

## E1. GF→DLM pathway: paired-pulse refractory period, following frequency, and 1:1 vs. doublet (wild type)

### Source 1 — Ryglewski S, Kadas D, Hutchinson K, Schuetzler N, Vonhoff F, Duch C (2014)
"Dendrites are dispensable for basic motoneuron function but essential for fine tuning of behavior."
*PNAS* 111(50):18049–18054. PMC4273390 / DOI 10.1073/pnas.1416247111.
(Read directly via PMC full text; high confidence on quotes below.)

- **Latency, GF stimulation → DLM muscle potential:** "the delay between giant fiber stimulation and
  muscle potential is 1.85 ± 0.21 ms" (Results text, Fig. 1H). n = 10 animals per group (stated in
  Methods, "Four parameters were measured"). This value "remained unaltered in motoneurons with
  significant dendritic defects" — i.e. it is reported as a control/wild-type baseline against which
  dendrite-ablated neurons are compared. Note: HANDOFF/DECISIONS already record this latency number as
  previously held out for the N30 pre-registration (commit de97887) — it is reproduced here for
  completeness since it occurs in the same figure/paragraph as the refractory-period and
  following-frequency numbers, but it may already be unsealed elsewhere in the project record. Treat
  the refractory-period and following-frequency numbers below (which were NOT previously logged as
  held out) as the newly sealed items from this source.
- **Refractory period (paired-pulse):** Methods state the protocol — "The minimal duration between two
  subsequent GF stimulations that result in two subsequent DLM fiber responses" was measured by
  decreasing the inter-stimulus interval in 0.1-ms increments starting at 6 ms. Figure 1J shows the
  result. The Results text states only that reliability of signal transmission through this circuit "is
  not altered after 90% dendrite removal in motoneurons: refractory period (Fig. 1J) ... remain[s] as in
  controls." **No explicit numeric ms value for the refractory period appears in the Results text itself
  that I could find** — the number (if extractable) is only in the Fig. 1J panel data (bar/plot), which
  I could not read pixel-values from via WebFetch of the HTML. So: a number almost certainly exists (it
  is plotted), but I could not retrieve its specific value in text form.
- **Following frequency (maximum, with % reliability):** Figure 1 legend, verbatim: "the pathway follows
  stimulation frequencies of approximately 130 Hz with 100% reliability (K) and up to 200 Hz with 50%
  reliability (L)." This is given as a control-equivalent value (unaltered after dendrite ablation), so
  it should reflect the wild-type/control GF-DLM following behavior.
- **1:1 vs. doublet:** Results text: "Electrical stimulation of the giant fiber interneuron reliably
  elicits action potentials in the axon of MN5, which in turn are transmitted to the DLM target muscle"
  — phrased as a 1:1 relationship (one GF stimulus → axonal AP → one muscle response), with no mention of
  doublets anywhere in what I read of this paper.
- Methods/animals: reared at 25 °C; flies used 1–2 days post-eclosion; adult; genotype
  C380-GAL4,UAS-mCD8::GFP;;Cha-GAL80 crossed to UAS-Dcr2 (control 1) or w1118 (control 2); recordings
  in situ (adult dissected thorax/CNS), intracellular patch clamp; separately, in-vivo MN5 extracellular
  recording from DLM during restrained flight used a tungsten electrode (100 µm diameter) — this second
  method is for the flight-firing-rate data, not the GF-stimulation data above.

### Source 2 — Fayyazuddin A, Zaheer MA, Hiesinger PR, Bellen HJ (2006)
*PLoS Biol* 4(3):e63. PMC1382016. (Read directly.)

- **1:1 vs. doublet / spike shape:** Results text, describing Figure 5D/5E: "In wild-type animals, when
  we activated the giant fiber at 1 Hz, the action potential generated at the distal PSI-DLMmn synapse
  on the axon appeared small and broad in somatic recordings (Figure 5E). This differed considerably
  from the narrow, large action potential evoked in the soma by current injection (Figure 5D), suggesting
  that the peripherally generated action potential fails to propagate antidromically into the dendrite."
  — this describes **one spike per GF stimulus** (singlet, not doublet) at 1 Hz stimulation, with that
  single spike appearing attenuated/broadened at the soma because it originates on the axon and does not
  fully back-propagate. No doublet is mentioned or shown.
- **Refractory period:** the paper describes (Methods/Results) a third method used to isolate the EPSP:
  "The third was to trigger an action potential by current injection in the MN5 soma just before giant
  fiber activation to force an absolute refractory period at the PSI-DLMmn synapse, causing the spike to
  fail thereby revealing the EPSP." This is a qualitative/methodological description of using the
  refractory period as a tool, not a quantified refractory-period duration. **No ms number found.**
- No EPSC/voltage-clamp recordings were made in this paper (current-clamp only, per what I read).

### Source 3 — Pavlidis P, Tanouye MA (1995)
"Seizures and failures in the giant fiber pathway of Drosophila bang-sensitive paralytic mutants."
*J Neurosci* 15(8):5810–5819. PMC6577637.

- I could only access the **abstract** via WebFetch (repeated attempts at the PMC full-text page
  returned only the abstract-level summary, not full Results/Methods text). The abstract states that
  "Seizure and failure in the GF pathway with a refractory period is common to all six members of the
  bang-sensitive class" and that "Failure occurs at the synapse between a peripherally synapsing
  interneuron (PSI) and the DLMmns, while the DLMmn-DLM neuromuscular junctions remain functional." No
  wild-type-specific numeric refractory-period or following-frequency value was retrievable from the
  abstract. **Full text not accessible to me; a number likely exists in the Results (this paper is
  largely about quantifying exactly this), but I could not retrieve it.**

### Source 4 — Tanouye MA, Wyman RJ (1980)
"Motor outputs of giant nerve fiber in Drosophila." *J Neurophysiol* 44:405–421.

- Not independently read (pre-PMC era paper, paywalled, no accessible full text found). A web-search
  tool's own summary (not a verified quote) asserted: "The giant fiber drove the DLM with very constant
  latencies of 1.3 msec," and separately (possibly conflated with a different paper in the search
  summary) claimed a following-frequency ceiling around 100 Hz and a refractory-period range of
  "7–15 ms for DLMs" vs. "1–4 ms for TTMs." **These numbers are UNVERIFIED — I never saw primary text,
  only an AI search summary, and the summary itself may have blended content from this paper with
  Engel & Wu's or another paper's findings on refractory period. Treat as low-confidence leads only,
  not as confirmed sealed data, until the primary 1980 paper or a reliable secondary citation of it is
  read directly.**

### Source 5 — Engel JE, Wu CF (1992 or later)
Referenced in the task brief as a likely refractory-period source (possibly conflated across several
Engel & Wu papers, e.g. the 1996 *J Neurosci* 16(10):3486–3499 habituation paper, or a *J Comp Physiol A*
1992 paper on membrane-excitability mutations). I was not able to pin down and read a specific Engel &
Wu paper with a confirmed wild-type refractory-period or following-frequency number — what I found was,
again, only an AI search-summary claim (the same "7–15 ms for DLMs" figure appeared in a search summary
attributed loosely to "Engel and Wu," without a clean citation match I could verify). **Unverified —
same caveat as Source 4. Possible that sources 4 and 5 are being conflated by the search engine's own
summarization and actually refer to one underlying number; this needs a direct primary-text read to
resolve.**

### Source 6 — Augustin H et al. (2017)
"Reduced insulin signaling maintains electrical transmission in a neural circuit in aging flies."
*PLoS Biol* 15(5):e2001655.

- Not read directly by me. Quoted (at one remove) inside a computational-model paper (see Source 7
  below) as: young flies show GF-pathway response latencies of "0.93 and 1.44 ms, respectively" for
  TTM and DLM; old flies show "1.22 and 1.85 ms." These are **latency** numbers (GF stimulation → muscle
  depolarization), not refractory period or following frequency, and not independently verified by me
  against the Augustin et al. primary text — only via the secondary citation below.

### Source 7 — computational model paper citing Augustin et al. 2017
*eNeuro* 6(2):ENEURO.0423-18.2019, "A Computational Model of the Escape Response Latency in the Giant
Fiber System of Drosophila melanogaster." (Read directly, partial — main text accessible via WebFetch.)

- Quotes the Augustin et al. 2017 young/old latency numbers above as its empirical calibration target.
- States: "A single action potential (AP) in a GF axon is sufficient to initiate patterned activity in
  jump and flight muscles" — i.e., asserts a 1:1 (not doublet) relationship as the modeling assumption,
  attributed to the general GF-system literature rather than to one specific quantified experiment.
- Does **not** give a refractory period or following-frequency number anywhere I could find in this
  paper (I searched explicitly for both and found neither).

### Source 8 — JoVE methods paper, "Electrophysiological Recordings from the Giant Fiber Pathway of D.
melanogaster" (video/text protocol; likely Allen/Godenschwege-lab authorship, referencing Allen et al.
1999/2006 and Godenschwege et al. 2006 for the underlying numbers). Accessed via PMC2967628 (a JoVE
article mirror).

- States: response latency "≤ 1 ms for TTM" and "≤ 1.6 ms for DLM" (Section 2.3.1) as the acceptance
  criterion for a healthy wild-type prep.
- States: "the ability for both pathways, GF-TTM and GF-DLM, to follow one-to-one when stimuli were
  given at 100Hz" — again a 1:1-at-100Hz statement, used as a prep-quality/healthiness criterion rather
  than as a fully characterized reliability curve.
- Does **not** give a quantified refractory period, nor a following-frequency curve beyond the single
  100 Hz 1:1 checkpoint.
- Explicitly attributes the detailed underlying characterization to "Allen et al., 1999; Allen et al.,
  2006; Godenschwege et al., 2006" — none of which I was able to independently fetch and read for
  further numbers (searches found only secondary mentions, no accessible full text).

### Source 9 — Hummon MB, Costello WJ (1989)
"Giant fiber activation of flight muscles in Drosophila: asynchrony in latency of wing depressor
fibers." *J Neurobiol* 20(6). (Not read directly — only an abstract-level search-engine summary.)

- Summary states the paper reports "a small but distinct inherent difference in latency between two
  sets of DLM fibers in ... two wild-type strains," stable over time, persisting when the motor axon is
  stimulated peripherally — i.e., this paper is about inter-fiber latency asynchrony within the DLM
  (which fiber group fires slightly before another), not about refractory period, following frequency,
  or 1:1-vs-doublet. Relevant as background on DLM fiber heterogeneity, not a direct answer to E1. No
  numeric latency difference value was retrieved.

### Source 10 — Sun Y, Wyman RJ (1997), "Neurons of the Drosophila giant fiber system: I. Dorsal
longitudinal motor neurons." *J Comp Neurol* 387(1):157–166. (Not read directly — search-summary only.)

- Anatomical identification paper: "DLM is comprised of six muscle fibers (named a through f), each
  singly innervated, with the four ventral muscle fibers each innervated by separate motor neurons
  (DLMn c–f), while the two dorsal fibers share an axon (DLMn a/b)" — confirms the DLMn a/b = MN5
  identity used in the model, but contains no refractory-period, following-frequency, or doublet data
  that I could find.

---

## E2. Somatic amplitude/half-width of the axon-initiated ("small and broad") MN5 spike when driven via PSI/GF

### Fayyazuddin et al. 2006, PMC1382016 (same paper as E1 Source 2 above)

This is the only source found describing this specific spike. Full relevant quote (Results, describing
Figure 5D vs. 5E): "In wild-type animals, when we activated the giant fiber at 1 Hz, the action
potential generated at the distal PSI-DLMmn synapse on the axon appeared small and broad in somatic
recordings (Figure 5E). This differed considerably from the narrow, large action potential evoked in
the soma by current injection (Figure 5D), suggesting that the peripherally generated action potential
fails to propagate antidromically into the dendrite."

**No numeric amplitude (mV) or half-width/duration (ms) value for the GF/PSI-driven "small and broad"
spike was found anywhere in the text I could access.** The description is qualitative only
("small and broad" vs. "narrow, large" for the current-injection-evoked spike, which by contrast IS
quantified at 50–60 mV in Figure 5D per the main literature file). If Figure 5E itself contains a
calibrated trace from which amplitude/half-width could be read off a published image, that would require
visually inspecting the figure (not done here — I only read text/figure-legend content via WebFetch,
which does not extract pixel/trace data from images).

No other source (Ryglewski 2012, Ryglewski 2014 PNAS, Herrera-Valdez 2012, or any of the E1 sources
above) was found to report or show a quantified somatic amplitude/half-width for this specific
GF/PSI-driven axon-initiated spike. Ryglewski & Duch 2009 and Ryglewski, Kilo & Duch 2014 (EJN) — both
behind 403 walls, not read — remain unchecked and are the most likely remaining candidates if this
needs to be hunted down further.

---

## Summary table (for the researcher's own tracking — NOT for the final reply to the requester)

| Source | E1 numeric value present in text? | E2 numeric value present in text? |
|---|---|---|
| Ryglewski et al. 2014 PNAS (PMC4273390) | Latency: yes. Refractory period: only in figure, not text. Following frequency: yes (130 Hz/100%, 200 Hz/50%). 1:1: stated qualitatively, yes. | not addressed |
| Fayyazuddin et al. 2006 (PMC1382016) | 1:1 (singlet) stated qualitatively; no refractory-period number | No amplitude/half-width number; qualitative "small and broad" only |
| Pavlidis & Tanouye 1995 (PMC6577637) | Abstract only accessible; number likely exists in body text, not retrieved | not addressed |
| Tanouye & Wyman 1980 | Unverified search-summary numbers only | not addressed |
| Engel & Wu (unclear which paper) | Unverified search-summary numbers only | not addressed |
| Augustin et al. 2017 / eNeuro 2019 model paper | Latency numbers (young/old) via secondary citation; no refractory/following-frequency number | not addressed |
| JoVE/PMC2967628 methods paper | Latency thresholds and a single 100 Hz/1:1 checkpoint; no refractory period, no following-frequency curve | not addressed |
| Hummon & Costello 1989 | Inter-fiber latency asynchrony (different question), no refractory/following/1:1 number | not addressed |
| Sun & Wyman 1997 | Anatomical identity only | not addressed |
