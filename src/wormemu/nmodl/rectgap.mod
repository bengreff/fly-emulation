TITLE Rectifying gap junction half (wormemu; gap_rectification toggle)

COMMENT
BAAIWorm's gapjunction.mod (i = weight * (v - vpre)) with a direction: the full conductance when current flows
into the receiving cell (side = +1 on the receiving half, -1 on the other half), weight / ratio the other way.
Both halves of one junction see the same sign of the voltage difference, so the current stays conserved; at
zero difference the current is zero either way, so it stays continuous. ratio = 1 is BAAIWorm's junction.
Used for AVA-class to A/B motor neuron junctions: current passes from the motor neuron (UNC-9) into the
interneuron (UNC-7) (Liu, Chen, Mailler and Wang 2017, Nat Commun 8:14818, paired recording of AVA and VA5).
ENDCOMMENT

UNITS {
    (mV) = (millivolt)
    (nA) = (nanoamp)
    (uS) = (microsiemens)
}

NEURON {
    POINT_PROCESS rectgap
    POINTER vpre
    RANGE weight, ratio, side, i
    NONSPECIFIC_CURRENT i
}

PARAMETER {
    weight = 0.0 (uS)
    ratio = 1.0 (1)
    side = 1.0 (1)
}

ASSIGNED {
    v (mV)
    vpre (mV)
    i (nA)
}

BREAKPOINT {
    if (side * (vpre - v) > 0) {
        i = weight * (v - vpre)
    } else {
        i = weight / ratio * (v - vpre)
    }
}
