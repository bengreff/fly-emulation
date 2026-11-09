"""The general fit's machinery (weki, phase 2 of the debugging pass, 8 Nov 2026). Nothing here fits real data until
the gate passes and Ben says go (docs/worm/FIT_GENERAL.md).

    vitals      the vital-signs battery: the entire worm's physiology read out of one closed-loop run per condition
    maturation  activity-dependent channel-density tuning before scoring (tested on the recorded cells first)
    eki         ensemble Kalman inversion on bounded, transformed parameters
"""
