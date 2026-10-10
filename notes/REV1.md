# REV1 — Review response for the selected Claude final draft

## 2026-10-10T01:23:00-04:00 — codex-1 — Claim / acceptance plan

Owner selected `paper/claude_final` and authorized relevant experiments in response to the supplied review. D53 records that this supersedes the D52 closed run list for these targeted follow-ups. Read AGENTS, MASTER 0–4, latest operational handoff, selected manuscript, and existing P2/D51/D52 analyses. Existing dirty P3/operator/ledger files are preserved.

Acceptance before implementation: (1) map every major reviewer concern to available evidence or a real gap; (2) publish small, matched long-generation and capacity-control jobs only after queue/stage/disk/pause checks and dry runs; (3) keep acceptance on frozen 6da2e42/vLLM0.31.0/A40, identical rendered IDs; (4) audit EDA from its paper and actual code before calling anything EDA; (5) correct factual lineage, cost, crossover, uncertainty and census misunderstandings in the selected draft; (6) compile manuscript and provide a review-response report, immutable job/evidence paths, and handoff. All new results remain pilots, including nulls.

Initial findings: reviewer M1/M4/M5 identify real interpretation or experimental gaps. M3 and W2 have existing model-level and paired-CI evidence missing from the selected draft. EDA is a gated shared/private FFN architecture and target-generated data method; existing decoder LoRA is only a proxy and cannot be called an EDA reproduction. Frozen harness hard-codes greedy sampling but already accepts longer generation limits.
