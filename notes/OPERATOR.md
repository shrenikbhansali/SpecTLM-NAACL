# Operator state (Claude Code)

Newest information first under each heading. Layout defined in MASTER.md §8.8.

## Now
- Time (ET): 2026-10-05 16:50
- Sprint day: Day 1 of 8 (Mon Oct 5)
- Next gate: Gate 1 (engine), due Mon Oct 5, 11 pm ET. Needs B2 in review **and** the pause marker lifted.
- Pause marker: PRESENT (`tlm-spec-maintenance/EXPERIMENTS_PAUSED.json`).
- Operator worktree: `/home/heck2/sbhansali8/SpecTLM-ops` (branch `claude/ops`; rebase on main, then update main with `git -C ../SpecTLM merge --ff-only claude/ops` (primary tree stays on clean main; Codex uses `.worktrees/<ID>`)).

## Active jobs
| Run ID | Task | Cluster | Started (ET) | ETA | Status |
| --- | --- | --- | --- | --- | --- |
| (none) | | | | | |

## Queue (ready to launch next)
- A1 (Gate 1): waits on B2 → review, and the pause being lifted.

## Open incidents
- INC-1 (16:48; updated 17:05): HF token at `$HF_HOME/token` is **write**-scoped (`role: write`, display name `spectlm`). At 16:48 codex-1 changed AGENTS.md rule 9 (commit ff2ef3c) to say the owner authorized the write-capable token for reads and downloads on 2026-10-05. There is no §13 row and no journal citation. Treated as owner-authorized; asking the owner to confirm and record it in §13.
- INC-2 (16:48): `/home/heck2` (heck-nfs1, 77 T) is 97% full with 2.5 TB free and shared with other users. B1 downloads of full fine-tunes (~16 GB each) for ~100 candidates per base plus B5 feature capture will not fit. Owner action listed in §1; B1 must check capacity before staging full fine-tunes.
- INC-3 (16:48): shared H100/H200 cluster access is unknown. On heck-srv2, `sinfo`/`squeue`/`sacctmgr` fail parsing `/etc/slurm/slurm.conf` (lines 18–19, `AutoDetect=nvml`, `Name=gpu`), which suggests a client/config version mismatch. No ssh config entries or docs name the cluster. This blocks M2/M3 placement (Tue).
- INC-4 (16:48): home quota `/nethome/sbhansali8` at 15262 MB used of 15360 MB soft (16384 MB hard). Anything writing to `~` (pip/conda caches, `~/.cache`, agent logs) may fail. Keep caches on `/home/heck2`.

## Recently verified
- (none yet)

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
