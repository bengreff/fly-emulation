# Brain port: BAAIWorm and c302 run as published, then extended to the whole worm

Order (Ben via Director, 5 Nov 15:05): port the brain wholesale, run it as published first, extend to all 302
neurons, add the missing layers at general ranges, toggles for the uncertain ones, the ledger built from the
ported code's parameters. NEURON is the engine for the port; Jaxley stays the fitting path.

## 1. BAAIWorm as published (backhouse, 5 Nov)

Code: github.com/Jessie940611/BAAIWorm commit b99ca5a, Apache 2.0. Setup script
`scripts/worm/port/baaiworm_setup.sh`. Local changes to their tree, none to their numbers: a numpy stand-in for
cupy (CPU only), `ngpu = 1`, `eworm_learn/utils/{func,data_factory}.py` linked from `eworm/utils` (the shipped
tree imports them from a path that does not exist), and the test run saves its voltages.

- **(a) eworm/network/test.py, 136 neurons, untrained construction, 100 ms at dt 0.5 ms: ran, 0.61 s of
  simulation (measured).**
- **(b) the trained 136-neuron network (eworm_learn trial10, RUN_MODE test, 5 s): ran in 36.9 s wall, 1.1 GB
  (measured).** Against the shipped output `v_final_eworm_v4.npy` the traces are not identical (median per-cell
  maximum difference 22 mV; they part after 2 ms), but the published statistic is reproduced: correlation of the
  simulated voltage correlation matrix with the measured calcium correlation matrix (65 cells, 4090 pairs) is 0.70
  for our run and 0.65 for the shipped file (derived). Likely cause, not checked: `v_final` is the last training
  epoch's output, before the last weight update.
- **Finding: the trained network is not physiological.** In both our run and the shipped file 13 of the 65 output
  cells leave [-100, +60] mV; the extremes are PHAL at -1648 mV (shipped) and ALNR at -1002 mV (ours), and several
  sensory cells reach +130 mV (measured from the traces). These are the cells driven by the fitted input currents.
  The trained weights are also per-synapse fits. **Not adopted**; only the untrained construction, morphologies,
  channel densities and mods are ported. BAAIWorm's CNN muscle readout is a decoder and is not ported either.

## 2. All 302 neurons and 96 muscles, neural only: pre-registration (run `port302a`)

Pre-registered 2026-11-05 15:26 CST, before the run.

Model: `scripts/worm/port/full_network.py`. BAAIWorm's `config2detailed` with every neuron and the 96 body-wall
muscle cells (their passive muscle parameter set), their construction constants unchanged, seed 1, dt 0.5 ms,
v_init -65 mV, 6 s. Synapse sign: GABA-only presynaptic neurons inhibitory (31 neurons; Wang et al. 2024, CeNGEN
fallback for 5, none for 15 which default excitatory), all else excitatory. Reference run `port302a_allexc`: the
same with BAAIWorm's all-excitatory rule.

Stimulus (a test input, not a parameter): +20 pA at the soma of ALML, ALMR, AVM, PLML and PLMR from 2 to 4 s.
The amplitude is guessed (touch receptor currents are of order 10-100 pA).

Bars, each pass/fail, scored on `port302a` (the reference run is reported, not scored):

- **G1** every recorded soma voltage is finite for the whole run.
- **G2** every soma voltage stays inside [-100, +60] mV from 100 ms on (the trained BAAIWorm network fails this).
- **G3** the touch input reaches the network: at least one neuron that is not stimulated changes its mean soma
  voltage by >= 1 mV between 1-2 s and 2-4 s.

Reported, not scored: build and simulation wall time, seconds of wall per biological second, peak memory, the
number of synapses and gap junctions placed by kind, and how many neurons sit above -20 mV at 6 s.

What a pass means: the ported network runs at whole-worm scale without numerical failure or non-physical voltage,
and propagates an input. It says nothing about whether any cell's physiology or the network's dynamics are right.

### Result (port302a, run 2026-11-05 on backhouse, seed 1)

**G1 pass, G2 pass, G3 pass** (measured from `data/worm/brain_runs/port302a/run.npz`, kept on backhouse; `.npz` is
not in git).

- G1: every soma voltage finite for 6 s.
- G2: soma voltages from 100 ms on span -73.5 to +28.1 mV, inside [-100, +60].
- G3: 180 of the 297 neurons that were not stimulated changed their mean voltage by >= 1 mV between 1-2 s and
  2-4 s; the largest change was ALA, 4.58 mV.

Reported, not scored (measured):

- Placed connections: 4898 neuron-neuron synapses (341 made inhibitory by the transmitter rule), 2094 gap
  junction halves, 552 neuron-to-muscle and 175 muscle-to-neuron synapses; 48,202 segments.
- Cost: build 16.3 s, 42.3 s of wall for 6 s of simulation = **7.06 s of wall per biological second**, one thread,
  888 MB peak.
- **The network saturates.** Within about 100 ms most neurons settle at a depolarised fixed point and stay there:
  the median neuron's mean voltage over 1-2 s is -9.6 mV, the 90th percentile +21.8 mV, and 180 of 302 neurons sit
  above -20 mV at 6 s. Muscle voltages span -66.5 to +28.5 mV. The touch input shifts this fixed point by a few
  mV; it does not produce a travelling response. Figure: `data/worm/brain_runs/port302a/traces.png` (viewed).
- Reference `port302a_allexc` (BAAIWorm's all-excitatory rule): 186 neurons above -20 mV at 6 s; 0 muscles move by
  >= 1 mV in response to the touch input, against 18 muscles under the transmitter rule.
- c302 (OpenWorm, parameter set C2, all 302 neurons and 95 muscles, run as published, `docs/worm/research/c302_port.md`)
  shows the same picture: most neurons rise to a plateau around -15 to -5 mV by 300-500 ms and stay there.

Likely cause (inferred, not yet tested): positive feedback. BAAIWorm's excitatory synapse reverses at +30 mV and
starts to open at -20 mV, and 51 neurons have a leak reversal of -33 mV, so a neuron resting near -33 mV already
drives its targets, which depolarise and drive it back. Every one of these numbers is outside the literature range
(excitatory reversal -10 to +10 mV, B5; leak reversal -80 to -45 mV, A5). The next run (`port302b`) applies the
literature overrides recorded in the ledger (`literature_overrides` toggle on) and nothing else.

## 3. brain.py runs: reference, port302b, port302c (pre-registration)

Pre-registered 2026-11-05 16:43 CST, before any of these runs. Model: `src/wormemu/brain.py` (the brain the
closed loop uses), every number from the ledger. Script `scripts/worm/port/brain_runs.py`. All three: seed None
(the template worm), dt 0.5 ms, v_init -65 mV, 6 s, every lumped layer toggle off (neural only), the same test
input as port302a (+20 pA at the soma of ALML, ALMR, AVM, PLML, PLMR from 2 to 4 s), sign rule = transmitter.

- **ref**: literature_overrides off, wiring=baaiworm, MCVL24 kept (96 muscles, as port302a). Checks that brain.py
  builds the same network as BAAIWorm's own code did. Bar **R1**: every cell's soma voltage within 1 mV of
  port302a at every 1 ms sample.
- **port302b**: literature_overrides on (the ledger's literature clips: neuron cm A1, leak reversal A5, muscle leak
  reversal F1, excitatory reversal B5, synapse decay B3, gap junction C4; the Ca units fix with celsius 20),
  wiring=baaiworm, MCVL24 dropped (95 muscles). Nothing else changes.
- **port302c**: port302b with wiring=cook (every Cook 2019 pair at the ledger's per-EM strengths, Cook's 956
  neuron-to-muscle pairs, no muscle-to-neuron synapses).

Bars on port302b and port302c, each pass/fail: G1, G2, G3 as defined for port302a.

Hypothesis test (port302b): the cause inferred in section 2 is that values outside the literature ranges drive the
saturation. Falsifier: if 150 or more of the 302 neurons sit above -20 mV at 6 s in port302b (port302a: 180), the
overrides alone do not remove the saturation and the hypothesis is rejected as the main cause.

Reported, not scored: placed connections by kind, wall time per biological second, peak memory, neurons above
-20 mV at 6 s, the median and 90th percentile neuron mean voltage over 1-2 s, muscles moving >= 1 mV with the touch.

Adoption: wiring=cook becomes the default only if port302c passes G1-G3 and its figure has been viewed. A pass
says the Cook wiring runs and propagates; it says nothing about whether the dynamics are right.
