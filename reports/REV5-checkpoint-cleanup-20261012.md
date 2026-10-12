# Documented deletion of obsolete FIX-24 checkpoint weights

Owner authorized deletion of recorded old results/checkpoints on2026-10-12 to free space for the128-query followup. Deleted32 unique trainable-weight files,30.401GB logical size, from the four official4k runs previously marked INVALID(FIX-24). Corrected FIX24 reruns and all raw evaluation results, training metrics, configs and shared shards are retained.

These deleted checkpoint files can no longer be loaded. Tensor shape/dtype headers, header hashes, sizes, inode/mtime and per-file deletion timestamps are preserved in artifacts/REV5_cleanup_20261012_1435/{manifest.json,actions.jsonl,dependency-audit.json,results.json}. There were no active jobs depending on these weights. This is an owner-authorized deletion, not a claim that the weight bytes are backed up.

| Deleted path (relative to artifacts/P3_D50_20261009_0200) | Bytes | Tensor-header SHA256 |
|---|---:|---|
| E1-official-t0-4k-fc/checkpoints/epoch-0-step-1115/trainable.safetensors | 201326712 | 48fc53b618a1b97c3f1cd0293f49a435c96fb70d2d35b8ca6f9922a89486c21a |
| E1-official-t0-4k-fc/checkpoints/step-279/trainable.safetensors | 201326712 | 48fc53b618a1b97c3f1cd0293f49a435c96fb70d2d35b8ca6f9922a89486c21a |
| E1-official-t0-4k-fc/checkpoints/step-558/trainable.safetensors | 201326712 | 48fc53b618a1b97c3f1cd0293f49a435c96fb70d2d35b8ca6f9922a89486c21a |
| E1-official-t0-4k-fc/checkpoints/step-837/trainable.safetensors | 201326712 | 48fc53b618a1b97c3f1cd0293f49a435c96fb70d2d35b8ca6f9922a89486c21a |
| E1-official-t0-4k-fc/export-1115/trainable.safetensors | 201326712 | 48fc53b618a1b97c3f1cd0293f49a435c96fb70d2d35b8ca6f9922a89486c21a |
| E1-official-t0-4k-fc/export-279/trainable.safetensors | 201326712 | 48fc53b618a1b97c3f1cd0293f49a435c96fb70d2d35b8ca6f9922a89486c21a |
| E1-official-t0-4k-fc/export-558/trainable.safetensors | 201326712 | 48fc53b618a1b97c3f1cd0293f49a435c96fb70d2d35b8ca6f9922a89486c21a |
| E1-official-t0-4k-fc/export-837/trainable.safetensors | 201326712 | 48fc53b618a1b97c3f1cd0293f49a435c96fb70d2d35b8ca6f9922a89486c21a |
| E1-official-t0-4k-full/checkpoints/epoch-0-step-1115/trainable.safetensors | 1698760016 | 44eb7a686cba28e846cf069709869fbc26e4fece1cefaa7323b50b4999a93604 |
| E1-official-t0-4k-full/checkpoints/step-279/trainable.safetensors | 1698760016 | 44eb7a686cba28e846cf069709869fbc26e4fece1cefaa7323b50b4999a93604 |
| E1-official-t0-4k-full/checkpoints/step-558/trainable.safetensors | 1698760016 | 44eb7a686cba28e846cf069709869fbc26e4fece1cefaa7323b50b4999a93604 |
| E1-official-t0-4k-full/checkpoints/step-837/trainable.safetensors | 1698760016 | 44eb7a686cba28e846cf069709869fbc26e4fece1cefaa7323b50b4999a93604 |
| E1-official-t0-4k-full/export-1115/trainable.safetensors | 1698760016 | 44eb7a686cba28e846cf069709869fbc26e4fece1cefaa7323b50b4999a93604 |
| E1-official-t0-4k-full/export-279/trainable.safetensors | 1698760016 | 44eb7a686cba28e846cf069709869fbc26e4fece1cefaa7323b50b4999a93604 |
| E1-official-t0-4k-full/export-558/trainable.safetensors | 1698760016 | 44eb7a686cba28e846cf069709869fbc26e4fece1cefaa7323b50b4999a93604 |
| E1-official-t0-4k-full/export-837/trainable.safetensors | 1698760016 | 44eb7a686cba28e846cf069709869fbc26e4fece1cefaa7323b50b4999a93604 |
| E1-official-t1-4k-fc/checkpoints/epoch-0-step-652/trainable.safetensors | 201326712 | 48fc53b618a1b97c3f1cd0293f49a435c96fb70d2d35b8ca6f9922a89486c21a |
| E1-official-t1-4k-fc/checkpoints/step-163/trainable.safetensors | 201326712 | 48fc53b618a1b97c3f1cd0293f49a435c96fb70d2d35b8ca6f9922a89486c21a |
| E1-official-t1-4k-fc/checkpoints/step-326/trainable.safetensors | 201326712 | 48fc53b618a1b97c3f1cd0293f49a435c96fb70d2d35b8ca6f9922a89486c21a |
| E1-official-t1-4k-fc/checkpoints/step-489/trainable.safetensors | 201326712 | 48fc53b618a1b97c3f1cd0293f49a435c96fb70d2d35b8ca6f9922a89486c21a |
| E1-official-t1-4k-fc/export-163/trainable.safetensors | 201326712 | 48fc53b618a1b97c3f1cd0293f49a435c96fb70d2d35b8ca6f9922a89486c21a |
| E1-official-t1-4k-fc/export-326/trainable.safetensors | 201326712 | 48fc53b618a1b97c3f1cd0293f49a435c96fb70d2d35b8ca6f9922a89486c21a |
| E1-official-t1-4k-fc/export-489/trainable.safetensors | 201326712 | 48fc53b618a1b97c3f1cd0293f49a435c96fb70d2d35b8ca6f9922a89486c21a |
| E1-official-t1-4k-fc/export-652/trainable.safetensors | 201326712 | 48fc53b618a1b97c3f1cd0293f49a435c96fb70d2d35b8ca6f9922a89486c21a |
| E1-official-t1-4k-full/checkpoints/epoch-0-step-652/trainable.safetensors | 1698760016 | 44eb7a686cba28e846cf069709869fbc26e4fece1cefaa7323b50b4999a93604 |
| E1-official-t1-4k-full/checkpoints/step-163/trainable.safetensors | 1698760016 | 44eb7a686cba28e846cf069709869fbc26e4fece1cefaa7323b50b4999a93604 |
| E1-official-t1-4k-full/checkpoints/step-326/trainable.safetensors | 1698760016 | 44eb7a686cba28e846cf069709869fbc26e4fece1cefaa7323b50b4999a93604 |
| E1-official-t1-4k-full/checkpoints/step-489/trainable.safetensors | 1698760016 | 44eb7a686cba28e846cf069709869fbc26e4fece1cefaa7323b50b4999a93604 |
| E1-official-t1-4k-full/export-163/trainable.safetensors | 1698760016 | 44eb7a686cba28e846cf069709869fbc26e4fece1cefaa7323b50b4999a93604 |
| E1-official-t1-4k-full/export-326/trainable.safetensors | 1698760016 | 44eb7a686cba28e846cf069709869fbc26e4fece1cefaa7323b50b4999a93604 |
| E1-official-t1-4k-full/export-489/trainable.safetensors | 1698760016 | 44eb7a686cba28e846cf069709869fbc26e4fece1cefaa7323b50b4999a93604 |
| E1-official-t1-4k-full/export-652/trainable.safetensors | 1698760016 | 44eb7a686cba28e846cf069709869fbc26e4fece1cefaa7323b50b4999a93604 |
