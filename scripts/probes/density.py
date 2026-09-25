import pandas as pd, numpy as np
fw=pd.read_parquet('external/Drosophila_brain_model/Connectivity_783.parquet')
print(fw.columns.tolist(), len(fw), 'dup pairs', fw.duplicated(['Presynaptic_ID','Postsynaptic_ID']).sum(), 'min', fw.Connectivity.min())
fin=fw.groupby('Postsynaptic_ID').Connectivity.sum()
ann=pd.read_csv('external/flywire_annotations_783.tsv',sep='\t',usecols=['root_id','cell_type','hemibrain_type','super_class'],low_memory=False)
ann['t']=ann.cell_type.fillna(ann.hemibrain_type)
ann['fin']=ann.root_id.map(fin).fillna(0)
n=pd.read_parquet('data/cache/male_cns_neurons.parquet').merge(pd.read_parquet('data/cache/male_cns_extra.parquet'),on='bodyId')
e=pd.read_parquet('data/cache/male_cns_edges.parquet')
keep=set(n.bodyId[(n.status=='Traced')|n.type.notna()])
for thr in (1,5):
    ee=e[(e.weight>=thr)&e.pre.isin(keep)&e.post.isin(keep)]
    n[f'min{thr}']=n.bodyId.map(ee.groupby('post').weight.sum()).fillna(0)
m=n[n.bodyId.isin(keep)].copy()
m['t']=m.flywireType.fillna(m.type)
fwt=ann[ann.fin>0].groupby('t').fin.mean()
res={}
for thr in (1,5):
    mt=m[m[f'min{thr}']>0].groupby('t')[f'min{thr}'].mean()
    j=pd.concat([fwt,mt],axis=1,join='inner').dropna(); j.columns=['fw','mc']
    r=np.log2(j.mc/j.fw)
    print(f'male-cns >= {thr} vs FlyWire(Shiu graph): {len(j)} matched types, median ratio {2**r.median():.3f}, IQR {2**r.quantile(.25):.2f}-{2**r.quantile(.75):.2f}')
    res[thr]=j
# specific: MN9 and sugar path
for t in ['MN9','LB3b','LB3c']:
    print(t, m.loc[m.t==t,['type','flywireType','min1','min5']].to_string())
print('FlyWire MN9 in:', ann.loc[ann.t=='MN9',['root_id','fin']].to_string())
# central-brain only (exclude optic lobe, sensory)
