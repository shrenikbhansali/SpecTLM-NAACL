import pytest
import torch
from followspec.family_repair import configure_variant, validate_rows
from followspec.tests.test_family_repair import Tiny

def test_whole_lora_updates_all_drafter_linears_not_teacher_or_embedding():
    m=Tiny();configure_variant(m,'whole_lora',rank=2,alpha=4)
    names=[n for n,p in m.named_parameters() if p.requires_grad]
    assert names and all('lora_' in n for n in names)
    assert any(n.startswith('fc.') for n in names)
    assert any(n.startswith('lm_head.') for n in names)
    assert any(n.startswith('layers.') for n in names)
    assert not any(n.startswith(('embed_tokens','verifier_','norm')) for n in names)

def test_response_pair_mixture_requires_explicit_disjoint_branches_and_same_prefix():
    from atlas.workloads import prompt_hash
    r=dict(sample_id='a',input_ids=[1,2,3],response_start=1,loss_mask=[False,True,True],raw_prompt='hello',prompt_sha256=prompt_hash('hello'),response_branch='short512')
    other=r|dict(sample_id='b',response_branch='long2048')
    with pytest.raises(ValueError):validate_rows([r,other],set(),10)
    validate_rows([r,other],set(),10,allow_response_pairs=True)
    with pytest.raises(ValueError):validate_rows([r,other|dict(response_branch='short512')],set(),10,allow_response_pairs=True)
    with pytest.raises(ValueError):validate_rows([r,other|dict(input_ids=[9,2,3])],set(),10,allow_response_pairs=True)

def test_optimizer_persistence_default_and_opt_out():
    from followspec.family_repair import final_optimizer_policy
    assert final_optimizer_policy(False,False)
    assert not final_optimizer_policy(True,True)
    with pytest.raises(ValueError):final_optimizer_policy(True,False)

def test_e8_has_twenty_new_trainings_and_no_existing_fc_duplicates():
    from pathlib import Path
    from followspec.rev2_launch import e8_jobs,parts
    src=dict(name='source',args=['--code-repo','old','--','python','-m','followspec.family_repair','--one-epoch'])
    jobs,records=e8_jobs({f'FIX24-official-t{t}-16k-fc':src for t in [0,1]},Path('/stage'),Path('/code'))
    assert len(jobs)==len({j['name'] for j in jobs})==20
    assert {(r['target'],r['seed']) for r in records if r['arm']=='interface'}=={(1,1),(1,2)}
    for j in jobs:
        o,i=parts(j)
        assert '--omit-final-optimizer' in i
        assert i[i.index('--epoch-export-fractions')+1]=='1'

def test_whole_lora_head_receives_gradient_and_export_matches():
    from followspec.family_repair import merged_state
    torch.manual_seed(17);m=Tiny();configure_variant(m,'whole_lora',rank=2,alpha=4)
    x=torch.randn(4,6);m(x).square().sum().backward()
    assert m.lm_head.lora_B.grad.abs().sum()>0
    for n,p in m.named_parameters():
        if 'lora_B' in n:p.data.normal_(0,.01)
    other=Tiny();other.load_state_dict(merged_state(m))
    torch.testing.assert_close(m(x),other(x))

def test_long_data_budget_is_explicit_and_never_truncates():
    from followspec.repair_data import validate_context_budget
    validate_context_budget([[1]*100],512,2048)
    with pytest.raises(ValueError):validate_context_budget([[1]*100],2048,2048)
    validate_context_budget([[1]*100],2048,4096)
    with pytest.raises(ValueError):validate_context_budget([[1]*2100],2048,4096)

def test_timing_long_and_large_batch_defaults_are_unchanged():
    from atlas.timing_panel import parser
    args=['--target','t','--target-revision','r','--prompts','p','--frozen-harness','f','--output','o']
    a=parser().parse_args(args)
    assert (a.max_new_tokens,a.max_model_len,a.batch_size)==(512,4096,8)
    b=parser().parse_args(args+['--max-new-tokens','8192','--max-model-len','12288','--batch-size','32'])
    assert (b.max_new_tokens,b.max_model_len,b.batch_size)==(8192,12288,32)

def test_step_profile_excludes_export_interval():
    from followspec.training_profile import StepProfiler
    values=iter([10.,12.,20.,23.]);sync=[]
    p=StepProfiler(lambda:next(values),lambda:sync.append(True),lambda:(100,200))
    p.begin();a=p.end(1);p.begin();b=p.end(2)
    assert [a['wall_s'],b['wall_s']]==[2.,3.] and len(sync)==4
    assert b['peak_allocated_bytes']==100 and b['peak_reserved_bytes']==200

def test_paired_seed_query_bootstrap_preserves_seed_and_query_pairs():
    import numpy as np
    from followspec.rev2_analysis import paired_seed_query
    a=np.array([[1.,2.,3.],[2.,3.,4.],[3.,4.,5.]])
    r=paired_seed_query(a,a+.5)
    assert r['delta']['mean']==.5 and r['delta']['ci95']==[.5,.5]
    assert r['n']==3 and r['seeds']==3
    r=paired_seed_query(a,a+np.array([[0.],[1.],[2.]]))
    assert r['delta']['ci95'][0]<1<r['delta']['ci95'][1]

def test_vocabulary_selection_uses_answer_only_and_preserves_overlapping_head_rows():
    from followspec.vocabulary_repair import select_vocabulary,apply_vocabulary
    rows=[dict(input_ids=[7,7,6,4,4,2],response_start=3,loss_mask=[False]*3+[True]*3)]
    ids=select_vocabulary(rows,8,3)
    assert ids.tolist()==[0,2,4]  # answer frequency, then token-ID tie; sorted storage
    class M(torch.nn.Module):
        def __init__(self):
            super().__init__();self.lm_head=torch.nn.Linear(2,3,bias=False);self.verifier_lm_head=torch.nn.Linear(2,3,bias=False)
            self.register_buffer('d2t',torch.tensor([0,1,4]));self.register_buffer('t2d',torch.tensor([True,False,True,False,False,False,True,False]))
    m=M();old=m.lm_head.weight.detach().clone();target=torch.arange(16.).reshape(8,2)
    proof=apply_vocabulary(m,ids,target)
    assert torch.equal(m.lm_head.weight[0],old[0]) and torch.equal(m.lm_head.weight[1],old[1])
    assert torch.equal(m.lm_head.weight[2],target[4])
    assert torch.equal(torch.arange(3)+m.d2t,ids) and m.t2d.nonzero().flatten().tolist()==ids.tolist()
    assert proof['new_tokens']==1 and proof['retained_tokens']==2
    assert torch.equal(m.verifier_lm_head.weight,target[ids])

def test_long_mixture_keeps_both_responses_and_rejects_prefix_changes():
    from followspec.rev2_seal import mixture
    r=dict(sample_id='x',prompt_sha256='h',prompt_token_ids=[1,2],completion_token_ids=[3])
    long=r|dict(completion_token_ids=[3,4])
    out=mixture([r],[long])
    assert [v['sample_id'] for v in out]==['short512:x','long2048:x']
    assert [v['completion_token_ids'] for v in out]==[[3],[3,4]]
    with pytest.raises(ValueError):mixture([r],[long|dict(prompt_token_ids=[1,9])])

def test_training_comparison_rejects_budget_and_data_mismatches():
    from followspec.rev2_training_analysis import matched_training
    a=dict(data_sha256='h',steps=100,seed=0,lr=2e-5)
    assert matched_training(a,a|dict(variant='decoder_qo'))
    for key,value in [('data_sha256','other'),('steps',200),('seed',1),('lr',1e-4)]:
        with pytest.raises(ValueError):matched_training(a,a|{key:value})

def test_profile_summary_counts_warmup_and_storage_separately():
    from followspec.rev2_profile_analysis import summarize_steps, tensor_bytes
    rows=[dict(step=i+1,wall_s=100. if i<10 else 2.,peak_allocated_bytes=1024+i,peak_reserved_bytes=4096) for i in range(200)]
    r=summarize_steps(rows)
    assert r['n_steps']==200 and r['steady_steps']==190
    assert r['all_steps_mean_s']==6.9 and r['steady_mean_s']==2.
    assert r['peak_allocated_bytes']==1223 and r['peak_reserved_bytes']==4096
    assert tensor_bytes({'x':{'shape':[3,4],'dtype':'F32'},'__metadata__':{}})==48
    with pytest.raises(ValueError):summarize_steps(rows[:199])
    with pytest.raises(ValueError):summarize_steps(rows[:199]+[rows[0]])

def test_preinspected_sample_match_rejects_any_unseen_text_or_mask():
    from followspec.rev2_audit_transfer import checked_samples
    row=dict(prompt='user',answer='answer',input_ids=[1,2],response_start=1,loss_mask=[False,True],mask_valid=True)
    checked_samples([row]*5,[row|dict(branch='long2048')]*5)
    with pytest.raises(ValueError):checked_samples([row]*5,[row]*4+[row|dict(answer='different')])
    with pytest.raises(ValueError):checked_samples([row]*5,[row]*4+[row|dict(loss_mask=[True,True])])

def test_resource_comparison_resamples_matched_step_blocks():
    from followspec.rev2_profile_analysis import paired_step_blocks
    r=paired_step_blocks([2.]*200,[4.]*200)
    assert r['ratio_arm_over_reference']['mean']==2
    assert r['ratio_arm_over_reference']['ci95']==[2,2]
    assert r['delta_s']['ci95']==[2,2]
    assert r['blocks']==19 and r['steps']==190

def test_completion_ping_changes_only_own_ready_row(tmp_path):
    from followspec.rev2_progress import ping_board
    (tmp_path/'notes').mkdir();(tmp_path/'ledger').mkdir()
    text='Gate unchanged\n| REV2-P0 | work | P0 | codex | D54 | now | in progress | codex-1 | evidence |\n| OTHER | untouched |\n'
    (tmp_path/'MASTER.md').write_text(text)
    ping_board(tmp_path,'P0',dict(ready_for_review=False),'/evidence','stamp')
    assert (tmp_path/'MASTER.md').read_text()==text
    ping_board(tmp_path,'P0',dict(ready_for_review=True,completed=270,expected=270),'/evidence','stamp')
    new=(tmp_path/'MASTER.md').read_text()
    assert '| review |' in new and 'Gate unchanged' in new and '| OTHER | untouched |' in new
    ping_board(tmp_path,'P0',dict(ready_for_review=True,completed=270,expected=270),'/evidence','stamp')
    assert (tmp_path/'notes/REV2.md').read_text().count('Completion ping')==1
