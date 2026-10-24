# s23 reads: crop capacity, cibarial pump, neural Q10, adaptation ratios (23 October 2026)

Two Sonnet readers, primary full text unless marked. No survival times, CAFE totals, MBON/DAN rates or rebound
magnitudes were reported. Used in DECISIONS 23 Oct 23:59 (S3 values corrected, N28 Q10 moved to 2.5).

## Crop capacity (S3)
- **Edgecomb, Harth & Schneiderman 1994** (J Exp Biol 197:215): abstract only (paywalled). Every later paper the
  reader could check cites it for an **ordinal 1-5 crop-fullness score**, not a volume (PMC2714410; bioRxiv
  2025.04.07.647529). The 23:20 citation of it for 250 nL is withdrawn.
- **Qi et al. 2015** Mol Brain 8:13 (PMC4687088), MAFE: fed 0.10 ± 0.01 µL, 36 h starved 0.27 ± 0.02 µL (100 mM
  sucrose); "The starved flies ingested 0.32 ± 0.01 μL liquid food on average". Virgin Canton-S females, 25 °C.
- **Pool et al. 2014** Neuron 83:164 (PMC4092013): controls after 24 h deprivation drink "approximately 17 seconds,
  150 nl volume"; DSOG1-silenced flies about 1 µL in about 150 s. Females, 30 °C.
- No male crop or meal volume found. `crop_max_nl` stays 250 nL, **inferred**, bounds 150-320 (these meals).

## Ingestion rate and pump (S3; B17 is fly2's)
- **Itskov et al. 2014** Nat Commun 5:4560: sip volume median 1.05 nL (0.72-1.35, 95 % CI); sips 0.13 s with a
  0.08 s inter-sip interval on yeast, 0.16 s sips on sucrose. w1118 males and females, 25 °C. Derived rate:
  1.05 nL / 0.21 s = **5.0 nL/s** (4.4 with the sucrose sip). The 23:20 value 7.0 used sip duration alone.
- Pool 2014 above gives about 8.8 nL/s (150 nL / 17 s) and 6.7 nL/s (1 µL / 150 s).
- **Manzo et al. 2012** PNAS 109:6307 (PMC3341050): "rhythmic pumping behavior at ≈6 Hz", n 14-21, females,
  25 °C; independent of sucrose and hunger, slowed by viscosity. GCaMP only, no spikes per cycle.
- **Sui et al. 2026** Nat Neurosci (full text, Methods not retrieved; sex and temperature not stated): pumping
  about 6 Hz (field potential), about 5 Hz (dual recording), about 7 Hz (video). Pump MNs fire in bursts each
  cycle; intra-burst rates about 90 (MN12V), 60 (MN12D), 50 (MN11V) and 25 Hz (MN11D), n 18 per MN.
- For fly2: `pump_full_rate_hz` 10 (guessed) sits above the measured 5-7 Hz pump cycle; if it means MN spike
  rate, the intra-burst rates above are the measured scale.

## Neural Q10 (N28)
- **Juusola & Hardie 2001** J Gen Physiol 117:27 (PMC2232470): adult R1-6 photoreceptors in vivo, Oregon R, n 3,
  15-30 °C. Time-to-peak "Q10 = 2.5 ± 0.2"; 3 dB cut-off 2.3 ± 0.3; dead time 3.1 ± 0.1; bump latency 3.4-3.5;
  information capacity 6.5 ± 2.8 per 10 °C. Kinetics range 2.3-3.5.
- Not found: wild-type giant-fibre latency Q10, larval NMJ current kinetics Q10, clock-neuron firing Q10. One of
  these would be the independent N28 check (the Juusola values all come from the same cells that set the value).

## Adaptation ratios (N4)
- No sustained-step early/late firing rates with stated windows in any open full text read: PNs (Wilson &
  Laurent 2005, Gouwens & Wilson 2009, Kazama & Wilson 2009), LNs (Chou 2010), KCs (Turner 2008, Gruntman &
  Turner 2013), LHNs (Frechter 2019), leg MNs (Azevedo 2020), MN5 (Ryglewski & Duch 2009).
- Qualitative only: MBON-α3 "is a spike-frequency adapting neuron" (Hafez et al. 2023 eLife 12:e77578, 400 ms
  steps, f-I only); MN5 "fired additional APs with spike frequency adaptation" (Herrera-Valdez et al. 2013).
- Hige et al. 2015 Neuron 88:985 defines a 1 s, 15 pA sustained-rate protocol for MBON-γ1pedc; values only in a
  figure panel the reader could not render (PMC figure access blocked).
- **Seki et al. 2010** J Neurophysiol 104:1007 defines a spike adaptation rate for AL LNs; paywalled (403), so
  unverified. It is the most likely source of per-class values. N4 stays blocked.
