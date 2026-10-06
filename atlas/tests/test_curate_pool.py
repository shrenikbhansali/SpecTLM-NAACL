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
