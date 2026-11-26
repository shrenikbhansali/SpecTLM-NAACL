# Owner-approved planner update — November 26, 2026

Deadline: final numbers in RESULTS.md by Nov28 EOD ET. Four A40s assumed. This supersedes the earlier optional scope.

- P0 E4c, budget15GPUh: six new R1 runs, exact E4 native recipe/steps/subsets. Interface on selected8k and random8k, seeds0/1; EDA50M on random8k,seeds0/1. Reuse existing selectedEDA50M seeds0/1. Frozen SPEED128/MATH128. Report full2x2 and paired interface-minus-EDA CIs on each subset regardless of sign.
- P0 timing divergence dueNov27noon: all timing arms/process pairs, identical fractions and first-divergence quartiles; no-spec/no-spec,spec/no-spec,spec/spec; eight full/student ratios restricted to outputs identical across all compared processes; first-divergence-truncated timing only if measurable. One b1 no-spec same-prompt same-process three-repeat check; no harness changes. Conclusion must answer whether divergence affects all arms alike.
- P0 E3: cumulative measured scratch checkpoint trainingGPUh and actual64k generationGPUh (missing is missing); epoch5 evaluation as exported; stopNov28noon. Finish E3a audits,200step measuredthroughput and labeledoneepochlowerbound byNov28EOD.
- CPU report additions: E1 derivative text a/b/c/d,d-a,(d-b)/(d-a) with pairedCIs forfourtargets; E4selectedEDA50M andvsfullCIs; E2checkpointrestoration table.
- P1 E8-lite only after aboveP0running andGPUidle; R1only,budget12GPUh.4kAyainstructions replace randomseed0 4kAlpaca,keep12kresponses; defaultgreedy512. LanguagesSPEEDmultilingual or8listedhighresource fallback; fullrepairseed0; disjointAya128 plusSPEED128/domain withreuse/Englishfullreferences. If notfinalNov28EOD reportnotrun.
- Dropped: E6,E7,E9,EDAnative20epochschedule,EDAseed2. NoSGLangintegration.
- No paper edits orOpenReviewposts. Ambiguities inSTATUS.md. Owner direct authorization received in conversation; recordD61.
