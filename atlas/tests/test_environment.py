"""B2 environment acceptance: exact pinned version, clean dependencies."""
import importlib.metadata
import json
from pathlib import Path
import subprocess
import sys


def test_engine_matches_committed_pin():
    lock=json.loads((Path(__file__).parents[1]/'env/engine.json').read_text())
    assert importlib.metadata.version('vllm') == lock['vllm_version']


def test_dependency_consistency():
    subprocess.run([sys.executable,'-m','pip','check'],check=True)
