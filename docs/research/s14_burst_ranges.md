# s14 arm B: burst-generating ranges for insect central interneurons

Literature pass for arm B of the s14 class-level options test (intrinsic bursting of the walking-core E1/E2
types). Searched by a Sonnet subagent on 20 Oct 2026; **unchecked by a second reader**. Every row below says
how it was read. Use: the bounds and the calibration target of `cell_type:core_rhythm_exc|adp_mv`,
`|adp_tau_ms` and `|nap_gbar_scale` (rows n2b_* in data/model/parameters.csv; all **guessed**, DIAGNOSTIC).

## What was not found

There is no spike-triggered after-depolarisation (ADP) amplitude or decay for any insect central interneuron in
text the agent could read. Seki et al. 2010 (locust Kenyon cells) and Choi et al. 2004 are paywalled and give no
ADP numbers in their abstracts. So the ADP mV/ms pair has no measured value and no measured range. The model's
value is set by matching a measured **burst output** (below) on single cells, before any network run.

## What was found

| Quantity | Value | Cell, species, prep | Source | Read in | Label |
|---|---|---|---|---|---|
| Burst depolarisation | 20-25 mV | cricket A3-AO opener and closer interneurons, singing CPG, synaptically intact | Schöneich, Hartmann & Hedwig 2012, Brain and Behavior (PMC3500458) | full text | measured |
| Spikes per burst | 4-6 (A3-AO), 3-4 (T3-DO), 5-6 (closer) | as above | same | full text | measured |
| Intra-burst rate | up to 380 Hz (A3-AO), 160-200 Hz (T3-DO), 250-300 Hz (closer) | as above | same | full text | measured |
| Current-evoked burst | 5 nA gives 2-6 spikes per depolarisation | A3-AO | same | full text | measured (an intrinsic burst mechanism) |
| Rebound after hyperpolarisation | 2-4 mV after -4 nA | closer interneuron | same | full text | measured |
| Plateau is soma-intrinsic | evoked in surgically isolated somata; drives 1:1 axonal bursts | cockroach fast coxal depressor MN | Hancox & Pitman 1991, Proc R Soc B 244:33 | abstract (secondary reproduction) | measured, qualitative |
| Octopamine-induced plateaus and bursting | qualitative | locust flight interneurons, isolated ganglion | Ramirez & Pearson 1991, J Neurophysiol 66:1522; Brain Res 549:332 | abstract (secondary) | measured, qualitative |
| Burst 50-75 ms, 4-16 Hz | **unverified** | as above | one search-engine summary only | not confirmed | do not use |
| Persistent Na current | ~8% of the transient current (exon L), ~2% (exon k) | Drosophila larval MNs aCC/RP2 | Lin, Wright, Muraro & Baines 2009, J Neurophysiol 102:1994 | secondary, unverified against the PDF | measured |
| Persistent Na current at -20 mV | ~50% of peak; activates near -60 mV | cockroach BgNav (expression system) | PMC511065 (Na-channel RNA editing) | full text | measured, cockroach |
| Leg-rhythm burst phase | 10-20% of a 0.5-2 s period | locust leg motor pattern, pilocarpine | Ryckebusch & Laurent 1993, J Neurophysiol 69:1583 | abstract | measured, motor-pattern level |

Gouwens & Wilson 2009, Fushiki 2016, Zwart 2016, Sheeba 2008 (l-LNv bursting, no numbers) and the MN5 Ca-current
work gave no usable ADP or plateau numbers in accessible text.

## How the model uses it

- **adp_mv (arm B):** bounds 0-25 mV (guessed). The upper bound is the cricket burst depolarisation, which is the
  sum over a burst and so is an upper bound on any per-spike increment.
- **adp_tau_ms:** bounds 2-75 ms (guessed). At 2-6 spikes and 160 Hz a burst lasts at most about 30 ms.
- **The target the value must hit (the rule in scripts/probes/s14_burst_calib.py):** on isolated E1/E2 cells
  with their own m10f0 constants and rung-1 channels, a single triggering spike gives a burst of 2-6 spikes at
  160-380 Hz that ends by itself. This is the cricket range, so it is a range from *some* insect rhythm
  interneuron, not from Drosophila E1/E2. Nothing has been recorded from E1/E2.
- **nap_gbar_scale (arm B'):** bounds 1-10 (guessed). The rung-1 NaP gbar is itself guessed. The larval-MN
  ratio of 2-8% is a ratio to the transient current, which the LIF model does not have, so it does not fix the
  scale.
- **Caveat:** Schöneich 2012 recorded in an intact network. The current-injection result is the evidence that
  the burst is intrinsic, and it does not separate an ADP from a plateau or a persistent inward current. Arm B
  and arm B' are two readings of one fact.

## Calibration result, linear ADP (20 Oct, scripts/probes/s14_burst_calib.py; measured on the model)

The ADP as first built (each spike adds `adp_mv` of drive, decaying at `adp_tau_ms`) has no admissible value.
All 12 E1/E2 cells carry identical m10f0 constants (tau_m 20 ms, rest -52, threshold -45, reset -52, t_ref 2.2 ms;
BK 7.87, Kv2 0.22, SK 0.025, NaP 0.015 x leak). With a +10 mV trigger:

- At adp_mv 0-24 mV with adp_tau_ms 5-20 ms, and below about 16-22 mV with 40-75 ms, the cell fires 1 spike.
- At 16 mV/60 ms, 18/50, 20/40 and above, it **latches**. The ISIs shorten (29, 16, 12, 9, 8, 7 ms ...) to a
  steady 2.6 ms (about 380 Hz), and it keeps firing through the whole 1.8 s run. The drive sums without limit.
- There is no setting in between with 2-6 spikes that then stop. In the first 60 ms the rate is at most about
  140 Hz, never 160-380 Hz.
- With BK set to 0 (a diagnostic only), the same latch reaches 167-239 Hz in its first 60 ms. So the m10f0 BK
  AHP caps the rate of the early burst.
- NaP x 1.5-10 with no ADP gives 1 spike at every scale. The model's NaP is instantaneous with V½ -48 mV, and the
  reset to -52 mV switches it off after every spike. So arm B' has no admissible value either.

Reading: a spike-triggered ADP alone is positive feedback with no limit. A burst also needs something that ends
it. Real ADPs and plateaus are conductances, so they saturate, and plateaus inactivate (Hancox & Pitman 1991:
plateaus outlive the stimulus, then end).

## Calibration result, saturating ADP with inactivation (rule v2, 20 Oct; measured on the model)

The ADP now saturates at `adp_mv`, and with `adp_recovery_ms` > 0 each trigger uses up its availability. The
ceiling is held inside the measured 20-25 mV. Of 105 triples (a ∈ {20, 22.5, 25} mV, tau 10-100 ms, recovery
0-200 ms), 32 are admissible: 2-6 spikes, and the burst ends and stays ended.

- **Rule selection (closest to 4 spikes; ties to the smaller a, tau, rec): 20 mV, 100 ms, 200 ms.** It gives
  4 spikes over 92 ms at 33 Hz. Tau and rec are both at their upper bounds.
- **The shortest admissible burst: 25 mV, 40 ms, 50 ms**, the smallest rec giving that burst. It gives 2 spikes
  in 21 ms (47 Hz), the closest admissible burst to the cricket burst duration (4-6 spikes in about 10-20 ms).
- Every admissible burst fires at 29-47 Hz, against the measured 160-380 Hz. This is the arm's validity limit.
  The model cell can match the cricket spike count or the cricket burst duration, but not both.
- NaP x 1.5-10 (arm B') still gives 1 spike at every scale, so it has no admissible value.
