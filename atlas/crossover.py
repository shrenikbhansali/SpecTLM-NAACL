"""D46 fixed-prefix HF diagnostic; never an online acceptance measurement."""
import argparse
import importlib.metadata
import json
from pathlib import Path
import subprocess
import time
import numpy as np
import torch
from atlas.context_agreement import first_draft, aligned_completion
from atlas.covariates import tap_layers
from atlas.run_cell import ensure_unpaused, sha256, write_new
from followspec.online_capture import OnlinePairCapture


def effects(matrix):
    a = np.asarray(matrix, dtype=float)
    if a.shape != (2, 2):
        raise ValueError('features x verifier 2x2 required')
    pp, pc, cp, cc = a.ravel()
    return dict(feature=float((cp-pp+cc-pc)/2), policy=float((pc-pp+cc-cp)/2),
                interaction=float(cc-cp-pc+pp))


def paired_summary(rows, seed=0, n_boot=2000):
    a = np.asarray(rows, dtype=float)
    if a.ndim != 3 or a.shape[1:] != (2, 2) or not len(a) or not np.isfinite(a).all():
        raise ValueError('nonempty finite paired matrices required')
    rng = np.random.default_rng(seed)
    draws = np.stack([a[rng.integers(len(a), size=len(a))].mean(0) for _ in range(n_boot)])
    estimates = [effects(x) for x in draws]
    result = dict(n=len(a), matrix=a.mean(0).tolist(), matrix_ci95=np.quantile(draws,[.025,.975],axis=0).tolist())
    for key, value in effects(a.mean(0)).items():
        result[key] = dict(mean=value, ci95=np.quantile([x[key] for x in estimates],[.025,.975]).tolist())
    return result


def swap_tap(source, donor, index, n_taps):
    if source.shape != donor.shape or source.shape[-1] % n_taps or not 0 <= index < n_taps:
        raise ValueError('incompatible tap blocks')
    width = source.shape[-1] // n_taps
    result = source.clone()
    result[..., index*width:(index+1)*width] = donor[..., index*width:(index+1)*width]
    return result


def token_diagnostics(logits, support):
    values, indices = logits.float().topk(2, dim=-1)
    # Full vocabulary normalizer; never renormalize onto draft support.
    normalizer = logits.float().logsumexp(-1)
    return dict(top1=indices[:,0], oov=~torch.isin(indices[:,0], support.to(indices.device)),
                logit_margin=values[:,0]-values[:,1],
                prob_margin=(values[:,0]-normalizer).exp()-(values[:,1]-normalizer).exp())


def read_sequences(path):
    path = Path(path)
    cfg = json.loads((path.parent/'config.json').read_text())
    rows = [json.loads(s) for s in path.read_text().splitlines()]
    if cfg['sequences_sha256'] != sha256(path) or cfg['n'] != len(rows) or not rows:
        raise ValueError('source hash/count mismatch')
    if len({r['prompt_id'] for r in rows}) != len(rows):
        raise ValueError('duplicate prefixes')
    for r in rows:
        start, ids = r['response_start'], r['input_ids']
        if not 2 <= start < len(ids) <= 4096 or any(type(x) is not int or x < 0 for x in ids):
            raise ValueError('invalid sequence or boundary; no truncation')
        if r['assistant_mask'] != [0]*start+[1]*(len(ids)-start):
            raise ValueError('invalid completion mask')
    return rows, cfg


def main():
    p = argparse.ArgumentParser(description=__doc__)
    for name in ['parent','child','drafter','sequences','output']:
        p.add_argument('--'+name, required=True)
    p.add_argument('--dry-run',action='store_true')
    p.add_argument('--calibration',help='approved full affine/RMS HF diagnostic fitted on training contexts')
    a = p.parse_args()
    rows, source = read_sequences(a.sequences)
    for path in [a.parent,a.child,a.drafter]:
        if len(Path(path).name) != 40 or not Path(path).is_dir():
            raise ValueError('local pinned snapshot required')
    config = vars(a)|dict(source=source,n=len(rows),seed=0,dtype='bfloat16',attention='eager',
        code_commit=subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip(),
        source_sha256=sha256(__file__),backend={k:importlib.metadata.version(k) for k in ['torch','transformers','speculators']},
        caveat='HF teacher-forced diagnostic on all completion positions; not vLLM block-boundary acceptance',
        factors=dict(rows=['parent_taps','child_taps'],columns=['parent_verifier','child_verifier']))
    calibration=json.loads(Path(a.calibration).read_text()) if a.calibration else None
    if calibration:config['calibration_sha256']=sha256(a.calibration)
    if a.dry_run:
        print(json.dumps(config,indent=2));return
    ensure_unpaused();ensure_unpaused(Path.cwd())
    if subprocess.check_output(['git','status','--porcelain','--untracked-files=no'],text=True).strip():
        raise ValueError('commit first')
    from transformers import AutoModelForCausalLM
    from speculators import SpeculatorModel, SpeculatorModelConfig
    from speculators.version import git_commit
    if git_commit != '261a82dd44ca05ff73006938c0614111bb2dd2b7':
        raise ValueError('wrong native backend')
    config['gpu_type'] = torch.cuda.get_device_name(0)
    if 'A40' not in config['gpu_type']:
        raise ValueError('A40 required')
    out = Path(a.output);out.mkdir(parents=True,exist_ok=False)
    write_new(out/'config.json',config)
    begin=time.monotonic();torch.manual_seed(0)
    try:
        teachers=[AutoModelForCausalLM.from_pretrained(x,local_files_only=True,torch_dtype=torch.bfloat16,
            attn_implementation='eager').to('cuda').eval().requires_grad_(False) for x in [a.parent,a.child]]
        if teachers[0].config.vocab_size != teachers[1].config.vocab_size:
            raise ValueError('shared token vocabulary required')
        taps=tap_layers(json.loads((Path(a.drafter)/'config.json').read_text()),teachers[0].config.num_hidden_layers)
        dc=SpeculatorModelConfig.from_pretrained(a.drafter,local_files_only=True)
        dc.eagle_aux_hidden_state_layer_ids=taps;dc.speculators_config.verifier.name_or_path=a.parent
        dc.transformer_layer_config._attn_implementation='eager'
        draft=SpeculatorModel.from_pretrained(a.drafter,config=dc,local_files_only=True,
            torch_dtype=torch.bfloat16).to('cuda').eval().requires_grad_(False)
        support=torch.arange(len(draft.d2t),device='cuda')+draft.d2t if draft.d2t is not None else torch.arange(teachers[0].config.vocab_size,device='cuda')
        captures=[OnlinePairCapture(t,taps,torch.arange(t.config.vocab_size)) for t in teachers]
        reports=[]
        with (out/'per_prompt.jsonl').open('x') as f, torch.no_grad():
            for row in rows:
                ensure_unpaused();ids=torch.tensor(row['input_ids'],device='cuda');start=row['response_start']
                features=[];diagnostics=[]
                for capture in captures:
                    feat,_,logits=capture._forward(ids)
                    features.append(feat);diagnostics.append(token_diagnostics(logits,support));del logits
                labels=[d['top1'][start-1:-1] for d in diagnostics]
                def score(feat):
                    prediction=first_draft(draft,ids,feat)[start-2:-1]
                    return [float((prediction==t).float().mean()) for t in labels]
                matrix=[score(feat) for feat in features]
                swaps={}
                for direction,(src,dst) in enumerate([(0,1),(1,0)]):
                    for j,layer in enumerate(taps):
                        swaps[f'{src}_with_{dst}_layer_{layer}']=score(swap_tap(features[src],features[dst],j,len(taps)))
                details=[]
                for d in diagnostics:
                    details.append({k:v[start-1:-1].cpu().tolist() for k,v in d.items()})
                r=dict(prompt_id=row['prompt_id'],n_tokens=len(labels[0]),matrix=matrix,swaps=swaps,
                    top1_disagreement=float((labels[0]!=labels[1]).float().mean()),teachers=details)
                if calibration:
                    from followspec.calibration import transform
                    r['calibration']={kind:score(transform(features[1],calibration,kind)) for kind in ['affine','rms']}
                f.write(json.dumps(r)+'\n');f.flush();reports.append(r)
                print(row['prompt_id'],matrix,flush=True)
        result=paired_summary([r['matrix'] for r in reports])
        # Swaps have two verifier scores; pair each with the unchanged source.
        result['swaps']={key:paired_summary([[r['matrix'][int(key[0])],r['swaps'][key]] for r in reports]) for key in reports[0]['swaps']}
        if calibration:result['calibration']={kind:paired_summary([[r['matrix'][1],r['calibration'][kind]] for r in reports]) for kind in ['affine','rms']}
        result.update(wall_s=time.monotonic()-begin,n_tokens=sum(r['n_tokens'] for r in reports),caveat=config['caveat'])
        write_new(out/'results.json',result)
    except Exception as e:
        write_new(out/'failure.json',dict(type=type(e).__name__,error=str(e)));raise


if __name__=='__main__':main()
