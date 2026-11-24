# E2 — provenance and interpretation

Native TTT3, audited existing16k responses, official family initialization with FIX24 target embedding, lr2e-5, one epoch, seed0–2; unchanged recipe. Whole LoRA r343/alpha686 has50,313,984trainable parameters. Decoder+head-only LoRA r386/alpha772 has50,297,344; dense interface50,331,648. The latter is the separately trained capacity-matched control; the two export ablations are different interventions on jointly trained whole-LoRA checkpoints.

LoRA-no-fc restores the initial dense fc values (cast exactly to export dtype). LoRA-fc-only restores every other LoRA-adapted dense tensor, including the head; embeddings and other frozen tensors remain unchanged. No subtraction of rounded LoRA deltas. Every tensor occurs in one physical safetensor shard; otherwise vLLM could read stale duplicate values despite the index. All8corrected exports pass this check and bit-exact restoration. Initial exports and4completed ablation cells are retained and INVALID as documented in INVALID-v1.md.

New training initially failed in compiled backward because stock pinned CPU activation offload discarded padded/transposed strides. New opt-in --preserve-offload-strides retains shape,stride,offset; multistep loss/gradient/Adam-state equality tests pass. No engine/environment/objective edits. Five failed attempts remain cost-counted; each ended before its first optimizer update. New _strides1 Nemotron attempts and R1 runs use tagged3ceff33.

Independent reducer: python -m rebuttal.reduce_e2 --workspace /home/heck2/sbhansali8/ReFit --output <new-directory>. Raw per-step counters only,10k paired seed/query resamples, explicit invalid exclusions, exact128prompt panels and prompt-hash checks. Current results are partial; do not treat seed0 comparisons as3seed evidence. First128MATH differs from the500prompt paper-anchor reproduction.

Owner approved40A40GPUh for E2 on Nov24 at15:36ET. Guard includes failed/invalid attempts and active time and stops before40GPUh unless explicitly changed; all outcomes retained.
