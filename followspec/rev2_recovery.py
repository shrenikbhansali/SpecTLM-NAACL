"""D54 explicit failed-E9 recovery; preserve data, artifacts and failed attempts."""
import argparse,copy,json
from pathlib import Path
from followspec.review_followup import parts,replace,publish
from ops.track_t import WS,DISPATCH,lines,write


def active_attempts(rows,finished):
    active=dict(rows);evidence=[]
    for name,row in rows.items():
        if row.get('kind')!='train' or not row.get('replaces_job'):continue
        prior=row['replaces_job']
        if prior not in rows or finished.get(prior) in [None,'0']:raise ValueError('replacement needs a recorded failed attempt')
        old=rows[prior]
        if row['experiment']!='E9' or any(row.get(k)!=old.get(k) for k in ['experiment','target','arm','seed','data_label','kind']):raise ValueError('retry changes experiment scope')
        if prior not in active:raise ValueError('multiple replacements for one attempt')
        active.pop(prior);evidence.append(dict(failed_job=prior,exit=finished[prior],replacement=name,failed_artifacts=old['run_dir'] if 'run_dir' in old else None))
    return active,evidence


def retry_job(source,record,stage,code):
    j=copy.deepcopy(source);name=record['name']+'-pack2304';out=stage/name;o,i=parts(j)
    for flag,value in [('--tag',name),('--code-repo',code),('--note','D54 E9 OOM recovery: packing2304 instead of4096; all complete sequences retained; native objective/data/seed unchanged; one epoch')]:replace(o,flag,value)
    for flag,value in [('--output',out),('--batch-tokens',2304),('--shared-export-root',stage/'shared-shards')]:replace(i,flag,value)
    j.update(name=name,args=o+['--']+i)
    return j,record|dict(name=name,run_dir=str(out),replaces_job=record['name'],recovery='first-backward OOM; authorized packing adjustment to2304')


def prepare(stage,source_stage,code):
    if stage.exists():raise ValueError('immutable retry stage already exists')
    events=lines(WS/'artifacts/M2_D28_20261006/response_queue.log');launched={};failed={}
    for e in events:
        if e['event']=='launched':launched[e['out_dir']]=e['name']
        if e['event']=='finished' and str(e['exit'])!='0':failed[launched[e['out_dir']]]=e
    specs={j['name']:j for j in lines(DISPATCH)};jobs=[];records=[];proof=[]
    for r in json.loads((source_stage/'plan.json').read_text()):
        if r['experiment']!='E9' or r['kind']!='train':raise ValueError('E9 training recovery only')
        e=failed[r['name']];log=Path(e['out_dir'])/'launch.log'
        if 'torch.OutOfMemoryError' not in log.read_text():raise ValueError('not documented OOM')
        root=Path(r['run_dir']);assert not (root/'results.json').exists()
        cfg=json.loads((root/'config.json').read_text());maximum=0
        for line in Path(cfg['data']).open():maximum=max(maximum,len(json.loads(line)['input_ids'])-1)
        if maximum>2304:raise ValueError('would truncate a sequence')
        j,row=retry_job(specs[r['name']],r,stage,code);jobs.append(j);records.append(row)
        proof.append(dict(failed_job=r['name'],failed_launcher=e['out_dir'],max_sequence_tokens=maximum,data_sha256=cfg['data_sha256'],old_batch_tokens=4096,new_batch_tokens=2304,all_sequences_retained=True))
    stage.mkdir();write(stage/'plan.json',records);write(stage/'jobs.json',jobs);write(stage/'recovery-proof.json',proof)
    publish(jobs,stage/'publish-initial')
    from followspec.rev2_priority import promote
    promote()

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--stage',type=Path,required=True);p.add_argument('--source-stage',type=Path,required=True);p.add_argument('--code',type=Path,required=True);a=p.parse_args();prepare(a.stage,a.source_stage,a.code)
