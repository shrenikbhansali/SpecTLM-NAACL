import json
from types import SimpleNamespace as NS
import pytest
from atlas.generate_magpie import candidate_budget,collect_queries,finish_generation,managed_engine


@pytest.fixture(autouse=True)
def unit_language_detector(monkeypatch):
    # Runtime environment has the pinned language detector; unit tests isolate IO.
    monkeypatch.setattr('atlas.generate_magpie.language',lambda text:'en')


def config(**changes):
    return dict(count=2,acceptance_only=True,acceptance_smoke=True,d23_oversampling=True,
                derivative_id='example/model',split='evaluation',seed=41,near_threshold=.9,
                revision='a'*40,code_commit='test',engine_version='0.31.0')|changes


def outputs(texts,reason='stop'):
    return [NS(outputs=[NS(text=t,finish_reason=reason,token_ids=[1,2])]) for t in texts]


def test_rounds_extend_original_candidate_budget_and_keep_seeds_and_filters(tmp_path):
    calls=[]
    def generate(seeds):
        calls.extend(seeds)
        if len(calls)<=48:return outputs(['bad']*len(seeds),'length')
        return outputs(['Forbidden valid query','Forbidden valid query','Describe orange sunsets vividly','Explain computer arithmetic gently'])
    kept,report=collect_queries(generate,config(),tmp_path,['Forbidden valid query'],lambda:None)
    assert len(kept)==2 and report['attempted']==52 and report['length_terminated']==48
    assert report['forbidden']==2 and len(set(calls))==52
    assert report['budget']==240 and report['rounds']==13
    assert len((tmp_path/'raw_queries.jsonl').read_text().splitlines())==52


def test_shortfall_counts_every_attempt_and_never_publishes_partial_workload(tmp_path):
    def generate(seeds):return outputs(['A repeated but valid question']*len(seeds))
    c=config();kept,report=collect_queries(generate,c,tmp_path,[],lambda:None)
    assert len(kept)==1 and report['attempted']==240 and report['exact_duplicates']==239
    result=finish_generation(tmp_path,c,kept,report)
    assert result['status']=='shortfall' and result['own_domain']=='unavailable'
    assert not (tmp_path/'prompts.jsonl').exists() and (tmp_path/'partial_queries.jsonl').exists()
    assert json.loads((tmp_path/'results.json').read_text())==result
    assert (tmp_path/'ledger_draft.json').exists()


def test_success_stops_early_and_training_shortfall_is_not_ready(tmp_path):
    kept,report=collect_queries(lambda seeds:outputs(['Draw a mellow sunset','Explain radix arithmetic','Describe violet blossoms','Build a birdhouse carefully']),config(),tmp_path,[],lambda:None)
    result=finish_generation(tmp_path,config(),kept,report)
    assert result['status']=='complete' and result['attempted']==4
    assert len((tmp_path/'prompts.jsonl').read_text().splitlines())==2
    other=tmp_path/'train';other.mkdir()
    result=finish_generation(other,config(split='training'),kept[:1],report)
    assert result['training_ready'] is False and result['own_domain'] is None
    assert not (other/'prompts.jsonl').exists()


def test_default_budget_and_shortfall_failure_are_preserved(tmp_path):
    assert candidate_budget(64,False,False)==1280
    assert candidate_budget(500,False,True)==6400
    c=config(d23_oversampling=False)
    kept,report=collect_queries(lambda seeds:outputs(['bad']*len(seeds)),c,tmp_path,[],lambda:None)
    assert report['attempted']==48
    with pytest.raises(RuntimeError,match='valid queries'):finish_generation(tmp_path,c,kept,report)


@pytest.mark.parametrize('error',[None,RuntimeError('generation failure'),KeyboardInterrupt()])
def test_engine_shutdown_on_success_error_and_interrupt(error):
    calls=[];llm=NS(llm_engine=NS(engine_core=NS(shutdown=lambda **kw:calls.append(kw))))
    def work():
        with managed_engine(lambda:llm) as engine:
            assert engine is llm
            if error:raise error
    if error:
        with pytest.raises(type(error)):work()
    else:work()
    assert calls==[{'timeout':10.}]


def test_pause_mid_generation_preserves_raw_and_shuts_engine(tmp_path):
    calls=[];llm=NS(llm_engine=NS(engine_core=NS(shutdown=lambda **kw:calls.append(kw))))
    n=0
    def pause():
        nonlocal n;n+=1
        if n==2:raise RuntimeError('Experiments paused')
    with pytest.raises(RuntimeError,match='paused'):
        with managed_engine(lambda:llm):
            collect_queries(lambda seeds:outputs(['bad']*len(seeds)),config(),tmp_path,[],pause)
    assert len((tmp_path/'raw_queries.jsonl').read_text().splitlines())==4 and len(calls)==1


def test_cleanup_failure_does_not_hide_original_error():
    def shutdown(**kwargs):raise OSError('cleanup')
    llm=NS(llm_engine=NS(engine_core=NS(shutdown=shutdown)))
    with pytest.warns(RuntimeWarning,match='cleanup'):
        with pytest.raises(ValueError,match='original'):
            with managed_engine(lambda:llm):raise ValueError('original')
    with pytest.raises(OSError,match='cleanup'):
        with managed_engine(lambda:llm):pass
