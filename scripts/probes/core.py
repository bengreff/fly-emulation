import sys; sys.path.insert(0,'scripts'); sys.path.insert(0,'src')
import numpy as np
from assay_pathways import select
from flyemu import connectome, lif, profiles
from flyemu.registry import Registry, Policy
reg=Registry(Policy.MINIMAL); reg.overrides['connection_class:all|efficacy_per_synapse']=0.165
prof=profiles.apply(reg,'shiu2024')
conn=connectome.build(reg,min_synapses=5); params=lif.default_params(reg,conn,timestep_ms=0.1)
nrn=conn.neurons; t=nrn.type.fillna('')
bitter=select(nrn,['LB1a','LB1b','LB1c','LB1d'])
apl=np.flatnonzero(t.eq('APL').to_numpy())
groups={'none':[], 'all KCs':np.flatnonzero(t.str.startswith('KC').to_numpy()),
 'lLN1_bc':np.flatnonzero(t.eq('lLN1_bc').to_numpy()),
 'CX ring (EPG,PEN,Delta7,EL,ER*)':np.flatnonzero(t.str.match(r'^(EPG|PEN_|Delta7|EL$|ER\d)').to_numpy())}
for name,g in groups.items():
    net=lif.Network(conn,params,0.1,rng=np.random.default_rng(0)); net.silence(g)
    rng=np.random.default_rng(1); on=np.zeros(conn.n); late=np.zeros(conn.n)
    for s in range(8000):
        k=(bitter[rng.random(len(bitter))<50e-4],prof['kick_mv']) if s<4000 else None
        spk=net.step(kick=k); on[spk]+=1
        if s>=6000: late[spk]+=1
    print(f'silenced {name:34s} n={len(g):5d}  active {int((on>0).sum()):5d}  persisting 600-800 ms {int((late>0).sum()):5d}  APL {on[apl]/0.4} Hz')
