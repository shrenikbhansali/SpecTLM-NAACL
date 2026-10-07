# FIX-21: complete matched D-39 K8 stress follow-up

## 2026-10-07T19:32:47.085974-04:00 — codex-1 — Claim / acceptance first

D-39 already authorizes K4/K8 comparisons consistently across arms. Existing secondary planner covers only FS/Frozen, so build a separate operational K8 plan for the full fixed six-condition code/math panel: 0.1 plus lambda0/.03/.3; reuse only identical K8 controls across variants. No target selection, training, seed repeats or evaluation implementation changes.

Acceptance: derive jobs from sealed K4 sources with only K, output identity and compile-cache path changed; prove reverse restoration of every other argument/record field. All four arms and Frozen present in each of four 70-cell indexes; exactly112unique K8jobs, no K4controls reused in K8pairing. Existingfrozen metrics validate per-prompt records and paired uncertainty, preserving all six correlated conditions. All cell/launcher dryruns pass; append to sole dispatcher after K4feasibility work. Each variant reports automatically when complete.

## 2026-10-07T19:36:45.105980-04:00 — codex-1 — CPU acceptance

Tests first (missingmodulefailure `/tmp/FIX21-first.log`). Operational derivation changes only K4→K8, run/output/cache identity, preserving complete original commands and source records. All four arms/Frozen and all4lambda indexes enforced; only identicalK8controljobs shared. Automaticreports call original frozen B7load_measurements/paired_values plus existingD39pairedprompt uncertainty; regressions retained. Added explicit comparison-target mismatch guard. `python -m pytest ops/tests followspec/tests -q`:328passed26.95s; additional diagnostic pairing/regression test:4targetedpass. Frozen metric/decoding files unchanged. Actual112-job preparation/preflight next; noGPUsubmittedyet.

## 2026-10-07T19:41:00.597352-04:00 — codex-1 — Actual acceptance PASS

`python -m ops.k8_stress ... --prepare-only` createdartifacts/D39_K8_20261007 fromsealedoriginalstress andlambdaevaluationplans:4indexes×70cells,112uniquejobs, noK4referencecellsinsideK8indexes. All224actualcell/launcher dryrunsPASS (`preflight/results.json`); preservedsourceproofs andpreparedSHAenvelope. FullCPU suite330passed27.04s. Addedtests-firstsmallFIX19integrationfollow-up: operationalappendmustretainSlurmplacement; defaultheck unchanged (oldcodeoverwroteallowed_nodes evenwithSlurmargs). No metric/decodingchanges. Merge/tagthenresumeoperationalwatcherandappendtosamequeue; prioritizeafterfixedfullpanel andK4stresslambda.

## 2026-10-07T19:43:05.071350-04:00 — codex-1 — Handoff / review

Merged/pushede39c8cb, taggedrun-FIX21-k8-20261007; allacceptancepassed. `python -m ops.k8_stress --resume /home/heck2/sbhansali8/SpecTLM/artifacts/D39_K8_20261007` fromcleanruntag startedPID3298174/session40284; event19:41:05112jobs appended. Outputsconfig/indexes/jobs/preflight/watchlog sealed; reports report_{000,003,010,030} will appearautomatically, withledgerdrafts andrawhashes. K8allcontrolsnew; noK4referencesreused acrossK. One unchangedfrozen6da2e42harness forhecknumbers. Queue3264226 excludesheck5 andprioritizesfixedfullpanel,42K4stresslambda,112K8,114publiclambda, thenremainingmatrix. Allpublicλhandoffs nowcomplete (last.3 at19:41:50). Dispatchorderproof `artifacts/FIX20_recovery_20261007/priority_final.json`.

Next: inspect full-budgetfixedpanel automaticreport (184/190complete at19:42,6controls alreadyrunning), thenλ/K8stress reports; verifyresults andassignledgerIDs. Do not inferGate3PASSfromsingleseed. Existingfullmatrixcontroller2981571,stressλ3067243,publicλ3269112, fixedpanel3283708 remainactive. OnlyidentifiedGPUcollisionfailuresauto-retryonce; inspectanyfurtherblockederror. ICEintegrationreviewready; actualICEconfig/enginevalidationpending, noICEjobs. No pausemarkersfound; source101worktreesauditclean beforeaddingFIX21runtag; mainandthreenewtags pushed.
