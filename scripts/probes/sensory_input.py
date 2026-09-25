"""Diagnostic: does removing central synapses ONTO sensory neurons stop ignition?"""
import sys; sys.path.insert(0,'scripts'); sys.path.insert(0,'src')
import numpy as np
from assay_pathways import select
from flyemu import connectome, lif, profiles
from flyemu.registry import Registry, Policy
for scale in (0.6, 1.0):
    reg=Registry(Policy.MINIMAL); reg.overrides['connection_class:all|efficacy_per_synapse']=0.275*scale
    prof=profiles.apply(reg,'shiu2024')
    conn=connectome.build(reg,min_synapses=5); params=lif.default_params(reg,conn,timestep_ms=0.1)
    nrn=conn.neurons
    sens=nrn.superclass.fillna('').str.contains('sensory').to_numpy()
    onto=sens[conn.indices]
    if scale==0.6: print('sensory neurons',sens.sum(),' edges onto them',onto.sum(),' synapses',int(conn.weight_syn[onto].sum()),'(%.1f%%)'%(100*conn.weight_syn[onto].sum()/conn.weight_syn.sum()))
    bit=select(nrn,['LB1a','LB1b','LB1c','LB1d']); sug=select(nrn,['LB3b','LB3c']); mn9=select(nrn,['MN9'])
    for lbl,cut in (('intact',False),('no input onto sensory',True)):
        for sn,st,r in (('sugar150',sug,150),('bitter50',bit,50)):
            net=lif.Network(conn,params,0.1,rng=np.random.default_rng(0))
            if cut: net.w[onto]=0
            rng=np.random.default_rng(1); on=np.zeros(conn.n); late=np.zeros(conn.n)
            for s in range(8000):
                k=(st[rng.random(len(st))<r*1e-4],prof['kick_mv']) if s<4000 else None
                spk=net.step(kick=k); on[spk]+=1
                if s>=6000: late[spk]+=1
            print(f'scale {scale} {lbl:22s} {sn:9s} active {int((on>0).sum()):6d} persisting {int((late>0).sum()):6d} MN9 {np.round(on[mn9]/0.4,1)}',flush=True)
