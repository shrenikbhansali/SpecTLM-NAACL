"""Audit matched B9 acceptance cells and preserve exact generated sequences."""
import argparse
import json
from pathlib import Path
from atlas.run_cell import sha256,write_new
from atlas.prepare_covariates import sequence,read

MATCHED=('target','target_revision','drafter','drafter_revision','method','K','seed','prompt_sha256',
         'max_new_tokens','batch_size','max_lora_rank','enable_lora','engine_version')


def prepare_pair(root,pair):
    root=Path(root);configs={};records={};results={}
    for arm in ['base','child']:
        p=root/arm
        if (p/'failure.json').exists():raise ValueError('failed source cell')
        configs[arm]=json.loads((p/'config.json').read_text());results[arm]=json.loads((p/'results.json').read_text())
        records[arm]=read(p/'per_prompt.jsonl')
        if not 1<=len(records[arm])<=5 or len(records[arm])!=results[arm]['n']:raise ValueError('bounded source counts differ')
        c=configs[arm]
        if c['engine_version']!='0.31.0' or sha256(c['prompts'])!=c['prompt_sha256']:raise ValueError('source engine or prompts changed')
    b,c=configs['base'],configs['child']
    if any(b[k]!=c[k] for k in MATCHED) or not b['enable_lora']:raise ValueError('unmatched engine settings')
    if results['base']['gpu_type']!=results['child']['gpu_type'] or 'A40' not in results['base']['gpu_type']:raise ValueError('unmatched hardware')
    if b['adapter'] or c['adapter_revision']!=pair['revision'] or Path(c['adapter']).resolve()!=Path(pair['adapter']).resolve():
        raise ValueError('wrong generating target')
    proof=Path(pair['filter_run'])
    if json.loads((proof/'config.json').read_text())['derivative_id']!=pair['derivative_id'] or json.loads((proof/'target_provenance.json').read_text())['revision']!=pair['revision'] or not json.loads((proof/'results.json').read_text())['accepted']:
        raise ValueError('wrong or rejected target identity')
    prompts={r['prompt_id']:r for r in read(c['prompts'])}
    indexed={arm:{r['prompt_id']:r for r in rows} for arm,rows in records.items()}
    if any(len(indexed[arm])!=len(records[arm]) or indexed[arm].keys()!=prompts.keys() for arm in indexed):raise ValueError('source prompt IDs differ')
    rows=[]
    for id,prompt in prompts.items():
        b_rec=indexed['base'][id];c_rec=indexed['child'][id]
        if b_rec['prompt_token_ids']!=c_rec['prompt_token_ids'] or c_rec['prompt_token_ids']!=prompt['rendered_token_ids']:
            raise ValueError('source exact contexts differ')
        rows.append(sequence(id,c_rec['prompt_token_ids'],c_rec['completion_token_ids']))
    # The fixed reference's original metadata does not identify the generating
    # child. Establish that identity from actual B2 adapter pins and A2 proof.
    cfg=dict(generation_engine=c['engine_version'],K=c['K'],prompt_sha256=c['prompt_sha256'],
        source_run_id=str((root/'child').resolve()),source_config_sha256=sha256(root/'child/config.json'),
        source_records_sha256=sha256(root/'child/per_prompt.jsonl'),derivative_id=pair['derivative_id'],
        derivative_revision=pair['revision'],workload='fixed general acceptance reference',acceptance_only=True,
        template_changed=None,base_cell=str((root/'base').resolve()),base_config_sha256=sha256(root/'base/config.json'),
        filter_results_sha256=sha256(proof/'results.json'))
    return rows,cfg


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--plan',required=True);p.add_argument('--index',type=int,required=True);p.add_argument('--output',required=True)
    a=p.parse_args();plan_path=Path(a.plan);plan=json.loads(plan_path.read_text());pair=plan['pairs'][a.index]
    if pair['index']!=a.index:raise ValueError('pair index mismatch')
    rows,cfg=prepare_pair(plan_path.parent/f'd{a.index:02d}',pair)
    out=Path(a.output);out.mkdir(parents=True,exist_ok=False)
    with (out/'sequences.jsonl').open('x') as f:
        for r in rows:f.write(json.dumps(r)+'\n')
    write_new(out/'config.json',cfg|dict(n=len(rows),sequences_sha256=sha256(out/'sequences.jsonl'),acceptance_plan_sha256=sha256(plan_path)))


if __name__=='__main__':main()
