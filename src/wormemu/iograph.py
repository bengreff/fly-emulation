"""The I/O graph of the worm model, read from the running code: what each registered mechanism writes (out keys,
g_scale names, I_pA, act_add) and reads (ctx.outputs keys, ctx.obs fields and head/tail channels), recorded over a
short default run, plus a static scan of the source for keys only other forms touch. docs/worm/INTERCONNECT.md is
written from it; tests/test_worm_iograph.py holds the default model to no unread output and no unproduced read.

    g = record(ms=20)        # {"writes": {mech: {kind: set}}, "reads": {mech: {kind: set}}}
    edges(g)                 # [(producer, key, consumer)]
"""
from __future__ import annotations

import re
from collections import defaultdict
from pathlib import Path

SRC = Path(__file__).resolve().parent
# keys read outside the registered mechanisms: brain.py's OVERRIDES go to BrainToBody (mech.OVERRIDES); the body
# reads muscle_activation only (body/loop.py Body.activations96); the rest of BrainToBody goes to observations
BRAIN_READS = "OVERRIDES"

# The contract: every ctx.outputs key one module writes and another reads, with its unit. cond = the producer
# writes it only while its state is away from neutral (absent = the consumer's neutral default). Some reads are
# themselves conditional (organs_pharynx reads q10 in its clock form only, the sherman2024 form takes the pump
# factor through tadj; metabolism reads the pump ATP at each DEB update; learning reads energy_fraction when
# daf16_nuclear is absent), so consumers are checked in the source and reads in a run.
LINKS = [
    # key, producer, consumers, unit, what, cond
    ("q10", "temperature", ("senses_chem", "senses_touch", "senses_proprio", "slow_signalling", "learning",
                            "organs_intestine", "organs_pharynx"), "1 (dict by rate class)",
     "Q10 factor per rate class at the worm's temperature", False),
    ("temperature_C", "temperature", ("slow_signalling", "organs_pharynx"), "C",
     "the worm's temperature (AFD T* components; the pharynx GHK temperature)", False),
    ("afd_gc_scale", "glia", ("senses_chem",), "1 (per AFD)", "AMsh glia's scale on AFD guanylyl cyclase", False),
    ("coelomocyte_uptake_per_s", "organs_other", ("organs_intestine", "neuromod"), "1/s",
     "pseudocoelomic clearance by the coelomocytes", False),
    ("pressure_kPa", "organs_other", ("senses_touch",), "kPa", "body fluid pressure (the FEM body takes the "
     "start-up value: body.layers.pressure_link)", False),
    ("peptide_release", "organs_intestine", ("neuromod",), "molecules/s (dict by compartment)",
     "intestinal NLP-40 release into the pseudocoelom", False),
    ("pumps", "organs_pharynx", ("metabolism",), "pumps this step", "feeding", False),
    ("pump_atp_excess_J_per_d", "pumps", ("metabolism",), "J/d", "Na/K pump ATP above rest", False),
    ("egg_production_per_h", "metabolism", ("organs_egglaying",), "eggs/h", "DEB reproduction flux", False),
    ("energy_fraction", "metabolism", ("slow_signalling", "learning"), "1 (0 to 1)",
     "scaled reserve density e clipped to 0-1 (fed = 1)", False),
    ("daf16_nuclear", "slow_signalling", ("learning",), "1 (0 to 1, per cell)", "starvation signal", False),
    ("ma_release_scale", "learning", ("neuromod",), "1 (per cell)", "pathogen-learning amine release factor", True),
    ("ma_release_scale_slow", "slow_signalling", ("neuromod",), "1 (per cell)",
     "DAF-7 on RIM/RIC amine release (daf7_effect)", True),
    ("afd_Tstar_shift_C", "slow_signalling", ("senses_chem",), "C", "AFD threshold reset (afd_tstar_*_frac)", True),
]
# reads with no producer yet: what the default uses instead
OPEN_READS = {"pathogen_exposure": "no intestinal infection model; 0 (naive). The data model sets the learned state "
                                   "from the experiment's history instead (training)"}


class _Rec(dict):
    """A dict that logs every key looked up, under the current reader."""

    def __init__(self, d, log, who, prefix=""):
        super().__init__(d)
        self._log, self._who, self._pre = log, who, prefix

    def _note(self, k):
        self._log[self._who[0]].add(self._pre + str(k))

    def _wrap(self, k, v):
        if isinstance(v, dict) and self._pre == "" and k in ("head", "tail"):
            return _Rec(v, self._log, self._who, f"{k}.")
        return v

    def __getitem__(self, k):
        self._note(k)
        return self._wrap(k, super().__getitem__(k))

    def get(self, k, default=None):
        self._note(k)
        return self._wrap(k, super().get(k, default))

    def __contains__(self, k):
        self._note(k)
        return super().__contains__(k)


def record(ms: float = 20.0, toggles: dict | None = None, cells=None, values: dict | None = None):
    """Run a default brain (open loop, default observation) for `ms` and log every mechanism's reads and writes.
    values: numbers over this worm's (e.g. a short slow_set_s, so the slow modules start reading within the run).
    One NEURON per process: call in a fresh process."""
    import numpy as np

    from wormemu import mech
    from wormemu.brain import Brain, sample_worm
    spec = sample_worm(None)
    spec.values.update(values or {})
    b = Brain(spec, toggles=toggles or {}, cells=cells)
    b.reset()
    who = ["brain"]
    reads_out, reads_obs = defaultdict(set), defaultdict(set)
    writes = defaultdict(lambda: defaultdict(set))
    Ctx = mech.Ctx

    def ctx_factory(**kw):
        kw["outputs"] = _Rec(kw["outputs"], reads_out, who)
        kw["obs"] = _Rec(kw["obs"], reads_obs, who)
        return Ctx(**kw)
    for m in b.mechs:
        name = m.__class__.__module__.rsplit(".", 1)[-1]
        f = m.step

        def step(ctx, dt, f=f, name=name):
            who[0] = name
            r = f(ctx, dt)
            who[0] = "brain"
            for k in ("I_pA", "act_add"):
                if k in r and np.any(np.asarray(r[k]) != 0):
                    writes[name]["drive"].add(k)
            for k in r.get("g_scale", {}):
                writes[name]["g_scale"].add(k)
            for k in r.get("out", {}):
                writes[name]["out"].add(k)
            return r
        m.step = step
    mech.Ctx = ctx_factory
    try:
        for _ in range(int(ms)):
            b.step()
    finally:
        mech.Ctx = Ctx
    mods = [m.__class__.__module__.rsplit(".", 1)[-1] for m in b.mechs]
    return dict(mechs=mods, writes={k: {kk: sorted(vv) for kk, vv in v.items()} for k, v in writes.items()},
                reads={m: dict(outputs=sorted(reads_out.get(m, ())), obs=sorted(reads_obs.get(m, ())))
                       for m in set(reads_out) | set(reads_obs)},
                overrides=list(mech.OVERRIDES))


# temperature -> compiled mods (NEURON GLOBAL tadj_<suffix>, set by mech/temperature.py; RATE_MODS)
NEURON_LINKS = "mech.temperature.RATE_MODS"


def contract_check(g):
    """Problems with a recorded graph against LINKS: a read not in the contract, a contracted read with no producer
    (not OPEN_READS), a link whose producer never wrote (and is not cond), a consumer whose source never names
    the key."""
    made = {k for w in g["writes"].values() for k in w.get("out", ())}
    L = {k: (p, set(c), cond) for k, p, c, _, _, cond in LINKS}
    bad = []
    for m, r in g["reads"].items():
        for k in r["outputs"]:
            if k in OPEN_READS:
                continue
            if k not in L:
                bad.append(f"{m} reads {k}: not in LINKS")
            elif m not in L[k][1]:
                bad.append(f"{m} reads {k}: not a listed consumer")
            elif k not in made and not L[k][2]:
                bad.append(f"{m} reads {k}: nothing wrote it")
    for k, (p, cons, cond) in L.items():
        if p in g["mechs"] and not cond and k not in made:
            bad.append(f"{p} never wrote {k}")
        for c in cons:
            if k not in (SRC / "mech" / f"{c}.py").read_text():
                bad.append(f"{c}.py never names {k}")
    return bad


def edges(g):
    """(producer, key, consumer) for every out key: consumer a mechanism, 'BrainToBody' or None (unread)."""
    prod = defaultdict(list)
    for m, w in g["writes"].items():
        for k in w.get("out", ()):
            prod[k].append(m)
    out = []
    for k, ps in sorted(prod.items()):
        cons = [m for m, r in g["reads"].items() if k in r["outputs"] and m not in ps or
                (k in r["outputs"] and m in ps and len(ps) > 1)]
        if k in g["overrides"]:
            cons.append("BrainToBody")
        for p in ps:
            for c in cons or [None]:
                if c != p:
                    out.append((p, k, c))
    return out


def unread(g):
    return sorted({(p, k) for p, k, c in edges(g) if c is None})


def unproduced(g):
    """ctx.outputs keys a mechanism reads that no mechanism writes in this configuration (its default is used)."""
    made = {k for w in g["writes"].values() for k in w.get("out", ())}
    return sorted({(m, k) for m, r in g["reads"].items() for k in r["outputs"] if k not in made})


def static_keys():
    """Every ctx.outputs key the source reads and every out key it writes, by file (all forms)."""
    rd, wr = defaultdict(set), defaultdict(set)
    pat_r = re.compile(r"outputs(?:\.get\(|\[)\s*[\"']([A-Za-z0-9_@]+)[\"']")
    pat_w = re.compile(r"[\"']([a-z][a-z0-9_]+)[\"']\s*:")
    for f in sorted((SRC / "mech").glob("*.py")):
        s = f.read_text()
        for k in pat_r.findall(s):
            rd[k].add(f.stem)
        for blk in re.findall(r"out\s*=\s*\{(.*?)\}", s, re.S) + re.findall(r"\"out\"\s*:\s*\{(.*?)\}", s, re.S):
            for k in pat_w.findall(blk):
                wr[k].add(f.stem)
        for k in re.findall(r"out\[\s*[\"']([a-z][a-z0-9_]+)[\"']\s*\]\s*=", s):
            wr[k].add(f.stem)
    return rd, wr
