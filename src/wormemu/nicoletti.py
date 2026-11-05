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


KCNL_KM_M, KCNL_TAU = 0.33e-6, 6.3
CA_EQ_M, CA_TAU, CA_FREE = 0.05e-6, 50.0, 0.001  # caintra1.mod

# Channel names in a fixed order; a neuron's model is a 0/1 mask over these plus fitted densities.
CHANNELS = ["leak", "nca", "egl19", "unc2", "kqt1", "shl1", "slo1egl19", "slo1unc2", "slo1iso",
            "slo2egl19", "slo2unc2", "slo2iso", "kcnl"]
# CeNGEN gene that gates each channel's inclusion (leak is always on).
GENE = {"leak": None, "nca": "nca-1|nca-2", "egl19": "egl-19", "unc2": "unc-2", "kqt1": "kqt-1", "shl1": "shl-1",
        "slo1egl19": "slo-1&egl-19", "slo1unc2": "slo-1&unc-2", "slo1iso": "slo-1", "slo2egl19": "slo-2&egl-19",
        "slo2unc2": "slo-2&unc-2", "slo2iso": "slo-2", "kcnl": "kcnl-1|kcnl-2|kcnl-3|kcnl-4"}
STATES = ["egl19_m", "egl19_h", "unc2_m", "unc2_h", "kqt1_m", "kqt1_s", "shl1_m", "shl1_hf", "shl1_hs",
          "slo1egl19_m", "slo1unc2_m", "slo1iso_m", "slo2egl19_m", "slo2unc2_m", "slo2iso_m", "kcnl_m", "ca"]


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
    return r, e, u


def coupled_rates(v, st, e, u, e_ca=E_CA):
    return {"slo1egl19_m": slo_coupled_rates(v, SLO1, e[0], e[1], st["egl19_m"], e_ca),
            "slo1unc2_m": slo_coupled_rates(v, SLO1, u[0], u[1], st["unc2_m"], e_ca),
            "slo2egl19_m": slo_coupled_rates(v, SLO2, e[0], e[1], st["egl19_m"], e_ca),
            "slo2unc2_m": slo_coupled_rates(v, SLO2, u[0], u[1], st["unc2_m"], e_ca)}


def currents(v, st, g, e_leak, e_ca=E_CA):
    """Per-channel currents (mA/cm2) given gates st and densities g (S/cm2). Returns (dict, i_ca)."""
    i = {"leak": g["leak"] * (v - e_leak), "nca": g["nca"] * (v - E_NCA),
         "egl19": g["egl19"] * st["egl19_m"] * st["egl19_h"] * (v - e_ca),
         "unc2": g["unc2"] * st["unc2_m"] * st["unc2_h"] * (v - e_ca),
         "kqt1": g["kqt1"] * st["kqt1_m"] * st["kqt1_s"] * (v - E_K),
         "shl1": g["shl1"] * st["shl1_m"] * (0.8 * st["shl1_hf"] + 0.2 * st["shl1_hs"]) * (v - E_K),
         "slo1egl19": g["slo1egl19"] * st["slo1egl19_m"] * st["egl19_h"] * (v - E_K),
         "slo1unc2": g["slo1unc2"] * st["slo1unc2_m"] * st["unc2_h"] * (v - E_K),
         "slo1iso": g["slo1iso"] * st["slo1iso_m"] * (v - E_K),
         "slo2egl19": g["slo2egl19"] * st["slo2egl19_m"] * st["egl19_h"] * (v - E_K),
         "slo2unc2": g["slo2unc2"] * st["slo2unc2_m"] * st["unc2_h"] * (v - E_K),
         "slo2iso": g["slo2iso"] * st["slo2iso_m"] * (v - E_K),
         "kcnl": g["kcnl"] * st["kcnl_m"] * (v - E_K)}
    return i, i["egl19"] + i["unc2"]


def ca_pool_step(ca, i_ca, sv, dt):
    """caintra1.mod: d[Ca]/dt = -fca * i_ca * (S/V) * 1e-3 / (2F) - ([Ca]-eq)/tau, influx only. ca in M.

    sv is the compartment surface/volume ratio (1/cm); caintra1 used whole-cell surf/vol (AIY 8.88e4 /cm).
    Exponential-Euler update of the linear ODE.
    """
    influx = jnp.where(i_ca <= 0, -CA_FREE * i_ca * sv * 1e-3 / (2 * 96485.0), 0.0)
    ss = CA_EQ_M + influx * CA_TAU
    return ss + (ca - ss) * jnp.exp(-dt / CA_TAU)
