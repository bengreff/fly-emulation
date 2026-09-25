"""What persists after one odour channel, eLNs silenced, at 0.3x? m1."""
import sys; sys.path.insert(0,'scripts'); sys.path.insert(0,'src')
import numpy as np, pandas as pd
from flyemu import connectome, lif, profiles
from flyemu.registry import Registry, Policy
reg=Registry(Policy.MINIMAL); reg.overrides['connection_class:all|efficacy_per_synapse']=0.0825
prof=profiles.apply(reg,'m1'); conn=connectome.build(reg,min_synapses=5); params=lif.default_params(reg,conn,timestep_ms=0.1)
nrn=conn.neurons; t=nrn.type.fillna('')
st=np.flatnonzero(t.eq('ORN_DM4').to_numpy())
net=lif.Network(conn,params,0.1,rng=np.random.default_rng(0)); net.silence(np.flatnonzero(t.eq('lLN1_bc').to_numpy()))
rng=np.random.default_rng(1); late=np.zeros(conn.n)
for s in range(8000):
    k=(st[rng.random(len(st))<100e-4],prof['kick_mv']) if s<4000 else None
    spk=net.step(kick=k)
    if s>=6000: late[spk]+=1
d=nrn.assign(hz=late/0.2)[late>0]
print(d.groupby(['type','predictedNt']).hz.agg(['size','mean']).sort_values('size',ascending=False).head(15).round(0).to_string())
print(d.superclass.value_counts().head(5).to_dict())
