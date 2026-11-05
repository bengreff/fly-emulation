# Vendored: MetaWorm body (BAAIWorm)

- Upstream: https://github.com/Jessie940611/BAAIWorm (Zhao et al. 2024, Nat Comput Sci, "An integrative data-driven
  model simulating C. elegans brain, body and environment interactions"). Commit b99ca5ab9c00aef739fceb1cf007bc50b06f2ccc.
- Licence: Apache 2.0 (`LICENSE`, copied from the repo root; `Metaworm/LICENSE` is the same text). The body physics
  is SoftCon-derived (projective dynamics FEM), as credited upstream.
- Copied, unchanged except one line: `Metaworm/sim/` (all sources; the prebuilt `libsim.a` and `fem/libfem.a`
  removed). The one line (2026-11-05): upstream's own `// #pragma omp parallel for` over the local step in
  `sim/fem/World.cpp:237` is uncommented. It is inert unless built with `OMP=1 driver/build.sh` (-fopenmp); the
  default build is the published single-thread code. With it on, the result matches to 9 digits at 1-8 threads
  (BODY_TESTS.md).
  One extension (2026-11-05, ours, marked "wormemu extension" in the source): `World::SetUnitMass` and
  `World::SetDragMatrix` in `sim/fem/World.h/.cpp`, plus two guarded lines in `ProjectiveDynamicsMethod` and
  `PreComputation`. They add an implicit linear drag (M/h^2 + C/h + L) x = M/h^2 q + C/h x_n + J d, needed for
  resistive-force drag on agar at the real mass. Inert unless called: with them uncalled, P2 (key) and P0 (dead)
  frames are bit-identical to the runs before the edit (checked 2026-11-05). A third, `World::SetReturnLatestIterate`
  (toggle `body.solver_exit`, neutral `published`), makes the converged branch of the solver loop keep its last
  solve; upstream breaks out and returns the iterate from before it, which at rest under a weak load is the
  inertial prediction (the dead zone in BODY_TESTS.md). Off unless `--solver_exit latest` is passed; with it off,
  P0 and P2 frames are bit-identical to the runs before any extension (checked 2026-11-05 17:12).
  `Metaworm/data/` (mesh `worm_mesh_4.mesh`, muscle fibres `worm_nerve_cord_highResCord.obj`, `worm.meta`,
  `worm.sampling`, the muscle key files `worm_givenkey_*.csv`, `worm_empty_key.csv`), and
  `Metaworm/args/train_worm_swim_args.txt`.
- Ours (not upstream): `driver/run_body.cpp` (headless loop replacing the GLUT window and the Boost.Python bridge;
  same stepping, muscle input at 30 Hz and 8 physics steps at 240 Hz; `--mode pipe` takes activations over a pipe
  and returns vertex positions each exchange, for the closed loop in `src/wormemu/body/loop.py`; the worm-scale
  world flags `--scale worm_1mm`, `--fluid agar_rft|viscous_rft_water`, `--substrate agar_plate|agar_film` replace
  Environment::Step with RFT drag in the implicit solve, gravity and plate/film projection, all off by default:
  P0 and P2 frames bit-identical, checked 2026-11-05 17:31) and `driver/build.sh` (rebuilds an object when any
  `sim/` header is newer).
- Build differences from upstream CMake: `-std=gnu++14` (Eigen 3.5 needs C++14; upstream gnu++11), `-O2` (upstream
  Release, -O3), `-include cassert -include cmath -include limits` (missing includes on clang), no Boost.Python,
  PythonLibs, and OpenMP only with `OMP=1`. Build products `driver/obj/` and `driver/run_body` are gitignored.
- Run: `third_party/metaworm/driver/build.sh` then `src/wormemu/body/metaworm.py: run(...)`; tests in
  `scripts/worm/metaworm_tests.py`, results in `docs/worm/BODY_TESTS.md`.
