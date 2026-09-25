"""Does adaptation act? Rates of the ignition hub with and without it."""
import sys; sys.path.insert(0,'scripts'); sys.path.insert(0,'src')
import numpy as np
from assay_pathways import select
from flyemu import connectome, lif, profiles
from flyemu.registry import Registry, Policy
for a in (0.0, 2.0):
    reg=Registry(Policy.MINIMAL); reg.overrides['cell_type:all|adaptation_increment']=a
    reg.overrides['connection_class:all|efficacy_per_synapse']=0.275*0.8
    prof=profiles.apply(reg,'shiu2024')
    conn=connectome.build(reg,min_synapses=5); params=lif.default_params(reg,conn,timestep_ms=0.1)
    nrn=conn.neurons; t=nrn.type.fillna('')
    bit=select(nrn,['LB1a','LB1b','LB1c','LB1d']); sug=select(nrn,['LB3b','LB3c'])
    net=lif.Network(conn,params,0.1,rng=np.random.default_rng(0)); rng=np.random.default_rng(1)
    on=np.zeros(conn.n); late=np.zeros(conn.n)
    for s in range(8000):
        k=(sug[rng.random(len(sug))<150e-4],prof['kick_mv']) if s<4000 else None
        spk=net.step(kick=k); on[spk]+=1
        if s>=6000: late[spk]+=1
    act=late>0
    print(f'adapt {a}: persisting {act.sum()}  mean adapt var among persisting {net.adapt[act].mean() if act.any() else 0:.1f} mV')
    if act.any():
        import pandas as pd
        d=nrn[act].assign(hz=late[act]/0.2, ad=net.adapt[act])
        print(d.groupby('type')[['hz','ad']].agg(['size','mean']).sort_values(('hz','size'),ascending=False).head(12).round(1).to_string())
