"""The cGMP transduction cascade of Usuyama et al. 2012 (AWC), read from the authors' own model file. Not registered;
senses_chem uses it for AWC as published and, as an inferred template, for the other cGMP sensory cells.

Usuyama C, Iwasaki Y, Iino Y, Ohnishi K, Kato H (2012) "Mathematical model of the olfactory signal transduction
pathway of C. elegans AWC neurons", PLOS ONE 7:e42907 (CC-BY). File S1, the runnable COPASI model, is vendored as
published/usuyama2012_awc.cps and parsed here, so the network (30 species, 31 reactions: odorant receptor, G protein
ODR-3, guanylyl cyclases with GCAPs, GTP supply, PDE and CaM-activated PDE, CNG and voltage-gated Ca entry, Ca
extrusion, CaM buffering) and every rate constant are the published ones. Units as published: concentrations in uM,
time in s; the model's membrane variable V and its voltage-gated Ca entry are the published lumped AWC membrane and
stay inside the cascade. What leaves the cascade is the CNG (TAX-2/TAX-4) open probability,
Po = cGMP^n / (EC50^n + cGMP^n) (the published I_CNG without its driving force), which sets a CNG conductance on the
NEURON cell (senses_chem).

Template use (inferred): for receptor guanylyl cyclase cells (ASE GCY-14/GCY-22, AFD GCY-8/18/23, URX/AQR/PQR
GCY-35/36, BAG GCY-9 and GCY-31/33, light via LITE-1 onto DAF-11/ODR-1) the stimulus multiplies the cyclases'
catalytic rate constants (reactions 4.2.x.2) by (1 + A a(stimulus)); the published odorant/G-protein input stays at
its resting value. For G-protein-coupled odour-OFF cells (AWC, AWB) the stimulus enters as the published Odorant.

Integration: a positive semi-implicit (Patankar) step, x' = P - L x -> x_new = (x + h P) / (1 + h L), with h set by
the caller; the published V follows explicit Euler. CPU reference: scipy's LSODA on the same right-hand side
(scripts/worm/senses_checks.py compares them on the published protocol).
"""
from __future__ import annotations

import xml.etree.ElementTree as ET
from functools import lru_cache
from pathlib import Path

import numpy as np

from wormemu.mech.senses_base import spec

CPS = Path(__file__).resolve().parent / "published" / "usuyama2012_awc.cps"
SRC = "Usuyama et al. 2012 PLOS ONE 7:e42907, File S1 (COPASI model, CC-BY), vendored src/wormemu/mech/published"
_NS = {"c": "http://www.copasi.org/static/schema"}
CUSTOM = ("[1]", "[2]", "[5]", "[6]", "[7]")
KCAT = ("[4.2.1.2]", "[4.2.2.2]", "[4.2.3.2]")       # the cyclases' catalytic steps (GTP -> cGMP)


@lru_cache(maxsize=1)
def network():
    """The published model: species names, initial state (uM), reactions and model values."""
    root = ET.parse(CPS).getroot()
    m = root.find("c:Model", _NS)
    mets = {e.get("key"): e.get("name") for e in m.find("c:ListOfMetabolites", _NS)}
    mvals = {e.get("key"): e.get("name") for e in m.find("c:ListOfModelValues", _NS)}
    refs = [e.get("objectReference") for e in m.find("c:StateTemplate", _NS)]
    vals = [float(x) for x in m.find("c:InitialState", _NS).text.split()]
    state = dict(zip(refs, vals))
    na = float(m.get("avogadroConstant")) * 1e-6 * state["Compartment_0"]      # particles per uM in the compartment
    init = {mets[k]: v / na for k, v in state.items() if k in mets}
    values = {mvals[k]: v for k, v in state.items() if k in mvals}
    species = [n for n in init if n not in ("R_total", "G_total", "Odorant")]
    fpar = {d.get("key"): d.get("name") for f in root.find("c:ListOfFunctions", _NS)
            for d in f.findall("c:ListOfParameterDescriptions/c:ParameterDescription", _NS)}
    rx = []
    for e in m.find("c:ListOfReactions", _NS):
        name = e.get("name").strip()
        tag = name.split()[0]
        subs = [mets[s.get("metabolite")] for s in e.findall("c:ListOfSubstrates/c:Substrate", _NS)]
        prods = [mets[s.get("metabolite")] for s in e.findall("c:ListOfProducts/c:Product", _NS)]
        k = {c.get("name"): float(c.get("value")) for c in e.findall("c:ListOfConstants/c:Constant", _NS)}
        glob = {}                                         # constants the reaction takes from a global model value
        for cp in e.findall("c:KineticLaw/c:ListOfCallParameters/c:CallParameter", _NS):
            ref = [x.get("reference") for x in cp]
            if fpar.get(cp.get("functionParameter")) in k and ref and ref[0] in mvals:
                glob[fpar[cp.get("functionParameter")]] = mvals[ref[0]]
        law = "custom" if tag in CUSTOM else ("const" if "v" in k else ("rev" if "k2" in k else "irr"))
        rx.append(dict(tag=tag, name=name, subs=subs, prods=prods, k=k, law=law, glob=glob))
    return dict(species=species, init=init, values=values, reactions=rx)


def _sid(tag, const):
    return "usu_r" + tag.strip("[]").replace(".", "_").replace("-", "_") + "_" + const.replace("+", "p").replace(
        "-", "m")


def network_specs(applies_to, mechanism="sens_odor_attract"):
    """One Spec per published number the cascade uses: every rate constant, the CNG and VG model values, and the
    published initial state (the conserved totals follow from it)."""
    net = network()
    out = []
    for r in net["reactions"]:
        for c, v in r["k"].items():
            if (r["tag"] in ("[5]", "[6]") and c in ("I_CNG", "V_Membrane")) or c in r["glob"]:
                continue                                  # call-site placeholders, or taken from a global value
            out.append(spec(_sid(r["tag"], c), mechanism, _unit(r, c), v, *_rng(v), "published_fit", SRC,
                            applies_to, notes=f"reaction {r['name']}; range guessed (x/10 to x10, signs kept)"))
    for name, unit in (("[CNG]_IMax_CNG", "1/s"), ("[CNG]_EC50_CNG", "uM"), ("[CNG]_n_CNG", "1"),
                       ("[VG]_Ef_VG", "1"), ("[CaM+Ca] K+1_CaM+Ca", "1/(uM s)"), ("[CaM+Ca] K-1_CaM+Ca", "1/s")):
        v = net["values"][name]
        out.append(spec(_gid(name), mechanism,
                        unit, v, *_rng(v, name.endswith("n_CNG")), "published_fit", SRC, applies_to,
                        notes="model value; range guessed"))
    for n, v in net["init"].items():
        if n == "Odorant":
            continue
        out.append(spec("usu_init_" + n.replace("::", "_").lower(), mechanism, "uM", v, v / 10, v * 10,
                        "published_fit", SRC, applies_to,
                        notes="the published simulation's initial state (resting, odorant 0.001); range guessed"))
    out.append(spec("usu_odorant_rest", mechanism, "model units", 0.001, 0.0, 0.01, "published_fit", SRC,
                    applies_to, notes="the published Odorant value with no stimulus ('Remove' event)"))
    out.append(spec("usu_odorant_on", mechanism, "model units", 1000.0, 100.0, 10000.0, "published_fit",
                    SRC, applies_to, notes="the published Odorant value during a stimulus ('Dose' event)"))
    return out


def _gid(name):
    """Spec id of a global model value."""
    return "usu_" + name.replace("[CaM+Ca] ", "").replace("[", "").replace("]", "").replace("+", "p").replace(
        "-", "m").lower()


def _unit(r, c):
    if r["law"] == "rev":
        return "1/(uM s)" if len(r["subs" if c == "k1" else "prods"]) == 2 else "1/s"
    if r["law"] in ("irr",):
        return "1/s"
    if r["law"] == "const":
        return "uM/s"
    return {"Ks": "1/(model unit s)", "Kd": "1/s", "Ef_CNG": "uM/s per model unit", "Ef_VGCC": "uM/(s mV)",
            "VR_VGCC": "mV (model)", "V50_VGCC": "mV (model)", "K_VGCC": "mV (model)", "Ef_Cax": "1/s",
            "K_CaX": "uM", "n_CaX": "1"}.get(c, "1")


def _rng(v, hill=False):
    if hill:
        return (v / 2, v * 2)
    if v == 0:
        return (-1.0, 1.0)
    lo, hi = sorted((v / 10, v * 10))
    return (lo, hi)


class Cascade:
    """The published network for n cells at once. p: {spec id: value} (network_specs ids)."""

    def __init__(self, p, n):
        net = network()
        self.sp = net["species"]
        self.i = {s: k for k, s in enumerate(self.sp)}
        self.n = n
        self.x0 = np.array([p["usu_init_" + s.replace("::", "_").lower()] for s in self.sp])
        self.R_tot, self.G_tot = p["usu_init_r_total"], p["usu_init_g_total"]
        self.v0 = net["values"]["V_Membrane"]
        self.imax, self.ec50, self.ncng = p[_gid("[CNG]_IMax_CNG")], p[_gid("[CNG]_EC50_CNG")], p[_gid(
            "[CNG]_n_CNG")]
        self.efvg = p[_gid("[VG]_Ef_VG")]
        # elementary mass-action fluxes f_j = k_j x[a_j] x[b_j] (b_j = the row of ones for one reactant), with the
        # stoichiometry as matrices so a step is a handful of array operations
        ones = len(self.sp)
        A, B, K, prod, cat, self.k = [], [], [], [], [], {}
        for r in net["reactions"]:
            k = {c: p[_gid(r["glob"][c])] if c in r["glob"] else p[_sid(r["tag"], c)] for c in r["k"]
                 if not (r["tag"] in ("[5]", "[6]") and c in ("I_CNG", "V_Membrane"))}
            if r["law"] in ("rev", "irr"):
                S = [self.i[s] for s in r["subs"]]
                Pr = [self.i[s] for s in r["prods"]]
                for kk, rea, pro in ((k["k1"], S, Pr),) + (((k["k2"], Pr, S),) if r["law"] == "rev" else ()):
                    A.append(rea[0]); B.append(rea[1] if len(rea) > 1 else ones); K.append(kk)
                    prod.append(pro); cat.append(r["tag"] in KCAT and rea is S)
            elif r["law"] == "const":
                self.k["gtp_supply"] = (self.i[r["prods"][0]], k["v"])
            else:
                self.k[r["tag"]] = k
        nf = len(K)
        self.fa, self.fb, self.fk = np.array(A), np.array(B), np.array(K)
        self.fcat = np.array(cat)
        self.Mp = np.zeros((len(self.sp), nf))
        for j, pro in enumerate(prod):
            for b in pro:
                self.Mp[b, j] += 1.0
        self.Ma = np.zeros((len(self.sp), nf)); self.Ma[self.fa, np.arange(nf)] = 1.0
        self.Mb = np.zeros((len(self.sp) + 1, nf)); self.Mb[self.fb, np.arange(nf)] = 1.0
        self.Mb = self.Mb[:-1]
        self.reset()

    def reset(self):
        self.x = np.repeat(self.x0[:, None], self.n, axis=1).astype(float)
        self.V = np.full(self.n, self.v0)

    def po(self, cgmp=None):
        c = np.maximum(self.x[self.i["cGMP"]] if cgmp is None else cgmp, 0.0)
        return c ** self.ncng / (self.ec50 ** self.ncng + c ** self.ncng)

    def rates(self, x, V, odor, kcat):
        """Production P and loss coefficient L (x' = P - L x) per species and cell, and V'."""
        i, k = self.i, self.k
        xe = np.vstack([x, np.ones((1, x.shape[1]))])
        kj = np.where(self.fcat[:, None], self.fk[:, None] * kcat[None, :], self.fk[:, None])
        xa, xb = xe[self.fa], xe[self.fb]
        P = self.Mp @ (kj * xa * xb)
        L = self.Ma @ (kj * xb) + self.Mb @ (kj * xa)
        g, v = self.k["gtp_supply"]
        P[g] += v
        k1, k2 = k["[1]"], k["[2]"]
        a = i["R_active"]
        P[a] += k1["Ks"] * odor * self.R_tot
        L[a] += k1["Ks"] * odor + k1["Kd"]
        a = i["G_active"]
        P[a] += k2["Ks"] * x[i["R_active"]] * self.G_tot
        L[a] += k2["Ks"] * x[i["R_active"]] + k2["Kd"]
        c = i["Ca"]
        Ca = np.maximum(x[c], 1e-12)
        icng = self.imax * self.po(x[i["cGMP"]]) * (0.08 - V)
        k6 = k["[6]"]
        j = k["[5]"]["Ef_CNG"] * icng + k6["Ef_VGCC"] * (k6["VR_VGCC"] - V) / (
            1.0 + np.exp((k6["V50_VGCC"] - V) / k6["K_VGCC"]))
        P[c] += np.maximum(j, 0.0)
        k7 = k["[7]"]
        L[c] += np.maximum(-j, 0.0) / Ca + k7["Ef_Cax"] / (
            1.0 + (np.maximum(x[i["CaM::Ca4"]], 0.0) / k7["K_CaX"]) ** k7["n_CaX"])
        ivg = -self.efvg * (6e-5 * V ** 3 + 8.1e-3 * V ** 2 + 0.49 * V + 9.5)
        return P, L, icng + ivg

    def advance(self, dt_s, odor, kcat, h_s=2.5e-4):
        """Advance by dt_s (s) with odorant input `odor` (model units) and catalytic multiplier `kcat` per cell."""
        n = max(1, int(np.ceil(dt_s / h_s - 1e-9)))
        h = dt_s / n
        odor, kcat = np.broadcast_to(odor, (self.n,)), np.broadcast_to(kcat, (self.n,))
        for _ in range(n):
            P, L, dV = self.rates(self.x, self.V, odor, kcat)
            self.x = (self.x + h * P) / (1.0 + h * L)
            self.V = self.V + h * dV
        return self.po()

    def rhs(self, t, y, odor_fn, kcat=1.0):
        """For scipy (CPU reference): y = species (n = 1 cell) then V."""
        x, V = y[:-1, None], y[-1:]
        P, L, dV = self.rates(x, V, np.array([odor_fn(t)]), np.array([kcat]))
        return np.concatenate([(P - L * x)[:, 0], dV])
