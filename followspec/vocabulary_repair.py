"""D54 E15 opt-in response-frequency draft support, unchanged serving architecture."""
from collections import Counter
import torch

def select_vocabulary(rows,vocab_size,k):
    if not 0<k<=vocab_size:raise ValueError('invalid support size')
    counts=Counter()
    for r in rows:
        start=r['response_start'];ids=r['input_ids']
        if r['loss_mask']!=[False]*start+[True]*(len(ids)-start):raise ValueError('answer mask mismatch')
        for t in ids[start:]:
            if type(t)!=int or not 0<=t<vocab_size:raise ValueError('invalid target token')
            counts[t]+=1
    if not counts:raise ValueError('empty training responses')
    selected=sorted(range(vocab_size),key=lambda t:(-counts[t],t))[:k]
    return torch.tensor(sorted(selected),dtype=torch.long)

def apply_vocabulary(model,ids,target_head):
    old=torch.arange(len(model.d2t),device=model.d2t.device)+model.d2t
    ids=ids.to(old.device)
    if len(ids)!=len(old) or not torch.equal(ids,ids.unique(sorted=True)):raise ValueError('support must be sorted unique and fixed size')
    if target_head.shape[1]!=model.lm_head.weight.shape[1] or int(ids.max())>=len(target_head):raise ValueError('target head incompatible')
    mapping={int(t):i for i,t in enumerate(old)};retained=[(i,mapping[int(t)]) for i,t in enumerate(ids) if int(t) in mapping]
    fresh=target_head.index_select(0,ids.to(target_head.device)).to(model.lm_head.weight)
    with torch.no_grad():
        for new_index,old_index in retained:fresh[new_index].copy_(model.lm_head.weight[old_index])
        model.lm_head.weight.copy_(fresh)
        model.verifier_lm_head.weight.copy_(target_head.index_select(0,ids.to(target_head.device)).to(model.verifier_lm_head.weight))
        model.d2t.copy_(ids-torch.arange(len(ids),device=ids.device))
        model.t2d.zero_();model.t2d[ids.to(model.t2d.device)]=True
    return dict(retained_tokens=len(retained),new_tokens=len(ids)-len(retained),draft_size=len(ids),selection='answer token frequency descending; ties target token ID ascending; stored IDs ascending',head_initialization='overlap keeps family row; new rows use target LM head',old_ids=old.cpu().tolist(),new_ids=ids.cpu().tolist())
