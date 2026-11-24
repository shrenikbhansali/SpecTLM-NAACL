# E1 — independent raw-cell reduction

All 12 target/source groups have 64 distinct sequences. Every saved feature, policy and interaction mean and CI reproduces the original Table-5 analysis to 1e-14.

The source code `atlas/crossover.py:factorial_effects` and saved independent reducer use:
```text
a = parent taps / parent verifier; b = parent taps / child verifier
c = child taps / parent verifier; d = child taps / child verifier
feature = ((c-a)+(d-b))/2
policy = ((b-a)+(d-c))/2
interaction = d-b-c+a
feature + policy = d-a
```

The interaction is a difference of simple effects, not an extra term to add to the averaged feature and policy effects. Additivity was checked in every resample.

Each sequence contributes its mean agreement over recorded completion positions. All four cells share the sequence bootstrap indices. CIs for every contrast and feature-share ratio come directly from its own bootstrap distribution. Ratios with near-zero denominators are unstable; zero denominators are reported as undefined, never as zero.

These are HF teacher-forced agreements, not online vLLM acceptance. Parent/child generations use the first 64 SPEED queries; public-reference uses MATH64 reference solutions and therefore changes queries as well as text source. Source-to-source differences are not controlled domain effects.

Child-source deployment contrasts (percentage points; 95% paired CIs):

| Target | Parent→child taps, parent verifier (c−a) | Parent→child taps, child verifier (d−b) | Joint change (d−a) |
|---|---:|---:|---:|
| deepseek-ai/DeepSeek-R1-Distill-Llama-8B | -5.08 [-5.72, -4.45] | +1.17 [+0.57, +1.77] | -4.98 [-5.76, -4.22] |
| nvidia/Llama-3.1-Nemotron-Nano-8B-v1 | -10.75 [-11.69, -9.78] | -3.10 [-3.92, -2.28] | -10.62 [-11.73, -9.48] |
| deepseek-ai/DeepSeek-R1-0528-Qwen3-8B | -5.25 [-5.84, -4.65] | +1.06 [+0.57, +1.55] | -5.70 [-6.45, -4.95] |
| shufanshen/Qwen3-8B-GRPO-DeepMath-50-steps | -0.05 [-0.22, +0.09] | +0.00 [-0.17, +0.15] | -0.04 [-0.24, +0.16] |

Exact source paths and SHA-256 hashes are recorded in results.json. No cached metrics library or old reducer was imported; the original outputs were read only for the equality check.

GPU-hours: 0.0 (CPU reanalysis of existing 12 × 64 fixed-context records).
