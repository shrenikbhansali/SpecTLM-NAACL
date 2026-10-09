"""Raw, paired D50 table statistics. Frozen counters only; no engine execution."""
from pathlib import Path
import numpy as np


def invalid_path(path,invalid_roots):
    p=Path(path).resolve()
    return any(p==Path(r).resolve() or Path(r).resolve() in p.parents for r in invalid_roots)


def raw_values(r,k):
    a,d=r['per_step_accepted'],r['per_step_drafted']
    if len(a)!=len(d) or any(not 0<=x<=y<=k for x,y in zip(a,d)):raise ValueError('invalid raw speculative counters')
    if len(a)!=r['num_drafts'] or sum(a)!=r['num_accepted_tokens'] or sum(d)!=r['num_draft_tokens']:raise ValueError('counter totals mismatch')
    tau=1+sum(a)/len(a) if a else np.nan
    if a and abs(tau-r['acceptance_length'])>1e-8:raise ValueError('per-prompt tau mismatch')
    rates=[]
    for j in range(1,k+1):
        den=sum(x>=j-1 and y>=j for x,y in zip(a,d));rates.append(sum(x>=j for x in a)/den if den else np.nan)
    return [rates[0],tau,len(r['completion_token_ids']),*rates[1:]]


def paired_summary(arms,base,oracle=None,draws=10000):
    """Resample training seeds and shared prompt IDs, preserving paired controls."""
    a=np.asarray(arms,dtype=float);b=np.asarray(base,dtype=float)
    if a.ndim!=3 or b.shape!=a.shape[1:]:raise ValueError('seed/query/metric shape mismatch')
    n_original=a.shape[1];valid=np.isfinite(a[:,:,:2]).all(axis=(0,2))&np.isfinite(b[:,:2]).all(1)
    if oracle is not None:valid &= np.isfinite(np.asarray(oracle)[:,:2]).all(1)
    a=a[:,valid,:];b=b[valid,:];ns,n,nm=a.shape
    if not n:raise ValueError('no shared nonzero-step prompt IDs')
    rng=np.random.default_rng(0);si=rng.integers(ns,size=(draws,ns));qi=rng.integers(n,size=(draws,n))
    av=a.mean((0,1));bv=b.mean(0);boot=[];bb=[]
    # Bound memory even for full MATH500 and three seeds.
    for start in range(0,draws,250):
        ss=si[start:start+250];qq=qi[start:start+250];boot.append(a[ss[:,:,None],qq[:,None,:]].mean((1,2)));bb.append(b[qq].mean(1))
    boot=np.concatenate(boot);bb=np.concatenate(bb)
    def pack(mean,values):return dict(mean=float(mean),ci95=np.quantile(values,[.025,.975]).tolist())
    names=['p1','tau','length'][:nm];metrics={k:pack(av[i],boot[:,i]) for i,k in enumerate(names)};delta={k:pack(av[i]-bv[i],boot[:,i]-bb[:,i]) for i,k in enumerate(names)};rec=None
    if oracle is not None:
        o=np.asarray(oracle)[valid];den=o[:,1].mean()-b[:,1].mean();num=av[1]-bv[1];d=o[qi,1].mean(1)-bb[:,1]
        if den!=0:
            dr=np.divide(boot[:,1]-bb[:,1],d,out=np.full(draws,np.nan),where=d!=0);finite=dr[np.isfinite(dr)];rec=dict(mean=float(num/den),ci95=np.quantile(finite,[.025,.975]).tolist() if len(finite) else None,undefined_draws=int((~np.isfinite(dr)).sum()))
    return dict(n_total=n_original,n_paired=n,seeds=ns,metrics=metrics,delta=delta,recovery=rec,bootstrap_draws=draws)


def check_pair(a,b,render_a,render_b):
    for key in ['engine_version','target','target_revision','batch_size','max_new_tokens','seed','temperature','dtype','max_model_len','enable_prefix_caching']:
        if a.get(key)!=b.get(key):raise ValueError(f'paired settings mismatch: {key}')
    if render_a!=render_b:raise ValueError('paired rendered token IDs mismatch')
