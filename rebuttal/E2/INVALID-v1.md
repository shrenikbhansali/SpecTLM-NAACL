# Initial ablation exports are invalid

All eight exports under rebuttal/E2/exports and their evaluations are INVALID because index-only redirection left duplicate parameter keys in physical safetensor shards. vLLM streams those files and can overwrite the intended restored tensor. Preserve all files; do not use any acceptance number from these ablation runs.

Affected completed cells: E2_t1_lora-no_fc_speed128_s0, E2_t1_lora-no_fc_math128_s0, E2_t1_lora-fc_only_speed128_s0, E2_t1_lora-fc_only_math128_s0. R1 ablation evaluations were not launched. Whole-drafter LoRA and dense-interface reference exports/cells are unaffected.

Correction: remove restored keys physically from retained source shards, keep immutable unaffected shards hardlinked, and assert every tensor key exists in exactly one included shard. New exports_v2 and new eval names will be used. No engine or scientific setting changed.
