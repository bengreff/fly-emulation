# s23 reads: graded_rmax (N1) and the S5 body heat balance (24 Oct 2026)

Two Sonnet readers (Explore, read-only), 24 Oct 00:45-00:50 CDT. Barred: Behnia 2014, Agrawal 2020 10Bα/9Aα,
Azevedo 2020 recruitment order, docs/research/sealed/, desiccation/starvation survival times. Quotes as returned
by the readers; "secondary" marks values the reader could not check against the primary text.

## graded_rmax (N1)

Model meaning (`lif.py`): a graded cell at the top of its release range delivers `graded_rmax` spike-equivalents
per second to each partner; one spike-equivalent is what a spiking cell releases per action potential through a
synapse of the same count. So graded_rmax = (vesicle release rate per active zone at the top of the graded range)
/ (vesicles released per active zone per action potential).

- **Graded side, blowfly R1-6 → LMC (Calliphora/Musca).** de Ruyter van Steveninck & Bialek 2002 (arXiv
  physics/0202014; chapter in *Probabilistic Models of the Brain*, MIT Press), derived from measured LMC
  reliability under Poisson release: "a maximum of about 540 events per second per synaptic zone"; with a gain
  factor g ≈ 2, "540/2² = 135 vesicles per second ... lower than the rate of 240 per second reported by Laughlin
  et al. (1987)"; "each synaptic active zone should emit vesicles at a tonic rate of well over a hundred vesicles
  per second". Laughlin, Howard & Blakeslee 1987 Proc R Soc Lond B 231:437 (doi 10.1098/rspb.1987.0051) is the
  origin of 240/s (primary paywalled; secondary through two papers). Simmons & de Ruyter van Steveninck 2005
  J Neurosci 25:7529 (PMC6725398): fly photoreceptor-LMC synapses "probably operate with a few hundred small quanta
  released each second (Laughlin et al., 1987, 1998)". Anatomy: about 220 synapses per photoreceptor-LMC pair,
  about 1,320 active zones per LMC (Nicol & Meinertzhagen 1982). Comparator: goldfish bipolar ribbon 23 vesicles/s
  (Lagnado et al. 1996 Neuron 17:957). Label: derived by the authors (noise analysis), not a vesicle count.
  These are tonic rates at the light-adapted operating point, so a lower bound on the rate at the top of the
  range.
- **Spiking side, Drosophila ORN → PN (DM4, adult, in vivo).** Kazama & Wilson 2008 Neuron 58:401
  (doi 10.1016/j.neuron.2008.02.030), multiple-probability fluctuation analysis, reused in Kazama & Wilson 2009
  Nat Neurosci 12:1136 (PMC2751859): "N = 51, p = 0.79, and q = 1.05 pA". So 0.79 vesicles per release site per
  spike (univesicular binomial model). Measured (estimated by the authors).
- **Direct graded vs spiking comparison:** none usable. Burrows & Siegler 1978 J Physiol 285:231 (locust
  nonspiking local interneurons → MNs) is paywalled; the secondary summary gives release from about 2 mV
  depolarisation and no saturation value.
- **Derived value (rule, DECISIONS 24 Oct 00:5x):** 240 / 0.79 = 304 → **300 Hz**; range 135/0.79 = 171 to
  540/0.79 = 684 Hz. Label **derived** (a fly graded synapse's tonic rate over a fly central spiking synapse's
  per-spike release), applied to every graded type (inferred transfer; one shared value, no per-type knob).

## S5 body heat balance

- **No quantitative resting body-minus-ambient temperature for any insect ≤ 5 mg** in what the reader could open.
  Heinrich & Bartholomew 1974 Science 185:747 (secondary): "the body temperature of small flies in flight is
  probably close to ambient temperature". A mosquito "<1 °C" gradient in flight: snippet only, source untraced.
  Hangartner et al. 2023 Sci Rep 13 (PMC9981618): D. melanogaster IR thermography under a 25 W lamp at 0.1 m,
  16 °C incubator; only morph differences (ebony vs yellow 0.63 ± 0.19 °C, n 15 pairs); "a difference in
  temperatures between the two flies emerged after 15 s"; no absolute excess and no irradiance.
- **Digby 1955 J Exp Biol 32:279** ("Factors affecting the temperature excess of insects in sunshine"; abstract):
  excess proportional to radiation; scales as about the 1.0 power of size for Diptera-Hymenoptera; independent of
  wind below 20-30 cm/s. Full text not reached by the reader. It is the registered check (DECISIONS 24 Oct).
- **Values for the build:** none for insect tissue specific heat, density, emissivity or surface area. Body
  length about 2.5 mm (BioNumbers 100750, tertiary). Church 1960 J Exp Biol 37:186 (insect convection, dead
  specimens) abstract only. Flight power: Lehmann & Dickinson 1997 J Exp Biol 200:1133, mechanical power about
  80 W/kg muscle at 24 °C, muscle efficiency up to 10 % (flight is outside the S5 validity range).

## N1 release at rest (r0), read 24 Oct 01:20 (Sonnet reader, after m10f9c failed G)

The model's resting graded drive is release_at_rest × graded_rmax, so with graded_rmax sourced, r0 binds.
**No open full text states r0 (release at the resting or dark potential as a fraction of maximal release) for any
fly graded synapse.**
- Uusitalo, Juusola, Kouvalainen & Weckström 1995 J Neurophysiol 74:470 (blowfly R1-6 → LMC; paywalled, secondary
  summary only): release is tonic in the dark and "decreased dramatically approximately 12 mV below the resting
  potential of the presynaptic photoreceptors".
- Laughlin, Howard & Blakeslee 1987 Proc R Soc B 231:437 (paywalled, secondary only): "a presynaptic depolarization
  of 1.50–1.86 mV produces an e-fold increase in postsynaptic conductance" (slope of the transfer curve, not r0).
- Weckström & Laughlin 2010 J Neurosci 30:9557 (PMC6632427, open): the synapse operates "in the steep mid-region of
  the synaptic characteristic curve" (qualitative: the resting point is not at the foot).
- de Ruyter van Steveninck & Bialek (arXiv physics/0202014, open): transmission "completely shut down when the
  photoreceptor hyperpolarizes", at about 50 % light modulation.
- Burrows & Siegler 1978 J Physiol 285:231 (locust, **other insect**, open): "At their resting potential some
  interneurones tonically release sufficient transmitter to have a measurable post-synaptic effect."
- Zheng et al. 2006 J Gen Physiol (Drosophila LMC, open): no transfer-curve value.

**Consequence.** r0 can't be sourced from open text. The two primary sources (Laughlin 1987, Uusitalo 1995) are
paywalled; with their transfer curves, r0 at the dark rest follows from the curve read at the dark potential over
the curve's maximum. Until then N1 stays partial: graded_rmax sourced but not ON (m10f9c fails G), r0 guessed or
flyvis-fitted.
