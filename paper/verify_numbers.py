"""Generate numeric macros and check CSV → artifact → ledger provenance.

This validates transcription and provenance, not scientific claims or promotion.
Only the owner can promote a ledger entry to paper-grade.
"""
import argparse
import csv
import hashlib
import json
import math
from pathlib import Path
import re

MACRO=re.compile(r'\\newcommand\{\\([A-Za-z]+)\}\{([^{}]+)\}')
NUMBER=re.compile(r'(?<![A-Za-z])[-+]?(?:\d+(?:\.\d*)?|\.\d+)(?:[eE][-+]?\d+)?')


def digest(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def strip_comments(text):
    # A percent is escaped iff preceded by an odd number of backslashes.
    lines=[]
    for line in text.splitlines():
        for i,c in enumerate(line):
            if c=='%' and (i-len(line[:i].rstrip('\\')))%2==0:
                line=line[:i];break
        lines.append(line)
    return '\n'.join(lines)


def hardcoded_numbers(text):
    text=strip_comments(text)
    # Citation/reference identifiers and layout paths are not empirical values.
    text=re.sub(r'\\(?:cite\w*|ref|eqref|autoref|label|input|include|includegraphics)\*?(?:\[[^\]]*\])*\{[^{}]*\}',lambda m:' '*(len(m[0])),text)
    return [m.group() for m in NUMBER.finditer(text)]


def resolve(value,base):
    p=Path(value);return p.resolve() if p.is_absolute() else (base/p).resolve()


def run_ids(row):
    values=json.loads(row['run_ids']) if row.get('run_ids') else [row.get('run_id')]
    if not isinstance(values,list) or not values or any(not isinstance(x,str) or not x.strip() for x in values):
        raise ValueError('source row needs run IDs')
    return sorted(set(values))


def expanded_paths(text):
    for token in re.findall(r'`([^`\n]+)`',text):
        todo=[token]
        while todo:
            p=todo.pop();m=re.search(r'\{([^{}]+)\}',p)
            if m:todo.extend(p[:m.start()]+v+p[m.end():] for v in m[1].split(','))
            else:yield p.rstrip('/')


def ledger_record(run_id,spec,base,require_paper_grade):
    artifact=resolve(spec['artifact'],base);ledger=resolve(spec['ledger'],base)
    if not artifact.is_dir():raise ValueError(f'{run_id}: missing artifact directory')
    text=ledger.read_text()
    if not re.search(r'EXP-ATL-\d+',text):raise ValueError('assigned EXP-ATL ledger ID required')
    for field in ('Landed','Status','What / why','New in this experiment','Artifacts','Config','Results','Caveats'):
        if not re.search(r'\*\*'+re.escape(field)+r'(?:[.:]?\*\*|\*\*[.:])',text,re.I):
            raise ValueError(f'{run_id}: ledger field missing: {field}')
    status=re.search(r'\*\*Status:?\*\*\s*:?\s*(paper-grade|pilot|diagnostic|superseded|invalid)',text,re.I)
    if not status:raise ValueError(f'{run_id}: explicit ledger status required')
    status=status[1].lower()
    if status in ('invalid','superseded'):raise ValueError(f'{run_id}: ledger is {status}')
    if require_paper_grade and status!='paper-grade':raise ValueError(f'{run_id}: ledger is {status}, not paper-grade')
    # Do not accept a fabricated run→ledger mapping that the entry never cites.
    cited={resolve(p,base) for p in expanded_paths(text) if not p.startswith('…')}
    if artifact not in cited:raise ValueError(f'{run_id}: ledger does not cite exact artifact path (brace lists supported)')
    files={name:digest(artifact/name) for name in ('config.json','results.json')}
    if (artifact/'failure.json').exists():raise ValueError(f'{run_id}: failed artifact')
    for name in ('config.json','results.json'):json.loads((artifact/name).read_text())
    return dict(run_id=run_id,artifact=str(artifact),ledger=str(ledger),ledger_sha256=digest(ledger),status=status,artifact_hashes=files)


def derive(manifest_path,allow_synthetic=False,require_paper_grade=False):
    path=Path(manifest_path).resolve();base=path.parent;m=json.loads(path.read_text())
    if type(m.get('synthetic')) is not bool:raise ValueError('explicit synthetic boolean required')
    if m['synthetic'] and not allow_synthetic:raise ValueError('synthetic acceptance requires --allow-synthetic')
    specs=list(m.get('numbers',[]));sidecar_hashes={}
    for rel in m.get('exhibits',[]):
        p=resolve(rel,base);sc=json.loads(p.read_text());source=resolve(sc['spec']['source'],base)
        if sc['spec']['synthetic']!=m['synthetic']:raise ValueError('mixed synthetic/real sources')
        if digest(source)!=sc['source_sha256']:raise ValueError('exhibit CSV hash changed')
        sidecar_hashes[str(p)]=digest(p)
        for macro in sc['table_macros']:
            specs.append(dict(macro=macro['name'],source=str(source),source_row=macro['source_row'],column=macro['column'],format='.6g',exhibit_expected=macro))
    names=set();records=[];run_records={}
    for spec in specs:
        name=spec['macro']
        if not re.fullmatch('[A-Za-z]+',name) or name in names:raise ValueError('invalid/duplicate macro name')
        names.add(name);source=resolve(spec['source'],base)
        with source.open(newline='') as f:rows=list(csv.DictReader(f))
        if 'source_row' in spec:
            idx=spec['source_row']-2
            selected=[(idx,rows[idx])] if 0<=idx<len(rows) else []
        else:
            where=spec.get('where')
            if not where:raise ValueError('explicit row selector required')
            selected=[(i,r) for i,r in enumerate(rows) if all(r.get(k)==str(v) for k,v in where.items())]
        if len(selected)!=1:raise ValueError(f'{name}: selector must match exactly one row')
        i,row=selected[0];raw=row[spec['column']];value=float(raw)
        if not math.isfinite(value):raise ValueError('nonfinite paper value')
        fmt=spec.get('format','.6g')
        if not re.fullmatch(r'\.(?:[0-9]|1[0-2])[fg]',fmt):raise ValueError('explicit 0–12 digit f/g format required')
        formatted=format(value,fmt);ids=run_ids(row)
        expected=spec.get('exhibit_expected')
        if expected and (expected['value']!=value or expected['formatted']!=formatted or expected['run_ids']!=ids):
            raise ValueError(f'{name}: exhibit sidecar differs from source CSV')
        for ident in ids:
            if ident not in m['runs']:raise ValueError(f'{ident}: no ledger mapping')
            if ident not in run_records:run_records[ident]=ledger_record(ident,m['runs'][ident],base,require_paper_grade)
        records.append(dict(macro=name,value=value,raw=raw,formatted=formatted,source=str(source),source_sha256=digest(source),source_row=i+2,column=spec['column'],format=fmt,run_ids=ids))
    trace=dict(synthetic=m['synthetic'],manifest_sha256=digest(path),numbers=records,runs=run_records,exhibit_hashes=sidecar_hashes,
               scope='transcription and provenance only; no scientific validation or ledger promotion')
    return m,trace


def generate(manifest_path,output,allow_synthetic=False):
    _,trace=derive(manifest_path,allow_synthetic)
    out=Path(output);out.mkdir(parents=True,exist_ok=False)
    header='% Generated from explicit aggregate cells; verify with paper.verify_numbers.\n'
    if trace['synthetic']:header+='% SYNTHETIC ACCEPTANCE ONLY — never include in paper.\n'
    (out/'numbers.tex').write_text(header+''.join('\\newcommand{\\'+r['macro']+'}{'+r['formatted']+'}\n' for r in trace['numbers']))
    (out/'numbers.trace.json').write_text(json.dumps(trace,indent=2,sort_keys=True,allow_nan=False)+'\n')
    return trace


def scan_results(paths,base,numbers_path,known):
    errors=[];visited=set()
    def visit(path):
        if path==numbers_path or path in visited:return
        visited.add(path);text=strip_comments(path.read_text())
        if re.search(r'\\(?:newcommand|renewcommand|providecommand|def|let)\b',text):errors.append(f'{path}: macro definition/override in results')
        for line_no,line in enumerate(text.splitlines(),1):
            for value in hardcoded_numbers(line):errors.append(f'{path}:{line_no}: hard-coded number {value}')
            for name in re.findall(r'\\((?:Result|Exhibit)[A-Za-z]+)',line):
                if name not in known:errors.append(f'{path}:{line_no}: undefined numeric macro {name}')
        for rel in re.findall(r'\\(?:input|include)\{([^{}]+)\}',text):
            child=resolve(rel,path.parent)
            if not child.suffix:child=child.with_suffix('.tex')
            visit(child)
    for p in paths:visit(resolve(p,base))
    return errors,sorted(map(str,visited))


def verify(manifest_path,output,allow_synthetic=False,require_paper_grade=False):
    errors=[];trace=None;scanned=[]
    try:
        m,trace=derive(manifest_path,allow_synthetic,require_paper_grade)
        out=Path(output);numbers=out/'numbers.tex';text=strip_comments(numbers.read_text())
        got={};matches=list(MACRO.finditer(text))
        for match in matches:
            if match[1] in got:errors.append(f'duplicate macro {match[1]}')
            got[match[1]]=match[2]
        if MACRO.sub('',text).strip():errors.append('unsupported content in numeric macro file')
        want={r['macro']:r['formatted'] for r in trace['numbers']}
        for key in sorted(set(want)|set(got)):
            if want.get(key)!=got.get(key):errors.append(f'{key}: macro={got.get(key)!r}, CSV={want.get(key)!r}')
        if json.loads((out/'numbers.trace.json').read_text())!=trace:errors.append('provenance trace changed (source, manifest, exhibit, artifact or ledger)')
        if not m.get('results'):errors.append('explicit results paths required for hard-coded-number scan')
        issues,scanned=scan_results(m.get('results',[]),Path(manifest_path).resolve().parent,numbers.resolve(),set(want));errors.extend(issues)
    except (ValueError,KeyError,OSError,TypeError) as exc:errors.append(str(exc))
    return dict(passed=not errors,errors=errors,n_macros=len(trace['numbers']) if trace else 0,scanned_results=scanned,
        synthetic=trace['synthetic'] if trace else None,require_paper_grade=require_paper_grade,
        caveat='Checks explicit result sources only. Empty skeleton has no empirical evidence. Pilot/diagnostic status is not promotion.')


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('command',choices=['generate','verify']);p.add_argument('--manifest',required=True)
    p.add_argument('--output',required=True);p.add_argument('--allow-synthetic',action='store_true');p.add_argument('--require-paper-grade',action='store_true');p.add_argument('--report');a=p.parse_args()
    if a.command=='generate':
        if a.require_paper_grade:p.error('--require-paper-grade is a verification mode')
        report=generate(a.manifest,a.output,a.allow_synthetic)
    else:report=verify(a.manifest,a.output,a.allow_synthetic,a.require_paper_grade)
    encoded=json.dumps(report,indent=2,sort_keys=True,allow_nan=False)+'\n'
    if a.report:
        with Path(a.report).open('x') as f:f.write(encoded)
    print(encoded)
    if a.command=='verify' and not report['passed']:raise SystemExit(1)

if __name__=='__main__':main()
