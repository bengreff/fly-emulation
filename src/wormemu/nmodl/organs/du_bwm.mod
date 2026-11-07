COMMENT
Body-wall muscle membrane, Du, Crodelle et al. 2025 PLOS Comput Biol 21:e1012318 (code: github.com/XuexingDu/
C.elegans-Muscle, CC-BY 4.0, Muscle_cell_model.ipynb, final wild-type cell). EGL-19 (m^2 h), SHK-1 (n^4), M (p),
SLO-2 (m_inf^3 p_slo2, Ca-gated), Kr (ERG-like), NCA Na leak and leak; one Ca shell (cad, mM) with linear clearance.
Parameters are whole-cell (nS, pF, as published); the current density uses the section area area_um2 (set by
wormemu.mech.muscle_bwm). Every current is NONSPECIFIC: cad is this model's own shell and does not touch cai.
published_init = 1 starts from the code's initial values (m 0.01, h 0.6, n 0.99, p 0.2, kr 0, p_slo2 0, Ca 0),
0 (default) from the steady state at the initial v.
ENDCOMMENT

NEURON {
    SUFFIX du_bwm
    NONSPECIFIC_CURRENT i
    RANGE gca, gk, gm, gslo2, gkr, gna, gl, vth, eca, ek, ena, el, alpha, beta, phi, phi_m, phi_n, tau_h, tau_kr
    RANGE kca, tau_ca, ca0, area_um2, published_init, ica_pA, i_pA
}

UNITS {
    (mV) = (millivolt)
    (mA) = (milliamp)
}

PARAMETER {
    gca = 19.8      : nS
    gk = 37         : nS
    gm = 0          : nS
    gslo2 = 3.6     : nS
    gkr = 3.2       : nS
    gna = 0.1       : nS
    gl = 0.1        : nS
    vth = 10        : mV
    eca = 60        : mV (before the vth shift)
    ek = -40        : mV
    ena = 15        : mV (before the vth shift)
    el = -24        : mV (before the vth shift)
    alpha = 43      : 1/(ms mM2)
    beta = 0.09     : 1/ms
    phi = 0.04
    phi_m = 1.2
    phi_n = 1.2
    tau_h = 24      : ms
    tau_kr = 62     : ms
    kca = 1.5e-5    : mM/(ms pA)
    tau_ca = 13.333333333333334 : ms
    ca0 = 0.001     : mM
    area_um2 = 314.1592653589793
    published_init = 0
}

ASSIGNED {
    v (mV)
    i (mA/cm2)
    ica_pA
    i_pA
    minf mtau hinf ninf ntau pinf ptau krinf
}

STATE { m h n p kr ps cad }

UNITSOFF

INITIAL {
    rates(v)
    if (published_init > 0) {
        m = 0.01  h = 0.6  n = 0.99  p = 0.2  kr = 0  ps = 0  cad = 0
    } else {
        m = minf  h = hinf  n = ninf  p = pinf  kr = krinf
        cad = ca0 - kca * gca * m * m * h * (v - vth - eca) * tau_ca
        ps = alpha * cad * cad / (alpha * cad * cad + beta)
    }
}

BREAKPOINT {
    SOLVE states METHOD cnexp
    ica_pA = gca * m * m * h * (v - vth - eca)
    i_pA = ica_pA + gk * n^4 * (v - vth - ek) + gm * p * (v - vth - ek) + gslo2 * ms3(v) * ps * (v - ek)
    i_pA = i_pA + gna * (v - vth - ena) + gkr * (1 - kr) * krinf_of(v) * (v - ek) + gl * (v - vth - el)
    i = i_pA * 0.1 / area_um2          : pA over um2 -> mA/cm2
}

DERIVATIVE states {
    rates(v)
    m' = (minf - m) / mtau
    h' = (hinf - h) / tau_h
    n' = (ninf - n) / ntau
    p' = (pinf - p) / ptau
    kr' = (krinf - kr) / tau_kr
    ps' = phi * (alpha * cad * cad - ps * (alpha * cad * cad + beta))
    cad' = -kca * gca * m * m * h * (v - vth - eca) - (cad - ca0) / tau_ca
}

FUNCTION ms3(v) {
    ms3 = (1 / (1 + exp(-(v + 33.4) / 3.2)))^3
}

FUNCTION krinf_of(v) {
    krinf_of = 0.5 * (1 + tanh((v - vth + 42) / 5))
}

PROCEDURE rates(v) { LOCAL u
    u = v - vth
    mtau = (0.4 + 0.7 / (exp(-(u + 5) / 15) + exp((u + 5) / 15))) / phi_m
    minf = 1 / (1 + exp(-(u + 8) / 8.6))
    hinf = 0.42 / (1 + exp((u + 11) / 2)) + 0.28
    ninf = 0.5 * (tanh((u + 15.2) / 36.22) + 1)
    ntau = (1.18 + 511.78 / (1 + exp((u + 89.3) / 21.92))) / phi_n
    pinf = 1 / (1 + exp(-(u + 45) / 10))
    ptau = 4000 / (3.38 * exp((u + 45) / 20) + exp(-(u + 45) / 20))
    krinf = krinf_of(v)
}

UNITSON
