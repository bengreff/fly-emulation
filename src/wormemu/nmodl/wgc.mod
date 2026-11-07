TITLE Settable conductance with a fixed reversal (wormemu; ligand-gated channels outside synapses)

COMMENT
i = g * (v - e). The brain's mechanisms set g each step (e.g. mech/neuromod.py: MOD-1, LGC-55 and LGC-53 opened by
the compartment's amine concentration); NEURON treats the current implicitly, so a large g stays stable at any step.
ENDCOMMENT

NEURON {
    POINT_PROCESS wgc
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
