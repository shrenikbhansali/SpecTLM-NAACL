# FIX-19: verified relocation and site-aware jobs

## 2026-10-07T19:20:09.851529-04:00 — codex-1 — Claim and acceptance specification

Prepare ICE without changing the running heck evaluation harness or metrics. Tests first: opt-in read-time path remapping leaves original bytes/seals untouched; validates every copied file hash and rejects missing/changed inputs, traversal and collisions; preserves prompt/response content and tokens; defaults unchanged. Sealed training/evaluation fixture must load from copied paths with original proofs; runtime training must inherit the same mapping. SITE=ice emits Slurm node/GPU placement and local paths; heck defaults remain identical. Submission and dry-run paths accept generated placement exactly once. No ICE GPU jobs until actual site/env configuration and engine validation are available.
