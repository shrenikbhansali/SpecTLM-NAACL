from followspec.stress_quality import code_pass,math_answer,compare


def test_number_extraction_and_paired_quality():
    assert math_answer('work... #### 1,250')=='1250'
    assert math_answer('Answer: 2.5')=='2.5'
    r=[dict(prompt_id='p',reference='#### 3',domain='math')]
    out=compare(r,[dict(prompt_id='p',completion='3')],[dict(prompt_id='p',completion='4')])
    assert out['parent_score']==1 and out['child_score']==0 and out['delta']==-1 and out['n']==1


def test_sandbox_runs_correct_incorrect_timeout_and_cannot_read_workspace(tmp_path):
    assert code_pass('def f(): return 2',['assert f()==2'])['passed']
    assert not code_pass('def f(): return 1',['assert f()==2'])['passed']
    assert not code_pass('raise SystemExit(0)',['assert True'])['passed']
    p=tmp_path/'secret';p.write_text('not exposed')
    assert not code_pass('open('+repr(str(p))+').read()',['assert True'])['passed']
    assert not code_pass('while True: pass',['assert True'])['passed']
