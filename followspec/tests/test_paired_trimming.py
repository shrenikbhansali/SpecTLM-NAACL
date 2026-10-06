import copy
import json
from pathlib import Path
import pytest
import torch
from followspec.tests.test_token_data import run
from followspec.paired_responses import pair_runs
from followspec.token_data import build_manifest,validate_arm_set,OnlineResponseDataset


def fixture(tmp_path):
    child=run(tmp_path,'child','c',answer=(4,5,6,7))
    base=run(tmp_path,'base','base',answer=(8,9))
    return child,base


def assemble(pair):
    return {arm:build_manifest(arm,pair['refs']['base' if arm=='PO-D' else 'child'],
        registry={'c':dict(kind='bank',revision='b'*40)},base_revision='a'*40,
        initialization_revision='d'*40,allow_acceptance=True) for arm in ['FS','MVD','PO-D','PO-T']}


class Bank:
    def capture(self,target,ids,mask,feature_target):
        return dict(input_ids=ids,loss_mask=mask,feature_target=feature_target)


def test_paired_prefixes_preserve_originals_full_prompts_and_match_actual_tokens(tmp_path):
    child,base=fixture(tmp_path)
    before={str(p):p.read_bytes() for folder in [child,base] for p in folder.iterdir()}
    pair=pair_runs(child,base,child_id='c')
    arms=assemble(pair);report=validate_arm_set(arms)
    assert report['shifted_sequence_tokens']==4
    assert report['assistant_loss_tokens']=={arm:2 for arm in arms}
    assert pair['trims'][0]['child_dropped_tokens']==2
    assert pair['trims'][0]['base_dropped_tokens']==0
    for arm,m in arms.items():
        ds=OnlineResponseDataset(m,split='train',bank=Bank(),shift=lambda r:r,allow_acceptance=True)
        got=ds[0]['tensors'];answer=[8,9] if arm=='PO-D' else [4,5]
        assert got['input_ids'].tolist()==[1,2,3]+answer
        assert got['loss_mask'].tolist()==[False]*3+[True]*2
        assert ds.approx_lengths==[4]
        assert not m['data_acceptance_passed'] and m['acceptance_only']
        assert got['feature_target']==('base' if arm in ['PO-D','PO-T'] else 'child')
    assert all(Path(p).read_bytes()==b for p,b in before.items())


def test_both_directions_and_equal_length_pairs_are_logged(tmp_path):
    child=run(tmp_path,'c','c',answer=(4,));base=run(tmp_path,'b','base',answer=(7,8,9))
    p=pair_runs(child,base,child_id='c');assert p['trims'][0]['base_dropped_tokens']==2
    equal=run(tmp_path,'equal','base',answer=(8,))
    t=pair_runs(child,equal,child_id='c')['trims'][0]
    assert t['base_dropped_tokens']==t['child_dropped_tokens']==0


def test_peer_changes_or_forged_lengths_are_rejected_before_capture(tmp_path):
    child,base=fixture(tmp_path);arms=assemble(pair_runs(child,base,child_id='c'))
    bad=copy.deepcopy(arms['FS']);bad['samples'][0]['response_view']['kept_response_tokens']=3
    with pytest.raises(ValueError,match='view'):OnlineResponseDataset(bad,split='train',bank=Bank(),shift=lambda r:r,allow_acceptance=True)
    (base/'per_prompt.jsonl').write_text('{}\n')
    with pytest.raises(ValueError,match='changed'):OnlineResponseDataset(arms['FS'],split='train',bank=Bank(),shift=lambda r:r,allow_acceptance=True)


def test_pair_requires_identical_prompts_and_generation_controls(tmp_path):
    child,base=fixture(tmp_path)
    cfg=json.loads((base/'config.json').read_text());cfg['seed']=999
    (base/'config.json').write_text(json.dumps(cfg))
    with pytest.raises(ValueError,match='controls'):pair_runs(child,base,child_id='c')
    cfg['seed']=1;(base/'config.json').write_text(json.dumps(cfg))
    r=json.loads((base/'per_prompt.jsonl').read_text());r['input_ids'][0]=10;r['prompt_token_ids'][0]=10
    (base/'per_prompt.jsonl').write_text(json.dumps(r)+'\n')
    with pytest.raises(ValueError,match='context'):pair_runs(child,base,child_id='c')


def test_po_t_cannot_reuse_untrimmed_child_when_fs_uses_trimmed_view(tmp_path):
    child,base=fixture(tmp_path);arms=assemble(pair_runs(child,base,child_id='c'))
    arms['PO-T']['samples'][0]['response_view']['peer_record_index']=1
    with pytest.raises(ValueError,match='view'):validate_arm_set(arms)


def test_source_acceptance_flag_cannot_be_laundered_into_production(tmp_path):
    child,base=fixture(tmp_path)
    cfg=json.loads((child/'config.json').read_text());cfg['acceptance_only']=False
    (child/'config.json').write_text(json.dumps(cfg))
    with pytest.raises(ValueError,match='scope'):pair_runs(child,base,child_id='c')


def test_base_parent_share_can_reference_itself_without_trimming(tmp_path):
    base=run(tmp_path,'base','base')
    cfg=json.loads((base/'config.json').read_text());cfg['prompt_target']='base'
    (base/'config.json').write_text(json.dumps(cfg))
    pair=pair_runs(base,base,child_id='base')
    assert pair['trims'][0]['child_dropped_tokens']==pair['trims'][0]['base_dropped_tokens']==0
    manifest=build_manifest('FS',pair['refs']['child'],registry={},base_revision='a'*40,
        initialization_revision='d'*40,allow_acceptance=True)
    ds=OnlineResponseDataset(manifest,split='train',bank=Bank(),shift=lambda r:r,allow_acceptance=True)
    assert ds[0]['tensors']['feature_target']=='base' and manifest['parent_sample_share']==1
