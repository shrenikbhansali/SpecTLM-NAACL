"""Apply recorded D-20 to preserved B3 evidence without changing old artifacts."""
import argparse
import json
import math
from pathlib import Path
import subprocess
from atlas.run_cell import sha256,write_new

CASES={'onehot_0','onehot_1','onehot_2','zero','random_0','random_1','random_2'}


def check_numeric(result,rows):
    if result['n']!=16 or len(rows)!=7*16:raise ValueError('seven complete16-prompt comparisons required')
    summary={r['case']:r for r in result['comparisons']}
    if len(result['comparisons'])!=7 or set(summary)!=CASES:raise ValueError('wrong comparison cases')
    seen=set();ids={};reports=[]
    for row in rows:
        key=(row['case'],row['prompt_id'])
        if key in seen or row['case'] not in CASES or row['dtype']!='torch.float32':raise ValueError('duplicate or wrong comparison row')
        seen.add(key);ids.setdefault(row['case'],set()).add(row['prompt_id'])
        if not math.isfinite(row['max_absolute_difference']) or row['max_absolute_difference']<0:raise ValueError('invalid numeric error')
    if any(len(x)!=16 or x!=next(iter(ids.values())) for x in ids.values()):raise ValueError('different16-prompt sets')
    for name in sorted(CASES):
        maximum=max(r['max_absolute_difference'] for r in rows if r['case']==name)
        if summary[name]['dtype']!='torch.float32' or maximum!=summary[name]['max_absolute_difference']:raise ValueError('summary differs from per-prompt records')
        reports.append(dict(case=name,max_absolute_difference=maximum,passed=maximum<1e-4))
    return dict(passed=all(r['passed'] for r in reports),n_prompts=16,n_cases=7,strict_absolute_threshold=1e-4,
        max_absolute_difference=max(r['max_absolute_difference'] for r in reports),cases=reports)


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--evidence-root',required=True);p.add_argument('--output',required=True);a=p.parse_args()
    root=Path(a.evidence_root);evidence={}
    def read(relative,lines=False):
        path=root/relative;evidence[str(path.resolve())]=sha256(path)
        return [json.loads(s) for s in path.read_text().splitlines()] if lines else json.loads(path.read_text())
    fp=read('rounding_fp32_full/results.json');records=read('rounding_fp32_full/per_prompt.jsonl',True)
    fcfg=read('rounding_fp32_full/config.json');bf=read('logits/results.json');bcfg=read('logits/config.json')
    bfrows=read('logits/per_prompt.jsonl',True);old_failure=read('logits/failure.json')
    v=read('vllm/results.json');vcfg=read('vllm/config.json');vrows=read('vllm/per_prompt.jsonl',True)
    numeric=check_numeric(fp,records)
    prompt_file=Path(vcfg['prompts']);prompt_ids={r['prompt_id'] for r in [json.loads(s) for s in prompt_file.read_text().splitlines()]}
    if len(prompt_ids)!=16 or {r['prompt_id'] for r in records}!=prompt_ids:raise ValueError('wrong diagnostic prompts')
    if len({c['prompt_sha256'] for c in [fcfg,bcfg,vcfg]})!=1 or sha256(prompt_file)!=fcfg['prompt_sha256']:raise ValueError('prompt provenance differs')
    if len({c['revision'] for c in [fcfg,bcfg,vcfg]})!=1:raise ValueError('base pin differs')
    if fcfg['source_launch']['args'][fcfg['source_launch']['args'].index('--adapters')+1:fcfg['source_launch']['args'].index('--adapters')+4]!=vcfg['adapters'] or bcfg['adapters']!=vcfg['adapters']:
        raise ValueError('source adapters differ')
    for folder,proof in zip(vcfg['adapters'],vcfg['adapters_sha256'],strict=True):
        for file,key in [('adapter_config.json','config'),('adapter_model.safetensors','weights')]:
            path=Path(folder)/file
            if sha256(path)!=proof[key]:raise ValueError('source adapter changed')
            evidence[str(path.resolve())]=proof[key]
    if bcfg['adapters_sha256']!=vcfg['adapters_sha256']:raise ValueError('bf16 and native adapter hashes differ')
    native=(v['passed'] and v['n']==16 and v['engine_version']=='0.31.0' and len(vrows)==16 and
        {r['prompt_id'] for r in vrows}==prompt_ids and all(r['token_ids'] for r in vrows) and
        sum(len(r['token_ids']) for r in vrows)==v['generated_tokens'])
    exact=[r for r in bfrows if r['case'] in {'onehot_0','onehot_1','onehot_2','zero'}]
    exact_pass=len(exact)==64 and len({(r['case'],r['prompt_id']) for r in exact})==64 and all(r['max_absolute_difference']==0 for r in exact)
    result=dict(passed=numeric['passed'] and bool(native) and exact_pass,decision='D-20',numeric=numeric,
        original_bf16_onehot_and_zero_exact=exact_pass,vllm_multi_lora_passed=bool(native),
        original_bf16_acceptance_passed=bf['passed'],original_bf16_failure=old_failure,
        original_bf16_random_max_errors=[r['max_absolute_difference'] for r in bf['cases'] if r['kind']=='random'],
        caveat='D-20 applies a new owner-delegated validation rule after the original bf16 failure. The earlier artifacts remain unchanged; fp32 onehot diagnostics compare source adapters to dense references, and bf16 onehot checks separately prove concatenation equality.',
        uncertainty='Deterministic numerical equality/tolerance checks on16 fixed prompts; no performance inference')
    out=Path(a.output);out.mkdir(parents=True,exist_ok=False)
    cfg=dict(decision='MASTER §13 D-20, recorded2026-10-06',evidence_sha256=evidence,code_commit=subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip(),
        producer_sha256=sha256(__file__),base_revision=vcfg['revision'],prompt_sha256=fcfg['prompt_sha256'],engine_version='0.31.0',seed=0,K=None)
    write_new(out/'config.json',cfg);write_new(out/'results.json',result)
    with (out/'per_prompt.jsonl').open('x') as f:
        for row in records:f.write(json.dumps(row|dict(D20_passed=row['max_absolute_difference']<1e-4))+'\n')
    write_new(out/'ledger_draft.json',dict(id='EXP-ATL-UNASSIGNED',title=out.name,landed=__import__('datetime').date.today().isoformat(),status='pilot',
        what_why='Evaluate B3 under the explicitly recorded D-20 rule',new='Recomputed strict fp32 gate and source-provenance audit',artifacts=str(out.resolve()),
        config_results=dict(config=cfg,results=result),caveats=result['caveat']))
    print(json.dumps(result,indent=2))
    if not result['passed']:raise SystemExit(1)


if __name__=='__main__':main()
