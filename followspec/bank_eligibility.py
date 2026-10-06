"""D-28 bank workload evidence, independent of mixture membership policy."""
import json
from pathlib import Path
from atlas.run_cell import sha256
from followspec.production import checked_queries


def audit_bank_prompts(registry,spec,runs):
    banks={k:v for k,v in registry.items() if v['kind']=='bank'}
    if not banks or set(runs)!=set(banks):raise ValueError('one explicit run for every frozen bank required')
    evidence={};eligible=[];dropped={};paths={}
    def read(path,rows=False):
        path=Path(path).resolve();evidence[str(path)]=sha256(path)
        return [json.loads(s) for s in path.read_text().splitlines() if s.strip()] if rows else json.loads(path.read_text())
    for name,entry in sorted(banks.items()):
        root=Path(runs[name]).resolve()
        if (root/'failure.json').exists():raise ValueError('failed run is not completed D-28 evidence')
        cfg=read(root/'config.json')
        if (cfg.get('derivative_id')!=name or cfg.get('revision')!=spec['base_revision'] or
            cfg.get('pool_sha256')!=sha256(spec['staging_manifest']) or cfg.get('count')!=500 or
            cfg.get('split')!='training' or cfg.get('acceptance_only') is not False or
            cfg.get('acceptance_smoke') is not False or cfg.get('engine_version')!='0.31.0'):
            raise ValueError('bank generation identity, pin, or production settings differ')
        for f in ('adapter_config.json','adapter_model.safetensors'):
            if cfg.get('adapter_sha256',{}).get(f)!=entry['files_sha256'][f]:
                raise ValueError('bank generation adapter hash differs')
        complete=(root/'prompts.jsonl').is_file()
        rows=read(root/('prompts.jsonl' if complete else 'partial_queries.jsonl'),True)
        if rows:checked_queries(rows,'bank training')
        if any(q.get('derivative_id')!=name or q.get('revision')!=entry['revision'] for q in rows):
            raise ValueError('bank query origin or revision differs')
        report=read(root/'filter_report.json')
        if complete:
            if len(rows)!=500 or report.get('kept',0)<500:raise ValueError('complete bank requires500 valid queries')
            if (root/'results.json').exists():
                result=read(root/'results.json')
                if result.get('status')!='complete' or result.get('n')!=500 or result.get('training_ready') is not True:
                    raise ValueError('bank completion evidence differs')
            eligible.append(name);paths[name]=str(root/'prompts.jsonl')
        else:
            result=read(root/'results.json');rounds=read(root/'rounds.jsonl',True)
            if (cfg.get('d23_oversampling') is not True or cfg.get('candidate_budget')!=6400 or
                result.get('status')!='shortfall' or result.get('requested')!=500 or
                result.get('training_ready') is not False or result.get('acceptance_only') is not False or
                result.get('engine_version')!='0.31.0' or not 0<=len(rows)<500 or
                result.get('n')!=len(rows) or result.get('valid_before_truncation')!=len(rows) or
                result.get('attempted')!=6400 or result.get('candidate_budget')!=6400 or
                report.get('attempted')!=6400 or report.get('budget')!=6400 or report.get('kept')!=len(rows) or
                not rounds or rounds[-1]!=report):
                raise ValueError('D-28 exclusion requires a completed6400-candidate shortfall')
            raw=read(root/'raw_queries.jsonl',True)
            if len(raw)!=6400 or [r.get('attempt_index') for r in raw]!=list(range(6400)):
                raise ValueError('shortfall raw attempts incomplete')
            dropped[name]=dict(n=len(rows),attempted=6400,run=str(root),reason='D-28 exhausted training prompt budget')
    return dict(schema='followspec_D28_bank_eligibility_v1',eligible_bank=eligible,dropped_bank=dropped,
                prompt_paths=paths,n_original_bank=len(banks),n_eligible_bank=len(eligible),
                evidence_sha256=evidence,mixture_policy_applied=False)
