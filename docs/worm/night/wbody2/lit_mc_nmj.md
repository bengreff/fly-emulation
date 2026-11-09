# Literature check: MC-to-pharyngeal-muscle NMJ and one-EPSP-to-one-AP question

Time box: about 15 minutes, free sources only, no paywall/bot-check bypass. Below, every number is
quoted exactly from the source I actually opened, with the label measured / model / not found.

Sources opened successfully (free, no bypass):
- Steger KA, Shtonda BB, Thacker C, Snutch TP, Avery L (2005) J Exp Biol 208:2191-2203. Full text via the
  free NIH manuscript deposit on PMC: https://pmc.ncbi.nlm.nih.gov/articles/PMC1382270/ (NIHMSID NIHMS7119).
  Note: the publisher page https://journals.biologists.com/jeb/article/208/11/2191/15553/... is behind a
  Cloudflare bot check (confirmed with a direct fetch: it returns a "Just a moment..." challenge page). I
  did not try to get past that. The PMC manuscript copy is the real, free full text and is what all quotes
  below come from.
- Shtonda BB, Avery L (2005) "CCA-1, EGL-19 and EXP-2 currents shape action potentials in the C. elegans
  pharynx", J Exp Biol 208:2177-2190. Full text via PMC: https://pmc.ncbi.nlm.nih.gov/articles/PMC1351090/.
  This one loaded as plain text with no bot check.
- McKay JP, Raizen DM, Gottschalk A, Schafer WR, Avery L (2004) Genetics 166:161-169. PMC page:
  https://pmc.ncbi.nlm.nih.gov/articles/PMC1470703/. Only the abstract is served as plain text; the PDF
  link goes through a proof-of-work bot check ("Preparing to download...", a JS challenge). I did not try
  to solve it. academic.oup.com/genetics/article/166/1/161/6060801 is a hard paywall (abstract only, $43
  for 24h access). So for this paper I only have the abstract, confirmed open.
- Sherman D, Harel D (2024) "Deciphering the underlying mechanisms of the pharyngeal pumping motions in
  Caenorhabditis elegans", PNAS 121(7):e2302660121. Full text via PMC:
  https://pmc.ncbi.nlm.nih.gov/articles/PMC10873627/ (this is the correct PMC ID; PMC11781704, which I was
  initially pointed at, is a different, unrelated paper — Du et al., "Biophysical modeling... of C. elegans
  body-wall muscle cells" — not the pharynx paper. Flagging this since the brief had the wrong PMC ID).
- Raizen DM, Lee RY, Avery L (1995) Genetics 141:1365-1382. Not opened — PMC PDF is behind the same
  proof-of-work bot check as the McKay paper above, which I did not try to bypass, per instructions. I did
  not find an open source quoting its specific numbers in the time available. Reported as "not found" below.

---

## 1. Steger et al. 2005, J Exp Biol 208:2191-2203 (PMC1382270)

(a) Resting potential of pharyngeal muscle — **measured**.
Fig. 7A legend: "Sample intracellular voltage recordings from wild-type worms show that resting potential
is about −73 mV." (Fig. 7A legend, Results/Fig. 7.)
In eat-2 mutants the resting potential is different (see below).
In cca-1 single mutants: "Resting potential in cca-1 single mutants matches that of wild-type worms."
(Fig. 7B legend.)

(b) EPSP amplitude and time course — **measured**.
Table 1 ("Effect of cca-1 on electrical activity in the pharynx"), exact row values quoted from the page:
"Wild type 2.6 8 1450 3.4±0.3 6.7±0.3" and "cca-1(ad1650) 14.4 7 640 1.3±0.1* 26.7±2.3*"
Columns are: I-spikes/100 APs, No. animals, No. APs, E/EPSP height, EPSP to E time (ms).
Text: "In wild-type pharynxes, E-phase spikes are, on average, 3.4 times the size of the EPSPs that precede
them (Table 1). The average time interval between the peaks of the EPSP and E spikes is seven milliseconds
(ms). In cca-1(ad1650) mutant worms, E-phase spikes average 1.3 times the size of their paired EPSPs and the
time between peaks averages 27 ms (Table 1)."
For eat-2 mutants: "When eat-2 function is eliminated, EPSPs are absent from EPG traces and mutant worms
pump slowly (Fig. 3A, Fig. 4E and Fig. 6A)." So no EPSP amplitude/time-course number exists for eat-2 —
the EPSP itself is gone. (eat-2 is also cited: "The same effects are seen in worms whose MC neurons have
been ablated with a laser (Raizen et al., 1995).")
No rise/decay time constants beyond the peak-to-peak latency above were found in the text.

(c) Action potential threshold / depolarization needed to fire — **measured**, indirect.
"Membrane potential in cca-1 mutants consistently stalls at around −30 mV, the potential at which the CCA-1
channel is expected to activate (Shtonda and Avery, 2005)." No separate single "threshold mV" number for
the full muscle action potential (as opposed to the CCA-1 channel's own activation voltage) is stated in
this paper; EGL-19 (L-type) is described as activating "at more-depolarized potentials" than CCA-1, without
a number here (see Shtonda & Avery below for −20 mV).

(d) Current injection protocol in Fig. 4A — **not found as asked**.
Fig. 4A is NOT a current-injection experiment. Quote: "(A) Sample intracellular voltage recordings from
wild-type and cca-1(ad1650) mutant worms. While the depolarization phase of the wild-type action potential
usually rises steeply and steadily from resting potential to a peak, action potentials from cca-1 mutant
worms often display a notch or flattened area early in depolarization." These are passive intracellular
recordings of spontaneous/MC-driven action potentials, not evoked by injected current. I did not find any
current-injection protocol (nA/pA, ms) anywhere in this paper's main text. There is no Fig. 4A current-clamp
stimulus to report — the question's premise (an injected-current Fig. 4A) does not match this paper.

(e) Latency from EPSP onset to action potential, and cca-1 effect — **measured**.
Same Table 1 numbers as in (b): wild type 6.7±0.3 ms EPSP-to-E-spike interval; cca-1(ad1650) 26.7±2.3 ms,
marked "*Significantly different from wild type, P<0.01." That is a roughly 4x slowing of the EPSP-to-AP
latency when cca-1 is removed. (Other genotypes in the same table: unc-17(e245) 12.2±0.7 ms.)

(f) E1/E2 spike amplitudes in EPGs — **not found** (method described, values not located).
Methods text: "The heights of E1 and E2 peaks, the time intervals between them and the log of the ratio of
the E1 and E2 heights were recorded for each of the first 12 action potentials from five cca-1 mutant worms
and eight wild-type worms." This describes the measurement but I could not find the resulting E1/E2 height
numbers reported in the main text (they may be in a supplementary table I did not have time to check).

Extra, confirmed in this paper and directly relevant: eat-2 mutants shift resting potential rather than
losing the ability to fire. Quote: "eat-2 single mutants display a resting potential that is elevated by
about 13 mV over wild-type resting potential (compare Fig. 7A and C, and see Fig. 7E; this is a
statistically significant difference)." So eat-2 resting potential is about −73 + 13 = roughly −60 mV
(this sum is mine, derived from the two measured numbers above, not a quote).

---

## 2. McKay et al. 2004, Genetics 166:161-169 (PMC1470703) — abstract only, free full text blocked

Full text PDF is gated by an NCBI proof-of-work JS challenge; OUP's page is a hard paywall. Only the
abstract was accessible for free. Quoted in full (Abstract, PMC landing page):

"Mutations in eat-2 and eat-18 cause the same defect in C. elegans feeding behavior: the pharynx is unable
to pump rapidly in the presence of food. EAT-2 is a nicotinic acetylcholine receptor subunit that functions
in the pharyngeal muscle. It is localized to the synapse between pharyngeal muscle and the main pharyngeal
excitatory motor neuron MC, and it is required for MC stimulation of pharyngeal muscle. eat-18 encodes a
small protein that has no homology to previously characterized proteins. It has a single transmembrane
domain and a short extracellular region. Allele-specific genetic interactions between eat-2 and eat-18
suggest that EAT-18 interacts physically with the EAT-2 receptor. While eat-2 appears to be required
specifically for MC neurotransmission, eat-18 also appears to be required for the function of other
nicotinic receptors in the pharynx. In eat-18 mutants, the gross localization of EAT-2 at the MC synapse is
normal, suggesting that it is not required for trafficking."

(a) Pumping rate numbers (pumps/min) — **not found** (not in the abstract; full text blocked).
(b) Whether eat-2 lacks the E1 spike / MC transmission — **not found as a number**, but qualitatively
confirmed: the abstract states EAT-2 "is required for MC stimulation of pharyngeal muscle," consistent with
Steger et al.'s statement (above) that eat-2 mutant EPGs lack EPSPs entirely.
(c) Pharmacology (nicotine, levamisole, antagonists) — **not found** (not in the abstract).
(d) Which cells EAT-2 is expressed in — **measured, partial**: abstract says "functions in the pharyngeal
muscle" and "localized to the synapse between pharyngeal muscle and ... MC"; it does not name pm4/pm5 or
marginal cells specifically in the visible text.
(e) EAT-2 receptor current kinetics — **not found** (not in the abstract).

---

## 3. Raizen, Lee, Avery 1995, Genetics 141:1365-1382

**Not found.** The PMC full text is behind the same proof-of-work bot check noted above, which per
instructions I did not try to bypass. In the time available I did not find a free, open source quoting its
specific pumping-rate numbers (the paper is cited by both Steger et al. 2005 and McKay et al. 2004 for the
fact that MC-ablated and eat-2 worms lack EPG I-phase spikes / EPSPs, but neither of those gives Raizen's
own numeric values in the text I could access).

---

## 4. Sherman & Harel 2024, PNAS 121(7):e2302660121 (PMC10873627)

Note on the brief: the PMC ID I was given, PMC11781704, is NOT this paper — it is Du et al. 2025, "Biophysical
modeling and experimental analysis of the dynamics of C. elegans body-wall muscle cells" (PLoS Comp Biol),
a different muscle entirely. The correct Sherman & Harel pharynx paper is PMC10873627. I used that.

What the injected current represents — **model**, quoted:
"AP generation was assumed to initiate by the firing of the MC neurons (3, 11–13), where the MC's
themselves were not modeled, and their firing was modeled as an external electrode current, injected at the
corpus–isthmus border (Fig. 2). No other pharyngeal neurons were modeled (SI Appendix)."
And: "In our model, MC's activity elevated the membrane potential (Vm) from a resting potential of −73 mV
[the PMC text literally renders this as "−73 ms", clearly a typo/OCR artifact for mV, matching Steger et
al.'s measured −73 mV] to about −40 mV (Fig. 5A and SI Appendix, Table S1). This activated the ion channels,
which resulted in the generation of an AP."
So: yes, the injected current is explicitly a stand-in for MC's firing (MC itself was not modeled as a
neuron), injected at the corpus-isthmus border.

Muscle geometry (radius, length, number of nodes/compartments) — **not found in main text**.
The paper states only, qualitatively: "two vectors were used for describing its geometry — an outer radii
vector, R, defining its outer, fixed contour, and an inner radii vector, z, describing the changing contour
of the lumen (SI Appendix, Fig. S20). R was set based on morphological data of an adult C. elegans nematode
(25, SI Appendix, Fig. S1)." Node indices up to at least 3400 are referenced (e.g. "the widest point of the
terminal bulb (node = 3400)"), implying a mesh of at least ~3400+ nodes along the pharynx, but I could not
find an explicit total node count, radius value, or length value in the main-text HTML; these are most
likely in the SI Appendix PDF, which I did not have time to fetch and check within the 15-minute budget. I
also did not find the "40 ms" / "62 µA/cm²" numbers the brief asked about anywhere in the main text — the
only "40 ms" mentions in the main text are about calcium-elevation onset latency after AP onset ("Ca cell
elevation started shortly (~40 ms) after AP onset") and a measured ~40 ms corpus-to-terminal-bulb contraction
delay, not the duration of the injected stimulus current. So: **not found** for the specific 40 ms /
62 µA/cm² figures — they may be in Methods/SI Appendix detail I could not reach in time.

What pumping results from one injected-current event — **model, qualitative only**: the paper describes a
single AP, triggered by one externally-injected-current event, as producing one simulated pump (contraction
of the relevant pharyngeal segment), consistent with corpus and terminal-bulb contraction dynamics discussed
around Fig. 7–9, but I did not find a sentence stating a precise quantitative mapping ("one 40 ms pulse =
X µm of lumen closure" or similar) in the portions of the text I had time to read.

---

## 5. Shtonda & Avery 2005, J Exp Biol 208:2177-2190 (PMC1351090)

Input resistance — **measured**.
Quote: "Electrical parameters of the wild-type pharynx are as follows: input resistance 22.8±5.2 MΩ,
capacitance 362.6±36.8 pF, equilibrium potential for the leakage current −53.6±4.1 mV (N=29)."
(Results section; whole-cell voltage clamp, N=29 wild-type pharynxes, dissected prep — see methods below.)

Capacitance — **measured**, same quote: "capacitance 362.6±36.8 pF."

"Resting potential" in the strict sense — the number given in this paper is the leakage-current equilibrium
potential, −53.6±4.1 mV, which is a related but not identical quantity to the resting potential reported by
Steger et al. (−73 mV, from direct intracellular current-clamp recording). I am flagging the difference
rather than treating them as interchangeable: Shtonda & Avery's number comes from a voltage-clamp fit of the
leak current; Steger et al.'s −73 mV comes from a passive current-clamp reading of resting Vm. Both are
measured, but by different methods and possibly not identical cells/conditions.

Action potential threshold / channel activation — **measured** (abstract + Results):
"We show that CCA-1 exhibits T-type calcium channel properties: activation at −40 mV and rapid
inactivation." (Abstract.) And from Discussion, for L-type EGL-19: "Starting from −20 mV, L-type currents
are activated." These two numbers (−40 mV for CCA-1 onset, −20 mV for EGL-19 onset) bracket the voltage
range over which the full muscle action potential is actually triggered.

Dissection/recording method — **measured**, methods: dissection using "two glass pipettes, the cuticle
covering the pharynx was inverted and torn off... the pharyngeal basement membrane was digested with
enzymes," recorded with "An Axoclamp 2B amplifier... in the cSEVC (continuous single electrode voltage
clamp) recording mode." Also noted: "it is nearly impossible to voltage clamp a cell with a resistance of
20 MΩ and currents of 10–20 nA via a single patch electrode" — consistent with the ~22.8 MΩ input resistance
figure above and giving a sense of the current scale (10-20 nA) seen in this preparation.

---

## Net for the model: numbers to test "does one MC event make one muscle AP"

1. **Pharyngeal muscle resting potential: about −73 mV.** Measured, Steger et al. 2005, Fig. 7A legend,
   PMC1382270. (A related but methodologically different number, −53.6±4.1 mV, is Shtonda & Avery's
   voltage-clamp leak-current equilibrium potential, PMC1351090 Results — not necessarily the same quantity,
   flagged above, don't conflate the two.)

2. **EPSP-to-action-potential latency: 6.7±0.3 ms in wild type, 26.7±2.3 ms in cca-1(ad1650) mutants.**
   Measured, Steger et al. 2005, Table 1, PMC1382270. If the model needs a "does the EPSP reliably turn
   into a spike within X ms" check, wild type is the ~7 ms number; cca-1 loss roughly quadruples it.

3. **E-phase spike / EPSP amplitude ratio: 3.4±0.3 in wild type, 1.3±0.1 in cca-1(ad1650).** Measured,
   Steger et al. 2005, Table 1, PMC1382270. Useful as a check that the model's EPSP is small relative to the
   full spike, and that removing the T-type current collapses that ratio toward 1.

4. **CCA-1 (T-type Ca) channel activates at about −40 mV; EGL-19 (L-type Ca) activates from about −20 mV
   onward; MC transmission in cca-1 mutants stalls at about −30 mV (the voltage CCA-1 is expected to open
   at).** Measured, Shtonda & Avery 2005 (abstract, discussion, PMC1351090) and Steger et al. 2005 (Results,
   PMC1382270). This is the voltage path an EPSP has to climb for a full AP to fire: rest (−73 mV) →
   EAT-2/nicotinic EPSP to about −30 to −40 mV (CCA-1 range) → EGL-19 takes over above about −20 mV → full
   spike.

5. **Pharyngeal muscle whole-cell electrical parameters: input resistance 22.8±5.2 MΩ, capacitance
   362.6±36.8 pF (N=29).** Measured, Shtonda & Avery 2005, Results, PMC1351090. Gives the passive
   RC scale for any model compartment representing pharyngeal muscle.

6. **In the Sherman & Harel 2024 model, MC is not simulated as a neuron at all** — its effect is injected
   directly as an external current at the corpus-isthmus border, driving Vm from −73 mV to about −40 mV to
   trigger the AP (PMC10873627, Results). That matches the −73 mV resting potential and ~−40 mV CCA-1
   threshold from the measured papers above, which is a reasonable independent check that the measured and
   modeled numbers are mutually consistent — but I could not confirm the exact current amplitude/duration
   (the "40 ms, 62 µA/cm²" figures in the brief) or the exact mesh geometry (radius, length, node count) in
   the time available; those are most likely in the paper's SI Appendix, which I did not fetch.

Not usable / not found in the time available, flagged rather than guessed: McKay et al. 2004 pumping rates,
pharmacology and EAT-2 kinetics (full text bot-gated); Raizen et al. 1995 numbers (full text bot-gated);
Steger et al.'s E1/E2 raw spike amplitudes (method described, values not located); Sherman & Harel's exact
injected-current amplitude/duration and mesh geometry numbers (likely in SI Appendix, not fetched).
