import sys; sys.path.insert(0,'scripts'); sys.path.insert(0,'src')
import numpy as np, pandas as pd
from assay_pathways import run_trial, select
from flyemu import connectome, lif, profiles
from flyemu.registry import Registry, Policy
reg=Registry(Policy.MINIMAL); prof=profiles.apply(reg,'shiu2024')
conn=connectome.build(reg,min_synapses=5); params=lif.default_params(reg,conn,timestep_ms=0.1)
nrn=conn.neurons
stim=select(nrn,['LB1a','LB1b','LB1c','LB1d'])
# short stim then silence: is it self-sustaining?
import flyemu.lif as L
net=L.Network(conn,params,0.1,rng=np.random.default_rng(0)); rng=np.random.default_rng(1)
first=np.full(conn.n,np.inf); counts_on=np.zeros(conn.n); counts_off=np.zeros(conn.n)
for s in range(8000):
    k=None
    if s<2000: k=(stim[rng.random(len(stim))<25*0.1/1000],prof['kick_mv'])
    spk=net.step(kick=k)
    first[spk]=np.minimum(first[spk],s*0.1)
    (counts_on if s<4000 else counts_off)[spk]+=1
print('active during 0-400ms',(counts_on>0).sum(),' active 400-800ms (stim ended at 200)',(counts_off>0).sum())
act=counts_off>0
df=nrn.assign(hz=counts_off/0.4,first=first)[act]
print(df.superclass.value_counts().head(10))
print(df.groupby('type').hz.agg(['size','mean']).sort_values('size',ascending=False).head(25))
# earliest recruited non-stim neurons
print(df.sort_values('first')[['type','superclass','first']].head(25).to_string())
print('MN9 hz', df.loc[df.type=='MN9','hz'].tolist())
