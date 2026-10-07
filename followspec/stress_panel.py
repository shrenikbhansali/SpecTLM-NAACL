"""D-39 fixed development screen with explicitly reserved confirmation inputs."""
import argparse
import hashlib
import json
from pathlib import Path
from atlas.run_cell import sha256,write_new
from atlas.workloads import prompt_hash,MinHashIndex
from followspec.production_pipeline import checked_stage,finish,jsonl,lines,new_output,read


def user_text(text):
    marker='<|start_header_id|>user<|end_header_id|>'
    return text.split(marker,1)[1].split('<|eot_id|>',1)[0].strip() if marker in text else text.strip()


def split_rows(rows,n,seed):
    if len(rows)<2*n or len({r['prompt_id'] for r in rows})!=len(rows) or len({prompt_hash(r['prompt']) for r in rows})!=len(rows):
        raise ValueError('need enough unique IDs and prompt contents')
    ordered=sorted(rows,key=lambda r:hashlib.sha256(f"{seed}:{r['prompt_id']}".encode()).hexdigest())
    return ordered[:n],ordered[n:2*n]


def adapter_provenance(path,base_id):
    path=Path(path);cfg=read(path/'adapter_config.json')
    if cfg.get('base_model_name_or_path')!=base_id or cfg.get('peft_type')!='LORA':raise ValueError('wrong local adapter base/type')
    files={p.name:sha256(p) for p in sorted(path.iterdir()) if p.is_file()}
    if not {'adapter_config.json','adapter_model.safetensors'}<=files.keys():raise ValueError('adapter files missing')
    return dict(adapter=str(path),revision=hashlib.sha1(json.dumps(files,sort_keys=True).encode()).hexdigest(),
        revision_kind='local content identity (SHA1 of complete SHA256 file map), not a Hub commit',files_sha256=files,
        license='llama3.1',training_base_revision=cfg.get('revision'),max_lora_rank=128)


def prepare(full_training,archive,output,*,domains=('code','math'),n=32,seed=20261007):
    from transformers import AutoTokenizer
    from atlas.adapter_similarity import load_factors,cosine_updates
    import torch
    torch.set_num_threads(2)
    training,tcfg=checked_stage(full_training);final,_=checked_stage(tcfg['finalized']);spec=tcfg['spec']
    tok=AutoTokenizer.from_pretrained(spec['base_snapshot'],local_files_only=True)
    out=new_output(output);archive=Path(archive).resolve()
    contexts={};forbidden_ids=set();registry={};inputs={}
    for arm in ('FS','MVD','PO-D','PO-T'):
        p=final/arm/'manifest.json';m=read(p);inputs[str(p)]=sha256(p)
        if arm=='FS':registry=m['registry']
        for r in m['samples']:
            # Include native validation too, to keep this screen separate from all fitting/early diagnostics.
            ids=r['context_token_ids'];h=hashlib.sha256(json.dumps(ids).encode()).hexdigest()
            contexts.setdefault(h,ids);forbidden_ids.add(r['sample_id'].split('::')[-1])
    near=MinHashIndex(.9);blocked=set()
    for ids in contexts.values():
        text=user_text(tok.decode(ids,skip_special_tokens=False));blocked.add(prompt_hash(text));near.add(text)
    del contexts
    targets=[];base_workloads={};reserved=[];rejected=[];spot=[];candidate_paths=[]
    for domain in domains:
        if domain not in ('code','math'):raise ValueError('screen only license-verified code/math; other domains reserved')
        split=archive/f'l31-{domain}-s0-splits-full-a1/splits'
        for file in ('adaptation.jsonl','calibration.jsonl','early_stop.jsonl'):
            p=split/file;inputs[str(p)]=sha256(p)
            for r in lines(p):
                text=user_text(r['prompt']);blocked.add(prompt_hash(text));near.add(text);forbidden_ids.add(r['prompt_id'])
        p=split/'evaluation.jsonl';inputs[str(p)]=sha256(p);kept=[]
        for r in lines(p):
            text=user_text(r['prompt']);ids=tok(r['prompt'],add_special_tokens=False)['input_ids']
            reason=('training_overlap' if r['prompt_id'] in forbidden_ids or prompt_hash(text) in blocked or near.query(text)
                    else 'context_over_3584' if len(ids)>3584 else None)
            if reason:rejected.append(dict(prompt_id=r['prompt_id'],reason=reason));continue
            if ids.count(tok.bos_token_id)!=1:raise ValueError('historical template must contain exactly one BOS')
            kept.append(r|dict(raw_prompt=text,rendered_token_ids=ids,format='chat_template_rendered',split='evaluation'))
        dev,confirm=split_rows(kept,n,seed)
        devpath=out/f'{domain}_development.jsonl';confirmpath=out/f'{domain}_confirmation_reserved.jsonl'
        jsonl(devpath,dev);jsonl(confirmpath,confirm);base_workloads[domain]=str(devpath)
        for r in dev[:5]:spot.append(dict(domain=domain,prompt_id=r['prompt_id'],decoded=tok.decode(r['rendered_token_ids']),
            reference=r['reference'],loss_mask=None,purpose='evaluation only; never trainer input'))
        for window in (0,1,3):
            adapter=archive/f'l31-{domain}-s0-drift-full-a1/adapters/window_{window:03d}'
            provenance=adapter_provenance(adapter,spec['base_id']);manifest=adapter.parent/'manifest.json';inputs[str(manifest)]=sha256(manifest)
            history=read(manifest);cmd=history['command']
            if cmd[cmd.index('--lr')+1]!='2e-4' or cmd[cmd.index('--steps-per-window')+1]!='50':raise ValueError('unexpected target update recipe')
            target=dict(model_id=f'local-d39/{domain}-sft-step{50*(window+1)}',pool='test',workloads={domain:str(devpath)},
                target_training_steps=50*(window+1),domain=domain,source_manifest=str(manifest),**provenance)
            targets.append(target);candidate_paths.append(adapter)
        reserved.append(dict(domain=domain,prompt_file=str(confirmpath),n=n,unmeasured_window=2))
    # Similarity is checked against every actual fitting target, including mixtures.
    factors=[load_factors(p) for p in candidate_paths];similarities=[]
    for name,item in registry.items():
        bank=load_factors(item['path'])
        for target,candidate in zip(targets,factors):
            cosine=cosine_updates(candidate,bank)
            similarities.append(dict(target=target['model_id'],training_target=name,cosine=cosine))
            if cosine is None or cosine>.9:raise ValueError(f'held-out weight overlap: {target["model_id"]} vs {name}')
    targets.insert(0,dict(model_id='base',pool='base',revision=spec['base_revision'],workloads=base_workloads))
    write_new(out/'targets.json',dict(decision_id='D-39',scope='Fixed development stress panel; no FS-outcome selection',targets=targets))
    write_new(out/'reserved.json',dict(prompts=reserved,model_domains=['hotpot','summ'],
        note='Reserved from this D-39 development campaign; archive benchmarks had earlier historical use. Fresh for selection here, not claimed never previously evaluated.'))
    write_new(out/'similarities.json',similarities);write_new(out/'decoded_spotchecks.json',spot)
    write_new(out/'audit.json',dict(n_development=n,n_reserved_per_domain=n,rejected=rejected,training_prompt_hashes=len(blocked),
        overlap_count=0,near_duplicate_threshold=.9,candidate_models=len(targets)-1,training_targets=len(registry),
        excluded_domains=[dict(domain='german',reason='upstream filtered dataset has no explicit license; defer pending authoritative terms')]))
    finish(out,dict(stage='stress-panel',decision_id='D-39',training=str(training),spec=spec,inputs_sha256=inputs,seed=seed,
        dataset_licenses={'code':{'license':'cc-by-4.0','source':'https://huggingface.co/datasets/google-research-datasets/mbpp'},
                          'math':{'license':'mit','source':'https://huggingface.co/datasets/openai/gsm8k'}},
        caveats='Historical adapter training base revision unspecified; evaluation composes content-pinned adapter with current pinned base. Updates within domain share a trajectory; not independent model replicates.'),
        dict(data_ready=True,n_targets=len(targets)-1,n_development_prompts=n*len(domains),confirmation_evaluated=False))
    return out


def main():
    p=argparse.ArgumentParser(description=__doc__)
    for name in ('full-training','archive','output'):p.add_argument('--'+name,required=True)
    a=p.parse_args();print(prepare(a.full_training,a.archive,a.output))

if __name__=='__main__':main()
