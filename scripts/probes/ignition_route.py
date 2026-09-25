"""Order of recruitment from bitter GRNs into the ignited state (0.6x, no adaptation)."""
import sys; sys.path.insert(0,'scripts'); sys.path.insert(0,'src')
import numpy as np, pandas as pd
from assay_pathways import select
from flyemu import connectome, lif, profiles
from flyemu.registry import Registry, Policy
reg=Registry(Policy.MINIMAL); reg.overrides['connection_class:all|efficacy_per_synapse']=0.165
prof=profiles.apply(reg,'shiu2024')
conn=connectome.build(reg,min_synapses=5); params=lif.default_params(reg,conn,timestep_ms=0.1)
nrn=conn.neurons; bit=select(nrn,['LB1a','LB1b','LB1c','LB1d'])
net=lif.Network(conn,params,0.1,rng=np.random.default_rng(0)); rng=np.random.default_rng(1)
first=np.full(conn.n,np.inf); cnt=np.zeros(conn.n)
for s in range(4000):
    spk=net.step(kick=(bit[rng.random(len(bit))<50e-4],prof['kick_mv'])); first[spk]=np.minimum(first[spk],s*0.1); cnt[spk]+=1
d=nrn.assign(first=first,n=cnt)[np.isfinite(first)]
g=d.groupby('type').agg(first=('first','min'),cells=('first','size'),nt=('predictedNt','first'),sc=('superclass','first')).sort_values('first')
print(g.head(45).to_string())
print('lLN1_bc first spike', d.loc[d.type=='lLN1_bc','first'].min(), 'ms; total active', len(d))
