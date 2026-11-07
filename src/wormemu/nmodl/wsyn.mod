TITLE Graded chemical synapse with one ionotropic receptor class (wormemu; receptor_kinetics toggle)

COMMENT
One receptor class at one synaptic site (PLAN row 7; docs/worm/research/PORT_SOURCES_NEURAL.md N1).

Release (presynaptic, graded): BAAIWorm's graded synapse state, unchanged (third_party/baaiworm/mod/
neuron_to_neuron_exc_syn.mod): s' = (sinf - s)/tau, sinf = 1/(1 + exp((Vth - vpre)/delta)), tau = (1 - sinf)/k.
s is the release fraction (0 to 1). Cleft transmitter T = tmax * relgain * s (mM); relgain is a presynaptic
release multiplier set by the brain from mechanisms' g_scale "release" (1 = neutral).

Receptor (postsynaptic), mode 2 (kinetic):
  a = T^hill / (T^hill + ec50^hill)               steady-state activation, the class's measured dose-response
  r' = (a - r)/tau_r, tau_r = tau_off + (tau_rise - tau_off) * a
                                                   opens with tau_rise at saturating transmitter, closes with
                                                   tau_off when transmitter is gone; steady state r = a exactly
  d' = (r * (1 - ss) - d)/tau_des                   desensitization: under a saturating step the open fraction
                                                   falls from 1 to ss with tau_des; tau_des = 0 means none
  open = r * (1 - d)
mode 1 (instantaneous, the nested form in PORT_SOURCES N1 (f)): open = a, no desensitization.
mode 0 (graded, BAAIWorm's form): open = s (relgain and recgain multiply the conductance); with gmax = weight *
conductance and BAAIWorm's erev this is neuron_to_neuron_exc_syn / _inh_syn exactly (the neutral-equivalence test).

Mg block (NMDA-like classes; mg = 0 means none): B(v) = 1 / (1 + exp(-mgk * v) * mg / mgc) (Jahr and Stevens
1990 J Neurosci 10:3178). i = gmax * recgain * open * B(v) * (v - erev); recgain is the postsynaptic receptor
multiplier from mechanisms' g_scale "rec_<class>" (1 = neutral).

Short-term plasticity (row 24; mech/plasticity.py, graded form of Dittman, Kreitzer and Regehr 2000 J Neurosci
20:1374), driven by the release fraction s taken at the start of the step:
  cF' = s - cF/tauF, cD' = s - cD/tauD           residual-Ca traces (ms of full release)
  F = F1 + (1 - F1) cF/(cF + KF)                  release probability, F1 at rest
  krec = k0 + (kmax - k0) cD/(cD + KD)            Ca-accelerated recovery
  x' = (1 - x) krec - beta F s x                  vesicle resource
  z' = (1 - z)/tau_h - beta_h s z                 slow resource (tap habituation; beta_h = 0 except touch cells)
  q = x z F/F1/q0                                 quantal content relative to the INITIAL steady state (q0 there;
                                                  tonic release keeps x, z < 1 at rest); g = g * q in every mode
The defaults (beta = 0, beta_h = 0, F1 = 1) keep x = z = q = 1 exactly: the synapse without plasticity.
Quantal noise (row 26; mech/noise.py): gd = the deterministic conductance (before the Mg block), read by the
module each step; qn = that step's vesicle shot noise over its mean, set by the module (default 1 = no noise).
ENDCOMMENT

NEURON {
    POINT_PROCESS wsyn
    POINTER vpre
    NONSPECIFIC_CURRENT i
    RANGE gmax, erev, delta, k, Vth, mode, tmax, ec50, hill, tau_rise, tau_off, tau_des, ss, mg, mgk, mgc
    RANGE relgain, recgain, i, g, T, a
    RANGE F1, tauF, KF, beta, k0, kmax, KD, tauD, beta_h, tau_h, q, qn, gd
}

UNITS {
    (nA) = (nanoamp)
    (mV) = (millivolt)
    (uS) = (microsiemens)
    (mM) = (milli/liter)
}

PARAMETER {
    gmax = 0 (uS)
    erev = 0 (mV)
    delta = 5 (mV)
    k = 0.1166666666666666 (/ms)
    Vth = -20 (mV)
    mode = 2
    tmax = 0.1 (mM)
    ec50 = 0.026 (mM)
    hill = 1
    tau_rise = 0.5 (ms)
    tau_off = 6.5 (ms)
    tau_des = 0 (ms)
    ss = 1
    mg = 0 (mM)
    mgk = 0.062 (/mV)
    mgc = 3.57 (mM)
    relgain = 1
    recgain = 1
    qn = 1
    F1 = 1
    tauF = 100 (ms)
    KF = 20 (ms)
    beta = 0 (/ms)
    k0 = 0.0002 (/ms)
    kmax = 0.005 (/ms)
    KD = 20 (ms)
    tauD = 500 (ms)
    beta_h = 0 (/ms)
    tau_h = 600000 (ms)
}

ASSIGNED {
    v (mV)
    vpre (mV)
    i (nA)
    g (uS)
    T (mM)
    a
    sinf
    tau (ms)
    tau_r (ms)
    tau_d (ms)
    dinf
    srel
    F
    krec (/ms)
    q
    q0
    gd (uS)
}

STATE {
    s
    r
    d
    x
    z
    cF (ms)
    cD (ms)
}

INITIAL {
    rates()
    s = sinf
    act()
    r = a
    dinf = 0
    if (tau_des > 0) {
        dinf = r * (1 - ss)
    }
    d = dinf
    cF = s * tauF                                   : plasticity starts at its steady state for the initial vpre
    cD = s * tauD                                   : (tonic graded release at rest depletes and habituates)
    F = F1 + (1 - F1) * cF / (cF + KF)
    krec = k0 + (kmax - k0) * cD / (cD + KD)
    x = krec / (krec + beta * F * s)
    z = 1 / (1 + beta_h * s * tau_h)
    q0 = x * z * F / F1                             : q is relative to this resting state
}

BREAKPOINT {
    SOLVE states METHOD cnexp
    if (mode == 0) {
        g = gmax * s * recgain * relgain
    } else if (mode == 1) {
        act()
        g = gmax * recgain * a
    } else {
        g = gmax * recgain * r * (1 - d)
    }
    q = x * z * (F1 + (1 - F1) * cF / (cF + KF)) / F1 / q0
    g = g * q
    gd = g
    g = g * qn
    if (mg > 0) {
        g = g / (1 + exp(-mgk * v) * mg / mgc)
    }
    i = g * (v - erev)
}

DERIVATIVE states {
    rates()
    act()
    tau_r = tau_off + (tau_rise - tau_off) * a
    if (tau_des > 0) {
        tau_d = tau_des
        dinf = r * (1 - ss)
    } else {
        tau_d = 1e9
        dinf = 0
    }
    srel = s
    F = F1 + (1 - F1) * cF / (cF + KF)
    krec = k0 + (kmax - k0) * cD / (cD + KD)
    s' = (sinf - s)/tau
    r' = (a - r)/tau_r
    d' = (dinf - d)/tau_d
    x' = (1 - x) * krec - beta * F * srel * x
    z' = (1 - z)/tau_h - beta_h * srel * z
    cF' = srel - cF/tauF
    cD' = srel - cD/tauD
}

PROCEDURE rates() {
    sinf = 1/(1 + exp((Vth - vpre)/delta))
    tau = (1 - sinf)/k
}

PROCEDURE act() {
    T = tmax * relgain * s
    if (T > 0) {
        a = 1/(1 + pow(ec50/T, hill))
    } else {
        a = 0
    }
}
