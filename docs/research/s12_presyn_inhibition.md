# S12: presynaptic inhibition of sensory terminals (for the leg sugar route and the N11 switch)

Why: the 00:41 margin pre-registration (DECISIONS, 6 October) named GABA-B presynaptic inhibition of sweet
GRN terminals as the next mechanism if leg bitter leaked into the leg sugar route at every margin. The model
has a switch for it, `cell_type:all|presynaptic_inhibition_gain` (row n11_preinh_gain, default 0, never
tested). This note records what an open-text search found for its strength and time course.

A Sonnet agent searched (6 October, 00:44-01:13); full texts saved under `data/raw/presyn_s12/`
(gitignored). I re-found every quote below in the saved text. Labels: **read** = I read the sentence;
**abstract only** = full text not obtained; **derived** = my arithmetic on a read number.

`data/raw/presyn_s12/chu_2014.pdf` is not the paper. It is a 5.8 kB Cloudflare "Just a moment..." page from
a failed fetch. Chu et al. 2014 was not retrieved (no PMC copy or preprint found). Do not cite that file.

| Terminal | Quantity | Value | Prep | Label | Source |
|---|---|---|---|---|---|
| ORN → PN | which receptors, which phase | "A GABA B receptor antagonist blocked the late phase of this inhibition, but had only a modest effect on the early phase ... Adding a GABA A antagonist to the GABA B antagonist blocked the residual early portion" | in vivo whole-cell PN, nerve stimulation and GABA iontophoresis | read | Olsen & Wilson 2008 Nature 452:956 |
| ORN → PN | GABA-B in the ORN itself | with pertussis toxin in ORNs, "GABA still inhibited ORN-PN EPSCs, but now this inhibition had a briefer duration" and was then fully blocked by the GABA-A antagonist | same | read | same |
| ORN → PN | size of the inhibition | not stated in the text (figures only) | same | not found | same |
| ORN → PN | GABA-B block, PN input-output slope | "increased the slope of the input-output function by 105% with no effect on the offset, thus revealing a multiplicative gain modulation" | PN dendrite GCaMP, nerve stimulation | read | Root et al. 2008 Neuron 59:311 |
| ORN → PN | same, per odour | slope up 153%, 67% and 43% (cVA, ethyl hexanoate, 2-phenylethanol); CO2 unchanged | same, odours | read | same |
| ORN terminal | GABA-B R2 RNAi in ORNs, release slope | "a 110% increase in the slope, thus indicating an increase in the gain of ORN transmission" | ORN synapto-pHluorin | read | same |
| ORN terminal | at what input | GABA-B block raises PN response "at high stimulus intensities but not at low intensities" | PN GCaMP | read | same |
| sweet GRN (labellum) | GABA-B and bitter suppression | blockade and knockdown of GABA-B "lead to increased sugar responses and decreased suppression of the sweet response by bitter compounds" | GRN terminal calcium | abstract only (agent's summary; full text not obtained) | Chu et al. 2014 Curr Biol 24:1978 |
| sweet GRN (labellum) | mechanosensory suppression | "Activation of the labellar MNs [mechanosensory neurons] ... reduced these calcium signals" at 100 mM sucrose | sweet GRN terminal calcium | read (size in a figure only) | Jeong et al. 2016 Nat Commun 7:12872 (PMC5031804) |
| sweet GRN (labellum) | which GABA-B subunit | "reduced GABA B R 2 but not GABA B R 1 or GABA B R 3 expression in sweet GRNs" impairs the shift in food preference | behaviour | read | same |
| leg hook and claw proprioceptors | receptor | "all claw and hook neurons strongly express Rdl, the gene for GABA A receptors" | single-cell RNA-seq | read | Dallmann et al. 2025 Nature 647:445 (PMC13070307) |
| hook axons | who inhibits | "Most GABAergic input onto hook axons (83%) comes from ... the 9A hemilineage"; one 9A neuron gives 57% of hook axon input | connectome | read | same |
| hook axons | when | calcium signals suppressed during active, self-generated leg movement | imaging | read (no percentage) | same |

## What this settles for the model

- **Kinetics.** At ORN terminals the inhibition has a fast GABA-A part and a slow GABA-B part (Olsen &
  Wilson 2008, read). No source here gives a decay time constant in ms for either at a sensory terminal.
  The only time constants found (Dallmann 2025, 30 ms on, 300 ms off) are for the calcium indicator, not
  the inhibition. The model's switch decays with the fast synaptic constant (5 ms), so it stands for the
  GABA-A part only (inferred). A GABA-B version would need a slower trace (the model's `gabab_tau`, 150 ms,
  guessed, is the obvious candidate).
- **Size.** Root 2008 is the one number for strength. Removing GABA-B about doubles the slope (+105% PN,
  +110% ORN release). So with GABA-B intact the gain at high input is about 1/2.05 to 1/2.1, about 0.48 of
  the disinhibited gain (derived). In the model's form, release × 1/(1 + k·I_inh), that means k·I_inh ≈ 1
  during strong olfactory input (derived). It varies with the glomerulus (+43% to +153%, CO2 none), so one
  k for every sensory terminal is a simplification.
- **Taste.** No number. Chu 2014 (abstract only) and Jeong 2016 (read) establish GABA-B on sweet GRN
  terminals and that it carries both bitter and mechanosensory suppression of sweet. Nothing here is from
  tarsal GRNs.
- **No GRN electrophysiology.** All taste evidence is calcium imaging.

## Bearing on the leg sugar route

The 00:41 margin sweep made the mechanism unnecessary for the leg bitter leak: at margins of 2 to 4 mV, leg
bitter at 100 Hz gives MN9_L 0 Hz (DECISIONS, result of the 00:41 pre-registration). The leak at 1 mV ran
through AN05B106, which bitter GRNs excite directly. Inhibition of sugar GRN terminals would not stop that.
So the switch stays off and untested. A bracket on it (GABA-B kinetics, k·I_inh about 1 at strong input) is
worth doing for labellar bitter-on-sugar suppression and for the olfactory gain, not for this route.
