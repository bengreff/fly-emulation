"""The held-out lock (docs/worm/HELDOUT.md; data/worm/heldout/lock.json): identifiers no fit may see.

Every data loader and wormemu.simulate exclude locked identifiers by default; only the one pre-registered scoring
run passes allow_heldout=True (simulate: Experiment.heldout=True).

    locked("atanas2023")                       # {recording ids} (every condition's ids)
    exclude("randi2023", items, key=...)       # the items whose identifier is not locked
    check("owmd_javer2018", ["unc-29"])        # raises HeldOut on a locked identifier

Identifiers are matched as given (neuron, strain, gene, recording or corpus-item names). Whole-cohort locks also
match their genotype: randi2023's unc-31 entry locks "unc-31" and strain "AML508". owmd_javer2018 also takes the
perturbation corpus's locked genes (HELDOUT.md step 4). A corpus ablation item locks an experiment that ablates at
least one cell of every class it names.
"""
from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path

LOCK = Path(__file__).resolve().parents[2] / "data" / "worm" / "heldout" / "lock.json"
WHOLE = {"randi2023": {"ALL_UNC31_ANIMALS": ("unc-31", "AML508")}}
ABLATION_CLASSES = {"ava_avb_pvc_avd_ablation": ("AVA", "AVB", "PVC", "AVD")}


class HeldOut(PermissionError):
    """A locked identifier reached a fit, a loader or a simulation."""


@lru_cache(maxsize=1)
def load() -> dict:
    return json.loads(LOCK.read_text())


@lru_cache(maxsize=None)
def locked(dataset: str) -> frozenset:
    ds = load()["datasets"]
    if dataset not in ds:
        raise KeyError(f"{dataset}: not in {LOCK.name} ({', '.join(ds)})")
    L = ds[dataset]["locked"]
    ids = [x for c in L.values() for x in c["ids"]] if isinstance(L, dict) else list(L)
    out = set()
    for x in ids:
        tag = x.split(" ")[0]
        if tag in WHOLE.get(dataset, {}):
            out |= set(WHOLE[dataset][tag])
        out.add(x)
    if dataset == "owmd_javer2018":
        out |= set(ds["perturbation_corpus"]["locked"])
    return frozenset(out)


def is_locked(dataset: str, ident: str) -> bool:
    return str(ident) in locked(dataset)


def exclude(dataset: str, items, key=lambda x: x, allow_heldout: bool = False) -> list:
    """The items whose identifier (key(item)) is not locked; all of them with allow_heldout."""
    items = list(items)
    return items if allow_heldout else [x for x in items if not is_locked(dataset, key(x))]


def check(dataset: str, idents, allow_heldout: bool = False):
    bad = sorted({str(i) for i in idents if is_locked(dataset, i)})
    if bad and not allow_heldout:
        raise HeldOut(f"{dataset}: locked identifiers {bad} (docs/worm/HELDOUT.md; only the pre-registered scoring "
                      "run may use them)")


def experiment_locks(genes=(), ablations=(), sources=()) -> list:
    """The locked identifiers an experiment touches: its genes in the perturbation corpus or the OWMD strains, a
    corpus ablation it reproduces, and any (dataset, identifier) source it names."""
    hits = [("perturbation_corpus", g) for g in genes if is_locked("perturbation_corpus", g)]
    hits += [("owmd_javer2018", g) for g in genes if is_locked("owmd_javer2018", g)
             and not is_locked("perturbation_corpus", g)]
    for item, classes in ABLATION_CLASSES.items():
        if is_locked("perturbation_corpus", item) and all(any(c.startswith(k) for c in ablations) for k in classes):
            hits.append(("perturbation_corpus", item))
    hits += [(d, i) for d, i in sources if is_locked(d, i)]
    return hits
