"""D54 finite run-list completion evidence; never promotes scientific results."""
import json
from collections import Counter
from pathlib import Path
from ops.track_t import WS

LEVEL={**{x:'P0' for x in ['E8','E9','E10a','E10b','E12','E14']},**{x:'P1' for x in ['E11','E13','E16','E17']},'E15':'P2'}
EXPECTED={'P0':270,'P1':106,'P2':8}


def progress(snapshot):
    roots=[WS/'artifacts'/s for s in ['REV2_E8_20261010_0425','REV2_data_20261010_0430','REV2_panels_20261010_0430_v2','REV2_E10a_20261010_0430','REV2_E10b_20261010_0430','REV2_E12_controls_20261010_0445','REV2_P1_20261010_0437','REV2_E11_20261010_0437','REV2_E15_20261010_0445']]
    follow=WS/'artifacts/REV2_followups_20261010_0500';roots+=sorted(follow.glob('training-t*'))+[follow/'qwen-repair-timing']
    rows={}
    for root in roots:
        for p in [root/'plan.json']+list(root.glob('eval-plan-*.json')):
            if not p.exists():continue
            for row in json.loads(p.read_text()):
                name=row['name'];assert name not in rows,'duplicate planned job '+name;rows[name]=row
    launched={};finished={}
    for line in (WS/'artifacts/M2_D28_20261006/response_queue.log').read_text().splitlines():
        e=json.loads(line)
        if e['event']=='launched':launched[e['out_dir']]=e['name']
        if e['event']=='finished':finished[launched[e['out_dir']]]=str(e['exit'])
    levels={k:dict(expected=EXPECTED[k],planned=0,completed=0,failed=[],pending=[],analysis_complete=False,ready_for_review=False) for k in EXPECTED}
    for name,row in rows.items():
        lev=levels[LEVEL[row['experiment']]];lev['planned']+=1
        if name in finished and finished[name]!='0':lev['failed'].append(name)
        elif finished.get(name)=='0' and (Path(row['run_dir'])/'results.json').exists():lev['completed']+=1
        else:lev['pending'].append(name)
    acceptance=Counter(r['experiment'] for r in json.loads((snapshot/'acceptance/results.json').read_text())['records'])
    timing=Counter(r['experiment'] for r in json.loads((snapshot/'timing/results.json').read_text())['records'])
    e8=json.loads((snapshot/'E8/results.json').read_text());e16=json.loads((snapshot/'E16/results.json').read_text());data=json.loads((snapshot/'data/results.json').read_text())
    levels['P0']['analysis_complete']=(len(e8['records'])==12 and not e8['pending'] and all(acceptance[k]==v for k,v in {'E9':40,'E12':7,'E14':6}.items()) and all(timing[k]==v for k,v in {'E10a':12,'E10b':32,'E12':14}.items()) and len(data['records'])==3)
    levels['P1']['analysis_complete']=(acceptance['E13']==3 and acceptance['E17']==12 and timing['E11']==32 and len(e16['records'])==4)
    levels['P2']['analysis_complete']=(acceptance['E15']==6 and (WS/'artifacts/REV2_diagnostics_20261010_0445/E18-feasibility.json').exists())
    for r in levels.values():r['ready_for_review']=(r['planned']==r['expected']==r['completed'] and not r['failed'] and r['analysis_complete'])
    return dict(levels=levels,acceptance_rows=dict(acceptance),timing_rows=dict(timing),scope='D54 mandatory jobs including prerequisite data, training/profiles, frozen acceptance and repeated timing; E18 pinned-engine infeasibility separately recorded; no scientific promotion')


def ping_board(workspace,level,state,evidence,stamp):
    """Only own row goes to review; owner promotion/gates never changed."""
    if not state['ready_for_review']:return False
    board=workspace/'MASTER.md';original=board.read_text();rows=original.splitlines();indices=[i for i,r in enumerate(rows) if r.startswith('| REV2-'+level+' |')]
    if len(indices)!=1:raise ValueError('own REV2 row missing/ambiguous')
    i=indices[0];cells=rows[i].split('|')
    if cells[7].strip() in ['review','done']:return False
    if cells[7].strip()!='in progress' or 'codex-1' not in cells[8]:raise ValueError('unexpected task ownership/status')
    cells[7]=' review ';cells[8]=' codex-1 / '+stamp+' ';cells[9]=' [results](reports/REV2-results-20261010.md), [completion evidence]('+evidence+'); all mandatory runs successful and independently reduced; pilot, no owner promotion '
    rows[i]='|'.join(cells);tmp=board.with_suffix('.md.rev2-ping');tmp.write_text('\n'.join(rows)+'\n');tmp.replace(board)
    message=f'\n## {stamp} — codex-1 — Completion ping REV2-{level}\n\n{state["completed"]}/{state["expected"]} mandatory jobs completed successfully; required raw counter/timing/resource analyses are present. Board moved to review, numbers remain pilot. Completion evidence: {evidence}. Nulls retained; paper unchanged.\n'
    with (workspace/'notes/REV2.md').open('a') as f:f.write(message)
    with (workspace/'ledger/EXP-ATL-027.md').open('a') as f:f.write(message)
    return True
