# Item 2, stage 2 (MC -> pharyngeal muscle): port spec (wbody2, 9 Nov 2026)

Status: class B (the published synapse is missing), to be built as a C toggle (both sources). Nothing built yet.
Sources: `lit_mc_nmj.md` (Sonnet agent; full texts opened: Steger 2005 PMC1382270, Shtonda & Avery 2005
PMC1351090, Sherman & Harel 2024 PMC10873627 and their code; McKay 2004 abstract only).

## What runs now (measured, merged code, 8 Nov)

MC synapses only onto the marginal cells (Cook 2019's EM partners) and reaches the muscle through the marginal cells'
gaps. With the 40 pA x 30 ms MC pulses at 4 Hz, the coupling probe gives at most 1 pump in 3 s at any of the 12
in-range gap and area points, at the ledger NMJ and at the range top (bar: >= 8 of 10). Since 9a67a6f the organ
synapses take the brain's receptor form (MC -> marginal cell: the nAChR class by the no-profile rule).

## What the sources say

- EAT-2 is a nicotinic receptor subunit that "functions in the pharyngeal muscle", is "localized to the synapse
  between pharyngeal muscle and the main pharyngeal motor neuron MC" and "is required for MC stimulation of pharyngeal
  muscle" (McKay et al. 2004, abstract; stated). It does not name pm4, pm5 or the marginal cells.
- Steger et al. 2005 (measured, wild type, EPG and intracellular): rest about -73 mV; EPSP to E-spike 6.7 +- 0.3 ms
  (cca-1: 26.7 +- 2.3); E-spike / EPSP 3.4 +- 0.3 (cca-1: 1.3 +- 0.1); eat-2 mutants have no EPSPs and rest about
  13 mV higher. n for the latency: to read (needed to turn the SEM into a range).
- Shtonda & Avery 2005 (measured, N = 29): Rin 22.8 +- 5.2 MOhm, C 362.6 +- 36.8 pF, E_leak -53.6 +- 4.1 mV; CCA-1
  activates from about -40 mV, EGL-19 from about -20 mV.
- Sherman & Harel 2024 (their code, read): MC is not modelled; a 40 ms square current at the metacorpus-isthmus
  border (EX_INPUT_NODE 2000) every 1450 ms takes the muscle from -73 to about -40 mV, "based on Steger et al. 2005
  Fig. 4A". That is the input their muscle was fitted with.

## The port

Toggle `ph_mc_route` (organs_pharynx):
- `cook` (nested; the current code): MC's Cook synapses onto the marginal cells, nothing else.
- `eat2` (the port): MC's Cook contacts onto each marginal cell are placed instead on the pharyngeal muscle cell at
  the same site (the pm the marginal cell borders: to read from Albertson & Thomson 1976 / WormAtlas; lookup), as an
  EAT-2 nicotinic synapse (receptor class nachr; EAT-2's own kinetics are not published, so the brain's nachr class
  kinetics, inferred, shared by class), at the ledger's shared NMJ conductance per contact (no new free value).
- `both` (C): both placements, each at half the contacts (the total EM contacts unchanged).
Validity: MC's EM synapses lie where marginal cells and muscle meet, and the EM partner assignment there cannot tell
the two apart; EAT-2's localisation says the muscle side carries the receptor.

## Bars (write into the check script's docstring before running)

1. Neutral: `ph_mc_route=cook` bit-identical to the code before the port (max |dV| 0 on every pharyngeal cell,
   the coupling probe's setup).
2. Muscle alone, the published drive (Sherman & Harel's): MC silent, a 40 ms square current into the metacorpus-
   isthmus pm every 1450 ms at the amplitude that takes it from rest to -40 mV: exactly one pm4 AP per input. This
   checks the muscle membrane separately from the synapse.
3. Effect (`eat2`): the coupling probe's bar unchanged, pumps >= 0.8 x MC pulses (40 pA x 30 ms at 4 Hz), at the
   ledger NMJ and the template gap and area (no value moved).
4. Latency (`eat2`): MC spike peak to pm AP onset inside Steger's wild-type range (6.7 ms, +- 2 SD from the SEM once
   n is read; until then reported, no bar).
5. eat-2 null (EAT-2 conductance 0 under `eat2`): no MC-evoked depolarisation above 1 mV in pm (Steger: no EPSPs).

Then tests, the coupling probe, the vitals battery (food on and off, 150 bio s, `wormemu.fit.vitals`) and the
MECHANISMS_AUDIT row 13 text through wbrain2. Default stays `cook` until a gate, a battery run and a viewed figure
adopt `eat2`.
