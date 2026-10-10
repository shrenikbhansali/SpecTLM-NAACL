# Synthesis decisions

This draft was produced after reading both independent manuscripts. The originals in `paper/codex` and `paper/claude` remain unchanged.

## Adopted from the Claude draft

- The searchable title pattern “Mind the Interface,” which immediately names the mechanism and the speculative-decoding setting.
- A direct motivation: target-conditioned drafters are fast because they read target features, and post-training can invalidate that coupling.
- The more explanatory method figure, which depicts the three target-layer taps, dense interface, native multi-step loss, full-repair option, and unchanged deployment path.
- A confident narrative that moves from failure, through localization, to repair and measured serving speed.

## Adopted from the Codex draft

- The lineage-aware frozen 21-checkpoint comparison and its hierarchical confidence intervals, kept distinct from the historical 174-checkpoint inventory.
- The controlled feature-source × verifier-policy crossover and its paired effects.
- The centralized main results table with paired confidence intervals, explicit sample sizes, workload-specific seed counts, and same-drafter reuse baselines.
- Separate component, timing, robustness, and protocol appendices; raw-counter verification and source hashes.
- The four-figure set: detailed method hero, typed-checkpoint retention, matched component ablation, and measured batch-1/batch-8 speedups.

## Excluded or corrected

- Provisional production-64k points were excluded because those jobs had not produced a verified final result at the paper snapshot.
- The model-based dedicated-drafter training-cost range was excluded from the headline because it is an estimate rather than a measured bill.
- Broad claims that all 174 historical derivatives were evaluated in one frozen, typed comparison were replaced by the audited focused panel and a provenance-distinct inventory description.
- Nemotron MATH results remain labeled as MATH-64, while R1 MATH-500 remains seed 0; they are not presented as matched full-benchmark replications.
- Interface repair is presented as the primary adaptation point, while the paper retains evidence that policy change and non-interface draft components also contribute.

The result keeps the Claude draft's clarity and visual explanation while using the Codex draft's evidence discipline and complete reproducibility package.
