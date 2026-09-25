"""Which cell types are necessary for the self-sustaining state? (m1, 0.1925 mV)

Ignite with bitter GRNs at 100 Hz for 400 ms; count cells still firing at
600-800 ms. Then silence each of the top types in that persisting set, one at
a time, and re-measure. Output: runs/probes/ignition_core_screen.csv
"""
import sys; sys.path.insert(0,'scripts'); sys.path.insert(0,'src')
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path
import numpy as np, pandas as pd
from assay_pathways import select
from flyemu import connectome, lif, profiles
from flyemu.registry import Registry, Policy

def build():
    reg=Registry(Policy.MINIMAL); reg.overrides['connection_class:all|efficacy_per_synapse']=0.1925
    prof=profiles.apply(reg,'m1'); conn=connectome.build(reg,min_synapses=5)
    return prof, conn, lif.default_params(reg,conn,timestep_ms=0.1)

def trial(silence_type):
    prof, conn, params = G
    nrn=conn.neurons; st=select(nrn,['LB1a','LB1b','LB1c','LB1d'])
    net=lif.Network(conn,params,0.1,rng=np.random.default_rng(0))
    if silence_type: net.silence(np.flatnonzero(nrn.type.eq(silence_type).to_numpy()))
    rng=np.random.default_rng(1); late=np.zeros(conn.n)
    for s in range(8000):
        k=(st[rng.random(len(st))<100e-4],prof['kick_mv']) if s<4000 else None
        spk=net.step(kick=k)
        if s>=6000: late[spk]+=1
    return silence_type, late

G = build()
if __name__ == '__main__':
    _, base = trial(None)
    nrn=G[1].neurons
    per=nrn[base>0].type.fillna('?').value_counts()
    cands=[t for t in per.index if t!='?'][:28]
    with ProcessPoolExecutor(7) as ex:
        res=list(ex.map(trial, cands))
    rows=[dict(silenced='none', n_cells=0, persisting=int((base>0).sum()))]
    for t,late in res:
        rows.append(dict(silenced=t, n_cells=int(nrn.type.eq(t).sum()), persisting=int((late>0).sum())))
    df=pd.DataFrame(rows).sort_values('persisting'); Path('runs/probes').mkdir(parents=True,exist_ok=True)
    df.to_csv('runs/probes/ignition_core_screen.csv',index=False); print(df.to_string(index=False))
