"""FIX-24: fill only an embedding genuinely absent from the drafter checkpoint."""
import hashlib,json
from pathlib import Path
import torch


def checkpoint_keys(checkpoint):
    p=Path(checkpoint)
    for name in ['model.safetensors.index.json','pytorch_model.bin.index.json']:
        if (p/name).exists():return set(json.loads((p/name).read_text())['weight_map'])
    if (p/'model.safetensors').exists():
        from safetensors import safe_open
        with safe_open(p/'model.safetensors',framework='pt',device='cpu') as f:return set(f.keys())
    if (p/'pytorch_model.bin').exists():
        return set(torch.load(p/'pytorch_model.bin',map_location='cpu',weights_only=True,mmap=True))
    raise ValueError(f'no supported local drafter checkpoint: {p}')


def tensor_sha256(tensor):
    t=tensor.detach().cpu().contiguous()
    h=hashlib.sha256();h.update(str(t.dtype).encode());h.update(str(list(t.shape)).encode());h.update(t.reshape(-1).view(torch.uint8).numpy().tobytes());return h.hexdigest()


def target_embedding(path):
    from speculators.utils.loading import load_model_layers
    return load_model_layers(['embed_tokens.weight'],str(path))['embed_tokens.weight']


def fill_missing_embedding(model,checkpoint,target):
    """Preserve explicit checkpoint embeddings and every unrelated parameter.

    Missing tensors may already have finite random HF initialization, so a NaN
    check (including native load_verifier_weights) is not sufficient here.
    """
    weight=model.embed_tokens.weight
    if 'embed_tokens.weight' in checkpoint_keys(checkpoint):
        return dict(source='checkpoint',checkpoint=str(checkpoint),embedding_sha256=tensor_sha256(weight),dtype=str(weight.dtype))
    source=target_embedding(target)
    if source.shape!=weight.shape:raise ValueError('target/drafter embedding shape mismatch')
    if not torch.isfinite(source).all():raise ValueError('nonfinite target embedding')
    cast=source.to(device=weight.device,dtype=weight.dtype)
    with torch.no_grad():weight.copy_(cast)
    if not torch.equal(weight,cast):raise AssertionError('embedding copy changed tensor')
    return dict(source='target_missing_checkpoint_embedding',checkpoint=str(checkpoint),target=str(target),source_dtype=str(source.dtype),dtype=str(weight.dtype),source_sha256=tensor_sha256(source),target_in_trainer_dtype_sha256=tensor_sha256(cast),embedding_sha256=tensor_sha256(weight),source_roundtrip_exact=torch.equal(weight.detach().cpu().to(source.dtype),source.cpu()))


def state_hashes(model):
    return {k:tensor_sha256(v) for k,v in model.state_dict().items()}


def probe_batches(model,loader,call,count):
    """Same autocast/train-mode forward as Trainer, with no optimizer updates."""
    import itertools
    model.train();device=next(model.parameters()).device;records=[]
    for batch in itertools.islice(loader,count):
        batch={k:v.to(device) if isinstance(v,torch.Tensor) else v for k,v in batch.items()}
        with torch.no_grad(),torch.autocast(device.type,dtype=torch.bfloat16):
            _tokens,_loss,metrics=model(**batch,**call)
        records.append({k:float(v.detach().cpu()) for k,v in metrics.items() if v.numel()==1})
    return records
