# A2 census composition — independent raw recomputation

10,000 hierarchical checkpoint/paired-query bootstrap draws; equal checkpoint weights. Compound histories retained as combinations. Historical and focused populations and workloads remain separate. Paired zero-step exclusions listed in audit.json.

| Population | Family | Panel | Lineage | History | Drafter | Models | Prompt pairs | p1 retention [95% CI] |
|---|---|---|---|---|---|---:|---:|---|
| focused21_prespecified_eligible | llama | math64 | direct_child | CPT+SFT+on_policy_RL_claim | dflash | 1 | 64 | 0.751 [0.734, 0.770] |
| focused21_prespecified_eligible | llama | math64 | direct_child | CPT+SFT+on_policy_RL_claim | eagle3 | 1 | 64 | 0.775 [0.752, 0.799] |
| focused21_prespecified_eligible | llama | math64 | direct_child | on_policy_RL | dflash | 1 | 64 | 0.996 [0.975, 1.019] |
| focused21_prespecified_eligible | llama | math64 | direct_child | on_policy_RL | eagle3 | 1 | 64 | 0.966 [0.942, 0.992] |
| focused21_prespecified_eligible | llama | math64 | sibling_from_base | SFT+synthetic_data | dflash | 1 | 64 | 0.976 [0.939, 1.011] |
| focused21_prespecified_eligible | llama | math64 | sibling_from_base | SFT+synthetic_data | eagle3 | 1 | 64 | 0.947 [0.909, 0.984] |
| focused21_prespecified_eligible | llama | math64 | sibling_from_base | SFT+teacher_distillation | dflash | 2 | 128 | 0.872 [0.809, 0.939] |
| focused21_prespecified_eligible | llama | math64 | sibling_from_base | SFT+teacher_distillation | eagle3 | 2 | 128 | 0.904 [0.868, 0.939] |
| focused21_prespecified_eligible | llama | math64 | sibling_from_base | SFT+teacher_distillation+on_policy_RL | dflash | 1 | 64 | 0.840 [0.816, 0.865] |
| focused21_prespecified_eligible | llama | math64 | sibling_from_base | SFT+teacher_distillation+on_policy_RL | eagle3 | 1 | 64 | 0.928 [0.886, 0.967] |
| focused21_prespecified_eligible | llama | speed128 | composite | SFT+on_policy_RL+merge | dflash | 1 | 128 | 0.708 [0.688, 0.729] |
| focused21_prespecified_eligible | llama | speed128 | composite | SFT+on_policy_RL+merge | eagle3 | 1 | 128 | 0.696 [0.672, 0.722] |
| focused21_prespecified_eligible | llama | speed128 | direct_child | CPT+SFT+on_policy_RL_claim | dflash | 1 | 128 | 0.801 [0.775, 0.828] |
| focused21_prespecified_eligible | llama | speed128 | direct_child | CPT+SFT+on_policy_RL_claim | eagle3 | 1 | 128 | 0.845 [0.810, 0.886] |
| focused21_prespecified_eligible | llama | speed128 | direct_child | on_policy_RL | dflash | 2 | 256 | 0.998 [0.978, 1.020] |
| focused21_prespecified_eligible | llama | speed128 | direct_child | on_policy_RL | eagle3 | 2 | 256 | 0.974 [0.955, 0.992] |
| focused21_prespecified_eligible | llama | speed128 | sibling_from_base | SFT | dflash | 1 | 128 | 0.937 [0.899, 0.976] |
| focused21_prespecified_eligible | llama | speed128 | sibling_from_base | SFT | eagle3 | 1 | 128 | 0.915 [0.863, 0.969] |
| focused21_prespecified_eligible | llama | speed128 | sibling_from_base | SFT+offline_preference | dflash | 1 | 128 | 0.832 [0.799, 0.865] |
| focused21_prespecified_eligible | llama | speed128 | sibling_from_base | SFT+offline_preference | eagle3 | 1 | 128 | 0.810 [0.770, 0.850] |
| focused21_prespecified_eligible | llama | speed128 | sibling_from_base | SFT+offline_preference+on_policy_RL | dflash | 1 | 128 | 0.837 [0.803, 0.872] |
| focused21_prespecified_eligible | llama | speed128 | sibling_from_base | SFT+offline_preference+on_policy_RL | eagle3 | 1 | 128 | 0.801 [0.763, 0.840] |
| focused21_prespecified_eligible | llama | speed128 | sibling_from_base | SFT+synthetic_data | dflash | 1 | 128 | 0.935 [0.904, 0.969] |
| focused21_prespecified_eligible | llama | speed128 | sibling_from_base | SFT+synthetic_data | eagle3 | 1 | 128 | 0.942 [0.904, 0.986] |
| focused21_prespecified_eligible | llama | speed128 | sibling_from_base | SFT+teacher_distillation | dflash | 4 | 512 | 0.875 [0.779, 0.947] |
| focused21_prespecified_eligible | llama | speed128 | sibling_from_base | SFT+teacher_distillation | eagle3 | 4 | 512 | 0.908 [0.785, 0.987] |
| focused21_prespecified_eligible | llama | speed128 | sibling_from_base | SFT+teacher_distillation+on_policy_RL | dflash | 1 | 128 | 0.858 [0.839, 0.877] |
| focused21_prespecified_eligible | llama | speed128 | sibling_from_base | SFT+teacher_distillation+on_policy_RL | eagle3 | 1 | 128 | 0.984 [0.954, 1.014] |
| focused21_prespecified_eligible | qwen3 | math64 | direct_child | SFT+teacher_distillation | dflash | 2 | 128 | 0.879 [0.851, 0.905] |
| focused21_prespecified_eligible | qwen3 | math64 | direct_child | SFT+teacher_distillation | eagle3 | 2 | 128 | 1.012 [0.993, 1.032] |
| focused21_prespecified_eligible | qwen3 | speed128 | direct_child | SFT+teacher_distillation | dflash | 2 | 256 | 0.882 [0.828, 0.936] |
| focused21_prespecified_eligible | qwen3 | speed128 | direct_child | SFT+teacher_distillation | eagle3 | 2 | 256 | 0.937 [0.888, 0.987] |
| focused21_prespecified_eligible | qwen3 | speed128 | direct_child | on_policy_RL | dflash | 2 | 256 | 0.982 [0.972, 0.993] |
| focused21_prespecified_eligible | qwen3 | speed128 | direct_child | on_policy_RL | eagle3 | 2 | 256 | 0.999 [0.988, 1.011] |
| focused21_prespecified_eligible | qwen3 | speed128 | sibling_from_base | SFT+teacher_distillation | dflash | 1 | 128 | 0.810 [0.788, 0.835] |
| focused21_prespecified_eligible | qwen3 | speed128 | sibling_from_base | SFT+teacher_distillation | eagle3 | 1 | 128 | 0.858 [0.828, 0.889] |
| focused21_prespecified_eligible | qwen3 | speed128 | sibling_from_base | on_policy_RL | dflash | 1 | 128 | 0.903 [0.869, 0.939] |
| focused21_prespecified_eligible | qwen3 | speed128 | sibling_from_base | on_policy_RL | eagle3 | 1 | 128 | 1.027 [0.997, 1.058] |
| focused21_prespecified_eligible | qwen3 | speed128 | unknown | CPT+SFT+on_policy_RL+teacher_distillation | dflash | 1 | 128 | 0.711 [0.688, 0.735] |
| focused21_prespecified_eligible | qwen3 | speed128 | unknown | CPT+SFT+on_policy_RL+teacher_distillation | eagle3 | 1 | 128 | 0.836 [0.801, 0.877] |
| focused21_prespecified_eligible | qwen3 | speed128 | unknown | unknown | dflash | 1 | 127 | 1.048 [1.004, 1.093] |
| focused21_prespecified_eligible | qwen3 | speed128 | unknown | unknown | eagle3 | 1 | 127 | 1.109 [1.051, 1.170] |
