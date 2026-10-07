"""Serialize planners which share inference exports, outside frozen eval code."""
import fcntl
from pathlib import Path


def locked_evaluation(planner,training,*args,**kwargs):
    stage=Path(training).resolve()
    if not stage.is_dir():raise ValueError('training stage required')
    with (stage/'inference_planning.lock').open('a+') as lock:
        fcntl.flock(lock,fcntl.LOCK_EX)
        try:return planner(training,*args,**kwargs)
        finally:fcntl.flock(lock,fcntl.LOCK_UN)
