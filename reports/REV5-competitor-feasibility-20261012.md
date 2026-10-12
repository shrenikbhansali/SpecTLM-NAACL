# Competing-method comparison: feasibility and elapsed estimates

October12,2026; codex-1. Read-only feasibility audit requested by owner. SPD means **Speculative Pipeline Decoding**, as confirmed by the owner. No new competing-method jobs have been launched; the frozen env is unchanged.

**EDA is the highest-value comparison, but a faithful comparison is not a three-hour addition from the current state.** The implementation work, missing compatible pretrained drafter, and evaluation compatibility dominate the schedule. The figures below are planning estimates, not measured runtimes or reservations. Scope: one target, one seed, existing16k response corpus where usable,128 held-out queries at512 cap, correctness checks and paired analysis; not full two-target/three-seed/long-timing campaigns. GPU waiting is additional.

| Method | Small runnable demonstration | Useful comparison on our targets | Main dependency |
|---|---|---|---|
|EDA|About4–8h **if** a compatible pretrained stage1 drafter is supplied|Budget **1–3+days** from current state; no firm upper bound until stage1 availability/runtime is resolved|Shared/private architecture, base-drafter initialization, Qwen2.5-oriented training/eval code, feature data conversion and matched evaluator|
|CARD|About2–4h with two available A40s and an isolated environment|About6–12h for a bounded supplementary systems comparison; frozen-vLLM integration would be additional|Custom parallel cache/verification runtime; comparable GPU allocation and its own autoregressive control|
|S2D/SoFT|Not a ready short demo on our targets|Roughly2–4+days if implemented/trained locally|Nested-depth6/9/12-layer drafter, SoFT training, confidence exits and decoder support; no matching released artifact verified|
|SPD|About4–8h on an already supported released checkpoint, conditional on dependencies|Roughly1–3+days for our target/repair comparison|Trained speculation head and multi-GPU pipeline; paper-v10 versus current-v11 distinction; actual timing needs distributed path|
|FastEagle|No verified runnable artifact located|Days or longer; no defensible precise ETA yet|Cascaded drafter plus constrained trees, compatible released weights/runtime or a new implementation/training run|

These estimates distinguish a successful toy invocation from evidence suitable for the paper. They are not claims that the listed methods are intrinsically slow. In particular, EDA authors report2.0hours for adaptation on4H200 GPUs; that does not include our port, missing initialization, validation or A40 conversion. We have not benchmarked their training path here.

## EDA: concrete shortest route

The repository trains a base shared/private-expert drafter first, then freezes the shared portion and adapts the private portion to a new target. Current scripts target the Qwen2.5 family and require a local `--pretrained_eda` checkpoint. I found no linked pretrained stage1 weights compatible with our Llama3.1 or Qwen3 runs. Its custom nonlinear gated FFN is not a linearly mergeable LoRA update to the official EAGLE3 release.

A defensible comparison would pin the release, validate/obtain a compatible stage1 checkpoint, adapt it on the same target responses, and evaluate EDA/reuse/appropriate controls on identical held-out prompts. If using its own runtime, report that as a separate supplementary protocol; its wall-clock numbers cannot simply be inserted into our frozen-vLLM table. Full frozen-engine support would require new implementation and validation. Common parent-drafter preparation should be reported separately from per-target repair cost for **both** methods; charging EDA's entire base preparation against only ReFit's incremental repair would be unfair.

Budget roughly4–8engineering hours just to establish target compatibility, feature alignment and a verified tiny train/eval round; stage1 preparation, substantive adaptation and comparative evaluation follow. Availability of pretrained weights could shorten this materially. Without those prerequisites, promising a final result in3hours is not credible. Our completed whole-drafter LoRA and matched-capacity decoder/interface controls remain useful comparisons, but must not be called EDA.

Sources: [EDA paper](https://arxiv.org/html/2603.09527v1), [official repository](https://github.com/Lyn-Lucy/Efficient-Draft-Adaptation), pinned commit `a29f0381479a92d0f3114fd264cd790bab3a208b`; existing local audit `artifacts/REV1_EDA_audit_20261010`. Paper §5.3–5.4 explicitly gives4H200 and2.0hours. Stage1/2 launch scripts reference local checkpoints rather than downloadable compatible releases. GitHub license metadata is currently null; no third-party code executed in this audit.

## Other methods: what changes

**CARD** is the fastest plausible new systems baseline because we already have the Llama1B and target weights. Its documented path uses transformers4.45.2 and two torchrun workers to overlap drafting and verification. It changes execution, not target-specific repair. A two-GPU speedup must be accompanied by hardware allocation/GPU-seconds and appropriate controls, rather than implicitly treated as a one-A40 result. Source: [official CARD repository](https://github.com/hunzhizi/CARD), commit `9014f05478e42d50714272d0a593fdf55b2196f0`.

**S2D uses SoFT-trained nested drafters.** The paper trains the first12layers of Vicuna with exits at6/9/12layers for3epochs. This is a different drafter and adaptive draft-generation mechanism; selecting a shallower existing EAGLE3 layer does not reproduce it. Source: [S2D §3.3–4.1](https://arxiv.org/html/2407.01955v1).

**SPD** offers code and checkpoint links. Its README explicitly distinguishes single-process algorithmic/theoretical-speedup evaluation from distributed actual wall-clock evaluation. Current releasev11 also differs from the paper implementationv10. We must select a version, compatible head and GPU topology before estimating actual R1/Nemotron performance. Source: [official SPD repository](https://github.com/yuyijiong/speculative_pipeline_decoding), commit `186f366764b213f5157fa0d15bce9fb59c0182db`.

**FastEagle** changes the drafter into a layer cascade and uses constrained draft trees. The paper includes R1-Distill, making it relevant as an acceleration reference. The checked paper and GitHub name search did not expose a verified official runnable release/checkpoint, so an evaluation-only ETA would be premature. This is a search finding, not proof no release exists. Source: [FastEagle paper](https://arxiv.org/html/2509.20416v1).

## Recommendation for this submission window

Prioritize EDA artifact/initialization feasibility over collecting many unrelated decoder baselines. A faithful EDA experiment would answer the adaptation-novelty concern most directly. CARD is the quickest plausible new system to smoke-test, but it would establish a different comparison and cannot substitute for EDA. None of the five has a verified drop-in path that produces a faithful new result under our current frozen harness within3hours.

The already authorized long128 study finished at15:53ET: all seven cells, paired raw reduction and report committed (`93c913e`). It provides immediate evidence for the draft: R1 full Δτ+.755[+.683,+.825],47.5%[44.3,50.6]oracle-gap recovery; Nemotron full Δτ+.960[+.890,+1.029],n128 each,cap8192. These are acceptance results, not new timing. [Long-panel report](REV5-long128-results-20261012.md).
