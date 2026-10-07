# FIX-13 — Single-seed feasibility handoff

## 2026-10-07T01:02:29.808985-04:00 — codex-1 — Claim

D-37 makes seed0 the exploratory priority. Existing evaluation_jobs insists all12runs complete and would reject intentionallyinterrupted seeds1/2, making accepted single-seed evaluation unavailable. Add explicit training_seeds selection, defaultall3 unchanged. Validate selectedtraining as before; reportexcludedruns, keep12jobplanidentityvalidation; reuse Frozen seed0 frompreviousfullstage without relaunching replicas. Tests first: single-seed fourarm coverage, unselectedinterruption tolerated, selectedfailures rejected, priorFrozenreuse, invalidseedselection rejected, defaults unchanged.

## 2026-10-07T01:04:42.356288-04:00 — codex-1 — Acceptance PASS

Tests-first red:8 expected unexpected-keyword failures,13 existingpass (artifacts/M3_feasibility_20261007/FIX13_red.log). Explicit training_seeds scope implemented; selectedfailures stillrefused, default12runchecksunchanged, priorFrozenseed0paths retained and otherseedjobs excluded. Targeted37PASS, full followspec+ops243PASS (FIX13_tests.log/FIX13_full_tests.log). No evaluationmetric, decoding, trainingbudget or Gate3threshold changed. Single-seed mode explicitlyexploratory. Eight intentionallystopped trainingruns savedcheckpoints/interrupted and exited0 at149–236steps; existingresults.json status string is generic, but completedbudgetguards refuse treating them as finishedproductionmodels. Fourseed0runscontinue.

## 2026-10-07T01:08:01.839478-04:00 — codex-1 — Review / Handoff

Merged301a6a6/pushed run-FIX13-single-seed-20261007; actual native planner PASS into artifacts/M4_single_seed_20261007/frozen using --training-seeds0 --completed-only --previous oldFrozenstage. Zero newjobs,202primary+404secondary references reused,4selectedpending,8excluded, exploratory_single_seed=true. Mainc7c69cc also adds explicit incomplete/overshootbudget regressions (23targetedPASS) responding to operatorprovenanceflag. Runtimeguardalreadyrequires exactplanned1294steps and tokenbudget, regardlessgeneric trainedstatus. Earlier full243PASS; noimplementationchange sincefullsuite. Allinterruptedcheckpoints excluded. Operator mayrerun tests andmarkdone. Next use thisclean tag/selectedstage for incrementalhandoff when fullseed0exports finish; originaldefaultthree-seed protocol remainsunchanged.
