"""W1 full acceptance: compile both official review templates and count pages."""
import os
from pathlib import Path
import re
import subprocess
import pytest

ROOT=Path(__file__).resolve().parents[1]
@pytest.mark.parametrize('framing',['method','atlas'])
def test_review_paper_compiles(framing,tmp_path):
    source=ROOT/framing/'main.tex'
    assert source.exists()
    env=os.environ.copy();env['TEXINPUTS']=str(ROOT/'style')+os.pathsep+env.get('TEXINPUTS','')
    result=subprocess.run(['latexmk','-pdf','-interaction=nonstopmode','-halt-on-error',f'-outdir={tmp_path}','main.tex'],cwd=source.parent,env=env,text=True,capture_output=True)
    assert result.returncode==0,result.stdout+result.stderr
    log=(tmp_path/'main.log').read_text()
    assert not re.search(r'undefined|LaTeX Error|Emergency stop',log,re.I),log
    assert '\\usepackage[review]{acl}' in source.read_text()
    assert '\\section*{Limitations}' in source.read_text()
    pages=re.search(r'Output written on .*?\((\d+) pages?',log,re.S)
    assert pages,log
    print(f'{framing}: {pages.group(1)} pages')
