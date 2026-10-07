# Gate 2 method data and training verification

2026-10-06T22:29:10.136664-04:00 — codex-1; pilot evidence.

M2 data and M3 training prerequisites pass. The owner explicitly approved deterministic native-batch subdivision and proceeding after remaining checks; D-36 records the policy. This report covers the method path. B9 transport validation remains failed and blocks A8 only. No held-out method performance result or Gate 3 decision is implied.

| Check | Evidence |
| --- | --- |
| Fresh bank and mixture admission | `artifacts/M1_D28_20261006/admission2/results.json`: 30 bank, 30 admitted mixtures after D-33 re-plan; M1 operator done |
| Complete generation | `artifacts/M2_D28_20261006/responses_parent_parallel`: 136 successful jobs, strict 16-shard parent join |
| Actual sample masks and strings | `artifacts/FIX12_acceptance_20261006/decoded_review.txt`: five per arm; reviewed response-only and shifted masks |
| Prompt separation | Assembly has 512 distinct validation prompts, 38,326 distinct training prompt hashes, zero overlap; full evaluation exclusions checked in manifests |
| Matched batches | `artifacts/FIX12_acceptance_20261006/native_acceptance.json`: all 12 schedules replay exactly, 10,320,835 shifted sequence tokens, 1,294 steps, 8,192-token ceiling; 15 total splits, sample order and coverage preserved |
| Feature capture | `artifacts/B5_operator_native_recheck_20261006/results.json`: fresh-forward and scale-zero checks pass |
| Full response/rank96 training capacity | `artifacts/B6_operator_capacity_recheck_20261006/results.json`: actual passing capacity evidence, both required memory flags |
| Longer overfit and native export | `artifacts/B6_overfit30_20261006/acceptance.json`: 30-step bounded overfit/export acceptance |
| Sealed final data/configs | `artifacts/M2_D28_20261006/finalized_D36/results.json`: all readiness fields true, no blockers; D-36 approval and mask/feature/capacity hashes in config.json |

Historical pending-approval and failed suffix-only outputs remain unchanged. Some generated responses contain errors or end at the approved cap/paired trim; they were inspected and retained without new quality filtering. The default suffix-only procedure remains unchanged in code; production explicitly enables the approved subdivision policy.

M3 execution evidence is recorded in `notes/M3.md` and `artifacts/M3_D36_20261006`. Production checkpoints still require successful training and real vLLM loading before held-out comparisons.
