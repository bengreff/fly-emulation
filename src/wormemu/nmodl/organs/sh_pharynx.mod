COMMENT
Pharyngeal muscle membrane, Sherman & Harel 2024 PNAS 121:e2302660121 (code: github.com/DanaSherman/CelegansPharynx,
GPLv3: hh_functions.cc, gene.cc "known" values, Params.h, main.cc). CCA-1 (m^2 h, Na + Ca), EGL-19 (m^2 f, Na + Ca,
f inactivated by shell Ca), EXP-2 (m^4 h^4, K), leak. The Ca parts are GHK fluxes with the code's numbers: the
permeabilities times the GHK term are used as uA/cm2, as in main.cc. Gates use the code's Crank-Nicolson update and
its switch: activation kinetics while v rises, the "HP" deactivation / de-inactivation kinetics while it falls
(CCA-1 m, EXP-2 m and h). Two Ca pools per compartment in M: the sub-membrane shell (2 % of the radius; EGL-19's f
reads it) and the core (cac; the MLCK activation reads it), exchanging by radial diffusion, both cleared to rest with
tau_ca. Every current is NONSPECIFIC: cas and cac are this model's own pools and do not touch cai.
The paper's 1-D finite-element cable along the pharynx is replaced by one compartment per muscle cell coupled by
gap junctions (wormemu.mech.organs_pharynx); the shell/core finite elements by the two pools.
INITIAL sets the gates to steady state at vrest (not at v), so the brain's finitialize at its own V_INIT leaves
this cell at its rest once the mechanism sets v = vrest.
ENDCOMMENT

NEURON {
    SUFFIX sh_pharynx
    GLOBAL tadj
    NONSPECIFIC_CURRENT i
    RANGE g_l, v_l, v_na, v_k, g_cca1_na, p_cca1_ca, g_egl19_na, p_egl19_ca, g_exp2
    RANGE cm_A2, cm_v0, cm_dv, cmt_A1, cmt_A2, cmt_v0, cmt_dv, cmt_deact
    RANGE ch_v0, ch_dv, cht_A1, cht_A2, cht_v0, cht_dv
    RANGE em_v0, em_dv, emt_A1, emt_A2, emt_v0, emt_dv
    RANGE ef_A1, ef_ca05, ef_dca, eft_A1, eft_A2, eft_ca05, eft_dca
    RANGE xm_v0, xm_dv, xmt_A1, xmt_A2, xmt_v0, xmt_dv, xmt_pow, xmd_A1, xmd_A2, xmd_v0, xmd_dv
    RANGE xh_v0, xh_dv, xht_A1, xht_A2, xht_v0, xht_dv, xht_deinact
    RANGE rgas, temp_k, faraday, ca_out, ca_rest, tau_ca, shell_av, k_sc, vs_vc, vrest
    RANGE i_cca1_na, i_cca1_ca, i_egl19_na, i_egl19_ca, i_exp2, i_leak, i_uA
}

UNITS {
    (mV) = (millivolt)
    (mA) = (milliamp)
}

PARAMETER {
    tadj = 1                         : mech/temperature.py's pump factor on the gates (1 = T_ref)
    g_l = 0.057651      : mS/cm2
    v_l = -73           : mV
    v_na = 69           : mV
    v_k = -82           : mV
    g_cca1_na = 2.5     : mS/cm2
    p_cca1_ca = 0.009   : code units (x GHK term -> uA/cm2)
    g_egl19_na = 0.1509 : mS/cm2
    p_egl19_ca = 0.001
    g_exp2 = 0.8        : mS/cm2
    cm_A2 = 1.0
    cm_v0 = -30
    cm_dv = 5
    cmt_A1 = 2.7        : ms
    cmt_A2 = 22.3
    cmt_v0 = -52
    cmt_dv = -8
    cmt_deact = 1.0
    ch_v0 = -76
    ch_dv = -4
    cht_A1 = 1
    cht_A2 = 250
    cht_v0 = 0
    cht_dv = -4.5
    em_v0 = 5.6
    em_dv = 7.5
    emt_A1 = 0.5455
    emt_A2 = 0.9635
    emt_v0 = 8.5
    emt_dv = 3
    ef_A1 = 0.8
    ef_ca05 = 1.3e-4    : M
    ef_dca = -5e-6      : M
    eft_A1 = 5
    eft_A2 = 50
    eft_ca05 = 1e-4
    eft_dca = 1e-5
    xm_v0 = -15.5
    xm_dv = 7
    xmt_A1 = 15
    xmt_A2 = 730
    xmt_v0 = -20
    xmt_dv = -0.15
    xmt_pow = 0.8
    xmd_A1 = 65
    xmd_A2 = 75.2
    xmd_v0 = -83.9
    xmd_dv = -3.4
    xh_v0 = -5
    xh_dv = -1
    xht_A1 = 0.3
    xht_A2 = 18
    xht_v0 = -60
    xht_dv = -20
    xht_deinact = 1.0
    rgas = 8.68815102      : J/(mol K), the code's value
    temp_k = 295.65          : K
    faraday = 96485           : C/mol
    ca_out = 0.003      : M
    ca_rest = 5e-8      : M
    tau_ca = 50         : ms
    shell_av = 50505    : 1/cm, shell area over volume
    k_sc = 0.35         : 1/ms, shell -> core exchange per shell volume
    vs_vc = 0.0412      : shell volume over core volume
    vrest = -73         : mV
}

ASSIGNED {
    v (mV)
    i (mA/cm2)
    vprev
    i_cca1_na i_cca1_ca i_egl19_na i_egl19_ca i_exp2 i_leak i_uA
}

STATE { mca hca meg feg mex hex cas cac }

UNITSOFF

INITIAL {
    cas = ca_rest
    cac = ca_rest
    mca = sig(vrest, 0, cm_A2, cm_v0, cm_dv)
    hca = sig(vrest, 0, 1, ch_v0, ch_dv)
    meg = sig(vrest, 0, 1, em_v0, em_dv)
    feg = sig(cas, ef_A1, 1, ef_ca05, ef_dca)
    mex = sig(vrest, 0, 1, xm_v0, xm_dv)
    hex = sig(vrest, 0, 1, xh_v0, xh_dv)
    vprev = vrest
}

BREAKPOINT {
    LOCAL G
    SOLVE states
    G = ghk(v, cas)
    i_cca1_na = g_cca1_na * hca * mca * mca * (v - v_na)
    i_cca1_ca = p_cca1_ca * hca * mca * mca * G
    i_egl19_na = g_egl19_na * feg * meg * meg * (v - v_na)
    i_egl19_ca = p_egl19_ca * feg * meg * meg * G
    i_exp2 = g_exp2 * hex^4 * mex^4 * (v - v_k)
    i_leak = g_l * (v - v_l)
    i_uA = i_cca1_na + i_cca1_ca + i_egl19_na + i_egl19_ca + i_exp2 + i_leak
    i = 1e-3 * i_uA                  : uA/cm2 -> mA/cm2
}

PROCEDURE states() { LOCAL J
    if (v >= vprev) {
        mca = cn(mca, sig(v, 0, cm_A2, cm_v0, cm_dv), sig(v, cmt_A1, cmt_A2, cmt_v0, cmt_dv))
        mex = cn(mex, sig(v, 0, 1, xm_v0, xm_dv), xmt_A1 + xmt_A2 * exp(xmt_dv * pow(fabs(v - xmt_v0), xmt_pow)))
        hex = cn(hex, sig(v, 0, 1, xh_v0, xh_dv), sig(v, xht_A1, xht_A2, xht_v0, xht_dv))
    } else {
        mca = cn(mca, sig(v, 0, cm_A2, cm_v0, cm_dv), cmt_deact)
        mex = cn(mex, sig(v, 0, 1, xm_v0, xm_dv), sig(v, xmd_A1, xmd_A2, xmd_v0, xmd_dv))
        hex = cn(hex, sig(v, 0, 1, xh_v0, xh_dv), xht_deinact)
    }
    hca = cn(hca, sig(v, 0, 1, ch_v0, ch_dv), sig(v, cht_A1, cht_A2, cht_v0, cht_dv))
    meg = cn(meg, sig(v, 0, 1, em_v0, em_dv), sig(v, emt_A1, emt_A2, emt_v0, emt_dv))
    feg = cn(feg, sig(cas, ef_A1, 1, ef_ca05, ef_dca), sig(cas, eft_A1, eft_A2, eft_ca05, eft_dca))
    : Ca: influx into the shell (M/ms), radial exchange and clearance to rest; implicit in the pools
    J = -(p_cca1_ca * hca * mca * mca + p_egl19_ca * feg * meg * meg) * ghk(v, cas) * shell_av / (2 * faraday) * 1e-3
    cas = (cas + dt * (J + ca_rest / tau_ca + k_sc * cac)) / (1 + dt * (1 / tau_ca + k_sc))
    cac = (cac + dt * (ca_rest / tau_ca + k_sc * vs_vc * cas)) / (1 + dt * (1 / tau_ca + k_sc * vs_vc))
    vprev = v
}

FUNCTION sig(x, A1, A2, x0, dx) {
    sig = A1 + (A2 - A1) / (1 + exp(-(x - x0) / dx))
}

FUNCTION cn(g, ginf, tau) { LOCAL a, b
    : the code's Crank-Nicolson gate step (calcGateOpeningProb)
    a = dt * tadj * ginf / tau
    b = dt * tadj * (1 - ginf) / tau
    cn = (a + (1 - 0.5 * (a + b)) * g) / (1 + 0.5 * (a + b))
}

FUNCTION ghk(vm, cin) { LOCAL u, x, e
    : z^2 faraday^2 u / (rgas temp_k) * (cin - ca_out exp(-z faraday u / rgas temp_k)) / (1 - exp(-z faraday u / rgas temp_k)), u in V (calcGca)
    u = 1e-3 * vm
    x = 2 * faraday * u / (rgas * temp_k)
    if (fabs(x) < 1e-6) {
        ghk = 2 * faraday * (cin - ca_out * (1 - x)) / (1 - 0.5 * x)
    } else {
        e = exp(-x)
        ghk = 4 * faraday * faraday * u / (rgas * temp_k) * (cin - ca_out * e) / (1 - e)
    }
}

UNITSON
