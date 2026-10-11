import pytest
from followspec.rev4_recovery import active_attempts, retry_job

def row(name='old', **kw):
 return dict(name=name,run_dir='/'+name,experiment='Y6',kind='train',target=0,arm='fc',seed=0,data_label='generic64k',**kw)

def test_replacement_requires_failure_and_matching_design():
 old=row();new=row('new',replaces_job='old')
 assert active_attempts([old,new],{'old':'1'})==[new]
 for exits in [{},{'old':'0'}]:
  with pytest.raises(ValueError):active_attempts([old,new],exits)
 with pytest.raises(ValueError):active_attempts([old,new|{'seed':1}],{'old':'1'})
 with pytest.raises(ValueError):active_attempts([old,new,row('new2',replaces_job='old')],{'old':'1'})

def test_retry_changes_only_name_and_output_paths(tmp_path):
 source=dict(name='old',args=['--tag','old','--code-repo','/pinned','--','python','--output','/old','--shared-export-root','/shared','--seed','0','--data','/data'])
 job,r=retry_job(source,row(),tmp_path)
 assert source['name']=='old' and source['args'][1]=='old'
 assert job['args']==['--tag','old-diskretry1','--code-repo','/pinned','--','python','--output',str(tmp_path/'old-diskretry1'),'--shared-export-root','/shared','--seed','0','--data','/data']
 assert r['replaces_job']=='old'

def test_retry_preserves_timing_strata(tmp_path):
 source=dict(name='old',args=['--tag','old','--','python','--output','/old','--batch-size','1'])
 r=row()|dict(kind='timing',workload='speed128',batch=1,replicate=2)
 _,r2=retry_job(source,r,tmp_path)
 assert all(r2[k]==r[k] for k in ['kind','workload','batch','replicate'])
