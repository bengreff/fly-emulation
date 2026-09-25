"""Does one odour channel ignite the model, and does it need the eLNs? m1."""
import sys; sys.path.insert(0,'scripts'); sys.path.insert(0,'src')
import numpy as np
from flyemu import connectome, lif, profiles
from flyemu.registry import Registry, Policy
for eff in (0.0825, 0.1925):
    reg=Registry(Policy.MINIMAL); reg.overrides['connection_class:all|efficacy_per_synapse']=eff
    prof=profiles.apply(reg,'m1'); conn=connectome.build(reg,min_synapses=5); params=lif.default_params(reg,conn,timestep_ms=0.1)
    nrn=conn.neurons; t=nrn.type.fillna('')
    orn_types=t[nrn['class'].eq('olfactory')].value_counts()
    eln=np.flatnonzero(t.eq('lLN1_bc').to_numpy())
    for ty in [x for x in orn_types.index if 'DA1' in x or 'DM4' in x or 'VA1v' in x][:3]:
        st=np.flatnonzero(t.eq(ty).to_numpy())
        for sil in (False, True):
            net=lif.Network(conn,params,0.1,rng=np.random.default_rng(0))
            if sil: net.silence(eln)
            rng=np.random.default_rng(1); on=np.zeros(conn.n); late=np.zeros(conn.n)
            for s in range(8000):
                k=(st[rng.random(len(st))<100e-4],prof['kick_mv']) if s<4000 else None
                spk=net.step(kick=k); on[spk]+=1
                if s>=6000: late[spk]+=1
            print(f'eff {eff:.4f} {ty:10s} ({len(st)} ORNs) eLN silenced={sil!s:5s} active {int((on>0).sum()):6d} persisting {int((late>0).sum()):6d}', flush=True)
