### EXP-ATL-000
**Preregistered predictions (§6.3), recorded before A4 and M3 launch**

**Landed:** 2026-10-06 01:31 ET · NAACL sprint, Day 2 · **Status:** preregistration (not a result)

**What / why.** §13 D-05 requires the §6.3 predictions in the ledger before the atlas sweeps (A4) and training (M3)
start, so that every prediction, including misses, is reported as made. No A4, A7 or M3 run had started at this time.

**New in this experiment.** None (no data). Text copied verbatim from MASTER.md §6.3 at main 135b822.
sha256 of the copied block: `869edaff158002d8b186a785e18f670ab3bb647b6c88b8233c56d8cea6686f8f`.

**Artifacts.** This file; MASTER.md §6.3 at the commit above.

**Config + results.** Not applicable: predictions only. Outcomes are added later as separate entries that cite this ID.

**Caveats.** Operational definitions (e.g., "loss" = relative A10 − A00 retention at the stated K; "predict better" =
higher cross-validated R² in the §8.7 regression) follow §5.2/§8.7; any later refinement is logged as a new entry.

---
### 6.3 Predictions (owner records in §13 before A4 and M3 launch)

1. LoRA adapters keep median EAGLE-3 retention above 95% at K = 4; full
   fine-tunes keep less.
2. Relative loss grows with K at the rate Proposition 1 predicts.
3. DFlash loses more than EAGLE-3 in relative terms at its native block size.
4. Target KL and tap displacement predict loss better than weight-delta norm.
5. Mass outside the drafter vocabulary predicts EAGLE-3's loss on non-English
   derivatives, but not DFlash's.
6. FS beats PO-D on held-out derivatives, with most but not all of the gain
   already captured by MVD.
7. FS keeps parent acceptance within 2%.
8. FS's gains are largest where the frozen drafter lost most.
