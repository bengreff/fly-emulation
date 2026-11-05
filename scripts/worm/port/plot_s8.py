# BRAIN_PORT section 8 figure (data/worm/brain_runs/s8_screen/s8.png) from the saved runs in /tmp/mine_c1.
import json, numpy as np, matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
O="/tmp/mine_c1/"; runs=[("c2_off","control (receptor_sign on)"),("s8_E1","E1 expression_map"),("s8_E2","E2 expression_map + muscle_active + gap_rect"),
 ("s8_S01","S01 chem strength 0.1 nS"),("s8_S11","S11 exc reversal -10 mV"),("s8_S14","S14 exc release slope 2 mV"),("s8_S16","S16 inh release threshold -45 mV")]
fig,ax=plt.subplots(len(runs),3,figsize=(15,2.3*len(runs)),gridspec_kw=dict(width_ratios=[3,2,1]))
for i,(k,lab) in enumerate(runs):
    m=json.load(open(O+k+".json")); nf=m["n_frames"]; A=np.fromfile(O+k+".act.f32",np.float32).reshape(nf,-1)
    X=np.fromfile(O+k+".frames.f32",np.float32).reshape(nf,-1,3); V=np.fromfile(O+k+".neural.f32",np.float32).reshape(-1,len(m["cells"]))
    g=np.repeat(m["muscles"],24); row=np.tile(np.arange(1,25),4); t=np.linspace(0,m["seconds"],nf)
    D=np.stack([A[:,(np.isin(g,["MDR","MDL"]))&(row==r)].mean(1)-A[:,(np.isin(g,["MVR","MVL"]))&(row==r)].mean(1) for r in range(1,25)])
    im=ax[i,0].imshow(D,aspect="auto",cmap="RdBu_r",vmin=-0.5,vmax=0.5,extent=[0,m["seconds"],24.5,0.5]); ax[i,0].set_ylabel("row (head=1)")
    ax[i,0].set_title(lab+": dorsal minus ventral activation",fontsize=9)
    w=t>=1; mid=(row>=9)&(row<=16); dv=A[:,mid&np.isin(g,["MDR","MDL"])].mean(1)-A[:,mid&np.isin(g,["MVR","MVL"])].mean(1)
    ax[i,1].plot(t,A[:,np.isin(g,["MDR","MDL"])].mean(1),label="dorsal mean"); ax[i,1].plot(t,A[:,np.isin(g,["MVR","MVL"])].mean(1),label="ventral mean")
    ax[i,1].plot(t,dv,"k",lw=1,label="mid-body D-V (rows 9-16)"); ax[i,1].axvline(1,color="0.6",ls=":"); ax[i,1].set_ylim(-0.6,0.8)
    n20=(V[:,:302]>-20).sum(1); ax2=ax[i,1].twinx(); ax2.plot(np.linspace(0,m["seconds"],len(n20)),n20,color="0.5",lw=0.8); ax2.set_ylim(0,310); ax2.set_ylabel("neurons > -20 mV",fontsize=7,color="0.4")
    if i==0: ax[i,1].legend(fontsize=6,loc="upper left")
    P=X.reshape(-1,3); P=P-P.mean(0); ev=np.linalg.svd(P[::50],full_matrices=False)[2][:2]
    for f,c in ((0,"0.7"),(nf//2,"C2"),(nf-1,"k")): Y=(X[f]-X.reshape(-1,3).mean(0))@ev.T; ax[i,2].plot(Y[:,0],Y[:,1],".",ms=0.5,color=c)
    ax[i,2].set_aspect("equal"); ax[i,2].set_xticks([]); ax[i,2].set_yticks([]); ax[i,2].set_title("body t=0 grey, 2.5 green, 5 black (best-fit plane)",fontsize=7)
ax[-1,0].set_xlabel("time (s)"); ax[-1,1].set_xlabel("time (s)")
fig.colorbar(im,ax=ax[:,0],fraction=0.02); fig.suptitle("BRAIN_PORT section 8: 5 s closed loop. Rhythm rule (mid-body D-V, after 1 s): >=3 zero crossings and peak-to-peak >=0.1. No run passes.\nS14 only: rows 18-24 rise together at 3.4 s, the defecation clock (pBoc, +0.5 dorsal and ventral alike), not the brain.",fontsize=10)
fig.subplots_adjust(top=0.93,hspace=0.45); fig.savefig("/Users/ben/fly-emulation/data/worm/brain_runs/s8_screen/s8.png",dpi=90)
