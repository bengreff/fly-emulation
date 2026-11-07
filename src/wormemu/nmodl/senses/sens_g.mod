TITLE SensG: a sensory channel population as one conductance with a reversal potential

COMMENT
The sensory mechanisms (wormemu.mech.senses_*) set g each step from their transduction cascades (open probability x
maximal conductance); NEURON integrates the current implicitly, so a large sensory conductance stays stable at the
brain's 0.5 ms step whatever the exchange interval. One per (cell, channel class), at the soma.
ENDCOMMENT

NEURON {
    POINT_PROCESS SensG
    NONSPECIFIC_CURRENT i
    RANGE g, e, i
}

UNITS {
    (nA) = (nanoamp)
    (mV) = (millivolt)
    (uS) = (microsiemens)
}

PARAMETER {
    g = 0 (uS)
    e = 0 (mV)
}

ASSIGNED {
    v (mV)
    i (nA)
}

BREAKPOINT {
    i = g * (v - e)
}
