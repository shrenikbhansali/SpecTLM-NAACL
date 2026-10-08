"""D-45 acceptance: parameter scope, merged exports, data masks and deterministic batches."""
import pytest
import torch
from followspec.family_repair import configure_variant, merged_state, step_batches, validate_rows

class Tiny(torch.nn.Module):
    def __init__(self):
        super().__init__();self.fc=torch.nn.Linear(6,2,bias=False)
        self.layers=torch.nn.ModuleList([torch.nn.ModuleDict({'q_proj':torch.nn.Linear(2,2),'v_proj':torch.nn.Linear(2,2)})])
        self.lm_head=torch.nn.Linear(2,3,bias=False);self.embed_tokens=torch.nn.Embedding(4,2)
        self.verifier_lm_head=torch.nn.Linear(2,3,bias=False);self.norm=torch.nn.LayerNorm(2)
        self.register_buffer('d2t',torch.arange(3))
    def forward(self,x):return self.lm_head(self.norm(self.layers[0]['q_proj'](self.fc(x))))

@pytest.mark.parametrize('variant',['fc','fc_lora','full'])
def test_parameter_scope_and_backward(variant):
    torch.manual_seed(0);m=Tiny();before={k:v.clone() for k,v in m.state_dict().items()}
    proof=configure_variant(m,variant,rank=2,alpha=2)
    opt=torch.optim.AdamW([p for p in m.parameters() if p.requires_grad],lr=.01)
    m(torch.randn(3,6)).square().sum().backward();opt.step()
    changed=[k for k,v in m.state_dict().items() if k in before and not torch.equal(v,before[k])]
    assert 'fc.weight' in changed
    if variant=='fc':assert changed==['fc.weight']
    assert not m.embed_tokens.weight.requires_grad and not m.verifier_lm_head.weight.requires_grad
    assert all(torch.isfinite(p.grad).all() for p in m.parameters() if p.grad is not None)
    assert proof['trainable_parameters']>0


def test_lora_zero_init_and_merged_equivalence():
    torch.manual_seed(4);m=Tiny();x=torch.randn(3,6);y=m(x).detach();keys=set(m.state_dict())
    configure_variant(m,'fc_lora',rank=2,alpha=4)
    torch.testing.assert_close(m(x),y)
    for n,p in m.named_parameters():
        if 'lora_B' in n:p.data.normal_()
    state=merged_state(m);assert set(state)==keys
    other=Tiny();other.load_state_dict(state);torch.testing.assert_close(m(x),other(x))


def test_batch_schedule_same_across_variants_and_no_truncation():
    rows=[dict(input_ids=list(range(k)),sample_id=str(k)) for k in [12,18,21,19]]
    plan=step_batches(rows,steps=7,ceiling=40,seed=0)
    assert len(plan)==7 and plan==step_batches(rows,steps=7,ceiling=40,seed=0)
    assert all(sum(len(rows[i]['input_ids'])-1 for i in b)<=40 for b in plan)
    with pytest.raises(ValueError):step_batches(rows,steps=1,ceiling=10,seed=0)


def test_data_contract_rejects_overlap_or_wrong_masks():
    from atlas.workloads import prompt_hash
    row=dict(sample_id='x',input_ids=[1,2,3],response_start=1,loss_mask=[False,True,True],raw_prompt='hello world',prompt_sha256=prompt_hash('hello world'))
    validate_rows([row],set(),max_length=10)
    with pytest.raises(ValueError):validate_rows([row],{row['prompt_sha256']},max_length=10)
    with pytest.raises(ValueError):validate_rows([row|dict(loss_mask=[True]*3)],set(),max_length=10)
