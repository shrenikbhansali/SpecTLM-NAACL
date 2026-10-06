# FIX-1 — A2 loadability and coherence filter (filed by claude-ops)

## 2026-10-05T20:07-04:00 — claude-ops — Filed

**Gap.** MASTER §6.1 A2 freezes pools after "filters of B1 plus vLLM loadability and coherence (perplexity on the general
set at most 2× base; no degenerate outputs on 10 prompts)". No §7 build task produces this filter. It is evaluation code
on the critical path (A2 → A3 → A4/A7) and beyond an operator script, so it goes to Codex.

**Requested (`atlas/filter_pool.py` + tests), on the pinned engine (B2 env, vLLM 0.31.0):**
1. Input: a B1 pool CSV (model_id, revision, type, staged path; adapters = base + adapter path).
2. Per derivative, one A40: (a) **loadability**: the engine starts with the derivative as target (LoRA via the B2 LoRA path;
   quantized via its native quantization) and the EAGLE-3 drafter attached, so it matches the atlas cell configuration;
   (b) **perplexity** of the derivative on the SPEED-Bench general set (B4's 128 prompts) with an explicitly documented
   definition (e.g., teacher-forced on the base's greedy responses, or on fixed reference continuations; state which),
   and the base's own value under the same definition; (c) **degeneracy**: greedy generation on 10 fixed general
   prompts (≤128 tokens), flagging empty output, immediate EOS, or repetition (e.g., any 4-gram making up > 50% of
   tokens). Thresholds are recorded in the output, and none is tuned after seeing results.
3. Output per derivative: `loadable`, `load_error`, `ppl`, `ppl_ratio_vs_base`, `degenerate_count/10`, sample outputs,
   runtime, GPU; plus config.json per AGENTS rule 5. Resumable, one derivative per process (so the operator can fan out
   with `ops/launch.py`).
4. Acceptance tests: base vs itself gives ratio 1.0 and 0 degenerate; a known-good child (EXP-MTH-018 cell D s0 adapter)
   loads and gives a finite ratio; a deliberately broken input (wrong-architecture repo, e.g. one of the Zebra-Llama
   hybrids, or a non-standard format) is reported `loadable=false` without crashing the run; 5 decoded samples in the journal.

The 2× ratio and the 10-prompt check are MASTER's thresholds; any other threshold needs an owner decision.

## 2026-10-05T22:13:11-04:00 — codex-1 — Claim

Read operator spec, MASTER §6.1 A2/§7 B2, and audit. No remote for pull/rebase. Claim FIX-1 on codex/FIX-1; tests first. B1 corrected curation runs independently. No pause marker; GPU acceptance allowed, full per-pool fanout remains operator-owned. Perplexity will use identical fixed reference text (general prompt tokens, teacher-forced from token2 onward) for base and derivative; masks/scored tokens and definition will be recorded. Generation check uses first10 general prompts and max128 tokens. Exact repetitive-4gram threshold will be a required explicit argument with no silent default, since only the owner may approve additional thresholds.

## 2026-10-05T22:32:58-04:00 — codex-1 — GPU acceptance diagnostics

Tests written first; initial missing-module failure preserved. Fixed Transformers 5 chat-template return type with explicit `return_dict=False`, and added a regression (4 filter tests pass). Commit34f0149. Failed initial reference directory remains preserved. Replacement `artifacts/FIX-1_reference_retry_20261005` contains128 fixed SPEED references,32968 scored tokens,3 truncated at2048 tokens; token1 is unscored. Generation retains the context suffix/assistant header. Exact base/child launch commands and logs are in `artifacts/FIX-1_acceptance_20261005/{base,child}_launch.json` and adjacent logs. Both use pinned vLLM0.31.0, EAGLE-3,K4,fresh compilation,heck-srv2GPU5. No large jobs.

`base`: ```json
{"accepted": null, "degeneracy_n": 10, "degenerate_count": 0, "engine_version": "0.31.0", "gpu_type": "NVIDIA A40", "load_error": null, "loadable": true, "n": 128, "nll_sum": 66256.69197616771, "pending": ["owner repetition threshold"], "ppl": 7.461282909956162, "ppl_ratio_vs_base": 1.0, "repetition_threshold": null, "scored_tokens": 32968, "wall_s": 251.64797094400274}
```

`child`: ```json
{"accepted": null, "degeneracy_n": 10, "degenerate_count": 0, "engine_version": "0.31.0", "gpu_type": "NVIDIA A40", "load_error": null, "loadable": true, "n": 128, "nll_sum": 68050.46503130598, "pending": ["owner repetition threshold"], "ppl": 7.878494964438699, "ppl_ratio_vs_base": 1.0559169327202187, "repetition_threshold": null, "scored_tokens": 32968, "wall_s": 205.0957031020007}
```

`broken`: ```json
{"accepted": false, "load_error": "ValueError: B1 exclusion: nonstandard_weight_layout", "loadable": false, "phase": "input_validation", "ppl": null, "ppl_ratio_vs_base": null, "wall_s": 0.3066386819991749}
```

Base ratio1.0; EXP-MTH-018 Ds0 child ratio1.0559169327202187, finite; nonstandard OpenVINO input returns loadable=false without process failure. These are acceptance diagnostics, not a promoted research comparison. Degeneracy count0/10 here covers empty/immediate-EOS; repetition metrics are recorded but no cutoff was invented. `accepted=null` while the owner repetition-threshold question is pending. Next: append five decoded scoring/generation samples, document operator commands, inspect identity matching, and complete final test suite.
