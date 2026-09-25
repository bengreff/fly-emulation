"""Is the left/right MN9 asymmetry in the wiring? Per-side counts and 2-hop drive."""
import numpy as np, pandas as pd
n=pd.read_parquet('data/cache/male_cns_neurons.parquet'); e=pd.read_parquet('data/cache/male_cns_edges.parquet')
keep=n[(n.status=='Traced')|n.type.notna()].set_index('bodyId')
e=e[(e.weight>=5)&e.pre.isin(keep.index)&e.post.isin(keep.index)]
sug=keep[keep.type.isin(['LB3b','LB3c'])]
print('sugar GRNs by type x side:'); print(pd.crosstab(sug.type, sug.somaSide.fillna('?')))
print('status', sug.status.value_counts().to_dict(), ' median pre', sug.pre.median())
mn9=keep[keep.type=='MN9']; print('MN9', list(zip(mn9.index, mn9.instance, mn9.post)))
sign=keep.predictedNt.fillna('unclear').str.lower().map({'gaba':-1,'glutamate':-1,'histamine':-1}).fillna(1)
a=e[e.pre.isin(sug.index)]
for m in mn9.index:
    b=e[e.post==m]
    x=a.groupby('post').weight.sum()
    y=b.set_index('pre').weight
    common=x.index.intersection(y.index)
    drive=(x[common]*y[common]*sign[common]).sum()
    print(f'MN9 {keep.instance[m]}: direct from sugar {int(a[a.post==m].weight.sum())}; signed 2-hop drive {int(drive)} via {len(common)} interneurons; total input {int(b.weight.sum())}')
    top=(x[common]*y[common]*sign[common]).sort_values(ascending=False).head(5)
    print('   top:', [(keep.type[i], keep.somaSide[i], int(v)) for i,v in top.items()])
