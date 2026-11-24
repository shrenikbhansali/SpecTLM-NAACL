# E4 — implementation choices fixed before evaluation

Reference implementation: https://github.com/Lyn-Lucy/Efficient-Draft-Adaptation at a29f0381479a92d0f3114fd264cd790bab3a208b. `git ls-remote HEAD` on 2026-11-24 confirms the release is unchanged from the pinned October audit. Paper: https://arxiv.org/abs/2603.09527, v1.

The primary port follows the released training script's one shared and one private expert, with independent singleton softmax gates. These gates each equal one, so their gradients are zero and the output is the sum of two SwiGLU experts. Both routing vectors remain present/trainable as requested by the handoff; their zero-gradient behavior is recorded. The shared expert is initialized from the released EAGLE-3 MLP. Interface, attention, norms, head and shared expert remain frozen. Private weights use nn.Linear's initialization. This comparison preserves the native EAGLE-3 TTT objective and three target taps.

Matched private width:4096, yielding 50,339,840 private/router parameters at hidden size4096. Repo-default private width is the released decoder intermediate size14336. Report the exact instantiated parameter counts for each run. PCA dimension128 and per-response90th-percentile squared Mahalanobis score are explicit port choices because the repository does not implement or specify them. Keep the highest-scoring8k of16k; freeze scoring choices before acceptance evaluation. PCA statistics use only the separate general-generation reference.

Deployment finding from implementation/tests: the released-code additive pair can be folded into one wider ordinary SwiGLU by concatenating gate/up rows and down columns. This preserves the mathematical function and standard state-dict keys, with a larger intermediate_size. FP64 forward/input-gradient and native merged-state round-trip tests pass. This is a potentially compatible export for unmodified vLLM; actual engine loading, untrained acceptance and bf16 numerical behavior are still unverified. It must not be reported as demonstrated serving compatibility yet.

The paper's joint gate would be a separate variant, not silently substituted for the release. No variant or selection hyperparameter will be chosen by obtaining a weak baseline result. The experiment reports the actual outcomes.

## 2026-11-24T15:38:56.145250-05:00 — serving sanity complete
Both private widths4096/14336 load through frozen6da2e42/vLLM0.31 without source patches. Native target embedding is recorded by the FIX24 proof. On identical R1 SPEED128 renders, tau1.7854/1.7869 against reuse1.7831;10k paired CIs include zero for both differences. Independent raw reduction: sanity_20261124_1538/results.json. This supersedes the earlier unverified-serving status, not the fixed implementation/selection choices. Training and selection are still pending.

## 2026-11-24T16:08:19-05:00 — native training smoke
Width4096 completed two optimizer steps through the FIX24/nativeTTT3 path and exported, with only private expert/router trainable. Source run E4_t0_train_smoke_w4096_s0. Reference2000 generation and exact target-state captures are now in the canonical queue. No trained acceptance claim yet.

## 2026-11-24T16:34:20.917107-05:00 — trained export and frozen-weight checks
Both widths also pass native two-step training/export and frozen-vLLM serving smoke checks. Independent direct safetensors inspection of width4096 proves all16 frozen tensors (including the shared FFN prefix and FIX24 target embedding) exactly match their intended source. The same check gates production EDA acceptance. Standalone b1 first-draft medians after50warmup/1000measured forwards are3.317ms released,3.364ms width4096,3.378ms width14336. These CUDA-event measurements include fc/decoder/head, no existing KV context or verifier; they are not end-to-end speedups. No trained-baseline acceptance result yet.

## Candidate/subset inspection
Fixed seed904 random24 candidate strings and masks were read before PCA selection (E4_candidate_review_20261124_1648). Each new subset must contain at least five byte-identical inspected members, with explicit sample IDs in its audit; otherwise training remains blocked. This is structural/provenance inspection, not answer-correctness certification. Some target factual errors and a repeated phrase were observed and retained to preserve the specified shared corpus. Full16k descriptive counts: R1 repeated4gram>50%5/16000 and cap11517/16000; Nemotron14/16000 and cap3019/16000. Selection-subset counts are generated separately without filtering.
