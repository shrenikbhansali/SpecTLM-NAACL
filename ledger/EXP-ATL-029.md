### EXP-ATL-029 — REV4 D56 follow-ups

**Landed:** 2026-10-11, codex-1.

**Status:** pilot; in progress.

**What/why:** owner-approved Y1–Y10 precision timing, reasoning-mode repair, second-family DFlash, scaling, matched supervision, training-free alignment, census, math-domain long data.

**New:** P0 141 jobs; P1/P2 planned in REV4-plan, unchanged thresholds and framing.

**Artifacts:** artifacts/REV4_P0_20261011_0240; reports/REV4-results-20261011.md; notes/REV4.md. P0 tag run-REV4-P0-20261011-0240; tests10pass. P1 tag run-REV4-P1-20261011-0250; tests11pass.

**Config/results:** frozen6da2e42/vLLM0.31/A40; exact matched target renders; seeded native repair; independent raw counter and paired query/seed/process bootstrap95%CIs. No new result claimed before successful runs and reduction.

**Caveats:** pilots; mode and cap extensions labelled; shared A40 placement; all nulls and failures retained. No paper edit or release package.

**Next:** P0 immediate summary on completion, then P1/P2 reduction and board review under D56 deadlines.

### 2026-10-11T02:56:45.902359-04:00 — codex-1 — Y9 complete; dependent stages
Y9 independently recomputed own-domain groups for163models/326rows; focused21 table42rows complete. Distillation pooled retention1.071 DFlash [0.907,1.262],1.141 EAGLE [0.924,1.449]; no reliable loss on this population/workload, reported plainly. Evidence artifacts/REV4_Y9_20261011_0300. Y3b8data shards andY8two fits queued; first ofeach running. New tests for audit gate/stable pending order failed before implementation then8pass. Followup code1ab0049 tagged/pushed run-REV4-followups-20261011-0310. One canonical queue; stable pending order P0, Y4/Y6/Y7/Y5/Y3b/Y8, Y10 last. No running jobs interrupted. Y8watch2336610.

### 2026-10-11T03:31:07.445685-04:00 — codex-1 — Y8 fit and provenance update
R1Y8fit4000responses/1875707positions complete,0.507A40GPU-h,31.14GiBpeak; four frozen acceptancecells queued. Outputs artifacts/REV4_Y8_20261011_0305/REV4-Y8-t0-linearfit; no acceptance gain claimed. ActualP1training runtime7faeef1/run-REV4-P1-native-20261011-0255; the0250tag above was CPUcollector preparation. HistoricalY9 sourcecommits423d3b6/f00992f retained; raw frozen-metric audit at artifacts/REV4_Y9_harness_audit_20261011_0340. AllnewREV4acceptance/timing uses6da2e42.

## 2026-10-11T09:16:59.004195-04:00 — codex-1 — P0 completion ping

All141P0 jobs successful, six acceptance and56timing contrasts independently reduced. P0 moved to review; P1/P2 remain separate. Evidence /home/heck2/sbhansali8/SpecTLM/artifacts/REV4_P0_live_20261011_0322/20261011_091644_963445. No scientific promotion.
