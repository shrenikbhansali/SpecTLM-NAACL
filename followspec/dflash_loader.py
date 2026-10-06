"""Load the pinned released DFlash body through the pinned native converter."""
from pathlib import Path
import torch


def load_released_dflash(path,base,*,attention='simple_flex_attention',dtype=torch.float32,device='cuda'):
    from speculators.version import git_commit
    from speculators.convert.dflash.converter import DFlashConverter,_VERIFIER_FILLED_KEYS
    from speculators.convert.utils import load_checkpoint_config,load_checkpoint_weights
    from speculators.models.dflash import DFlashDraftModel
    from followspec.train_eagle3 import BACKEND
    if git_commit!=BACKEND:raise ValueError('wrong pinned native backend')
    path=Path(path);source=load_checkpoint_config(path);body=load_checkpoint_weights(path)
    cfg=DFlashConverter()._build_config(source,base,None)
    cfg.transformer_layer_config._attn_implementation=attention
    model=DFlashDraftModel(cfg)
    missing,unexpected=model.load_state_dict(body,strict=False,assign=True)
    if unexpected or set(missing)-_VERIFIER_FILLED_KEYS:raise ValueError('released DFlash body differs from native model')
    model.load_verifier_weights();model=model.to(dtype=dtype)
    for name,tensor in body.items():
        if not torch.equal(model.state_dict()[name],tensor.to(dtype)):raise ValueError('DFlash conversion changed body weights')
    return model.to(device)
