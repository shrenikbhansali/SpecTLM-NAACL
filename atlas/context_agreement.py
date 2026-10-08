"""D-44 exploratory HF teacher-forced first-draft agreement; no online AL claims.

The frozen online EAGLE checkpoint consumes feature[t-1] and token[t] to
predict token[t+1]. Compare against the full-vocabulary target argmax at t.
Keep the checkpoint's own embeddings/head fixed when switching the teacher.
"""
import argparse
import importlib.metadata
import json
from pathlib import Path
import subprocess
import time
import torch
from atlas.covariates import load_sequences, tap_layers
from atlas.run_cell import ensure_unpaused, sha256, write_new
from followspec.online_capture import OnlinePairCapture


def aligned_completion(draft_ids, target_argmax, response_start):
    if draft_ids.ndim != 1 or target_argmax.ndim != 1 or len(draft_ids) != len(target_argmax)-1:
        raise ValueError('one shifted draft sequence required')
    if not 2 <= response_start < len(target_argmax):
        raise ValueError('need two prompt tokens and a nonempty completion')
    # Prediction position p uses draft index p-2 and teacher logit index p-1.
    positions=torch.arange(response_start,len(target_argmax),device=draft_ids.device)
    return draft_ids[response_start-2:-1], target_argmax[response_start-1:-1], positions


def summarize_agreement(draft_ids, target_ids):
    if draft_ids.shape != target_ids.shape or not draft_ids.numel():
        raise ValueError('nonempty aligned tokens required')
    matches=int((draft_ids == target_ids).sum())
    return dict(matches=matches,n_tokens=draft_ids.numel(),agreement=matches/draft_ids.numel())


def first_draft(draft, ids, features):
    """Native causal, one-TTT-step forward; returned IDs are target vocabulary."""
    tokens=draft(hidden_states=features[:-1].unsqueeze(0),input_ids=ids[1:].unsqueeze(0),
                 document_ids=torch.zeros_like(ids[1:]).unsqueeze(0),
                 position_ids=torch.arange(1,len(ids),device=ids.device).unsqueeze(0),ttt_steps=1)[0][0]
    return tokens + draft.d2t[tokens] if draft.d2t is not None else tokens


def main():
    p=argparse.ArgumentParser(description=__doc__)
    for key in ['target','target-revision','drafter','drafter-revision','drafter-base','sequences','output']:
        p.add_argument('--'+key,required=True)
    p.add_argument('--dry-run',action='store_true');a=p.parse_args()
    rows,source=load_sequences(a.sequences,True)
    if any(r['response_start']<2 for r in rows):raise ValueError('two prompt tokens required')
    for path,revision in [(a.target,a.target_revision),(a.drafter,a.drafter_revision)]:
        if Path(path).name!=revision or len(revision)!=40:raise ValueError('pinned snapshots required')
    config=vars(a)|dict(source=source,n=len(rows),dtype='bfloat16',attention='eager',seed=0,K=1,
        backend={k:importlib.metadata.version(k) for k in ['torch','transformers','speculators']},
        code_commit=subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip(),
        source_sha256=sha256(__file__),prompt_sha256=source['prompt_sha256'],
        alignment='predict completion p from feature[p-2], input[p-1], teacher logits[p-1]; no after-EOS prediction',
        caveat='HF teacher-forced all completion positions, not vLLM speculative block-boundary acceptance')
    if a.dry_run:print(json.dumps(config,indent=2));return
    ensure_unpaused();ensure_unpaused(Path.cwd())
    if subprocess.check_output(['git','status','--porcelain','--untracked-files=no'],text=True).strip():raise ValueError('commit first')
    from transformers import AutoModelForCausalLM
    from speculators import SpeculatorModel,SpeculatorModelConfig
    from speculators.version import git_commit
    if git_commit!='261a82dd44ca05ff73006938c0614111bb2dd2b7':raise ValueError('wrong native backend')
    out=Path(a.output);out.mkdir(parents=True,exist_ok=False);start=time.perf_counter();torch.manual_seed(0)
    config['gpu_type']=torch.cuda.get_device_name(0);config['native_backend_commit']=git_commit
    if 'A40' not in config['gpu_type']:raise ValueError('A40 required')
    write_new(out/'config.json',config)
    try:
        target=AutoModelForCausalLM.from_pretrained(a.target,local_files_only=True,torch_dtype=torch.bfloat16,
            attn_implementation='eager').to('cuda').eval().requires_grad_(False)
        dc=SpeculatorModelConfig.from_pretrained(a.drafter,local_files_only=True)
        taps=tap_layers(json.loads((Path(a.drafter)/'config.json').read_text()),target.config.num_hidden_layers)
        dc.eagle_aux_hidden_state_layer_ids=taps;dc.speculators_config.verifier.name_or_path=a.drafter_base
        dc.transformer_layer_config._attn_implementation='eager'
        draft=SpeculatorModel.from_pretrained(a.drafter,config=dc,local_files_only=True,torch_dtype=torch.bfloat16).to('cuda').eval().requires_grad_(False)
        # Full vocabulary: argmax outside draft support is a genuine disagreement.
        capture=OnlinePairCapture(target,taps,torch.arange(target.config.vocab_size,dtype=torch.long))
        reports=[]
        with (out/'per_prompt.jsonl').open('x') as f:
            for row in rows:
                ensure_unpaused();ids=torch.tensor(row['input_ids'],device='cuda')
                with torch.no_grad():
                    features,_,logits=capture._forward(ids)
                    target_ids=logits.argmax(-1);del logits
                    drafted=first_draft(draft,ids,features)
                    d,t,positions=aligned_completion(drafted,target_ids,row['response_start'])
                    report=dict(prompt_id=row['prompt_id'],**summarize_agreement(d,t),
                        completion_positions=positions.tolist(),draft_ids=d.tolist(),target_argmax_ids=t.tolist(),
                        source_completion_ids=ids[row['response_start']:].tolist(),
                        target_matches_saved_completion=int((t==ids[row['response_start']:]).sum()))
                f.write(json.dumps(report)+'\n');f.flush();reports.append(report)
                print(row['prompt_id'],report['agreement'],flush=True)
        n=sum(r['n_tokens'] for r in reports);matches=sum(r['matches'] for r in reports)
        write_new(out/'results.json',dict(n_prompts=len(reports),n_tokens=n,matches=matches,
            micro_agreement=matches/n,macro_agreement=sum(r['agreement'] for r in reports)/len(reports),
            wall_s=time.perf_counter()-start,caveat=config['caveat']))
    except Exception as e:write_new(out/'failure.json',dict(type=type(e).__name__,error=str(e)));raise


if __name__=='__main__':main()
