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

### Result (runs 2026-11-05 16:45-16:49 CST on backhouse, one thread each)

All numbers measured. Figures: `data/worm/brain_runs/bw_<run>/traces.png` (viewed). Traces (`run.npz`) are not in
git; summaries are.

| | ref | port302b | port302c |
|---|---|---|---|
| R1 (within 1 mV of port302a) | **pass**, max difference 0.0 mV | - | - |
| G1 finite | pass | pass | pass |
| G2 range after 100 ms (mV) | pass, -73.5 to 28.1 | pass, -73.7 to 14.1 | pass, -66.1 to 13.2 |
| G3 as written (unstimulated neurons whose 2-4 s mean moves >= 1 mV from the 1-2 s mean) | pass, 180 | pass, 140 | pass, 155 |
| neurons above -20 mV at 6 s (port302a: 180) | 180 | **141** | 188 |
| median / 90th pct neuron mean V, 1-2 s (mV) | -9.6 / 21.8 | -20.3 / 4.2 | -13.4 / 5.3 |
| placed: chemical / gap / NMJ / muscle-to-neuron | 4898 / 2094 halves / 552 / 175 | same | 6301 / 1539 sites / 956 / 0 |
| wall s per bio-s / peak memory | 3.77 / 213 MB | 3.75 / 212 MB | 4.10 / 239 MB |

**R1: brain.py builds BAAIWorm's network exactly.** With overrides off it reproduces port302a to 0.0 mV in every cell
at every sample. It is also cheaper than the run script of section 2 (3.77 against 7.06 s of wall per bio-s, 213 MB
against 888 MB), because it records only the soma.

**G3 as written is passed by drift alone (found after scoring, not pre-registered).** Matching runs with no input
(`--no_stim`; runs are deterministic, so stim minus no-stim is the input's effect alone) "move" 180, 146 and 158
neurons by the same test. The real touch effect, as the largest |V(stim) - V(no stim)| over 2-4 s in unstimulated
neurons (`touch_effect.json`):

| | neurons >= 1 mV | >= 5 mV | muscles >= 1 mV | largest |
|---|---|---|---|---|
| ref | 1 | 0 | 0 | BDUR 1.2 mV |
| port302b | 9 | 0 | 0 | BDUR 3.1, BDUL 2.5, FLPR 2.1 mV |
| port302c | 9 | 1 | 0 | PVR 5.1, PDEL 4.7, LUAR 4.2, LUAL 4.1, PVCR 3.1 mV |

Under this stricter reading G3 still passes in all three runs (at least one unstimulated neuron moves >= 1 mV), so
the scores stand, but the input barely spreads: no muscle moves and at most 9 neurons move a millivolt. In port302c
the effect follows the anatomical posterior-touch path (PLM to PVC, LUA, PVR, PDE: Cook pairs, PVC is the forward
command interneuron). In the BAAIWorm wiring it reaches BDU, FLP and ADE (ALM partners) instead. Under Cook wiring
the touch neurons themselves depolarise far less (largest PLML change 13.8 mV against 84.4 in port302b); inferred,
not checked: Cook gives them more gap partners, so the input current leaks into more cells.

**Falsifier not triggered: 141 is below 150.** The literature overrides cut saturation from 180 to 141 neurons above
-20 mV, and the median neuron mean drops from -9.6 to -20.3 mV. So the hypothesis survives, but only partly: almost
half the network still sits depolarised and flat. The out-of-range values are one cause, not the whole cause.
Untested candidates for the rest: the synapse strengths (BAAIWorm's construction weights in port302b; the shared
template strength on every Cook pair in port302c), the slow currents and homeostasis that are off in these runs,
and graded synapses with no adaptation.

**Adopted: wiring=cook is the default** (port302c passed G1-G3, figure viewed; `build_ledger.py` default flipped,
ledger rebuilt). It saturates more than port302b (188 against 141 neurons above -20 mV), so the saturation problem
is now the brain's top open question before the closed loop.

## 4. Why the network saturates: diagnosis runs (pre-registration)

Pre-registered 2026-11-05 16:54 CST, before any of these runs. Diagnosis only: nothing here is a model change or an
adoption. Base: port302c (the current default: literature_overrides on, wiring=cook, every lumped layer off,
template worm, 6 s, same touch input). The scale factors multiply the `weight` of every placed point process of one
kind inside `scripts/worm/port/brain_runs.py`; `brain.py` and the ledger are untouched.

- **D0** chemical x0, gap x0 (every cell isolated: intrinsic resting state).
- **D1** chemical x0, gap x1.
- **D2** chemical x1, gap x0.
- **D3** chemical x0.1, gap x1.
- **D4** every connection x0 from 0 to 1 s, then x1 (does the full network leave a settled resting state?).

Hypothesis H-syn: recurrent chemical excitation holds the network in a depolarised state; the cells themselves rest
low. The graded synapse turns on around Vth = -20 mV (slope 5 mV), so a neuron above -20 mV drives its targets.
Predictions, each pass/fail, on neurons above -20 mV at 6 s (port302c: 188):
- P1: D0 < 30 (if D0 >= 150, the cells' own channels hold them up and H-syn is rejected);
- P2: D1 < 30;
- P3: D2 >= 150.

D4 is reported, not scored: if it stays below 30 the full network is bistable and the depolarised state is entered
in the start-up transient (from v_init -65 mV); if it climbs back to about 188 the depolarised state is the only
stable one at these strengths. Also reported per run: median and 90th percentile neuron mean V over 1-2 s and the
neurons sitting above -20 mV in D0 by name.

### Result (runs finished 2026-11-05 16:55 CST on backhouse, file times; all measured)

| run | neurons above -20 mV at 6 s | median / 90th pct neuron mean V, 1-2 s (mV) | prediction |
|---|---|---|---|
| port302c (base) | 188 | -13.4 / 5.3 | |
| D0 all x0 | **0** | -53.0 / -46.2 | P1 (< 30) **pass** |
| D1 chemical x0 | **0** | -55.7 / -49.8 | P2 (< 30) **pass** |
| D2 gap x0 | **173** | -15.3 / 5.6 | P3 (>= 150) **pass** |
| D3 chemical x0.1 | 0 | -55.6 / -49.5 | reported |
| D4 all off 0-1 s, then on | 188 | -13.0 / 4.2 | reported |

**H-syn holds: recurrent chemical excitation holds the network up; the cells themselves rest low** (no isolated
neuron sits above -20 mV). D4 climbs back to 188 from a settled state, so at these strengths the depolarised state
is the only stable one, not an accident of the start-up transient. Cutting every chemical weight to a tenth removes
it entirely. Next: whether the missing inhibition (glutamate-gated Cl and ACh-gated Cl receptors; the transmitter
rule makes only GABA inhibitory) is the cause, section 4b.

## 4b. Inhibition from receptor identity (pre-registration)

Pre-registered 2026-11-05 16:55 CST, before the run. Base port302c. **D5**: receptor_sign on
(each pair's sign from the postsynaptic cell's CeNGEN receptor genes for the presynaptic transmitter, a guessed rule
already in the ledger: 3262 of 3709 pairs have a CeNGEN call, 1125 flip relative to the transmitter rule). Nothing
else changes. Hypothesis H-inh: the missing receptor-level inhibition is the main cause. Falsifier: D5 has 150 or
more neurons above -20 mV at 6 s. D5 also gets a matching no-stim run so its touch effect is measured as stim minus
no-stim. If a published polarity map (Fenyves et al. 2020, PLoS Comput Biol 16:e1007974) proves usable, it is run
as D6 under the same falsifier, pre-registered by a line here before the run.
