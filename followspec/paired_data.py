"""Paired feature input contract for B6; B5 must produce and audit these shards.

Manifest records have sample_id, target_id, split, prompt_sha256, path, sha256,
and raw token length. Safetensors store an entire single sequence before the
native EAGLE shift. Shared input_ids guarantee identical child/base prefixes.
"""
import hashlib
import json
from pathlib import Path
import torch
from torch.utils.data import Dataset

FEATURES=('hidden_states','base_hidden_states','verifier_last_hidden_states','base_verifier_last_hidden_states')
REQUIRED={'input_ids','loss_mask',*FEATURES}
LABELS={'child_target_logits','base_target_logits'}


def file_sha(path):
    h=hashlib.sha256()
    with Path(path).open('rb') as f:
        for chunk in iter(lambda:f.read(8*1024**2),b''):h.update(chunk)
    return h.hexdigest()


def shift_paired(raw):
    if not REQUIRED<=raw.keys() or raw.keys()-REQUIRED-LABELS:
        raise ValueError('paired feature shard schema mismatch')
    if bool(raw.keys()&LABELS) and not LABELS<=raw.keys():raise ValueError('both target projections required')
    ids=raw['input_ids'];length=len(ids)
    if ids.ndim!=1 or length<2 or ids.dtype!=torch.long:raise ValueError('one token sequence required')
    if raw['loss_mask'].shape!=ids.shape or raw['loss_mask'].dtype!=torch.bool:raise ValueError('boolean loss mask required')
    if any(v.shape[0]!=length for v in raw.values()):raise ValueError('paired token alignment mismatch')
    if any(raw[k].shape!=raw['base_'+k].shape for k in ('hidden_states','verifier_last_hidden_states')):
        raise ValueError('paired feature dimensions mismatch')
    if any(v.ndim!=2 or not torch.isfinite(v).all() for k,v in raw.items() if k not in ('input_ids','loss_mask')):
        raise ValueError('finite 2D features required')
    result={k:(v[:-1] if k in ('hidden_states','base_hidden_states') else v[1:]) for k,v in raw.items()}
    result.update(lengths=torch.tensor([length-1]),position_ids=torch.arange(1,length))
    return result


def validate_packed(batch,ttt_steps):
    docs=batch['document_ids'];mask=batch['loss_mask']
    if mask.shape!=docs.shape or docs.shape!=batch['input_ids'].shape:raise ValueError('packed shapes mismatch')
    if (mask & (docs<0)).any():raise ValueError('padding must be masked')
    for step in range(1,ttt_steps):
        if (mask[:,step:] & (docs[:,:-step]!=docs[:,step:])).any():
            raise ValueError('assistant loss would cross a document boundary; correct source masks')


class PairedFeatureDataset(Dataset):
    def __init__(self,manifest_path,*,split,allowed_targets,forbidden_hashes=(),noise_std=0.):
        self.noise_std=noise_std
        self.root=Path(manifest_path).resolve().parent
        self.manifest=json.loads(Path(manifest_path).read_text())
        if self.manifest.get('schema')!='followspec_paired_features_v1':raise ValueError('wrong paired manifest schema')
        self.rows=[r for r in self.manifest['samples'] if r['split']==split]
        if not self.rows:raise ValueError('empty split')
        if len({r['sample_id'] for r in self.manifest['samples']})!=len(self.manifest['samples']):raise ValueError('duplicate sample IDs')
        seen_splits={}
        for r in self.manifest['samples']:
            if r['target_id'] not in allowed_targets:raise ValueError('non-bank target in training data')
            if r['prompt_sha256'] in forbidden_hashes:raise ValueError('evaluation prompt in training data')
            prior=seen_splits.setdefault(r['prompt_sha256'],r['split'])
            if prior!=r['split']:raise ValueError('training/validation prompt overlap')
            if r['length']<2:raise ValueError('empty sample')
        self.approx_lengths=[r['length']-1 for r in self.rows]
        self.hidden_states_dtype=torch.bfloat16

    def __len__(self):return len(self.rows)

    def __getitem__(self,index):
        from safetensors.torch import load_file
        r=self.rows[index];path=(self.root/r['path']).resolve()
        if not path.is_relative_to(self.root):raise ValueError('shard outside manifest directory')
        if file_sha(path)!=r['sha256']:raise ValueError('feature shard hash mismatch')
        raw=load_file(str(path))
        if len(raw['input_ids'])!=r['length']:raise ValueError('manifest token length mismatch')
        if self.noise_std:
            # Native uniform augmentation, one shared draw preserves paired shifts.
            noise=2*(torch.rand_like(raw['hidden_states'])-.5)*self.noise_std
            raw['hidden_states']=raw['hidden_states']+noise
            raw['base_hidden_states']=raw['base_hidden_states']+noise
        return dict(tensors=shift_paired(raw),target_id=r['target_id'],sample_id=r['sample_id'])


class PairedCollator:
    def __init__(self,total_seq_len,hidden_size,num_target_layers,ttt_steps):
        from speculators.train.data import CollateFn
        self.native=CollateFn(total_seq_len,hidden_size,num_target_layers,dtype=torch.bfloat16)
        self.max_len=total_seq_len;self.ttt_steps=ttt_steps
    def __call__(self,items):
        if sum(int(i['tensors']['lengths'].sum()) for i in items)>self.max_len:
            raise ValueError('packing exceeds token budget; no silent truncation')
        if any(i['tensors'].keys()!=items[0]['tensors'].keys() for i in items):raise ValueError('mixed projection schemas in batch')
        batch=self.native([i['tensors'] for i in items])
        batch['target_id']=[i['target_id'] for i in items]
        validate_packed(batch,self.ttt_steps)
        return batch
