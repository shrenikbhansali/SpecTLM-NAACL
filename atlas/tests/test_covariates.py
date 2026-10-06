import torch
import pytest
from atlas.covariates import compare_tokens, relative_weight_groups, draft_mask, tap_layers


def test_base_self_displacements_are_zero_but_absolute_outside_mass_is_retained():
    logits=torch.tensor([[1.,2.,3.],[2.,1.,0.]])
    features={2:torch.tensor([[1.,2.],[2.,1.]])}
    result=compare_tokens(logits,logits,features,features,torch.tensor([True,False,True]))
    assert result['kl_child_base']==0 and result['outside_vocab_mass_shift']==0
    assert result['outside_vocab_mass_child']>0
    assert result['features']['2']['relative_l2']==0 and result['features']['2']['cosine_displacement']==0


def test_shifted_distribution_and_features_are_nonzero_and_teacher_orientation_is_correct():
    base=torch.tensor([[1.,2.,3.],[1.,0.,0.]])
    child=torch.tensor([[3.,2.,1.],[0.,0.,1.]])
    bh={2:torch.tensor([[1.,0.],[1.,0.]])};ch={2:torch.tensor([[0.,1.],[1.,1.]])}
    result=compare_tokens(base,child,bh,ch,torch.tensor([True,False,True]))
    expected=(child.log_softmax(-1).exp()*(child.log_softmax(-1)-base.log_softmax(-1))).sum(-1).mean().item()
    assert result['kl_child_base']==pytest.approx(expected)
    assert result['features']['2']['relative_l2']>0 and result['features']['2']['cosine_displacement']>0


def test_grouped_weight_norm_uses_summed_squares_and_unchanged_modules():
    base={'model.layers.0.q_proj.weight':torch.eye(2),'model.layers.1.q_proj.weight':torch.eye(2),'lm_head.weight':torch.ones(3,2)}
    updates={'model.layers.0.q_proj.weight':torch.eye(2)}
    r=relative_weight_groups(base,updates)
    assert r['q_proj']['relative_norm']==pytest.approx(2**-.5)
    assert r['lm_head']['relative_norm']==0


def test_pinned_tap_defaults_and_vocab_mapping():
    assert tap_layers({},32)==[2,16,29]
    assert tap_layers({'eagle_aux_hidden_state_layer_ids':[1,3,5]},8)==[1,3,5]
    assert torch.equal(draft_mask(torch.tensor([True,False,True]),torch.tensor([0,1])),torch.tensor([True,False,True]))
    with pytest.raises(ValueError):draft_mask(torch.tensor([True,True,False]),torch.tensor([0,1]))


def test_preparation_requires_actual_engine_prompt_tokens_and_preserves_response_mask(tmp_path):
    import json
    from atlas.prepare_covariates import from_cell
    cfg=dict(engine_version='0.31.0',prompt_sha256='will-set',target='child',target_revision='a'*40,adapter=None,adapter_revision=None,K=4)
    prompts=tmp_path/'prompts.jsonl';prompts.write_text(json.dumps(dict(prompt_id='p',prompt='query',derivative_id='child',split='evaluation',acceptance_only=True))+'\n')
    import hashlib
    cfg['prompt_sha256']=hashlib.sha256(prompts.read_bytes()).hexdigest();cfg['prompts']=str(prompts)
    (tmp_path/'config.json').write_text(json.dumps(cfg))
    (tmp_path/'results.json').write_text(json.dumps(dict(n=1)))
    (tmp_path/'per_prompt.jsonl').write_text(json.dumps(dict(prompt_id='p',completion_token_ids=[3,4]))+'\n')
    with pytest.raises(ValueError,match='prompt_token_ids'):from_cell(tmp_path,True,5)
    (tmp_path/'per_prompt.jsonl').write_text(json.dumps(dict(prompt_id='p',prompt_token_ids=[1,2],completion_token_ids=[3,4]))+'\n')
    rows,config=from_cell(tmp_path,True,5)
    assert rows[0]['input_ids']==[1,2,3,4] and rows[0]['response_start']==2
    assert rows[0]['assistant_mask']==[0,0,1,1] and config['acceptance_only']


def test_template_identity_is_measured_from_snapshot_and_adapter_inheritance(tmp_path):
    import json
    from atlas.covariates import template_identity
    base=tmp_path/'base';base.mkdir();child=tmp_path/'child';child.mkdir()
    (base/'tokenizer_config.json').write_text(json.dumps({'chat_template':'template-A'}))
    assert template_identity(base,child,adapter=True)['changed'] is False
    (child/'chat_template.jinja').write_text('template-B')
    assert template_identity(base,child,adapter=True)['changed'] is True
