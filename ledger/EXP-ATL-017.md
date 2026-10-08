### EXP-ATL-017 — P2 fixed-prefix feature/verifier crossover

**Landed:** 2026-10-08.

**Status:** pilot HF diagnostic; no certification or online acceptance claim.

**What / why.** Separate effects of feature source and verifier policy on fixed token contexts, with layer swaps and draft-vocabulary ceiling diagnostics.

**New.** Five targets ×three context origins ×64sequences; each sequence allfour factorial conditions and six tap swaps. Exact saved parent/child SPEED traces plus explicitly labeled public MATH64 reference solutions. No training or new data generation for this diagnostic.

**Artifacts.** [Report](../reports/P2-crossover-20261008.md); `artifacts/P2_crossover_20261008_0348/full64/`, pinned configs, source hashes, full per-token diagnostics; independent `analyze_full.py` and `full64/report/results.json`.

**Config + results.** Native261a82d,code0e8f033,HFbf16/eager,A40,64contexts/cell;10,000 paired sequence bootstrap. On child text, feature effects R1Llama−.0196[−.0250,−.0142],Nemotron−.0693[−.0767,−.0617],R1Qwen−.0209[−.0255,−.0163],TuluDPO+.0002[−.0047,+.0053],GRPO50−.0003[−.0019,+.0012]. Policy effects respectively−.0303,−.0369,−.0361,−.0193,−.0002, with intervals and positive interactions in report. Margins,OOV,disagreement and layer swaps retained with uncertainty.

**Caveats.** HF all-completion-position greedy agreement is not vLLM acceptance. Main effects average over the other factor; interactions substantial and retained. Public-reference origin changes query distribution and length; origin contrasts not causal. First64 frozen-order prompts, no population sampling claim. Tulu parent traces show repetition/role continuations; retained. Unequal output vocabularies handled without renormalization; contexts restricted to IDs valid for both models. Greedy ceiling applies only to diagnostic prefixes. Native n8 integration/affine smokes are engineering checks; full256-fit calibrated diagnostic and Nemotron frozen online toggles dispatched separately, pending. No winner or mechanism conclusion promoted.

### 2026-10-08T15:30:07.989954-04:00 — Nemotron frozen toggle completion
Fourcells,n128pairedqueries; EAGLEΔp1−.0296[−.0437,−.0157],DFlash−.0278[−.0448,−.0113];τ/lengths andlimitations in [report](../reports/P2-nemotron-toggle-20261008.md). Raw independent10kpairedbootstrap; frozen6da2e42/vLLM0.31/A40. Promptinterventionchangeslength/content; notreasoningtextcausalproof.
