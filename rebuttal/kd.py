"""E5 full-vocabulary forward KL and deterministic training-only split."""
import hashlib
import random
import torch
from torch.nn import functional as F
from torch.utils.checkpoint import checkpoint


def factor_logits(hidden, head):
    return F.linear(hidden, head)


def response_hidden(hidden,row):
    start=row['response_start'];ids=row['input_ids']
    if not 0<start<len(ids) or len(hidden)!=len(ids):raise ValueError('invalid aligned sequence')
    if row['loss_mask']!=[False]*start+[True]*(len(ids)-start):raise ValueError('invalid response mask')
    return hidden[start-1:-1]


def full_kl(hidden,head,teacher_hidden,teacher_head,chunk=128):
    """Exact normalized forward KL; recompute logits to bound activation memory."""
    if len(hidden)!=len(teacher_hidden) or head.shape[0]!=teacher_head.shape[0]:raise ValueError('unaligned teacher/student')
    if len(hidden)==0 or chunk<1:raise ValueError('empty response')
    def loss(h,w,th,tw):
        double=h.dtype==torch.float64
        q=factor_logits(h,w);p=factor_logits(th,tw)
        logq=(q if double else q.float()).log_softmax(-1)
        logp=(p if double else p.float()).log_softmax(-1).detach()
        return (logp.exp()*(logp-logq)).sum()
    total=hidden.new_zeros((),dtype=torch.float64 if hidden.dtype==torch.float64 else torch.float32)
    for offset in range(0,len(hidden),chunk):
        values=(hidden[offset:offset+chunk],head,teacher_hidden[offset:offset+chunk],teacher_head)
        total=total+(checkpoint(loss,*values,use_reentrant=False) if torch.is_grad_enabled() else loss(*values))
    return total/len(hidden)


def split_rows(rows,heldout=256,seed=0):
    keys=[r['prompt_sha256'] for r in rows]
    if len(set(keys))!=len(keys) or not 0<heldout<len(rows):raise ValueError('invalid split')
    order=sorted(range(len(rows)),key=lambda i:hashlib.sha256((str(seed)+':'+keys[i]).encode()).hexdigest())
    validation=set(order[:heldout])
    return [i for i in range(len(rows)) if i not in validation],order[:heldout]


def pack_by_responses(rows,indices,ceiling,epochs,seed):
    lengths={i:len(rows[i]['input_ids'])-rows[i]['response_start'] for i in indices}
    if not lengths or min(lengths.values())<1 or max(lengths.values())>ceiling:raise ValueError('invalid response length')
    rng=random.Random(seed);batches=[]
    for _ in range(epochs):
        order=list(indices);rng.shuffle(order);batch=[];tokens=0
        for i in order:
            if batch and tokens+lengths[i]>ceiling:batches.append(batch);batch=[];tokens=0
            batch.append(i);tokens+=lengths[i]
        if batch:batches.append(batch)
    return batches
