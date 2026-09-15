# Environment survey

Measured 14 September 2026 by direct inspection. Corrects the README, which lists an "RTX 4070 Super"; the installed card is an **RTX 4070 Ti SUPER (16 GB)**.

## Mac (orchestration; this repository's checkout)

| Item | Value |
|---|---|
| Machine | Apple M2 Pro, 10 CPU cores, 16 GPU cores (Metal 3), 16 GB RAM |
| Free disk | ~56 GB of 460 GB |
| Python | 3.14.2 system; no uv/conda; no scientific packages installed |
| Other | git 2.39, Homebrew, node 22, Docker 29 |
| Role | Orchestration, docs, small CPU reference tests. **No CUDA.** Python 3.14 is too new for JAX/Brian2/MuJoCo wheels; use a pinned 3.11/3.12 via uv. Disk is too small for the ~49 GB Azevedo release or MaleCNS position files; keep raw data on backhouse. |

## backhouse (GPU compute; SSH host `backhouse`, Tailscale 100.81.254.12, user `ben`)

| Item | Value |
|---|---|
| OS | Windows 11 Pro, 64 GB RAM |
| GPU | NVIDIA GeForce RTX 4070 Ti SUPER, 16376 MiB, driver 591.86 |
| Windows disk | C: 1.1 TB free of 2 TB; F: 533 GB free of 1 TB |
| Windows Python | 3.8.3 (too old; do not use) |
| WSL2 | Ubuntu 24.04.2 LTS (running, default), Ubuntu-22.04 (stopped) |
| WSL Ubuntu | Python 3.12.3, 28 logical CPUs, 31 GB RAM visible to WSL, 8 GB swap, 936 GB free on WSL root disk, GPU visible via nvidia-smi. No uv/conda/nvcc. Linux user `greff`, home `/home/greff`. |
| Existing content | `/home/greff` already holds unrelated work (`nn/`, `gpu/`, `inquiry-project/`, GPU run/profiling scripts). Treat as the user's other project; do not modify. |

## Access pattern

- From the Mac: `ssh backhouse "wsl -d Ubuntu -- <cmd>"`. The SSH login shell is `cmd.exe`, so bash syntax must be wrapped inside the `wsl` invocation. Direct `ssh` into WSL (or a WSL-side sshd) would simplify long jobs; not yet configured.
- WSL memory is capped at 31 GB by default `.wslconfig`; raise it if a whole-brain import needs more.

## Immediate implications

- Primary numerical backend candidates (JAX+CUDA, Brian2, MuJoCo/FlyGym) should be installed in WSL Ubuntu with a pinned Python 3.11/3.12 environment.
- Mac-side work uses a CPU-only environment for tests and analysis.
- Raw datasets live under WSL (fast ext4 disk), outside git, with checksums in a manifest.

## Additions from session 1

- **PC environment built offline.** backhouse's internet stayed blocked at the
  eero router all session. Its Python environment was assembled from wheels
  downloaded on the Mac and copied over the Tailscale SSH link. See
  `docs/RUNNING.md`. CUDA was deliberately skipped: this workload parallelises
  across cores, the PC has 28, and CPU throughput there matches the Mac's.
- **Cross-machine numerical agreement verified.** The same simulation on Apple
  arm64 with JAX 0.11.1 and on x86_64 with JAX 0.6.2 returned identical readouts
  to three decimal places (97 active neurons, 3 active motor neurons, rhythm
  0.813, 9.47 Hz). Architecture and JAX version are not a source of drift here.
- **Body platform resolved.** `flygym` 2.1.0 bundles NeuroMechFly, the
  Turaga-lab flybody and a musculoskeletal model, with MuJoCo Warp GPU support,
  so the roadmap's open question about picking a body is largely closed. Its
  mesh assets download on demand and were not fetched. See finding F6 for what
  the muscle model does and does not cover.
