"""Immutable CPU stages for M1/M2. GPU work is emitted for the operator."""
import argparse
import csv
from datetime import date
import json
from pathlib import Path
import random
import subprocess

from atlas.run_cell import sha256, write_new
from atlas.workloads import prompt_hash
from followspec.production import (ARMS, admission_selection, allocate_queries, checked_queries,
                                   launcher_job, match_tails, sample_candidates, validate_spec)


def read(path):
    return json.loads(Path(path).read_text())


def lines(path):
    return [json.loads(s) for s in Path(path).read_text().splitlines() if s.strip()]


def jsonl(path, rows):
    path = Path(path); path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('x') as f:
        for row in rows:f.write(json.dumps(row, allow_nan=False)+'\n')


def finish(out, config, result):
    write_new(out/'config.json', config | dict(code_commit=subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip()))
    write_new(out/'results.json', result)
    write_new(out/'ledger_draft.json', dict(id='EXP-ATL-UNASSIGNED',title=out.name,landed=str(date.today()),status='pilot',
        what_why='D-27 method production data preparation and exact matched controls',new=config['stage'],
        artifacts=str(out),config_results=dict(config=config,results=result),
        caveats='CPU data preparation only; operator launches and verifies GPU runs. No transfer-performance claim.'))
    # Hash every stage output except this envelope. Recheck at every dependent stage.
    write_new(out/'stage_files.json', {str(p.relative_to(out)):sha256(p) for p in out.rglob('*') if p.is_file()})


def checked_stage(path):
    root = Path(path).resolve()
    for name, digest in read(root/'stage_files.json').items():
        if Path(name).is_absolute() or '..' in Path(name).parts or sha256(root/name) != digest:
            raise ValueError('production stage changed')
    return root, read(root/'config.json')


def new_output(path):
    out = Path(path).resolve(); out.mkdir(parents=True, exist_ok=False); return out


def base_args(spec):
    return ['--base-snapshot',spec['base_snapshot'],'--base-id',spec['base_id'],'--base-revision',spec['base_revision']]


def load_bank(spec):
    """Frozen A2 identities, staging sizes/hashes and accepted A2 proofs."""
    from argparse import Namespace
    from atlas.filter_pool import resolve_target
    from atlas.generate_magpie import verify_inputs
    csv.field_size_limit(16*1024**2)
    with open(spec['pool_manifest']) as f:rows=[r for r in csv.DictReader(f) if r['in_bank']=='True']
    if len(rows)!=33 or len({r['model_id'] for r in rows})!=33:
        raise ValueError('D-27 needs the complete 33-child frozen Llama bank')
    registry = {}; metadata = {}
    for r in sorted(rows,key=lambda x:x['model_id']):
        name=r['model_id']
        if r['type']!='lora_adapter' or r['pool']!='bank' or r['base_revision']!=spec['base_revision']:
            raise ValueError('invalid frozen bank identity')
        _, adapter, staged=resolve_target(Namespace(**dict(base_id=spec['base_id'],base_revision=spec['base_revision'],
            base_snapshot=spec['base_snapshot'],derivative_id=name,pool=spec['staging_manifest'],downloads=spec['downloads'],adapter=None)))
        if staged['revision']!=r['revision'] or Path(adapter).resolve()!=Path(r['staged_path']).resolve():
            raise ValueError('staging differs from frozen bank')
        tok=spec['base_snapshot'] if staged['tokenizer_source']=='inherited_base' else adapter
        tokrev=spec['base_revision'] if staged['tokenizer_source']=='inherited_base' else r['revision']
        hashes=verify_inputs(staged,adapter,tok,tokrev)
        proof=Path(spec['artifacts_root'])/r['a2_run_id']/'cell'
        cfg=read(proof/'config.json'); res=read(proof/'results.json'); prov=read(proof/'target_provenance.json')
        if cfg['derivative_id']!=name or prov['revision']!=r['revision'] or res.get('accepted') is not True:
            raise ValueError('frozen bank A2 proof differs or failed')
        registry[name]=dict(kind='bank',path=adapter,revision=r['revision'],files_sha256=hashes,rank=int(r['r']),license=r['license'])
        metadata[name]=dict(tokenizer=tok,tokenizer_revision=tokrev,filter_run=str(proof),
            filter_sha256={f:sha256(proof/f) for f in ['config.json','results.json','target_provenance.json']})
    return registry, metadata


def prepare(spec_path, output):
    """No weights synthesized and no models loaded; both candidate rounds pinned."""
    spec=validate_spec(read(spec_path)); registry,metadata=load_bank(spec)
    general=lines(spec['general_prompts']); forbidden=[q for p in spec['forbidden_files'] for q in lines(p)]
    checked_queries(general,'general', {prompt_hash(q['prompt']) for q in forbidden})
    if len(general)!=20000:raise ValueError('D-27 requires the pinned general20000 pool')
    candidates=sample_candidates(registry,seed=spec['seed'],max_lora_rank=spec['max_lora_rank'])
    out=new_output(output)
    write_new(out/'spec.json',spec);write_new(out/'bank_registry.json',registry);write_new(out/'bank_metadata.json',metadata)
    write_new(out/'candidates.json',candidates)
    reference=random.Random(spec['seed']).sample(general,128);jsonl(out/'reference_queries.jsonl',reference)
    finish(out,dict(stage='prepare',spec=spec,spec_sha256=sha256(spec_path),
        inputs_sha256={p:sha256(p) for p in [spec['pool_manifest'],spec['staging_manifest'],spec['downloads'],spec['general_prompts'],*spec['forbidden_files']]}),
        dict(n_bank=33,n_candidate_plans=60,n_reference=128,production_ready=False,
             next='materialize round1 on CPU, then operator launches baseline followed by filter jobs'))
    return out


def materialize(plan, output, *, previous=None):
    from followspec.mixture import mix
    from followspec.mixture_targets import checked_files
    from followspec.train_eagle3 import ensure_unpaused
    from atlas.filter_pool import prepare_reference
    from transformers import AutoTokenizer
    import torch
    plan,cfg=checked_stage(plan);spec=cfg['spec']; registry=read(plan/'bank_registry.json')
    for path,digest in cfg['inputs_sha256'].items():
        if sha256(path)!=digest:raise ValueError('planning input changed')
    round_number=1
    if previous:
        old,oc=checked_stage(previous);res=read(old/'results.json')
        if Path(oc['plan'])!=plan or res.get('next_round')!=2:raise ValueError('round2 requires complete round1 admission with fewer than30 passes')
        round_number=2
    for entry in registry.values():checked_files(entry['path'],entry['files_sha256'])
    ensure_unpaused()
    candidates=read(plan/'candidates.json'); out=new_output(output)
    from followspec.adapter_views import canonical_bank
    if round_number==1:
        registry=canonical_bank(registry,out/'bank_views')
    else:
        registry={k:v for k,v in read(old/'registry.json').items() if v['kind']=='bank'}
    for candidate in candidates:
        if candidate['round']!=round_number:continue
        ensure_unpaused()
        name=candidate['id'];dest=out/'mixtures'/name
        mix([registry[k]['path'] for k in candidate['source_ids']],candidate['weights'],candidate['scale'],dest,
            max_lora_rank=spec['max_lora_rank'],dtype=torch.bfloat16)
        registry[name]=dict(kind='mixture',path=str(dest),revision=sha256(dest/'mixture_manifest.json'),source_ids=candidate['source_ids'],
            files_sha256={f:sha256(dest/f) for f in ['adapter_config.json','adapter_model.safetensors','mixture_manifest.json']},
            admission_pending=True)
    write_new(out/'registry.json',registry)
    if round_number==1:
        refdir=out/'reference';refdir.mkdir()
        tokenizer=AutoTokenizer.from_pretrained(spec['base_snapshot'],local_files_only=True,trust_remote_code=False)
        refs=prepare_reference(lines(plan/'reference_queries.jsonl'),tokenizer,2048);jsonl(refdir/'reference.jsonl',refs)
        write_new(refdir/'config.json',dict(base_id=spec['base_id'],base_revision=spec['base_revision'],
            source_prompts=str(plan/'reference_queries.jsonl'),prompt_sha256=sha256(plan/'reference_queries.jsonl'),
            max_reference_tokens=2048,reference_sha256=sha256(refdir/'reference.jsonl'),ppl_definition='fixed_prompt_tokens',n=128))
        baseline=out/'runs'/'baseline'
    else:
        prev,_=checked_stage(previous);oldround=Path(read(prev/'config.json')['round_dir']);oldcfg=read(oldround/'config.json')
        refdir=Path(oldcfg['reference']).parent;baseline=Path(oldcfg['baseline'])
    common=['-m','atlas.filter_pool',*base_args(spec),'--drafter',spec['drafter_snapshot'],'--drafter-revision',spec['drafter_revision'],
            '--reference',str(refdir/'reference.jsonl'),'--max-lora-rank',str(spec['max_lora_rank']),
            '--seed',str(spec['seed']),'--K','4','--repetition-threshold','0.5']
    if round_number==1:
        jsonl(out/'baseline_jobs.jsonl',[launcher_job(spec,out.name+'-baseline','M1',plan/'reference_queries.jsonl',
            common+['--output',str(baseline)])])
    filter_runs={};jobs=[]
    for i,(name,entry) in enumerate(sorted(registry.items())):
        if round_number==2 and entry['kind']=='bank':continue
        dest=out/'runs'/f'target-{i:03}';filter_runs[name]=str(dest)
        cmd=common+['--derivative-id',name,'--baseline',str(baseline),'--output',str(dest)]
        if entry['kind']=='bank':cmd+=['--pool',spec['staging_manifest'],'--downloads',spec['downloads']]
        else:cmd+=['--adapter',entry['path'],'--adapter-revision',entry['revision']]
        jobs.append(launcher_job(spec,f'{out.name}-filter-{i:03}','M1',plan/'reference_queries.jsonl',cmd))
    write_new(out/'filter_runs.json',filter_runs);jsonl(out/'filter_jobs.jsonl',jobs)
    finish(out,dict(stage='materialize',plan=str(plan),round=round_number,previous=str(previous) if previous else None,
                    reference=str(refdir/'reference.jsonl'),baseline=str(baseline),spec=spec),
           dict(n_candidates=30,n_filter_jobs=len(jobs),production_ready=False,
                dependencies=['baseline results before filter queue','complete round before admission']))
    return out


def retry_filters(round_dir, targets, output):
    """Fresh attempt paths for explicitly failed cells; retain all earlier bytes."""
    root,cfg=checked_stage(round_dir)
    if cfg['stage'] not in {'materialize','retry-filters'}:raise ValueError('filter round required')
    runs=read(root/'filter_runs.json');registry=read(root/'registry.json')
    if not targets or len(set(targets))!=len(targets) or not set(targets)<=runs.keys():
        raise ValueError('distinct known failed targets required')
    jobs=lines(root/('all_filter_jobs.jsonl' if (root/'all_filter_jobs.jsonl').exists() else 'filter_jobs.jsonl'))
    selected={};failures={}
    for name in targets:
        failure=Path(runs[name])/'failure.json'
        if not failure.is_file():raise ValueError('explicit failure evidence required; do not retry successful or active cells')
        read(failure);failures[str(failure)]=sha256(failure)
        matches=[]
        for index,job in enumerate(jobs):
            command=job['args'][job['args'].index('--')+1:]
            if '--derivative-id' in command and command[command.index('--derivative-id')+1]==name:
                if command[command.index('--output')+1]!=runs[name]:raise ValueError('retry job output differs from recorded run')
                matches.append(index)
        if len(matches)!=1:raise ValueError('exactly one original job per failed target required')
        selected[name]=matches[0]
    out=new_output(output);retry_jobs=[]
    for name,index in sorted(selected.items()):
        job=jobs[index];args=list(job['args']);new_name=out.name+'-'+job['name']
        args[args.index('--tag')+1]=new_name
        sep=args.index('--');output_index=args.index('--output',sep)+1
        dest=out/'runs'/Path(runs[name]).name
        args[output_index]=str(dest);runs[name]=str(dest)
        jobs[index]=dict(job,name=new_name,args=args);retry_jobs.append(jobs[index])
    write_new(out/'registry.json',registry);write_new(out/'filter_runs.json',runs)
    jsonl(out/'filter_jobs.jsonl',retry_jobs);jsonl(out/'all_filter_jobs.jsonl',jobs)
    finish(out,cfg|dict(stage='retry-filters',parent_round=str(root),retry_targets=sorted(targets),
        parent_stage_sha256=sha256(root/'stage_files.json'),failure_evidence_sha256=failures),
        dict(n_retry_jobs=len(retry_jobs),production_ready=False,
             next='operator runs filter_jobs; admit this overlay after all referenced cells complete'))
    return out


def admit(round_dir, output):
    from followspec.mixture_targets import collect_admission,validate_registry
    root,cfg=checked_stage(round_dir);spec=cfg['spec'];plan,pc=checked_stage(cfg['plan'])
    registry=read(root/'registry.json');runs=read(root/'filter_runs.json');allresults={};oldregistry={}
    if cfg['round']==2:
        old,oc=checked_stage(cfg['previous']);allresults=read(old/'admission_results.json');oldregistry=read(old/'registry.json')
        bank_runs=read(old/'bank_filter_runs.json')
    else:bank_runs={k:v for k,v in runs.items() if registry[k]['kind']=='bank'}
    # Every run must be complete. A crashed candidate is not an admission decision.
    for run in [*bank_runs.values(),*runs.values()]:
        if not (Path(run)/'results.json').exists() or (Path(run)/'failure.json').exists():
            raise ValueError('complete successful filter run required; retry failed/missing cells before admission')
    computed={}
    for name,entry in registry.items():
        if entry['kind']=='mixture':
            result,evidence=collect_admission(name,registry,runs[name],bank_runs,spec['pool_manifest'])
            computed[name]=(result,evidence);allresults[name]=result['accepted']
    selection=admission_selection([r['id'] for r in read(plan/'candidates.json')],allresults)
    out=new_output(output);final={k:v for k,v in registry.items() if v['kind']=='bank'}
    for name,(result,evidence) in computed.items():
        proof=out/'admission'/name;proof.mkdir(parents=True)
        write_new(proof/'config.json',dict(mixture_filter_run=runs[name],bank_filter_runs=bank_runs,
            pool_manifest=spec['pool_manifest'],evidence_sha256=evidence))
        write_new(proof/'results.json',result)
        if name in selection['admitted']:
            entry=registry[name].copy();entry.pop('admission_pending',None)
            entry['admission']=dict(path=str(proof),files_sha256={f:sha256(proof/f) for f in ['config.json','results.json']})
            final[name]=entry
    for name in selection['admitted']:
        if name not in final:final[name]=oldregistry[name]
    validate_registry(final)
    write_new(out/'registry.json',final);write_new(out/'admission_results.json',allresults);write_new(out/'bank_filter_runs.json',bank_runs)
    finish(out,dict(stage='admit',plan=str(plan),round_dir=str(root),spec=spec), selection|dict(production_ready=False))
    return out


def mixture_prompts(admission, output, forbidden_files):
    from followspec.mixture_targets import validate_registry
    root,cfg=checked_stage(admission);spec=cfg['spec'];registry=read(root/'registry.json');validate_registry(registry)
    if not read(root/'results.json')['ready']:raise ValueError('mixture admission not ready')
    forbidden=sorted(set(spec['forbidden_files']+forbidden_files+[spec['general_prompts']]))
    for p in forbidden:lines(p)
    out=new_output(output);jobs=[];paths={}
    for i,(name,entry) in enumerate(sorted(registry.items())):
        if entry['kind']!='mixture':continue
        dest=out/'runs'/name;paths[name]=str(dest/'prompts.jsonl')
        command=['-m','atlas.generate_magpie','--derivative-id',name,'--target-registry',str(root/'registry.json'),
            '--target',spec['base_id'],'--revision',spec['base_revision'],'--adapter',entry['path'],
            '--tokenizer',spec['base_snapshot'],'--tokenizer-revision',spec['base_revision'],'--family','llama',
            '--split','training','--seed',str(spec['seed']+1000+i),'--allow-a40-production','--output',str(dest),
            '--forbidden-files',*forbidden]
        jobs.append(launcher_job(spec,f'{out.name}-magpie-{i:03}','M2',spec['general_prompts'],command))
    jsonl(out/'jobs.jsonl',jobs);write_new(out/'prompt_paths.json',paths)
    finish(out,dict(stage='mixture-prompts',admission=str(root),spec=spec,forbidden_sha256={p:sha256(p) for p in forbidden}),
           dict(n_jobs=len(jobs),production_ready=False))
    return out


def responses(admission, prompt_paths, validation_prompts, output, forbidden_files):
    from followspec.mixture_targets import validate_registry
    root,cfg=checked_stage(admission);spec=cfg['spec'];registry=read(root/'registry.json');validate_registry(registry)
    if not read(root/'results.json')['ready']:raise ValueError('mixture admission not ready')
    plan,pc=checked_stage(cfg['plan']);metadata=read(plan/'bank_metadata.json')
    paths=read(prompt_paths);magpie={k:lines(p) for k,p in paths.items()}
    for name,path in paths.items():
        c=read(Path(path).parent/'config.json')
        if c['derivative_id']!=name or c['split']!='training' or c['acceptance_only'] or c['pool_sha256'] not in {
                sha256(spec['staging_manifest']),sha256(root/'registry.json')}:
            raise ValueError('Magpie production provenance differs')
        if c.get('revision')!=spec['base_revision'] or c.get('count')!=500:
            raise ValueError('wrong Magpie base pin/count')
        if any(q.get('revision')!=registry[name]['revision'] for q in magpie[name]):
            raise ValueError('wrong Magpie target revision')
    forbidden=sorted(set(spec['forbidden_files']+forbidden_files));blocked=[q for p in forbidden for q in lines(p)]
    validation=lines(validation_prompts);val_hash={prompt_hash(q['prompt']) for q in validation}
    general=lines(spec['general_prompts'])
    if not val_hash <= {prompt_hash(q['prompt']) for q in general}:raise ValueError('validation must be explicitly selected from general20000')
    assignment=allocate_queries(registry,[q for q in general if prompt_hash(q['prompt']) not in val_hash],magpie,validation,
                                seed=spec['seed'],forbidden=blocked)
    out=new_output(output);write_new(out/'assignment.json',assignment)
    cpu=[];jobs=[];runs={}
    for i,(target,queries) in enumerate(sorted(assignment['queries'].items())):
        query_path=out/'queries'/f'target-{i:03}.jsonl';jsonl(query_path,queries)
        entry=metadata.get(target,dict(tokenizer=spec['base_snapshot'],tokenizer_revision=spec['base_revision']))
        origin=['--derivative-id',target,'--pool',spec['staging_manifest'],'--downloads',spec['downloads']]
        if target!='base' and registry[target]['kind']=='mixture':origin=['--derivative-id',target,'--target-registry',str(root/'registry.json')]
        if entry.get('filter_run'):origin+=['--filter-run',entry['filter_run']]
        render=out/'rendered'/f'target-{i:03}'
        common=base_args(spec)+['--tokenizer',entry['tokenizer'],'--tokenizer-revision',entry['tokenizer_revision'],
                                '--prompts',str(query_path)]
        cpu.append([spec['python'],'-m','followspec.render_inputs',*common,*origin,'--output',str(render)])
        pair={}
        for role,generation_target in [('child',target),('base','base')]:
            if target=='base' and role=='child':continue
            dest=out/'runs'/f'target-{i:03}-{role}';pair[role]=str(dest)
            # PO-D uses base vocabulary, but the exact child's already-rendered template.
            generation_common=base_args(spec)+['--tokenizer',spec['base_snapshot'] if role=='base' else entry['tokenizer'],
                '--tokenizer-revision',spec['base_revision'] if role=='base' else entry['tokenizer_revision'], '--prompts',str(query_path)]
            controls=['--prompt-target',target,'--rendered-inputs',str(render/'prompts.jsonl'),
                      '--seed',str(spec['seed']+2000+i),'--max-lora-rank',str(spec['max_lora_rank']),
                      '--allow-a40-production','--output',str(dest),'--forbidden-files',*forbidden]
            source=list(origin)
            source[source.index('--derivative-id')+1]=generation_target
            cmd=['-m','followspec.generate_responses',*generation_common,*source,*controls]
            jobs.append(launcher_job(spec,f'{out.name}-response-{i:03}-{role}','M2',query_path,cmd))
        if target=='base':pair['child']=pair['base']
        runs[target]=pair
    write_new(out/'render_commands.json',cpu);write_new(out/'response_runs.json',runs);jsonl(out/'jobs.jsonl',jobs)
    finish(out,dict(stage='responses',admission=str(root),spec=spec,validation_prompts=str(Path(validation_prompts).resolve()),
                    input_sha256={p:sha256(p) for p in [prompt_paths,validation_prompts,*paths.values(),*forbidden]},
                    forbidden_files=forbidden),dict(counts=assignment['counts'],n_gpu_jobs=len(jobs),n_cpu_render_commands=len(cpu),
                    production_ready=False,next='run render-local, then operator GPU response queue, then assemble'))
    return out


def render_local(stage):
    root,cfg=checked_stage(stage)
    if cfg['stage']!='responses':raise ValueError('response planning stage required')
    # Each completed rendering is validated later by generate_responses; never overwrite.
    for command in read(root/'render_commands.json'):
        output=Path(command[command.index('--output')+1])
        if output.exists():
            from followspec.render_inputs import load_bundle
            query=command[command.index('--prompts')+1];target=command[command.index('--derivative-id')+1]
            load_bundle(output/'prompts.jsonl',lines(query),prompt_target=target,
                        base_tokenizer_sha256=sha256(Path(cfg['spec']['base_snapshot'])/'tokenizer.json'),prompt_sha256=sha256(query))
        else:subprocess.run(command,check=True,cwd=cfg['spec']['code_repo'])


def main():
    p=argparse.ArgumentParser(description=__doc__);sub=p.add_subparsers(dest='stage',required=True)
    a=sub.add_parser('prepare');a.add_argument('--spec',required=True);a.add_argument('--output',required=True)
    a=sub.add_parser('materialize');a.add_argument('--plan',required=True);a.add_argument('--previous');a.add_argument('--output',required=True)
    a=sub.add_parser('retry-filters');a.add_argument('--round-dir',required=True);a.add_argument('--targets',nargs='+',required=True);a.add_argument('--output',required=True)
    a=sub.add_parser('admit');a.add_argument('--round-dir',required=True);a.add_argument('--output',required=True)
    a=sub.add_parser('mixture-prompts');a.add_argument('--admission',required=True);a.add_argument('--output',required=True);a.add_argument('--forbidden-files',nargs='*',default=[])
    a=sub.add_parser('responses')
    for key in ('admission','prompt-paths','validation-prompts','output'):a.add_argument('--'+key,required=True)
    a.add_argument('--forbidden-files',nargs='*',default=[])
    a=sub.add_parser('render-local');a.add_argument('--plan',required=True)
    a=sub.add_parser('assemble');a.add_argument('--plan',required=True);a.add_argument('--output',required=True)
    a=sub.add_parser('finalize');a.add_argument('--assembly',required=True);a.add_argument('--evidence',required=True);a.add_argument('--output',required=True)
    args=vars(p.parse_args());stage=args.pop('stage')
    if stage=='prepare':args['spec_path']=args.pop('spec')
    if stage=='render-local':render_local(args['plan']);return
    if stage=='assemble':
        from followspec.production_assembly import assemble
        out=assemble(**args)
    elif stage=='finalize':
        from followspec.production_assembly import finalize
        out=finalize(**args)
    else:out=globals()[stage.replace('-','_')](**args)
    print(out)


if __name__=='__main__':main()
