TITLE AFD membrane: Naudin et al. 2022's AFD model (I_Ca,p + I_Kir + I_K,t + I_L)

COMMENT
Ported as published: Naudin L, Jimenez Laredo JL, Liu Q, Corson N (2022) Systematic generation of biophysically
detailed models with generalization capability for non-spiking neurons. PLoS ONE 17:e0268380 (PMC9106219, CC-BY);
the equations of S1 Table (the I_Ca,p + I_Kir + I_K,t + I_L model, chosen for AFD in Naudin et al. 2020, Int J
Neural Syst) and the multi-objective AFD column of S2 Table, fitted to Liu lab AFD recordings (current clamp -15 to
+35 pA, voltage clamp -100 to +50 mV). The single-objective column is not ported: the authors reject it for AFD
("not acceptable and inadequate for the description of the AFD neuron behavior", Results, Fig 3).

  C dV/dt = -I_Ca - I_Kir - I_K - I_L + I
  I_Ca  = g_Ca mCa (v - e_Ca),        mCa' = (b(v, vh_mCa, k_mCa) - mCa)/tau_mCa
  I_Kir = g_Kir b(v, vh_Kir, k_Kir) (v - e_K)        (instantaneous; k_Kir < 0, so it opens on hyperpolarisation)
  I_K   = g_K mK hK (v - e_K),        mK' = (b(v, vh_mK, k_mK) - mK)/tau_mK,  hK' = (b(v, vh_hK, k_hK) - hK)/tau_hK
  I_L   = g_L (v - e_L)
  b(v, vh, k) = 1/(1 + exp((vh - v)/k))

Naudin's time unit is the decisecond (a 50 ds sweep sampled every 0.004 ds = 0.4 ms) and their conductances are
whole-cell nS; the module (wormemu.mech.cell_models) converts the taus to ms (x 100), C to pF (x 100: pA ds/mV), and
each g to a density g_nS * cm / (1000 * C_pF) S/cm2, which keeps every g/C ratio. I_Ca is written as ica (fixed
e_Ca, as published) so BAAIWorm's Ca pool and the GCaMP readout see it; I_Kir and I_K as ik with the fixed e_K;
the leak is nonspecific. INITIAL puts every gate at its steady state at the start voltage (Naudin fitted m0, h0 to
their sweep start; the brain settles before any stimulus).
ENDCOMMENT

NEURON {
    SUFFIX n22afd
    USEION ca WRITE ica
    USEION k WRITE ik
    NONSPECIFIC_CURRENT il
    RANGE g_Ca, g_Kir, g_K, g_L, i_ca, i_kir, i_k
    GLOBAL e_Ca, e_K, e_L, vh_mCa, k_mCa, vh_Kir, k_Kir, vh_mK, k_mK, vh_hK, k_hK, tau_mCa, tau_mK, tau_hK
}

UNITS {
    (mA) = (milliamp)
    (mV) = (millivolt)
    (S) = (siemens)
}

PARAMETER {
    : densities are set by the module; these defaults are S2 Table's multi-objective AFD values at cm 1 and C 6.6 pF
    g_Ca = 1.0151515e-03 (S/cm2)
    g_Kir = 3.5151515e-04 (S/cm2)
    g_K = 4.2439394e-03 (S/cm2)
    g_L = 6.0606061e-07 (S/cm2)
    e_Ca = 23.61 (mV)
    e_K = -79.26 (mV)
    e_L = -89.43 (mV)
    vh_mCa = -3.65 (mV)
    k_mCa = 7.25 (mV)
    vh_Kir = -86.19 (mV)
    k_Kir = -9.01 (mV)
    vh_mK = -2.54 (mV)
    k_mK = 8.44 (mV)
    vh_hK = -64.19 (mV)
    k_hK = -29.36 (mV)
    tau_mCa = 562 (ms)
    tau_mK = 0.01 (ms)
    tau_hK = 4.5 (ms)
}

ASSIGNED {
    v (mV)
    ica (mA/cm2)
    ik (mA/cm2)
    il (mA/cm2)
    i_ca (mA/cm2)
    i_kir (mA/cm2)
    i_k (mA/cm2)
}

STATE { mCa mK hK }

BREAKPOINT {
    SOLVE states METHOD cnexp
    i_ca = g_Ca * mCa * (v - e_Ca)
    i_kir = g_Kir * b(v, vh_Kir, k_Kir) * (v - e_K)
    i_k = g_K * mK * hK * (v - e_K)
    ica = i_ca
    ik = i_kir + i_k
    il = g_L * (v - e_L)
}

INITIAL {
    mCa = b(v, vh_mCa, k_mCa)
    mK = b(v, vh_mK, k_mK)
    hK = b(v, vh_hK, k_hK)
}

DERIVATIVE states {
    mCa' = (b(v, vh_mCa, k_mCa) - mCa) / tau_mCa
    mK' = (b(v, vh_mK, k_mK) - mK) / tau_mK
    hK' = (b(v, vh_hK, k_hK) - hK) / tau_hK
}

FUNCTION b(v (mV), vh (mV), k (mV)) {
    b = 1 / (1 + exp((vh - v) / k))
}
