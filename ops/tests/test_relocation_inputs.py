import json
from pathlib import Path
import pytest
from ops.ice.relocation_inputs import training_inputs
from followspec.tests.test_training_jobs import final_stage


def test_training_copy_list_includes_sealed_and_runtime_dependencies(tmp_path):
    final=final_stage(tmp_path);config=json.loads((final/'config.json').read_text());spec=config['spec']
    for key in ('base_snapshot','drafter_snapshot'):
        p=Path(spec[key]);p.mkdir();(p/'config.json').write_text('{}');(p/'model.safetensors').write_bytes(b'weights')
    files=training_inputs(final)
    assert final/'FS/manifest.json' in files and final/'stage_files.json' in files
    assert final/'FS/decoded_masks.jsonl' in files
    assert Path(spec['base_snapshot'])/'model.safetensors' in files
    assert Path(spec['code_repo'])/'atlas/env/requirements.lock' in files
    (Path(spec['drafter_snapshot'])/'model.safetensors').unlink()
    (Path(spec['drafter_snapshot'])/'config.json').unlink()
    with pytest.raises(ValueError,match='empty'):training_inputs(final)
