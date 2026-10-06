# FIX-6 — zero-step requests and paired analysis

## 2026-10-06T12:55:54-04:00 — codex-1 — Claim

Read D32 and A4 failure evidence. Record requests with no speculative steps using zero counters, zero_step=true and null undefined metrics; exclude from cell macro, report total/valid/zero counts. Pairwise analyses must intersect nonzero prompt IDs and report exclusions; never compare independent per-cell subsets. Preserve existing normal outputs and historical artifacts. Write regression tests first, then implementation, including strict malformed-counter rejection and all-zero behavior. No GPU production submission; original failed cells require operator retries with new IDs. FIX4 CPU materialization proceeds in background; no active pause marker.
