import math
import pytest
from atlas.filter_pool import score_reference, repetition_coverage, summarize, validate_baseline


def test_teacher_forced_ppl_excludes_first_token_and_counts_tokens():
    records=score_reference([5,6,7],[None,{6:-1.0},{7:-3.0}])
    assert records['scored_tokens']==2 and records['nll_sum']==4 and records['ppl']==pytest.approx(math.exp(2))
    with pytest.raises(ValueError):score_reference([5,6],[None,{8:-1}])


def test_repeated_4gram_counts_covered_positions_and_requires_repetition():
    assert repetition_coverage([1,2,3,4])==0
    assert repetition_coverage([1,2,3,4]*4)==1
    assert repetition_coverage([1,1,1,1,1])==1
    assert repetition_coverage(list(range(20)))==0


def test_matched_baseline_identity_ratio_and_pending_threshold():
    cfg={'engine_version':'0.31.0','reference_sha256':'x','base_revision':'a'*40,'max_reference_tokens':2048,'ppl_definition':'fixed_prompt_tokens'}
    validate_baseline(cfg,cfg)
    with pytest.raises(ValueError):validate_baseline(cfg,cfg|{'reference_sha256':'changed'})
    rows=[dict(nll_sum=4.,scored_tokens=2)]*128
    samples=[dict(empty=False,immediate_eos=False,repetition_coverage=0.)]*10
    result=summarize(rows,samples,math.exp(2),None)
    assert result['ppl_ratio_vs_base']==1 and result['degenerate_count']==0
    assert result['accepted'] is None
    assert summarize(rows,samples,math.exp(2),.5)['accepted'] is True
    assert summarize(rows,samples,math.exp(2)/3,.5)['accepted'] is False


def test_reference_contains_flat_ids_and_explicit_truncation():
    from atlas.filter_pool import prepare_reference
    class Tokenizer:
        def __call__(self,text,**kwargs):return {'input_ids':list(range(12))}
        def apply_chat_template(self,*args,return_dict=True,**kwargs):
            return {'input_ids':list(range(20))} if return_dict else list(range(20))
        def decode(self,ids):return str(ids)
    row=prepare_reference([{'prompt_id':'a','prompt':'hello'}],Tokenizer(),8)[0]
    assert row['input_ids']==list(range(8)) and row['generation_input_ids']==list(range(12,20))
    assert row['score_mask']==[0]+[1]*7 and row['truncated'] and row['generation_truncated']
