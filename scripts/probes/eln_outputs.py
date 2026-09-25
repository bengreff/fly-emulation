"""Diagnostic: which eLN (lLN1_bc) chemical outputs carry the ignition? m1, 0.1925 mV."""
import sys; sys.path.insert(0,'scripts'); sys.path.insert(0,'src')
import numpy as np
from assay_pathways import select
from flyemu import connectome, lif, profiles
from flyemu.registry import Registry, Policy
reg=Registry(Policy.MINIMAL); reg.overrides['connection_class:all|efficacy_per_synapse']=0.1925
prof=profiles.apply(reg,'m1'); conn=connectome.build(reg,min_synapses=5); params=lif.default_params(reg,conn,timestep_ms=0.1)
nrn=conn.neurons; t=nrn.type.fillna(''); cls=nrn['class'].fillna('')
eln=t.eq('lLN1_bc').to_numpy(); pn=cls.eq('ALPN').to_numpy()
pre=np.repeat(np.arange(conn.n),np.diff(conn.indptr)); post=conn.indices
cut={'none':np.zeros(len(post),bool),'eLN->PN':eln[pre]&pn[post],'eLN->eLN':eln[pre]&eln[post],
     'eLN->PN and eLN->eLN':eln[pre]&(pn[post]|eln[post])}
tot=conn.weight_syn[eln[pre]].sum()
bit=select(nrn,['LB1a','LB1b','LB1c','LB1d']); sug=select(nrn,['LB3b','LB3c']); mn9=select(nrn,['MN9'])[:1]
for name,m in cut.items():
    print(f'{name:22s} removes {conn.weight_syn[m].sum()/tot:5.1%} of eLN output synapses')
    for sn,st,r in (('bitter100',bit,100),('sugar150',sug,150)):
        net=lif.Network(conn,params,0.1,rng=np.random.default_rng(0)); net.w[m]=0
        rng=np.random.default_rng(1); on=np.zeros(conn.n); late=np.zeros(conn.n)
        for s in range(8000):
            k=(st[rng.random(len(st))<r*1e-4],prof['kick_mv']) if s<4000 else None
            spk=net.step(kick=k); on[spk]+=1
            if s>=6000: late[spk]+=1
        print(f'    {sn:9s} active {int((on>0).sum()):6d} persisting {int((late>0).sum()):6d}  MN9_L {on[mn9][0]/0.4:.1f} Hz', flush=True)
