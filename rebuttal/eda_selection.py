"""Predeclared E4 PCA128 / 90th-percentile squared Mahalanobis selection."""
import argparse,json,random
from pathlib import Path
import numpy as np

class MomentAccumulator:
    def __init__(self,width):self.n=0;self.mean=np.zeros(width);self.m2=np.zeros((width,width))
    def add(self,x):
        x=np.asarray(x,dtype=np.float64)
        if not len(x):return
        mean=x.mean(0);delta=mean-self.mean;n=self.n+len(x)
        self.m2+=(x-mean).T@(x-mean)+np.outer(delta,delta)*(self.n*len(x)/n)
        self.mean+=delta*len(x)/n;self.n=n
    def covariance(self):
        if self.n<2:raise ValueError('not enough reference observations')
        return self.m2/(self.n-1)

def fit_pca(m,dimension):
    vals,vec=np.linalg.eigh(m.covariance());order=np.argsort(vals)[::-1][:dimension]
    return {'mean':m.mean,'components':vec[:,order],'eigenvalues':np.maximum(vals[order],1e-12),'n':m.n}

def score_response(hidden,state,quantile):
    z=(np.asarray(hidden,dtype=np.float64)-state['mean'])@state['components']
    return float(np.quantile((z*z/state['eigenvalues']).sum(-1),quantile))

def select_indices(scores,count):
    if not 0<count<=len(scores) or not np.isfinite(scores).all():raise ValueError('invalid scores/count')
    return sorted(range(len(scores)),key=lambda i:(-scores[i],i))[:count]

def main():
    import torch
    from followspec.independent_kd import read,write,jsonl
    from rebuttal.teacher_cache import load_hidden
    from followspec.train_eagle3 import ensure_unpaused
    from atlas.workloads import file_hash
    p=argparse.ArgumentParser()
    for k in ['reference-cache','candidate-cache','output']:p.add_argument('--'+k,type=Path,required=True)
    p.add_argument('--dimension',type=int,default=128);p.add_argument('--quantile',type=float,default=.9);p.add_argument('--keep',type=int,default=8000)
    a=p.parse_args();ensure_unpaused();out=a.output;out.mkdir(parents=True,exist_ok=False)
    ref=json.loads((a.reference_cache/'manifest.json').read_text());cand=json.loads((a.candidate_cache/'manifest.json').read_text())
    if ref['target']!=cand['target']:raise ValueError('reference target differs')
    rindex=read(a.reference_cache/'index.jsonl');cindex=read(a.candidate_cache/'index.jsonl')
    if set(x['prompt_sha256'] for x in rindex)&set(x['prompt_sha256'] for x in cindex):raise ValueError('reference/candidate prompt overlap')
    width=ref['hidden_size'];total=0;mean=torch.zeros(width,device='cuda',dtype=torch.float64);m2=torch.zeros(width,width,device='cuda',dtype=torch.float64)
    with torch.no_grad():
        for entry in rindex:
            ensure_unpaused();x=load_hidden(a.reference_cache,entry)[entry['response_start']:].cuda().double();batchmean=x.mean(0);n=total+len(x);delta=batchmean-mean
            m2+=(x-batchmean).T@(x-batchmean)+torch.outer(delta,delta)*(total*len(x)/n);mean+=delta*(len(x)/n);total=n
        vals,vec=torch.linalg.eigh(m2/(total-1));order=torch.argsort(vals,descending=True)[:a.dimension]
        eigen=vals[order].clamp_min(1e-12);components=vec[:,order]
        np.savez(out/'pca.npz',mean=mean.cpu().numpy(),components=components.cpu().numpy(),eigenvalues=eigen.cpu().numpy(),n=total)
        scores=[]
        for entry in cindex:
            ensure_unpaused();x=load_hidden(a.candidate_cache,entry)[entry['response_start']:].cuda().double();z=(x-mean)@components
            scores.append(float(torch.quantile((z*z/eigen).sum(-1),a.quantile)))
    rows=read(cand['data']);selected=select_indices(scores,a.keep);random_indices=random.Random(0).sample(range(len(rows)),a.keep)
    for label,indices in [('selected',selected),('random',random_indices)]:
        dest=out/label;dest.mkdir();jsonl(dest/'per_prompt.jsonl',[rows[i] for i in indices]);write(dest/'indices.json',indices)
    jsonl(out/'scores.jsonl',[{'sample_id':e['sample_id'],'score':s} for e,s in zip(cindex,scores)])
    write(out/'results.json',{'status':'pending_five_sample_subset_audit','n':len(rows),'keep':a.keep,'reference_n':len(rindex),'reference_answer_tokens':total,'dimension':a.dimension,'quantile':a.quantile,'layer':'final normalized hidden state, answer token positions','eigenvalue_floor':1e-12,'reference_manifest_sha256':file_hash(a.reference_cache/'manifest.json'),'candidate_manifest_sha256':file_hash(a.candidate_cache/'manifest.json')})
if __name__=='__main__':main()
