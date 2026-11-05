"""C. elegans channel kinetics library, transcribed from the NEURON .mod files of Nicoletti et al. 2024
(PLoS ONE 19:e0298105; github.com/martinanicoletti92/CelegansInterMotorNeuronsModels @ 84726a72).

Each entry is one gene (or a gene coupled to a Ca channel nanodomain). Kinetic constants are the
published ones: Nicoletti et al. fitted them to voltage-clamp recordings of the identified currents
(labelled "derived from measured" in our ledger). Densities (gbar) are NOT here: they are per neuron
and are what we fit. Units follow NEURON: mV, ms, S/cm2, mA/cm2, Ca in M (pool) or uM (nanodomain).

Port check against NEURON on the same .mod files: scripts/worm/check_port.py.
"""
import jax.numpy as jnp

E_K, E_CA, E_NCA = -80.0, 60.0, 30.0  # mV, as set in the Nicoletti scripts (eca=60, ek=-80, nca e=30)
# NB the published AIY/RIM runs actually used eca = 127.59 mV: NEURON recomputes eca by Nernst at finitialize
# because slo1iso READs cai (measured 2026-11-04, scripts/worm/neuron_ref.py eca_mode). E_CA is a parameter.
CA_REST_MM = 5e-5  # NEURON default cai (mM); the published AIY/RIM models have no pool writing cai


def _sig(x):
    return 1.0 / (1.0 + jnp.exp(x))


# ---- Ca channels -------------------------------------------------------------------------------
def egl19_rates(v):
    s = 10.0
    minf = _sig(-(v - 5.6 + s) / 7.5)
    hinf = (1.4314 * _sig(-(v - 24.8573 + s) / 11.9541) + 0.1427) * (5.9589 * _sig((v + 10.5428 + s) / 8.0552) + 0.6038)
    mtau = 2.3359 + 2.9324 * jnp.exp(-((v - 5.2357 + s) ** 2) / 36.0) + 1.8739 * jnp.exp(-((v - 1.3930 + s) ** 2) / 900.0)
    htau = 0.4 * (0.55 * 81.1179 * _sig((v + 22.9723 + s) / 5.0) + 43.0937 + 0.9 * 40.4885 * _sig((v - 28.7251 + s) / 3.7125))
    return minf, mtau, hinf, htau


def unc2_rates(v):
    minf = _sig(-(v + 12.17 + 25.0) / 3.97)
    hinf = _sig((v + 52.47 + 25.0) / 5.6)
    x = v + 8.1761 + 30.0
    mtau = (1.4969 / (jnp.exp(-x / 9.0753) + jnp.exp(x / 15.3456)) + 0.1029) * 3.0
    htau = (83.8037 * _sig((v - 52.8997 + 30.0) / 3.4557) + 72.0995 * _sig(-(v - 23.9009 + 30.0) / 3.5903)) * 1.7
    return minf, mtau, hinf, htau


# ---- SLO (BK, SLO-1; Na/Ca-activated, SLO-2) ----------------------------------------------------
SLO1 = dict(wom=3.152961, wyx=0.012643, kyx=34.338784, nyx=0.000100, wop=0.156217, wxy=-0.027527, kxy=55.726186, nxy=1.299198)
SLO2 = dict(wom=0.896395, wyx=0.019405, kyx=3294.553404, nyx=0.000010, wop=0.026719, wxy=-0.024123, kxy=93.449423, nxy=1.835067)
BKG_UM = 0.05


def nanodomain_ca_um(v, e_ca=E_CA):
    """Ca (uM) at r = 13 nm from an open Ca channel (gsc 40 pS), steady-state buffered diffusion."""
    gsc, r, d, F, kb, b, pi = 40e-12, 13e-9, 250e-12, 96485.0, 500e6, 30e-6, 3.14
    return jnp.abs(gsc * (v - e_ca) * 1e-3) / (8 * pi * r * d * F) * jnp.exp(-r / jnp.sqrt(d / (kb * b))) * 1e3 + BKG_UM


def slo_coupled_rates(v, k, ca_minf, ca_mtau, ca_m, e_ca=E_CA):
    """SLO coupled to one Ca channel (three-state scheme of Nicoletti 2019). Returns (minf, mtau)."""
    ca = nanodomain_ca_um(v, e_ca)
    alpha = ca_minf / ca_mtau
    beta = 1.0 / ca_mtau - alpha
    ev = jnp.exp(-k["wyx"] * v)
    kcm = k["wom"] * ev / (1 + (BKG_UM / k["kyx"]) ** k["nyx"])
    kom = k["wom"] * ev / (1 + (ca / k["kyx"]) ** k["nyx"])
    kop = k["wop"] * jnp.exp(-k["wxy"] * v) / (1 + (k["kxy"] / ca) ** k["nxy"])
    den = (kop + kom) * (kcm + alpha) + beta * kcm
    return ca_m * kop * (alpha + beta + kcm) / den, (alpha + beta + kcm) / den


def slo_iso_rates(v, k, ca_mm=CA_REST_MM):
    cu = ca_mm * 1e3
    s0 = 1.0 / (k["wyx"] - k["wxy"])
    v0 = s0 * (jnp.log(k["wom"] / k["wop"]) + jnp.log(1 + (k["kxy"] / cu) ** k["nxy"]) - jnp.log(1 + (cu / k["kyx"]) ** k["nyx"]))
    minf = _sig(-(v - v0) / s0)
    mtau = jnp.exp(k["wxy"] * v) / k["wop"] * (1 + (k["kxy"] / cu) ** k["nxy"]) * minf
    return minf, mtau


# ---- K channels ---------------------------------------------------------------------------------
def kqt1_rates(v):
    minf = _sig(-(v + 17.6053) / 9.5843)
    sinf = 0.41 * _sig((v + 86.84) / 15.05) + 0.59 * _sig((v - 70.13) / 13.37)
    mtau = 895.9 * _sig((-18.01 - v) / 31.04) + 10.0
    stau = 1077.0 + 185845.0 / (1 + ((v - 39.44) / 7.34) ** 2)
    return minf, mtau, sinf, stau


def shl1_rates(v):
    minf = _sig(-(v - 10.26 + 10.0) / 16.25)
    hinf = _sig((v + 40.0 + 10.0) / 8.3)
    mtau = (13.8 / (jnp.exp(-(v + 40.0) / 12.9213) + jnp.exp((v + 40.0) / 6.4876)) + 1.8849) / 2.0
    hftau = (539.1584 * _sig((v + 60.0) / 4.9199) + 27.2811) / 3.0
    hstau = 8422.0 * _sig((v + 60.0) / 6.3785) + 118.8983
    return minf, mtau, hinf, hftau, hstau


# ---- added for W1 (RIM, AFD): nine more channels, transcribed the same way from the same commit -------
# (cca1, egl2, egl36, irk, kqt3, kvs1, shk1, unc103, exp2 .mod; cnexp gates, so the exponential-Euler update is exact)
def cca1_rates(v):  # CCA-1, T-type Ca; the .mod's hinf(m) reads the global v, i.e. hinf(v)
    minf = _sig(-(v + 42.65 + 15.0) / (1.7 * 1.4))
    hinf = _sig((v + 58.0 + 15.0) / (7.0 * 1.15))
    mtau = (40.0 * _sig(-(v + 62.5393 + 30.0) / (-12.4758 * 1.7)) + 0.6947) * 0.5
    htau = (280.0 * _sig((v + 60.7312 + 15.0) / (8.5224 * 1.1)) + 19.7456) * 0.08
    return minf, mtau, hinf, htau


def egl2_rates(v):  # EGL-2, EAG K
    return _sig(-(v + 6.8594) / 14.9131), (16.78 * _sig((v + 122.5682) / 13.7976) + 8.0969) * 0.5


def egl36_minf(v):  # EGL-36, Shaw K; three gates share minf, time constants 355, 63, 13 ms
    return _sig(-(v - 63.0) / 28.5)


EGL36_TAU, EGL36_W = (355.0, 63.0, 13.0), (0.31, 0.36, 0.39)


def irk_rates(v):  # IRK, inward rectifier K (the .mod labels gbar nS/cm2 but uses it as S/cm2, as here)
    return _sig((v + 52.0 + 30.0) / 13.0), 17.0752 / (jnp.exp(-(v + 17.8258) / 20.3154) + jnp.exp((v + 43.4414) / 11.1691)) + 3.8329


def kqt3_rates(v):  # KQT-3, KCNQ K: fast and slow activation (0.3 / 0.7), two partial inactivations s and w
    minf = _sig(-(v + 12.6726 + 10.0) / 15.8008)
    mtauf = 395.3 / (1 + ((v + 38.1) / 33.59) ** 2) * 0.1
    mtaus = (5503.0 - 5345.4 / (1 + 10.0 ** (-0.02827 * (-23.9 - v))) - 4590.6 / (1 + 10.0 ** (-0.0357 * (v + 14.15)))) * 0.1
    winf = 0.49 + 0.51 * _sig((v + 1.084) / 28.78)
    wtau = (5.44 + 29.2 / (1 + ((v + 48.09) / 48.83) ** 2)) * 0.1
    sinf = 0.34 + 0.66 * _sig((v + 45.3) / 12.3)
    return minf, mtauf, mtaus, winf, wtau, sinf, 500.0


def kvs1_rates(v):  # KVS-1, A-type K
    minf = _sig(-(v - 57.1 + 30.0) / 25.0)
    hinf = _sig((v - 47.3 + 30.0) / 11.1)
    mtau = (30.0 * _sig(-(v - 18.1232) / -20.0) + 1.0) * 0.1
    htau = (88.4715 * _sig(-(v - 50.0) / -15.0) + 53.406) * 0.1
    return minf, mtau, hinf, htau


def shk1_rates(v):  # SHK-1, Shaker K; inactivation tau fixed at 1400 ms
    x = v + 33.741611800716130
    mtau = 26.571450568169027 / (jnp.exp(-x / 15.364937728953288) + jnp.exp(x / 15.757936311607475)) + 1.990037272604829
    return _sig(-(v - 2.0) / 10.0), mtau, _sig((v + 6.95) / 5.8), 1400.0


def unc103_rates(v):  # UNC-103, ERG K; the .mod's time constants are products of two sigmoids
    a, b = (v + 28.3339) / 13.0998, (v + 25.2890) / 29.5074
    mtau = (87.4088 * _sig(a) + 0.2562) * (87.4088 * _sig(-a) + 0.2562)
    htau = (8.1559 * _sig(b) + 0.2300) * (8.1559 * _sig(-b) + 0.2300)
    return _sig(-(v + 15.1) / 7.85), mtau, _sig((v + 48.0) / 28.0), htau


def exp2_rates(v):  # EXP-2, inward-rectifying K (Kv-like); current m * h^2; same product-form time constants
    a, b = (v + 20.5284) / 4.7071, (v + 89.0175) / 49.3492
    mtau = (40.0 * _sig(a) + 2.4025) * (40.0 * _sig(-a) + 2.4025)
    htau = (1.2790 * _sig(b) + 0.8739) * (1.2790 * _sig(-b) + 0.8739)
    return _sig(-(v + 17.0) / 6.5), mtau, _sig((v + 50.0) / 10.0), htau


KCNL_KM_M, KCNL_TAU = 0.33e-6, 6.3
CA_EQ_M, CA_TAU, CA_FREE = 0.05e-6, 50.0, 0.001  # caintra1.mod

# Channel names in a fixed order; a neuron's model is a 0/1 mask over these plus fitted densities.
# CHANNELS / STATES are the default set (the AIY spike's 13); ALL_* add the nine W1 channels, opt-in through
# make_membrane(lib, channels=...). GATES says which states each channel needs, so a subset compiles only those.
CHANNELS = ["leak", "nca", "egl19", "unc2", "kqt1", "shl1", "slo1egl19", "slo1unc2", "slo1iso",
            "slo2egl19", "slo2unc2", "slo2iso", "kcnl"]
NEW_CHANNELS = ["cca1", "egl2", "egl36", "irk", "kqt3", "kvs1", "shk1", "unc103", "exp2"]
ALL_CHANNELS = CHANNELS + NEW_CHANNELS
# CeNGEN gene that gates each channel's inclusion (leak is always on).
GENE = {"leak": None, "nca": "nca-1|nca-2", "egl19": "egl-19", "unc2": "unc-2", "kqt1": "kqt-1", "shl1": "shl-1",
        "slo1egl19": "slo-1&egl-19", "slo1unc2": "slo-1&unc-2", "slo1iso": "slo-1", "slo2egl19": "slo-2&egl-19",
        "slo2unc2": "slo-2&unc-2", "slo2iso": "slo-2", "kcnl": "kcnl-1|kcnl-2|kcnl-3|kcnl-4",
        "cca1": "cca-1", "egl2": "egl-2", "egl36": "egl-36", "irk": "irk-1|irk-2|irk-3", "kqt3": "kqt-3",
        "kvs1": "kvs-1", "shk1": "shk-1", "unc103": "unc-103", "exp2": "exp-2"}
STATES = ["egl19_m", "egl19_h", "unc2_m", "unc2_h", "kqt1_m", "kqt1_s", "shl1_m", "shl1_hf", "shl1_hs",
          "slo1egl19_m", "slo1unc2_m", "slo1iso_m", "slo2egl19_m", "slo2unc2_m", "slo2iso_m", "kcnl_m", "ca"]
NEW_STATES = ["cca1_m", "cca1_h", "egl2_m", "egl36_m1", "egl36_m2", "egl36_m3", "irk_m", "kqt3_mf", "kqt3_ms",
              "kqt3_w", "kqt3_s", "kvs1_m", "kvs1_h", "shk1_m", "shk1_h", "unc103_m", "unc103_h", "exp2_m", "exp2_h"]
ALL_STATES = STATES + NEW_STATES
GATES = {"leak": (), "nca": (), "egl19": ("egl19_m", "egl19_h"), "unc2": ("unc2_m", "unc2_h"),
         "kqt1": ("kqt1_m", "kqt1_s"), "shl1": ("shl1_m", "shl1_hf", "shl1_hs"),
         "slo1egl19": ("slo1egl19_m", "egl19_m", "egl19_h"), "slo1unc2": ("slo1unc2_m", "unc2_m", "unc2_h"),
         "slo1iso": ("slo1iso_m",), "slo2egl19": ("slo2egl19_m", "egl19_m", "egl19_h"),
         "slo2unc2": ("slo2unc2_m", "unc2_m", "unc2_h"), "slo2iso": ("slo2iso_m",), "kcnl": ("kcnl_m",),
         "cca1": ("cca1_m", "cca1_h"), "egl2": ("egl2_m",), "egl36": ("egl36_m1", "egl36_m2", "egl36_m3"),
         "irk": ("irk_m",), "kqt3": ("kqt3_mf", "kqt3_ms", "kqt3_w", "kqt3_s"), "kvs1": ("kvs1_m", "kvs1_h"),
         "shk1": ("shk1_m", "shk1_h"), "unc103": ("unc103_m", "unc103_h"), "exp2": ("exp2_m", "exp2_h")}


def states_for(channels):
    """The states a channel subset needs, in ALL_STATES order (the Ca pool is always kept)."""
    need = {s for c in channels for s in GATES[c]} | {"ca"}
    return [s for s in ALL_STATES if s in need]


def all_rates(v, ca):
    """(inf, tau) for every gate at voltage v and pool Ca (M). SLO-coupled gates need the Ca channel m."""
    e = egl19_rates(v)
    u = unc2_rates(v)
    q = kqt1_rates(v)
    s = shl1_rates(v)
    r = {"egl19_m": (e[0], e[1]), "egl19_h": (e[2], e[3]), "unc2_m": (u[0], u[1]), "unc2_h": (u[2], u[3]),
         "kqt1_m": (q[0], q[1]), "kqt1_s": (q[2], q[3]), "shl1_m": (s[0], s[1]), "shl1_hf": (s[2], s[3]),
         "shl1_hs": (s[2], s[4]), "slo1iso_m": slo_iso_rates(v, SLO1), "slo2iso_m": slo_iso_rates(v, SLO2),
         "kcnl_m": (ca / (ca + KCNL_KM_M), KCNL_TAU)}
    c1, k3, kv, sk, un, x2 = cca1_rates(v), kqt3_rates(v), kvs1_rates(v), shk1_rates(v), unc103_rates(v), exp2_rates(v)
    m36 = egl36_minf(v)
    r.update({"cca1_m": (c1[0], c1[1]), "cca1_h": (c1[2], c1[3]), "egl2_m": egl2_rates(v), "irk_m": irk_rates(v),
              "egl36_m1": (m36, EGL36_TAU[0]), "egl36_m2": (m36, EGL36_TAU[1]), "egl36_m3": (m36, EGL36_TAU[2]),
              "kqt3_mf": (k3[0], k3[1]), "kqt3_ms": (k3[0], k3[2]), "kqt3_w": (k3[3], k3[4]), "kqt3_s": (k3[5], k3[6]),
              "kvs1_m": (kv[0], kv[1]), "kvs1_h": (kv[2], kv[3]), "shk1_m": (sk[0], sk[1]), "shk1_h": (sk[2], sk[3]),
              "unc103_m": (un[0], un[1]), "unc103_h": (un[2], un[3]), "exp2_m": (x2[0], x2[1]), "exp2_h": (x2[2], x2[3])})
    return r, e, u


def coupled_rates(v, st, e, u, e_ca=E_CA, want=None):
    """want: the states to return (default all four); a subset may lack egl19_m or unc2_m in st."""
    f = {"slo1egl19_m": lambda: slo_coupled_rates(v, SLO1, e[0], e[1], st["egl19_m"], e_ca),
         "slo1unc2_m": lambda: slo_coupled_rates(v, SLO1, u[0], u[1], st["unc2_m"], e_ca),
         "slo2egl19_m": lambda: slo_coupled_rates(v, SLO2, e[0], e[1], st["egl19_m"], e_ca),
         "slo2unc2_m": lambda: slo_coupled_rates(v, SLO2, u[0], u[1], st["unc2_m"], e_ca)}
    return {s: fn() for s, fn in f.items() if want is None or s in want}


def currents(v, st, g, e_leak, e_ca=E_CA):
    """Per-channel currents (mA/cm2) for the channels in g (densities, S/cm2), gates st. Returns (dict, i_ca)."""
    f = {"leak": lambda: g["leak"] * (v - e_leak), "nca": lambda: g["nca"] * (v - E_NCA),
         "egl19": lambda: g["egl19"] * st["egl19_m"] * st["egl19_h"] * (v - e_ca),
         "unc2": lambda: g["unc2"] * st["unc2_m"] * st["unc2_h"] * (v - e_ca),
         "kqt1": lambda: g["kqt1"] * st["kqt1_m"] * st["kqt1_s"] * (v - E_K),
         "shl1": lambda: g["shl1"] * st["shl1_m"] * (0.8 * st["shl1_hf"] + 0.2 * st["shl1_hs"]) * (v - E_K),
         "slo1egl19": lambda: g["slo1egl19"] * st["slo1egl19_m"] * st["egl19_h"] * (v - E_K),
         "slo1unc2": lambda: g["slo1unc2"] * st["slo1unc2_m"] * st["unc2_h"] * (v - E_K),
         "slo1iso": lambda: g["slo1iso"] * st["slo1iso_m"] * (v - E_K),
         "slo2egl19": lambda: g["slo2egl19"] * st["slo2egl19_m"] * st["egl19_h"] * (v - E_K),
         "slo2unc2": lambda: g["slo2unc2"] * st["slo2unc2_m"] * st["unc2_h"] * (v - E_K),
         "slo2iso": lambda: g["slo2iso"] * st["slo2iso_m"] * (v - E_K),
         "kcnl": lambda: g["kcnl"] * st["kcnl_m"] * (v - E_K),
         "cca1": lambda: g["cca1"] * st["cca1_m"] ** 2 * st["cca1_h"] * (v - e_ca),
         "egl2": lambda: g["egl2"] * st["egl2_m"] * (v - E_K),
         "egl36": lambda: g["egl36"] * sum(w * st[f"egl36_m{k + 1}"] for k, w in enumerate(EGL36_W)) * (v - E_K),
         "irk": lambda: g["irk"] * st["irk_m"] * (v - E_K),
         "kqt3": lambda: g["kqt3"] * (0.3 * st["kqt3_mf"] + 0.7 * st["kqt3_ms"]) * st["kqt3_s"] * st["kqt3_w"] * (v - E_K),
         "kvs1": lambda: g["kvs1"] * st["kvs1_m"] * st["kvs1_h"] * (v - E_K),
         "shk1": lambda: g["shk1"] * st["shk1_m"] * st["shk1_h"] * (v - E_K),
         "unc103": lambda: g["unc103"] * st["unc103_m"] * st["unc103_h"] * (v - E_K),
         "exp2": lambda: g["exp2"] * st["exp2_m"] * st["exp2_h"] ** 2 * (v - E_K)}
    i = {c: f[c]() for c in g}
    return i, sum(i.get(c, 0.0) for c in ("egl19", "unc2", "cca1"))  # every ica writer feeds caintra1


def ca_pool_step(ca, i_ca, sv, dt):
    """caintra1.mod: d[Ca]/dt = -fca * i_ca * (S/V) * 1e-3 / (2F) - ([Ca]-eq)/tau, influx only. ca in M.

    sv is the compartment surface/volume ratio (1/cm); caintra1 used whole-cell surf/vol (AIY 8.88e4 /cm).
    Exponential-Euler update of the linear ODE.
    """
    influx = jnp.where(i_ca <= 0, -CA_FREE * i_ca * sv * 1e-3 / (2 * 96485.0), 0.0)
    ss = CA_EQ_M + influx * CA_TAU
    return ss + (ca - ss) * jnp.exp(-dt / CA_TAU)
