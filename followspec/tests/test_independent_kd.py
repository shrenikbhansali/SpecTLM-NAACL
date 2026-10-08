import pytest
from followspec.independent_kd import validate_target, answer_labels, balanced_pool, filter_training_queries


def test_test_pool_cannot_enter_repairs():
    for pool in ['bank','precutoff_atlas']:
        validate_target({'pool':pool,'base':'llama','exclusion':''})
    with pytest.raises(ValueError,match='pre-cutoff'):
        validate_target({'pool':'test','base':'llama','exclusion':''})


def test_answer_only_labels_and_no_silent_truncation():
    row={'input_ids':[1,2,3,4,5], 'response_start':3,'loss_mask':[False]*3+[True]*2}
    assert answer_labels(row,5)==[-100,-100,-100,4,5]
    with pytest.raises(ValueError):answer_labels(row,4)
    with pytest.raises(ValueError):answer_labels(dict(row,loss_mask=[True]*5),5)


def test_pool_is_balanced_disjoint_and_deterministic():
    donors={x:[{'prompt_sha256':f'{x}{i}','sample_id':f'{x}{i}'} for i in range(4)] for x in ['a','b']}
    out=balanced_pool(donors,6)
    assert [r['sample_id'] for r in out]==['a0','b0','a1','b1','a2','b2']
    assert out==balanced_pool(donors,6)
    donors['b'][0]=donors['a'][0]
    with pytest.raises(ValueError):balanced_pool(donors,6)


def test_queries_exclude_exact_and_near_evaluation_overlap():
    prompt='Explain how a small neural language model predicts the next token in a sequence.'
    other='Give three concrete examples of geological processes shaping rocky mountain landscapes.'
    rows=[dict(prompt=prompt),dict(prompt=prompt+' Please.'),dict(prompt=other)]
    kept,_=filter_training_queries(rows,[prompt],.7)
    assert [x['prompt'] for x in kept]==[other]


def test_native_lora_step_merge_preserves_logits(tmp_path):
    torch=pytest.importorskip('torch');peft=pytest.importorskip('peft')
    from transformers import LlamaConfig,LlamaForCausalLM
    torch.set_num_threads(1);torch.manual_seed(0)
    model=LlamaForCausalLM(LlamaConfig(vocab_size=24,hidden_size=16,intermediate_size=32,num_hidden_layers=1,
        num_attention_heads=2,num_key_value_heads=2,tie_word_embeddings=False))
    model=peft.get_peft_model(model,peft.LoraConfig(r=2,lora_alpha=4,target_modules=['q_proj','v_proj'],task_type='CAUSAL_LM'))
    ids=torch.tensor([[1,2,3,4,5]]);labels=torch.tensor([[-100,-100,-100,4,5]])
    out=model(input_ids=ids,labels=labels)
    expected=torch.nn.functional.cross_entropy(out.logits[0,2:4],ids[0,3:5])
    torch.testing.assert_close(out.loss,expected)
    optimizer=torch.optim.AdamW([p for p in model.parameters() if p.requires_grad],lr=.01)
    out.loss.backward();optimizer.step();model.eval()
    with torch.no_grad():before=model(ids).logits
    merged=model.merge_and_unload();merged.save_pretrained(tmp_path)
    loaded=LlamaForCausalLM.from_pretrained(tmp_path).eval()
    with torch.no_grad():after=loaded(ids).logits
    torch.testing.assert_close(before,after,rtol=1e-5,atol=1e-6)
