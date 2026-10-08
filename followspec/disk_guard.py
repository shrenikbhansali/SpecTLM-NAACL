"""Opt-in free-space guard. GB means decimal gigabytes, matching the disk budget."""
from pathlib import Path
import shutil


def require_free(path, minimum_gb=0):
    if minimum_gb <= 0:
        return
    parent = Path(path).resolve()
    while not parent.exists():
        parent = parent.parent
    free = shutil.disk_usage(parent).free / 10**9
    if free < minimum_gb:
        raise RuntimeError(f'free disk {free:.1f} GB below required {minimum_gb:g} GB at {parent}')
