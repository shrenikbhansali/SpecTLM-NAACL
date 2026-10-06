"""Diagnostic offline feature/label/head cells; never substitute for vLLM AL."""
import argparse
import csv
import hashlib
import json
from pathlib import Path
import warnings
import numpy as np
from scipy.special import logsumexp
from scipy.stats import spearmanr


def score_distribution(logp,logq,mask):
    p,q=np.asarray(logp,dtype=float),np.asarray(logq,dtype=float);mask=np.asarray(mask,dtype=bool)
    if p.ndim!=2 or p.shape!=q.shape or mask.shape!=p.shape[:1] or not mask.any():raise ValueError('distribution/mask shape mismatch')
    p,q=p[mask],q[mask]
    if np.isnan(p).any() or np.isnan(q).any() or np.isposinf(p).any() or np.isposinf(q).any():raise ValueError('invalid log probability')
    if not np.allclose(logsumexp(p,axis=-1),0,atol=1e-6,rtol=0) or not np.allclose(logsumexp(q,axis=-1),0,atol=1e-6,rtol=0):raise ValueError('input must be normalized log probabilities')
    overlap=np.exp(np.minimum(p,q)).sum(-1);supported=np.isfinite(p)
    infinite=(supported & np.isneginf(q)).any(-1);kl=np.zeros(p.shape[0])
    for i in range(len(p)):
        if infinite[i]:kl[i]=np.inf
        else:kl[i]=np.sum(np.exp(p[i,supported[i]])*(p[i,supported[i]]-q[i,supported[i]]))
    if np.min(kl)<-1e-8:raise ValueError('negative forward KL')
    return dict(n=len(p),top1_agreement=float(np.mean(p.argmax(-1)==q.argmax(-1))),overlap=float(overlap.mean()),
        forward_kl=None if infinite.any() else float(np.maximum(kl,0).mean()),forward_kl_infinite=bool(infinite.any()),
        infinite_kl_positions=int(infinite.sum()),kl_direction='labels p || draft q',diagnostic=True,
        support_policy='exact support; no epsilon floor or hidden renormalization')


def score_grid(labels,drafts,mask):
    if set(labels)!={'base','child'} or set(drafts)!={'base','child'}:raise ValueError('base/child features and labels required')
    shape=np.asarray(labels['base']).shape;mask=np.asarray(mask,dtype=bool)
    if len(shape)!=3 or mask.shape!=shape[:2] or any(np.asarray(v).shape!=shape for v in labels.values()):raise ValueError('need depth×positions×vocabulary tensors')
    if set(drafts['base'])!=set(drafts['child']):raise ValueError('head swaps must be crossed with both feature sources')
    result=[]
    for features in ('base','child'):
        for head,q in sorted(drafts[features].items()):
            if np.asarray(q).shape!=shape:raise ValueError('draft tensor shape mismatch')
            for label,p in labels.items():
                for depth in range(shape[0]):
                    result.append(dict(feature_source=features,label_source=label,head=head,unroll_position=depth,
                        **score_distribution(p[depth],q[depth],mask[depth])))
    return result


def rank_correlation(x,y):
    if len(set(x))<2 or len(set(y))<2:return None
    with warnings.catch_warnings():
        warnings.simplefilter('ignore');r=float(spearmanr(x,y).statistic)
    return r if np.isfinite(r) else None


def decompose(base_base,base_child,child_child):
    """Owner-approved signed decomposition; no denominator floor or clipping."""
    cells=(base_base,base_child,child_child)
    if any(v is not None and not np.isfinite(v) for v in cells):
        raise ValueError('nonfinite cells must use explicit null representation')
    if any(v is None for v in cells):
        return dict(label_shift=None,transport=None,total_shift=None,R=None,
                    R_defined=False,undefined_reason='nonfinite cell',diagnostic=True)
    label_shift=float(base_child-base_base)
    transport=float(child_child-base_child)
    denominator=-label_shift
    return dict(label_shift=label_shift,transport=transport,
                total_shift=float(child_child-base_base),
                R=transport/denominator if denominator!=0 else None,
                R_defined=denominator!=0,
                undefined_reason=None if denominator!=0 else 'zero denominator',diagnostic=True)


def decompose_grid(rows):
    indexed={}
    for row in rows:
        key=(row['head'],row['unroll_position'],row['feature_source'],row['label_source'])
        if key in indexed:raise ValueError('duplicate diagnostic cell')
        indexed[key]=row
    result=[]
    for head,depth in sorted({k[:2] for k in indexed}):
        cells=[indexed[(head,depth,f,p)] for f,p in [('base','base'),('base','child'),('child','child')]]
        if len({c['n'] for c in cells})!=1:raise ValueError('unmatched decomposition positions')
        for metric in ('top1_agreement','overlap','forward_kl'):
            result.append(dict(head=head,unroll_position=depth,metric=metric,n=cells[0]['n'],
                **decompose(*(c[metric] for c in cells))))
    return result


def validate_diagonals(records):
    if len(records)<10:raise ValueError('at least10 real derivatives required')
    if len({r['derivative_id'] for r in records})!=len(records):raise ValueError('duplicate derivative')
    x=np.array([[r['offline_A00'],r['offline_A10']] for r in records],dtype=float)
    y=np.array([[r['A00'],r['A10']] for r in records],dtype=float)
    if not np.isfinite(x).all() or not np.isfinite(y).all():raise ValueError('nonfinite diagonal validation')
    rho=rank_correlation(x.ravel().tolist(),y.ravel().tolist())
    sign=float(np.mean(np.sign(x[:,1]-x[:,0])==np.sign(y[:,1]-y[:,0])))
    return dict(n_derivatives=len(records),spearman_pooled_diagonal_pairs=rho,
        spearman_A00=rank_correlation(x[:,0].tolist(),y[:,0].tolist()),spearman_A10=rank_correlation(x[:,1].tolist(),y[:,1].tolist()),
        sign_agreement=sign,spearman_threshold=.8,sign_threshold=.9,passed=rho is not None and rho>=.8 and sign>=.9,
        diagnostic=True,independent_unit='derivative; both paired diagonal cells included in correlation',
        caveat='offline diagnostics; operator verifies real-source matching before interpreting this check')


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--manifest',required=True);p.add_argument('--output',required=True);a=p.parse_args()
    manifest=json.loads(Path(a.manifest).read_text())
    if manifest.get('scope')!='offline diagnostic':raise ValueError('manifest must label diagnostic scope')
    if not manifest.get('source_run_ids') or not manifest.get('prompt_sha256'):raise ValueError('source run IDs and matched prompt hash required')
    bundle=Path(manifest['tensor_file'])
    if hashlib.sha256(bundle.read_bytes()).hexdigest()!=manifest['tensor_sha256']:raise ValueError('tensor hash mismatch')
    with np.load(bundle,allow_pickle=False) as f:
        labels={name:f['labels_'+name] for name in ('base','child')}
        drafts={name:{head:f[f'draft_{name}_{head}'] for head in manifest['heads']} for name in ('base','child')}
        rows=score_grid(labels,drafts,f['mask'])
    out=Path(a.output);out.mkdir(parents=True,exist_ok=False)
    for row in rows:row.update(derivative_id=manifest['derivative_id'],source_run_ids=manifest['source_run_ids'],scope='offline diagnostic')
    (out/'cells.json').write_text(json.dumps(rows,indent=2,allow_nan=False)+'\n')
    decomposition=decompose_grid(rows)
    for row in decomposition:row.update(derivative_id=manifest['derivative_id'],source_run_ids=manifest['source_run_ids'],scope='offline diagnostic')
    (out/'decomposition.json').write_text(json.dumps(decomposition,indent=2,allow_nan=False)+'\n')
    (out/'config.json').write_text(json.dumps(manifest|dict(source_code_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        transport_ratio='(a(child,child)-a(base,child))/(-(a(base,child)-a(base,base))); zero denominator undefined; owner approved 2026-10-05',
        primary_validation_metric='not selected by scorer'),indent=2)+'\n')
    with (out/'cells.csv').open('x',newline='') as f:
        w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows({**r,'source_run_ids':json.dumps(r['source_run_ids'])} for r in rows)

if __name__=='__main__':main()
