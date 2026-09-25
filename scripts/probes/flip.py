import sys; sys.path.insert(0,'scripts'); sys.path.insert(0,'src')
import numpy as np, dataclasses
from assay_pathways import select
from flyemu import connectome, lif, profiles
from flyemu.registry import Registry, Policy
reg=Registry(Policy.MINIMAL); prof=profiles.apply(reg,'shiu2024')
conn=connectome.build(reg,min_synapses=5); params=lif.default_params(reg,conn,timestep_ms=0.1)
nrn=conn.neurons; t=nrn.type.fillna('')
ln=np.flatnonzero(t.eq('lLN1_bc').to_numpy())
s2=conn.sign.copy(); s2[ln]=-1; flipped=dataclasses.replace(conn,sign=s2)
sug=select(nrn,['LB3b','LB3c']); bit=select(nrn,['LB1a','LB1b','LB1c','LB1d']); mn9=select(nrn,['MN9'])
for gain in (0.6,1.0):
  for gname,g in (('as predicted (ACh)',conn),('lLN1_bc inhibitory',flipped)):
    for sname,st,r in (('sugar 150',sug,150),('bitter 50',bit,50)):
        net=lif.Network(g,params,0.1,rng=np.random.default_rng(0)); net.w*=gain/1.0*(0.275/0.275)
        rng=np.random.default_rng(1); on=np.zeros(conn.n); late=np.zeros(conn.n)
        for s in range(8000):
            k=(st[rng.random(len(st))<r*1e-4],prof['kick_mv']) if s<4000 else None
            spk=net.step(kick=k); on[spk]+=1
            if s>=6000: late[spk]+=1
        print(f'gain {gain}  {gname:20s} {sname:10s} active {int((on>0).sum()):6d} persisting {int((late>0).sum()):6d}  MN9 {np.round(on[mn9]/0.4,1)}',flush=True)
