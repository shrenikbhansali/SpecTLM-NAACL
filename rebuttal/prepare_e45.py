"""CPU-only source preparation and recorded five-example masks."""
import argparse,json,hashlib,random
from pathlib import Path
from followspec.independent_kd import read,write,jsonl,filter_training_queries
from followspec.repair_data import tokenizer_for,render
from atlas.workloads import file_hash
from rebuttal.kd import split_rows

def main():
 p=argparse.ArgumentParser();p.add_argument('--workspace',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args();root=a.workspace;out=a.output;out.mkdir(parents=True,exist_ok=False)
 source=root/'rebuttal/E45_sources_20261124';dataset=json.loads((source/'dataset-complete.json').read_text())
 forbidden=root/'artifacts/P3_repair_20261008_0305/eval/forbidden.jsonl'
 data=[root/'artifacts/P3_D49_20261008_1800/sealed-generic16k/per_prompt.jsonl',root/'artifacts/P3_D50_20261009_0200/E7-sealed16000/per_prompt.jsonl']
 allblocked=read(forbidden)+[{'raw_prompt':r['raw_prompt']} for r in read(data[0])]
 jsonl(out/'reference-forbidden.jsonl',allblocked)
 for t,path in enumerate(data):
  rows=read(path);tr,va=split_rows(rows);target=json.loads((root/f'rebuttal/inputs/target-{t}.json').read_text());tok=tokenizer_for(target['path']);dest=out/f't{t}';dest.mkdir()
  write(dest/'split.json',{'data_sha256':file_hash(path),'seed':0,'train_indices':tr,'validation_indices':va,'n_train':len(tr),'n_validation':len(va)})
  jsonl(dest/'validation256.jsonl',[{'prompt_id':rows[i]['prompt_id'],'prompt':rows[i]['raw_prompt'],'rendered_token_ids':rows[i]['prompt_token_ids']} for i in va])
  jsonl(dest/'smoke16.jsonl',rows[:16])
  for label,inds in [('train',tr[:5]),('validation',va[:5]),('smoke',list(range(5)))]:
   write(dest/(label+'-five.json'),[{'sample_id':rows[i]['sample_id'],'prompt':tok.decode(rows[i]['prompt_token_ids']),'answer':tok.decode(rows[i]['completion_token_ids']),'input_ids':rows[i]['input_ids'],'loss_mask':rows[i]['loss_mask'],'response_start':rows[i]['response_start']} for i in inds])
 # Use first human turn only, never imported ShareGPT answers. Fixed seed0 order.
 raw=json.loads((Path(dataset['path'])/'ShareGPT_V3_unfiltered_cleaned_split.json').read_text());random.Random(0).shuffle(raw)
 candidates=[]
 for r in raw:
  turns=r.get('conversations',[])
  if turns and turns[0].get('from') in ['human','user']:
   text=turns[0]['value']
   if 10<=len(text)<=1000:candidates.append({'prompt':text,'prompt_id':'sharegpt-'+str(r['id'])})
  if len(candidates)==4000:break
 filtered,report=filter_training_queries(candidates,[r.get('raw_prompt',r.get('prompt')) for r in allblocked])
 target=json.loads((root/'rebuttal/inputs/target-0.json').read_text());tok=tokenizer_for(target['path'])
 filtered=[r for r in filtered if len(render(tok,r['prompt']))+512<=2048][:2000]
 if len(filtered)!=2000:raise ValueError('ShareGPT reference shortfall')
 jsonl(out/'reference_queries.jsonl',filtered);write(out/'reference_source.json',dataset|{'selection':'first human turn, fixed shuffle seed0; no source answers','n':len(filtered),'filter_report':report,'forbidden_sha256':file_hash(out/'reference-forbidden.jsonl')})
 print('Prepared reference2000 and two disjoint training/validation splits',flush=True)
if __name__=='__main__':main()
