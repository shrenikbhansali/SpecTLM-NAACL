# Operator state (Claude Code)

Newest information first under each heading. Layout defined in MASTER.md §8.8.

## Now
- Time (ET): 2026-10-05 17:35
- Sprint day: Day 1 of 8 (Mon Oct 5)
- Next gate: Gate 1 (engine), due 11 pm ET. **At risk:** B2 code and env are ready (vLLM 0.31.0 env `.venv-atlas-031-clean`, 13 unit tests pass) but `blocked` on the pause marker, because its acceptance needs GPU cells. Same for B3.
- Pause marker: PRESENT.
- Operator worktree: `/home/heck2/sbhansali8/SpecTLM-ops` (branch `claude/ops`; rebase on main, then `git -C ../SpecTLM merge --ff-only claude/ops`; primary tree stays on clean main; Codex uses `.worktrees/<ID>`). Commit as claude-ops with `git -c user.name=... -c user.email=...`; never `git config`.
- Owner decision pending from B6: centering of the delta term (see §1).

## Active jobs
| Run ID | Task | Cluster | Started (ET) | ETA | Status |
| --- | --- | --- | --- | --- | --- |
| (none) | | | | | |

## Queue (ready to launch next)
- A1 (Gate 1): waits on B2 → review, and the pause being lifted.

## Open incidents
- INC-1 (16:48; updated 17:05): HF token at `$HF_HOME/token` is **write**-scoped (`role: write`, display name `spectlm`). At 16:48 codex-1 changed AGENTS.md rule 9 (commit ff2ef3c) to say the owner authorized the write-capable token for reads and downloads on 2026-10-05. There is no §13 row and no journal citation. Treated as owner-authorized; asking the owner to confirm and record it in §13.
- INC-2 (16:48): `/home/heck2` (heck-nfs1, 77 T) is 97% full with 2.5 TB free and shared with other users. B1 downloads of full fine-tunes (~16 GB each) for ~100 candidates per base plus B5 feature capture will not fit. Owner action listed in §1; B1 must check capacity before staging full fine-tunes. **Update ~17:00 (mis-stamped 17:25 in an earlier commit):** B1's Qwen3 draft sample (100 models) totals 1.18 TB (full_finetune 28 × 18.7 GB, rl_tuned 26 × 17.7 GB, lora 28 × 0.5 GB). Llama is likely similar, so both pools need ≈2.3 TB of the 2.5 TB free, before any B5 feature capture. Owner is freeing a few TB (~17:00). **Caveat (17:15):** that sample came from a rate-limited inspection, with 4,131 of 4,876 Qwen3 candidates failing on HF 429; codex-1 restarted with throttling (`B1_*_throttled_20261005`), so pool composition and size will change. Owner asked whether the atlas needs full fine-tunes: per §5.7 the atlas is stratified across types and the method bank is LoRA-only; scope is the owner's call.
- INC-3 (16:48): shared H100/H200 cluster access is unknown. On heck-srv2, `sinfo`/`squeue`/`sacctmgr` fail parsing `/etc/slurm/slurm.conf` (lines 18–19, `AutoDetect=nvml`, `Name=gpu`), which suggests a client/config version mismatch. No ssh config entries or docs name the cluster. This blocks M2/M3 placement (Tue).
- INC-4 **update 17:35:** ~/.cache/pip (written by codex-1's isolated env builds, which ignore the global `no-cache-dir=true`) grew about 900 MB in 30 min and pushed home to 15.86 GB. The operator ran `python3 -m pip --isolated cache purge` (272 files; regenerable cache; no pip process running) → home **15.22 GB**, under the soft limit. **Codex: set `PIP_CACHE_DIR=/home/heck2/sbhansali8/SpecTLM/artifacts/.pip-cache` (or `--no-cache-dir`) for env builds.** The tmux log and python3.9 offload items are still with the owner.
- INC-4 (16:48; updated ~17:00; first written as 17:25, a mis-stamp): home `/nethome/sbhansali8` is **over** its soft quota (15.76 of 15.36 GB; 6-day grace). Causes: `~/.local/state/tmux-persistent/exit.log` is 553 MB because user service `tmux-persistent.service` (`tmux -D`) has crash-looped every ~2 s since Aug, appending one line per exit; `~/.local/lib/python3.9` user site-packages is 7.0 GB (torch 1.7 G, nvidia 4.1 G); `~/.cache/copilot.premigration-20260728` is 764 MB. The operator's offload (move to `/home/heck2` and symlink back) was denied by the permission classifier; the commands were handed to the owner at ~17:00.

## Recently verified
- 17:14 W1 → done (fresh checkout; 2 passed; method 2 pp, atlas 1 pp; no warnings). Non-blocking: build relies on TEXINPUTS=paper/style.

## Inventory (2026-10-05 16:41–16:48 ET)

**Nodes (ssh BatchMode works from heck-srv2 to all):**

| Host | GPUs | State at 16:42 |
| --- | --- | --- |
| heck-srv1 | 8× A40 46 GB | GPUs 0–5 busy (user `adokme3`, vLLM, 41–44 GB each); 6–7 free |
| heck-srv2 (operator host, local) | 8× A40 46 GB | all free |
| heck-srv3 | 8× A40 46 GB | all free |
| heck-srv4 | 8× A40 46 GB | GPU 7: 6.5 GB used (user `swoo81`); 0–6 free |
| heck-srv5 | 8× A40 46 GB | all free |
| heck-srv6 | 4× H200 143 GB | all free. **Dedicated: A9 timing only** |

Total 40 A40s (heck-srv1–5); 33 free at 16:42. Local root disks: 400–735 GB free per node (`/`).

**Shared cluster (H100/H200):** unknown, see INC-3. No Slurm access from heck nodes.

**Storage:**
- `/home/heck2` = `heck-nfs1:/export/data1/data`, 77 T, 75 T used, **2.5 T free (97%)**, mounted on every node.
- `/nethome/sbhansali8` = `ecelinfile6:/export/array201/students/sbhansali8`, user quota 15.26/15.36 GB soft.
- Our usage: `HFcache` 19 GB; `SpecTLM` 60 GB (mostly the historical `tlm-spec-maintenance`).
- `$WS` is unset. Following codex-1 (notes/B1.md), `WS=/home/heck2/sbhansali8/SpecTLM` and artifacts live in `$WS/artifacts/<run_id>/` (gitignored).

**Hugging Face:** `HF_HOME=/home/heck2/sbhansali8/HFcache`; token file `$HF_HOME/token`, **write**-scoped (INC-1).

**Environments (never touch the vLLM 0.17.1 one):**
- `/home/heck2/sbhansali8/condastuff/tlm`: vLLM 0.17.1, torch 2.10.0+cu128, transformers 4.57.6. **Historical harness env; read-only for the sprint.**
- Other conda envs in `condastuff/`, `SpecRouter/envs/` and `~/miniconda3/envs` are unrelated to the sprint.
- No pinned sprint engine env yet (B2 builds it).

## Handoff
- 16:50: O1 claimed, inventory done. Next: ops tooling (`ops/status.sh`, `ops/launch.py`), then the operator loop. Gate 1 needs B2 plus the pause lift.
