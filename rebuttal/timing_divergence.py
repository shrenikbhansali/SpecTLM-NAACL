"""D61 CPU-only output diagnostics. No harness or elapsed-time interpolation."""
import argparse
import copy
import itertools
import json
from collections import defaultdict
from pathlib import Path
import numpy as np
from rebuttal.reduce_e45 import FROZEN, csv_write, sha, timing_contrast


def first_difference(a,b):
    for i,(x,y) in enumerate(zip(a,b)):
        if x!=y:return i
    return min(len(a),len(b)) if len(a)!=len(b) else None


def tokens(p):
    result={r['prompt_id']:r['completion_token_ids'] for r in p['per_prompt']}
    if len(result)!=len(p['per_prompt']):raise ValueError('duplicate query')
    return result


def validate_pair(a,b):
    for key in ['prompt_sha256','target_revision','batch_size','max_new_tokens','seed','temperature','max_model_len','gpu_memory_utilization']:
        if a['config'].get(key)!=b['config'].get(key):raise ValueError('unmatched '+key)
    if len(a['timing']['passes'])!=4 or len(b['timing']['passes'])!=4:raise ValueError('expected cold + three warm passes')


def summarize_differences(values):
    divergent=[v for v in values if v is not None]
    return {'observations':len(values),'identical':len(values)-len(divergent),
            'identical_fraction':1-len(divergent)/len(values),
            'first_divergence_quartiles':np.quantile(divergent,[.25,.5,.75]).tolist() if divergent else None,
            'divergent':len(divergent)}


def pair_summary(a,b,passes=(1,2,3)):
    validate_pair(a,b);values=[];n=None
    for repeat in passes:
        am,bm=[tokens(x['timing']['passes'][repeat]) for x in (a,b)]
        if am.keys()!=bm.keys():raise ValueError('unpaired query IDs')
        n=len(am);values.extend(first_difference(am[q],bm[q]) for q in sorted(am))
    return {'n_queries':n,'passes':list(passes),**summarize_differences(values)}


def matching_queries(cells):
    first=tokens(cells[0]['timing']['passes'][1]);kept=set(first)
    for cell in cells:
        validate_pair(cells[0],cell)
        for p in cell['timing']['passes'][1:]:
            current=tokens(p)
            if current.keys()!=first.keys():raise ValueError('unpaired query IDs')
            kept.intersection_update(q for q in current if current[q]==first[q])
    return kept


def restrict_complete_batches(cells,kept):
    groups=[b['prompt_ids'] for b in cells[0]['timing']['passes'][1]['batches']]
    retained=[i for i,g in enumerate(groups) if set(g)<=kept]
    actual={q for i in retained for q in groups[i]}
    result=copy.deepcopy(cells)
    for cell in result:
        for p in cell['timing']['passes']:
            if [b['prompt_ids'] for b in p['batches']]!=groups:raise ValueError('changed timed batch composition')
            p['batches']=[p['batches'][i] for i in retained]
            p['per_prompt']=[r for r in p['per_prompt'] if r['prompt_id'] in actual]
    return result,len(retained)


def load_timings(root):
    groups=defaultdict(dict);sources=[]
    for run in sorted((root/'rebuttal/runs').glob('E5_*_timing_*')):
        if not (run/'metrics.json').exists() or json.loads((run/'metrics.json').read_text())['exit_code']!=0:continue
        plan=json.loads((run/'config.yaml').read_text());cell=run/'cell'
        c=json.loads((cell/'config.json').read_text())
        if c['harness_commit']!=FROZEN or c['engine_version']!='0.31.0' or c['gpu_type']!='NVIDIA A40' or c['temperature']!=0:raise ValueError('changed timing protocol')
        arm=run.name.split('_timing_',1)[1].split('_',1)[0]
        key=(plan['target'],plan['benchmark'],plan['batch_size'])
        entry={'config':c,'timing':json.loads((cell/'timing.json').read_text()),'run':run.name,'sha256':sha(cell/'timing.json')}
        identity=(arm,plan['replicate'])
        if identity in groups[key]:raise ValueError('two successful runs for one process identity: '+run.name)
        groups[key][identity]=entry;sources.append({'run':run.name,'timing_sha256':entry['sha256'],'config_sha256':sha(cell/'config.json')})
    return groups,sources


def main():
    p=argparse.ArgumentParser();p.add_argument('--workspace',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
    a.output.mkdir(parents=True,exist_ok=False)
    groups,sources=load_timings(a.workspace);pairs=[];within=[];ratios=[]
    for key,cells in sorted(groups.items()):
        panel=dict(zip(['target','benchmark','batch'],key))
        for (aa,ai),(ba,bi) in itertools.combinations(sorted(cells),2):
            category='no-spec/no-spec' if aa==ba=='none' else 'spec/no-spec' if 'none' in (aa,ba) else 'spec/spec'
            pairs.append(panel|{'category':category,'same_arm':aa==ba,'left_arm':aa,'left_process':ai,'right_arm':ba,'right_process':bi,
                               'left_run':cells[aa,ai]['run'],'right_run':cells[ba,bi]['run'],**pair_summary(cells[aa,ai],cells[ba,bi])})
        for (arm,i),cell in sorted(cells.items()):
            for x,y in itertools.combinations([1,2,3],2):
                left,right=[tokens(cell['timing']['passes'][r]) for r in (x,y)]
                if left.keys()!=right.keys():raise ValueError('unpaired warm repetitions')
                within.append(panel|{'arm':arm,'process':i,'left_repeat':x,'right_repeat':y,'n_queries':len(left),
                                    **summarize_differences([first_difference(left[q],right[q]) for q in sorted(left)])})
        if any((arm,i) not in cells for arm in ['full','distilled'] for i in range(3)):
            ratios.append(panel|{'status':'pending three processes per arm'});continue
        full=[cells['full',i] for i in range(3)];student=[cells['distilled',i] for i in range(3)]
        kept=matching_queries(full+student);restricted,n=restrict_complete_batches(full+student,kept)
        baseline=timing_contrast(full,student)['warm']
        record=panel|{'all_queries':baseline,'n_matching_queries':len(kept),'matching_query_ids':sorted(kept),'n_complete_matching_batches':n,
                      'n_timed_matching_queries':sum(len(b['prompt_ids']) for b in restricted[0]['timing']['passes'][1]['batches'])}
        record['matching_outputs']=timing_contrast(restricted[:3],restricted[3:])['warm'] if n else None
        record['status']='complete' if n else 'not estimable: no complete matching timed batch'
        ratios.append(record)
    categories=[]
    for panel in sorted(groups):
        for cat in ['no-spec/no-spec','spec/no-spec','spec/spec']:
            rr=[r for r in pairs if (r['target'],r['benchmark'],r['batch'])==panel and r['category']==cat]
            if not rr:continue
            total=sum(r['observations'] for r in rr);same=sum(r['identical'] for r in rr)
            categories.append(dict(zip(['target','benchmark','batch'],panel))|{'category':cat,'process_pairs':len(rr),'observations':total,'identical_fraction':same/total})
    protocol={'indexing':'first divergence is zero-based, including first missing token for strict prefixes; quartiles conditional on divergence',
              'process_pairs':'all unordered pairs, including every cross-arm process-index pairing; same warm-repeat index paired (three repeats)',
              'within_process':'all three pairs of warm repeats, each process separately',
              'matching_subset':'identical completion IDs across full and distilled, all six processes and all three warm repeats; no selection on timing',
              'batch8':'retain only original batches whose every query matches; never apportion shared batch wall time',
              'first_divergence_truncated_timing':'not identifiable: only total batch elapsed time was recorded, without per-token timestamps; token-count prorating would not measure prefix throughput',
              'inference':'matching-output subset is a conditional sensitivity analysis; its representativeness can differ from the complete evaluation panel',
              'bootstrap':'10000 paired process and original prompt-batch resamples; warm repetitions averaged within process'}
    result={'status':'pilot','protocol':protocol,'sources':sources,'process_pair_count':len(pairs),'category_summary':categories,'ratios':ratios,'within_process':within}
    csv_write(a.output/'process-pairs.csv',pairs);csv_write(a.output/'within-process.csv',within);csv_write(a.output/'categories.csv',categories)
    (a.output/'results.json').write_text(json.dumps(result,indent=2,allow_nan=False)+'\n')
    print(json.dumps({'timing_processes':len(sources),'process_pairs':len(pairs),'ratios':[r|{'matching_query_ids':'see file'} for r in ratios]},indent=2))


if __name__=='__main__':main()
