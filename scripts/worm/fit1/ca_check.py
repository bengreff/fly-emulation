import sys, time, numpy as np
sys.path.insert(0, 'src')
from wormemu.brain import Brain, sample_worm
t0=time.time()
b = Brain(sample_worm(None), cells=["AVAL"])
print('build s', round(time.time()-t0,1))
h=b.h; s=b.soma[0]
print('soma area um2', round(sum(seg.area() for seg in s),1), 'vcell', s(0.5).vcell_cainternm if hasattr(s(0.5),'vcell_cainternm') else None)
b.reset()
for amp in (0, 5, 20):
    b.reset(); b.extra_pA[:] = 0
    for k in range(400): b.step(dt_ms=1.0)
    b.extra_pA[0] = amp
    vs, cs, ics = [], [], []
    for k in range(1000):
        o = b.step(dt_ms=1.0); vs.append(o.v_mV[0]); cs.append(o.ca_uM[0]); ics.append(s(0.5).ica)
    print(f'step {amp} pA: v {vs[0]:.1f}->{max(vs):.1f} mV, ca {cs[0]:.5f}->{max(cs):.5f} uM, ica min {min(ics):.3e} mA/cm2')
