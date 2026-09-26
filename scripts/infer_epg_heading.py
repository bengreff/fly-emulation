"""EPG ring position inferred from connectivity (session 8).

Glomerulus labels alone do not give heading: in the wiring, L1..L8 run one way
round the ring and R1..R8 the other (R_k sits near L_(9-k)). This places every
EPG on a circle by spectral embedding of its input+output connectivity profile
(cosine similarity of sqrt synapse counts, >=1 synapse, normalised graph
Laplacian, eigenvectors 2 and 3). The angle's origin and direction are
arbitrary; only relative positions matter for bump tests. Label: inferred.

    uv run python scripts/infer_epg_heading.py   -> data/derived/epg_heading_embedding.csv
"""
import re, numpy as np, pandas as pd
n=pd.read_parquet('data/cache/male_cns_neurons.parquet',columns=['bodyId','type','instance'])
epg=n[n.type.isin(['EPG','EPGt'])].reset_index(drop=True)
ids=epg.bodyId.tolist()
ein=pd.read_parquet('data/cache/male_cns_edges.parquet',filters=[('post','in',ids)])
eout=pd.read_parquet('data/cache/male_cns_edges.parquet',filters=[('pre','in',ids)])
A=pd.concat([ein.pivot_table(index='post',columns='pre',values='weight',aggfunc='sum',fill_value=0).add_prefix('i'),
             eout.pivot_table(index='pre',columns='post',values='weight',aggfunc='sum',fill_value=0).add_prefix('o')],axis=1).fillna(0).reindex(ids).fillna(0)
X=np.sqrt(A.to_numpy()); X=X/np.linalg.norm(X,axis=1,keepdims=True)
S=X@X.T; np.fill_diagonal(S,0)
d=S.sum(1); L=np.diag(1/np.sqrt(d))@S@np.diag(1/np.sqrt(d))
w,v=np.linalg.eigh(L); u=v[:,-2]; z=v[:,-3]
ang=(np.rad2deg(np.arctan2(z,u))%360)
epg['emb']=ang
epg['side']=epg.instance.str.extract(r'_([LR])\d$')[0]; epg['k']=epg.instance.str.extract(r'_[LR](\d)$')[0].astype(float)
print('eigenvalues top5', np.round(w[-5:],3))
print(epg.groupby(['side','k']).emb.agg(lambda s: f'{np.rad2deg(np.angle(np.exp(1j*np.deg2rad(s)).mean()))%360:6.1f} (n={len(s)}, spread {np.rad2deg(np.sqrt(-2*np.log(abs(np.exp(1j*np.deg2rad(s)).mean()))) ):.0f})').to_string())
epg[['bodyId','type','instance','emb']].rename(columns={'emb':'heading_deg'}).to_csv('data/derived/epg_heading_embedding.csv',index=False)
