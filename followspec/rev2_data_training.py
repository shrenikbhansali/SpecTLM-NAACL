"""Publish E9/E12 training only after matching sealed five-sample audits exist."""
import argparse,json
from pathlib import Path
from followspec.rev2_launch import training_job
from followspec.rev2_p1_jobs import remove
from followspec.review_followup import parts,replace,publish
from followspec.rev2_priority import promote
from ops.track_t import WS,DISPATCH,lines,write,sha

def prepare(stage,code,sealed,t):
    stage.mkdir(exist_ok=False);d={j['name']:j for j in lines(DISPATCH)};jobs=[];records=[]
    for label in (['long4k','mixed20k'] if t<2 else ['generic16k']):
        data=sealed/label/'per_prompt.jsonl';audit=sealed/label/'manual-audit.json';a=json.loads(audit.read_text())
        assert a['passed'] and a['data_sha256']==sha(data)
        for arm in ['fc','full']:
            exp='E9' if t<2 else 'E12';name=f'REV2-{exp}-t{t}-{arm}-{label}';out=stage/name
            source=d[f'FIX24-official-t{t}-16k-{arm}'] if t<2 else d[f'P3-D48-generality-2-{arm}']
            j=training_job(source,name,out,code,arm);o,i=parts(j)
            replace(o,'--prompts',data)
            for f,v in [('--data',data),('--audit',audit),('--batch-tokens',4096 if t<2 else 2048)]:replace(i,f,v)
            remove(i,'--schedule-steps')
            if '--one-epoch' not in i:i.append('--one-epoch')
            if label=='mixed20k':i.append('--allow-response-pairs')
            replace(o,'--note',f'D54 {exp}; {label}; native TTT3 one epoch, cap'+('2048+512 mixture' if label=='mixed20k' else ('2048' if t<2 else '512'))+'; compact final export; audited masks/eval exclusion')
            j['args']=o+['--']+i;jobs.append(j)
            records.append(dict(experiment=exp,kind='train',target=t,arm=arm,data_label=label,seed=0,name=name,run_dir=str(out),workloads=['speed128','math64','math32-512','math32-2048','math32-8192'] if t<2 else ['speed128','math500']))
    write(stage/'plan.json',records);write(stage/'jobs.json',jobs);publish(jobs,stage/'publish-initial');promote()
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--stage',type=Path,required=True);p.add_argument('--code',type=Path,required=True);p.add_argument('--sealed',type=Path,required=True);p.add_argument('--target',type=int,required=True);a=p.parse_args();prepare(a.stage,a.code,a.sealed,a.target)
