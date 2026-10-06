"""B1 acceptance contracts, written before implementation."""
import copy
import json
import pytest
from atlas.curate_pool import FIELDS, assign_pools, stratify, validate, verify_downloads


def row(i=0, author=None, date="2025-01-01T00:00:00+00:00", kind="lora_adapter"):
    r = dict.fromkeys(FIELDS, "")
    r.update(model_id=f"{author or 'author'+str(i)}/model{i}", revision="a"*40,
             relation="adapter", created_at=date, author=author or f"author{i}",
             license="apache-2.0", downloads=i, gated=False, file_formats=["safetensors"],
             size_bytes=10, r=8, lora_alpha=16, use_rslora=False, target_modules=["q_proj"],
             type=kind, tokenizer_identical=True, template_changed=False, exclusion="", pool="",
             files=[{"path":"adapter_model.safetensors", "size":10}], base_id="base/model")
    return r


def test_schema_duplicates_and_counts():
    rows = assign_pools([row(0), row(1,date="2026-02-01")], "2025-07-01")
    counts = validate(rows)
    assert sum(counts["pool"].values()) == 2
    assert sum(counts["type"].values()) == 2
    with pytest.raises(ValueError,match="duplicate"):
        validate(rows + [rows[0]])
    broken=copy.deepcopy(rows); del broken[0]["license"]
    with pytest.raises(ValueError,match="missing"):
        validate(broken)


def test_author_disjoint_and_only_adapters_in_bank():
    rows=assign_pools([row(0,author="same"),row(1,author="same",date="2026-01-01"),
                       row(2,date="2025-07-01"),row(3,kind="full_finetune")],"2025-07-01")
    assert [r["pool"] for r in rows] == ["bank","excluded","test","precutoff_atlas"]
    assert "author" in rows[1]["exclusion"]
    validate(rows)


def test_sampling_reproducible_stratified_and_prefers_downloads():
    rows=[row(i,kind="lora_adapter" if i<4 else "full_finetune") for i in range(8)]
    selected=stratify(rows,4)
    assert {r["model_id"] for r in selected} == {rows[i]["model_id"] for i in [2,3,6,7]}
    assert selected == stratify(list(reversed(rows)),4)


def test_revision_and_download_presence(tmp_path):
    r=row(); r["pool"]="bank"
    root=tmp_path/"model"; root.mkdir()
    (root/"adapter_model.safetensors").write_bytes(b"0123456789")
    log=tmp_path/"downloads.jsonl"
    entry=dict(model_id=r["model_id"],revision=r["revision"],path=str(root),status="complete")
    log.write_text(json.dumps(entry)+"\n")
    verify_downloads([r],log)
    entry["revision"]="b"*40; log.write_text(json.dumps(entry)+"\n")
    with pytest.raises(ValueError,match="revision"):
        verify_downloads([r],log)
    entry["revision"]=r["revision"]; log.write_text(json.dumps(entry)+"\n")
    (root/"adapter_model.safetensors").write_bytes(b"short")
    with pytest.raises(ValueError,match="size"):
        verify_downloads([r],log)


def test_download_completion_event_can_record_snapshot_path(tmp_path):
    from atlas.curate_pool import event
    log=tmp_path/'log.jsonl'
    event(log,status='complete',path='/cache/snapshot')
    assert json.loads(log.read_text())['path']=='/cache/snapshot'


def test_csv_roundtrip_string_fields_and_large_file_inventory(tmp_path):
    from atlas.curate_pool import read_csv, write_csv
    r=row();r['target_modules']='all-linear';r['gated']='auto'
    r['files']=[dict(path=f'part-{i}.safetensors',size=100,sha256='a'*64) for i in range(2000)]
    path=tmp_path/'large.csv';write_csv(path,[r])
    actual=read_csv(path)[0]
    for key in ('target_modules','gated','files','tokenizer_identical'):
        assert actual[key]==r[key]


def test_read_legacy_string_csv_and_reject_malformed_json(tmp_path):
    import csv
    from atlas.curate_pool import read_csv,write_csv
    r=row();path=tmp_path/'old.csv';write_csv(path,[r])
    with path.open() as f:records=list(csv.DictReader(f))
    records[0]['target_modules']='all-linear';records[0]['gated']='manual'
    def save():
        with path.open('w',newline='') as f:
            w=csv.DictWriter(f,fieldnames=FIELDS);w.writeheader();w.writerows(records)
    save();actual=read_csv(path)[0]
    assert actual['target_modules']=='all-linear' and actual['gated']=='manual'
    records[0]['files']='[invalid';save()
    with pytest.raises(json.JSONDecodeError):read_csv(path)


def test_reject_nonstandard_layout_but_not_repository_names():
    from atlas.curate_pool import layout_exclusion
    cfg={'model_type':'llama','architectures':['LlamaForCausalLM']}
    assert layout_exclusion(cfg,['openvino_model.bin','openvino_config.json'])=='nonstandard_weight_layout'
    assert layout_exclusion(cfg,['model.safetensors','hybrid_config.json'])=='different_architecture'
    assert layout_exclusion(cfg|{'quantization':{'bits':4,'group_size':64}},['model.safetensors'])=='mlx_quantization'
    assert layout_exclusion(cfg,['pytorch_model-00001-of-00003.bin'])==''
    assert layout_exclusion(cfg,['model-00001-of-00004.safetensors'])==''
    assert layout_exclusion(cfg,['weights/0.pth','config.ini'])=='nonstandard_weight_layout'


def test_modelopt_fp8_is_typed_but_other_precision_is_not_fp8():
    from atlas.curate_pool import classify
    cfg={'quantization_config':{'quant_method':'modelopt','quant_algo':'FP8'}}
    assert classify(['quantized'],cfg,'','org/model')=='quantized_fp8'
    cfg={'quantization_config':{'quant_method':'compressed-tensors','config_groups':{'g':{'weights':{'type':'float','num_bits':4}}}}}
    assert classify(['quantized'],cfg,'','org/model')=='other'


def test_exllama_quantization_is_nonstandard_even_with_hf_filenames():
    from atlas.curate_pool import layout_exclusion
    for method in ('exl2','exl3'):
        assert layout_exclusion({'quantization_config':{'quant_method':method}},['model.safetensors'])=='nonstandard_quantization'


def test_mlx_quantization_with_duplicate_config_fields_is_rejected():
    from atlas.curate_pool import layout_exclusion
    q={'bits':6,'group_size':64}
    assert layout_exclusion({'quantization':q,'quantization_config':q},['model.safetensors'])=='mlx_quantization'


def test_adapter_file_must_be_real_safetensors_with_lora_pairs(tmp_path):
    from atlas.curate_pool import adapter_file_exclusion
    from safetensors.numpy import save_file
    import numpy as np
    path=tmp_path/'adapter_model.safetensors';path.write_text('# not model weights')
    assert adapter_file_exclusion(path)=='invalid_adapter_weights'
    save_file({'base.model.q.lora_A.weight':np.zeros((2,4),dtype=np.float32),
               'base.model.q.lora_B.weight':np.zeros((4,2),dtype=np.float32)},str(path))
    assert adapter_file_exclusion(path)==''


def test_similarity_manifest_requires_all_pairs_and_exact_revisions():
    from atlas.validate_pool import validate_similarities
    adapters=[dict(model_id='a',revision='a'*40,pool='bank',type='lora_adapter'),dict(model_id='b',revision='b'*40,pool='test',type='lora_adapter')]
    pair=dict(model_a='a',model_b='b',revision_a='a'*40,revision_b='b'*40,cosine='.91',threshold='.9',flag='above_threshold')
    assert validate_similarities(adapters,[pair])['pairs']==1
    with pytest.raises(ValueError):validate_similarities(adapters,[])
    with pytest.raises(ValueError):validate_similarities(adapters,[pair|dict(revision_b='c'*40)])
    with pytest.raises(ValueError):validate_similarities(adapters,[pair|dict(flag='')])
