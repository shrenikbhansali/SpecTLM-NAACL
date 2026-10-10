"""Describe all admitted responses, including capped/repetitive outputs; no filtering."""
import argparse,json
from collections import Counter
from pathlib import Path
import numpy as np
from atlas.filter_pool import repetition_coverage
from ops.track_t import lines,write,sha


def describe(rows):
    sizes=np.array([len(r['completion_token_ids']) for r in rows]);coverage=[repetition_coverage(r['completion_token_ids']) for r in rows]
    return dict(n=len(rows),sequence_tokens=sum(len(r['input_ids']) for r in rows),answer_tokens=int(sizes.sum()),mean_answer_tokens=float(sizes.mean()),answer_length_quantiles=dict(zip(['min','p25','median','p75','p90','max'],np.quantile(sizes,[0,.25,.5,.75,.9,1]).tolist())),finish_reasons=dict(Counter(r['finish_reason'] for r in rows)),empty=int((sizes==0).sum()),at_most_one_token=int((sizes<=1).sum()),repeated_4gram_over_half=sum(x>.5 for x in coverage),repetition_metric='maximum union coverage of any repeated4gram; strictly greater than0.5; reporting only, no filtering')


def analyze(stage,out):
    out.mkdir(exist_ok=False);plan=json.loads((stage/'plan.json').read_text());records=[];pending=[]
    for t in [0,1,2]:
        selected=[r for r in plan if r['target']==t]
        if any(not (Path(r['run_dir'])/'results.json').exists() for r in selected):pending.append(t);continue
        rows=[];wall=0;paths=[]
        for r in selected:
            p=Path(r['run_dir']);result=json.loads((p/'results.json').read_text());source=p/'per_prompt.jsonl';assert sha(source)==result['per_prompt_sha256'];batch=lines(source);assert len(batch)==result['n'];rows+=batch;wall+=result['wall_s'];paths.append(dict(path=str(source),sha256=sha(source)))
        record=dict(target=t,new_responses=describe(rows),generation_gpu_hours=wall/3600,sources=paths)
        if t<2:
            chosen={r['prompt_sha256'] for r in rows};short=lines(Path(selected[0]['source']));paired=[r for r in short if r['prompt_sha256'] in chosen];assert len(paired)==len(rows)
            record['paired_short_responses']=describe(paired);record['all_short_responses']=describe(short)
        records.append(record)
    write(out/'results.json',dict(status='pilot',records=records,pending=pending))
    text=['# REV2 response-data statistics — pilot','', 'All target responses retained. Generation GPU-hours sum completed shard wall clocks including engine initialization. The repeated4gram diagnostic reports degeneration without changing admission.','', '| Target | Data | n | Answer tokens | Mean length | Capped | Repeated4gram >50% | Generation GPUh |','|---|---|---:|---:|---:|---:|---:|---:|']
    for r in records:
        for key in ['new_responses','paired_short_responses','all_short_responses']:
            if key not in r:continue
            d=r[key];cost=f"{r['generation_gpu_hours']:.3f}" if key=='new_responses' else 'previously recorded';text.append(f"|{r['target']}|{key}|{d['n']}|{d['answer_tokens']}|{d['mean_answer_tokens']:.1f}|{d['finish_reasons'].get('length',0)}|{d['repeated_4gram_over_half']}|{cost}|")
    (out/'report.md').write_text('\n'.join(text)+'\n')
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--stage',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args();analyze(a.stage,a.output)
