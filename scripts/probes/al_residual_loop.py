"""After cutting cholinergic-ALLN -> {PN, cholinergic ALLN}, what sustains
odour-evoked persistence? m1 at 0.1155 mV (0.7 x 0.165)."""
import sys; sys.path.insert(0,'scripts'); sys.path.insert(0,'src')
import numpy as np, pandas as pd
from flyemu import connectome, lif, profiles
from flyemu.registry import Registry, Policy
reg=Registry(Policy.MINIMAL); reg.overrides['connection_class:all|efficacy_per_synapse']=0.1155
prof=profiles.apply(reg,'m1'); conn=connectome.build(reg,min_synapses=5); params=lif.default_params(reg,conn,timestep_ms=0.1)
nrn=conn.neurons; t=nrn.type.fillna('')
ach_ln=(nrn['class'].eq('ALLN') & nrn.predictedNt.eq('acetylcholine')).to_numpy(); pn=nrn['class'].eq('ALPN').to_numpy()
pre=np.repeat(np.arange(conn.n),np.diff(conn.indptr)); post=conn.indices
cut=ach_ln[pre]&(pn[post]|ach_ln[post])
st=np.flatnonzero(t.eq('ORN_DM4').to_numpy())
net=lif.Network(conn,params,0.1,rng=np.random.default_rng(0)); net.w[cut]=0
rng=np.random.default_rng(1); late=np.zeros(conn.n)
for s in range(8000):
    k=(st[rng.random(len(st))<150e-4],prof['kick_mv']) if s<4000 else None
    spk=net.step(kick=k)
    if s>=6000: late[spk]+=1
d=nrn.assign(hz=late/0.2)[late>0]
print('persisting', len(d))
print(d.groupby(['type','predictedNt','class']).hz.agg(['size','mean']).sort_values('size',ascending=False).head(18).round(0).to_string())
