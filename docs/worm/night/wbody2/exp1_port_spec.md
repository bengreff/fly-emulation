# EXP-1 port onto the enteric muscles (wbody2, 9 Nov 2026, inbox 02:35 item 1)

Written 9 Nov between 02:58 and 03:01 CST (the two `date` calls around it), before any code change or check run. Status row "3 defecation, expulsion chain", class B.

## What is published (sources opened; notes `lit_exp1.md`)

- Beg & Jorgensen 2003 Nat Neurosci 6:1145 (full text, the Jorgensen lab's PDF): EXP-1 in Xenopus oocytes, two-electrode
  clamp at -60 mV. GABA EC50 26.4 +- 1.08 uM, Hill 1.8 +- 0.24 (n 19); reversal -5.54 +- 2.20 mV in Ringer's (n 24);
  Cl-free -5.05 mV, Na-free -84.3 mV, PK/PNa 1.1, negligible divalent permeability (all measured). No single-channel
  conductance, no rise, decay or desensitisation time constants (not reported). Expression (GFP): intestinal muscles
  and anal depressor, not the sphincter; the inhibitory UNC-49B is in the sphincter and not the other two. exp-1
  mutants: enteric muscle contraction in 13.6-24.2 % of cycles against 95.7 % in wild type. No recording from an
  enteric muscle.
- Jiang et al. 2022 Nat Commun 13:2783 (PMC9120479, full text): DVB rest -49.0 +- 3.6 mV, threshold -23.4 +- 1.6 mV,
  peak 26.3 +- 2.6 mV, half-width 358.8 +- 59.5 ms (n 5; measured, dissected worms); AVL and DVB spikes "lagged about
  3 s behind the intestinal calcium wave" and coincided with expulsion; expulsion in 18 of 19 wild-type cycles.
- Wang et al. 2013 Curr Biol (PMC3651789): one DVB Ca spike per cycle, beginning about 3 s after pBoc, peaking just
  before Exp.
- The enteric muscle's own membrane: no recording or model found free (lit_exp1.md section C). It stays the BWM's Du
  2025 membrane (inferred), as now.

## Current code (the nested form)

`organs_intestine._build_enteric`: Cook's DVB synapses (DVB -> mu_intL 3 contacts, mu_intR 1; Cook has no chemical
input to mu_anal or mu_sph and none from AVL) go through `organs_nrn.chem_synapse` with the sign forced excitatory, so
under receptor_kinetics (kinetic, the default) they take the brain's default GABA-cation class `gabacat`: at the
ledger EC50 19 uM, Hill 1, reversal 0 mV, tau_off 20 ms, tau_des 1000 ms (read from the built wsyn on 5834790).

## The port

New toggle `enteric_exp1` in organs_intestine (neutral by default):
- `brain` (default, the code before): the brain's gabacat class values.
- `beg2003`: the enteric muscles' GABA-cation sites are EXP-1: EC50 26.4 uM, Hill 1.8, reversal -5.54 mV (Beg &
  Jorgensen 2003, measured in oocytes; new Specs `exp1_ec50_uM`, `exp1_hill`, `exp1_erev_mV`, ranges the reported
  mean +- 2 SD where given). Rise, decay and desensitisation stay the gabacat class's (not reported for EXP-1).
  A GABAergic input onto mu_sph, if a connectome ever gives one, is inhibitory (UNC-49B: the brain's default
  GABA-chloride class); Cook gives none, so this arm changes nothing today and is stated, not tested on a trace.
Validity: oocyte values at room temperature stand for the worm's muscle; under receptor_kinetics off or graded the
synapse has no dose-response and `beg2003` changes nothing.

## Pre-registered check (`scripts/worm/wbody2/exp1_check.py`)

Preparation: the DMP sub-brain (dmp_trace.DMP: AVL, DVB, PVR, AVAL/R, PHAL/R, PDA, DA09, VA12, LUAL/R, PVCL/R) with
the intestine, the enteric muscles and the other organs, ledger values (at_ledger), 1 ms steps, 150 s.
DVB driven: an SEClamp on DVB's soma (series resistance 0.01 MOhm) plays one spike per int9 wave: V = -49.0 + 75.3
exp(-0.5 ((t - t_pk) / 152.4 ms)^2) mV from t_pk - 3 sigma to t_pk + 3 sigma (rest, peak and half-width from Jiang
2022, FWHM 358.8 ms = 2.355 sigma, derived), t_pk = 3.0 s after each int9 Ca peak (Jiang 2022 "about 3 s"; the peak
found causally with the battery's rule: mean of int9L and int9R, vitals.peaks threshold and gap). Between spikes the
clamp is off (series resistance 1e9 MOhm).

Bars, written now:
1. Neutral: `enteric_exp1=brain` reproduces the code before exactly: the 150 s driven run's enteric V (4 muscles),
   DVB V and expulsion times bit-identical to a reference run made on this commit before the change.
2. The Director's check, per form: once DVB fires, one expulsion after each int9 wave. Pass: at least 2 DVB spikes in
   8-150 s; for every spike exactly 1 expulsion between its onset and the next spike's onset (the last: run end, at
   least 10 s later); 0 expulsions in 8 s to the first spike onset (the first 8 s are the start-up, as in
   enteric_probe.py).
3. Control, reported: the same run with DVB not driven (expected 0 expulsions; a nonzero count is reported as is).
Reported for diagnosis, not scored: per spike, the peak mean activation of mu_intL, mu_intR, mu_anal (the detector
needs 0.5 then 0.2), enteric spikes, enteric peak Ca, and the same driven run with the Du membrane set to the first
in-range set that is silent at rest (`du=0`, bwm_rest_probe; diagnostic, not adopted).
Adoption of beg2003 needs bar 2 to pass under it, a battery and a viewed figure; if it fails, beg2003 stays nested and
the failure is written down (two attempts at most).
