TITLE AWA membrane: calcium-mediated all-or-none action potentials (Liu et al. 2018)

COMMENT
Ported as published: Liu Q, Kidd PB, Dobosiewicz M, Bargmann CI (2018) C. elegans AWA olfactory neurons fire
calcium-mediated all-or-none action potentials. Cell 175:57-70 (bioRxiv 10.1101/359935, CC-BY), STAR Methods
"Modeling" equations and Table S4 (docs/worm/research/liu2018_equations.png, liu2018_tableS4.jpg).

  I_Ca  = gCa (c1 + f c2)(v - vCa)
  c1'   = (cainf_a(v) cainf_i(v)(1 - c2) - c1)/tc1 - (c1 - c2)/tc2(v)
  c2'   = (c1 - c2)/tc2(v)
  cainf_a = 0.5(tanh((v - vc1)/dvc1) + 1),  cainf_i = (tanh((v - vc2)/dvc2) + 1)/c0
  tc2(v) = tc2 / cosh((v - vc3)/dvc3)
  I_Ka  = gKa ka (v - vK), ka' = (kinf_a(v) - ka)/tKa, a = 1, 2, 3 (K1 = SHK-1, K2 and K3 high-voltage K)
  I_Kr  = gKr kr kinf_r1(v)(v - vK), kr' = (kinf_r2(v) - kr)/tKr
  I_Kslow = gKs ks (v - vK), ks' = (kinf_s(v) - ks)/tKs(v), tKs(v) = tKs1 + 0.5(tKs2 - tKs1)(tanh((v - vKs2)/dvKs2) + 1)
            (the paper's "Ka", slowly activating; renamed here to keep it apart from the K1-K3 index)
  I_Kir = gKir(I0 - beta log[1 + exp(-(v - vK - I0)/beta)])        (kir_form 0, default)
  I_Kir = -gKir(beta log[1 + exp(-(v - vK + I0)/beta)] + I0)      (kir_form 1, as printed)
  I_L   = gL (v - vL)

The inward rectifier as printed is inward at every voltage (-4.0 pA at -50 mV, above E_K), which no K+ current can
be, and puts the AWA rest at -64.6 mV against the recorded -75.3 +- 4.7 mV (DEBUG_TRIAGE line 7). The default is the
form in the authors' code (github.com/wormwhisperer/CElegansAWAActionPotentialAnalysis, qiangstoch3c.py, 2018; the
equation is re-written here, not copied): gKir times the smooth minimum of (v - vK) and I0, ohmic below E_K and
saturating at gKir I0 (4 pA) above it. Table S4 calls I0 a 5.0 pA saturated current; the code uses it in mV. The
printed form stays as kir_form 1 for attribution.

Liu's conductances are whole-cell (nS, C = 1.5 pF); the module (wormemu.mech.senses_odor) converts each to a
density g_nS * cm / (1000 * C_pF) S/cm2, which keeps every g/C ratio, so an isopotential cell of any area follows the
published dynamics. The calcium current is written as ica (fixed reversal vCa, as published) so BAAIWorm's calcium
pool (cainternm) and the GCaMP readout see it; the potassium currents are written as ik with the fixed vK.
ENDCOMMENT

NEURON {
    SUFFIX awa_liu
    USEION ca WRITE ica
    USEION k WRITE ik
    NONSPECIFIC_CURRENT il
    RANGE gCa, vCa, f, tc1, tc2, vc1, dvc1, vc2, dvc2, vc3, dvc3, c0
    RANGE vK, gK1, vK1, dvK1, tK1, gK2, vK2, dvK2, tK2, gK3, vK3, dvK3, tK3
    RANGE gKr, vKr1, dvKr1, vKr2, dvKr2, tKr
    RANGE gKs, vKs1, dvKs1, vKs2, dvKs2, tKs1, tKs2
    RANGE gKir, I0, beta, kir_form, gL, vL
    RANGE iCa, iK, iKir
}

UNITS {
    (mA) = (milliamp)
    (mV) = (millivolt)
    (S) = (siemens)
}

PARAMETER {
    : densities in S/cm2 are set by the module from the whole-cell Table S4 values; these defaults are Table S4's
    : WT values at cm = 1 uF/cm2 and C = 1.5 pF
    gCa = 6.667e-05 (S/cm2)
    vCa = 120 (mV)
    f = 0.4
    tc1 = 1.0 (ms)
    tc2 = 160.0 (ms)
    vc1 = -21.6 (mV)
    dvc1 = 9.17 (mV)
    vc2 = 16.2 (mV)
    dvc2 = -16.1 (mV)
    vc3 = 23.0 (mV)
    dvc3 = 24.0 (mV)
    c0 = 0.55
    vK = -84 (mV)
    gK1 = 1.0e-03 (S/cm2)
    vK1 = 2.0 (mV)
    dvK1 = 10.0 (mV)
    tK1 = 30.0 (ms)
    gK2 = 6.667e-04 (S/cm2)
    vK2 = 13.0 (mV)
    dvK2 = 20.0 (mV)
    tK2 = 1000 (ms)
    gK3 = 6.667e-05 (S/cm2)
    vK3 = -25.0 (mV)
    dvK3 = 5.0 (mV)
    tK3 = 1000 (ms)
    gKr = 2.6e-04 (S/cm2)
    vKr1 = -42.0 (mV)
    dvKr1 = 5.0 (mV)
    vKr2 = -42.0 (mV)
    dvKr2 = 5.0 (mV)
    tKr = 1800 (ms)
    gKs = 6.067e-04 (S/cm2)
    vKs1 = -52.0 (mV)
    dvKs1 = 20.0 (mV)
    vKs2 = -32.0 (mV)
    dvKs2 = 4.0 (mV)
    tKs1 = 27000 (ms)
    tKs2 = 3000 (ms)
    gKir = 5.333e-04 (S/cm2)
    I0 = 5.0 (mV)
    beta = 5.0 (mV)
    kir_form = 0
    gL = 1.667e-04 (S/cm2)
    vL = -65.0 (mV)
}

ASSIGNED {
    v (mV)
    ica (mA/cm2)
    ik (mA/cm2)
    il (mA/cm2)
    iCa (mA/cm2)
    iK (mA/cm2)
    iKir (mA/cm2)
}

STATE { c1 c2 k1 k2 k3 kr ks }

BREAKPOINT {
    SOLVE states METHOD derivimplicit
    iCa = gCa * (c1 + f * c2) * (v - vCa)
    if (kir_form > 0.5) {
        iKir = -gKir * (beta * log(1 + exp(-(v - vK + I0) / beta)) + I0)
    } else {
        iKir = gKir * (I0 - beta * softplus(-(v - vK - I0) / beta))
    }
    iK = (gK1 * k1 + gK2 * k2 + gK3 * k3 + gKr * kr * hinf(v, vKr1, dvKr1) + gKs * ks) * (v - vK)
    ica = iCa
    ik = iK + iKir
    il = gL * (v - vL)
}

INITIAL {
    : the published model's steady state at the starting voltage
    c2 = cinfa(v) * cinfi(v) / (1 + cinfa(v) * cinfi(v))
    c1 = c2
    k1 = hinf(v, vK1, dvK1)
    k2 = hinf(v, vK2, dvK2)
    k3 = hinf(v, vK3, dvK3)
    kr = hinf(v, vKr2, dvKr2)
    ks = hinf(v, vKs1, dvKs1)
}

DERIVATIVE states {
    LOCAL t2
    t2 = tc2 / cosh((v - vc3) / dvc3)
    c1' = (cinfa(v) * cinfi(v) * (1 - c2) - c1) / tc1 - (c1 - c2) / t2
    c2' = (c1 - c2) / t2
    k1' = (hinf(v, vK1, dvK1) - k1) / tK1
    k2' = (hinf(v, vK2, dvK2) - k2) / tK2
    k3' = (hinf(v, vK3, dvK3) - k3) / tK3
    kr' = (hinf(v, vKr2, dvKr2) - kr) / tKr
    ks' = (hinf(v, vKs1, dvKs1) - ks) / (tKs1 + 0.5 * (tKs2 - tKs1) * (tanh((v - vKs2) / dvKs2) + 1))
}

FUNCTION hinf(v (mV), vh (mV), dv (mV)) {
    hinf = 0.5 * (tanh((v - vh) / dv) + 1)
}

FUNCTION cinfa(v (mV)) {
    cinfa = 0.5 * (tanh((v - vc1) / dvc1) + 1)
}

FUNCTION cinfi(v (mV)) {
    cinfi = (tanh((v - vc2) / dvc2) + 1) / c0
}

FUNCTION softplus(z) {
    : log(1 + exp(z)), exact to double precision above z = 30
    if (z > 30) {
        softplus = z
    } else {
        softplus = log(1 + exp(z))
    }
}
