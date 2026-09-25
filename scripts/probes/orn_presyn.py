"""Does keeping central input onto ORN terminals (presynaptic inhibition,
Olsen & Wilson 2008) stop odour-evoked ignition? shiu2024 (terminals kept) vs m1."""
import sys; sys.path.insert(0,'scripts'); sys.path.insert(0,'src')
from concurrent.futures import ProcessPoolExecutor
import numpy as np, pandas as pd
from assay_pathways import select
from flyemu import connectome, lif, profiles
from flyemu.registry import Registry, Policy
def run(args):
    prof_name, eff, stn = args
    reg=Registry(Policy.MINIMAL); reg.overrides['connection_class:all|efficacy_per_synapse']=eff
    prof=profiles.apply(reg,prof_name); conn=connectome.build(reg,min_synapses=5); params=lif.default_params(reg,conn,timestep_ms=0.1)
    nrn=conn.neurons; t=nrn.type.fillna('')
    st=np.flatnonzero(t.eq(stn).to_numpy()) if stn.startswith('ORN') else select(nrn,['LB3b','LB3c'])
    mn9=select(nrn,['MN9'])[:1]
    net=lif.Network(conn,params,0.1,rng=np.random.default_rng(0)); rng=np.random.default_rng(1)
    on=np.zeros(conn.n); late=np.zeros(conn.n)
    for s in range(8000):
        k=(st[rng.random(len(st))<150e-4],prof['kick_mv']) if s<4000 else None
        spk=net.step(kick=k); on[spk]+=1
        if s>=6000: late[spk]+=1
    return prof_name, eff, stn, int((on>0).sum()), int((late>0).sum()), float(on[st].mean()/0.4), float(on[mn9][0]/0.4)
if __name__=='__main__':
    jobs=[(p,e,s) for p in ('shiu2024','m1') for e in (0.0825,0.165) for s in ('ORN_DM4','ORN_DA1','sugar')]
    with ProcessPoolExecutor(6) as ex: res=list(ex.map(run,jobs))
    df=pd.DataFrame(res,columns=['profile','eff_mv','stim','active','persisting','stim_cells_hz','mn9_L_hz'])
    df.to_csv('runs/probes/orn_presyn.csv',index=False); print(df.round(1).to_string(index=False))
