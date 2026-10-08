"""Training-free tap calibration; RMS fold is compatible with frozen vLLM.

Fit one scalar mean and RMS per tap layer over assistant-prediction features.
Full affine uses centered RMS (standard deviation); RMS-only uses raw RMS.
The full affine is an HF-only diagnostic, never mislabeled as an online export.
"""
import argparse
import json
from pathlib import Path
import subprocess
import time
import torch
from atlas.run_cell import ensure_unpaused, sha256, write_new


class TapMoments:
    def __init__(self,n_taps):
        self.n_taps=n_taps;self.n=0;self.n_tokens=0;self.width=None
        self.total=torch.zeros(n_taps,dtype=torch.float64)
        self.square=torch.zeros(n_taps,dtype=torch.float64)
    def add(self,x):
        if x.ndim!=2 or x.shape[1]%self.n_taps or not torch.isfinite(x).all():
            raise ValueError('finite concatenated tap features required')
        width=x.shape[1]//self.n_taps
        if self.width is not None and self.width!=width:raise ValueError('tap width changed')
        self.width=width;x=x.detach().double().reshape(-1,self.n_taps,width)
        self.total+=x.sum((0,2)).cpu();self.square+=x.square().sum((0,2)).cpu()
        self.n+=len(x)*width;self.n_tokens+=len(x)
    def stats(self):
        if not self.n:raise ValueError('no calibration observations')
        mean=self.total/self.n;second=self.square/self.n
        return mean,second.sqrt(),(second-mean.square()).clamp_min(0).sqrt()


def calibration_parameters(parent,child):
    if parent.n!=child.n or parent.width!=child.width or parent.n_taps!=child.n_taps:
        raise ValueError('paired moments required')
    pm,pr,ps=parent.stats();cm,cr,cs=child.stats()
    if (cr<=0).any() or (cs<=0).any():raise ValueError('zero child RMS')
    affine_scale=ps/cs
    return dict(n_tokens=parent.n_tokens,width=parent.width,n_taps=parent.n_taps,
        parent_mean=pm.tolist(),child_mean=cm.tolist(),parent_rms=pr.tolist(),child_rms=cr.tolist(),
        affine_scale=affine_scale.tolist(),affine_offset=(pm-affine_scale*cm).tolist(),
        rms_scale=(pr/cr).tolist(),semantics='one scalar per tap layer; affine centered RMS, online raw RMS')


def transform(x,parameters,kind):
    if kind not in {'affine','rms'}:raise ValueError('unknown calibration kind')
    if x.shape[-1]!=parameters['width']*parameters['n_taps']:raise ValueError('feature width mismatch')
    scale=x.new_tensor(parameters[kind+'_scale']).repeat_interleave(parameters['width'])
    result=x*scale
    if kind=='affine':result=result+x.new_tensor(parameters['affine_offset']).repeat_interleave(parameters['width'])
    return result


def fold_rms(weight,parameters):
    if weight.ndim!=2 or weight.shape[1]!=parameters['width']*parameters['n_taps']:
        raise ValueError('fc input width mismatch')
    return weight*weight.new_tensor(parameters['rms_scale']).repeat_interleave(parameters['width'])[None,:]


def main():
    p=argparse.ArgumentParser(description=__doc__)
    for key in ['parent','child','drafter','data','audit','forbidden','output']:p.add_argument('--'+key,required=True)
    p.add_argument('--dry-run',action='store_true');a=p.parse_args()
    from followspec.family_repair import validate_rows
    from atlas.workloads import prompt_hash
    rows=[json.loads(s) for s in Path(a.data).read_text().splitlines()]
    forbidden={prompt_hash(r.get('raw_prompt',r.get('prompt'))) for r in [json.loads(s) for s in Path(a.forbidden).read_text().splitlines()]}
    validate_rows(rows,forbidden,4096)
    audit=json.loads(Path(a.audit).read_text())
    if not audit.get('passed') or audit.get('data_sha256')!=sha256(a.data):raise ValueError('manual decoded audit required')
    for path in [a.parent,a.child,a.drafter]:
        if len(Path(path).name)!=40 or not Path(path).is_dir():raise ValueError('pinned snapshots required')
    cfg=vars(a)|dict(n=len(rows),seed=0,data_sha256=sha256(a.data),audit_sha256=sha256(a.audit),
        forbidden_sha256=sha256(a.forbidden),code_commit=subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip(),
        source_sha256=sha256(__file__),fit_positions='completion-prediction feature[p-2], excluding after-EOS',
        owner_approval='2026-10-08: full affine HF diagnostic; RMS-only frozen-harness evaluation')
    if a.dry_run:print(json.dumps(cfg,indent=2));return
    ensure_unpaused();ensure_unpaused(Path.cwd())
    if subprocess.check_output(['git','status','--porcelain','--untracked-files=no'],text=True).strip():raise ValueError('commit first')
    if 'A40' not in torch.cuda.get_device_name(0):raise ValueError('A40 required')
    from speculators import SpeculatorModel,SpeculatorModelConfig
    from speculators.version import git_commit
    from followspec.train_eagle3 import BACKEND
    if git_commit!=BACKEND:raise ValueError('wrong native backend')
    from transformers import AutoModelForCausalLM
    from followspec.online_capture import OnlinePairCapture
    from atlas.covariates import tap_layers
    out=Path(a.output);out.mkdir(parents=True,exist_ok=False);write_new(out/'config.json',cfg)
    begin=time.monotonic();torch.manual_seed(0)
    try:
        taps=tap_layers(json.loads((Path(a.drafter)/'config.json').read_text()),json.loads((Path(a.parent)/'config.json').read_text())['num_hidden_layers'])
        moments=[]
        # Same saved contexts, sequential models to reduce peak memory.
        for path in [a.parent,a.child]:
            teacher=AutoModelForCausalLM.from_pretrained(path,local_files_only=True,torch_dtype=torch.bfloat16,
                attn_implementation='eager').to('cuda').eval().requires_grad_(False)
            capture=OnlinePairCapture(teacher,taps,torch.tensor([0]))
            moment=TapMoments(len(taps))
            for row in rows:
                ensure_unpaused();features,_,_=capture._forward(torch.tensor(row['input_ids'],device='cuda'))
                moment.add(features[row['response_start']-2:-2]);del features
            moments.append(moment);del capture,teacher;torch.cuda.empty_cache()
        fitted=calibration_parameters(*moments);fitted['taps']=taps
        write_new(out/'calibration.json',fitted)
        dc=SpeculatorModelConfig.from_pretrained(a.drafter,local_files_only=True)
        dc.speculators_config.verifier.name_or_path=a.parent;dc.eagle_aux_hidden_state_layer_ids=taps
        draft=SpeculatorModel.from_pretrained(a.drafter,config=dc,local_files_only=True,torch_dtype=torch.float32)
        if draft.fc.bias is not None:raise ValueError('expected bias-free fc')
        with torch.no_grad():draft.fc.weight.copy_(fold_rms(draft.fc.weight,fitted))
        dest=out/'export-rms';draft.save_pretrained(dest,safe_serialization=True)
        write_new(dest/'repair_provenance.json',dict(kind='training-free RMS-only',fit_sha256=sha256(out/'calibration.json'),
            config_sha256=sha256(out/'config.json'),elapsed_s=time.monotonic()-begin,changed_keys=['fc.weight']))
        write_new(out/'results.json',dict(n=len(rows),n_tokens=fitted['n_tokens'],wall_s=time.monotonic()-begin,
            export=str(dest),full_affine='HF diagnostic only',online='RMS-only; frozen engine unchanged'))
    except Exception as e:write_new(out/'failure.json',dict(error=str(e),type=type(e).__name__));raise


if __name__=='__main__':main()
