# s18 N19 row-check (Sonnet Explore subagent, foreground, 21 Oct 2026; read levels as reported by it)

Checks the magnitude and kinetic rows of `s18_n19_receptor_coupling.md` that N19 would rest on, and looks for
non-associative (unpaired) monoamine gain effects on identified adult Drosophila neurons.

## 1. Hige, Aso, Modi, Rubin, Turner 2015, Neuron 88:985 (PMC4674068, full text read)
- The "90 +/- 3.7%" is the reduction in MBON-gamma1pedc EPSC charge transfer **after pairing** a 1 s odor (CS+)
  with optogenetic activation of one PPL1-gamma1pedc DAN (four 1 ms pulses at 2 Hz; MB320C>CsChrimson),
  in vivo whole-cell voltage clamp (Fig. 3D). Spiking falls 80 +/- 5.7% (Fig. 1F).
- Backward pairing (DAN 0.5 s before odor): no effect (Fig. 1G-J). Unpaired odor (CS-): 20-27% depression,
  tracking KC overlap (Fig. 1F, S6, Fig. 7). Non-cognate DAN (PPL1-gamma2alpha'1, MB099C): no change (Fig. 5A-D).
  No DAN-alone (no odor) condition in the paper.
- Receptor: cited as dDA1 (Dop1R1) **in KC axons, presynaptic** (Kim 2007; Qin 2012); LTD persists with MBON
  spiking blocked (QX-314).
- Onset within 1-1.5 min; persists >= 40 min (Fig. S4).
- **Verdict: not a valid check for N19.** It is associative, pathway-specific, presynaptic plasticity. It belongs
  to the MB plasticity rows (N21, fly2), as a unit check there.

## 2. Lv et al. 2024, Natl Sci Rev 11(5):nwae112 (PMC11126161, full text read), GRAB-OA1.0
- In vivo, single optogenetic pulse (Tdc2>CsChrimson), MB gamma3: tau_on ~0.34 s, tau_off ~5.90 s (Fig. 2J, n=7).
- In vivo, 50 electrical pulses at 100 Hz near the MB, OA1.0 in MB247 KCs: tau_on ~0.6 s, tau_off ~9.4 s
  (Fig. 2E, n=3); signal lost with Tdc2>TbetaH-RNAi.
- In vitro HEK293T (OA then epinastine, line scan): tau_on ~0.02 s, tau_off ~1.40 s (Fig. 1D).
- The paper does not say the in vivo decay is clearance-limited; that the sensor's 1.4 s is much shorter than
  5.9-9.4 s makes it likely (inferred, ours).

## 3. Non-associative monoamine gain effects, adult Drosophila
- **Dacks et al. 2009, J Neurogenet 23:366 (PMC2850205, full text read).** Bath 5-HT 100 uM (also 1 uM, 10 nM),
  ex vivo brain-antennae, GH146>G-CaMP PNs. Broad odor: PN responses in DM2/DL1/DM3 up **~15%** (n=8, Fig. 5C-D).
  Sparse odors (cVA->DA1, ethyl hexanoate->DM2, 3-heptanol->VM2): significantly enhanced (Figs. 1-2).
  Electrically evoked PN input-output curve shifted left, slope unchanged (Fig. 3A). Blocked by methysergide.
  No receptor subtype named.
- **Strother et al. 2018, PNAS 115:E102 (PMC5776785, full text read).** Bath CDM (OA agonist) 50 nM, ex vivo:
  Mi4 response to L5 photoactivation (Chrimson) much larger, higher asymptote (Fig. 6F,H; numbers in the figure
  only). In vivo CDM 10 uM: Mi1, Tm3, Mi4, Mi9 and T4 responses to high temporal-frequency gratings increase
  (Fig. 4E-F). Receptor not named.
- **Suver, Mamiya, Dickinson 2012, Curr Biol 22:2294:** paywalled; abstract only (bath OA and CDM mimic the
  flight increase of VS-cell responses). No numbers.

## 4. In vivo decay of other monoamines
- **Wan et al. 2021, Nat Neurosci 24:746 (PMC8544647, full text read).** GRAB-5HT1.0 in KCs, in vivo, single
  electrical stimulus of the MB horizontal lobe: tau_on ~0.07 s, tau_off ~4.08 s (Fig. 2h-j, n=8).
- **Sun et al. 2018, Cell 174:481 (PMC6092020).** No fly in vivo GRAB-DA tau_off number found in the text; the
  ~3 s (DA1m) and ~17 s (DA1h) values are **mouse acute slice** (Fig. 2F). Do not use them for the fly.

## Not verified
- Suver 2012 numbers and CDM concentration (paywalled).
- Strother 2018 Fig. 6 Mi4 gain numbers (figure pixels only; next step: read the figure image).
- Arenz 2017 Drosophila CDM numbers (not fetched).
- Sun 2018 fly in vivo GRAB-DA tau_off.
