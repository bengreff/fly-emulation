# Lit check: amphid glia K+/Cl- numbers in C. elegans (not mammal)

Searched Europe PMC REST API, PMC full text via NCBI eutils efetch (grep-verified against raw
XML), and WormAtlas handbook. No paid sources.

## 1. Extracellular K+ around amphid endings / sheath lumen / pseudocoelomic fluid

**None found.** Searched: `"amphid sheath" potassium`, `pseudocoelomic fluid potassium
concentration`, `"pseudocoelomic fluid" elegans`, `potassium ion-selective electrode elegans`,
`"extracellular potassium" sensory neuron elegans`.

- Huang et al. 2026, *Nat Commun*, "p38 MAPK orchestrates cross-tissue potassium homeostasis for
  survival," PMID 41796133, PMCID PMC13100137 — opened full text, verified. Names the hypodermis as
  the barrier contacting pseudocoelomic fluid, but gives no measured concentration in worm
  tissue/fluid, only bath/plate K+ ("various KCl concentrations (0-250 mM)" in liquid medium; "50 mM
  potassium phosphate buffer"). Quote: "elevated hypodermal CATP-3 likely restores organismal K+
  homeostasis ... Because the hypodermis ... directly contacts pseudocoelomic fluid." No number for
  the fluid itself.
- No ion-selective-electrode or K+-dye measurement of pseudocoelomic or amphid-lumen K+ found.

## 2. Glial K+ clearance/buffering kinetics, Kir (irk-1/2/3), knockout numbers

**Partial.** No K+ clearance/buffering time constant found.

- Graziano, Wang, White, Kaplan, Fernandez-Abascal, Bianchi 2024, *Neuron*, "Glial KCNQ K+ channels
  control neuronal output by regulating GABA release from glia in C. elegans," PMID 38460523, PMCID
  PMC11156561 — **opened full text**, grep-verified. A KQT (KCNQ-family) paper, not Kir, but the
  only hit using an *irk* gene in glia: "we wondered whether an inward rectifier K+ channel ... would
  rescue kqt-2 1-octanol avoidance deficit. To test this idea, we expressed worm irk-2, an ortholog
  of human inward rectifier KCNJ K+ channel genes, in AMsh glia of kqt-2 knockout and found
  significant rescue (Fig. 1B)." No irk-1/irk-3 data; no current/voltage numbers in body text
  (figure-only). Ca2+ numbers given as a downstream readout, not K+: "WT AMsh had an average Ca2+
  concentration of ~111 nM ... kqt-2 AMsh had a Ca2+ concentration of ~526 nM (Fig. 2I)." Recording
  saline "145 mM NaCl, 5 mM KCl, 1 mM CaCl2, 5 mM MgCl2, 20 mM D-glucose, 10 mM HEPES ... pH 7.2" is a
  bath recipe, not a measured value.
- Ray, Gurung, Manning, Kravchuk, Singhvi 2024, *Cell Reports*, "Neuron cilia restrain glial KCC-3
  to a microdomain to regulate multisensory processing," PMID 38421867, PMCID PMC11296322 —
  **opened full text**. Authors flag the gap directly: "While direct assessment of K+ or Cl- levels
  or dynamic cell volume at these glia-NRE subcompartments is currently technically limited, these
  models will be exciting to test in future studies." (Discussion). Purely localization/structural;
  no kinetics or concentrations.
- No AMsh/CEPsh Kir (irk-1/2/3) expression-profiling numbers found.

## 3. Anatomy: are left/right amphid sheath lumens separate (no shared lumen)?

**No explicit "not shared" sentence found, but the anatomy is unambiguously bilateral, one
structure per side.** Ward et al. 1975, Ware et al. 1975 (J Comp Neurol), and Perkins et al. 1986
(J Neurosci) are pre-PMC EM papers with no free full text located (no PMCID in Europe PMC).
WormAtlas Handbook, "Nervous System Neuronal Support Cells" (wormatlas.org,
hermaphrodite/neuronalsupport/mainframe.htm) — **opened full page**, citing Perkins et al. 1986:
- "Hermaphrodites have 61 ciliated neurons ... all except three (AQR, PQR, and PVR) are members of
  bilateral pairs (Ward et al., 1975; White et al., 1986; Hall and Russell, 1991)."
- "Each of the bilaterally symmetric amphid nerves contains dendrites of 12 amphid neurons and the
  process of one amphid sheath cell."
- Figure legend: "TEM of the left amphid channel, longitudinal section ... (Based on Perkins et al.,
  1986.)" — a distinct, single-side structure; "a similar set of sensilla ... found on the right
  side" elsewhere on the page.
No sentence states the two lumens don't connect; this is an inference from "one sheath cell, one
channel, per side," not a direct answer to the question as posed.

## 4. Named papers / 2017-2026 glial K+/Cl- numbers

- **Singhvi et al. 2016, Cell**, "A Glial K/Cl Transporter Controls Neuronal Receptive Ending Shape
  by Chloride Inhibition of an rGC," PMID 27062922, PMCID PMC4860081 — **opened full text, grep-
  verified**. "Cl- ions ... are potent inhibitors of GCY-8 cyclase activity ... with an IC50 of
  ~60mM" (Fig 5D); "wild-type AFD neurons have 43 ± 2 microvilli (n=6), gcy-8(ns335) mutants have
  12 ± 1 (n=4)"; length "2.5 µm for wild-type ... 1.5 µm for gcy-8(ns335)" (Fig 3E-H); diet "150 mM
  KCl" restored kcc-3(ok228) AFD shape, "150 mM Na+Cl- or K+Acetate-" gave only partial,
  non-sustained rescue (Fig 2F). Intervention concentrations, not endogenous K+/Cl- levels.
- **Fernandez-Abascal, Johnson, Graziano, Wang, Encalada, Bianchi 2022, Neuron**, "A glial ClC Cl-
  channel mediates nose touch responses in C. elegans," PMID 34861150, PMCID PMC8813913 —
  **opened full text, grep-verified**. "clh-1 knockout worms have significantly reduced response to
  nose touch (Fig. 1B, 30.8 ± 1.3% versus 79.9 ± 0.9% in wild type)." Basal intracellular Cl-
  (SuperClomeleon YFP/CFP ratio, not an absolute concentration): "1.38 and 1.42 for wild type and
  clh-1 respectively, not statistically different." Diet "150 mM NaCl or KCl" partially rescued
  nose-touch insensitivity (Fig 5A). GCaMP decay "time constants" plotted per animal, Fig 2-7, no
  numeric value in body text.
- **Yoshida, Nakano, Suzuki, Ihara, Higashiyama, Mori 2016, Genes Brain Behav**, "A glial K+/Cl-
  cotransporter modifies temperature-evoked dynamics in C. elegans sensory neurons," PMID 26463820
  — **abstract only** (no PMCID, no free full text). Describes KCC-3 in amphid sheath glia
  modulating AFD dynamics; abstract gives no K+/Cl- concentration or kinetic numbers.
