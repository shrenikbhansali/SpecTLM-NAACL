"""D-28: only exhausted, pinned training shortfalls permit a bank exclusion."""
import json
from pathlib import Path
import pytest
from atlas.run_cell import sha256
from followspec.production_pipeline import jsonl,write_new
from followspec.production import allocate_queries
from followspec.tests.test_production import banks,queries


def fixture(tmp_path,short=False):
    staging=tmp_path/'staging.csv';staging.write_text('pinned pool')
    spec=dict(base_revision='a'*40,staging_manifest=str(staging))
    reg={'child':dict(kind='bank',revision='b'*40,files_sha256={'adapter_model.safetensors':'weights','adapter_config.json':'config'})}
    root=tmp_path/'run';root.mkdir()
    cfg=dict(derivative_id='child',revision='a'*40,pool_sha256=sha256(staging),count=500,
        split='training',acceptance_only=False,acceptance_smoke=False,engine_version='0.31.0',
        adapter_sha256=reg['child']['files_sha256'],d23_oversampling=short,candidate_budget=6400 if short else 1280)
    write_new(root/'config.json',cfg)
    n=3 if short else 500
    rows=[q|dict(derivative_id='child',revision='b'*40) for q in queries(n,'mag')]
    jsonl(root/('partial_queries.jsonl' if short else 'prompts.jsonl'),rows)
    report=dict(kept=n)
    if short:
        report.update(attempted=6400,budget=6400)
        jsonl(root/'raw_queries.jsonl',[dict(attempt_index=i) for i in range(6400)])
        jsonl(root/'rounds.jsonl',[report])
        write_new(root/'results.json',dict(status='shortfall',requested=500,n=n,valid_before_truncation=n,
            attempted=6400,candidate_budget=6400,training_ready=False,acceptance_only=False,engine_version='0.31.0'))
    write_new(root/'filter_report.json',report)
    return reg,spec,{'child':str(root)}


def test_accepts_legacy_complete_and_exhausted_shortfall_without_mutating_sources(tmp_path):
    from followspec.bank_eligibility import audit_bank_prompts
    reg,spec,runs=fixture(tmp_path)
    result=audit_bank_prompts(reg,spec,runs)
    assert result['eligible_bank']==['child'] and result['dropped_bank']=={}
    other=tmp_path/'short';other.mkdir();reg,spec,runs=fixture(other,True)
    before={p:p.read_bytes() for p in other.rglob('*') if p.is_file()}
    result=audit_bank_prompts(reg,spec,runs)
    assert result['eligible_bank']==[] and result['dropped_bank']['child']['n']==3
    assert all(p.read_bytes()==b for p,b in before.items())
    assert str(other/'run'/'raw_queries.jsonl') in result['evidence_sha256']


@pytest.mark.parametrize('mutation',['budget','missing','failed','pin','partial','incomplete_raw','duplicate','smoke','unknown'])
def test_refuses_unproven_or_corrupted_drop(tmp_path,mutation):
    from followspec.bank_eligibility import audit_bank_prompts
    reg,spec,runs=fixture(tmp_path,True);root=Path(runs['child'])
    if mutation=='budget':
        p=root/'results.json';r=json.loads(p.read_text());r['attempted']=1280;p.write_text(json.dumps(r))
    elif mutation=='missing':(root/'results.json').unlink()
    elif mutation=='failed':write_new(root/'failure.json',dict(error='crashed'))
    elif mutation in ('pin','smoke'):
        p=root/'config.json';c=json.loads(p.read_text());c['revision' if mutation=='pin' else 'acceptance_only']='c'*40 if mutation=='pin' else True;p.write_text(json.dumps(c))
    elif mutation=='partial':jsonl(root/'prompts.jsonl',queries(3))
    elif mutation=='incomplete_raw':(root/'raw_queries.jsonl').write_text('{}\n')
    elif mutation=='duplicate':(root/'partial_queries.jsonl').write_text((json.dumps(queries(1)[0])+'\n')*3)
    else:runs['unknown']=runs['child']
    with pytest.raises((ValueError,FileNotFoundError)):audit_bank_prompts(reg,spec,runs)


def test_d28_quotas_use_only_explicit_eligible_targets_and_keep_controls_matched():
    registry=banks()|{f'm{i:02}':dict(kind='mixture') for i in range(30)}
    eligible=sorted(banks(24));targets=eligible+[f'm{i:02}' for i in range(30)]
    mag={k:queries(500,k) for k in targets}
    a=allocate_queries(registry,queries(20000),mag,queries(4,'val'),seed=101,forbidden=[],eligible_bank=eligible)
    assert a['counts']['child']['MVD']==24000 and a['counts']['fs_per_target']==444
    assert set(a['arm_ids']['MVD'])==set(eligible) and set(a['arm_ids']['FS'])==set(targets)
    assert a['counts']['parent']['MVD']==8000
    for k in eligible:assert set(a['arm_ids']['FS'][k])<=set(a['arm_ids']['MVD'][k])
    for invalid in ([],eligible+[eligible[0]],eligible+['unknown']):
        with pytest.raises(ValueError):allocate_queries(registry,queries(20000),mag,queries(4,'val'),seed=101,forbidden=[],eligible_bank=invalid)
