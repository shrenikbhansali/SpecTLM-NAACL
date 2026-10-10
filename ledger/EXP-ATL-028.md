### EXP-ATL-028 — REV3 X5 native DFlash repair at16k

**Landed:**2026-10-10, codex-1, owner D55/X5 promoted P0, dueSun08ET.

**Status:**pilot, in progress; no new16k acceptance claim yet.

**What / why.** Test whether interface/full repair transfers to the DFlash architecture at the main16k budget, on R1-Distill and Nemotron, with held-out long reasoning and repeated measured timing.

**New.** Eight native DFlash trainings: R1fc/fullseeds0–2,Nemofc/fullseed0. Thirty frozen acceptance cells including fresh reuse controls;48timing processes onSPEED128 atb1/b8,three processes×three warm passes. Dedicated-reference catalog search found no compatible public R1DFlash; PAROis a quantized target,notDFlash. Existingcensus EAGLE/DFlash retention reproduced/linked in report.

**Artifacts.** `artifacts/REV3_X5_20261010_1410`, `artifacts/REV3_X5_hub_audit_20261010_1405`; [report](../reports/REV3-results-20261010.md), [journal](../notes/REV3.md). Code followspec/rev3_x5.py, optionalDFlash timing and final-export-only persistence,46testsPASS; tagrun-REV3-X5-20261010-1410/b65eeed pushed beforelaunch. One canonicalqueue4129996, no duplicated runs.

**Config + results.** Pinned z-labDFlash revisiond3af30def9601abdd10810aba220d692f0e803f0/MIT; exactexisting16kAlpaca512responses andfive-sampleaudits; oneepoch2048tokenpacking,64anchors,nativeDFlashγ4fixedexpKL. Native checkpointedlayers/offload; frozen teacher/embeddings/output head. All8trainings pastmultiplebackwards at14:08. Acceptance6da2e42/vLLM0.31/A40,greedyK10, identicalrenderedSPEED128/MATH500/MATH32cap8192. Raw pairedseed/queryCIs; timedseed0exports,b1/b8eachn128,3processes×3warm,pairedprocess/querybatchCIs. Numbers will be appended only oncompletegroups.

**Caveats.** Three-seed R1,one-seedNemotron. DFlashK10 differs fromEAGLEK4, so no direct cross-architectureτequivalence claim. Longcap supplementary. No dedicatedoracleavailablefromsearch; no inventedgaprecovery. Everyoutcome retained; no paper edit. Disk350GBfloor enforced with final-onlysharedexports andno redundantnativecheckpoint.

**Next.** Finish8trainings; autolaunch24repairedacceptance cells/24repairedtimingprocesses; independently reduce and markX5review whenall86jobs complete.
