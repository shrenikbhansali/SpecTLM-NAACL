# ICE (PACE Slurm) runbook

Prepared by claude-ops 2026-10-07 (task O2). One `main` for both sites (D-18); everything site-specific lives in
`sites/ice.env`. Heck keeps running what is in flight. ICE takes **new, self-contained** work once step 6 passes
(MASTER §3.2; AGENTS rules 2 and 10).

## 0. What is ready and what is not

| Piece | Status |
| --- | --- |
| Exact environment pins for the 4 production venvs (`ops/ice/locks/`, frozen from heck; all 218 pins on PyPI; `speculators` pinned to git 261a82dd) | ready |
| Slurm launch: `ops/launch.py run --node slurm --gpus slurm` (same config.json/run records; adds `sbatch.sh`, `slurm_job_id`, `hardware.txt`) | ready, tested (dry run + mocked sbatch) |
| Batch submit of a jobs.jsonl: `ops/ice/submit.py` (idempotent; refuses heck paths) | ready |
| Pinned model manifest + stager: `ops/ice/models.json`, `ops/ice/stage_models.py` (tiers core / bank / atlas) | ready |
| Engine validation vs heck: `ops/ice/validate.sh` + `validate_compare.py` (vendored 128-prompt file, sha-checked) | ready |
| Artifact copy from heck: `ops/ice/sync_from_heck.sh` | ready (copy only) |
| **Running sealed followspec stages (M2/M3/M4/D-39) on ICE** | **blocked on FIX-19**: sealed manifests store absolute heck paths + hashes; needs a verified path-relocation layer (codex) |
| `followspec` job planners place jobs on `heck-srv*` (`allowed_nodes`) | FIX-19 (site-aware placement) |

## 1. Clone and fill the site file (owner, ~10 min)

```bash
cd <large scratch/project dir>
git clone https://github.com/shrenikbhansali/SpecTLM-NAACL.git SpecTLM && cd SpecTLM
$EDITOR sites/ice.env          # replace every TODO: WS (= this dir), HF_HOME, ICE_PYTHON (3.11.5), SLURM_*, HECK_HOST
git add sites/ice.env && git commit -m "sites: fill ice.env" && git push   # no secrets in this file
source sites/ice.env
```
Python 3.11.5: `module load python/3.11` may give another patch version. If so, `conda create -p $WS/.py3115 python=3.11.5`
and point ICE_PYTHON at `$WS/.py3115/bin/python`. Hugging Face: `export HF_TOKEN=...` in your shell (not in the file).
The token needs access to `meta-llama`. Use it read-only (AGENTS rule 9).

## 2. Check the site
```bash
bash ops/ice/check_site.sh          # PASS/FAIL per item; envs/models show TODO until steps 3–4
```

## 3. Build environments (login node, ~30–60 min)
```bash
bash ops/ice/build_envs.sh          # all four; or name some: atlas-031-clean transport
```
Each env must print `PASS: <env> matches lock`, and the engine lock sha256 must be deb579cd…. A mismatch is a FAIL. Keep the env and
report it; never "fix" by upgrading packages.

## 4. Stage models (login node)
```bash
python3 -m pip install --user huggingface_hub   # or use $ATLAS_PY
$ATLAS_PY ops/ice/stage_models.py --tier core          # ~50 GB: Llama/Qwen3 bases + EAGLE-3 + DFlash drafters
$ATLAS_PY ops/ice/stage_models.py --tier bank          # 30 D-28-eligible Llama bank adapters (training targets)
$ATLAS_PY ops/ice/stage_models.py --check --tier core bank
```
`--tier atlas` (174 models, multi-TB) only if atlas sweeps move to ICE, which is not planned.

## 5. Copy sealed inputs from heck (optional until FIX-19)
```bash
bash ops/ice/sync_from_heck.sh --dry-run && bash ops/ice/sync_from_heck.sh     # ~21 GB
```

## 6. Validate the engine on ICE GPUs (~20 min of GPU)
```bash
bash ops/ice/validate.sh 5          # 5 fresh-compile Gate 1 reference cells via sbatch
squeue -u $USER                     # wait
python3 ops/ice/validate_compare.py # SAME_RANGE or SHIFTED vs heck A40 (mean 3.105030, SD 0.0029, n 20)
```
Record the result in `notes/O2.md` (the operator drafts a ledger entry). **SHIFTED does not mean broken.** It means ICE
numbers go only into ICE-only comparisons. The owner decides whether any table may mix sites. Both arms of a comparison always run
on the same site and GPU type.

## 7. Running work on ICE

- Any launcher job: same arguments as heck, plus `--node slurm --gpus slurm`. Example: see the generated
  `artifacts/ICE_validation_*/jobs.jsonl`. Submit a jobs file with `python3 ops/ice/submit.py --jobs J --log L [--time 24:00:00]`.
- Training jobs: pass `--time` large enough for the arm (heck A40: ~1 step/min FS, 1,294 steps; H100/H200 faster). Record
  GPU type from `hardware.txt` in the run's ledger entry.
- Monitoring: `python3 ops/launch.py list` (uses squeue for Slurm runs), `squeue -u $USER`, `sacct -j <id>`.
- Pause contract, run-ID rules, never-overwrite and clean-checkout guards apply unchanged.

## 8. Agents on ICE
`codex-ice` (builder) follows AGENTS.md. The operator keeps heck. Both coordinate through MASTER §4 rows and `notes/`.
Before launching anything, check for live queues/stages (`squeue -u $USER`, the stage dir), because duplicate launches have happened on heck.
