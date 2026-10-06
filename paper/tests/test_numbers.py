import csv
import json
from pathlib import Path
import pytest
from paper.verify_numbers import generate, verify, hardcoded_numbers


def fixture(root):
    run=root/'run-a';run.mkdir()
    (run/'config.json').write_text('{"engine_version":"0.31.0"}')
    (run/'results.json').write_text('{"n":10,"value":1.234567}')
    ledger=root/'EXP-ATL-999.md'
    ledger.write_text(f'''### EXP-ATL-999
**Synthetic test only**
**Landed:** 2026-10-05, checker acceptance
**Status:** pilot
**What / why.** Synthetic fixture.
**New in this experiment.** Checker exercise.
**Artifacts.** `{run}`
**Config.** Synthetic.
**Results.** Synthetic.
**Caveats.** Not a research result.
''')
    source=root/'aggregate.csv'
    with source.open('w',newline='') as f:
        w=csv.DictWriter(f,fieldnames=['arm','value','run_id']);w.writeheader();w.writerow(dict(arm='test',value='1.234567',run_id='run-a'))
    result=root/'results.tex';result.write_text('Value: \\ResultValue. See \\ref{fig:2} and \\cite{author2026}.\n')
    manifest=dict(synthetic=True,numbers=[dict(macro='ResultValue',source=str(source),where={'arm':'test'},column='value',format='.6g')],
        exhibits=[],runs={'run-a':dict(artifact=str(run),ledger=str(ledger))},results=[str(result)])
    path=root/'manifest.json';path.write_text(json.dumps(manifest))
    return path,manifest


def test_generate_verify_and_deliberately_altered_number(tmp_path):
    path,m=fixture(tmp_path);out=tmp_path/'generated';generate(path,out,allow_synthetic=True)
    assert verify(path,out,allow_synthetic=True)['passed']
    numbers=out/'numbers.tex';numbers.write_text(numbers.read_text().replace('1.23457','1.23458'))
    r=verify(path,out,allow_synthetic=True)
    assert not r['passed'] and any('ResultValue' in x for x in r['errors'])


def test_source_mutation_missing_ledger_and_invalid_status_are_caught(tmp_path):
    path,m=fixture(tmp_path);out=tmp_path/'generated';generate(path,out,allow_synthetic=True)
    src=Path(m['numbers'][0]['source']);src.write_text(src.read_text().replace('1.234567','1.2345671'))
    assert not verify(path,out,allow_synthetic=True)['passed']  # even below print precision
    ledger=Path(m['runs']['run-a']['ledger']);ledger.write_text(ledger.read_text().replace('pilot','invalid'))
    with pytest.raises(ValueError,match='invalid'):generate(path,tmp_path/'invalid',allow_synthetic=True)
    ledger.unlink()
    with pytest.raises((ValueError,FileNotFoundError)):generate(path,tmp_path/'missing',allow_synthetic=True)


def test_unique_selector_and_no_untracked_macros(tmp_path):
    path,m=fixture(tmp_path);out=tmp_path/'generated';generate(path,out,allow_synthetic=True)
    with (out/'numbers.tex').open('a') as f:f.write('\\newcommand{\\Extra}{99}\n')
    assert not verify(path,out,allow_synthetic=True)['passed']
    src=Path(m['numbers'][0]['source'])
    with src.open('a') as f:f.write('test,1.234567,run-a\n')
    with pytest.raises(ValueError,match='exactly one'):generate(path,tmp_path/'duplicate',allow_synthetic=True)


def test_hardcoded_results_and_recursive_inputs_with_comments_refs_and_percent(tmp_path):
    path,m=fixture(tmp_path);out=tmp_path/'generated';generate(path,out,allow_synthetic=True)
    result=Path(m['results'][0]);child=tmp_path/'child.tex';child.write_text('Gain 12.5\\% (n=10). % 999 ignored\n')
    result.write_text('\\input{child}\n')
    r=verify(path,out,allow_synthetic=True)
    assert not r['passed'] and any('12.5' in x for x in r['errors']) and any('10' in x for x in r['errors'])
    assert hardcoded_numbers('\\ref{sec:4} \\citep[p.~2]{smith2026} % 999\n')==[]


def test_synthetic_and_pilot_require_explicit_modes(tmp_path):
    path,m=fixture(tmp_path)
    with pytest.raises(ValueError,match='synthetic'):generate(path,tmp_path/'not-allowed')
    generate(path,tmp_path/'allowed',allow_synthetic=True)
    assert not verify(path,tmp_path/'allowed',allow_synthetic=True,require_paper_grade=True)['passed']


def test_exhibit_macro_is_rederived_from_original_csv_not_sidecar_value(tmp_path):
    from paper.exhibits import render
    path,m=fixture(tmp_path)
    side=render(dict(id='atlas_table1',source=m['numbers'][0]['source'],kind='table',columns=['arm','value'],synthetic=True),tmp_path/'exhibit')
    m['exhibits']=[str(tmp_path/'exhibit/atlas_table1.json')];path.write_text(json.dumps(m))
    out=tmp_path/'generated';generate(path,out,allow_synthetic=True)
    assert verify(path,out,allow_synthetic=True)['n_macros']==2
    sc=Path(m['exhibits'][0]);data=json.loads(sc.read_text());data['table_macros'][0]['value']=999;sc.write_text(json.dumps(data))
    assert not verify(path,out,allow_synthetic=True)['passed']
