# ICE (Slurm) launching — stub

`ops/launch.py` launches over ssh on heck-srv and is not used on ICE. On ICE, every job is an sbatch script that:
1. `source sites/ice.env`; refuses to run if `$PAUSE_MARKER` exists;
2. runs from a detached worktree at a pushed `run-*` tag on main (`$RUN_ROOT/<tag>`), never a dirty checkout;
3. writes `$WS/artifacts/<run_id>/config.json` with the same fields as `ops/launch.py` (model IDs + revisions, engine lock path
   and sha256, code commit and tag, seed, K, prompt-file sha256, **GPU type**, Slurm job ID, node);
4. uses run IDs `<task>-<base>-<drafter>-k<K>-s<seed>-<YYYYMMDDHHMM>[-<tag>][-rNN]` (MASTER §8.2) and never reuses a directory.
A tested sbatch wrapper is a FIX row for codex once ICE values in `sites/ice.env` are filled (no guessing of cluster settings).
