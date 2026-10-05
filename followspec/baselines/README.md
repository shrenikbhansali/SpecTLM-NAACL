# B11: EAGLE 3.1 baseline (incomplete; not approved for jobs)

`eagle31_llama.json` starts from the released SpecBundle Llama configuration
at `lmsys/SGLang-EAGLE3-Llama-3.1-8B-Instruct-SpecForge`, revision
`4a8e38f7dbee5d6dc82369f59a58540855fe09af` (MIT). The only changes are
`fc_norm: true` and `norm_output: true`, as required by MASTER §7 B11.
SpecForge commit `53398a8f01ae47175bee8459c5b5cca3848c8a7e` implements both,
as does the pinned evaluation engine vLLM 0.31.0. Source inspection is not
proof of a loadable trained checkpoint.

The model card states 1.4M target-regenerated Open-PerfectBlend examples and
two epochs. It does not specify the remaining training or regeneration
hyperparameters. The upstream Llama example uses ShareGPT, 10 epochs and a
10,000-step cap; it is **not** the SpecBundle recipe and is not copied here.
Do not silently substitute those settings. A complete recipe must be located
or the owner must choose the missing settings before implementing the launch.

Source data: `mlabonne/open-perfectblend` at
`af60f3c18201652a83a93f46fcfee1b646ba3df7`, Apache-2.0. The released
`frankleeeee/PerfectBlend-Regenerated-Llama-3.1-8B-Instruct` at
`c8cf5337f3a4bed5ba9da7362446cc5111fd24f1` has 1,418,731 rows but no license
in its card; skip it under AGENTS rule 9 until verified. Neither dataset's
training records have been downloaded or used by this task. Dataset approval,
training/evaluation disjointness, and five decoded assistant-mask inspections
remain required before training. Actual regeneration/training belongs to the
operator and cannot run while the pause marker exists.

SpecForge's `specforge export --to sglang` exports EAGLE3 serving keys,
including FC norms from the state dict. There is no `--to vllm` target in
this pinned source. Compatibility must be demonstrated by a real B2 cell;
do not count successful export alone as acceptance.

## Acceptance after training and B2 verification

Run two B2 cells using the same validated B4 SPEED128 file, unchanged Llama
base revision, K=4, seed, decoding and engine settings. One uses the local
trained checkpoint (so B2 records all file hashes); the other uses
`RedHatAI/Llama-3.1-8B-Instruct-speculator.eagle3` pinned to a Hub commit.
Then, from this branch:

```sh
python -m followspec.baselines.eagle31 \
  --candidate /path/to/trained-drafter-cell \
  --reference /path/to/redhat-cell \
  --speed-prompts /path/to/validated/speed128.jsonl \
  --engine-lock /path/to/atlas/env/engine.json \
  --report /path/to/new/b11_acceptance.json
```

The checker verifies matched settings, normalization flags, 128 unique prompt
IDs, real execution metadata and aggregates. It reports the paired gain and
prompt-bootstrap interval; a negative gain is explicitly reported as a
shortfall, as the task permits. The checker cannot establish training recipe
provenance or dataset licensing: include the training manifest and license
evidence in the journal. Its eight synthetic unit tests are not the real
acceptance test. No trained checkpoint or real acceptance result exists yet.
