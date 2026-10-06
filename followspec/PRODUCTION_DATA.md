# D-27 method data preparation

`python -m followspec.production` is a CPU orchestrator for M1/M2. It creates
immutable stage folders and `ops/queue.py` job files. It never submits GPU
work. The operator runs jobs from a clean, tagged main checkout, using A40s,
the pinned vLLM 0.31.0 environment, offline models, and a fresh compile per
cell. Every retry uses a new stage/output directory; source runs are retained.

The JSON specification supplies absolute paths: `code_repo`, `python` (the
vLLM environment), `base_id`, `base_revision`, `base_snapshot`,
`drafter_revision`, `drafter_snapshot`, `pool_manifest` (the frozen A2 CSV),
`staging_manifest` (B1 CSV with tokenizer/file provenance), `downloads` (B1
JSONL), `artifacts_root`, `general_prompts`, `forbidden_files` (JSONL paths),
`seed`, and `max_lora_rank`. Llama's frozen bank has 33 adapters. Use a rank
capacity supporting the candidate source sums and use that same capacity in
all scoring and response jobs. No default seed or validation fraction is
silently inferred.

1. `prepare --spec SPEC.json --output PLAN` checks the frozen bank, pinned
   weights, tokenizer templates, and A2 acceptance. It chooses 128 shared
   training-general PPL queries and fixes all 60 candidate definitions before
   any scores. Two rounds of 30, width uniformly 2 or 3, distinct bank sources,
   Dirichlet alpha 0.5, scale uniform [0,1.5]. Only rank-feasible source subsets
   are sampled; both widths must be feasible. This stage loads no models.
2. `materialize --plan PLAN --output ROUND1` constructs the first 30 B3
   adapters and tokenizes the reference on CPU. Run this longer CPU step in
   the background with a log. The operator launches `baseline_jobs.jsonl`,
   waits for its successful result, then launches `filter_jobs.jsonl` (33
   bank children plus 30 candidates). The PPL reference is training general,
   never the old A2 SPEED reference.
3. `admit --round-dir ROUND1 --output ADMISSION1` recomputes every PPL and
   compares each mixture with the worst bank child using B5 admission checks.
   Missing/crashed cells block admission; they are not counted as PPL rejects.
   If fewer than 30 pass, run `materialize --plan PLAN --previous ADMISSION1
   --output ROUND2`, then its filter jobs, then `admit --round-dir ROUND2
   --output ADMISSION2`. Round2 reuses the first reference and bank scores.
   The final registry keeps the first at most30 passing candidates in the
   preregistered order; at least20 are required. No third round.
4. `mixture-prompts --admission ADMISSION --forbidden-files EVAL_FILES...
   --output MIXTURE_PROMPTS` emits admitted-mixture Magpie training jobs.
   It also excludes all general20000 prompts, preventing parent/general
   collisions. Combine its `prompt_paths.json` with the operator's bank A3
   training paths into a JSON map `{target_id: absolute_prompts_jsonl}`.
5. `responses --admission ADMISSION --prompt-paths PATHS.json
   --validation-prompts VALIDATION.jsonl --forbidden-files EVAL_FILES...
   --output RESPONSES` verifies 500 real Magpie queries per target and emits
   CPU rendering commands plus child/base response jobs. `VALIDATION.jsonl`
   is an explicit operator-selected subset of general20000; its size is an
   input, not a new hidden validation-fraction default. It is excluded from
   every arm's training data and generated separately by each target.
   `render-local --plan RESPONSES` executes only these CPU rendering commands.
   Then the operator launches `jobs.jsonl`.
6. `assemble --plan RESPONSES --output ASSEMBLY` runs in the pinned native
   speculators environment (`.venv-transport` on heck). It checks completed
   responses against the plan, applies paired response trimming, and writes
   four arm manifests, every trim, suffix-drop logs, a native sampler audit
   across seeds0/1/2, and five decoded strings/masks per arm. No GPU is loaded.
7. Inspect each arm's `decoded_masks.jsonl` and put its SHA256 in an evidence
   JSON's `mask_review_sha256` map. Add `feature_acceptance` (passing B5 native
   acceptance/aggregate JSON) and `feature_acceptance_sha256`. Run
   `finalize --assembly ASSEMBLY --evidence EVIDENCE.json --output FINAL` in
   the native environment. It rechecks actual sources and native batches,
   records the reviewed mask evidence, and resolves all four training configs.
   It reports data readiness separately from full-response training capacity.
   If available, `capacity_acceptance` and its SHA256 point to an actual
   passing 8192-token, full-response, at-least-one-step capacity check, not
   the bounded64-token-response overfit. M3 launches remain operator-owned.

## Exact matching and integer counts

The planned MVD corpus uses 1000 queries/bank child. The FS per-target count
starts at `round(1000 * n_bank / n_targets)`; when odd, its last query is omitted so
both halves are equal (recorded). General queries are shared across targets,
as §5.4 specifies, with no repeated query within a target. A seeded partition
keeps parent general queries disjoint from every child general query; validation
is disjoint from both. FS bank responses reuse a subset of the very same MVD
generation job; no second stochastic copy of an identical sample is generated.

Before looking at token lengths, the assembler orders each child-kind stream
with a fixed seed into groups of three Magpie plus three general children and
two parents. Final incomplete groups are logged and dropped. It selects the
largest common prefix token budget at group boundaries for which every arm
and all three seeds have identical native optimizer steps and every requested
target remains represented. FS/PO-T share exact child views; PO-D uses the
reciprocal base views. Truncation removes complete records from the list tail;
it never cuts a prompt, repeats a sample, or invents response tokens. Every
retained prefix has 25% parent samples and 50:50 child composition. Final
per-target counts and retained totals are reported, since suffix truncation
can change the initially assigned quotas.

## D-28 bank workload eligibility

`bank-eligibility --plan ORIGINAL_PLAN --bank-runs RUNS.json --output NEW_AUDIT`
audits one final Magpie cell directory per original bank adapter. The mapping
must cover the complete original bank. Complete legacy workloads remain usable;
each must contain exactly 500 unique training queries with matching model pins
and adapter hashes. A dropped child needs a completed FIX-5 shortfall with all
6400 raw attempts, matching round/filter summaries and no failure marker.
Missing, still-running or crashed jobs do not justify exclusions. The stage
writes eligible prompt paths, drop counts/reasons and hashes of all evidence.
It changes no source artifact, pool, candidate plan or admission result.

The audit itself reports `mixture_policy_applied=false`. Apply the owner
fresh-plan decision with the stage below before planning production responses.

A shared prefix may not exist for real response lengths. The assembler then
preserves `failure.json` and the pretrim counts and refuses readiness. It does
not relax the recipe, choose a new ordering after seeing lengths, or call
unequal native step counts matched. The operator must resolve that data
blocker under the decision process in MASTER.

## Saved embedding copies in bank adapters

Two frozen bank adapters also save `lm_head.base_layer.weight`. The pinned
vLLM loader explicitly ignores saved input/output embedding base weights,
whereas PEFT would load them into the shared base. `materialize` therefore
creates new factor-only views for precisely the two suffixes ignored by vLLM
0.31.0. It preserves every LoRA tensor bit-for-bit and the entire adapter
configuration, records original hashes and skipped keys, and leaves the
original files untouched. The registry uses these views for mixtures and
online PEFT capture; vLLM response/filter jobs can still use the original
pinned Hub adapter. Unknown extra weights are refused. Ordinary adapters and
B3's default strict tensor handling are unchanged.

### Retrying failed filter cells without overwriting artifacts

`python -m followspec.production retry-filters --round-dir ROUND --targets ID1 ID2
--output NEW_ROUND` creates an immutable overlay and jobs for explicitly failed
cells only. Each target must have failure.json. Successful and active cells are
refused. The original registry, plan, reference, baseline, seeds and thresholds
stay fixed; untouched target paths are reused. Original failures remain intact.
Run NEW_ROUND/filter_jobs.jsonl, then `admit --round-dir NEW_ROUND --output NEW_ADMISSION`.
Every referenced cell must still complete successfully; this does not discard
candidates or grant admission. Later retries can use the preceding overlay.
A failed baseline needs separate recovery; this command retries target filters.


For new M2 jobs, `mixture-prompts` and `responses` accept `--code-repo` pointing
to a clean execution checkout. It must retain the original engine lock hash;
the new commit is recorded in the new stage. The operator should use a tagged
main checkout as required by the launcher. This changes future command paths
without editing the original M1 spec or existing jobs. Use
`mixture-prompts ... --code-repo NEW_CHECKOUT --d23-oversampling` to enable
FIX-5's complete candidate budget and clean shortfall handling. Without the
explicit options, old command behavior is preserved. Mixture shortfalls still
block full response planning; D-28 only specifies bank-child exclusions.


## Fresh plan after D-28 exclusions

The owner's direct instruction on October 6 supersedes D-29's retention policy:
exclude affected mixtures and create a fresh plan from the remaining bank.
Run `replan-d28 --plan ORIGINAL_PLAN --eligibility FINAL_BANK_AUDIT
--code-repo CLEAN_TAGGED_CHECKOUT --output FRESH_PLAN`. This rechecks every
workload proof, preserves the original pool and artifacts, and writes a separate
remaining-bank CSV, registry and tokenizer metadata. It records affected old
candidates and supersedes the old candidate plan without importing old admission
results. New IDs distinguish all 60 candidates; the seed, sampling recipe and
128 training-reference queries remain fixed.

Then use the existing `materialize`, `admit`, `mixture-prompts --d23-oversampling`,
`responses`, `assemble` and `finalize` stages on this new plan. Fresh admission
uses the worst PPL among the remaining bank, with the original D-27 maximum of
two rounds and minimum of 20 admitted mixtures. The old 29-mixture admission
cannot certify the fresh plan. GPU filter/generation/training jobs belong to
the operator. `bank_prompt_paths.json` supplies the 30 reusable completed bank
workloads in the current run; mixture prompts follow new admission. Quotas are
recomputed from the actual remaining-bank size throughout response planning.
