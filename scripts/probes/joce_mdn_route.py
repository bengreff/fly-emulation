"""Strongest 1-3 hop routes from JO-C/E to MDN in the m1 graph (>=5 synapses)."""
import numpy as np, pandas as pd
n=pd.read_parquet('data/cache/male_cns_neurons.parquet'); e=pd.read_parquet('data/cache/male_cns_edges.parquet')
keep=n[(n.status=='Traced')|n.type.notna()]; t=keep.set_index('bodyId').type.fillna('?'); nt=keep.set_index('bodyId').predictedNt.fillna('unclear')
e=e[(e.weight>=5)&e.pre.isin(t.index)&e.post.isin(t.index)]
sens=set(keep.bodyId[keep.superclass.fillna('').str.contains('sensory')])
e=e[~e.post.isin(sens)]    # m1: no input onto sensory terminals
jo=set(keep.bodyId[keep.type.fillna('').str.match(r'^JO-(C|E)')]); mdn=set(keep.bodyId[keep.type=='MDN'])
into_mdn=e[e.post.isin(mdn)]
g=into_mdn.assign(pt=into_mdn.pre.map(t), nt=into_mdn.pre.map(nt)).groupby(['pt','nt']).weight.sum().sort_values(ascending=False)
print('top inputs to MDN (4 cells):'); print(g.head(12).to_string())
from_jo=e[e.pre.isin(jo)]
g1=from_jo.groupby(from_jo.post.map(t)).weight.sum().sort_values(ascending=False)
print('\ntop JO-C/E targets:'); print(g1.head(12).to_string())
# 2-hop: JO -> X -> MDN
a=from_jo.groupby('post').weight.sum(); b=into_mdn.groupby('pre').weight.sum()
two=(a.reindex(b.index).fillna(0)*b).sort_values(ascending=False)
print('\n2-hop JO-C/E -> X -> MDN, by product of synapse counts:')
print(pd.DataFrame({'type':two.index.map(t),'nt':two.index.map(nt),'jo_to_x':a.reindex(two.index).values,'x_to_mdn':b.reindex(two.index).values}).head(10).to_string())
x=keep.set_index('bodyId')
for ty in ['pIP1','GNG583']:
    ids=keep.bodyId[keep.type==ty]; print(ty, 'size', x.loc[ids,'size'].tolist(), 'post', x.loc[ids,'post'].tolist(), 'nt', x.loc[ids,'predictedNt'].tolist())
print('MDN size', x.loc[list(mdn),'size'].tolist(), 'post', x.loc[list(mdn),'post'].tolist())
print('median size traced', int(keep['size'].median()))
