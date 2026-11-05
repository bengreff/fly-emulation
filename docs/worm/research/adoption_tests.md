# Adoption install tests on backhouse (CPU, threads capped)

Run 2026-11-04 (date checked before writing). All work under `~/worm-tools/` on backhouse (WSL Ubuntu, user
greff). Every launched process sets `OMP_NUM_THREADS=4 OPENBLAS_NUM_THREADS=4 MKL_NUM_THREADS=4
NUMBA_NUM_THREADS=4 NUMEXPR_NUM_THREADS=4` and runs under `taskset -c 0-3`. Load checked before each run
(`uptime`); started at load ~21 (below the 24 wait bar).

Status: **in progress - this file is being filled as each tool is tested.**

## Summary table (fill in as completed)

| Tool | Version/commit | Installs | Runs | Speed (stated config) | Licence | Fidelity notes |
|---|---|---|---|---|---|---|
| NEURON | 9.0.2 (pip wheel) | Y | Y | 1-compt HH: 1 s sim in 0.21 s wall; 100-compt cable: 1 s sim in 0.55 s wall (dt=0.025 ms, taskset -c 0-3, 4 threads capped) | BSD 3-Clause (per neuron.yale.edu / github.com/neuronsimulator/nrn; not independently re-read from a LICENSE file in the pip package, which ships no LICENSE file) | Multicompartment Hodgkin-Huxley cable equation solver, standard `hh` mechanism (Na/K/leak) and custom NMODL mechanisms; the long-standing reference simulator this whole field cites |
| Arbor | 0.12.2 (pip wheel) | Y | Y | 1-compt HH: 1 s sim in 0.0074-0.0081 s wall; 100-compt cable: 1 s sim in 0.0048 s wall (dt=0.025 ms, 4 threads) | BSD 3-Clause (LICENSE file shipped in the pip package, read directly) | Multicompartment cable equation solver, same `hh` density mechanism concept as NEURON; built for HPC/vectorized backends - noticeably faster than NEURON on this same small test (about 25-70x in these two toy cases), but API differs (units-typed quantities, no hoc) |
| OpenWorm c302 | c302 0.12.1 + pyneuroml 1.3.22 + jNeuroML 0.14.0 | Y | Y | C2 IClamp config (2 neurons ADAL/PVCL + 1 muscle MDR01): generate 1.4 s; simulate 6 simulated s (120,000 steps, dt=0.05 ms) in 5.5 s jLEMS time, 8.1 s wall incl. JVM start -> roughly real-time to ~0.7x real time for this tiny network | c302: MIT (LICENSE file read). pyneuroml: LGPL v3 (LICENSE.lesser file read). jNeuroML/jLEMS: not re-checked this pass (bundled jar) | Generates NeuroML2 point-neuron-ish network models (leaky-integrator style per-cell dynamics, not full multicompartment HH) from a connectivity spreadsheet (`cect` package, formerly owmeta); simulated via jLEMS (Java). This is a network/connectome tool, not a single-neuron biophysical fitting tool - channel detail is much lower than NEURON/Arbor/the Nicoletti models |
| Sibernetic | github openworm/sibernetic, commit at clone time 2026-11-04 (shallow clone, no tag) | Partial (compiles, link not completed) | N | N/A - OpenCL unavailable on this box regardless of build outcome | MIT (LICENSE file read directly) | SPH (smoothed-particle hydrodynamics) body-mechanics simulator with an OpenCL compute backend and an attached neuron/muscle signal layer (`owNeuronSimulator`, `owSignalSimulator`); models the worm's physical body and musculature, not single-neuron channel biophysics |
| BAAIWorm/MetaWorm | github Jessie940611/BAAIWorm, shallow clone 2026-11-04; `eworm` submodule only (NEURON mod mechanisms + pure-Python network builder); `neuronXcore` (C++/OptiX 3D viewer) and Boost build **not attempted** | Y (eworm only) | Y (eworm only) | 136-cell detailed multicompartment network, 100 ms simulated (dt=0.5 ms, 200 steps) in 0.65 s wall -> about **0.15x real time** (slower than real time) on 4 threads | Apache 2.0 (LICENSE file read directly) | `eworm` builds NEURON multicompartment cells (channels: egl-19, unc-2, slo-1, slo-2, egl-2, egl-36, irk, kcnl, kqt-3, kvs-1, nca, shk-1, shl-1, plus gap junctions and exc/inh synapse mechanisms - full gene-named channel set, confirmed from the compiled `.mod` file list) wired by a full adjacency-matrix connectome (136 cells reached from an 8-cell input set); this is the real single/few-neuron-detail layer, separate from the GPU/OptiX 3D body-and-environment layer which was not tested |

## Details

### 1. NEURON (pip `neuron` 9.0.2)

Commands:
```
uv venv neuron_env --python 3.12
source neuron_env/bin/activate
uv pip install neuron
```
Install: clean, ~18 s (7 packages, incl. numpy 2.5.4, sympy). `python -c "import neuron; print(neuron.__version__)"` -> `9.0.2`.

1-compartment HH test: single `Section`, `insert('hh')`, L=diam=18.8 um, IClamp 0.1 nA for 1 ms, dt=0.025 ms,
`h.continuerun(1000)` (1000 ms = 1 simulated second). Wall time 0.209 s -> **about 4.8x real time** on 4 threads.

100-compartment cable: 100 sections chained end-to-end (L=10 um, diam=1 um, nseg=1 each, all `hh`), IClamp at
one end, 1 simulated second. Wall time 0.549 s -> **about 1.8x real time**.

Licence: BSD 3-Clause, per the project's own site (neuron.yale.edu) and GitHub (`neuronsimulator/nrn`); the pip
wheel itself ships no LICENSE file in the installed package directory, so this is sourced from the upstream
project page, not re-read locally - flag before any formal reuse decision.

Fidelity: full multicompartment cable equation with Hodgkin-Huxley-style conductances via NMODL mechanisms;
this is the same model class (and largely the same `.mod` format) used by both Nicoletti papers' GitHub code
found in Part 1. Good candidate to directly run those repos' `.py`/`.mod` files once cloned.

---

### 2. Arbor (pip `arbor` 0.12.2)

Commands:
```
uv venv arbor_env --python 3.12
source arbor_env/bin/activate
uv pip install arbor
```
Install: clean, ~9 s (numpy + arbor 36.7 MB wheel).

1-compartment HH: single cylindrical segment (18.8 x 18.8 um, matching the NEURON test geometry), `hh` density
mechanism, i_clamp 0.1 nA for 1 ms, dt=0.025 ms, 1 simulated second. Wall time 0.0074-0.0081 s (two runs) ->
**about 125-135x real time** on 4 threads.

100-compartment cable: 100 chained segments (10 um long, 1 um diameter each), default discretization (one
control volume per segment), i_clamp 0.5 nA at one end, same dt, 1 simulated second. Wall time 0.0048 s ->
**about 210x real time**.

Note: Arbor's numbers here are 25-70x faster than NEURON's on the same toy problems. This is plausible given
Arbor is designed for vectorized/HPC execution, but the two tests are not controlled for identical adaptive-step
behaviour or identical effective time constants, so treat this as a rough install/smoke-test comparison, not a
benchmark - a fair comparison would fix identical mechanisms, identical solver tolerances, and profile properly.

Licence: BSD 3-Clause - read directly from the `LICENSE` file shipped inside the installed pip package
(`arbor_env/lib/python3.12/site-packages/arbor/LICENSE`), copyright ETH Zurich and Forschungszentrum Julich.

Fidelity: same class of model as NEURON (multicompartment cable equation, NMODL-style density mechanisms via
Arbor's own mechanism catalogue). Newer codebase, actively developed, built for large-scale/GPU-ready network
simulation - worth a second look if the project later needs many-cell network speed rather than single-neuron
fitting.

---

---

### 3. OpenWorm c302 (pip `c302` 0.12.1 + `pyneuroml` 1.3.22)

Java was already present on backhouse WSL (`openjdk 21.0.12.1`), so no user-local JDK tarball was needed.

Commands:
```
uv venv c302_env --python 3.12
source c302_env/bin/activate
uv pip install c302 pyneuroml
cp c302_env/lib/python3.12/site-packages/c302/c302_IClamp.py .
python c302_IClamp.py C2        # generates NeuroML2 + LEMS files for parameter set C2
pynml examples/LEMS_c302_C2_IClamp.xml -nogui   # runs via bundled jNeuroML jar
```
Install pulled in `cect` (the current name for the old `owmeta`-based connectome reader) and a long dependency
chain (pandas, numpy, matplotlib, h5py, pymongo, etc) - about 90 packages, no errors. `owmeta` itself is not
installed and c302 prints "owmeta not installed! Proceeding anyway" - it falls back to a bundled cache
(`c302/data/owmeta_cache.json`) and the `cect.readers.SpreadsheetDataReader` reading
`c302/data/CElegansNeuronTables.xls`, so this is not blocking.

Ran the **C2** parameter set (smallest of the `A/B/C/C0/C1/C2/D/D1` sets that ships an `IClamp` example) with
cells `['ADAL','PVCL']` and muscle `MDR01` (the example's hardcoded default list) - generation took 1.4 s wall;
jNeuroML simulation of the resulting network (6 simulated seconds, 6 x 1 pA-6 pA current steps, 120,000 steps at
dt=0.05 ms) took 5.5 s of jLEMS run time, 8.1 s wall including JVM startup (`java -Xmx400M`). That is **close to
real-time for this 2-cell + 1-muscle network** (0.7-1.1x depending on whether JVM startup is counted).

Licence: `c302` MIT (LICENSE file inside the installed dist-info, read directly, (c) 2024 OpenWorm). `pyneuroml`
LGPL v3 (`LICENSE.lesser` file read directly). The bundled `jNeuroML-0.14.0-jar-with-dependencies.jar` licence
was not independently re-checked this pass.

Fidelity: c302 builds point/few-compartment NeuroML2 cell models from a connectome spreadsheet
(`CElegansNeuronTables.xls`) and simulates with jLEMS - it is a **network-level, not single-neuron-biophysics**
tool. Per-parameter-set, the biophysical detail is a leaky-integrator-style dynamic (not full HH channel
kinetics), so this is not itself a route to a validated single-neuron conductance model, but it is a cheap way
to get a whole-connectome-shaped network running for comparison/sanity checks.

Cleanup: deleted `~/worm-tools/c302_run` output files (dat files, ~14 MB total) after the timing was recorded.

---

---

### 4. Sibernetic (github openworm/sibernetic)

Licence: MIT (`LICENSE` file read directly after clone, (c) 2011/2013/2014 OpenWorm).

**OpenCL availability on backhouse WSL - checked first, precisely:**
- `clinfo` is not installed and there is no `/etc/OpenCL/vendors` directory (the standard ICD registration
  location) - confirmed by direct `ls`.
- No `libnvidia-opencl.so*` is exposed into WSL. `/usr/lib/wsl/lib` (the directory WSL uses to expose
  Windows-host GPU paravirtualization libraries) contains `libcuda.so*` and D3D12 interop libs, but no NVIDIA
  OpenCL runtime library - confirmed by directory listing.
- A CUDA toolkit (13.3) happens to be installed and ships its own `libOpenCL.so.1.0.0` (package
  `cuda-opencl-13-3`), registered in `ldconfig -p`. Installed `pyopencl` (2026.1.4, pip) in a throwaway venv to
  test it directly:
  ```
  python -c "import pyopencl as cl; cl.get_platforms()"
  -> pyopencl._cl.LogicError: clGetPlatformIDs failed: PLATFORM_NOT_FOUND_KHR
  ```
  This is the precise failure: a working OpenCL *runtime library* exists, but no OpenCL *platform* is
  registered for the loader to find, with or without a hand-built `OCL_ICD_VENDORS` override pointing straight
  at that library (tried, same failure).
- **What would fix it:** root-level setup of `/etc/OpenCL/vendors/nvidia.icd` pointing at a working NVIDIA
  OpenCL platform library, which in turn needs WSL's GPU paravirtualization layer to expose
  `libnvidia-opencl.so` (it currently only exposes `libcuda.so`, i.e. CUDA, not OpenCL, from the Windows host
  driver) - this is a Windows-host NVIDIA driver / WSL GPU driver configuration question, not something fixable
  from inside this unprivileged WSL user account. No sudo is available on this box per the project's own rules,
  so this was not pursued further.
- Also relevant: at the time of this check the GPU was at **99% utilisation, 14.4-15.7 GB / 16.4 GB VRAM used**
  by another user's job (confirmed via `nvidia-smi`) - even if OpenCL worked, this was not a good moment to run
  a GPU job on this shared box.

**Build attempt (CPU-side compilation, no root):**
- Cloned `github.com/openworm/sibernetic` (398 MB after clone, mostly example/test data).
- First `make` failure: `inc/owOpenCLSolver.h` includes `<CL/cl.hpp>`, but the repo's bundled C++ OpenCL header
  actually ships at `inc/OpenCL/cl.hpp` (not `inc/CL/cl.hpp`) - a path-naming mismatch inside the repo itself.
  Worked around with a local symlink inside the cloned checkout: `ln -s OpenCL inc/CL` (no system change).
- Next failures: missing system headers `GL/gl.h`, `GL/glut.h`, `CL/opencl.h` - none of `freeglut3-dev`,
  `libglu1-mesa-dev`, `libglew-dev`, `mesa-common-dev`, `libglut-dev`, `libgl-dev`, `opencl-c-headers`,
  `opencl-clhpp-headers`, `ocl-icd-opencl-dev` were installed, and this account has no sudo (`sudo -n true` ->
  "a password is required"). Worked around **without root** using `apt-get download <pkg>` (downloads the
  `.deb` without installing) followed by `dpkg-deb -x <pkg>.deb local_deps/extracted/` (unpacks the package
  contents to a plain directory) for all of the above, then pointed the compiler at that directory via
  `C_INCLUDE_PATH` / `CPLUS_INCLUDE_PATH` / `LIBRARY_PATH`. Two of the extracted `-dev` packages (`libgl-dev`,
  `ocl-icd-opencl-dev`) shipped **dangling** unversioned `.so` symlinks (e.g. `libGL.so -> libGL.so.1` with no
  `libGL.so.1` actually in the package - that file belongs to a separate runtime package not installed); fixed
  by re-pointing those two symlinks at the real system-wide `.so.1` files that do already exist
  (`/lib/x86_64-linux-gnu/libGL.so.1`, the CUDA-provided `libOpenCL.so.1`).
- With all of the above, **every `.cpp` file in `src/` compiled successfully** (only deprecation/sign-compare
  warnings, no errors).
- **Final link stage still fails.** It needs `-lGL -lGLU -lOpenCL -lrt -lglut` per the Makefile; after fixing
  the two broken symlinks, `-lGL` and `-lOpenCL` resolved, but `-lglut` is being satisfied from a **static**
  `libglut.a` (no working `libglut.so` in the extracted set) which in turn needs direct X11 extension libraries
  (`-lX11`, then `-lXi`, `-lXxf86vm`, `-lXext`) that were not yet extracted. This is solvable in principle with
  more rounds of the same `apt-get download` + `dpkg-deb -x` trick, but was not pursued further: OpenCL cannot
  run on this box regardless of whether the link succeeds (see above), so finishing the link would not enable
  an actual bounded run tonight.
- **Net result: compiles, does not yet link; cannot run even if it did link, because there is no OpenCL
  platform available.** No GPU time or GPU memory was consumed by any of this (pure CPU compilation).

Cleanup: deleted the clone and `local_deps` (`~/worm-tools/sibernetic`, 398 MB; `~/worm-tools/local_deps`, 15
MB) after recording the findings above - the exact repro commands (which `.deb`s to `apt-get download`, which
symlinks needed re-pointing) are written out above, so a future session can redo this in a couple of minutes
without needing the files kept around. No processes were left running; every build command used `timeout` and
completed or was killed within its bound.

---

---

### 5. BAAIWorm / MetaWorm

Repo: `github.com/Jessie940611/BAAIWorm`, shallow-cloned 2026-11-04 (no pinned release tag found; used default
branch HEAD at clone time). The repo bundles three parts: `eworm` (pure Python + NEURON `.mod` mechanisms - the
detailed multicompartment circuit builder/simulator), `MetaWorm` (connectome/model data), and `neuronXcore`
(C++/OptiX GPU 3D visualization). Only `eworm` was installed and run; `neuronXcore` needs an NVIDIA OptiX SDK,
CUDA 11.4 specifically, and a Boost 1.79 source build, none of which are available here without sudo, so it was
**not attempted** - this box's GPU is also a different generation to what BAAIWorm's OptiX layer targets and was
at the time occupied by another user's job anyway.

Install (`~/worm-tools/baaiworm_env`, a `uv`-created venv, all installs via `uv pip install`):
- Cloned repo (609 MB) into `~/worm-tools/BAAIWorm`.
- `eworm/network/test.py` is the smallest demo entry point (builds a 136-cell detailed circuit and runs a short
  simulation). Running it cold produced a chain of four `ModuleNotFoundError`/format errors, fixed in order:
  1. missing `torch` -> `uv pip install torch --index-url https://download.pytorch.org/whl/cpu` (CPU wheel,
     `torch==2.15.0+cpu` - no CUDA build needed since this layer does no GPU work itself).
  2. missing `xlrd`, `openpyxl`, `tqdm`, `seaborn` -> installed together.
  3. missing `pymp` -> `uv pip install pymp-pypi` (built from source, no issues).
  4. `xlrd.biffh.XLRDError: Excel xlsx file; not supported` - modern `xlrd` (2.x) dropped `.xlsx` support;
     BAAIWorm's own `requirements.txt` pins `xlrd==1.2.0` with a comment explaining exactly this, so matched
     that pin.
- Also compiled the NEURON mechanisms shipped in the repo via `nrnivmodl` (using the `neuron_env` from test #1,
  same pip `neuron` package) - this is where the channel list below was confirmed, from the compiled mechanism
  file names.

Run: `OMP_NUM_THREADS=4 ... taskset -c 0-3 python eworm/network/test.py`, completed cleanly:
```
It takes 0.50s to construct connections!
<class 'eworm.network.detailed_circuit.DetailedCircuit'>
136
{... 136-entry cell name -> index dict, e.g. 'AWAL': 24, 'VD13': 291, plus pharyngeal cells I1L/I1R/I2L/I2R/
 I3/I4/I5/I6/M1/M2L/M2R/M3L/M3R/M4/M5 per config.json ...}
simulation takes 0.6532714366912842 s.
done!
```
This is a 136-cell detailed multicompartment network (connectome-defined adjacency from an 8-cell seed set),
simulated for 100 ms (dt = 0.5 ms, 200 steps) in 0.653 s wall on 4 threads - **about 0.15x real time (roughly 6.5x
slower than real time)** for this config. Confirmed via `uptime` that backhouse load (15.9-16.5) stayed well
under the 24 cap throughout.

Licence: **Apache 2.0** (LICENSE file at repo root read directly).

Fidelity notes: the compiled `.mod` mechanisms give a full gene-named channel set per cell - `egl-19`, `unc-2`,
`slo-1`, `slo-2`, `egl-2`, `egl-36`, `irk`, `kcnl`, `kqt-3`, `kvs-1`, `nca`, `shk-1`, `shl-1` - plus gap-junction
and excitatory/inhibitory synapse mechanisms, i.e. this is a real biophysical multicompartment layer (same
class of model as NEURON/Arbor above), not a reduced point-neuron network. It is distinct from, and does not
require, the separate OptiX-based 3D body/environment visualization layer, which was correctly scoped out as a
different (and here infeasible) dependency chain.

Cleanup: deleted `~/worm-tools/BAAIWorm` (2.2 GB - repo clone plus `baaiworm_env`/torch) after recording the
findings above; the exact repro commands and the four dependency fixes are written out above, so a future
session can redo this in a few minutes without needing the files kept around. No background processes were
left running.

