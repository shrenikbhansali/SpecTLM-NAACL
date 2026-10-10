### EXP-ATL-026 — ReFit extended-generation, capacity and supervision controls

**Landed:** 2026-10-10, codex-1; owner D53 and second-review instruction.

**Status:** pilot, partial results; remaining jobs running/queued. No certification or manuscript edits.

**What / why.** Test whether repair persists beyond512-token training contexts, under sampling, at matched trainable capacity, and when identical derivative-generated contexts are supervised by the family parent instead of the derivative.

**New.** Twenty-one frozen greedy MATH32 cells at512/2048/8192 tokens; seven separate sampled8192 cells atT=.6/p=.95; seven300-step component/supervision controls with14 frozen held-out evaluations. Full-rank q/o and rank655 decoder updates match the50.33M interface budget; fc-r75 exactly matches decoder-r16's1.2288M budget. Parent-supervision preserves response tokens/initialization and changes HF taps plus soft labels. One bounded decoder-r16 learning-rate check at1e-4 complements existing2e-5.

**Artifacts.** `artifacts/REV1_20261010_0130`, `REV1_controls_20261010_0140`, `REV1_sampled_20261010_0140`; plans/jobs/preflights/watch logs/configs/raw counters. Analysis `artifacts/REV1_analysis_20261010_0140/{report.md,results.json}`; source `followspec/review_analysis.py`. Report `reports/REV1-paper-strengthening-20261010.md`; journal `notes/REV1.md`.

**Config + results.** Primary greedy cells: frozen6da2e42, vLLM0.31.0, A40,K4,b8,seed0,max model length12288; identical fixed first32 MATH64 rendered IDs, chosen before outcomes. Official reuse/fc16k/full16k on R1/Nemotron plus R1 dedicated. R1 cap2048 n32: reusedp1.536,τ2.080; fc p1.736,τ2.858,Δp1.200[.184,.215],Δτ.777[.718,.839]; fullp1.769,τ3.042,Δp1.232[.216,.249],Δτ.961[.897,1.026].10,000 paired query draws,seed20261010. No repeated4-gram flag in these32 outputs/arm;18–20 requests hit2048. Supplemental sampling uses explicit opt-in extension tagged1ffbf2b, same engine; not pooled with frozen primary. Training controls reuse D46 self256/300steps/TTT3/seed0 and production initialization. Compact/shared exports,350GB floor, all publications dry-run and duplicate checked.

**Caveats.** Small fixed-panel pilots, one seed for new controls. Generated trajectories/lengths vary across arms even with identical prompts. The larger caps are not proof of complete reasoning. Position summaries reconstruct verified-token progress with a final-truncation audit. Parent supervision sees unchanged R1 special IDs with seven logged string aliases, not remapped parent-role tokens. Capacity/location/optimization controls are not exact EDA. EDA implementation audit and all null/failed controls are retained. Initial parent-vocabulary dry run failed before publication and was corrected with explicit lexical-ID and alias validation. No timing gain is inferred from acceptance alone.

- 2026-10-10T01:44:25.781423-04:00: **23/42** new acceptance cells complete. [Long/sampled results](../artifacts/REV1_evidence_watch_20261010/snapshot-20261010_014425/report.md); [component/supervision results](../artifacts/REV1_evidence_watch_20261010/snapshot-20261010_014425/components.md). All are raw-recomputed pilots; pending and null arms retained.

- 2026-10-10T01:45:02.537232-04:00: **24/42** new acceptance cells complete. [Long/sampled results](../artifacts/REV1_evidence_watch_20261010/snapshot-20261010_014502/report.md); [component/supervision results](../artifacts/REV1_evidence_watch_20261010/snapshot-20261010_014502/components.md). All are raw-recomputed pilots; pending and null arms retained.

- 2026-10-10T01:46:36.214412-04:00: **27/42** new acceptance cells complete. [Long/sampled results](../artifacts/REV1_evidence_watch_20261010/snapshot-20261010_014636/report.md); [component/supervision results](../artifacts/REV1_evidence_watch_20261010/snapshot-20261010_014636/components.md). All are raw-recomputed pilots; pending and null arms retained.

- 2026-10-10T01:47:40.300250-04:00: **29/42** new acceptance cells complete. [Long/sampled results](../artifacts/REV1_evidence_watch_20261010/snapshot-20261010_014740/report.md); [component/supervision results](../artifacts/REV1_evidence_watch_20261010/snapshot-20261010_014740/components.md). All are raw-recomputed pilots; pending and null arms retained.

- 2026-10-10T01:48:44.720592-04:00: **30/42** new acceptance cells complete. [Long/sampled results](../artifacts/REV1_evidence_watch_20261010/snapshot-20261010_014844/report.md); [component/supervision results](../artifacts/REV1_evidence_watch_20261010/snapshot-20261010_014844/components.md). All are raw-recomputed pilots; pending and null arms retained.

- 2026-10-10T01:49:19.271369-04:00: **31/42** new acceptance cells complete. [Long/sampled results](../artifacts/REV1_evidence_watch_20261010/snapshot-20261010_014919/report.md); [component/supervision results](../artifacts/REV1_evidence_watch_20261010/snapshot-20261010_014919/components.md). All are raw-recomputed pilots; pending and null arms retained.

- 2026-10-10T01:51:54.197649-04:00: **32/42** new acceptance cells complete. [Long/sampled results](../artifacts/REV1_evidence_watch_20261010/snapshot-20261010_015154/report.md); [component/supervision results](../artifacts/REV1_evidence_watch_20261010/snapshot-20261010_015154/components.md). All are raw-recomputed pilots; pending and null arms retained.

- 2026-10-10T01:55:29.394871-04:00: **33/42** new acceptance cells complete. [Long/sampled results](../artifacts/REV1_evidence_watch_20261010/snapshot-20261010_015529/report.md); [component/supervision results](../artifacts/REV1_evidence_watch_20261010/snapshot-20261010_015529/components.md). All are raw-recomputed pilots; pending and null arms retained.

- 2026-10-10T01:57:34.698519-04:00: **34/42** new acceptance cells complete. [Long/sampled results](../artifacts/REV1_evidence_watch_20261010/snapshot-20261010_015734/report.md); [component/supervision results](../artifacts/REV1_evidence_watch_20261010/snapshot-20261010_015734/components.md). All are raw-recomputed pilots; pending and null arms retained.

- 2026-10-10T01:58:10.093737-04:00: **35/42** new acceptance cells complete. [Long/sampled results](../artifacts/REV1_evidence_watch_20261010/snapshot-20261010_015810/report.md); [component/supervision results](../artifacts/REV1_evidence_watch_20261010/snapshot-20261010_015810/components.md). All are raw-recomputed pilots; pending and null arms retained.

- 2026-10-10T01:58:46.005772-04:00: **36/42** new acceptance cells complete. [Long/sampled results](../artifacts/REV1_evidence_watch_20261010/snapshot-20261010_015846/report.md); [component/supervision results](../artifacts/REV1_evidence_watch_20261010/snapshot-20261010_015846/components.md). All are raw-recomputed pilots; pending and null arms retained.

- 2026-10-10T01:59:22.205454-04:00: **38/42** new acceptance cells complete. [Long/sampled results](../artifacts/REV1_evidence_watch_20261010/snapshot-20261010_015922/report.md); [component/supervision results](../artifacts/REV1_evidence_watch_20261010/snapshot-20261010_015922/components.md). All are raw-recomputed pilots; pending and null arms retained.

- 2026-10-10T01:59:58.951243-04:00: **39/42** new acceptance cells complete. [Long/sampled results](../artifacts/REV1_evidence_watch_20261010/snapshot-20261010_015958/report.md); [component/supervision results](../artifacts/REV1_evidence_watch_20261010/snapshot-20261010_015958/components.md). All are raw-recomputed pilots; pending and null arms retained.

- 2026-10-10T02:01:06.318244-04:00: **41/42** new acceptance cells complete. [Long/sampled results](../artifacts/REV1_evidence_watch_20261010/snapshot-20261010_020106/report.md); [component/supervision results](../artifacts/REV1_evidence_watch_20261010/snapshot-20261010_020106/components.md). All are raw-recomputed pilots; pending and null arms retained.

- 2026-10-10T02:01:44.809810-04:00: **42/42** new acceptance cells complete. [Long/sampled results](../artifacts/REV1_evidence_watch_20261010/snapshot-20261010_020144/report.md); [component/supervision results](../artifacts/REV1_evidence_watch_20261010/snapshot-20261010_020144/components.md). All are raw-recomputed pilots; pending and null arms retained.

### 2026-10-10T02:31:15.670216-04:00 — completed pilot batch

All42 evaluation cells and7 training controls complete;7 matched-data/budget audits and26 regression tests pass. Final raw-recomputed tables andCIs: [long/sampling](../artifacts/REV1_evidence_watch_20261010/snapshot-20261010_020144/report.md), [components/supervision](../artifacts/REV1_evidence_watch_20261010/snapshot-20261010_020144/components.md). [Completed synthesis](../reports/REV1-paper-strengthening-20261010.md). All nulls and capacity/LR counterexamples retained; sampling remains explicitlysupplementary. Status remains pilot.
