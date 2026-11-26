"""Publish D61 sections without changing E4/E5 automatic result sections."""
import argparse
import json
import re
from pathlib import Path


def fmt(value,ci,scale=1):
    return 'undefined' if value is None or ci is None else f'{value*scale:.3f} [{ci[0]*scale:.3f}, {ci[1]*scale:.3f}]'


def sections(data,div,source,divsource):
    out={};l=['## E1-D61 — derivative-text raw crossover cells','',
      'Pilot; n=64 paired contexts per target, 10,000 sequence resamples. Values a–d and d−a are percentage points. a=parent taps/parent verifier, b=parent taps/child verifier, c=child taps/parent verifier, d=child taps/child verifier. These are fixed-text HF agreement measurements, not served acceptance.',
      '','| Target | a | b | c | d | d−a | (d−b)/(d−a) |','|---|---:|---:|---:|---:|---:|---:|']
    for r in data['E1']:
        x=r['cells'];v=r['deployment_ratio'];l.append('| '+r['model']+' | '+' | '.join(fmt(x[k]['mean'],x[k]['ci95'],100) for k in ['a','b','c','d','d-a'])+' | '+fmt(v['mean'],v['ci95'])+' |')
    l+=['','The requested ratio is recomputed from macro contrasts in each paired resample; it is not the prior averaged-feature share. A denominator CI crossing zero makes the ratio unstable (see JSON flags); it is not a percentage of an identified causal mechanism. No additional GPU runs. Source: '+source+'.']
    out['E1-D61']='\n'.join(l)
    l=['## E2-restoration — checkpoint interventions','',
       'Pilot; three paired training seeds, n=128 queries per seed and panel. All differences below are versus the same seed’s intact whole-drafter LoRA checkpoint. These are eval-time restorations, not separately trained variants.',
       '','| Target | Panel | Kept trained deltas | Tau [95% CI] | Delta tau versus whole LoRA [95% CI] |','|---|---|---|---:|---:|']
    labels={'lora-all':'all','lora-fc_only':'interface only; restore all other weights','lora-no_fc':'all except interface; restore interface'}
    for r in data['E2_restoration']:
        l.append(f"| {['R1','Nemotron'][r['target']]} | {r['benchmark']} | {labels[r['variant']]} | {fmt(r['candidate_tau'],r['candidate_tau_ci95'])} | {fmt(r['delta_tau'],r['delta_tau_ci95'])} |")
    l+=['','Only audited corrected shard exports are included. Independent raw-counter reduction; source: '+source+'.'];out['E2-restoration']='\n'.join(l)
    r=data['E3'];curve=['## E3b — continuous scratch curve','',
      'Pilot; fixed20epoch cosine schedule, one uninterrupted seed0 run. Intermediate exports are not independently annealed short runs. Stop no later than Nov28 noon ET. Frozen K4 acceptance, n=128 per panel; query bootstrap95%CIs.',
      '','| Epoch | Cumulative train GPU-h | SPEED tau | MATH tau |','|---|---:|---:|---:|']
    for c in r['checkpoints']:
        scores=[]
        for panel in ['speed128','math128']:
            v=c.get('acceptance',{}).get(panel);scores.append(fmt(v['candidate_tau'],v['candidate_tau_ci95']) if v else 'pending')
        curve.append(f"| {c['epoch']} | {c['train_gpu_h_cumulative']:.3f} | "+' | '.join(scores)+' |')
    curve+=['','Source: '+source+'. Raw p1, counters and hashes retained in JSON. Existing watcher evaluates every scheduled completed export; unexported epochs have no inferred acceptance.'];out['E3b']='\n'.join(curve)
    l=['## E3-cost — measured scratch and data costs','',
      f"Original generation logs are present for all 64,000 examples: **{r['generation_gpu_h']:.6f} A40 GPU-hours**, including reused 16k plus the 48k Alpaca/Dolly extension. This is a sum of recorded successful generation wall times, not an estimate.",
      '','| Exported epoch | Step | Cumulative training GPU-h | Generation GPU-h | Data + training GPU-h |','|---|---:|---:|---:|---:|']
    for c in r['checkpoints']:l.append(f"| {c['epoch']} | {c['step']} | {c['train_gpu_h_cumulative']:.6f} | {c['generation_gpu_h']:.6f} | {c['total_gpu_h']:.6f} |")
    l+=['',r['cost_scope']+'.',r['source_mixture']+'. Epoch-5 evaluation is already wired to the existing export watcher. E3a’s separate one-epoch lower-bound extrapolation awaits measured 200-step training runs. Source: '+source+'.'];out['E3-cost']='\n'.join(l)
    l=['## E4-selected50M — explicit paired comparison with full repair','',
       'Pilot; same EDA-selected 8k, same native recipe/steps, paired seeds 0 and 1, n=128. EDA50M has 50,339,840 trainable parameters; ReFit-full has 424,689,664. This comparison is data/step matched, not capacity matched.',
       '','| Panel | EDA50M tau | ReFit-full tau | Full minus EDA50M tau |','|---|---:|---:|---:|']
    for r in data['E4_small_vs_full']:l.append(f"| {r['benchmark']} | {fmt(r['reference_tau'],r['reference_tau_ci95'])} | {fmt(r['candidate_tau'],r['candidate_tau_ci95'])} | {fmt(r['delta_tau'],r['delta_tau_ci95'])} |")
    l+=['','All intervals are paired seed/query bootstrap 95% CIs. Source: '+source+'.'];out['E4-selected50M']='\n'.join(l)
    r=data['E4c'];l=['## E4c — capacity-matched method × subset comparison','',
      'Pilot. ReFit-interface: 50,331,648 parameters; EDA50M: 50,339,840 (routing accounts for the 8,192 difference). Same selected/random 8k, steps, optimizer and native objective within each seed. Seeds 0 and 1; n=128 per evaluation panel. Pending results are not inferred.',
      '','| Panel / method | EDA-selected 8k tau [95% CI] | Random 8k tau [95% CI] |','|---|---:|---:|']
    for panel in ['speed128','math128']:
        for method in ['eda50m','interface']:
            cells=[]
            for subset in ['selected','random']:
                row=next((x for x in r['results'] if x['kind']=='mean' and x['benchmark']==panel and x['method']==method and x['subset']==subset),None)
                cells.append(fmt(row['candidate_tau'],row['candidate_tau_ci95'])+f" (seeds {row['seeds']})" if row else 'pending')
            l.append('| '+panel+' / '+method+' | '+' | '.join(cells)+' |')
    l+=['','| Panel / subset | Paired interface − EDA50M tau [95% CI] | Seeds / n |','|---|---:|---:|']
    for panel in ['speed128','math128']:
        for subset in ['selected','random']:
            row=next((x for x in r['results'] if x['kind']=='paired interface minus EDA50M' and x['benchmark']==panel and x['subset']==subset),None)
            l.append(f"| {panel} / {subset} | "+(fmt(row['delta_tau'],row['delta_tau_ci95'])+f" | {row['seeds']} / {row['n']} |" if row else 'pending | pending |'))
    l+=['',f"New E4c completed cost {r['completed_gpu_hours_including_failures']:.3f}/15 GPU-h; active time is additional and enforced by the live guard. Historical selected EDA is reused, not charged again. Old automatic E4 rows may include E4c because the exact pipeline retains experiment=E4; this E4c prefix accounting is the separate approved budget.",'Source: '+source+'.'];out['E4c']='\n'.join(l)
    if div:
        l=['## Timing-divergence — required E5 characterization','',f"Pilot CPU audit of {len(div['sources'])} completed fresh processes. Full pair-level details are in {divsource}/process-pairs.csv; every arm and all cross-process pairings included. Warm repeats use the same repeat index in each pair. Identical completion means exact token-ID equality, including length. First-divergence quartiles (in CSV) use zero-based token index among nonidentical completions; a strict prefix diverges at its first missing token.",
           '','| Target / panel / batch | No-spec vs no-spec identical % | Spec vs no-spec identical % | Spec vs spec identical % |','|---|---:|---:|---:|']
        keys=sorted({(r['target'],r['benchmark'],r['batch']) for r in div['category_summary']})
        for key in keys:
            rr=[x for x in div['category_summary'] if (x['target'],x['benchmark'],x['batch'])==key]
            values=[next(x['identical_fraction'] for x in rr if x['category']==c) for c in ['no-spec/no-spec','spec/no-spec','spec/spec']]
            l.append('| '+str(key)+' | '+' | '.join(f'{v*100:.2f}' for v in values)+' |')
        l+=['','ReFit-full / distilled-1B warm throughput ratios; 10,000 paired process/query-batch bootstrap 95% CIs. Output-matching subset requires equality across all six processes and all three warm repeats. For batch8, only entire matching original batches have measured elapsed time.',
            '','| Target / panel / batch | All 128 queries | Matching queries | Timed matching queries | Matching-output ratio |','|---|---:|---:|---:|---:|']
        for r in div['ratios']:
            if 'all_queries' not in r:continue
            x,y=r['all_queries'],r['matching_outputs'];l.append(f"| {['R1','Nemotron'][r['target']]} / {r['benchmark']} / b{r['batch']} | {fmt(x['token_speedup'],x['token_ci95'])} | {r['n_matching_queries']} | {r['n_timed_matching_queries']} | "+(fmt(y['token_speedup'],y['token_ci95']) if y else 'not estimable')+' |')
        l+=['','Divergence is present in every no-spec/spec category, including repeated fresh no-spec processes, but its rates vary substantially by arm pairing, workload and batch; the evidence does **not** establish that all arms are affected alike. Batch1 matching-output subsets retain the measured ReFit-full advantage, with only 1–16 queries per panel, so they do not establish equivalence on the full population. No complete batch8 matching subset survives. First-divergence-truncated throughput is not identifiable from total batch elapsed time: no per-token timestamps were recorded, and prorating by token count would manufacture a timing measurement. The root numerical/engine cause is unestablished. These observations qualify E5 as observed serving throughput under the recorded outputs, not a proof of bit-identical execution across methods.',
           '','The newly requested one-prompt, same-process no-spec three-repeat check is queued as TD_t0_none_sameprocess_threewarm_20261126; results pending. Existing within-process pair counts are in within-process.csv. Harness unchanged. Source: '+divsource+'/results.json.'];out['Timing-divergence']='\n'.join(l)
    out['D61-scope']='## D61-scope — deadline and exclusions\n\nFinal numbers: Nov28 EOD ET. E6, E7, E9, EDA native20epoch schedule and EDA seed2: **not run for the response**, per owner-approved Nov26 scope. No SGLang integration. E8-lite is conditional P1, R1 only, 12GPUh; its results remain pending and will be marked not run if not final by the deadline. No paper edits or OpenReview posting.\n'
    return out


def main():
    p=argparse.ArgumentParser();p.add_argument('--analysis',type=Path,required=True);p.add_argument('--timing',type=Path);p.add_argument('--output',type=Path,required=True);p.add_argument('--publish',type=Path);a=p.parse_args()
    data=json.loads(a.analysis.read_text());div=json.loads(a.timing.read_text()) if a.timing else None
    ss=sections(data,div,str(a.analysis),str(a.timing.parent) if a.timing else '')
    with a.output.open('x') as f:f.write('\n\n'.join(ss.values())+'\n')
    if a.publish:
        text=a.publish.read_text();(a.output.parent/'previous-RESULTS.md').write_text(text)
        for key,value in ss.items():
            pattern=r'(?ms)^## '+re.escape(key)+r' — .*?(?=^## |\Z)'
            if re.search(pattern,text):text=re.sub(pattern,lambda _:value+'\n\n',text)
            else:text+='\n'+value+'\n'
        temp=a.publish.with_suffix('.d61.tmp');temp.write_text(text);temp.replace(a.publish)


if __name__=='__main__':main()
