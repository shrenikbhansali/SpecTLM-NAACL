"""Prepare exact saved generation tokens for paired offline covariates."""
import argparse
import json
from pathlib import Path
from atlas.run_cell import sha256,write_new


def read(path):return [json.loads(line) for line in Path(path).read_text().splitlines() if line.strip()]


def sequence(prompt_id,context,answer):
    if not context or not answer or any(type(i) is not int or i<0 for i in context+answer):raise ValueError('invalid/empty sequence')
    return dict(prompt_id=prompt_id,input_ids=context+answer,response_start=len(context),assistant_mask=[0]*len(context)+[1]*len(answer))


def from_cell(root,smoke,count):
    root=Path(root);cfg=json.loads((root/'config.json').read_text())
    if (root/'failure.json').exists() or not (root/'results.json').exists():raise ValueError('cell incomplete')
    if cfg['engine_version']!='0.31.0':raise ValueError('generation engine differs from pin')
    if sha256(cfg['prompts'])!=cfg['prompt_sha256']:raise ValueError('prompt file changed')
    prompts={r['prompt_id']:r for r in read(cfg['prompts'])};records=read(root/'per_prompt.jsonl')
    if len(records)!=json.loads((root/'results.json').read_text())['n'] or {r['prompt_id'] for r in records}!=set(prompts):raise ValueError('source prompt mismatch')
    if any('prompt_token_ids' not in r for r in records):raise ValueError('need B2 --capture-prompt-token-ids; never retokenize and guess prompt_token_ids')
    if not smoke and (len(records)!=64 or any(r.get('acceptance_only') or r.get('split')!='evaluation' or not r.get('derivative_id') for r in prompts.values())):
        raise ValueError('production needs64 derivative-own evaluation prompts')
    derivative_ids={r['derivative_id'] for r in prompts.values() if r.get('derivative_id')}
    if len(derivative_ids)!=1:raise ValueError('need one workload derivative identity')
    revision=cfg['adapter_revision'] if cfg.get('adapter') else cfg['target_revision']
    if any(r.get('revision')!=revision for r in prompts.values()):
        raise ValueError('generation revision must match workload derivative revision; use A10, not A00')
    config=dict(generation_engine=cfg['engine_version'],K=cfg['K'],prompt_sha256=cfg['prompt_sha256'],
        source_run_id=root.name,source_config_sha256=sha256(root/'config.json'),source_records_sha256=sha256(root/'per_prompt.jsonl'),
        derivative_id=next(iter(derivative_ids)),derivative_revision=revision,
        workload='own',acceptance_only=smoke,template_changed=None)
    selected=records[:count] if smoke else records
    return [sequence(r['prompt_id'],r['prompt_token_ids'],r['completion_token_ids']) for r in selected],config


def from_filter(root,count):
    root=Path(root);cfg=json.loads((root/'config.json').read_text());ref=Path(cfg['reference'])
    target=json.loads((root/'target_provenance.json').read_text())
    if cfg['engine_version']!='0.31.0' or sha256(ref)!=cfg['reference_sha256']:raise ValueError('filter provenance mismatch')
    refs={r['prompt_id']:r for r in read(ref)};samples=read(root/'samples.jsonl')[:count]
    result=[sequence(r['prompt_id'],refs[r['prompt_id']]['generation_input_ids'],r['token_ids']) for r in samples]
    config=dict(generation_engine=cfg['engine_version'],K=cfg['K'],prompt_sha256=cfg['reference_config']['prompt_sha256'],
        source_run_id=root.name,source_config_sha256=sha256(root/'config.json'),source_records_sha256=sha256(root/'samples.jsonl'),
        derivative_id=cfg['derivative_id'],derivative_revision=target['revision'],
        workload='general acceptance only',acceptance_only=True,template_changed=False)
    return result,config


def main():
    p=argparse.ArgumentParser(description=__doc__);g=p.add_mutually_exclusive_group(required=True);g.add_argument('--cell');g.add_argument('--filter-run')
    p.add_argument('--acceptance-smoke',action='store_true');p.add_argument('--count',type=int,default=5);p.add_argument('--output',required=True);a=p.parse_args()
    if not 1<=a.count<=10:raise ValueError('smoke count1–10')
    if a.filter_run and not a.acceptance_smoke:raise ValueError('FIX-1 reuse is acceptance-only')
    rows,cfg=from_filter(a.filter_run,a.count) if a.filter_run else from_cell(a.cell,a.acceptance_smoke,a.count)
    out=Path(a.output);out.mkdir(parents=True,exist_ok=False)
    with (out/'sequences.jsonl').open('x') as f:
        for row in rows:f.write(json.dumps(row)+'\n')
    write_new(out/'config.json',cfg|dict(n=len(rows),sequences_sha256=sha256(out/'sequences.jsonl')))

if __name__=='__main__':main()
