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
