"""Signed 1- and 2-hop synaptic drive from a stimulus type set to each readout cell.
    uv run python scripts/probes/route_strength.py LB3a,LB3b,LB3c MN9"""
import sys, numpy as np, pandas as pd
stim, read = sys.argv[1].split(','), sys.argv[2].split(',')
n=pd.read_parquet('data/cache/male_cns_neurons.parquet'); e=pd.read_parquet('data/cache/male_cns_edges.parquet')
keep=n[(n.status=='Traced')|n.type.notna()].set_index('bodyId')
sens=set(keep.index[keep.superclass.fillna('').str.contains('sensory')])
e=e[(e.weight>=5)&e.pre.isin(keep.index)&e.post.isin(keep.index)&~e.post.isin(sens)]
sign=keep.predictedNt.fillna('unclear').str.lower().map({'gaba':-1,'glutamate':-1,'histamine':-1}).fillna(1)
for s in stim:
    src=keep.index[keep.type==s]; a=e[e.pre.isin(src)].groupby('post').weight.sum()
    for r in read:
        for m in keep.index[keep.type==r]:
            y=e[e.post==m].set_index('pre').weight
            c=a.index.intersection(y.index)
            d2=(a[c]*y[c]*sign[c]).sum()
            print(f'{s:6s} ({len(src):2d} cells, {int(a.sum()):5d} out-syn) -> {keep.instance[m]:8s}: direct {int(a.get(m,0)):4d}  2-hop signed {int(d2):6d} via {len(c)}')
