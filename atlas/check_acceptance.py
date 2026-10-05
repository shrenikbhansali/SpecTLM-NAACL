"""Read real B2 artifacts and report §7 acceptance; never launches inference."""
import argparse
import json
from pathlib import Path
from atlas.run_cell import compare_golden,load_prompts,sha256


def read_cell(path):
    root=Path(path)
    if (root/'failure.json').exists():raise ValueError(f'failed cell: {root}')
    config=json.loads((root/'config.json').read_text())
    result=json.loads((root/'results.json').read_text())
    rows=[json.loads(x) for x in (root/'per_prompt.jsonl').read_text().splitlines()]
    if len(rows)!=128 or result['n']!=128:raise ValueError('golden cell must have 128 records')
    if config.get('dry_run') or result.get('synthetic'):raise ValueError('synthetic data is not acceptance evidence')
    if result['engine_version']!=config['engine_version']:raise ValueError('engine mismatch')
    if abs(sum(r['acceptance_length'] for r in rows)/128-result['macro_acceptance_length'])>1e-12:
        raise ValueError('aggregate not derivable from records')
    return dict(config=config,results=result)


def main():
    p=argparse.ArgumentParser(description=__doc__)
    for key in ('base','repeat','lora','merged','eagle','dflash'):p.add_argument('--'+key,required=True)
    p.add_argument('--golden-prompts',required=True);p.add_argument('--report',required=True)
    a=p.parse_args();cells={key:read_cell(getattr(a,key)) for key in ('base','repeat','lora','merged','eagle','dflash')}
    if len(load_prompts(a.golden_prompts))!=128:raise ValueError('wrong golden prompt count')
    for cell in cells.values():
        if cell['config']['prompt_sha256']!=sha256(a.golden_prompts):raise ValueError('golden prompt hash mismatch')
        if cell['config']['engine_version']!=cells['base']['config']['engine_version']:raise ValueError('mixed engines')
    report=compare_golden(*(cells[k] for k in ('base','repeat','lora','merged')))
    for method in ('eagle','dflash'):
        if cells[method]['config']['method']!=method:raise ValueError('wrong drafter method')
        if cells[method]['results']['generation_wall_s']<=0:raise ValueError('missing timing')
    report['timings']={k:v['results'] for k,v in cells.items()}
    report['automated_checks_pass']=all(report[k] for k in ('child_negative_shift','lora_merged_within_repeat_difference'))
    report['operator_review_required']=['rough child drift size','repeat discrepancy if outside noise floor','source identity of LoRA and merged child']
    with Path(a.report).open('x') as f:json.dump(report,f,indent=2);f.write('\n')
    if not report['automated_checks_pass']:raise SystemExit(1)

if __name__=='__main__':main()
