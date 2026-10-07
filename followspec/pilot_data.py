"""D-38: derive a sealed, matched exploratory prefix from audited production data."""
import argparse
import copy
import json
from collections import Counter
from pathlib import Path
from atlas.run_cell import sha256, write_new
from followspec.production import ARMS
from followspec.production_pipeline import checked_stage, finish, jsonl, new_output, read


def subset_manifests(manifests, *, max_tokens):
    if set(manifests) != set(ARMS):raise ValueError('all four arms required')
    if type(max_tokens) is not int or max_tokens<=0 or any(max_tokens>=m['token_budget'] for m in manifests.values()):
        raise ValueError('pilot token ceiling must be positive and smaller than full data')
    trains={a:[r for r in m['samples'] if r['split']=='train'] for a,m in manifests.items()}
    ends={}
    for arm,rows in trains.items():
        required={r['child_id'] for r in rows};seen=set();tokens=0;ends[arm]={}
        for i,row in enumerate(rows,1):
            tokens+=row['length']-1;seen.add(row['child_id'])
            if i%8==0 and seen>=required and tokens<=max_tokens:ends[arm][tokens]=i
    common=set.intersection(*(set(v) for v in ends.values()))
    if not common:raise ValueError('no common composition-preserving prefix retains all targets')
    budget=max(common);result=copy.deepcopy(manifests);counts={a:ends[a][budget] for a in ARMS}
    for arm,m in result.items():
        train=trains[arm][:counts[arm]];val=[r for r in m['samples'] if r['split']=='val']
        parents=sum(r['child_id']=='base' for r in train)
        kinds=Counter(r['data_kind'] for r in train if r['child_id']!='base')
        if parents*4!=len(train) or kinds['magpie']!=kinds['general'] or sum(kinds.values())!=len(train)-parents:
            raise ValueError('pilot composition differs from 25% parent / equal child prompt kinds')
        m.update(samples=copy.deepcopy(train)+val,token_budget=budget,
                 assistant_loss_tokens=sum(r['assistant_tokens'] for r in train),parent_sample_share=.25)
    return result,dict(token_budget=budget,counts=counts,selection='largest common complete eight-sample prefix within ceiling; all original targets retained')


def prepare(finalized, output, *, max_tokens, decision_id, expected_tokens, expected_steps):
    from followspec.production_assembly import native_auditor
    from followspec.token_data import OnlineResponseDataset, validate_arm_set
    from followspec.audit_batches import inspect_splits
    from followspec.configs import check_matched
    from followspec.train_eagle3 import resolve_plan
    root,cfg=checked_stage(finalized);ready=read(root/'results.json')
    if not decision_id or cfg['stage']!='finalize' or not all(ready.get(k) is True for k in ('production_ready','data_ready','training_capacity_verified')) or ready.get('blockers'):
        raise ValueError('owner decision and fully audited finalized data required')
    original={a:read(root/a/'manifest.json') for a in ARMS}
    manifests,selection=subset_manifests(original,max_tokens=max_tokens)
    if selection['token_budget']!=expected_tokens:raise ValueError('actual pilot token budget differs from approved expectation')
    lengths={}
    for arm,m in manifests.items():
        if not m.get('data_acceptance_passed') or m.get('acceptance_only'):raise ValueError('audited production source required')
        audit=m['sample_mask_audit'];mask=Path(audit['path'])
        if sha256(mask)!=audit['sha256']:raise ValueError('reviewed masks changed')
        decoded=[json.loads(s) for s in mask.read_text().splitlines()]
        train=[r for r in m['samples'] if r['split']=='train']
        if len(decoded)!=5 or [r['sample_id'] for r in train[:5]]!=[r['sample_id'] for r in decoded]:raise ValueError('reviewed five samples no longer preserved')
        ds=OnlineResponseDataset(m,split='train',bank=None,shift=lambda r:r)
        OnlineResponseDataset(m,split='val',bank=None,shift=lambda r:r)
        for item,view in zip(ds.rows[:5],decoded,strict=True):
            row=ds._view(item)
            if row['input_ids']!=view['input_ids'] or row['loss_mask']!=view['loss_mask'] or row['loss_mask'][1:]!=view['shifted_loss_mask']:
                raise ValueError('reviewed token/mask view changed')
        lengths[arm]=ds.approx_lengths
    policies={m.get('batch_step_policy') for m in manifests.values()}
    if len(policies)!=1:raise ValueError('batch policies differ')
    audit=native_auditor(lengths,batch_step_policy=policies.pop())
    if audit['optimizer_steps']!=expected_steps:raise ValueError('actual pilot optimizer steps differ from approved expectation')
    pilot=dict(decision_id=decision_id,scope='single-seed reduced-budget feasibility',source=str(root),
        source_stage_sha256=sha256(root/'stage_files.json'),max_tokens=max_tokens,token_budget=expected_tokens,optimizer_steps=expected_steps,
        selection=selection,seeds=[0],validation='unchanged full native validation; final checkpoint may be evaluated concurrently')
    out=new_output(output);configs={}
    summaries={a:dict(n_train=sum(r['split']=='train' for r in m['samples']),n_val=sum(r['split']=='val' for r in m['samples']),tokens=m['token_budget'],assistant_tokens=m['assistant_loss_tokens'],parent_share=m['parent_sample_share']) for a,m in manifests.items()}
    for arm,m in manifests.items():
        dest=out/arm;dest.mkdir();original_mask=Path(m['sample_mask_audit']['path'])
        (dest/'decoded_masks.jsonl').write_bytes(original_mask.read_bytes())
        m.update(optimizer_steps=expected_steps,pilot=pilot,sample_mask_audit=dict(path=str(dest/'decoded_masks.jsonl'),sha256=sha256(dest/'decoded_masks.jsonl')))
        c=read(root/arm/'training_config.json');c.update(token_budget=expected_tokens,optimizer_steps=expected_steps,seeds=[0],pilot=pilot,status='resolved_D38_matched_pilot',resolved_data_recipe=dict(decision=decision_id,source_recipe=c.get('resolved_data_recipe'),actual_arm_counts=summaries))
        configs[arm]=c;resolve_plan(c,m,0)
        write_new(dest/'manifest.json',m);write_new(dest/'training_config.json',c)
    matched=validate_arm_set(manifests);splits=inspect_splits(manifests)
    write_new(out/'config_diff.json',check_matched(configs));jsonl(out/'per_batch.jsonl',audit.pop('batches'))
    write_new(out/'batch_audit.json',audit);write_new(out/'selection.json',selection)
    finish(out,dict(stage='finalize',spec=cfg['spec'],pilot=pilot,source=str(root)),
           dict(production_ready=True,data_ready=True,training_capacity_verified=True,training_configs_resolved=True,
                blockers=[],matched=matched,split_audit=splits,pilot=True,validation_preserved=True))
    return out


def main():
    p=argparse.ArgumentParser(description=__doc__)
    for k in ('finalized','output','decision-id'):p.add_argument('--'+k,required=True)
    for k in ('max-tokens','expected-tokens','expected-steps'):p.add_argument('--'+k,type=int,required=True)
    a=p.parse_args();print(prepare(a.finalized,a.output,max_tokens=a.max_tokens,decision_id=a.decision_id,expected_tokens=a.expected_tokens,expected_steps=a.expected_steps))


if __name__=='__main__':main()
