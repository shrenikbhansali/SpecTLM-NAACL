import pytest
from atlas.workloads import normalize,prompt_hash,filter_prompts,stratified_sample,audit_disjoint,magpie_prefix


def test_overlap_normalized_and_eval_eval_allowed():
    a=[{'prompt':'Tell me about\n  gravity'}];b=[{'prompt':'tell me about gravity'}]
    assert prompt_hash(a[0]['prompt'])==prompt_hash(b[0]['prompt'])
    with pytest.raises(ValueError,match='overlap'):audit_disjoint({'train':a},{'eval':b})
    assert audit_disjoint({'train':[{'prompt':'Completely independent example'}]}, {'e1':a,'e2':b})['overlap_count']==0


def test_filter_lengths_duplicates_and_forbidden():
    rows=[{'prompt':s} for s in ['short','Describe the physics of rainbows in clear language.',
          'Describe the physics of rainbows in clear language.', 'This belongs only to evaluation.','x'*1001]]
    kept,report=filter_prompts(rows,forbidden=['This belongs only to evaluation.'],near_threshold=.8)
    assert len(kept)==1
    assert report['exact_duplicates']==1
    assert report['forbidden']==1
    assert report['length_rejected']==2
    assert report['duplicate_rate']==.2


def test_near_duplicate_minhash():
    a=' '.join('word'+str(i) for i in range(40))
    b=a+' extra'
    kept,report=filter_prompts([{'prompt':a},{'prompt':b}],near_threshold=.8)
    assert len(kept)==1
    assert report['near_duplicates']==1


def test_stratified_reproducible_count_and_balance():
    rows=[dict(prompt_id=str(i),prompt='p'+str(i),category=str(i%4)) for i in range(40)]
    a=stratified_sample(rows,16,42)
    assert a==stratified_sample(list(reversed(rows)),16,42)
    assert len(a)==16
    assert all(sum(r['category']==str(j) for r in a)==4 for j in range(4))
    with pytest.raises(ValueError):stratified_sample(rows,41,42)


def test_prefix_uses_exact_derivative_template():
    class Tokenizer:
        def apply_chat_template(self,messages,**kwargs):
            assert kwargs['enable_thinking'] is False
            return 'custom-user:'+messages[0]['content']+'<end>'
    assert magpie_prefix(Tokenizer(),'qwen3')=='custom-user:'


def test_unresolved_benchmark_placeholders_are_rejected():
    rows=[dict(prompt_id=str(i),prompt='FULL BENCHMARK DATA SHOULD BE FETCHED FROM THE SOURCE USING SPECDEC_BENCH',category='math') for i in range(128)]
    with pytest.raises(ValueError,match='placeholder'):stratified_sample(rows,128,42)
