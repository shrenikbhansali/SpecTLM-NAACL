"""D-39: three FS lambda variants, exact sealed D-38 data and reused controls."""
import argparse
from pathlib import Path
from atlas.run_cell import sha256,write_new
from followspec.configs import check_matched
from followspec.production import ARMS
from followspec.production_pipeline import checked_stage,execution_spec,finish,jsonl,lines,new_output,read
from followspec.training_jobs import training_jobs


def build(source,output,*,code_repo):
    root,cfg=checked_stage(source)
    if cfg['stage']!='training-jobs' or cfg.get('training_seeds')!=[0]:raise ValueError('sealed single-seed source required')
    final,fc=checked_stage(cfg['finalized'])
    if sha256(final/'stage_files.json')!=cfg['finalized_stage_sha256']:raise ValueError('finalized source changed')
    configs={a:read(final/a/'training_config.json') for a in ARMS};check_matched(configs)
    if any(c.get('pilot',{}).get('decision_id')!='D-38' for c in configs.values()):raise ValueError('D-38 pilot required')
    original=lines(root/'jobs.jsonl');by_arm={}
    for j in original:
        cmd=j['args'][j['args'].index('--')+1:];arm=cmd[cmd.index('--arm')+1]
        if arm in by_arm or cmd[cmd.index('--seed')+1]!='0':raise ValueError('unique seed0 source matrix required')
        by_arm[arm]=j
    if set(by_arm)!=set(ARMS):raise ValueError('four original arms required')
    spec=execution_spec(fc['spec'],code_repo)
    out=new_output(output);variants=[];dispatch=[]
    for label,value in [('000',0.),('003',.03),('030',.3)]:
        dest=new_output(out/label/'finalized')
        for arm in ARMS:
            (dest/arm).mkdir()
            config=dict(configs[arm])
            if arm=='FS':config['delta_lambda']=value
            write_new(dest/arm/'training_config.json',config)
            # All data paths and their hash proofs remain the sealed original ones.
            write_new(dest/arm/'manifest.json',read(final/arm/'manifest.json'))
        finish(dest,fc|dict(spec=spec,source_finalized=str(final),source_sha256=sha256(final/'stage_files.json'),
            ablation=dict(decision_id='D-39',fs_delta_lambda=value)),read(final/'results.json'))
        proposal=training_jobs(dest,out/label/'proposed',python=cfg['python'],code_repo=code_repo,
            training_seeds=[0],job_prefix='m5-d39-l'+label,fs_delta_lambda=value,ablation_decision='D-39')
        jobs=lines(proposal/'jobs.jsonl');fs=next(j for j in jobs if j['name'].endswith('-fs-s0'))
        actual=new_output(out/label/'training')
        jsonl(actual/'jobs.jsonl',[fs,*[by_arm[a] for a in ARMS if a!='FS']])
        finish(actual,read(proposal/'config.json')|dict(source_training=str(root),source_sha256=sha256(root/'stage_files.json'),
            reused_controls=[by_arm[a]['name'] for a in ARMS if a!='FS']),
            dict(n_jobs=4,n_new_jobs=1,production_ready=True,submitted=False))
        variants.append(dict(label=label,value=value,training=str(actual)));dispatch.append(fs)
    jsonl(out/'dispatch.jsonl',dispatch)
    finish(out,dict(stage='lambda-ablation',decision_id='D-39',source_training=str(root),source_sha256=sha256(root/'stage_files.json'),
        variants=variants,reused_lambda=.1,reused_fs_job=by_arm['FS']),dict(n_new_jobs=3,submitted=False))
    return out


def main():
    p=argparse.ArgumentParser(description=__doc__)
    for name in ('source','output','code-repo'):p.add_argument('--'+name,required=True)
    a=p.parse_args();print(build(a.source,a.output,code_repo=a.code_repo))

if __name__=='__main__':main()
