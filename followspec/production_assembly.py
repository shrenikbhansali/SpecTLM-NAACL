"""D-27 paired views, suffix-only matching, mask and native batch audits."""
from collections import Counter
import copy
import json
from pathlib import Path
import random

from atlas.run_cell import sha256,write_new
from atlas.workloads import prompt_hash
from followspec.production import ARMS,match_tails
from followspec.production_pipeline import checked_stage,finish,jsonl,lines,new_output,read


def balanced_order(child, parent, *, seed):
    """Predetermined eight-sample blocks: six children (3+3), two parents.

    Only final incomplete groups are discarded and logged. This makes every
    eligible suffix cut preserve both composition ratios exactly.
    """
    kinds={k:[r|dict(data_role='child') for r in child if r['data_kind']==k] for k in ['magpie','general']}
    if sum(map(len,kinds.values()))!=len(child):raise ValueError('unknown child prompt kind')
    rng=random.Random(seed)
    for rows in kinds.values():rng.shuffle(rows)
    parents=[r|dict(data_role='parent') for r in parent];rng.shuffle(parents)
    n=min(len(kinds['magpie'])//3,len(kinds['general'])//3,len(parents)//2)
    result=[]
    for i in range(n):
        for j in range(3):result.extend([kinds['magpie'][3*i+j],kinds['general'][3*i+j]])
        result.extend(parents[2*i:2*i+2])
    dropped=[r for k in kinds for r in kinds[k][n*3:]]+parents[n*2:]
    return result,[dict(sample_id=r['pair_id'],reason='incomplete final composition block') for r in dropped]


def native_auditor(lengths):
    from followspec.audit_batches import inspect_batches
    from followspec.train_eagle3 import BACKEND
    from speculators.version import git_commit
    from speculators.train.distributed_batch_sampler import MultipackDistributedBatchSamplerV2
    if git_commit!=BACKEND:raise ValueError('native sampler backend differs from pin')
    return inspect_batches(lengths,factory=MultipackDistributedBatchSamplerV2,batch_max_length=8192,seeds=[0,1,2],epochs=1,replicas=1)


def verify_response_plan(root, cfg, assignment, runs):
    from followspec.token_data import response_run
    spec=cfg['spec']
    if set(runs)!=set(assignment['queries']):raise ValueError('generation targets differ from assignment')
    for target,pair in runs.items():
        expected=assignment['queries'][target]
        for role in ('child','base'):
            rows,c,_=response_run(pair[role]);generation=target if role=='child' else 'base'
            if c['acceptance_only'] or c['base_revision']!=spec['base_revision'] or c['derivative_id']!=generation or c['prompt_target']!=target:
                raise ValueError('wrong production response identity')
            for key,value in dict(temperature=.6,top_p=.95,max_new_tokens=512,max_lora_rank=spec['max_lora_rank'],engine_version='0.31.0').items():
                if c[key]!=value:raise ValueError('production generation recipe differs: '+key)
            if len(rows)!=len(expected):raise ValueError('response count differs from assignment')
            for row,query in zip(rows,expected,strict=True):
                if row['sample_id']!=query['prompt_id'] or row['prompt_sha256']!=prompt_hash(query['prompt']):
                    raise ValueError('response query identity differs from assignment')


def assemble(plan, output):
    from followspec.paired_responses import pair_runs
    from followspec.token_data import build_manifest,OnlineResponseDataset,validate_arm_set
    from followspec.audit_batches import inspect_splits
    from transformers import AutoTokenizer
    root,cfg=checked_stage(plan)
    if cfg['stage']!='responses':raise ValueError('response planning stage required')
    spec=cfg['spec'];admission,_=checked_stage(cfg['admission']);registry=read(admission/'registry.json')
    assignment=read(root/'assignment.json');runs=read(root/'response_runs.json')
    for path,digest in cfg['input_sha256'].items():
        if sha256(path)!=digest:raise ValueError('response planning input changed')
    verify_response_plan(root,cfg,assignment,runs)
    pairs={};trims=[];query_meta={}
    for target,pair in runs.items():
        p=pair_runs(pair['child'],pair['base'],child_id=target);pairs[target]=p
        trims.extend(p['trims'])
        for q in assignment['queries'][target]:query_meta[target+'::'+q['prompt_id']]=q
    train_refs={};validation_refs={};dropped={}
    parent_by_id={r['pair_id'].split('::',1)[1]:r for r in pairs['base']['refs']['child']}
    for arm in ['FS','MVD']:
        children=[];validation=[]
        for target,ids in assignment['arm_ids'][arm].items():
            selected=set(ids)
            for r in pairs[target]['refs']['child']:
                q=query_meta[r['pair_id']]; decorated=r|dict(data_kind=q['kind'])
                if q['role']=='validation':validation.append(decorated|dict(split='val'))
                elif q['prompt_id'] in selected:children.append(decorated)
        parent=[parent_by_id[i]|dict(data_kind='general') for i in assignment['parent_ids'][arm]]
        train_refs[arm],dropped[arm]=balanced_order(children,parent,seed=spec['seed']+3000)
        validation+=[r|dict(split='val',data_kind='general') for r in pairs['base']['refs']['child']
                     if query_meta[r['pair_id']]['role']=='validation']
        validation_refs[arm]=validation
    train_refs['PO-T']=train_refs['FS'];validation_refs['PO-T']=validation_refs['FS']
    base_refs={r['pair_id']:r for p in pairs.values() for r in p['refs']['base']}
    for split,refs in [('train',train_refs),('val',validation_refs)]:
        refs['PO-D']=[base_refs[r['pair_id']]|dict(split=split,data_kind=r['data_kind'],
            **({'data_role':r['data_role']} if split=='train' else {})) for r in refs['FS']]
    forbidden={prompt_hash(q['prompt']) for p in cfg['forbidden_files'] for q in lines(p)}
    manifests={};lengths={}
    for arm in ARMS:
        refs=train_refs[arm]+validation_refs[arm]
        m=build_manifest(arm,refs,registry=registry,base_revision=spec['base_revision'],initialization_revision=spec['drafter_revision'],forbidden_hashes=forbidden)
        meta={r['pair_id']:r for r in refs}
        for row in m['samples']:
            r=meta[row['sample_id']];row['data_kind']=r['data_kind'];row['data_role']=r.get('data_role','validation')
        manifests[arm]=m;lengths[arm]=[r['length']-1 for r in m['samples'] if r['split']=='train']
    allowed={}
    for arm in ['FS','MVD']:
        seen=set();allowed[arm]=[];required=set(assignment['arm_ids'][arm])
        for i,row in enumerate(manifests[arm]['samples'][:len(lengths[arm])],1):
            seen.add(row['child_id'])
            if i%8==0 and seen>=required:allowed[arm].append(i)
    out=new_output(output)
    jsonl(out/'paired_trims.jsonl',trims);write_new(out/'composition_tail_drops.json',dropped)
    write_new(out/'pretrim_counts.json',{a:dict(n=len(lengths[a]),tokens=sum(lengths[a])) for a in ARMS})
    try:
        matching=match_tails(lengths,batch_check=native_auditor,allowed_ends=allowed)
        audit=matching.pop('audit');batches=audit.pop('batches')
        jsonl(out/'per_batch.jsonl',batches);write_new(out/'batch_audit.json',audit|dict(passed=True))
        write_new(out/'tail_matching.json',matching)
        all_dropped=[]
        for arm,m in manifests.items():
            train=[r for r in m['samples'] if r['split']=='train'];val=[r for r in m['samples'] if r['split']=='val']
            count=matching['kept'][arm]
            all_dropped += [dict(arm=arm,sample_id=r['sample_id'],source=r['source'],record_index=r['record_index'],
                tokens=r['length']-1,reason='D-27 common-token/native-step suffix match') for r in train[count:]]
            train=train[:count];m['samples']=train+val;m['token_budget']=sum(r['length']-1 for r in train)
            m['assistant_loss_tokens']=sum(r['assistant_tokens'] for r in train);m['parent_sample_share']=sum(r['child_id']=='base' for r in train)/len(train)
            m['optimizer_steps']=audit['optimizer_steps'];m['status']='matched_pending_decoded_review_and_feature_evidence'
            if m['parent_sample_share']!=.25:raise ValueError('final parent share differs')
            if Counter(r['data_kind'] for r in train if r['child_id']!='base')['magpie']*2 != sum(r['child_id']!='base' for r in train):
                raise ValueError('final child composition differs')
            ds=OnlineResponseDataset(m,split='train',bank=None,shift=lambda r:r)
            OnlineResponseDataset(m,split='val',bank=None,shift=lambda r:r)
            if ds.approx_lengths!=lengths[arm][:count]:raise ValueError('dataset lengths differ after matching')
        jsonl(out/'dropped_tail.jsonl',all_dropped)
        matched=validate_arm_set(manifests);splits=inspect_splits(manifests)
        tokenizer=AutoTokenizer.from_pretrained(spec['base_snapshot'],local_files_only=True,trust_remote_code=False)
        summaries={}
        for arm,m in manifests.items():
            dest=out/arm;dest.mkdir()
            ds=OnlineResponseDataset(m,split='train',bank=None,shift=lambda r:r)
            decoded=[]
            for item in ds.rows[:5]:
                row=ds._view(item);start=row['response_start']
                decoded.append(dict(sample_id=item['sample_id'],child_id=item['child_id'],feature_target=item['feature_target'],
                    context=tokenizer.decode(row['input_ids'][:start]),completion=tokenizer.decode(row['input_ids'][start:]),
                    input_ids=row['input_ids'],loss_mask=row['loss_mask'],response_start=start,
                    shifted_loss_mask=row['loss_mask'][1:]))
            if len(decoded)!=5:raise ValueError('five decoded samples per arm required')
            jsonl(dest/'decoded_masks.jsonl',decoded);write_new(dest/'manifest.json',m)
            summaries[arm]=dict(n_train=len(ds),n_val=sum(r['split']=='val' for r in m['samples']),
                tokens=m['token_budget'],assistant_tokens=m['assistant_loss_tokens'],parent_share=m['parent_sample_share'],
                per_child_counts=dict(Counter(r['child_id'] for r in ds.rows)),mask_audit_sha256=sha256(dest/'decoded_masks.jsonl'))
        finish(out,dict(stage='assemble',plan=str(root),spec=spec),dict(matched=matched,split_audit=splits,arms=summaries,
            batch_audit=audit,production_ready=False,data_ready=False,
            next='Inspect all five decoded samples/masks per arm, supply hash-pinned B5 feature evidence to finalize; capacity remains separate'))
    except Exception as exc:
        write_new(out/'failure.json',dict(type=type(exc).__name__,error=str(exc)));raise
    return out


def readiness(evidence, masks):
    blockers=[];proof=evidence.get('feature_acceptance')
    if not proof or not Path(proof).is_file() or sha256(proof)!=evidence.get('feature_acceptance_sha256') or read(proof).get('passed') is not True:
        blockers.append('hash-pinned passing B5 feature acceptance required')
    for arm,path in masks.items():
        if evidence.get('mask_review_sha256',{}).get(arm)!=sha256(path):blockers.append(f'{arm}: decoded/mask review missing or stale')
    capacity=evidence.get('capacity_acceptance');capacity_ok=False
    if capacity and Path(capacity).is_file() and sha256(capacity)==evidence.get('capacity_acceptance_sha256'):
        c=read(capacity);capacity_ok=(c.get('passed') is True and c.get('total_seq_len')==8192 and
            c.get('full_response') is True and c.get('optimizer_steps',0)>=1)
    return dict(data_ready=not blockers,training_capacity_verified=capacity_ok,blockers=blockers,
                capacity_note='B6 bounded64-response overfit does not establish production full-response capacity')


def finalize(assembly, evidence, output):
    from followspec.configs import load_presets,check_matched
    from followspec.token_data import OnlineResponseDataset,validate_arm_set
    from followspec.train_eagle3 import resolve_plan
    root,cfg=checked_stage(assembly);spec=cfg['spec']
    if cfg['stage']!='assemble':raise ValueError('matched assembly required')
    proof=read(evidence);masks={a:root/a/'decoded_masks.jsonl' for a in ARMS};status=readiness(proof,masks)
    out=new_output(output)
    if not status['data_ready']:
        finish(out,dict(stage='finalize',assembly=str(root),evidence_sha256=sha256(evidence),spec=spec),status|dict(production_ready=False))
        return out
    manifests={a:read(root/a/'manifest.json') for a in ARMS}
    validate_arm_set(manifests)
    lengths={a:OnlineResponseDataset(m,split='train',bank=None,shift=lambda r:r).approx_lengths for a,m in manifests.items()}
    actual=native_auditor(lengths);saved=read(root/'batch_audit.json')
    if any(actual[k]!=saved[k] for k in ['token_budget','optimizer_steps','step_counts']):raise ValueError('native batch recheck differs')
    presets=load_presets()
    for arm,m in manifests.items():
        dest=out/arm;dest.mkdir()
        m.update(data_acceptance_passed=True,sample_mask_audit=dict(path=str(masks[arm]),sha256=sha256(masks[arm])),
                 production_assembly=dict(path=str(root),stage_files_sha256=sha256(root/'stage_files.json')),status='data_audited')
        presets[arm].update(initialization_revision=m['initialization_revision'],token_budget=m['token_budget'],
                            optimizer_steps=m['optimizer_steps'],status='resolved_D27_matched_data',
                            resolved_data_recipe=dict(decision='D-27',actual_arm_counts=read(root/'results.json')['arms']))
        write_new(dest/'manifest.json',m);write_new(dest/'training_config.json',presets[arm])
        for seed in [0,1,2]:resolve_plan(presets[arm],m,seed)
    differences=check_matched(presets);write_new(out/'config_diff.json',differences)
    finish(out,dict(stage='finalize',assembly=str(root),evidence_sha256=sha256(evidence),evidence=proof,spec=spec),
           status|dict(production_ready=status['training_capacity_verified'],training_configs_resolved=True,
                       next='Operator verifies data and full-batch capacity, then launches M3 from pinned main'))
    return out
