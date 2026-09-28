# Batched GPU simulator

Status (session 10, 27 September 2026): **built and equivalence-tested, brain only (open loop).**
Not yet used in any claimed result, and not yet coupled to the body. It is the first
item of CONSTRUCTION.md "Afterwards (search)".

## What it is

`src/flyemu/gpu/batched.py`, class `BatchedNetwork`. It runs B parameter variants
("members") of one connectome at the same time in JAX. It reproduces
`flyemu.lif.Network.step`, which remains the CPU reference.

```python
from flyemu import lif
from flyemu.gpu.batched import BatchedNetwork
net = lif.Network(conn, params, 0.1)            # the reference, built as usual
g = BatchedNetwork(net, B=32, member={          # absolute per-member values, (B, n)
    "release_gain": rel, "input_gain": inp, "spont_mv": spont})
r = g.run(10_000, external_mv=ext, kicks=(stim_idx, 100.0, kick_mv), record=readout_idx)
counts = g.spike_counts()                        # (B, n) since reset()
```

- **Per-member parameters** (`MEMBER_PARAMS`): release_gain, input_gain, spont_mv,
  v_rest, v_th, v_reset, tau_m, t_ref, tau_s, adapt_mv, tau_adapt, std_u,
  std_tau_rec. Any of these may be a (B, n) array. Delays, weights and the
  graded/spiking split are shared by all members.
- **Weights are shared.** lif.py folds release_gain[pre] × input_gain[post] into each
  edge. Here W is the reference network's weights, and each member carries two
  relative vectors: release_b/release_ref multiplies the presynaptic output, and
  input_b/input_ref multiplies the summed input. Because both gains factor per
  cell, the product is the same; only the float32 rounding differs. A per-class
  search (circuit_class → per-neuron vector) fits this form directly.
  Per-*edge-class* scalings (e.g. FLYEMU_EDGE_SCALES) do not factor; they must be
  baked into the reference network and are then shared by all members.
- **Delays.** A ring buffer holds the last D presynaptic output vectors y (D = max
  delay = 41 steps in m4). Each step gathers, per presynaptic cell, its y from its
  own delay ago; graded cells use delay 1, as in lif.py. This fuses the "delay
  buckets" into one gather, so the input is one sparse product per step for any
  number of distinct delays.
- **Sparse activity.** m4 is quiet: about 1–15 spikes and 0–600 depolarised graded
  cells per step. Each step therefore first tries an *event path*. It expands only
  the outgoing edges of presynaptic cells whose output is nonzero in any member,
  within fixed capacity tiers (`DEFAULT_TIERS = ((1024 cells, 16384 edges),
  (4096, 65536))`). A step that exceeds every tier falls back to the dense product
  over all 6.08 M edges, with the same semantics. The tests cover all three paths.
- **Time.** Refractory ends are compared exactly as lif.py does: t_ms is
  accumulated as a Python float and compared in float32. `run()` precomputes that
  sequence on the host.

### Mechanisms

| Mechanism | Status |
|---|---|
| Exponential-Euler LIF, refractory period, reset, `syn_reset_on_spike` | ported (on in m4) |
| Per-presynaptic-type conduction delays | ported (on in m4; 5–41 steps) |
| Graded (non-spiking) transmission, one-step delay | ported (on in m4; 11,420 cells) |
| Tonic drive `spont_mv` (includes any class tonic drive folded into it) | ported (on in m4), per member |
| `external_mv` (constant per `run` call), `kick` (held while refractory), `silence` (per member) | ported |
| Glutamate sign per target, CX ring class normalisation, FLYEMU_EDGE_SCALES | inherited through the reference weights (static) |
| Spike-frequency adaptation | ported (off in m4); toy-tested |
| Short-term depression (incl. ORN / leg afferent depression switches) | ported (off in m4); toy-tested |
| GABA-B slow path | ported (off in m4); toy-tested |
| N7/N8 slow channels: mGluR, mAChR, NMDA-type with Mg block (`net.chan`) | ported (off in m4); toy-tested, exact raster |
| N3 class noise (`noise_class_mv`) | ported, own RNG (off in m4) |
| N2/N3/N5 class threshold offset, tau_m scale, tonic drive, release/input scale | inherited: they are folded into v_th, tau_m, spont_mv, release_gain, input_gain; any of those can also vary per member |
| N1 class modes (graded or spiking) | inherited from `net.graded` (shared by all members) |
| Neuromodulator pools (gain on arriving fast input) | ported (inert in m4: sensitivities 0); toy-tested |
| Identified electrical synapses (`net.elec` kicks; N12, wired into the Organism in s10) | ported; toy-tested |
| Membrane noise | ported with JAX's own RNG: equivalent only in distribution, not per draw (m4 noise = 0) |
| Conductance-based synapses (`cond`) | **NotImplementedError** |
| Presynaptic inhibition of sensory terminals (`presyn_inh_gain > 0`) | **NotImplementedError** |
| KC→MBON plasticity: DAN-gated depression (`kc_mbon_eta`) and N21/N22 timing rules and forgetting | **NotImplementedError** (the weights change during the run; this needs a per-member copy of the ~KC→MBON edge block) |

## Equivalence (measured, backhouse RTX 4070 Ti SUPER, JAX 0.11.1 CUDA 12)

Whole CNS, m4 brain only: 167,111 neurons and 6,078,541 nonzero edges (6,241,231
edges, minus zero-sign ones, plus graded rows). Noise is 0. The stimulus is a fixed
kick schedule. `sugar` is Poisson kicks at 100 Hz into LB3b/LB3c. `broad` adds kicks
at 20 Hz into a random 3% of all cells, plus 4 mV into every ORN. Member 0 has the
reference parameters. Member 1 has per-cell-type random factors in [0.8, 1.2] on
release_gain, input_gain and spont_mv; its CPU comparison is a separate lif.Network
built with those absolute values.

| Stimulus, duration | Member | CPU spikes | GPU spikes | Raster | Rate corr / max \|Δ\| |
|---|---|---|---|---|---|
| sugar, 500 ms | reference | 4,938 | 4,938 | identical, every step | 1.0 / 0 Hz |
| sugar, 500 ms | class gains | 4,096 | 4,096 | identical | 1.0 / 0 Hz |
| broad, 500 ms | reference | 58,381 | 58,381 | identical | 1.0 / 0 Hz |
| broad, 500 ms | class gains | 66,128 | 66,128 | identical | 1.0 / 0 Hz |
| broad, 2000 ms | reference | 234,648 | 234,648 | identical (7,118 active cells) | 1.0 / 0 Hz |
| broad, 2000 ms | class gains | 278,962 | 278,962 | identical | 1.0 / 0 Hz |

Run twice: first on lif.py as of session start, then again on lif.py at commit 03f2608
(session-10 class mechanisms present and neutral). The results were identical.
Files: `runs/gpu_equiv/*.json` on backhouse.

Float32 summation order differs, so membrane potentials differ in the low bits
(toy network: max |ΔV| ≈ 1e-4 mV after 300 ms). Over these windows no spike moved.
On the toy network with every optional mechanism on at once (adaptation, STD, GABA-B,
modulators, electrical synapses), one spike moved by one step at t = 195.8 ms; each
mechanism alone matched exactly. Expect rare one-step shifts that grow in chaotic
regimes; judge long runs by statistics.

**Determinism.** GPU scatter-adds use atomics. Two identical GPU runs of `broad` ended
with membrane potentials that were not bitwise equal; spikes still matched the CPU.
`sugar` reruns were bitwise equal. `XLA_FLAGS=--xla_gpu_deterministic_ops=true` ran out
of memory (it requested 5–8 GB buffers), so it is not usable as is.

## Throughput (measured; the GPU was shared with another ~50%-utilisation process, so these are pessimistic and noisy ±30%)

Wall time per simulated second, whole CNS, dt = 0.1 ms, default tiers; the run is
split into 250 ms `run()` calls.

| B | sugar: wall s / sim s | per member | broad: wall s / sim s | per member |
|---|---|---|---|---|
| 1 | 2.1 | 2.1 | 1.4 | 1.4 |
| 8 | 4.9 | 0.61 | 7.2 | 0.90 |
| 32 | 12.2 | 0.38 | 13.3 | 0.42 |
| 64 | 23.4 | 0.37 | 28.8 | 0.45 |

- **CPU reference, same machine** (lif.Network alone, one process, backhouse WSL):
  sugar 10.6–19.8 s and broad 24–39 s of wall time per simulated second. The range
  reflects how many other model processes were running on the box.
  For comparison, the whole organism on the Mac M2 Pro takes ≈ 50 s per simulated second.
- **Speed-up** per member at B = 32–64: about 30–50× (sugar) and 55–90× (broad) over
  one CPU process.
- **Dense path only** (`--tiers '[]'`), for comparison: 0.7–0.9 ms/step at B = 1 and
  1.6–1.9 ms/step at B = 32.
- **Bottleneck.** At B ≥ 32 the cost is mostly elementwise state traffic (≈ 0.7 ms/step
  at B = 32 with no synaptic input at all), not the synapses. Further gains would come
  from fusing and shrinking per-step state (counts, kick buffer, the switch output),
  not from the sparse product.
  - Tried and reverted: a compact per-cell "active" ring buffer, so that finding
    active cells avoids reading the (n, B) output history. It gave no measurable gain.
  - Next step: profile one step with `jax.profiler` or nsys before optimising further.
- **Compile time:** 1.5–7 s per (B, stimulus shape).
- **Memory:** the delay ring buffer is D × n × B × 4 bytes (0.9 GB at B = 32). B = 64
  ran; XLA logged failed 4 GB speculative allocations but completed.

## Backend choice

**JAX with CUDA 12** (`jax[cuda12]==0.11.1`) in a separate venv on backhouse,
`~/fly-emulation/.venv-gpu`, so `uv sync` and uv.lock are untouched. It contains
numpy 2.5.3, scipy 1.18.1, pandas 3.0.5 and pyarrow (the same versions as the Mac
venv), pytest, and jax[cuda12].

Measured on a random 167k × 167k matrix with 6.24 M nonzeros:
- a sorted `segment_sum` took 0.6–1.1 ms for B = 8–64;
- `jax.experimental.sparse` BCSR (cuSPARSE) took 6–9 ms;
- BCOO took 1.6–7.5 ms.

Hand-written gather/segment-sum plus the event path was therefore used. PyTorch was
not needed: the bottleneck is elementwise state, which any framework pays. On the Mac,
`jax==0.11.1` (CPU) was installed into the project venv with `uv pip` for the tests;
it is not in pyproject.toml, so the test skips where JAX is absent.

## Reproduce

```bash
uv run pytest -q tests/test_gpu_batched.py            # Mac, JAX CPU, toy network, ~5-15 s
scripts/sync_backhouse.sh
# on backhouse (pipe via: ssh backhouse 'wsl -d Ubuntu -- bash -s' < job.sh)
cd ~/fly-emulation && export XLA_PYTHON_CLIENT_PREALLOCATE=false
.venv-gpu/bin/python scripts/gpu_bench.py equiv --ms 500 --stim sugar    # -> runs/gpu_equiv/*.json
.venv-gpu/bin/python scripts/gpu_bench.py equiv --ms 2000 --stim broad
.venv-gpu/bin/python scripts/gpu_bench.py bench --batch 1,8,32,64 --ms 1000 --stim broad
.venv-gpu/bin/python scripts/gpu_bench.py cpu --ms 500 --stim broad     # CPU reference speed
# recreate the venv if missing:
~/.local/bin/uv venv .venv-gpu --python 3.12.3
~/.local/bin/uv pip install -p .venv-gpu numpy==2.5.3 scipy==1.18.1 pandas==3.0.5 pyarrow pyyaml pytest "jax[cuda12]==0.11.1"
```

## Known issues and findings

- lif.py's `Network.silence` did not remove the GABA-B slow path. The main session
  fixed this during s10. The GPU silences every path by zeroing the presynaptic output.
- Graded presynaptic cells have no GABA-B slow path, as in lif.py (documented there).
- `external_mv` is constant within one `run()` call. `run(..., ext_rows=S)` takes
  values for the rows S only (tested equal to a dense input). A closed loop would
  call `run(k, ...)` once per window (below).
- `step()` exists for convenience, but it costs one dispatch per 0.1 ms step (slow).
- The Poisson-kick generator on the device is independent per member. It is
  statistically, not per-draw, equivalent to assay_pathways.py's host RNG.
- Unverified: behaviour of tier overflow under runaway activity (the dense fallback
  is tested on the toy network only), and the throughput of a heavily active regime
  (the most active case measured is broad, ~13 spikes/step).

## Closed-loop coupling: design note (not built)

The Organism loop per 0.1 ms step is: body.observe → sense (afferent drive, an
n-vector nonzero only on sensory rows) → net.step → motor spikes → nm.step
(+ Hill muscles) → body.step. To run B bodies with the batched brain:

1. **Fixed channel index sets.** Take S as the union of the rows that aff, vis, chem
   and extra can write (a few thousand sensory cells) and M as the motor units
   (`nm.mn_index` plus grip cells). Only a (B, |S|) float32 sensory block goes to the
   device, and only (k, B, |M|) spike bits come back, so no n-vector crosses the bus.
2. **Exchange every k steps.** `run(k, external_mv=(B, |S|), ext_rows=S)` (implemented) holds the sensory
   drive for the window; the host then replays the k motor-spike steps through each
   member's nm.step/body.step. k = 1 is exact but costs one dispatch
   (~30–100 µs) plus a transfer per 0.1 ms step; that alone is ≥ 1 s per simulated
   second, before the bodies run. k = 10 (1 ms) adds up to 1 ms of sensory and motor
   latency. Modelled conduction delays are 0.5–4 ms, and graded cells transmit in one
   step, so the hold is **not** invisible. It must be validated: run the CPU Organism
   with the same k-step sensory hold and compare closed_loop_check metrics and
   sugar→MN9 across k = 1, 5, 10 on seeds 0–2. The GPU loop is then
   equivalence-tested against the CPU k-hold loop, not against k = 1.
3. **Bodies on CPU.** Step the B MuJoCo bodies in a pool of processes (28 threads on
   backhouse) with shared-memory sensory and motor blocks. Ping-pong two half-batches
   so that the GPU integrates half A while the CPU steps the bodies of half B; each
   half's own loop stays causal.
   - Measure first: flybody step cost per member, and vision rendering (every
     `sample_every` steps per member; likely the most expensive sense).
4. **Later option:** bodies on the GPU with MJX, to put the whole loop in one jit. Blocked
   on whether flybody's adhesion actuators and contact settings are supported in MJX;
   check before investing.
5. **Open-loop assays** (sugar→MN9, pathway assays, silencing screens) need none of
   this and can use `run()` now. They are the natural first search targets.
