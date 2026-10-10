"""Seal completed D54 shards without training until five decoded samples are audited."""
import argparse,json
from pathlib import Path
from followspec.independent_kd import jsonl
from followspec.repair_data import tokenizer_for
from followspec.family_repair import validate_rows
from atlas.workloads import prompt_hash
from ops.track_t import WS,lines,write,sha

def mixture(short,long):
    old={r['prompt_sha256']:r for r in short}
    if len(old)!=len(short):raise ValueError('short-source duplicate')
    for r in long:
        if r['prompt_sha256'] not in old or old[r['prompt_sha256']]['prompt_token_ids']!=r['prompt_token_ids']:raise ValueError('long response not paired to original short prompt')
    return [r|dict(original_sample_id=r['sample_id'],sample_id=branch+':'+r['sample_id'],response_branch=branch) for branch,rows in [('short512',short),('long2048',long)] for r in rows]

def seal(stage,out,t):
    plan=[r for r in json.loads((stage/'plan.json').read_text()) if r['target']==t];expected=4000 if t<2 else 16000
    for r in plan:
        root=Path(r['run_dir'])
        if not (root/'results.json').exists():raise ValueError('unfinished shard '+r['name'])
        result=json.loads((root/'results.json').read_text());assert result['n']==r['n'] and result['per_prompt_sha256']==sha(root/'per_prompt.jsonl')
    out.mkdir(exist_ok=False);source=Path(plan[0]['source']);original=lines(source);selected=original[:expected]
    response={};sources=[]
    for r in plan:
        p=Path(r['run_dir'])/'per_prompt.jsonl';rows=lines(p)
        for q in rows:
            if q['prompt_sha256'] in response:raise ValueError('shard duplicate')
            response[q['prompt_sha256']]=q
        sources.append(dict(path=str(p),sha256=sha(p),n=len(rows)))
    assert len(response)==expected and set(response)=={r['prompt_sha256'] for r in selected}
    ordered=[response[r['prompt_sha256']] for r in selected]
    row=json.loads((WS/f'artifacts/P3_D48_20261008_1455/target-{t}.json').read_text());tok=tokenizer_for(row['path'])
    forbidden={prompt_hash(r.get('raw_prompt',r.get('prompt'))) for r in lines(WS/'artifacts/P3_repair_20261008_0305/eval/forbidden.jsonl')}
    datasets={'long4k' if t<2 else 'generic16k':ordered}
    if t<2:datasets['mixed20k']=mixture(original,ordered)
    for label,rows in datasets.items():
        dest=out/label;dest.mkdir();validate_rows(rows,forbidden,4097 if t<2 else 2049,allow_response_pairs=label=='mixed20k')
        data=dest/'per_prompt.jsonl';jsonl(data,rows)
        inspect=rows[:5] if label!='mixed20k' else rows[:5]+rows[len(original):len(original)+5]
        decoded=[dict(sample_id=r['sample_id'],branch=r.get('response_branch'),prompt=tok.decode(r['prompt_token_ids']),answer=tok.decode(r['completion_token_ids']),input_ids=r['input_ids'],response_start=r['response_start'],loss_mask=r['loss_mask'],mask_valid=r['loss_mask']==[False]*r['response_start']+[True]*len(r['completion_token_ids'])) for r in inspect]
        write(dest/'five_decoded_masks.json',decoded)
        write(dest/'seal.json',dict(target=row,n=len(rows),data_sha256=sha(data),sources=sources,short_source=str(source) if label=='mixed20k' else None,original_order_source=str(source),original_order_sha256=sha(source),five_decoded_sha256=sha(dest/'five_decoded_masks.json'),status='pending_manual_audit',answer_tokens=sum(len(r['completion_token_ids']) for r in rows),sequence_tokens=sum(len(r['input_ids']) for r in rows)))
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--stage',type=Path,required=True);p.add_argument('--output',type=Path,required=True);p.add_argument('--target',type=int,required=True);a=p.parse_args();seal(a.stage,a.output,a.target)
