# fly2 s23 literature reads: STP held-out, gap-junction coupling, KC→MBON plasticity (21 Oct night)

Two Sonnet readers (fly2 brief, 21 Oct 21:40). "Read" = the reader saw it in the primary text, legend or table; anything else is flagged. Nothing here is entered in a table yet.

## ORN→PN depression (N10/N29), a held-out check
- Nagel, Hong & Wilson 2015 Nat Neurosci 18:56, Fig 1b-c, Eq 1 (read): f 0.78, τ 893 ms, 10 Hz nerve trains, DM6/VM2 PNs, n 19. This is the fit in `stp_connections.csv`, so a check against it is a consistency check, not held out.
- Same paper, Fig 2 (read): the curare-resistant component f 0.77, τ 1006 ms; the IMI-resistant component f 0.91, τ 629 ms. These are components of the same data, not an independent test of the pooled row.
- 50 Hz depression "even more pronounced" (Fig 2e-f), but no ratio in readable text.
- Kazama & Wilson 2008 Neuron 58:401 (paired-pulse ratio) and Olsen & Wilson 2008 Nature 452:956 (4 Hz trains): primary text not reachable (403). **No held-out ORN→PN depression number is readable today.**

## Gap-junction coupling (N12), per identified site
- **DLMn (Hurkey et al. 2023 Nature 618:118, not 613:721; PMC10232364, Fig 2f, 2h, read):** coupling coefficient (post peak V / pre peak V) 0.023 ± 0.003 (SEM, n 6) for the strong pairs MN1-MN2 and MN3-MN4; 0.01 ± 0.0027 for all other MN1-4 pairs. By component: AHP 0.042 ± 0.04, spike overshoot 0.01 ± 0.004. No input resistance given.
- **Sister PNs (Kazama & Wilson 2009 Nat Neurosci 12:1136, Fig 7, read):** a mixed electrical/chemical synapse, reduced but not abolished by Cd²⁺. No coupling coefficient in the text. An automated read of the plot gave about 0.15-0.20 (hyperpolarising) and 0.25-0.35 (depolarising); this is a figure estimate, not citable as measured.
- **eLN→PN (Yaksi & Wilson 2010 Neuron 67:1034, Fig 4C, read):** mean coupling coefficients are plotted, not stated. The 0.0021/0.0039 values in circulation are unconfirmed.
- **VS-VS (Haag & Borst 2004 Nat Neurosci 7:628, not J Neurosci; secondhand):** up to 10 nA into one VS cell gives about 1 mV in its neighbour; transfer is a 2nd-order low-pass filter, τ about 1.4 ms. No coupling coefficient.
- **GF→TTMn:** no measured coupling coefficient or junction conductance. The 135 µS / 34.5 µS g_gap of the 2019 eNeuro escape-latency model are hand-fitted model values, not measurements.

## KC→MBON plasticity (N21) and memory decay (N22)
- **Hige, Aso, Modi, Rubin & Turner 2015 Neuron 88:985 (PMC4674068, read):** one pairing (a 1 s odour; PPL1-γ1pedc driven by four 1 ms light pulses at 2 Hz from 0.2 s after odour onset) depresses MBON-γ1pedc. CS+ spike count 118 ± 8.3 → 24 ± 7.4 (SEM, n 7; about 80% down; Fig 1F). Charge transfer down 90 ± 3.7% (Fig 3D). The CS− drop is much smaller. Depression persists ≥ 40 min (the recording limit) with only a small sign of recovery.
- **Handler et al. 2019 Cell 178:60 (PMC9012144, read; MBON-γ4, not γ1pedc):** forward pairing depresses, maximal at ISI 0 s. Backward pairing (DAN first) potentiates, maximal at ISI −1.2 s. At an ISI of 6 s plasticity is minimal. Depression needs Dop1R1 and potentiation needs Dop1R2. Single trials. No % magnitudes in readable text.
- **Aso & Rubin 2016 eLife 5:e16135 (read):** γ1pedc memory forms in one round, is fully retained at 10 min and has largely decayed by 24 h. No half-life is given.
- **Berry, Phan & Davis 2018 Cell Reports 25:651 (not Cell; PMC6239218, read):** MBON-γ2α'1 is completely depressed after conditioning and decays to non-significant by 1 h.
- **Baseline KC→MBON unitary EPSP:** none confirmed for Drosophila. The 1.58 mV in a bioRxiv preprint is attributed to locust work.
- **Reader's best held-out check:** fit to Hige Fig 3D (charge), then predict Fig 1F (spikes) on another odour. Better, because it is a different measurement and lab: with the rate fitted to Hige forward pairing, predict Handler 2019's sign flip at ISI −1.2 s and the near-zero change at ISI 6 s.
