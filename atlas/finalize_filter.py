"""Apply an explicitly approved repetition criterion to immutable FIX-1 outputs."""
import argparse
import json
import math
from pathlib import Path
import subprocess
from atlas.filter_pool import repetition_coverage,summarize,validate_baseline
from atlas.run_cell import sha256,write_new


def read_rows(path):return [json.loads(line) for line in Path(path).read_text().splitlines() if line.strip()]


def verified_ppl(root):
    rows=read_rows(root/'per_prompt.jsonl')
    if len(rows)!=128 or len({r['prompt_id'] for r in rows})!=128:raise ValueError('missing/duplicate scoring prompts')
    for r in rows:
        if len(r['token_logprobs'])!=r['scored_tokens'] or not r['scored_tokens']:raise ValueError('score count mismatch')
        if any(not math.isfinite(v) or v>1e-5 for v in r['token_logprobs']):raise ValueError('invalid scored logprob')
        if abs(sum(r['token_logprobs'])+r['nll_sum'])>1e-7:raise ValueError('NLL mismatch')
    ppl=math.exp(sum(r['nll_sum'] for r in rows)/sum(r['scored_tokens'] for r in rows))
    if abs(ppl-json.loads((root/'results.json').read_text())['ppl'])>1e-9:raise ValueError('saved PPL mismatch')
    return ppl,rows


def finalize(root,threshold):
    root=Path(root)
    if not 0<threshold<1:raise ValueError('explicit repetition threshold must be between0 and1')
    cfg=json.loads((root/'config.json').read_text());original=json.loads((root/'results.json').read_text())
    if not original['loadable']:raise ValueError('only completed loadable runs can be finalized')
    own,rows=verified_ppl(root);samples=read_rows(root/'samples.jsonl')
    if [r['prompt_id'] for r in samples]!=[r['prompt_id'] for r in rows[:10]]:raise ValueError('generation/scoring prompt mismatch')
    for s in samples:
        if abs(repetition_coverage(s['token_ids'])-s['repetition_coverage'])>1e-12:raise ValueError('saved repetition metric mismatch')
        if s['empty']!=(not s['completion'].strip()):raise ValueError('empty flag mismatch')
        if s['immediate_eos']!=(not s['token_ids'] and s['finish_reason']=='stop'):raise ValueError('EOS flag mismatch')
    base_ppl=own
    if cfg['derivative_id']!='base':
        baseline=Path(cfg['baseline']);bc=json.loads((baseline/'config.json').read_text())
        validate_baseline(cfg,bc)
        if bc['derivative_id']!='base':raise ValueError('baseline is not base')
        for key in ('drafter','drafter_revision','K','max_lora_rank','seed'):
            if cfg[key]!=bc[key]:raise ValueError('baseline engine settings mismatch')
        base_ppl,_=verified_ppl(baseline)
    return original|summarize(rows,samples,base_ppl,threshold)


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--run',required=True);p.add_argument('--repetition-threshold',required=True,type=float);p.add_argument('--decision',required=True);p.add_argument('--output',required=True);a=p.parse_args()
    root=Path(a.run);result=finalize(root,a.repetition_threshold)
    config=dict(source_run=str(root.resolve()),repetition_threshold=a.repetition_threshold,owner_decision=a.decision,
        code_commit=subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip(),
        source_sha256={name:sha256(root/name) for name in ('config.json','results.json','samples.jsonl','per_prompt.jsonl')})
    out=Path(a.output);out.mkdir(parents=True,exist_ok=False)
    write_new(out/'config.json',config);write_new(out/'results.json',result)
    original_ledger=json.loads((root/'ledger_draft.json').read_text())
    write_new(out/'ledger_draft.json',original_ledger|dict(artifacts=str(out.resolve()),
        config_results=dict(config=config,results=result),caveats='Derived threshold decision on immutable source run; no new GPU run. Operator assigns ledger ID.'))
    print(json.dumps(result,indent=2))

if __name__=='__main__':main()
