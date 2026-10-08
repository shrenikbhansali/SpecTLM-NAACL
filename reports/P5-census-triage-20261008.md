# P5 historical census triage — 2026-10-08

**Retrospective pilot, all174 checkpoints retained.** The broader own-domain census gives full16-request AUROC0.908[0.668,0.983] for EAGLE-3 and0.934[0.745,0.993] for DFlash. Ranking is useful on these observed models, but the fixed0.9 threshold misses5/14 and3/17 degraded checkpoints. The shortest prefix has more false positives. This does not establish performance on future checkpoints.

Each model contributes two outcome-blind SHA256-selected batches (16queries) for the probe and its remaining48 own-domain or112 fallback queries for labels. A00/A10 use the same prompt IDs. Label and prediction thresholds remain first-position retention<0.9. Seven checkpoints have paired zero-step exclusions; all348 method/checkpoint records remain defined. No collapsed/short-output model was removed.

| Population | Drafter | Probe | Checkpoints / degraded | AUROC [95% CI] | TP / FP / FN / TN |
|---|---|---|---|---|---|
| derivative-own-64 | eagle3 | full16requests | 163 / 14 | 0.908 [0.668, 0.983] | 9 / 3 / 5 / 146 |
| derivative-own-64 | eagle3 | prefix16iterations | 163 / 14 | 0.888 [0.608, 0.971] | 8 / 9 / 6 / 140 |
| general-fallback-128 | eagle3 | full16requests | 11 / 1 | 1.000 [0.000, 1.000] | 1 / 0 / 0 / 10 |
| general-fallback-128 | eagle3 | prefix16iterations | 11 / 1 | 1.000 [0.900, 1.000] | 1 / 0 / 0 / 10 |
| derivative-own-64 | dflash | full16requests | 163 / 17 | 0.934 [0.745, 0.993] | 14 / 4 / 3 / 142 |
| derivative-own-64 | dflash | prefix16iterations | 163 / 17 | 0.929 [0.709, 0.981] | 15 / 10 / 2 / 136 |
| general-fallback-128 | dflash | full16requests | 11 / 2 | 0.944 [0.417, 1.000] | 2 / 1 / 0 / 8 |
| general-fallback-128 | dflash | prefix16iterations | 11 / 2 | 1.000 [0.333, 1.000] | 2 / 0 / 0 / 9 |

Intervals use3000 checkpoint and paired-query draws, recomputing noisy probe scores and labels. Identical query-ID sets share draws across checkpoints/methods. Probe and label queries remain disjoint. One-class draws are excluded and counted in the source. The11-checkpoint fallback subset has only1/2 degraded checkpoints; its estimates and intervals are unstable. Related lineages and model-specific own-domain prompts limit population and causal interpretations.

Observed full-probe generation costs sum the two batches and both target arms: median24.7seconds for EAGLE and18.8seconds for DFlash on own-domain queries. Loading/initialization adds median306.4/315.5seconds. Prefix16 is reconstructed from full saved counters; its wall-clock cost was not measured. These times exclude creating the own-domain query sets and do not demonstrate end-to-end deployment savings.

Historical provenance stays explicit: source harness commits423d3b6/f00992f, vLLM0.31.0, A40, greedy,batch8,512tokens. FIX23 independently established unchanged generation calls and reconstructed frozen6da2e42metrics with paired D32 exclusions. These are audited historical observations, not newly launched frozen-harness cells, and remain separate from the21-checkpoint SPEED analysis.

Source: [artifacts/P5_census_20261008_1702/analysis-v2/results.json](../artifacts/P5_census_20261008_1702/analysis-v2/results.json); script analyze_v2.py and immutable raw hashes. AUROC synthetic checks and actual348 pairing/exclusion/batch assertions pass. Initialanalysis also reproduced central estimates but used independent query draws for shared query sets; analysis-v2 supersedes those CIs, preserving the original files.

Prospective new-checkpoint validation, self-elicited deployment-query evaluation, and measured short-probe timing remain open. No threshold is tuned from these results.
