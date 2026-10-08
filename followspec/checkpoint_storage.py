"""Opt-in immutable shared HF shards and trainable-only native checkpoints."""
import hashlib
import json
import os
import fcntl
from pathlib import Path
import torch
from safetensors.torch import save_file
from followspec.disk_guard import require_free


def _json(path, value):
    with path.open('x') as f:
        json.dump(value, f, indent=2)


def _digest(state):
    h=hashlib.sha256()
    for key,tensor in sorted(state.items()):
        t=tensor.detach().cpu().contiguous()
        h.update(json.dumps([key,str(t.dtype),list(t.shape)]).encode())
        h.update(t.view(torch.uint8).numpy().tobytes())
    return h.hexdigest()


def shared_export(model, dest, shared_root, state, mutable_keys, minimum_gb=0):
    """Exact merged tensors, ordinary HF index, hardlinks for immutable tensors.

    Content-addressing prevents sharing across different frozen tensors, including
    different families/initializations. Mutable tensors are never shared.
    """
    dest=Path(dest);root=Path(shared_root)
    require_free(dest,minimum_gb)
    dest.mkdir(parents=True,exist_ok=False);root.mkdir(parents=True,exist_ok=True)
    ignored=set(getattr(model,'_keys_to_ignore_on_save',[]) or [])
    state={k:v.detach().cpu().contiguous().clone() for k,v in state.items() if k not in ignored}
    fixed={k:v for k,v in state.items() if k not in mutable_keys}
    changed={k:v for k,v in state.items() if k in mutable_keys}
    if not changed:raise ValueError('export has no mutable weights')
    weight_map={}
    if fixed:
        digest=_digest(fixed);name=f'shared-{digest}.safetensors';path=root/name
        with (root/'.lock').open('a') as lock:
            fcntl.flock(lock,fcntl.LOCK_EX)
            if not path.exists():
                require_free(root,minimum_gb)
                tmp=root/f'.{digest}-{os.getpid()}.partial'
                save_file(fixed,tmp,metadata={'format':'pt'})
                os.chmod(tmp,0o444);os.rename(tmp,path)
            os.link(path,dest/name)
        weight_map.update({k:name for k in fixed})
    name='trainable.safetensors'
    require_free(dest,minimum_gb)
    save_file(changed,dest/name,metadata={'format':'pt'})
    weight_map.update({k:name for k in changed})
    # Same config serialization used by native HF save_pretrained, no model mutation.
    model.config.dtype=str(next(model.parameters()).dtype).split('.')[-1]
    model.config.architectures=[model.__class__.__name__]
    model.config.save_pretrained(dest)
    _json(dest/'model.safetensors.index.json',dict(metadata=dict(total_size=sum(v.numel()*v.element_size() for v in state.values())),weight_map=weight_map))
    _json(dest/'storage.json',dict(format='immutable shared HF shards',mutable_keys=sorted(changed),shared_keys=sorted(fixed),shared_root=str(root.resolve())))


def save_trainable_checkpoint(model,dest,optimizers,metadata,minimum_gb=0):
    require_free(dest,minimum_gb);dest=Path(dest);dest.mkdir(parents=True,exist_ok=False)
    state={k:v.detach().cpu().contiguous().clone() for k,v in model.named_parameters() if v.requires_grad}
    save_file(state,dest/'trainable.safetensors',metadata={'format':'pt'})
    opts=list(optimizers) if isinstance(optimizers,(list,tuple)) else [optimizers]
    saved=[]
    names={id(p):n for n,p in model.named_parameters()}
    for opt in opts:
        payload=opt.state_dict();groups=[];keep=set();parameter_names={}
        for group,live in zip(payload['param_groups'],opt.param_groups,strict=True):
            ids=[]
            for index,p in zip(group['params'],live['params'],strict=True):
                if p.requires_grad:ids.append(index);keep.add(index);parameter_names[index]=names[id(p)]
            groups.append(group|dict(params=ids))
        saved.append(payload|dict(param_groups=groups,state={k:v for k,v in payload['state'].items() if k in keep},parameter_names=parameter_names))
    torch.save(saved,dest/'optimizer_state_dict.pt')
    _json(dest/'trainable_checkpoint.json',metadata|dict(format='trainable-only; requires recorded pinned initialization',keys=sorted(state)))
