import sys; sys.path.insert(0,'scripts'); sys.path.insert(0,'src')
import numpy as np
from assay_pathways import select
from flyemu import connectome, lif, profiles
from flyemu.registry import Registry, Policy
reg=Registry(Policy.MINIMAL); prof=profiles.apply(reg,'shiu2024')
conn=connectome.build(reg,min_synapses=5); params=lif.default_params(reg,conn,timestep_ms=0.1)
nrn=conn.neurons; kc=nrn.type.fillna('').str.startswith('KC').to_numpy()
pre=np.repeat(np.arange(conn.n),np.diff(conn.indptr)); post=conn.indices
kk=kc[pre]&kc[post]
print('KC->KC edges',kk.sum(),'synapses',conn.weight_syn[kk].sum(),'= %.1f%% of KC output'%(100*conn.weight_syn[kk].sum()/conn.weight_syn[kc[pre]].sum()))
def trial(net_mod, stim, rate, label):
    net=lif.Network(conn,params,0.1,rng=np.random.default_rng(0)); net_mod(net)
    rng=np.random.default_rng(1); on=np.zeros(conn.n); off=np.zeros(conn.n)
    for s in range(8000):
        k=(stim[rng.random(len(stim))<rate*1e-4],prof['kick_mv']) if s<4000 else None
        spk=net.step(kick=k); (on if s<4000 else off)[spk]+=1
    mn9=np.flatnonzero(nrn.type.eq('MN9').to_numpy())
    print(f'{label:28s} active(stim) {int((on>0).sum()):6d}  persisting after {int((off>0).sum()):6d}  MN9 {on[mn9]/0.4} Hz  KC active {int((on[kc]>0).sum())}')
def cut(net): net.w[kk]=0.0
sugar=select(nrn,['LB3b','LB3c']); bitter=select(nrn,['LB1a','LB1b','LB1c','LB1d'])
for lbl,mod in [('intact',lambda n:None),('KC->KC removed',cut)]:
    for sname,st,r in [('sugar 50',sugar,50),('bitter 25',bitter,25),('bitter 100',bitter,100)]:
        trial(mod,st,r,f'{lbl} / {sname}')
