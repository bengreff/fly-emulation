# Decision log

Short records of user decisions and major implementation choices. Newest last.

## 2026-09-14 Session 1 setup

- **Compute:** backhouse GPU (RTX 4070 Ti SUPER, WSL2 Ubuntu 24.04) may be used freely. Set up direct SSH into WSL for long jobs. Existing `/home/greff` content belongs to another project; do not modify.
- **Data access:** user has no neuPrint/Janelia or FlyWire/CAVE account yet and will register on request. Proceed with open releases first (Pugliese code/data, Azevedo Dryad, Zenodo, Caltech Data) and list exactly which registration unblocks which dataset.
- **Budget:** overnight unattended GPU jobs are acceptable. Raw data up to ~200 GB on the WSL disk. Mac keeps no raw data (56 GB free).
- **Repository:** private GitHub repo as canonical remote; checkouts on both the Mac and WSL. Raw data stays out of git.
- **Hardware correction:** README's "RTX 4070 Super" is actually a 4070 Ti SUPER with 16 GB (see ENVIRONMENT.md).
