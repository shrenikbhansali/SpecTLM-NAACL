"""Prepare auditable, length-recorded E3a throughput samples only."""
import argparse
import hashlib
import heapq
import json
from pathlib import Path
import numpy as np
from rebuttal.throughput_data import clip_response


def write(path,value):
    with path.open('x') as f:f.write(json.dumps(value,indent=2,ensure_ascii=False)+'\n')


def jsonl_line(row):
    # Existing consumers use str.splitlines(), which recognizes U+2028/U+0085.
    # Escape Unicode in the container; decoded prompt contents stay identical.
    return json.dumps(row,ensure_ascii=True)+'\n'


def seal(out,rows,tokenizer,provenance):
    out.mkdir(parents=True,exist_ok=False);trimmed=[];cuts=[]
    for r in rows:
        rr,cut=clip_response(r);trimmed.append(rr);cuts.append(cut)
    data=out/'per_prompt.jsonl'
    with data.open('x') as f:
        for r in trimmed:f.write(jsonl_line(r))
    original=np.array([c['original_tokens'] for c in cuts]);kept=np.array([c['kept_tokens'] for c in cuts])
    manifest=provenance|{'n':len(rows),'data_sha256':hashlib.sha256(data.read_bytes()).hexdigest(),
        'length_policy':'full prompt, response clipped to fit 2049 input IDs (2048 shifted training tokens); no regenerated native answers',
        'original_mean_input_tokens':float(original.mean()),'kept_mean_input_tokens':float(kept.mean()),
        'original_mean_answer_tokens':float(np.mean([len(r['completion_token_ids']) for r in rows])),
        'kept_mean_answer_tokens':float(np.mean([len(r['completion_token_ids']) for r in trimmed])),
        'truncated_examples':sum(c['removed_answer_tokens']>0 for c in cuts),'removed_answer_tokens':sum(c['removed_answer_tokens'] for c in cuts)}
    write(out/'manifest.json',manifest);write(out/'truncation.json',cuts)
    write(out/'five_decoded_masks.json',[{'sample_id':r['sample_id'],'prompt':tokenizer.decode(r['prompt_token_ids']),
        'answer':tokenizer.decode(r['completion_token_ids']),'prompt_tokens':r['response_start'],
        'answer_tokens':len(r['completion_token_ids']),'loss_mask_runs':[[False,r['response_start']],[True,len(r['completion_token_ids'])]],
        'mask_contiguous':r['loss_mask']==[False]*r['response_start']+[True]*len(r['completion_token_ids']),
        'single_BOS':r['input_ids'].count(tokenizer.bos_token_id)==1,'truncation':cuts[i]} for i,r in enumerate(trimmed[:5])])
    print(json.dumps(manifest,indent=2));return manifest


def main():
    from followspec.independent_kd import filter_training_queries
    from followspec.repair_data import tokenizer_for,render
    from followspec.family_repair import prompt_hash
    p=argparse.ArgumentParser();p.add_argument('--workspace',type=Path,required=True);p.add_argument('--output',type=Path,required=True)
    p.add_argument('--generated',type=Path);p.add_argument('--native',action='store_true');a=p.parse_args()
    if bool(a.generated)==a.native:raise ValueError('choose generated or native')
    target=json.loads((a.workspace/'rebuttal/inputs/target-0.json').read_text());tok=tokenizer_for(target['path'])
    if a.generated:
        result=json.loads((a.generated/'results.json').read_text());data=a.generated/'per_prompt.jsonl'
        if result['n']!=2000 or result['per_prompt_sha256']!=hashlib.sha256(data.read_bytes()).hexdigest():raise ValueError('incomplete generation')
        rows=[json.loads(s) for s in data.read_text().splitlines()]
        seal(a.output,rows,tok,{'mode':'E3a-regenerated-throughput','source':str(a.generated),'source_sha256':result['per_prompt_sha256'],'measured_generation_s':result['wall_s']});return
    import pyarrow.parquet as pq
    source=json.loads((a.workspace/'rebuttal/source_stage_20261125_2020/openthoughts-complete.json').read_text());pool=[];count=0
    for f in sorted((Path(source['path'])/'metadata').glob('*.parquet')):
        for batch in pq.ParquetFile(f).iter_batches(columns=['problem','deepseek_reasoning','deepseek_solution','domain'],batch_size=512):
            for r in batch.to_pylist():
                if r['domain']!='math' or not r['problem'] or not r['deepseek_reasoning'] or not r['deepseek_solution']:continue
                count+=1;text=r['problem'];digest=hashlib.sha256(('E3a-native-seed0\0'+text).encode()).hexdigest();item=(-int(digest,16),count,r)
                if len(pool)<5000:heapq.heappush(pool,item)
                elif item>pool[0]:heapq.heapreplace(pool,item)
    candidates=[{'prompt':r['problem'],'prompt_id':'E3a-native-'+hashlib.sha256(r['problem'].encode()).hexdigest(),'native_reasoning':r['deepseek_reasoning'],'native_solution':r['deepseek_solution']} for _,_,r in sorted(pool,reverse=True)]
    forbidden=a.workspace/'artifacts/P3_repair_20261008_0305/eval/forbidden.jsonl'
    forbidden_rows=[json.loads(s) for s in forbidden.read_text().splitlines()]
    candidates,report=filter_training_queries(candidates,[r.get('raw_prompt',r.get('prompt')) for r in forbidden_rows]);rows=[]
    for r in candidates:
        prompt=render(tok,r['prompt'])
        if len(prompt)>1536:continue
        answer=tok.encode(r['native_reasoning']+'\n</think>\n'+r['native_solution'],add_special_tokens=False)
        if not answer:continue
        rows.append({'sample_id':r['prompt_id'],'prompt_id':r['prompt_id'],'raw_prompt':r['prompt'],'prompt_sha256':prompt_hash(r['prompt']),
                     'prompt_token_ids':prompt,'completion_token_ids':answer,'input_ids':prompt+answer,'response_start':len(prompt),
                     'loss_mask':[False]*len(prompt)+[True]*len(answer),'generation_target':'deepseek-ai/DeepSeek-R1','generation_revision':None,
                     'response_dataset':source['repo'],'response_dataset_revision':source['revision']})
        if len(rows)==2000:break
    if len(rows)!=2000:raise ValueError('native math sample shortfall')
    seal(a.output,rows,tok,{'mode':'E3a-native-throughput','dataset_id':source['repo'],'dataset_revision':source['revision'],'license':source['license'],
         'response_model':'deepseek-ai/DeepSeek-R1','response_model_revision':None,'response_model_revision_note':'not specified by dataset; dataset revision pins exact native text',
         'supervision_target':target,'source_math_count':count,'selection':'2000 of lowest seed0 prompt hashes after dedup and whole-prompt<=1536 filter',
         'format':'native metadata reasoning and solution, joined with </think> boundary; target default template supplies initial <think>; no answer regeneration',
         'forbidden_sha256':hashlib.sha256(forbidden.read_bytes()).hexdigest(),'deduplication':report})


if __name__=='__main__':main()
