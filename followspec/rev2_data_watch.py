"""D54 data completion → manual decoded audit → training → frozen evaluations."""
import argparse,fcntl,json,subprocess,time
from pathlib import Path
from followspec.rev2_data_training import prepare as train
from followspec.rev2_qwen_serving import prepare as timing
from followspec.rev2_watch import sweep
from followspec.rev2_priority import promote
from ops.track_t import WS

def main():
    p=argparse.ArgumentParser();p.add_argument('--data',type=Path,required=True);p.add_argument('--root',type=Path,required=True);p.add_argument('--code',type=Path,required=True);p.add_argument('--panels',type=Path,required=True);a=p.parse_args()
    a.root.mkdir(exist_ok=True);lock=(a.root/'watch.lock').open('a');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
    plan=json.loads((a.data/'plan.json').read_text());seen=set();ready_targets=set()
    while True:
        promote()
        for line in (WS/'artifacts/M2_D28_20261006/response_queue.log').read_text().splitlines():
            if 'REV2-' in line and 'launch_failed' in line and line not in seen:print('ALERT launch_failed',line,flush=True);seen.add(line)
        for t in [0,1,2]:
            rows=[r for r in plan if r['target']==t];labels=['long4k','mixed20k'] if t<2 else ['generic16k'];sealed=a.root/f'sealed-t{t}';stage=a.root/f'training-t{t}'
            complete=sum((Path(r['run_dir'])/'results.json').exists() for r in rows)
            if complete!=len(rows):print('DATA',t,complete,'/',len(rows),flush=True);continue
            if not sealed.exists():
                log=a.root/f'seal-t{t}.log'
                with log.open('x') as f:
                    result=subprocess.run([str(WS/'.venv-atlas-031-clean/bin/python'),'-u','-m','followspec.rev2_seal','--stage',str(a.data),'--output',str(sealed),'--target',str(t)],stdout=f,stderr=subprocess.STDOUT)
                if result.returncode:raise RuntimeError('sealing failed; inspect '+str(log))
            if not all((sealed/x/'seal.json').exists() for x in labels):raise RuntimeError('incomplete sealed dataset '+str(sealed))
            if not all((sealed/x/'manual-audit.json').exists() for x in labels):
                print('MANUAL_AUDIT_REQUIRED',t,[str(sealed/x/'five_decoded_masks.json') for x in labels],flush=True);continue
            if not stage.exists():train(stage,a.code,sealed,t)
            if not (stage/'publish-initial/published.json').exists():raise RuntimeError('incomplete training publication '+str(stage))
            pending=sweep(stage,a.panels);print('TRAIN',t,'pending',pending,flush=True)
            if not pending and t==2:
                dest=a.root/'qwen-repair-timing'
                if not dest.exists():timing(dest,a.code,a.panels,stage)
            if not pending:ready_targets.add(t)
        if ready_targets=={0,1,2}:print('All target training complete; frozen evaluations and Qwen timing submitted; check final results separately.',flush=True);return
        time.sleep(30)
if __name__=='__main__':main()
