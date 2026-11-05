# c302 full-network port (C. elegans, NEURON backend)

Run date: 2026-11-05. Machine: backhouse (Windows PC, WSL2 Ubuntu), all work confined to
`/home/greff/worm-port/c302/` as instructed. Nothing in this repo was edited to produce this; this
document plus the four CSVs/JSON/PNG under `data/worm/ported/c302/` are the deliverables.

Every number below is labelled **measured** (I generated/ran it and read it off the output) or
**c302-source** (c302's own code/data states it; I did not independently verify it against biology).

## What ran

OpenWorm's `c302` package (version 0.12.1, MIT licence) generates a NeuroML2 network from a
connectome table, then `pyNeuroML`/`jNeuroML` (1.3.22 / 0.14.0, LGPL v3) exports that network to
NEURON (hoc + mod files) and runs it. I ran the "Full" network: all 302 `C. elegans` neurons plus
all 95 body-wall muscles, parameter set **C2**.

### Parameter set choice: C2

c302 ships several parameter sets (A, B, BC1, C, C0, C1, C2, D, D1), differing in cell model
(integrate-and-fire vs Hodgkin-Huxley-style conductance-based vs multicompartment) and synapse
model (event-based vs graded/analogue). `runAndPlot.py` documents two CLI flags for running the
complete network, `-fullC1` and `-fullC2`, both at duration=1000 ms, dt=0.05 ms, NEURON backend.
I chose **C2**: single-compartment HH-like conductance-based cells, graded (analogue) chemical
synapses, electrical gap junctions, and muscle-specific NMJ synapse components defined in
`custom_muscle_components.xml` (C1 lacks the muscle-specific NMJ parameterisation). [c302-source]

### Exact commands

```
# venv setup (existing uv venv at /home/greff/worm-tools/c302_env, python 3.12, c302 0.12.1 + pyneuroml 1.3.22 already installed)
export PATH=$HOME/.local/bin:$PATH
taskset -c 0-3 uv pip install neuron==9.0.2

# generate the network (cells=all, muscles=all, parameter set C2)
cd /home/greff/worm-port/c302
python3 genfull.py
#   wraps: from c302 import c302_Full
#          c302_Full.setup('C2', generate=True, duration=1000, dt=0.05,
#                           target_directory='examples', verbose=True)

# export to NEURON and run
cd /home/greff/worm-port/c302/examples
export NEURON_HOME=/home/greff/worm-tools/c302_env
/usr/bin/time -v taskset -c 0-3 pynml LEMS_c302_C2_Full.xml -neuron -run -nogui

# post-processing (written by me, not part of c302)
python3 analyze.py     # voltage sanity checks + traces.png
python3 extract.py     # regex-parse the .net.nml into cells/connections CSVs
```

Every heavy command ran with `taskset -c 0-3` and `OMP_NUM_THREADS=4 OPENBLAS_NUM_THREADS=4
MKL_NUM_THREADS=4 NUMBA_NUM_THREADS=4 NUMEXPR_NUM_THREADS=4` set, per the 4-core budget. `uptime`
was checked before the heavy steps (load was already 18-22 from other jobs on the shared box; this
job used only its own pinned 4 cores, 142% of that budget).

### Versions [measured, from the actual venv]

c302 0.12.1, cect 0.3.5, pyneuroml 1.3.22, libNeuroML (python package `neuroml`) 0.6.7, jNeuroML
0.14.0, neuron (python) 9.0.2, OpenJDK 21.0.12.1. owmeta and owmeta_core are not installed; c302
falls back to a bundled `owmeta_cache.json` for cell morphology placement and proceeds with a
warning, not an error.

### A fix that was needed

`pynml ... -neuron -run -nogui` failed the first time with `Could not find NEURON home
directory!`. jNeuroML's Java `ProcessManager.findNeuronHome()` searches a short list of known
NEURON install layouts and doesn't recognise a pip-wheel venv install. Fix: `export
NEURON_HOME=/home/greff/worm-tools/c302_env` (the venv root containing `bin/nrniv`,
`bin/nrnivmodl`) before invoking `pynml`. The mod/hoc file generation step had already succeeded
on the first attempt; only the final compile-and-run step needed this.

### Timing [measured]

- Network setup inside NEURON: 8.63 s
- NEURON simulation itself (1000 ms model time, dt 0.05 ms): 9.12 s wall (0.152 min)
- Saving results: 11.31 s
- Whole `pynml ... -neuron -run -nogui` command (includes Java startup, mod compilation, the
  above): 51.00 s wall clock, 66.87 s user + 5.86 s sys CPU (142% of the 4-core budget), max RSS
  994 MB, exit status 0.

## Model contents

- 302 neuron populations (`GenericNeuronCell`) + 95 muscle populations (`GenericMuscleCell`) =
  397 populations. [measured, counted from the generated `.net.nml`]
- 1084 `electricalProjection` elements (all neuron-neuron gap junctions) + 2831
  `continuousProjection` elements (graded chemical synapses) = 3915 connections. Breakdown of the
  chemical connections: 2079 excitatory neuron-neuron, 200 inhibitory neuron-neuron, 428
  excitatory neuron-to-muscle (NMJ), 124 inhibitory neuron-to-muscle (NMJ). [measured]
- Connectivity data source: `cect.readers.SpreadsheetDataReader`, reading
  `CElegansNeuronTables.xls` (bundled with cect). **Important caveat**: cect's own
  `READER_DESCRIPTION` string for this exact reader reads, verbatim: *"legacy dataset (based on
  White_whole) used in the past in OpenWorm. Only included here for reference! Do not use!"*
  [c302-source / cect-source]. This is the reader c302's default Full-network generation path
  actually calls. It is **not** the Cook 2019 adjacency data; `cect.Cook2019HermReader` exists as
  an alternative reader in the same package but is not what `c302_Full.setup()` uses by default.
  Anyone treating `c302_connections.csv` as current best-estimate connectivity should know its
  source is the one cect's own authors flag as deprecated.
- Stimulus: only `PLML` and `PLMR` receive current injection (a `PulseGenerator` named
  `offset_current`), 5 pA, delay 50 ms, duration 900 ms. c302 itself calls this
  "unphysiological_offset_current" in its own parameter naming, and the C2-default version of
  this parameter group (0 pA, unused here because `c302_Full.py` overrides it) carries the source
  label `"KnownError"` with certainty `"0"` in `parameters_C2.py`. This is a built-in smoke-test
  stimulus, not a modelled sensory or physiological input. [c302-source]
- Random seed: 123456789. [measured, printed in the NEURON run log]

### Muscle naming

The 95 generated muscles are named `MDL01`-`MDL24` (24), `MDR01`-`MDR24` (24), `MVL01`-`MVL23`
(23), `MVR01`-`MVR24` (24): dorsal/ventral, left/right body-wall muscle numbering. [measured,
printed in the generation log: `Using for muscles: [...]`]. This is the standard
WormAtlas/White-et-al-era body-wall muscle naming convention also used throughout the worm
literature; Cook 2019's body-wall muscle names (e.g. `dBWML1`...`dBWML24` etc.) correspond
position-for-position (dorsal/ventral, left/right, anterior-to-posterior index) to c302's MDL/MDR/
MVL/MVR numbering. I did not find an explicit c302- or cect-authored lookup table proving an exact
id-to-id correspondence inside this install; treat the mapping above as positional/by-naming-
convention, not as a verified crosswalk file. [inferred from naming convention, not verified
against a crosswalk table]

### Cell/channel model

Both neurons and muscles are single-compartment (soma-only) HH-like cells built from the same
three active ion channel types plus leak, from Boyle and Cohen 2008:

- `Leak`: ohmic passive leak.
- `k_slow` / `k_slow_muscle`: potassium current, one activation gate (power 1), fixed
  (voltage-independent) time constant 25.0 ms, sigmoid steady state.
- `k_fast` / `k_fast_muscle`: potassium current, activation gate power 4 (tau 2.26 ms) and
  inactivation gate power 1 (tau 150.0 ms).
- `ca_boyle` / `ca_boyle_muscle`: calcium current, activation gate power 2 (tau 0.1 ms),
  inactivation gate power 1 (tau 150.9 ms), plus a calcium-concentration-dependent inactivation
  gate (c302's own `customHGate` ComponentType, not from Boyle and Cohen 2008 directly).
  c302's own code comment on the inactivation-gate slope value flags that it used -5.03 mV where
  Boyle and Cohen 2008's Table A1 gives +5 mV, citing the OpenWorm muscle-model repo's Matlab/
  Python support code as the source for the sign flip, not the paper's table directly.
- `CaPool` / `CaPoolMuscle`: simple calcium concentration dynamics (decay time + current-to-
  concentration factor rho), separate time constants for neurons (13.8 ms) and muscles (60.8 ms).

Geometry: soma length = diameter = 5 um for neurons, length 20 um / diameter 5 um for muscles.
Specific capacitance 5 uF/cm2 (neurons), 1 uF/cm2 (muscles). All these numbers, plus every channel
conductance density and reversal potential, synapse parameter, and gap-junction conductance, are
in `data/worm/ported/c302/c302_parameters.csv` (95 rows) with provenance per row.

One resolved loose end: the hoc files show axial resistivity Ra = 100 ohm.cm for both cell types,
but this is not one of the 62 bioparameters c302 exposes for level C2. Grepping
`parameters_C2.py` found it hardcoded at line 688, `Resistivity(value="0.1 kohm_cm")`, with c302's
own comment on that exact line: *"resistivity/axial resistance not used for single compartment
cell models, so value irrelevant!"*. So it is a fixed placeholder, not a fitted or measured
biological quantity, and has zero effect on these single-compartment C2 dynamics. By contrast,
the (unused, multicompartment) parameter sets D and D1 do expose a real "resistivity"
bioparameter (12 kohm.cm and 3 kohm.cm respectively), both labelled `BlindGuess` / certainty 0.1
in their own source.

### Unused-but-defined components (caveats)

- `custom_muscle_components.xml` declares five extra muscle ion channels (`slo-2`, `shk-1`,
  `egl-19`, `k_muscle`, `ca_muscle`) that are never actually inserted into `GenericMuscleCell`'s
  biophysics in this generated network (no corresponding channelDensity reference, and no .mod
  file for them was emitted by the NEURON export). They are declared but dormant for this
  configuration. [measured, by absence]
- Gap junctions: `neuron_to_muscle_elec_syn` (nonzero conductance 0.00152 nS) and
  `neuron_to_motor_delayed_elec_syn` are both defined as bioparameters in `parameters_C2.py` but
  have zero actual connections in the generated network; `muscle_to_muscle_elec_syn` is defined
  with conductance explicitly set to 0 nS (off by design). Only neuron-neuron gap junctions
  (1084 of them) are actually instantiated. [measured]

## Output sanity checks [measured]

No NaN anywhere across all 302 neuron and 95 muscle voltage traces. All values stayed within
-100 to +60 mV: neurons ranged -63.14 to 4.36 mV, muscles ranged -29.50 to -1.90 mV. Full
per-cell min/max/mean is in `data/worm/ported/c302/c302_voltage_stats.csv`.

### What the traces actually look like

`data/worm/ported/c302/traces.png` (copied from the run) shows 16 representative traces: 11
neurons (AVAL, AVBL, DA1, DB1, VA1, VB1, VD1, DD1, AIYL, ASEL, AWCL, RIML) and 4 muscles (MDL08,
MDL09, MVL08, MVL09), over the full 1000 ms. All start at rest (-60 mV neurons, about -28 mV
muscles). Most neurons rise smoothly starting around t=100-150 ms and settle into a depolarised
plateau around -15 to -5 mV by t=300-500 ms, then stay flat for the rest of the 1000 ms run; a
few (AIYL, ASEL, AWCL, RIML) rise later and more gradually, reaching plateau around t=400-600 ms.
The four muscle traces show a sharper transient: a rise, then an overshoot/spike around t=250 ms,
then relaxation down to an intermediate depolarised plateau that holds for the remaining 700+ ms.
Nothing oscillates or bursts repeatedly anywhere in the 1000 ms window, despite the 900 ms-long
PLML/PLMR current injection still being active throughout most of it.

**Caveat worth carrying forward**: driven only by the Full config's built-in PLML/PLMR test
current, the network does not produce rhythmic, locomotor-like activity. It produces one
widespread, roughly saturating depolarisation across nearly the whole network. This is good
evidence the network is correctly wired and excitable (nothing diverges, nothing stays silent),
but it is not evidence of a validated locomotor pattern, and the driving stimulus itself is
explicitly unphysiological by c302's own labelling.

## What this port does and doesn't give you

**Gives you**: every passive, channel, synapse, gap-junction and stimulus parameter c302's C2
parameter set uses for the full network, with values read directly from the generated NEURON
code (not just the Python bioparameter dump, which is missing some values such as Ra that only
appear in the generated hoc); the full connection list (pre/post/kind/component/weight) for 3915
connections; per-cell type assignment for all 397 cells; a reproducible run with all intermediate
files preserved on backhouse.

**Does not give you**: Cook 2019 connectivity (this reader uses the older, cect-flagged-as-
deprecated spreadsheet instead); any confirmation that the C2 parameter values are good
biological estimates (c302 itself labels nearly all of them `"BlindGuess"` with certainty 0.1 in
`parameters_C2.py` -- only the three stimulus-override values carry a different, also weak,
label); any locomotor/behavioural validation (the one test stimulus run here saturates the
network rather than producing rhythmic output); a verified muscle-id crosswalk to Cook 2019
naming (positional correspondence only, not a confirmed lookup table).

## Files left on backhouse (not deleted, per instructions)

All generated NeuroML/LEMS/hoc/mod/data files remain at
`/home/greff/worm-port/c302/examples/` (and `/home/greff/worm-port/c302/genfull.py`,
`generate.log` one level up). Sizes in bytes:

```
LEMS_c302_C2_Full.xml              97275
LEMS_c302_C2_Full_nrn.py         5245471
c302_C2_Full.net.nml             1556311
cell_C.xml                          4961
custom_muscle_components.xml       12791
custom_synapses.xml                12339
GenericNeuronCell.hoc               4033
GenericMuscleCell.hoc               4033 (4013)
Leak.mod                            2195
k_slow.mod / k_slow_muscle.mod      5729 / 5778
k_fast.mod / k_fast_muscle.mod      8368 / 8417
ca_boyle.mod / ca_boyle_muscle.mod  9971 / 10019
CaPool.mod / CaPoolMuscle.mod       2757 / 2777
neuron_to_neuron_elec_syn.mod       1849
neuron_to_neuron_exc_syn.mod        3281
neuron_to_neuron_inh_syn.mod        3266
neuron_to_muscle_exc_syn.mod        3285
neuron_to_muscle_inh_syn.mod        3267
offset_current.mod                  1696
silent.mod                          1757
c302_C2_Full.dat                 84811949
c302_C2_Full.activity.dat        78803940
c302_C2_Full.muscles.dat         26881344
c302_C2_Full.muscles.activity.dat 24981249
time.dat                           160008
run_neuron2.log                   583889
analyze.py / analyze.log / traces.png / voltage_stats.csv / cells_extract.csv / connections_extract2.csv  (my own post-processing scripts/outputs)
x86_64/   (compiled NEURON mod-file object directory from nrnivmodl)
```

generate.log (58681 bytes) lives at `/home/greff/worm-port/c302/generate.log`.
