import pytest
import torch
from followspec.tests.test_token_data import run
from followspec.token_data import build_manifest, OnlineResponseDataset
from followspec.dflash_extension import prepare_block_sample
from followspec.paired_data import shift_paired


def test_dflash_budget_counts_unshifted_tokens_and_preserves_raw_positions(tmp_path):
    source=run(tmp_path,'child','c')
    refs=[dict(run=str(source),record_index=0,child_id='c',pair_id='p',split='train')]
    kw=dict(registry={'c':dict(kind='bank',revision='b'*40)},base_revision='a'*40,
            initialization_revision='d'*40,allow_acceptance=True)
    eagle=build_manifest('FS',refs,**kw)
    raw=build_manifest('FS',refs,sequence_layout='dflash_raw',**kw)
    assert eagle['token_budget']==4 and raw['token_budget']==5
    assert raw['token_budget_unit']=='raw sequence tokens'
    ds=OnlineResponseDataset(raw,split='train',bank=None,shift=prepare_block_sample,allow_acceptance=True)
    assert ds.approx_lengths==[5]
    assert raw['samples'][0]['context_token_ids']==eagle['samples'][0]['context_token_ids']
    class Bank:
        def capture(self,target,ids,mask,feature_target):
            data=dict(input_ids=ids,loss_mask=mask)
            for key in ['hidden_states','base_hidden_states','verifier_last_hidden_states','base_verifier_last_hidden_states']:
                data[key]=torch.zeros(len(ids),3)
            return data
    wrong=OnlineResponseDataset(raw,split='train',bank=Bank(),shift=shift_paired,allow_acceptance=True)
    with pytest.raises(ValueError,match='layout'):wrong[0]


def test_manifest_unit_must_agree_with_layout(tmp_path):
    source=run(tmp_path,'child','c')
    refs=[dict(run=str(source),record_index=0,child_id='c',pair_id='p',split='train')]
    manifest=build_manifest('FS',refs,registry={'c':dict(kind='bank',revision='b'*40)},
        base_revision='a'*40,initialization_revision='d'*40,allow_acceptance=True)
    manifest['sequence_layout']='dflash_raw'
    with pytest.raises(ValueError,match='layout'):
        OnlineResponseDataset(manifest,split='train',bank=None,shift=prepare_block_sample,allow_acceptance=True)
