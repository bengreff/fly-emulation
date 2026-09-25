"""Rule-v2 stability with cholinergic ALLN chemical output onto PNs and onto
other cholinergic ALLNs removed (eLN->PN is electrical, Yaksi & Wilson 2010;
eLN->eLN unmeasured). eLN->inhibitory LN output kept. m1, current-based."""
import sys; sys.path.insert(0,'scripts'); sys.path.insert(0,'src')
from concurrent.futures import ProcessPoolExecutor
import numpy as np, pandas as pd
from assay_pathways import select
from flyemu import connectome, lif, profiles
from flyemu.registry import Registry, Policy

reg=Registry(Policy.MINIMAL); prof=profiles.apply(reg,'m1')
conn=connectome.build(reg,min_synapses=5); params=lif.default_params(reg,conn,timestep_ms=0.1)
nrn=conn.neurons; t=nrn.type.fillna('')
ach_ln=(nrn['class'].eq('ALLN') & nrn.predictedNt.eq('acetylcholine')).to_numpy()
pn=nrn['class'].eq('ALPN').to_numpy()
pre=np.repeat(np.arange(conn.n),np.diff(conn.indptr)); post=conn.indices
cut=ach_ln[pre]&(pn[post]|ach_ln[post])
pool=np.flatnonzero((nrn.superclass.fillna('').str.contains('sensory') & ~t.str.match(r'^(JO-|LB|LPLC2|Lg|PhG|WG|claw_|dorsal_tp)') & (t!='')).to_numpy())
g=np.random.default_rng(12345)
stims=[('sugar',select(nrn,['LB3b','LB3c']))]+[(f'generic{k}',g.choice(pool,40,replace=False)) for k in range(4)]+[('ORN_DM4',np.flatnonzero(t.eq('ORN_DM4').to_numpy()))]
mn9=select(nrn,['MN9'])[:1]

def run(args):
    scale, cutting, (sn, st) = args
    net=lif.Network(conn,params,0.1,rng=np.random.default_rng(0))
    net.w*=scale/0.275*0.275  # profile psp is 0.275; scale relative to Shiu
    if cutting: net.w[cut]=0
    rng=np.random.default_rng(1); on=np.zeros(conn.n); late=np.zeros(conn.n)
    for s in range(8000):
        k=(st[rng.random(len(st))<150e-4],prof['kick_mv']) if s<4000 else None
        spk=net.step(kick=k); on[spk]+=1
        if s>=6000: late[spk]+=1
    return scale, cutting, sn, int((on>0).sum()), int((late>0).sum()), on[mn9][0]/0.4

if __name__=='__main__':
    print('cut synapses', int(conn.weight_syn[cut].sum()), 'of', int(conn.weight_syn[ach_ln[pre]].sum()), 'cholinergic-ALLN output synapses')
    jobs=[(sc,c,s) for sc in (0.3,0.5,0.7,1.0) for c in (False,True) for s in stims]
    with ProcessPoolExecutor(8) as ex:
        res=list(ex.map(run,jobs))
    df=pd.DataFrame(res,columns=['scale','cut','stim','active','persisting','mn9_L_hz'])
    df.to_csv('runs/probes/aln_ach_targets_v2.csv',index=False)
    print(df.pivot_table(index=['scale','cut'],columns='stim',values='persisting').to_string())
    print(df[df.stim=='sugar'].to_string(index=False))
