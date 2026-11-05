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

### Result D5 (run finished 2026-11-05 17:00 CST on backhouse; all measured)

**H-inh holds: receptor-level inhibition cuts saturation from 188 to 64 neurons above -20 mV** (falsifier line 150).
The median neuron mean over 1-2 s drops from -13.4 to -36.5 mV (90th percentile -12.7). Under the CeNGEN receptor
rule 2113 of 6301 placed chemical synapses are inhibitory (278 under the transmitter rule). The touch input now
moves 50 unstimulated neurons by >= 1 mV (3 by >= 5 mV) and 21 muscles (port302c: 9, 1, 0), still led by the
posterior-touch path (LUA, PVR, PVC, ALN). G1 and G2 pass. Figure `data/worm/brain_runs/bw_D5/traces.png` (viewed).
The rule is our own guess (receptor genes from CeNGEN, label guessed); a published polarity map is next.

## 4c. The ledger's own defaults after the template fix, and the published sign map (pre-registration)

Pre-registered 2026-11-05 17:03 CST, before the runs. Two ledger changes since D5 (commit 5b6a717): (a) guessed
templates no longer sit on a range bound (the Director's sampling fix): per-pair strengths go to the range
log-midpoint, 0.447 nS per EM synapse for chemical and NMJ (was 0.1, clipped), 0.224 nS per EM gap junction (was
0.05, clipped), and the global synapse rows at a bound go to the midpoint (exc and inh rate k 0.117 per ms, i.e.
8.6 ms decay, was 0.2 and 0.033; exc reversal 0 mV, was 10); (b) receptor_sign on now takes Fenyves et al. 2020's
published polarity where it is + or - (1705 of 3709 pairs), our CeNGEN rule elsewhere. D6 (Fenyves on the old
templates) is dropped: the old templates are no longer a ledger state. The sign effect is D7 vs D8 at equal
strengths. Base port302c (the ledger defaults; every lumped layer off), no strength scaling.

- **D7**: receptor_sign off (transmitter rule). Prediction P4 (H-strength: stronger synapses re-raise saturation):
  150 or more neurons above -20 mV at 6 s.
- **D8**: receptor_sign on (Fenyves first). Falsifier for H-inh at the new strengths: 150 or more above -20 mV.
- Both get a matching no-stim run; the touch effect is stim minus no-stim.

No strength is changed in response to these results (Thursday's bar is complete, not behaving). If D8 is saturated,
the closed loop goes ahead on the least-saturated ledger-default configuration, labelled, and saturation goes in the
ledger as an open question.

### Result D7, D8 (runs finished 2026-11-05 17:04 CST on backhouse, file times; all measured)

| Run | neurons above -20 mV at 6 s | median / p90 neuron mean 1-2 s (mV) | inhibitory chemical synapses placed | touch moves (>= 1 mV / >= 5 mV / muscles) | bar |
|---|---|---|---|---|---|
| D5 (old templates, our CeNGEN signs) | 64 | -36.5 / -12.7 | 2113 of 6301 | 50 / 3 / 21 | reported earlier |
| **D7** (new templates, transmitter signs) | **206** | -11.2 / -2.0 | 278 of 6301 | 7 / 0 / 0 | P4 (>= 150) **holds** |
| **D8** (new templates, Fenyves first) | **100** | -26.9 / -8.1 | 1946 of 6301 | 15 / 3 / 0 | falsifier (>= 150) **not met: H-inh holds** |

Moving the strengths off the bottom of their ranges (4.5x for most synapses) re-raises saturation, as predicted:
the transmitter-sign network now has 206 neurons above -20 mV. Published receptor-level signs halve it (100), but
the network is still far from a resting nervous system: in both runs it settles within 0.2 s into a fixed state
(3 neurons in D8 and none in D7 vary by more than 2 mV SD over 4-6 s), and the muscles sit tonically depolarised
(D8: 40 of 95 above -20 mV, the highest at the new 0 mV excitatory reversal). Touch reaches 15 neurons in D8, led by
LUA, PVN, PQR and PVR; in D8 three of them (LUAL, PVNL, PQR) keep a slow oscillation of about 1 s period after the
input ends. No muscle moves by 1 mV in either run. G1 and G2 pass in both. Figures `bw_D7/traces.png`,
`bw_D8/traces.png` (viewed).

**Where this leaves saturation (open):** with every value at its ledger default, the least-saturated configuration
is D8 (receptor_sign on). Neither run is tuned and none is adopted. Saturation goes in the ledger as an open question:
at literature-midpoint strengths, recurrent excitation through the Cook wiring holds a third of the neurons above
-20 mV even with published inhibition.

## 5. Range-end sensitivity at the D8 configuration (pre-registration, report-only)

Pre-registered 2026-11-05 17:08 CST, before the runs (approved by the Director, report-only). Base D8 (port302c_rs:
literature_overrides on, wiring cook, receptor_sign on, every lumped layer off, ledger defaults). One quantity at a
time is set to an end of its literature range (`brain_runs.py --set PARAM=VALUE`, every element of that row), the
rest at their defaults. Nothing found here is adopted or written into the ledger as a value; the point is which
numbers the network's state depends on, and whether saturation survives everywhere inside the ranges.

| Run | quantity (ledger row) | range (param_ranges) | ends run |
|---|---|---|---|
| S01, S02 | per-EM chemical strength (`syn_strength_per_pair`) | B4 0.1-2 nS | 0.1, 2 |
| S03, S04 | per-EM gap strength (`gap_strength_per_pair`) | C4 0.05-1 nS | 0.05, 1 |
| S05, S06 | per-EM NMJ strength (`nmj_strength_per_pair`) | B4 0.1-2 nS | 0.1, 2 |
| S07, S08 | excitatory rate k (`syn_exc_k`) | B3 decay 5-30 ms | 1/30, 1/5 per ms |
| S09, S10 | inhibitory rate k (`syn_inh_k`) | B3 | 1/30, 1/5 per ms |
| S11, S12 | excitatory reversal (`syn_exc_erev`) | B5 -10 to 10 mV | -10, 10 |
| S13 | excitatory release threshold (`syn_exc_Vth`, BAAIWorm fit -20 = top of range) | B1 -45 to -20 mV | -45 |
| S14, S15 | excitatory release slope (`syn_exc_delta`) | B2 2-10 mV | 2, 10 |
| S16 | inhibitory release threshold (`syn_inh_Vth`, fit -20) | B1 | -45 |
| S17, S18 | inhibitory release slope (`syn_inh_delta`) | B2 | 2, 10 |
| S19 | inhibitory reversal (`syn_inh_erev`, fit -70 = bottom of range) | B6-B8 -70 to -45 mV | -45 |

Measured per run: neurons above -20 mV at 6 s, median neuron mean over 1-2 s, muscles above -20 mV at 6 s, neurons
with SD > 2 mV over 4-6 s (whether anything moves). Predictions (guessed, written before the runs):
- **P5**: the chemical strength row has the largest swing of the three strength rows, and at 0.1 nS fewer than 64
  neurons sit above -20 mV (D5 had 64 at 0.1 nS with other differences).
- **P6**: the release threshold matters in the direction that releases more at rest: the BAAIWorm value -20 mV is
  already the least tonic end (release at a -55 mV rest is sigmoid(-7), about 0.1%), so S13 (exc at -45 mV, release
  at rest about 12%) raises the count and S16 (inh at -45) lowers it.
- **Q1** (reported either way): does any single range end bring the count under 30 (the level with chemical synapses
  off)? A yes would say saturation depends on where inside the literature ranges the true values lie, not that the
  model is wrong.

### Result S01-S19 (runs finished 2026-11-05 17:11 CST on backhouse; all measured; D8 = base)

| Run | set | neurons above -20 mV at 6 s | median neuron mean 1-2 s (mV) | muscles above -20 mV | neurons with SD > 2 mV, 4-6 s |
|---|---|---|---|---|---|
| D8 | (ledger defaults) | 100 | -26.9 | 40 | 3 |
| S01 / S02 | chemical strength 0.1 / 2 nS | **0** / 136 | -56.9 / -22.4 | 51 / 52 | 0 / 0 |
| S03 / S04 | gap strength 0.05 / 1 nS | 110 / 93 | -27.7 / -26.9 | 44 / 34 | 0 / 0 |
| S05 / S06 | NMJ strength 0.1 / 2 nS | 100 / 100 | -26.9 / -26.9 | 38 / 40 | 3 / 3 |
| S07 / S08 | exc k 1/30 / 1/5 per ms | 100 / 100 | -26.9 / -26.9 | 40 / 40 | 3 / 3 |
| S09 / S10 | inh k 1/30 / 1/5 per ms | 99 / 100 | -26.9 / -26.9 | 40 / 40 | 23 / 3 |
| S11 / S12 | exc reversal -10 / +10 mV | **14** / 145 | -38.1 / -20.2 | 28 / 64 | 0 / 0 |
| S13 | exc release threshold -45 mV | 143 | -20.4 | 77 | 0 |
| S14 / S15 | exc release slope 2 / 10 mV | **0** / 108 | -57.7 / -26.2 | 0 / 42 | 0 / 0 |
| S16 | inh release threshold -45 mV | **0** | -62.7 | 3 | 0 |
| S17 / S18 | inh release slope 2 / 10 mV | 105 / 93 | -25.6 / -29.9 | 43 / 41 | 3 / 0 |
| S19 | inh reversal -45 mV | 141 | -20.6 | 78 | 0 |

G1 and G2 pass in all 19. **P5 holds** (chemical strength swings 0 to 136, gap 93 to 110, NMJ none; 0 at 0.1 nS).
**P6 holds** (exc threshold at -45 raises the count to 143; inh threshold at -45 drops it to 0). **Q1: yes, four
single range ends each bring saturation under 30**: chemical strength 0.1 nS (0), excitatory reversal -10 mV (14),
excitatory release slope 2 mV (0), inhibitory release threshold -45 mV (0). So saturation is not forced by the
model's structure: it depends on where the true values lie inside ranges the literature leaves wide. Ranked by the
swing they cause in the count: chemical strength (136), excitatory reversal (131), excitatory release slope (108),
inhibitory release threshold (100), excitatory release threshold (43), inhibitory reversal (41), gap strength (17),
inhibitory slope (12); NMJ strength and both decay rates move it by 1 or less. These are the numbers whose precision
matters first. Every run is still a fixed point (no ongoing activity; only S09 has 23 slowly moving neurons): the
quiet ends are quiet, not rhythmic. Nothing is adopted; the ledger defaults stay at the range midpoints.

## 6. muscle_active: c302 C2's body-wall muscle membrane (pre-registration)

Pre-registered 2026-11-05 17:31 CST, before any run of the patched mods (Director 17:40 order: port a published
body-wall muscle model, don't write one). Boyle and Cohen 2008 (Biosystems 94:170) has no code we can use; c302 C2's
`GenericMuscleCell` is that channel set (leak, slow K, fast K, Ca with Ca-dependent inactivation, Ca pool) at c302's
published fit, and jNeuroML already generated NEURON mods for it when c302 ran as published. Vendored in
`third_party/c302/` (MIT). BAAIWorm's muscles are the same 5 x 20 um cylinder and are passive (every channel density
0), so `muscle_active=on` replaces their membrane with c302's, every value from the ledger's `c302_*` rows.

One change to the generated code, numerical only: jNeuroML writes each gate as `x' = rate_x` with the rate computed
beforehand, so NEURON's cnexp steps it as forward Euler. The Ca activation gate's time constant is 0.1 ms; at
BAAIWorm's 0.5 ms step that is unstable (the first test went NaN within 3 ms). The patched mods
(`third_party/c302/mod/`) write `x' = (x_inf - x) / x_tau`, which cnexp integrates exactly; the unchanged files are
in `third_party/c302/generated/`.

- **M1 (implementation):** at the template, every value the brain sets in the muscle mods equals c302's (the mod
  default, or for densities and the leak reversal the value in `c302_C2_Full.net.nml`), relative difference under
  1e-9. Fail = a mapping bug, fixed before anything else runs.
- **M2 (numerical port check):** one isolated c302 muscle (5 x 20 um, its membrane only), 1 s at 0 pA, then steps of
  +1, +3, +10, +30 pA for 1 s each. Patched mods at dt 0.5 ms against the unchanged mods at dt 0.025 ms (finer than
  c302's own 0.05 ms). Bar: the same number of upward crossings of -10 mV (c302's spike threshold) in every step, and
  mean V over the last 200 ms at 0 pA within 0.5 mV. Reported: largest |dV| and spike-time differences. Falsifier:
  any step's count differs; then the 0.5 ms step does not hold this muscle, and it needs a substep (reported, not
  adopted).
- **M3 (report-only):** resting V and whether the muscle fires all-or-none Ca spikes under the steps. Real body-wall
  muscle fires Ca-dependent action potentials (Gao and Zhen 2011, PNAS 108:2557; seen literature, not held out).
  Nothing is fitted to it.
- **M4 (report-only):** the D8 configuration plus `muscle_active=on`, neural only, 6 s, with its no-stim control:
  neurons and muscles above -20 mV at 6 s, muscle spikes, touch effect on muscles.
- **C1 (report-only):** the body worker's 5 s closed loop (`sample_worm(None)`, receptor_sign on) with
  `muscle_active` off and on: rhythm (activation power above the lowest bin), centroid travel. Not a crawling test;
  no bar.

### 6 results (5 Nov, 17:40 CST)

- **M1 passes.** Every value the brain sets in the muscle mods equals c302's: densities, leak reversal and the
  pool's two constants exactly as in `c302_C2_Full.net.nml` (the generated mod defaults round the pool's two to 6
  significant figures, a 5e-7 relative difference); every gate constant equals the mod default exactly. Now a test
  (`tests/test_worm_brain.py::test_muscle_active`).
- **M2 passes** (`data/worm/brain_runs/muscle_m2/`, figure `m2.png`, viewed). Patched at 0.5 ms against unchanged at
  0.025 ms: -10 mV crossings 0, 0, 1, 0, 0 in both for the 0, 1, 3, 10, 30 pA steps; the one crossing 0.8 ms apart
  (2016.5 against 2015.7 ms); mean V over the last 200 ms of each step equal within 0.002 mV; largest voltage
  difference 0.42 mV, at the onset of the 3 pA step. The patched files at 0.025 ms differ from the unchanged ones by
  at most 0.007 mV, so the patch changes the integration, not the model. The unchanged files at 0.5 ms go NaN.
- **M3: the published c302 muscle is graded, not spiking** (measured on the model). It rests at -28.6 mV; each step
  gives a small onset overshoot and then a steady plateau (-18.9, -8.4, 0.0, +7.4 mV at 1, 3, 10, 30 pA). No
  repetitive firing at any step. Real body-wall muscle fires all-or-none Ca action potentials (Gao and Zhen 2011),
  so c302's C2 fit does not reproduce that; recorded in the mechanism's notes. Its Ca-dependent inactivation
  saturates (h_ca_half 6.4e-8 mM, slope 1e-8 mM, in c302's own Ca scale), which is what NEURON's "exp out of
  range" warnings under large steps are: harmless, h_inf goes to 0.
- **M4: no change in any count** (`bw_M4`, `bw_M4_nostim` against `bw_D8`, `bw_D8_nostim`). Neurons above -20 mV at
  6 s 100 in both; neuron voltages identical (largest difference 0.0000 mV, as expected: no muscle-to-neuron
  synapses); muscles above -20 mV at 6 s 40 in both; 48 muscle -10 mV crossings in both, all in the first transient.
  The muscle voltages do change (largest 18.7 mV, median per-muscle largest 2.5 mV). Touch reaches 11 neurons and
  no muscle in either (stim minus no-stim, 2-4 s means). Reading: each muscle's NMJ synapses (0.447 nS per EM
  synapse at the template, several synapses per muscle) outweigh its own channels (about 1 to 3 nS fully open), so
  the muscle follows its tonic motor neurons whatever its membrane.
- **C1: no rhythm either way** (`data/worm/brain_runs/c1_muscle/`, figure `c1.png`, viewed;
  `scripts/worm/port/closed_loop_c1.py` runs the body worker's loop with this brain). 5 s, 18.4 s of wall each.
  Neurons above -20 mV in the last frame 103 in both. Activation is tonic after a 0.3 s rise; over the last 3 s the
  median muscle's activation SD is 0.003 (off) and 0.002 (on), and a few muscles wander slowly (largest SD 0.21 and
  0.14), with no alternating dorsal-ventral pattern. The centroid moves under 0.001 body lengths in both. The off
  run has a step at 4.35 s (one muscle to full activation) that the on run lacks; not chased.
- **Verdict:** `muscle_active` is implemented and correct as a port, stays off by default, and is not the missing
  rhythm. The rhythm question goes upstream to the motor neurons and their drive (section 7).

## 6a. Range ends from the literature (RANGE_ENDS_LIT.md): what is adopted

Written 2026-11-05 17:41 CST, before the ledger rebuild. Rule (Director 17:40): adopt only values the research file
labels measured, pre-registered. Of its measured values, two bear on a row's range; the rest are gaps, derived, model
choices, or measured in other units (Wen 2012's 0.62 is curvature per curvature, not current per curvature).

- **Adopted: `syn_exc_erev` range -10 to +10 becomes -10 to +11 mV** (param_ranges B5, bound basis measured_this_class).
  Measured: ACh-evoked current at body-wall muscle reverses at +11 mV (Richmond and Jorgensen 1999, Nat Neurosci
  2:791, Fig. 4c, n = 4); glutamate synaptic current at AVA reverses at -7.0 +/- 3.2 mV (Lindsay, Thiele and Lockery
  2011, Nat Commun 2:306, Fig. 6b). The research file calls +11 "inside the range"; it is 1 mV above it, so the upper
  end moves. The lower end stays (-7.0 - 3.2 = -10.2, within rounding of -10). By the midpoint rule the guessed
  template moves from 0 to +0.5 mV. Prediction (not a bar): D8's count of neurons above -20 mV moves by a few (the
  S11-S12 sweep gives 131 neurons over 20 mV); rerun once as D8b, report-only.
- **Not adopted, and why.** Chemical strength: 0.19 nS per quantum is derived (17.6 pA mEPSC over an assumed 91 mV
  driving force), not measured; it sits inside 0.1-2 nS. Release threshold and slope: no measurement exists (two of
  the papers say it could not be measured). Inhibitory reversal: +17 to +20 mV was measured under an imposed
  chloride gradient, not native chloride; the file itself says it is not the physiological value.
- **Consequence for the saturation question:** none of the four range ends that end saturation (chemical strength
  0.1 nS, excitatory reversal -10 mV, excitatory release slope 2 mV, inhibitory release threshold -45 mV) has a
  measured value behind it or against it. The question stays open in `ledger.json`.
- **Result (D8b, `data/worm/brain_runs/bw_D8b/`, 6 s):** 105 neurons above -20 mV at 6 s (D8: 100); touch moves 46
  neurons by 1 mV or more (D8: 44); 40 muscles above -20 mV (unchanged). As predicted, a few. D8b is the default
  configuration from here on.

## 7. gap_rectification (pre-registration)

Pre-registered 2026-11-05 17:44 CST, before any run. The toggle (off by default) makes the 86 Cook gap junction
pairs between AVA, AVB, AVD, AVE, PVC (38, 31, 1, 1, 15 pairs) and DA, VA, DB, VB rectify, in
`src/wormemu/nmodl/rectgap.mod` (ours: BAAIWorm's junction equation with a direction). Direction is measured: in
paired in-situ recordings of AVA and VA5, current passes only when VA5 is the more depolarised cell, from the motor
neuron (UNC-9 side) into AVA (UNC-7 side) (Liu, Chen, Mailler and Wang 2017, Nat Commun 8:14818). Starich et al.
2009 (oocytes) gives the same polarity and states it for AVB to B; extending it to AVD, AVE and PVC is the ledger's
class rule, inferred. Magnitude: no paper gives a ratio, so `gap_rect_ratio` stays at its inferred template, 4
(range 2-10). Choice (guessed): the preferred direction keeps the template conductance and the other direction gets
template / ratio.

- **R1 (neutral):** on with `gap_rect_ratio` = 1 is bit-identical to off on the test brain (largest |dV| = 0).
- **R2 (direction):** AVAL with DA01 and VA01 only, chemical synapses removed (weights 0), 0.4 s steps of +20 pA into
  one cell at a time. Coupling coefficient CC = (change in the other cell's V) / (change in the injected cell's V).
  Bar: with the toggle on, CC from motor neuron to AVAL is at least 0.95 of its off value, and CC from AVAL to the
  motor neuron is at most 0.6 of its off value. Falsifier: either fails.
- **R3 (report-only):** D8b plus `gap_rectification=on`, 6 s, with no-stim control: neurons above -20 mV at 6 s,
  touch effect.
- **C2 (report-only):** the 5 s closed loop (`scripts/worm/port/closed_loop_c1.py`) with the toggle on; rhythm as in
  C1. No bar.

### 7 results (5 Nov, 17:48 CST)

- **R1 misses its literal bar, and the miss is rounding.** With `gap_rect_ratio` = 1 the toggle-on brain differs
  from off by at most 1.6e-12 mV, not exactly 0. The equation is the same, but NEURON sums the two mechanism types'
  currents in a different order, so the last bits differ. The scale matches `innexin_identity`'s neutrality
  (1.7e-11 mV). Read as neutral; recorded as a miss of the bar as written.
- **R2 passes** (`data/worm/brain_runs/rect_r/summary.json`, `scripts/worm/port/rect_r.py`). AVAL, DA01 and VA01
  with chemical synapses removed, CC on/off: DA01 to AVAL 0.995 and VA01 to AVAL 1.05 (bar at least 0.95); AVAL to
  DA01 0.44 and AVAL to VA01 0.59 (bar at most 0.6; VA01 is close to the line). The DA01-VA01 coupling, which runs
  through AVAL, also drops (0.53 and 0.41).
- **R3: no change in the count** (`bw_R3`, `bw_R3_nostim` against `bw_D8b`, `bw_D8b_nostim`). Neurons above -20 mV at
  6 s 105 in both. Individual neurons move by up to 10.9 mV (PVNL, PQR, VA07, AS06). Touch reaches 13 neurons
  (D8b: 11), no muscle in either. 138 junction sites rectify.
- **C2: no rhythm either way** (`data/worm/brain_runs/c2_rect/`, figure `c2.png`, viewed). Both runs are at the D8b
  template (C1's off run predates the template change, so it was rerun as `c2_off`). Over the last 3 s the median
  muscle's activation SD is 0.0011 (off) and 0.0013 (on); 4 muscles above 0.05 in each; the centroid moves under
  0.001 body lengths.
- **Verdict:** `gap_rectification` is implemented with the measured direction and stays off by default. It is not
  the missing rhythm either.
- A unit test (`test_gap_rectification`) checks the junction currents directly: at set voltages, motor neuron to
  AVAL carries the full current, AVAL to motor neuron carries 1 / ratio of it, and the two halves conserve current.
