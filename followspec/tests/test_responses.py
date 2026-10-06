import pytest
from followspec.generate_responses import validate_queries,make_sample


def test_training_queries_reject_test_split_smoke_and_forbidden_hashes():
    rows=[dict(prompt_id='p',prompt='A training question about weather.',split='training')]
    validate_queries(rows,[],False)
    with pytest.raises(ValueError):validate_queries([rows[0]|dict(split='evaluation')],[],True)
    with pytest.raises(ValueError):validate_queries([rows[0]|dict(acceptance_only=True)],[],False)
    with pytest.raises(ValueError):validate_queries(rows,[{'prompt':rows[0]['prompt'].upper()}],False)
    with pytest.raises(ValueError):validate_queries(rows*2,[],False)
    with pytest.raises(ValueError):validate_queries([rows[0]|dict(derivative_id='test')],[],False,prompt_target='bank')


def test_exact_engine_tokens_form_assistant_only_mask_without_retokenization():
    r=make_sample(dict(prompt_id='p',prompt='text',split='training'),[1,2,3],[4,5],target_id='child',revision='a'*40,acceptance_only=True)
    assert r['input_ids']==[1,2,3,4,5] and r['loss_mask']==[False,False,False,True,True]
    assert r['response_start']==3 and r['generation_target']=='child'
    assert r['acceptance_only']
    with pytest.raises(ValueError):make_sample({},[1],[],target_id='c',revision='r',acceptance_only=True)


def test_overfit64_is_an_explicit_bounded_acceptance_mode():
    rows=[dict(prompt_id=str(i),prompt=f'Explain training example number {i}.',split='training') for i in range(64)]
    with pytest.raises(ValueError):validate_queries(rows,[],True)
    validate_queries(rows,[],True,acceptance_limit=64)
    with pytest.raises(ValueError):validate_queries(rows,[],False,acceptance_limit=64)
    with pytest.raises(ValueError):validate_queries(rows+[rows[0]|dict(prompt_id='65')],[],True,acceptance_limit=64)
