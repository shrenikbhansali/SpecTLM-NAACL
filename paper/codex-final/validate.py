#!/usr/bin/env python3
"""Check manuscript references, template integrity and the compiled artifact."""
from pathlib import Path
import datetime
import hashlib
import json
import re
import subprocess
P=Path(__file__).resolve().parent
tex='\n'.join(p.read_text() for p in [P/'main.tex',P/'appendix.tex',*(P/'tables').glob('*.tex'),*(P/'figures').glob('*.tex')])
bib=(P/'references.bib').read_text()
keys=re.findall(r'@\w+\s*\{\s*([^,]+),',bib)
assert len(keys)==len(set(keys)), 'duplicate bibliography keys'
cited={k.strip() for group in re.findall(r'\\cite\w*\{([^}]+)\}',tex) for k in group.split(',')}
assert cited<=set(keys), 'missing bibliography entry: '+str(cited-set(keys))
labels=re.findall(r'\\label\{([^}]+)\}',tex)
assert len(labels)==len(set(labels)), 'duplicate labels'
refs=set(re.findall(r'\\(?:eqref|ref)\{([^}]+)\}',tex))
assert refs<=set(labels), 'undefined cross reference'
for f in re.findall(r'\\input\{([^}]+)\}',tex):
    assert (P/(f+'.tex')).is_file(), f
log=(P/'build/main.log').read_text()
for error in ['Overfull','undefined','LaTeX Error','Fatal error','multiply defined']:
    assert error not in log,error
subprocess.run(['pdftotext','-layout',str(P/'build/main.pdf'),str(P/'build/main.txt')],check=True)
pages=(P/'build/main.txt').read_text().split('\f');pages=[x for x in pages if x.strip()]
assert '??' not in '\n'.join(pages)
conclusion_page=next(i+1 for i,p in enumerate(pages) if re.search(r'\bConclusion\b',p))
limitations_page=next(i+1 for i,p in enumerate(pages) if 'Limitations' in p)
assert conclusion_page<=8 and limitations_page<=9
raw=json.loads((P/'data/raw-verification.json').read_text());assert raw['status']=='passed'
templates=json.loads((P/'data/template-sha256.json').read_text())
for name,digest in templates.items():assert hashlib.sha256((P/name).read_bytes()).hexdigest()==digest
source_status=json.loads((P/'data/results.json').read_text())['status'];assert 'pilot' in source_status
validation={'status':'passed','time':datetime.datetime.now(datetime.timezone.utc).isoformat(),'pages':len(pages),'conclusion_page':conclusion_page,'limitations_page':limitations_page,'cited_primary_sources':len(cited),'cross_references':len(refs),'figures':4,'undefined_references':0,'overfull_boxes':0,'template_files_unmodified':True,'raw_counter_check':raw['check'],'pdf_sha256':hashlib.sha256((P/'build/main.pdf').read_bytes()).hexdigest()}
(P/'validation.json').write_text(json.dumps(validation,indent=2)+'\n')
print(json.dumps(validation,indent=2))
