TITLE AVL membrane: Jiang et al. 2022's single-cell model (UNC-2, EGL-19, CCA-1, SHL-1, EGL-36, EXP-2, NCA, leak)

COMMENT
Ported as published: Jiang J, Su Y, Zhang R, Li H, Tao L, Liu Q (2022) C. elegans enteric motor neurons fire
synchronized action potentials underlying the defecation motor program. Nat Commun 13:2783 (PMC9120479, CC-BY),
Supplementary Methods (the current equations) and Supplementary Table 1 (WT column). Checked line by line against
the authors' code (github.com/taolab302/AVL-Modeling @ d8303f3, base/AVLModel.m) through the CPU reference
scripts/worm/debug2/jiang22_ref.py; the equations are re-written here, not copied.

  I_UNC2  = g_UNC2 m^2 h (v - v_Ca),  m' = am(1 - m) - bm m,  h' = ah(1 - h) - bh h
            am = m_a (v - m_b)/(1 - exp(-(v - m_b)/m_c)), bm = m_d exp(-(v - m_e)/m_f)
            ah = h_a exp(-(v - h_b)/h_c),                 bh = h_d/(1 + exp(-(v - h_e)/h_f))
  I_EGL19 = g_EGL19 m h (v - v_Ca),   x' = (x_inf - x)/tau_x
            tau_m = s_1 exp(-((v - s_2)/s_3)^2) + s_4 exp(-((v - s_5)/s_6)^2) + s_7
            tau_h = s_8 (s_9/(1 + exp((v - s_10)/s_11)) + s_12/(1 + exp((v - s_13)/s_14)) + s_15)
            m_inf = 1/(1 + exp(-(v - q_1)/q_2))
            h_inf = (q_3/(1 + exp(-(v - q_4)/q_5)) + q_6)(q_7/(1 + exp((v - q_8)/q_9)) + q_10)
  I_CCA1  = g_CCA1 m^2 h (v - v_Ca),  m_inf (c_1, c_2), h_inf (d_1, d_2); tau = a/(1 + exp(-+(v - b)/c)) + d
  I_SHL1  = g_SHL1 m^3 (0.7 hf + 0.3 hs)(v - v_K)
            tau_m = a_m/(exp(-(v - b_m)/c_m) + exp((v - d_m)/e_m)) + f_m; m_inf (v_1, v_2); h_inf (v_3, v_4)
            tau_hf = a_hf/(1 + exp((v - b_hf)/c_hf)) + d_hf; tau_hs the same with _hs
  I_EGL36 = g_EGL36 (w36_f mf + w36_m mm + w36_s ms)(v - v_K), m_inf (e_1, e_2), taus t_f, t_m, t_s
            (weights: Eq. 50 prints 0.33, 0.36, 0.39; the code uses 0.31 for the fast one; the module sets them)
  I_EXP2  = g_EXP2 O (v - v_K), C1 <-> C2 (a1, b1), C2 <-> C3 (Kf, Kb), C3 <-> O (a2, b2), O <-> I (ai, bi),
            C3 <-> I (ai2, psi), psi = b2 bi ai2/(a2 ai), a1 = p_1 exp(p_2 v), b1 = p_3 exp(-p_4 v), Kf = p_5,
            Kb = p_6, a2 = p_7 exp(p_8 v), b2 = p_9 exp(-p_10 v), ai = p_11 exp(p_12 v), bi = p_13 exp(-p_14 v),
            ai2 = p_15 exp(p_16 v); I = 1 - C1 - C2 - C3 - O
  I_NCA   = g_NCA (v - v_Na);  I_L = g_L (v - v_L)

Jiang's conductances are whole-cell (nS, C = 5 pF); the module (wormemu.mech.cell_models) converts each to a density
g_nS * cm / (1000 * C_pF) S/cm2, which keeps every g/C ratio, so an isopotential cell of any area follows the
published dynamics. The Ca currents are written as ica (fixed reversal v_Ca, as published) so BAAIWorm's Ca pool and
the GCaMP readout see them; the K currents as ik with the fixed v_K; NCA and the leak are nonspecific. INITIAL is
the authors' sweep start (every gate 0, EXP-2 in C1).
ENDCOMMENT

NEURON {
    SUFFIX j22avl
    USEION ca WRITE ica
    USEION k WRITE ik
    NONSPECIFIC_CURRENT inca, il
    RANGE g_UNC2, g_EGL19, g_CCA1, g_SHL1, g_EGL36, g_EXP2, g_NCA, g_L
    RANGE i_unc2, i_egl19, i_cca1, i_shl1, i_egl36, i_exp2
    GLOBAL v_Ca, v_K, v_L, v_Na
    GLOBAL m_a, m_b, m_c, m_d, m_e, m_f, h_a, h_b, h_c, h_d, h_e, h_f
    GLOBAL s_1, s_2, s_3, s_4, s_5, s_6, s_7, s_8, s_9, s_10, s_11, s_12, s_13, s_14, s_15
    GLOBAL q_1, q_2, q_3, q_4, q_5, q_6, q_7, q_8, q_9, q_10
    GLOBAL c_1, c_2, c_3, c_4, c_5, c_6, d_1, d_2, d_3, d_4, d_5, d_6
    GLOBAL v_1, v_2, a_m, b_m, c_m, d_m, e_m, f_m, v_3, v_4, a_hf, b_hf, c_hf, d_hf, a_hs, b_hs, c_hs, d_hs
    GLOBAL e_1, e_2, t_f, t_m, t_s, w36_f, w36_m, w36_s
    GLOBAL p_1, p_2, p_3, p_4, p_5, p_6, p_7, p_8, p_9, p_10, p_11, p_12, p_13, p_14, p_15, p_16
}

UNITS {
    (mA) = (milliamp)
    (mV) = (millivolt)
    (S) = (siemens)
}

PARAMETER {
    : densities are set by the module; these defaults are Table 1's WT values at cm = 1 uF/cm2 and C = 5 pF
    g_UNC2 = 2.0e-04 (S/cm2)
    g_EGL19 = 1.5e-04 (S/cm2)
    g_CCA1 = 5.0e-05 (S/cm2)
    g_SHL1 = 8.0e-04 (S/cm2)
    g_EGL36 = 2.7e-04 (S/cm2)
    g_EXP2 = 6.2e-04 (S/cm2)
    g_NCA = 4.0e-06 (S/cm2)
    g_L = 5.4e-05 (S/cm2)
    v_Ca = 100 (mV)
    v_K = -84 (mV)
    v_L = -60 (mV)
    v_Na = 30 (mV)
    : the rate constants below in Table 1's units (ms, mV, /ms); unit checking is left to the module's Specs
    m_a = 0.1
    m_b = 25
    m_c = 10
    m_d = 0.4
    m_e = -25
    m_f = 18
    h_a = 0.01
    h_b = -50
    h_c = 10
    h_d = 0.03
    h_e = -17
    h_f = 17
    s_1 = 2.9
    s_2 = -4.8
    s_3 = 6.0
    s_4 = 1.9
    s_5 = -8.6
    s_6 = 30.0
    s_7 = 2.3
    s_8 = 0.4
    s_9 = 44.6
    s_10 = -33.0
    s_11 = 5.0
    s_12 = 36.4
    s_13 = 18.7
    s_14 = 3.7
    s_15 = 43.1
    q_1 = -4.4
    q_2 = 7.5
    q_3 = 1.43
    q_4 = 14.9
    q_5 = 12
    q_6 = 0.14
    q_7 = 5.96
    q_8 = -20.5
    q_9 = 8.1
    q_10 = 0.6
    c_1 = -43.32
    c_2 = 7.6
    c_3 = 40.0
    c_4 = -62.5
    c_5 = -12.6
    c_6 = 0.7
    d_1 = -58
    d_2 = 7.0
    d_3 = 280
    d_4 = -60.7
    d_5 = 8.5
    d_6 = 19.8
    v_1 = -6.8
    v_2 = 14.1
    a_m = 1.4
    b_m = -17.5
    c_m = 12.9
    d_m = -3.7
    e_m = 6.5
    f_m = 0.2
    v_3 = -33.1
    v_4 = 8.3
    a_hf = 5.9
    b_hf = -8.2
    c_hf = 2.9
    d_hf = 2.73
    a_hs = 84.2
    b_hs = -7.7
    c_hs = 2.4
    d_hs = 11.9
    e_1 = 63
    e_2 = 28.5
    t_f = 13
    t_m = 63
    t_s = 355
    w36_f = 0.33
    w36_m = 0.36
    w36_s = 0.39
    p_1 = 0.0241
    p_2 = 0.0408
    p_3 = 0.0091
    p_4 = 0.030
    p_5 = 0.0372
    p_6 = 0.31
    p_7 = 0.0376
    p_8 = 0.0472
    p_9 = 0.0015
    p_10 = 0.0703
    p_11 = 0.2177
    p_12 = 0.03
    p_13 = 0.0313
    p_14 = 0.1418
    p_15 = 8.7204e-06
    p_16 = 1.4011e-06
}

ASSIGNED {
    v (mV)
    ica (mA/cm2)
    ik (mA/cm2)
    inca (mA/cm2)
    il (mA/cm2)
    i_unc2 (mA/cm2)
    i_egl19 (mA/cm2)
    i_cca1 (mA/cm2)
    i_shl1 (mA/cm2)
    i_egl36 (mA/cm2)
    i_exp2 (mA/cm2)
}

STATE { mU hU mE hE mC hC mS hfS hsS mf36 mm36 ms36 C1 C2 C3 O }

BREAKPOINT {
    SOLVE states METHOD derivimplicit
    i_unc2 = g_UNC2 * mU * mU * hU * (v - v_Ca)
    i_egl19 = g_EGL19 * mE * hE * (v - v_Ca)
    i_cca1 = g_CCA1 * mC * mC * hC * (v - v_Ca)
    i_shl1 = g_SHL1 * mS * mS * mS * (0.7 * hfS + 0.3 * hsS) * (v - v_K)
    i_egl36 = g_EGL36 * (w36_f * mf36 + w36_m * mm36 + w36_s * ms36) * (v - v_K)
    i_exp2 = g_EXP2 * O * (v - v_K)
    ica = i_unc2 + i_egl19 + i_cca1
    ik = i_shl1 + i_egl36 + i_exp2
    inca = g_NCA * (v - v_Na)
    il = g_L * (v - v_L)
}

INITIAL {
    : the authors' sweep start (set_constant_current_sequence.m): every gate 0, EXP-2 in C1
    mU = 0
    hU = 0
    mE = 0
    hE = 0
    mC = 0
    hC = 0
    mS = 0
    hfS = 0
    hsS = 0
    mf36 = 0
    mm36 = 0
    ms36 = 0
    C1 = 1
    C2 = 0
    C3 = 0
    O = 0
}

DERIVATIVE states {
    LOCAL x, am, bm, ah, bh, a1, b1, a2, b2, ai, bi, ai2, psi, Ii, h36
    x = v - m_b
    if (fabs(x) > 1e-9) {
        am = m_a * x / (1 - exp(-x / m_c))
    } else {
        am = m_a * m_c
    }
    bm = m_d * exp(-(v - m_e) / m_f)
    ah = h_a * exp(-(v - h_b) / h_c)
    bh = h_d / (1 + exp(-(v - h_e) / h_f))
    mU' = am * (1 - mU) - bm * mU
    hU' = ah * (1 - hU) - bh * hU
    mE' = (1 / (1 + exp(-(v - q_1) / q_2)) - mE) / (s_1 * exp(-((v - s_2) / s_3)^2) + s_4 * exp(-((v - s_5) / s_6)^2) + s_7)
    hE' = ((q_3 / (1 + exp(-(v - q_4) / q_5)) + q_6) * (q_7 / (1 + exp((v - q_8) / q_9)) + q_10) - hE) / (s_8 * (s_9 / (1 + exp((v - s_10) / s_11)) + s_12 / (1 + exp((v - s_13) / s_14)) + s_15))
    mC' = (1 / (1 + exp(-(v - c_1) / c_2)) - mC) / (c_3 / (1 + exp(-(v - c_4) / c_5)) + c_6)
    hC' = (1 / (1 + exp((v - d_1) / d_2)) - hC) / (d_3 / (1 + exp((v - d_4) / d_5)) + d_6)
    mS' = (1 / (1 + exp(-(v - v_1) / v_2)) - mS) / (a_m / (exp(-(v - b_m) / c_m) + exp((v - d_m) / e_m)) + f_m)
    hfS' = (1 / (1 + exp((v - v_3) / v_4)) - hfS) / (a_hf / (1 + exp((v - b_hf) / c_hf)) + d_hf)
    hsS' = (1 / (1 + exp((v - v_3) / v_4)) - hsS) / (a_hs / (1 + exp((v - b_hs) / c_hs)) + d_hs)
    h36 = 1 / (1 + exp(-(v - e_1) / e_2))
    mf36' = (h36 - mf36) / t_f
    mm36' = (h36 - mm36) / t_m
    ms36' = (h36 - ms36) / t_s
    a1 = p_1 * exp(p_2 * v)
    b1 = p_3 * exp(-p_4 * v)
    a2 = p_7 * exp(p_8 * v)
    b2 = p_9 * exp(-p_10 * v)
    ai = p_11 * exp(p_12 * v)
    bi = p_13 * exp(-p_14 * v)
    ai2 = p_15 * exp(p_16 * v)
    psi = b2 * bi * ai2 / (a2 * ai)
    Ii = 1 - C1 - C2 - C3 - O
    C1' = b1 * C2 - a1 * C1
    C2' = a1 * C1 + p_6 * C3 - (b1 + p_5) * C2
    C3' = p_5 * C2 + psi * Ii + b2 * O - (p_6 + ai2 + a2) * C3
    O' = bi * Ii + a2 * C3 - (b2 + ai) * O
}
