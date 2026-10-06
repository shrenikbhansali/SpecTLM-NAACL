import csv
import json
import pytest
from paper.exhibits import render, CATALOG


def make_source(path):
    with path.open('w',newline='') as f:
        w=csv.DictWriter(f,fieldnames=['x','y','series','low','high','diagnostic','run_ids']);w.writeheader()
        for i in range(6):w.writerow(dict(x=str(i%3),y=str(1+i/10),series='A' if i<3 else 'B',low=str(.9+i/10),high=str(1.1+i/10),diagnostic='true',run_ids=json.dumps([f'synthetic-run-{i}'])))


@pytest.mark.parametrize('kind',['points','line','distribution','table'])
def test_two_regenerations_are_byte_identical_and_trace_every_row(tmp_path,kind):
    src=tmp_path/'input.csv';make_source(src)
    spec=dict(id='acceptance',kind=kind,source=str(src),x='x',y='y',series='series',low='low',high='high',columns=['x','y','series'],xlabel='x',ylabel='y',synthetic=True)
    for name in ['one','two']:render(spec,tmp_path/name)
    one={p.name:p.read_bytes() for p in (tmp_path/'one').iterdir()};two={p.name:p.read_bytes() for p in (tmp_path/'two').iterdir()}
    assert one==two and 'acceptance.pdf' in one and 'acceptance.png' in one
    side=json.loads(one['acceptance.json'])
    assert set(side['source_run_ids'])=={f'synthetic-run-{i}' for i in range(6)}
    assert len(side['data_rows'])==6 and all(r['run_ids'] for r in side['data_rows'])
    if kind=='table':
        assert b'newcommand' in one['acceptance.numbers.tex']
        assert b'1.1' not in one['acceptance.tex']


def test_missing_provenance_nonfinite_and_unlabeled_transport_are_rejected(tmp_path):
    src=tmp_path/'input.csv';make_source(src)
    spec=dict(id='test',kind='points',source=str(src),x='x',y='y',series='series',synthetic=True)
    content=src.read_text();src.write_text(content.replace('synthetic-run-0',''))
    with pytest.raises(ValueError,match='run'):render(spec,tmp_path/'bad')
    src.write_text(content.replace('1.0,','nan,',1))
    with pytest.raises(ValueError):render(spec,tmp_path/'nonfinite')
    src.write_text(content.replace('true','false'))
    with pytest.raises(ValueError,match='diagnostic'):render(spec|dict(transport=True),tmp_path/'transport')


def test_catalog_covers_both_framings_and_appendices():
    expected={f'{framing}_figure{i}' for framing in ['method','atlas'] for i in range(1,5)}
    expected|={f'{framing}_table{i}' for framing in ['method','atlas'] for i in [1,2]}
    expected|={'appendix_ablations','appendix_generality','appendix_eagle31','appendix_speedups','appendix_derivatives','appendix_ledger_children'}
    assert set(CATALOG)==expected
