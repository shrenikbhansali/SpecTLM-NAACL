"""Effective weight-only targets and native CT quantization for offline covariates.

AWQ nibble order and GPTQ's symmetric/static restriction follow vLLM0.31.0
awq_triton.py / auto_gptq.py, not repository-name heuristics. Weight-only
targets are reconstructed in memory, never exported or substituted for B2.
"""
import json
from pathlib import Path
import torch


def unpack_awq(qweight,qzeros,scales,group_size):
    if qweight.ndim!=2 or scales.ndim!=2:raise ValueError('invalid AWQ shapes')
    n=qweight.shape[0];group_size=n if group_size==-1 else group_size
    if group_size<=0 or n%group_size or scales.shape!=(n//group_size,qweight.shape[1]*8) or qzeros.shape!=(n//group_size,qweight.shape[1]):raise ValueError('AWQ group/shape mismatch')
    shifts=torch.tensor([0,4,1,5,2,6,3,7],device=qweight.device)*4
    unpack=lambda t:((t[...,None].long()>>shifts)&15).reshape(t.shape[0],-1)
    w,z=unpack(qweight),unpack(qzeros);g=torch.arange(n,device=w.device)//group_size
    return ((w.float()-z[g].float())*scales[g].float()).T.contiguous()


def unpack_gptq_symmetric(qweight,scales,bits,group_size):
    if bits not in (4,8):raise ValueError('pinned engine supports symmetric GPTQ4/8 only')
    pack=32//bits;n=qweight.shape[0]*pack;group_size=n if group_size==-1 else group_size
    if group_size<=0 or n%group_size or scales.shape!=(n//group_size,qweight.shape[1]):raise ValueError('GPTQ group/shape mismatch')
    shifts=torch.arange(pack,device=qweight.device)*bits
    w=((qweight[:,None,:].long()>>shifts[None,:,None])&((1<<bits)-1)).reshape(n,-1)
    g=torch.arange(n,device=w.device)//group_size
    return ((w.float()-(1<<(bits-1)))*scales[g].float()).T.contiguous()


class TensorStore:
    def __init__(self,path):
        from safetensors import safe_open
        self.paths={};self.binary={};root=Path(path)
        safe=sorted(root.glob('*.safetensors'))
        if safe:
            for file in safe:
                with safe_open(file,framework='pt',device='cpu') as f:
                    for key in f.keys():
                        if key in self.paths:raise ValueError('duplicate checkpoint tensor')
                        self.paths[key]=file
        else:
            for file in sorted(root.glob('pytorch_model*.bin')):
                state=torch.load(file,map_location='cpu',weights_only=True,mmap=True)
                if set(state)&set(self.binary):raise ValueError('duplicate checkpoint tensor')
                self.binary.update(state)
        if not self.paths and not self.binary:raise ValueError('no supported checkpoint tensors')
    def __contains__(self,key):return key in self.paths or key in self.binary
    def __getitem__(self,key):
        from safetensors import safe_open
        if key in self.binary:return self.binary[key]
        with safe_open(self.paths[key],framework='pt',device='cpu') as f:return f.get_tensor(key)
    def keys(self):return set(self.paths)|set(self.binary)


def load_weight_only(path,device='cuda'):
    from transformers import AutoConfig,AutoModelForCausalLM
    from accelerate import init_empty_weights
    from accelerate.utils import set_module_tensor_to_device
    config=AutoConfig.from_pretrained(path,local_files_only=True,trust_remote_code=False)
    q=config.quantization_config;method=q['quant_method'];bits=q.get('bits',4)
    if method not in ('awq','gptq'):raise ValueError('not an AWQ/GPTQ target')
    if q.get('dynamic'):raise ValueError('per-module dynamic GPTQ rules need explicit validated handling')
    if method=='gptq' and (not q.get('sym',True) or (q.get('desc_act') and q.get('group_size')!=-1)):
        raise ValueError('GPTQ not supported by pinned engine symmetric/static contract')
    if method=='awq' and (bits!=4 or str(q.get('version','gemm')).lower()!='gemm'):raise ValueError('AWQ requires GEMM4 layout')
    delattr(config,'quantization_config');store=TensorStore(path);used=set()
    with init_empty_weights():model=AutoModelForCausalLM.from_config(config,torch_dtype=torch.bfloat16,attn_implementation='eager')
    for name,param in list(model.named_parameters()):
        prefix=name.removesuffix('.weight')
        if name in store:value=store[name];used.add(name)
        elif name.endswith('.weight') and prefix+'.qweight' in store:
            qweight=store[prefix+'.qweight'].to(device);scales=store[prefix+'.scales'].to(device)
            used.update([prefix+'.qweight',prefix+'.scales'])
            if method=='awq':
                zeros=store[prefix+'.qzeros'].to(device);used.add(prefix+'.qzeros')
                value=unpack_awq(qweight,zeros,scales,q['group_size'])
            else:
                value=unpack_gptq_symmetric(qweight,scales,bits,q['group_size'])
                # vLLM0.31 uses uint4b8/uint8b128 implicit symmetric zero points.
                for suffix in ('.qzeros','.g_idx'):
                    if prefix+suffix in store:used.add(prefix+suffix)
            del qweight,scales
        else:raise ValueError(f'missing model weight: {name}')
        if value.shape!=param.shape:raise ValueError(f'reconstructed shape mismatch: {name}')
        set_module_tensor_to_device(model,name,device,value=value.to(torch.bfloat16));del value
    # GPTQ serializers sometimes include zero biases for bias-free architecture.
    for key in store.keys()-used:
        if key.endswith('.bias') and not torch.count_nonzero(store[key]):continue
        if key.endswith('rotary_emb.inv_freq'):continue
        raise ValueError(f'unconsumed target tensor: {key}')
    model.tie_weights();model.to(device).eval()
    return model,dict(method=method,semantics='effective stored weight-only target, bf16 eager forward',quantization_config=q)


def load_child(path,device='cuda'):
    from transformers import AutoModelForCausalLM
    cfg=json.loads((Path(path)/'config.json').read_text());quant=cfg.get('quantization_config',{});method=quant.get('quant_method')
    if method in ('awq','gptq'):return load_weight_only(path,device)
    if method and method!='compressed-tensors':raise ValueError(f'unvalidated quantized backend: {method}')
    model=AutoModelForCausalLM.from_pretrained(path,torch_dtype=torch.bfloat16,local_files_only=True,trust_remote_code=False,attn_implementation='eager')
    if method=='compressed-tensors':
        model.hf_quantizer.compressor.decompress_model(model)
        # Native CT wrappers retain input/output quantize-dequantize operations.
        enabled=[m for m in model.modules() if getattr(m,'quantization_scheme',None)]
        if not enabled or any(getattr(m,'quantization_enabled',True) is not True for m in enabled):raise ValueError('native quantization hooks missing/disabled')
    return model.to(device).eval(),dict(method=method or 'dense',semantics='native Transformers / CT activation quantization retained',quantization_config=quant)
