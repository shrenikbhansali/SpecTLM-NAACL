### EXP-ATL-015 — Track T phase 1b: domain/model separation, dedicated drafter and KL

**Landed:** 2026-10-08.

**Status:** pilot; D-44 exploratory, no certification or framing decision.

**What / why.** Test whether reasoning-target acceptance loss is due to text versus target-conditioned model changes; measure a dedicated-drafter reference; compare RL and distillation with child‖base KL.

**New.** Nine online cells, eight HF teacher-forced conditions, seventeen trace KL diagnostics. No training. Explicit vocabulary-support handling for Tülu; incomplete RL step expansion is reported, not hidden.

**Artifacts.** `artifacts/T1b_report_20261008_0200/` contains raw re-derivation, source hashes, results, KL points, PNG/PDF. Run/data/model staging paths are listed in [the report](../reports/T1-phase1b-20261008.md).

**Config + results.** vLLM0.31.0 frozen6da2e42, greedy seed0, batch8,512tokens, K4/K16, fresh compile,n128; HFbf16/eager torch2.13.0/transformers5.16.1, code44c5fbb/7bc01c1,n8fixed queries/traces. All revision and prompt hashes in run configs.

- Thinking-mode p1 retention EAGLE1.038[1.000,1.080],DFlash.923[.898,.951]; DFlashτretention.692[.639,.752].
- Dedicated R1 drafter p1.411→.705 (Δ+.294[+.278,+.310]),τ1.730→2.848 (Δ+1.118[+1.054,+1.183]);n128. Model-specific card training data/cost unknown.
- On identical child text, HF child-minus-Instruct macro agreement: R1−.058[−.080,−.037],Nemotron−.097[−.130,−.057];n8. Text-only contrasts are uncertain for R1 and negative for Nemotron; token-weighted versus macro conclusions differ.
- New TMLR RL-from-base: p1 retention1.027[.998,1.059] EAGLE/.903[.870,.936] DFlash; no repetition flags,n128. KL.436,n8.
- KL: DeepMathRL50/.150steps .0028/.0146; R1Llama.768,Nemotron.943,R1Qwen1.026; SwallowRL1.065 with poor retention. Tülu conditional-KL decreases while retention worsens. Full table and all intervals in report/JSON.

**Caveats.** n8 nonrandom prefix diagnostic; no run-to-run uncertainty. Prompt bootstrap conditional on the panel/one run. Truncations, synthetic/factual errors and model-specific templates remain. HF agreement is not online acceptance. Tülu full KL is infinite under zero-extended support; conditional KL labeled separately. Atlas KL context distribution differs. RL step expansion blocked by empty repositories/unknown licenses; existing2886/4461 have license provenance gaps and overwhelmingly repetitive outputs, excluded from realistic-drift interpretation. No speedup or correctness claim; D-44, not a test/promoted conclusion of EXP-ATL-000.
