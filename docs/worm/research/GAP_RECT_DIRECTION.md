# AVA-A(DA/VA) UNC-7/UNC-9 gap junction rectification: direction and ratio

Verdict: current passes preferentially from the A-class motor neuron (UNC-9 side) into
AVA (UNC-7 side) - i.e. "antidromic" relative to the AVA-to-A cholinergic chemical synapse.
This is measured directly, in vivo, by Liu et al. 2017. No source gives a numeric
rectification ratio (fold, index, or Ij ratio) for this specific junction; all three
describe it qualitatively ("strongly rectifying", "minimal", "only allow antidromic
current"). Starich 2009's one quantitative-ish statement is about the AVB:B-type junction,
not AVA:A, and is explicitly called physiologically minimal.

## 1. Kawano et al. 2011, Neuron 72:572-586
Full text read (free PDF mirror, wormweb.org; pdftotext extraction).
- Direction: states the junction has "an asymmetric junctional property that favors
  AVA to A communication" - i.e. frames the asymmetry as AVA influencing A, based on
  optogenetic/calcium-imaging manipulation (hyperpolarizing AVA reduced A activity;
  hyperpolarizing A did not reduce AVA activity), not a direct Ij measurement.
- Numeric ratio: not found. The paper cites Starich et al. 2009 for the biophysical
  rectification itself and does not measure Ij or Gj directly.
- Quote: "Moreover, in wild-type animals, hyperpolarizing AVA and AVE led to an
  effective reduction of A motoneuron activity (Figure 8A); by contrast, hyperpolarizing
  A motoneurons... failed to reduce AVA activity (Figure S7)."
- Label: measured (the hyperpolarization/calcium-imaging asymmetry itself), inferred
  (the paper's own interpretation that this reflects "AVA to A" junctional asymmetry -
  it could also/instead reflect the separate chemical synapse, see disagreement note).

## 2. Starich et al. 2009, Neural Development 4:16
Full text read (PMC2694797).
- System: Xenopus oocyte pairs expressing UNC-7S (or UNC-7L) in one oocyte and UNC-9 in
  the other (heterotypic, not actual AVA/A-MN cells). Dual voltage clamp, Vj stepped
  -100 to +100 mV in 10 mV increments (Figure 9D-E).
- Direction stated: for the AVB:B-type circuit specifically (not AVA:A), "would appear
  to favor conduction of depolarizing potentials from the motor neuron to AVB, rather
  than the reverse" - i.e. same polarity as Liu 2017 (UNC-9 side to UNC-7 side), but
  the paper's own discussion names AVB, not AVA, and calls the effect physiologically
  minimal because channel gating is too slow to matter on a neuronal impulse timescale.
- Numeric ratio: not found. Reports Boltzmann fit parameters (Gmin, V0, steepness A)
  that differ between the two polarities (heterotypic channel "lower Gmin and V0,
  higher A" than homotypic), but no Ij or Gj ratio number for opposite-polarity steps.
- Quote: "The rectification of Gj0 would appear to favor conduction of depolarizing
  potentials from the motor neuron to AVB, rather than the reverse, but again the
  degree of rectification is minimal enough that it may not play a major role
  physiologically."
- Label: measured (the oocyte Gj0/gating asymmetry), inferred (extrapolation to any
  real neuron pair, including AVA:A, since the oocyte system used generic UNC-7/UNC-9
  constructs, not native AVA or A-MN cells).

## 3. Liu, Chen, Mailler, Wang 2017, Nat Commun 8:14818
Full text read (PMC5364397; nature.com itself blocked by login wall).
- System: in situ dual whole-cell voltage/current clamp on actual AVA and VA5 in intact
  adult worms (not oocytes). Holding potential -30 mV, Vm of the other cell stepped
  across a range from that holding potential.
- Direction: current (Ij) is seen only when VA5 (A-MN, UNC-9 side) is more depolarized
  than AVA (UNC-7 side); current flows from VA5 into AVA. Coupling coefficient is
  correspondingly asymmetric: injecting current into VA5 produces a large Vm change in
  AVA; injecting current into AVA produces little Vm change in VA5. The paper calls
  this "probably the strongest degree of rectification ever observed with gap junctions
  in native tissues" but gives no numeric CC, Gj, or Ij ratio for wild type (only n:
  WT n=10, unc-7 n=8, unc-9 n=8, where Ij/CC essentially vanish in the mutants).
- Quote: "Gap junctions between AVA and A-MNs only allow antidromic current...
  AVA showed large Vm changes in response to current injections into VA5 whereas VA5
  showed little Vm change in response to current injections into AVA."
- Label: measured (direction, in vivo paired recording). No numeric ratio reported
  (so none to label).

## Agreement / disagreement
All three sources agree on the polarity when stated in rectification terms: easier
current flow from the UNC-9 (A-MN or B-MN) side into the UNC-7 (AVA or AVB) side.
Starich 2009's explicit statement is about AVB:B, not AVA:A, and is called minimal;
Liu 2017's direct AVA:A measurement is called the strongest rectification seen in
native gap junctions, so the two differ sharply in how large/important the effect is,
not in its sign. Kawano 2011's own prose phrase ("favors AVA to A communication") reads
as the opposite direction in words, but it is a functional/behavioral inference from
calcium imaging, not a biophysical Ij measurement, and most likely reflects the separate
AVA-to-A cholinergic chemical synapse (confirmed by Liu 2017) rather than the gap
junction's own polarity. No numeric rectification ratio was found in any of the three
papers for this junction.
