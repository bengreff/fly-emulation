"""Sensitivity: AL local neurons with 'unclear' predicted NT treated as
inhibitory (literature: most AL LNs are GABAergic or glutamatergic) instead
of Shiu's unknown -> excitatory. With and without the eLN output cut. m1."""
import sys, dataclasses; sys.path.insert(0,'scripts'); sys.path.insert(0,'src')
from concurrent.futures import ProcessPoolExecutor
import numpy as np, pandas as pd
from assay_pathways import select
from flyemu import connectome, lif, profiles
from flyemu.registry import Registry, Policy
reg=Registry(Policy.MINIMAL); prof=profiles.apply(reg,'m1'); conn=connectome.build(reg,min_synapses=5); params=lif.default_params(reg,conn,timestep_ms=0.1)
nrn=conn.neurons; t=nrn.type.fillna('')
alln=nrn['class'].eq('ALLN').to_numpy(); unclear=nrn.predictedNt.fillna('unclear').eq('unclear').to_numpy()
ach_ln=alln & nrn.predictedNt.eq('acetylcholine').to_numpy(); pn=nrn['class'].eq('ALPN').to_numpy()
pre=np.repeat(np.arange(conn.n),np.diff(conn.indptr)); post=conn.indices
cut=ach_ln[pre]&(pn[post]|ach_ln[post])
s2=conn.sign.copy(); s2[alln&unclear]=-1.0; flipped=dataclasses.replace(conn,sign=s2)
stims={'ORN_DM4':np.flatnonzero(t.eq('ORN_DM4').to_numpy()),'sugar':select(nrn,['LB3b','LB3c'])}
mn9=select(nrn,['MN9'])[:1]
def run(a):
    scale, flip, docut, sn = a
    g=flipped if flip else conn
    net=lif.Network(g,params,0.1,rng=np.random.default_rng(0)); net.w*=scale
    if docut: net.w[cut]=0
    st=stims[sn]; rng=np.random.default_rng(1); on=np.zeros(conn.n); late=np.zeros(conn.n)
    for s in range(8000):
        k=(st[rng.random(len(st))<150e-4],prof['kick_mv']) if s<4000 else None
        spk=net.step(kick=k); on[spk]+=1
        if s>=6000: late[spk]+=1
    return scale, flip, docut, sn, int((on>0).sum()), int((late>0).sum()), on[mn9][0]/0.4
if __name__=='__main__':
    print('AL LNs with unclear NT:', int((alln&unclear).sum()), 'of', int(alln.sum()))
    jobs=[(sc,f,c,s) for sc in (0.7,1.0,1.2) for f in (False,True) for c in (False,True) for s in stims]
    with ProcessPoolExecutor(8) as ex: res=list(ex.map(run,jobs))
    df=pd.DataFrame(res,columns=['scale','unclear_inhib','eln_cut','stim','active','persisting','mn9_L'])
    df.to_csv('runs/probes/al_unclear_sign.csv',index=False)
    print(df.pivot_table(index=['scale','unclear_inhib','eln_cut'],columns='stim',values=['persisting','mn9_L']).round(1).to_string())
