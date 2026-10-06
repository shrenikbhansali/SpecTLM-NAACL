"""Explicit factor-only bank views matching pinned vLLM loader semantics.

vLLM 0.31.0 LoRAModel.from_lora_tensors skips is_base_embedding_weights:
.embed_tokens.base_layer.weight and .lm_head.base_layer.weight. PEFT instead
loads these tensors into the shared base. Such a bank file must use this
immutable view for online PEFT capture and mixtures to preserve the same target
as response generation. Originals and all LoRA factors remain unchanged.
"""
import copy
import hashlib
import json
from pathlib import Path
import shutil
from safetensors import safe_open
from safetensors.torch import save_file
import torch
from atlas.run_cell import sha256,write_new

POLICY='vllm_0.31.0_base_embedding_skip'
SUFFIXES=('.embed_tokens.base_layer.weight','.lm_head.base_layer.weight')


def check_files(root, hashes):
    for name,digest in hashes.items():
        if Path(name).is_absolute() or '..' in Path(name).parts or sha256(Path(root)/name)!=digest:
            raise ValueError('adapter view/source hash mismatch')


def canonical_bank(registry, output):
    result=copy.deepcopy(registry);root=Path(output)
    for name,entry in result.items():
        if entry['kind']!='bank':raise ValueError('canonicalization requires bank-only registry')
        check_files(entry['path'],entry['files_sha256'])
        source=Path(entry['path'])
        with safe_open(source/'adapter_model.safetensors',framework='pt',device='cpu') as f:
            extra=[k for k in f.keys() if not k.endswith(('.lora_A.weight','.lora_B.weight'))]
            if any(not k.endswith(SUFFIXES) for k in extra):raise ValueError('unsupported non-LoRA adapter tensors')
            if not extra:continue
            factors={k:f.get_tensor(k) for k in f.keys() if k not in extra}
        if not factors:raise ValueError('empty factor-only view')
        out=root/hashlib.sha256(name.encode()).hexdigest()[:16];out.mkdir(parents=True,exist_ok=False)
        shutil.copyfile(source/'adapter_config.json',out/'adapter_config.json')
        save_file(factors,str(out/'adapter_model.safetensors'))
        proof=dict(policy=POLICY,engine_version='0.31.0',source=str(source.resolve()),source_revision=entry['revision'],
                   source_files_sha256=entry['files_sha256'],skipped_keys=sorted(extra),retained_keys=sorted(factors),
                   reference='vllm/lora/lora_model.py:LoRAModel.from_lora_tensors and vllm/lora/utils.py:is_base_embedding_weights')
        write_new(out/'normalization.json',proof)
        entry.update(path=str(out.resolve()),normalization=dict(policy=POLICY,source=str(source.resolve())),
            files_sha256={p:sha256(out/p) for p in ['adapter_config.json','adapter_model.safetensors','normalization.json']})
        validate_view(entry)
    return result


def validate_view(entry):
    if 'normalization' not in entry:return
    if entry['normalization'].get('policy')!=POLICY:raise ValueError('unknown bank normalization policy')
    root=Path(entry['path']);check_files(root,entry['files_sha256'])
    proof=json.loads((root/'normalization.json').read_text())
    if proof['policy']!=POLICY or proof['engine_version']!='0.31.0' or proof['source_revision']!=entry['revision']:
        raise ValueError('bank view policy or revision differs')
    if proof['source']!=entry['normalization']['source']:raise ValueError('bank view source differs')
    check_files(proof['source'],proof['source_files_sha256'])
    if (root/'adapter_config.json').read_bytes()!=(Path(proof['source'])/'adapter_config.json').read_bytes():
        raise ValueError('bank view configuration changed')
    with safe_open(root/'adapter_model.safetensors',framework='pt',device='cpu') as a, safe_open(
        Path(proof['source'])/'adapter_model.safetensors',framework='pt',device='cpu') as b:
        omitted=set(b.keys())-set(a.keys())
        if not omitted or sorted(omitted)!=proof['skipped_keys'] or any(not k.endswith(SUFFIXES) for k in omitted):
            raise ValueError('view omitted unexpected parameters')
        if sorted(a.keys())!=proof['retained_keys']:raise ValueError('view retained keys differ')
        for key in a.keys():
            if key not in b.keys() or not key.endswith(('.lora_A.weight','.lora_B.weight')):
                raise ValueError('view inserted unsupported parameter')
            x=a.get_tensor(key);y=b.get_tensor(key)
            if x.dtype!=y.dtype or not torch.equal(x,y):raise ValueError('view changed LoRA factors')
