"""D61 CPU dependency/report watcher; all GPU work goes to the existing queue."""
import argparse
import datetime
import fcntl
import hashlib
import json
import subprocess
import sys
import time
import traceback
from pathlib import Path
from rebuttal.jobs import ROOT,job,submit


def completed(name):
    p=ROOT/'rebuttal/runs'/name/'metrics.json'
    return p.exists() and json.loads(p.read_text())['exit_code']==0


def advance_cap2048(stage,code):
    name='E3a_t0_generation2000_cap2048_s0_retry1'
    if not completed(name):return
    source=ROOT/'rebuttal/runs'/name/'cell';dest=stage/'cap2048-data'
    if not (dest/'manifest.json').exists():
        subprocess.run([sys.executable,'-m','rebuttal.e3a_data','--workspace',str(ROOT),'--generated',str(source),'--output',str(dest)],check=True)
    preview=ROOT/'rebuttal/E3a_preview2048_20261126.json';review=ROOT/'rebuttal/E3a_preview2048_review_20261126.json'
    approval=json.loads(review.read_text())
    if not approval['passed'] or hashlib.sha256(preview.read_bytes()).hexdigest()!=approval['preview_sha256']:raise ValueError('manual preview evidence changed')
    expected=json.loads(preview.read_text())
    with (source/'per_prompt.jsonl').open() as f:first=[json.loads(next(f)) for _ in range(5)]
    hashes=[hashlib.sha256(json.dumps(r,sort_keys=True).encode()).hexdigest() for r in first]
    if hashes!=[r['raw_record_sha256'] for r in expected]:raise ValueError('first five no longer match manual review')
    manifest=json.loads((dest/'manifest.json').read_text());audit=dest/'manual-audit.json'
    if not audit.exists():
        value=approval|{'data_sha256':manifest['data_sha256'],'source_complete':True,'first_five_source_hashes':hashes,'n':manifest['n'],'scope':'manual decoded review made during generation; sealed only after complete output and exact first-five identity proof'}
        with audit.open('x') as f:json.dump(value,f,indent=2);f.write('\n')
    template=json.loads((ROOT/'rebuttal/E3a_training_launch_20261126_1715_v2/E3a_t0_throughput200_cap512_s0.json').read_text());cmd=template['command'].copy();i=cmd.index('--output');del cmd[i:i+2]
    for k,v in [('--data',dest/'per_prompt.jsonl'),('--audit',audit)]:cmd[cmd.index(k)+1]=str(v)
    j=job(stage,code,'E3a_t0_throughput200_cap2048_s0','E3a',0,cmd,[dest/'per_prompt.jsonl',audit,dest/'manifest.json'],metadata={'kind':'throughput_train','sample':'cap2048','steps':200,'no_acceptance_requested':True})
    submit(stage,[j])


def throughput_report(stage):
    from rebuttal.reduce_e45 import csv_write
    measures=[];estimates=[]
    for mode in ['cap512','cap2048','native']:
        name='E3a_t0_throughput200_'+mode+'_s0'
        if not completed(name):continue
        cell=ROOT/'rebuttal/runs'/name/'cell';cfg=json.loads((cell/'config.json').read_text())
        profile=[json.loads(s) for s in (cell/'step_profile.jsonl').read_text().splitlines()]
        if len(profile)!=200 or [r['step'] for r in profile]!=list(range(1,201)):raise ValueError('incomplete200step profile')
        rows=[json.loads(s) for s in Path(cfg['data']).read_text().splitlines()]
        token_counts=[sum(len(rows[i]['input_ids'])-1 for i in b) for b in cfg['batch_plan']]
        if len(token_counts)!=200 or sum(token_counts)!=cfg['token_budget']:raise ValueError('token budget mismatch')
        data_manifest=json.loads((Path(cfg['data']).parent/'manifest.json').read_text())
        warm_s=sum(r['wall_s'] for r in profile[20:]);all_s=sum(r['wall_s'] for r in profile)
        measures.append({'sample':mode,'n':2000,'steps':200,'profiled_s_200':all_s,'tokens_200':sum(token_counts),'tokens_per_gpu_h_200':sum(token_counts)/all_s*3600,
                         'warm_steps':180,'warm_profiled_s':warm_s,'warm_tokens':sum(token_counts[20:]),'warm_tokens_per_gpu_h':sum(token_counts[20:])/warm_s*3600,
                         'mean_retained_shifted_tokens':data_manifest['kept_mean_input_tokens']-1,'mean_original_input_tokens':data_manifest['original_mean_input_tokens'],
                         'truncated_examples':data_manifest['truncated_examples'],'measured_total_trial_gpu_h':json.loads((cell.parent/'metrics.json').read_text())['gpu_hours'],
                         'source':str(cell),'profile_sha256':hashlib.sha256((cell/'step_profile.jsonl').read_bytes()).hexdigest(),'data_sha256':cfg['data_sha256']})
    native=next((m for m in measures if m['sample']=='native'),None)
    for mode in ['cap512','cap2048']:
        current=next((m for m in measures if m['sample']==mode),None)
        gen=ROOT/f'rebuttal/runs/E3a_t0_generation2000_{mode}_s0_retry1/cell/results.json'
        if not current or not native or not gen.exists():continue
        g=json.loads(gen.read_text());generation_h=g['wall_s']/3600*532000/2000
        gen_train_h=532000*current['mean_retained_shifted_tokens']/current['warm_tokens_per_gpu_h']
        native_h=114000*native['mean_retained_shifted_tokens']/native['warm_tokens_per_gpu_h']
        estimates.append({'response_cap':int(mode[3:]),'label':'extrapolated from measured throughput; one epoch; lower bound',
                          'generation_gpu_h_532k':generation_h,'regenerated_training_gpu_h_532k':gen_train_h,'native_training_gpu_h_114k':native_h,
                          'one_epoch_total_gpu_h':generation_h+gen_train_h+native_h,'measured_generation_n':2000,
                          'measured_generation_gpu_h':g['wall_s']/3600,'mean_generated_answer_tokens':g['answer_tokens']/2000,
                          'generated_tokens_per_gpu_h':g['answer_tokens']/(g['wall_s']/3600),'capped':g['capped'],
                          'scope':'one pass; native answers and regenerated responses explicitly clipped to2049input IDs; throughput from measured180steady steps after20startup steps; excludes full-corpus setup, optimizer persistence and failed attempts; not actual dedicated-checkpoint cost'})
    snapshot=stage/'throughput';snapshot.mkdir();csv_write(snapshot/'throughput.csv',measures);csv_write(snapshot/'one_epoch_cost.csv',estimates)
    (snapshot/'results.json').write_text(json.dumps({'status':'pilot','measurements':measures,'extrapolations':estimates},indent=2)+'\n')
    lines=['## E3a-throughput — measured training and labelled extrapolation','',
           'Pilot. Three separate200-step scratch trials with native objective and2048 shifted-token ceiling. Both all200-step and steady180-step rates are retained; lower-bound projection uses steps21–200, including online target capture. Actual trial GPUh includes initialization/export overhead. Native source model revision is not published; exact answer text is pinned by dataset revision.',
           '','| Data | n | Actual trial GPU-h | All200 tokens/GPU-h | Steady180 tokens/GPU-h | Truncated / 2000 |','|---|---:|---:|---:|---:|---:|']
    for m in measures:lines.append(f"| {m['sample']} | 2000 | {m['measured_total_trial_gpu_h']:.4f} | {m['tokens_per_gpu_h_200']:.0f} | {m['warm_tokens_per_gpu_h']:.0f} | {m['truncated_examples']} |")
    lines+=['','| Response cap | Generation532k GPU-h | Regenerated training532k GPU-h | Native training114k GPU-h | One-epoch total GPU-h |','|---|---:|---:|---:|---:|']
    for e in estimates:lines.append(f"| {e['response_cap']} | {e['generation_gpu_h_532k']:.2f} | {e['regenerated_training_gpu_h_532k']:.2f} | {e['native_training_gpu_h_114k']:.2f} | {e['one_epoch_total_gpu_h']:.2f} |")
    lines+=['','All projected cells are **extrapolated from measured throughput; one epoch; lower bound**, under the recorded truncation policy. This is not a measured reproduction of the dedicated checkpoint. Missing trials remain pending. Source: '+str(snapshot/'results.json')+'.']
    return '\n'.join(lines)


def determinism_report():
    name='TD_t0_none_sameprocess_threewarm_20261126'
    if not completed(name):return None
    cell=ROOT/'rebuttal/runs'/name/'cell';r=json.loads((cell/'timing.json').read_text());passes=r['passes']
    if len(passes)!=4 or any(len(p['per_prompt'])!=1 for p in passes):raise ValueError('unexpected determinism panel')
    from rebuttal.timing_divergence import first_difference
    seq=[p['per_prompt'][0]['completion_token_ids'] for p in passes]
    diffs=[first_difference(seq[i],seq[j]) for i,j in [(1,2),(1,3),(2,3)]]
    return ('## Timing-determinism — same-process no-spec check\n\nPilot; one fixed first SPEED prompt, batch1, unchanged frozen harness, one cold pass and three warm repetitions in the same process. '
            f'Warm pair first-divergence indices: {diffs} (null means identical). All four output lengths: {[len(s) for s in seq]}. '
            'This one-query diagnostic does not replace the all-process/output characterization. Source: '+str(cell/'timing.json')+'.\n')


def advance_e8_generation(stage,code):
    """Conditional P1: all new P0 stages dispatched, no P0 backlog, idle A40."""
    name='E8lite_t0_aya4000_generation_s0';inputs=ROOT/'rebuttal/E8_lite_inputs_20261126'
    if (ROOT/'rebuttal/runs'/name/'cmd.txt').exists():return
    if not (inputs/'prompt-review.json').exists():return
    if not (ROOT/'rebuttal/runs/E3a_t0_throughput200_cap2048_s0/cmd.txt').exists():return
    from rebuttal.jobs import CANONICAL
    plans=[json.loads(s) for s in CANONICAL.read_text().splitlines()]
    for plan in plans:
        if not plan['name'].startswith(('E4c','E3a','TD_')):continue
        run=ROOT/'rebuttal/runs'/plan['name']
        if not (run/'cmd.txt').exists() and not (run/'metrics.json').exists():return
    if datetime.datetime.now().astimezone()>=datetime.datetime.fromisoformat('2026-11-28T12:00:00-05:00'):return
    result=subprocess.run(['ssh','-o','BatchMode=yes','heck-srv4.ece.gatech.edu','nvidia-smi --query-gpu=index,memory.used,utilization.gpu --format=csv,noheader,nounits'],capture_output=True,text=True,timeout=30,check=True)
    idle=[]
    for line in result.stdout.splitlines():
        index,memory,util=map(int,line.split(','))
        if index in [0,1,2,3] and memory<512 and util<5:idle.append(index)
    if not idle:return
    template=json.loads((ROOT/'rebuttal/E3a_launch_20261125_2027/E3a_t0_generation2000_cap512_s0.json').read_text());cmd=template['command'].copy();i=cmd.index('--output');del cmd[i:i+2]
    for flag,value in [('--public-queries',inputs/'queries4000.jsonl'),('--forbidden',inputs/'forbidden.jsonl'),('--count',4000),('--training-context-budget',2048)]:cmd[cmd.index(flag)+1]=str(value)
    j=job(stage,code,name,'E8-lite',0,cmd,[inputs/'queries4000.jsonl',inputs/'forbidden.jsonl',inputs/'manifest.json',inputs/'prompt-review.json'],metadata={'kind':'generation','n':4000,'source':'Aya','stop_at_et':'2026-11-28T23:59:00-05:00','conditional_P1_idle_slots':idle})
    submit(stage,[j])


def advance_e8_repair(stage,code):
    from rebuttal.e45_dispatch import eval_job
    inputs=ROOT/'rebuttal/E8_lite_inputs_20261126';generation=ROOT/'rebuttal/runs/E8lite_t0_aya4000_generation_s0/cell'
    if not (generation/'config.json').exists():return
    jobs=[];gate=json.loads((ROOT/'rebuttal/advance_r1_20261124_1523/gate/results.json').read_text())
    for arm in ['reuse','full']:
        ref=next(r for r in gate if r['target']==0 and r['arm']==arm and r['benchmark']=='speed128')
        cfg=json.loads((ROOT/'rebuttal/runs'/ref['name']/'cell/config.json').read_text())
        jobs.append(eval_job(stage,code,f'E8lite_t0_{arm}_aya128_s0',0,Path(cfg['drafter']),cfg['drafter_revision'],'eagle3',inputs/'aya128.jsonl',experiment='E8-lite',metadata={'benchmark':'aya128','arm':arm}))
    audit=generation/'manual-audit.json'
    if completed('E8lite_t0_aya4000_generation_s0') and not audit.exists():
        notice=stage/'E8-response-audit-needed.json'
        if not notice.exists():notice.write_text(json.dumps({'status':'needs manual five decoded response/mask review','data':str(generation/'per_prompt.jsonl'),'samples':str(generation/'five_decoded_masks.json')},indent=2)+'\n')
    if completed('E8lite_t0_aya4000_generation_s0') and audit.exists():
        import shutil
        from rebuttal.e3a_data import jsonl_line
        m=json.loads((inputs/'manifest.json').read_text());check=json.loads(audit.read_text())
        source=generation/'per_prompt.jsonl'
        if not check.get('passed') or check.get('data_sha256')!=hashlib.sha256(source.read_bytes()).hexdigest():raise ValueError('E8 manual response audit hash mismatch')
        original=Path(m['original_data'])
        if hashlib.sha256(original.read_bytes()).hexdigest()!=m['original_data_sha256']:raise ValueError('English baseline data changed')
        base=[json.loads(s) for s in original.read_text().splitlines()];new=[json.loads(s) for s in source.read_text().splitlines()]
        queries=[json.loads(s) for s in (inputs/'queries4000.jsonl').read_text().splitlines()];byid={r['sample_id']:r for r in new}
        if len(new)!=4000 or len(byid)!=4000 or set(byid)!={r['prompt_id'] for r in queries}:raise ValueError('Aya response identity mismatch')
        for index,q in zip(m['replace_indices'],queries,strict=True):base[index]=byid[q['prompt_id']]
        dest=stage/'mixed16k';data=dest/'per_prompt.jsonl'
        if not data.exists():
            dest.mkdir(exist_ok=False)
            with data.open('x') as f:
                for r in base:f.write(jsonl_line(r))
            manifest=m|{'mixed_data_sha256':hashlib.sha256(data.read_bytes()).hexdigest(),'generation_data_sha256':check['data_sha256'],'new_responses':4000,'reused_responses':12000}
            (dest/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
            shutil.copyfile(generation/'five_decoded_masks.json',dest/'five_decoded_masks.json')
            review=check|{'data_sha256':manifest['mixed_data_sha256'],'scope':'exact copied4000 audited Aya responses plus12000 unchanged already-audited Alpaca responses; inspected five new-path decoded responses/masks; exact replacement indices logged','source_audit':str(audit)}
            (dest/'manual-audit.json').write_text(json.dumps(review,indent=2)+'\n')
        template=json.loads((ROOT/'rebuttal/advance_r1_20261124_1523/E2_t0_decoder_head_lora_s0.json').read_text());cmd=template['command'].copy();i=cmd.index('--output');del cmd[i:i+2]
        for flag,value in [('--variant','full'),('--data',data),('--audit',dest/'manual-audit.json'),('--forbidden',inputs/'forbidden.jsonl')]:cmd[cmd.index(flag)+1]=str(value)
        jobs.append(job(stage,code,'E8lite_t0_full_mixed16k_s0','E8-lite',0,cmd,[data,dest/'manual-audit.json',dest/'manifest.json',inputs/'forbidden.jsonl'],metadata={'kind':'train','variant':'full','training_seed':0,'stop_at_et':'2026-11-28T23:59:00-05:00'}))
    train=ROOT/'rebuttal/runs/E8lite_t0_full_mixed16k_s0'
    if completed(train.name):
        cfg=json.loads((train/'config.yaml').read_text());exports=list((train/'cell').glob('export-*'))
        if len(exports)!=1:raise ValueError('expected one final E8 export')
        for panel in ['speed128','aya128']:
            jobs.append(eval_job(stage,code,f'E8lite_t0_mixed_{panel}_s0',0,exports[0],cfg['harness_commit'],'eagle3','speed128' if panel=='speed128' else inputs/'aya128.jsonl',experiment='E8-lite',metadata={'benchmark':panel,'arm':'mixed'}))
    if jobs:submit(stage,jobs)


def e8_report(stage):
    from rebuttal.reduce_e45 import rows,sha,acceptance_contrast,FROZEN
    gate=json.loads((ROOT/'rebuttal/advance_r1_20261124_1523/gate/results.json').read_text());results=[]
    ids={r['prompt_id'] for r in rows(ROOT/'rebuttal/E8_lite_inputs_20261126/speed-multilingual12.jsonl')}
    for panel in ['speed128','multilingual12','aya128']:
        basepanel='speed128' if panel=='multilingual12' else panel
        name='E8lite_t0_mixed_'+basepanel+'_s0'
        if not completed(name):continue
        candidate=ROOT/'rebuttal/runs'/name/'cell';cc=json.loads((candidate/'config.json').read_text())
        for arm in ['reuse','full']:
            if basepanel=='speed128':ref=ROOT/'rebuttal/runs'/next(r['name'] for r in gate if r['target']==0 and r['benchmark']=='speed128' and r['arm']==arm)/'cell'
            else:
                if not completed(f'E8lite_t0_{arm}_aya128_s0'):continue
                ref=ROOT/'rebuttal/runs'/f'E8lite_t0_{arm}_aya128_s0'/'cell'
            rc=json.loads((ref/'config.json').read_text())
            for cfg in [cc,rc]:
                if cfg.get('frozen_harness_commit',cfg.get('code_commit'))!=FROZEN or cfg['engine_version']!='0.31.0' or cfg['K']!=4:raise ValueError('nonfrozen E8 acceptance')
            if cc['prompt_sha256']!=rc['prompt_sha256']:raise ValueError('unpaired E8 prompts')
            rr,cr=rows(ref/'per_prompt.jsonl'),rows(candidate/'per_prompt.jsonl')
            if panel=='multilingual12':rr=[r for r in rr if r['prompt_id'] in ids];cr=[r for r in cr if r['prompt_id'] in ids]
            results.append({'panel':panel,'reference':arm,'reference_source':str(ref),'candidate_source':str(candidate),'raw_sha256':[sha(ref/'per_prompt.jsonl'),sha(candidate/'per_prompt.jsonl')],**acceptance_contrast({0:rr},{0:cr},4,4)})
    (stage/'E8-lite-results.json').write_text(json.dumps({'status':'pilot' if results else 'pending','results':results},indent=2)+'\n')
    from rebuttal.report_planner import fmt
    lines=['## E8-lite — conditional multilingual repair','',
       'R1 only, seed0. Replace4000 uniformly chosen Alpaca instruction indices with4000 Aya instructions, retaining12000 original responses. Six language labels match the12 SPEED multilingual queries: Arabic, English (including translation requests), French, Spanish, Thai, Vietnamese. Counts and fixed held-out128 allocation are in E8_lite_inputs_20261126/manifest.json. All new training/evaluation queries deduplicated against existing evaluation and full English-only training data; disjoint Aya panel. No language chosen from evaluation outcomes.',
       '','| Panel | Reference | n | Mixed tau | Paired mixed minus reference tau |','|---|---|---:|---:|---:|']
    for r in results:lines.append(f"| {r['panel']} | {r['reference']} | {r['n']} | {fmt(r['candidate_tau'],r['candidate_tau_ci95'])} | {fmt(r['delta_tau'],r['delta_tau_ci95'])} |")
    lines+=['','Pending until audited generation, training and frozen acceptance finish. Budget12GPUh; no completion is inferred. If not final by Nov28 EOD, status for the response is not run. Source: '+str(stage/'E8-lite-results.json')+'.']
    return '\n'.join(lines)


def main():
    p=argparse.ArgumentParser();p.add_argument('--output',type=Path,required=True);p.add_argument('--code',type=Path,required=True);p.add_argument('--once',action='store_true');a=p.parse_args();a.output.mkdir(parents=True,exist_ok=True)
    with (a.output/'watch.lock').open('a') as lock:
        fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB);previous=None
        while True:
            try:
                advance_cap2048(a.output,a.code)
                advance_e8_generation(a.output,a.code)
                advance_e8_repair(a.output,a.code)
                files=sorted((ROOT/'rebuttal/runs').glob('*/metrics.json'))+sorted((ROOT/'rebuttal/runs/E3b_t0_scratch20ep_s0_gcc13/cell').glob('export-*/repair_provenance.json'))
                signature=hashlib.sha256(b''.join(str(f).encode()+f.read_bytes() for f in files)).hexdigest()
                if signature!=previous:
                    stamp=datetime.datetime.now().astimezone().strftime('%Y%m%d_%H%M%S_%f');out=a.output/stamp;out.mkdir()
                    subprocess.run([sys.executable,'-m','rebuttal.reduce_e45','--workspace',str(ROOT),'--output',str(out/'E45')],check=True)
                    subprocess.run([sys.executable,'-m','rebuttal.report_e45','--results',str(out/'E45/results.json'),'--output',str(out/'E45/report.md'),'--publish',str(ROOT/'rebuttal/RESULTS.md')],check=True)
                    subprocess.run([sys.executable,'-m','rebuttal.planner_analysis','--workspace',str(ROOT),'--output',str(out/'analysis')],check=True)
                    subprocess.run([sys.executable,'-m','rebuttal.report_planner','--analysis',str(out/'analysis/results.json'),'--timing',str(ROOT/'rebuttal/timing_divergence_20261126_all120/results.json'),'--output',str(out/'report.md'),'--publish',str(ROOT/'rebuttal/RESULTS.md')],check=True)
                    extra=[throughput_report(out),determinism_report(),e8_report(out)]
                    from rebuttal.report_e45 import replace_section
                    text=(ROOT/'rebuttal/RESULTS.md').read_text()
                    for section in extra:
                        if not section:continue
                        key=section.split(' — ',1)[0][3:]
                        text=replace_section(text,key,section) if '\n## '+key+' — ' in text else text+'\n'+section+'\n'
                    (ROOT/'rebuttal/RESULTS.md').write_text(text)
                    (a.output/'latest.json').write_text(json.dumps({'path':str(out),'signature':signature})+'\n');previous=signature
                    print('PUBLISHED',out,flush=True)
            except Exception as e:
                with (a.output/'alerts.jsonl').open('a') as f:f.write(json.dumps({'time':datetime.datetime.now().astimezone().isoformat(),'error':repr(e),'traceback':traceback.format_exc()})+'\n')
                print(traceback.format_exc(),flush=True)
                if a.once:raise
            if a.once:return
            time.sleep(60)


if __name__=='__main__':main()
