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


def test_magpie_identical_prefixes_receive_distinct_reproducible_seeds():
    from atlas.generate_magpie import request_seeds
    first=request_seeds(42,0,64)
    assert len(set(first))==64 and first==request_seeds(42,0,64)
    assert not set(first)&set(request_seeds(42,1,64))
    assert not set(first)&set(request_seeds(43,0,64))


def test_smoke_limit_and_production_counts():
    from atlas.generate_magpie import generation_count, validate_hardware
    assert generation_count('training',False)==500
    assert generation_count('evaluation',False)==64
    assert generation_count('training',True)==10
    validate_hardware('NVIDIA A40',True)
    with pytest.raises(ValueError):validate_hardware('NVIDIA A40',False)


def test_adapter_and_tokenizer_provenance_is_verified(tmp_path):
    import hashlib,json
    from atlas.generate_magpie import verify_inputs
    adapter=tmp_path/'adapter';adapter.mkdir();tokenizer=tmp_path/'tok';tokenizer.mkdir()
    (adapter/'adapter_model.safetensors').write_bytes(b'weights')
    (tokenizer/'tokenizer.json').write_bytes(b'tokens')
    (tokenizer/'tokenizer_config.json').write_text(json.dumps({'chat_template':'template'}))
    sha=lambda b:hashlib.sha256(b).hexdigest()
    row={'revision':'b'*40,'base_revision':'a'*40,'tokenizer_source':'repository',
         'tokenizer_sha256':sha(b'tokens'),'template_sha256':sha(json.dumps('template',sort_keys=True).encode()),
         'files':json.dumps([{'path':'adapter_model.safetensors','size':7,'sha256':sha(b'weights')}])}
    verify_inputs(row,str(adapter),str(tokenizer),'b'*40)
    (adapter/'adapter_model.safetensors').write_bytes(b'changed')
    with pytest.raises(ValueError,match='hash'):verify_inputs(row,str(adapter),str(tokenizer),'b'*40)


def test_rendered_eval_keeps_source_ids_and_disables_qwen_thinking():
    from atlas.workloads import render_evaluation
    class Tokenizer:
        def apply_chat_template(self,messages,**kwargs):
            assert kwargs['enable_thinking'] is False and kwargs['add_generation_prompt']
            return '<user>'+messages[0]['content']+'<assistant>'
    result=render_evaluation([{'prompt_id':'p','prompt':'query'}],Tokenizer(),'qwen3')
    assert result[0]['prompt']=='<user>query<assistant>' and result[0]['prompt_id']=='p'
    assert result[0]['raw_prompt']=='query' and result[0]['format']=='chat_template_rendered'


def test_rendered_prompt_audit_still_detects_raw_query_leakage():
    with pytest.raises(ValueError,match='overlap'):
        audit_disjoint({'train':[{'prompt':'A shared user query'}]},
                       {'eval':[{'prompt':'<user>A shared user query<assistant>','raw_prompt':'A shared user query'}]})
