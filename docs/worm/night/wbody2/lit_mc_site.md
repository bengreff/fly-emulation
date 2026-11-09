# MC motor neuron: synapse site, EPSP/E-spike latency, EAT-2 kinetics

Lit lookup only. Free web sources, no subagents. Date of lookup: 2026-11-09.

Access note up front: the two oldest primary sources (Raizen, Lee & Avery 1995, Genetics 141:1365;
McKay et al. 2004, Genetics 166:161) exist on PubMed Central only as scanned PDFs. The PMC PDF
endpoint for both is gated by a proof-of-work/CAPTCHA challenge that curl and the fetch tool could
not solve, and the OUP Genetics page for McKay 2004 is paywalled. I could only reach their abstracts,
not the full text. This is marked below wherever it matters. The WormBook pharynx electrophysiology
chapter (NBK19665) and the "Feeding" chapter of C. elegans II (NBK20143) on NCBI Bookshelf were also
blocked by an NCBI reCAPTCHA page and could not be opened.

## 1. Anatomy: where MC's synapses are, and onto what

**Primary source (Albertson & Thomson 1976) is not directly reachable as full text here.** Everything
below is WormAtlas text that paraphrases or quotes Albertson & Thomson 1976; I read these WormAtlas
pages through a text-extraction proxy (r.jina.ai) because the wormatlas.org TLS certificate could not
be verified by the fetch tool directly. Treat these as secondary (WormAtlas full text, not abstracts).

- Source: WormAtlas, MC neuron page.
  URL: https://www.wormatlas.org/neurons/Individual%20Neurons/MCmainframe.htm
  Opened: full text (via proxy).
  Quote: "Their most prominent connections are gap junctions to M2 and they synapse strongly on the
  mc2 (Albertson and Thomson, 1976)."
  Quote: "On the dorsal side these processes send a branch to the outside edge of the pharynx under
  the marginal cell 2 (mc2) of the opposite side."
  Quote (unpublished, flagged by WormAtlas itself as not from Albertson & Thomson): "MC's also
  synapse onto pm4 (L. Avery pers. comm.)."
  So: WormAtlas's own citation of Albertson & Thomson 1976 says MC's chemical synaptic output is onto
  mc2 marginal cells. A separate claim, sourced only to a personal communication from L. Avery (not
  a publication), says MC also synapses onto pm4 muscle directly. I could not find a published source
  for the pm4 claim.

- Source: WormAtlas, Albertson 1976 summary page (describes the 1976 Phil Trans paper).
  URL: https://www.wormatlas.org/albertson_1976/Albertson_1976.html
  Opened: full text (via proxy).
  Quote: "...send a branch to the outside edge of the pharynx under the marginal cell 2 of the
  opposite side," then "...continue to run posteriorly under the ventral marginal cell, terminating
  at the very anterior of the isthmus." So MC's process ends right at the metacorpus-isthmus boundary,
  where it also synapses onto mc2.
  Quote: "The marginal cell neurones have free subcuticular endings between muscles m3 and m4."
  (Caveat: likely means the MC neurons, since MC = "marginal cell neuron," but the page does not spell
  this out, and I could not get the actual Albertson & Thomson text to confirm.)

- Source: WormAtlas Pharynx Atlas, pm5DL muscle cell page.
  URL: https://www.wormatlas.org/pharynxatlas/pharynx4pm5DL.html
  Opened: full text (via proxy).
  Quote: "The six pm5 nuclei belong to three muscle cells, each of which runs the length of the
  isthmus," and are "separated from each other by the mc2 marginal cells." So mc2 sits in the isthmus,
  between the three pm5 muscle columns, not pm4. Consistent with MC's mc2 synapse sitting at the
  anterior isthmus (metacorpus-isthmus boundary) rather than inside the metacorpus proper.

- Search-snippet-only (page fetch failed; not independently verified), paraphrasing a WormAtlas
  pharynx overview: pm1-4 and mc1 make up the corpus; pm5 and mc2 make up the isthmus; pm6-8 and mc3
  make up the terminal bulb; the three mc2 cells run the isthmus in ventral, left-subdorsal and
  right-subdorsal sectors. I could not confirm which of mc2DL, mc2DR, mc2V (Cook et al. 2019 naming)
  individually receives MC's synapse in anything I could open, only that MC synapses onto "mc2" as a
  class per the Albertson & Thomson citation above.

- Source: Cook, Jarrell et al. (connectome of the C. elegans pharynx paper, hosted on PMC).
  URL: https://pmc.ncbi.nlm.nih.gov/articles/PMC7601127
  Opened: full text (direct fetch worked, no proxy needed).
  Quote: "The MC neuron...synapses solely onto marginal cells."
  This is the clearest explicit statement found that MC's synaptic output is onto marginal cells, not
  onto muscle directly (contradicting, or at least not supporting, the pm4 personal-communication claim
  above). It also states MC "has unexposed sensors near the sieve" (its own sensory role), separate
  from the output-synapse question.

- Raizen, Lee & Avery 1995 (Genetics 141:1365, PMC1206873,
  https://pmc.ncbi.nlm.nih.gov/articles/PMC1206873): only the abstract was reachable (full text PDF
  blocked by PMC's bot-challenge). Opened: abstract only. Quote: MC "transmits excitatory postsynaptic
  potentials, suggesting that MC acts as a neurogenic pacemaker for pharyngeal pumping." No anatomical
  synapse-site detail in the part I could read.

- McKay, Raizen, Gottschalk, Schafer & Avery 2004 (Genetics 166:161, PMC1470703,
  https://pmc.ncbi.nlm.nih.gov/articles/PMC1470703/; OUP page paywalled): only the abstract was
  reachable. Opened: abstract only. Quote: EAT-2 "is localized to the synapse between pharyngeal
  muscle and the main pharyngeal excitatory motor neuron MC." This names muscle, not marginal cells,
  as the postsynaptic partner, in tension with the Cook et al. "solely onto marginal cells" quote
  above. Could not reach Results/Discussion to see if they address that tension.

**Bottom line on Q1:** Sources disagree at the level of exact wording. WormAtlas's citation of
Albertson & Thomson 1976, and Cook et al.'s connectome paper, both say MC's chemical synapses are onto
mc2 marginal cells, anatomically at the anterior isthmus / metacorpus-isthmus boundary (between the
pm5 muscle columns). McKay et al. 2004's abstract calls the same synapse "between pharyngeal muscle
and... MC," and an unpublished (personal communication) WormAtlas note adds a direct MC-to-pm4
synapse. I could not resolve this discrepancy with the material I could open; it most likely needs the
actual Albertson & Thomson 1976 paper or the McKay 2004 full text, neither of which I could reach.

## 2. Steger, Shtonda, Thacker, Snutch & Avery 2005, J Exp Biol 208:2191 (PMC1382270)

Source: https://pmc.ncbi.nlm.nih.gov/articles/PMC1382270
Opened: full text (direct fetch succeeded; cross-checked with a second, independent fetch through the
proxy, both gave the same numbers).

- Wild type EPSP-to-E-spike latency: 6.7 +/- 0.3 ms, **n = 8 animals, 1450 action potentials total**
  (Table 1).
- cca-1(ad1650) mutant: 26.7 +/- 2.3 ms, **n = 7 animals, 640 action potentials total** (Table 1).
- Quoted table-legend language (as extracted): "The E/EPSP height column shows the average ratio
  between the height of the E-phase spike and the height of the EPSP spike (mean +/- s.e.m.). The
  average interval between the peaks of the E-phase and EPSP spikes is shown in ms (mean +/- s.e.m.)."
- E/EPSP amplitude ratio (not an absolute mV amplitude): wild type, E-phase spikes are "on average, 3.4
  times the size of the EPSPs that precede them" (n = 8); in cca-1(ad1650), E-phase spikes "average 1.3
  times the size of their paired EPSPs" (n = 7).
- No absolute EPSP amplitude in mV was found anywhere in the paper (per both fetches).
- No EPSP rise time or decay time course (ms) was found, including for a background with no action
  potential. I looked specifically for this and did not find it; this appears to be genuinely absent
  from the paper, not just missed by me, but I flag it as possibly present in a figure/table I could
  not get the extraction tool to read in full (large HTML page, summarized by a secondary model).

## 3. EAT-2 nicotinic receptor kinetics

Not found. Specifically checked:
- Raizen 1995 and McKay 2004: abstracts only (see above); no kinetic numbers in the abstract text, and
  I could not get past the PMC bot-challenge/OUP paywall to check the full text.
- EAT-18/EAT-2 heterologous expression paper (auxiliary subunit paper), PMC7173930,
  URL: https://pmc.ncbi.nlm.nih.gov/articles/PMC7173930/, opened: full text (direct fetch worked).
  This reports two-electrode-voltage-clamp pharmacology for heterologously expressed Cel-EAT-2 and
  Asu-EAT-2: pEC50 for ACh = 4.8 +/- 0.0, pEC50 for nicotine = 4.2 +/- 0.1 (Cel-EAT-2); pEC50 for ACh =
  5.7 +/- 0.0 (Asu-EAT-2); a Hill coefficient example "methacholine having the steepest Hill slope (nH
  = 3.5 +/- 1.3)". These are concentration-response (dose-response) numbers, not current kinetics. I
  found no rise time, decay time constant, or desensitization time constant for the EAT-2 current
  anywhere in this paper.

**Conclusion: no published time constant or kinetic description of the EAT-2 current was found in any
freely accessible source checked.** If this number exists, it is most likely only in the unreachable
full texts of Raizen 1995 or McKay 2004, or in a paper I did not find in the time available (e.g. a
more recent heterologous-expression paper beyond the EAT-18 one above). Treat the absence as "not
found," not as "confirmed absent."
