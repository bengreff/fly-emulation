"""Silence every cholinergic AL local neuron type: does odour input still ignite? m1."""
import sys; sys.path.insert(0,'scripts'); sys.path.insert(0,'src')
import numpy as np, pandas as pd
from flyemu import connectome, lif, profiles
from flyemu.registry import Registry, Policy
for eff in (0.0825, 0.1925):
    reg=Registry(Policy.MINIMAL); reg.overrides['connection_class:all|efficacy_per_synapse']=eff
    prof=profiles.apply(reg,'m1'); conn=connectome.build(reg,min_synapses=5); params=lif.default_params(reg,conn,timestep_ms=0.1)
    nrn=conn.neurons; t=nrn.type.fillna('')
    ach_ln=(nrn['class'].eq('ALLN') & nrn.predictedNt.eq('acetylcholine')).to_numpy()
    if eff==0.0825: print('cholinergic ALLN types:', t[ach_ln].value_counts().to_dict(), 'of', int(nrn['class'].eq('ALLN').sum()), 'ALLNs')
    st=np.flatnonzero(t.eq('ORN_DM4').to_numpy())
    for sil in (False, True):
        net=lif.Network(conn,params,0.1,rng=np.random.default_rng(0))
        if sil: net.silence(np.flatnonzero(ach_ln))
        rng=np.random.default_rng(1); late=np.zeros(conn.n); on=np.zeros(conn.n)
        for s in range(8000):
            k=(st[rng.random(len(st))<100e-4],prof['kick_mv']) if s<4000 else None
            spk=net.step(kick=k); on[spk]+=1
            if s>=6000: late[spk]+=1
        print(f'eff {eff} cholinergic ALLNs silenced={sil!s:5s} active {int((on>0).sum()):6d} persisting {int((late>0).sum()):6d}', flush=True)
