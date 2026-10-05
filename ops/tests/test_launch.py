"""Tests for ops/launch.py guards, run IDs and config.json contents."""
import datetime as dt
import hashlib
import importlib.util
import json
import subprocess
from pathlib import Path

import pytest

SPEC = importlib.util.spec_from_file_location("launch", Path(__file__).resolve().parents[1] / "launch.py")


@pytest.fixture
def L(tmp_path, monkeypatch):
    mod = importlib.util.module_from_spec(SPEC)
    SPEC.loader.exec_module(mod)
    repo = tmp_path / "repo"
    repo.mkdir()
    for c in (["init", "-q", "-b", "main"], ["config", "user.email", "t@t"], ["config", "user.name", "t"]):
        subprocess.run(["git", *c], cwd=repo, check=True)
    (repo / "f.txt").write_text("x")
    subprocess.run(["git", "add", "."], cwd=repo, check=True)
    subprocess.run(["git", "commit", "-qm", "init"], cwd=repo, check=True)
    monkeypatch.setattr(mod, "WS", tmp_path / "ws")
    monkeypatch.setattr(mod, "REGISTRY", tmp_path / "ws" / "ops" / "runs.jsonl")
    monkeypatch.setattr(mod, "PAUSE_MARKER", tmp_path / "EXPERIMENTS_PAUSED.json")
    mod._repo = repo
    mod._tmp = tmp_path
    return mod


def base_args(L, *extra):
    prompts = L._tmp / "prompts.jsonl"
    prompts.write_text('{"prompt": "hi"}\n')
    lock = L._tmp / "vllm.lock"
    lock.write_text("torch==2.9.0\nvllm==0.22.0\n")
    return ["run", "--task", "A1", "--base", "llama", "--drafter", "eagle3", "--k", "4", "--seed", "0",
            "--node", "heck-srv3", "--gpus", "0", "--no-resolve",
            "--target", "meta-llama/Llama-3.1-8B-Instruct", "--target-rev", "a" * 40,
            "--drafter-model", "RedHatAI/Llama-3.1-8B-Instruct-speculator.eagle3", "--drafter-rev", "b" * 40,
            "--prompts", str(prompts), "--engine-lock", str(lock), "--code-repo", str(L._repo),
            *extra, "--", "echo", "{run_id}", "{out_dir}"]


def test_run_id_format(L):
    when = dt.datetime(2026, 10, 5, 21, 7, tzinfo=L.ET)
    assert L.make_run_id("A1", "llama", "eagle3", 4, 0, when) == "A1-llama-eagle3-k4-s0-202610052107"
    assert L.make_run_id("A1", "llama", "eagle3", 4, 0, when, rep=3) == "A1-llama-eagle3-k4-s0-202610052107-r03"


def test_dry_run_writes_complete_config(L):
    assert L.main(base_args(L, "--dry-run")) == 0
    (d,) = (L.WS / "artifacts" / "_dryrun").iterdir()
    cfg = json.loads((d / "config.json").read_text())
    assert cfg["run_id"] == d.name
    assert cfg["models"]["target"]["revision"] == "a" * 40
    assert cfg["models"]["drafter"]["revision"] == "b" * 40
    assert cfg["K"] == 4 and cfg["seed"] == 0
    assert cfg["engine"]["vllm"] == "0.22.0" and len(cfg["engine"]["lock_sha256"]) == 64
    assert cfg["prompts"]["sha256"] == hashlib.sha256(b'{"prompt": "hi"}\n').hexdigest()
    assert len(cfg["code"]["commit"]) == 40 and cfg["code"]["dirty"] is False
    assert cfg["launch"]["command"] == ["echo", d.name, str(d)]


def test_refuses_existing_dir(L):
    assert L.main(base_args(L, "--dry-run", "--rep", "1")) == 0
    assert L.main(base_args(L, "--dry-run", "--rep", "1")) == 2  # same minute, same rep -> refuse


def test_pause_marker_blocks_real_launch(L, monkeypatch):
    L.PAUSE_MARKER.write_text("{}")
    monkeypatch.setattr(L.subprocess, "run", lambda *a, **k: pytest.fail("must not ssh while paused"))
    assert L.main(base_args(L)) == 2
    assert not (L.WS / "artifacts").exists()


def test_dedicated_h200_only_for_a9(L):
    args = base_args(L, "--dry-run")
    args[args.index("heck-srv3")] = "heck-srv6"
    assert L.main(args) == 2
    args[args.index("A1")] = "A9"
    assert L.main(args) == 0


def test_real_run_requires_clean_main(L):
    (L._repo / "f.txt").write_text("dirty")
    with pytest.raises(L.LaunchError, match="dirty"):
        L.check_guards(L.main.__globals__["argparse"].Namespace(
            node="heck-srv3", task="A1", dry_run=False, code_repo=str(L._repo), allow_branch=False,
            engine_lock="x", prompts="y"))


def test_unresolved_local_path_needs_revision(L):
    with pytest.raises(L.LaunchError):
        L.resolve_revision(str(L._tmp), None)
