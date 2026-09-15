# Running the code

Session 2 deleted the isolated-fragment drivers. What remains is infrastructure
that serves any model, plus the data-validation tests.

## Setup

Mac, orchestration and CPU work:

```bash
cd /Users/ben/fly-emulation
uv sync                       # pinned Python 3.12
uv run pytest tests -q        # 7 data-validation checks
```

The neuPrint token lives at `~/.config/flyemu/neuprint_token`, mode 600, outside
the repository. It reaches `manc`, `male-cns`, `hemibrain` and `optic-lobe` for
live queries, which avoids multi-gigabyte downloads. Use `male-cns:v1.0` as the
primary graph; see finding F-DATA-2 for why, and note its annotations use
different field names from the nerve-cord dataset.

PC, `backhouse`, 28 cores under WSL2 Ubuntu. Its internet is blocked at the
router, so its environment was built from wheels shipped over the Tailscale SSH
link:

```bash
# on the Mac
pip download --platform manylinux2014_x86_64 --python-version 3.12 \
    --only-binary=:all: --dest /tmp/wheels_linux <packages>
scp /tmp/wheels_linux/*.whl backhouse:C:/flyemu/wheels/
# on the PC
~/flyemu/venv/bin/python -m pip install --no-index \
    --find-links /mnt/c/flyemu/wheels <packages>
```

Its SSH login shell is `cmd.exe`, so quoting bash inline is unreliable. Ship a
script and execute it:

```bash
ssh backhouse "wsl -d Ubuntu -- bash /mnt/c/flyemu/<script>.sh"
```

Do not run more than two simulation sweeps at once on the laptop. Three
oversubscribes ten cores and slows everything by roughly the factor you added.

## What remains

```bash
uv run pytest tests -q                        # validates the source data itself
uv run python scripts/audit_provenance.py     # every run record complete
```

`src/flyemu/provenance.py` is the recorder. Any run that produces a number
should write one: commits for this repo and any pinned upstream, SHA-256 of every
input, resolved config, environment, wall time, peak memory, and an explicit list
of **scaffolds**, meaning every imposed stimulus, prescribed input or
non-biological substitute used. Session 1 wrote 53 of these and the audit script
confirms all are complete.

## What was deleted

The fragment runner, its sweeps, its figures and its bespoke analyses, about 40
files. Recoverable from git history at commit `1f7f5a4` or earlier. See
`docs/PLAN.md` for why.

`external/Pugliese_cpg_2025` is untracked and remains on disk as a precedent to
consult. Its bundled connectivity extracts are what the data-validation tests
read, so the tests skip if it is absent.

## Untracked but retained

`runs/` holds 53 provenance records and their metrics from session 1, about
16 MB. They are the evidence behind every number in `docs/FINDINGS.md`, so they
stay on disk even though the code that produced them is gone.
