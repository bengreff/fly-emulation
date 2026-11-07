"""FIT2's expression-to-excitability map (docs/worm/FIT2.md section 1): one map from CeNGEN expression to somatic
channel density and leak, shared by every neuron class. Form `expression_map=fit2` (neutral: not the default).

    g_k,c = 0                                                              where class c does not detect k's gene
    g_k,c = clip(m_k 10^a_f(k) ((TPM_k,c + C) / (TPMref_k + C))^b, lo_k, hi_k)   otherwise
    gpas_part,c = clip(M_part 10^a_leak ((TWK_c + C) / (TWKref + C))^b, ledger bounds);  e_pas = e_leak everywhere

m_k, lo_k, hi_k: the published nonzero densities of channel k (BAAIWorm's 302 per-cell fits in the ledger; for the
Nicoletti 2024 channels, mech/channels' fitted cells). TPM: CeNGEN threshold 2, max over a channel's genes (as
build_ledger.CHANNELS). 19 parameters: 17 family scales a_f (log10, relative to m_k), one slope b, one e_leak.

Validity: somatic channels and passive leak of BAAIWorm's morphologies with literature_overrides on; kinetics, Ca
pool, cm, Ra and morphology are the brain's. The parameters in force are PARAMS if a caller set them (the fit), else
the fitted file data/worm/excite/fit2_map.json if it exists, else the neutral template (every a_f 0, b 0, e_leak the
ledger template).
"""
from __future__ import annotations

import json
from pathlib import Path
from statistics import median

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
FITTED = ROOT / "data" / "worm" / "excite" / "fit2_map.json"

# channel -> CeNGEN genes (BAAIWorm's 16 as scripts/worm/build_ledger.CHANNELS; Nicoletti's 5 as mech/channels)
GENES = {"shl1": ["shl-1"], "shk1": ["shk-1"], "kvs1": ["kvs-1"], "egl2": ["egl-2"], "egl36": ["egl-36"],
         "kqt3": ["kqt-3"], "egl19": ["egl-19"], "unc2": ["unc-2"], "cca1": ["cca-1"],
         "slo1_egl19": ["slo-1"], "slo1_unc2": ["slo-1"], "slo2_egl19": ["slo-2"], "slo2_unc2": ["slo-2"],
         "kcnl": ["kcnl-1", "kcnl-2", "kcnl-3", "kcnl-4"], "nca": ["nca-1", "nca-2"], "irk": ["irk-1", "irk-2", "irk-3"],
         "kqt1": ["kqt-1"], "unc103": ["unc-103"], "exp2": ["exp-2"], "slo1iso": ["slo-1"], "slo2iso": ["slo-2"]}
NIC = ("kqt1", "unc103", "exp2", "slo1iso", "slo2iso")
FAMILY = {"shk1": "shk1", "egl36": "egl36", "shl1": "shl1", "kvs1": "kvs1", "kqt3": "kqt", "kqt1": "kqt",
          "egl2": "egl2", "unc103": "unc103", "exp2": "exp2", "irk": "irk",
          "slo1_egl19": "slo1", "slo1_unc2": "slo1", "slo1iso": "slo1",
          "slo2_egl19": "slo2", "slo2_unc2": "slo2", "slo2iso": "slo2",
          "kcnl": "kcnl", "egl19": "egl19", "unc2": "unc2", "cca1": "cca1", "nca": "nca"}
FAMILIES = sorted(set(FAMILY.values())) + ["leak"]
NIC_NAME = {"slo1_egl19": "slo1egl19", "slo1_unc2": "slo1unc2", "slo2_egl19": "slo2egl19", "slo2_unc2": "slo2unc2"}
TWK = r"^(twk-\d+|sup-9|unc-58|egl-23)$"
C_TPM = 10.0                     # pseudo-count (guessed, FIT2 section 1)
B_BOUNDS = (0.0, 1.5)
LEAK_BOUNDS = (-1.5, 1.5)
NAMES = [f"a_{f}" for f in FAMILIES] + ["b", "e_leak"]
RECORDED = ("AIY", "RIM", "AFD", "AWA")

PARAMS: dict | None = None       # set by a caller (the fit) to override the file and the template
SHUFFLE: int | None = None       # seed of a shuffled-CeNGEN control (FIT2 section 4); None = the real table
GENERIC = False                  # the generic-cell comparison: every channel present everywhere, expression ignored
INSERT_ALL = False               # insert every Nicoletti channel in every soma (gbar 0 where absent), for the fit


class Map:
    def __init__(self, led, st, shuffle=None, generic=False):
        self.st, self.generic = st, generic
        tpm = np.asarray(st.tpm, float)
        self.classes = list(st.cengen_classes)
        if shuffle is not None:
            tpm = tpm[:, shuffle_perm(self.classes, shuffle)]
        self.tpm = tpm
        gi = st.gene_index
        self.tpm_k = {k: np.max([tpm[gi[g]] if g in gi else np.zeros(tpm.shape[1]) for g in gs], axis=0)
                      for k, gs in GENES.items()}
        import re
        twk = [g for g in gi if re.match(TWK, g)]
        self.twk = tpm[[gi[g] for g in twk]].sum(0)
        self.n_twk = len(twk)
        # TPMref: the median over detecting classes; invariant under a column permutation
        self.ref = {k: float(np.median(v[v > 0])) if (v > 0).any() else 1.0 for k, v in self.tpm_k.items()}
        self.twk_ref = float(np.median(self.twk))
        self.m, self.lo, self.hi, self.pub = {}, {}, {}, {}
        from wormemu.mech import channels as nic
        allk = [x for c in nic.SURF_CM2 for ch in nic.K_CHANNELS if (x := nic.fitted_density(c, ch)) > 0]
        for k in GENES:
            if k in NIC:
                vals = sorted(nic._cells_fitted_with(k).values())
                if len(vals) >= 2:
                    m, lo, hi = median(vals), vals[0], vals[-1]
                elif len(vals) == 1:
                    m, lo, hi = vals[0], 0.0, 2.0 * vals[0]
                else:
                    m, lo, hi = median(allk), 0.0, max(allk)
            else:
                v = led.values(f"dens_{k}").value.to_numpy(float)
                own = sorted(v[v > 0])
                # the published range also takes Nicoletti 2024's fits of the same channel (FIT2 section 8)
                nk = NIC_NAME.get(k, k)
                vals = sorted(own + [x for c in nic.SURF_CM2 if (x := nic.fitted_density(c, nk)) > 0])
                m, lo, hi = median(own), vals[0], vals[-1]
            self.m[k], self.lo[k], self.hi[k], self.pub[k] = m, lo, hi, vals
        self.bounds = {}
        for f in FAMILIES[:-1]:
            r = [x / self.m[k] for k in GENES if FAMILY[k] == f for x in self.pub[k]]
            if len(r) >= 2:
                self.bounds[f"a_{f}"] = (max(-2.0, float(np.log10(min(r)))), min(2.0, float(np.log10(max(r)))))
            else:
                self.bounds[f"a_{f}"] = (-1.0, 1.0)          # fewer than two published values (guessed)
        self.bounds["a_leak"] = LEAK_BOUNDS
        pr = led.parameters.set_index("param_id")
        self.bounds["b"] = B_BOUNDS
        self.bounds["e_leak"] = (float(pr.loc["pas_soma_epas", "bio_min"]), float(pr.loc["pas_soma_epas", "bio_max"]))
        self.e_template = float(pr.loc["pas_soma_epas", "value_template"])
        self.gpas_bounds = (float(pr.loc["pas_soma_gpas", "bio_min"]), float(pr.loc["pas_soma_gpas", "bio_max"]))
        self.M = {part: float(led.values(f"pas_{part}_gpas").value.median()) for part in ("soma", "neurite")}
        self._baai_present = {k: led.values(f"dens_{k}").set_index("element").value for k in GENES if k not in NIC}
        self.lo_vec = np.array([self.bounds[n][0] for n in NAMES])
        self.hi_vec = np.array([self.bounds[n][1] for n in NAMES])

    def template(self):
        return {**{f"a_{f}": 0.0 for f in FAMILIES}, "b": 0.0, "e_leak": self.e_template}

    def from_unit(self, x):
        x = np.clip(np.asarray(x, float), 0.0, 1.0)
        return dict(zip(NAMES, (self.lo_vec + x * (self.hi_vec - self.lo_vec)).tolist()))

    def to_unit(self, P):
        return (np.array([P[n] for n in NAMES]) - self.lo_vec) / (self.hi_vec - self.lo_vec)

    def cell(self, name, P):
        """{channel: S/cm2} for the 21 channels, plus gpas_soma, gpas_neurite (S/cm2) and epas (mV)"""
        from wormemu.brain_structure import cengen_class
        cls = cengen_class(name, set(self.classes))
        j = self.classes.index(cls) if cls in self.classes else None
        b, out = P["b"], {}
        for k in GENES:
            base = self.m[k] * 10.0 ** P[f"a_{FAMILY[k]}"]
            if self.generic:
                out[k] = float(np.clip(base, self.lo[k], self.hi[k]))
                continue
            if j is None:                                    # no CeNGEN class: BAAIWorm's presence pattern
                present = k in NIC or float(self._baai_present[k].get(name, 0.0)) > 0
                out[k] = float(np.clip(base, self.lo[k], self.hi[k])) if present else 0.0
                continue
            t = float(self.tpm_k[k][j])
            out[k] = 0.0 if t <= 0 else float(np.clip(base * ((t + C_TPM) / (self.ref[k] + C_TPM)) ** b,
                                                      self.lo[k], self.hi[k]))
        tw = float(self.twk[j]) if j is not None else self.twk_ref
        scale = 10.0 ** P["a_leak"] * ((tw + C_TPM) / (self.twk_ref + C_TPM)) ** (0.0 if self.generic else b)
        for part in ("soma", "neurite"):
            out[f"gpas_{part}"] = float(np.clip(self.M[part] * scale, *self.gpas_bounds))
        out["epas"] = float(P["e_leak"])
        return out


def shuffle_perm(classes, seed):
    """A permutation of the CeNGEN class columns that moves every recorded class (FIT2 section 4)"""
    rng = np.random.default_rng(seed)
    idx = [classes.index(c) for c in RECORDED if c in classes]
    while True:
        p = rng.permutation(len(classes))
        if all(p[i] != i for i in idx):
            return p


def params(m: Map):
    if PARAMS is not None:
        return PARAMS
    if FITTED.exists():
        return json.loads(FITTED.read_text())["params"]
    return m.template()


def for_brain(brain):
    """the brain's Map (built once per brain) and the parameters in force"""
    if getattr(brain, "_excite_map", None) is None:
        brain._excite_map = Map(brain.spec.led, brain.st, shuffle=SHUFFLE, generic=GENERIC)
    return brain._excite_map, params(brain._excite_map)
